#!/usr/bin/env python3
"""Streaming Log Parser for Large Files.

This module provides optimized log parsing capabilities for large log files
using streaming and incremental processing techniques to minimize memory usage
and improve performance.

Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import mmap
import gzip
import bz2
import lzma
from typing import Iterator, Optional, Callable, Dict, Any, List, Union, TextIO
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import threading
import queue
import time

from ..interfaces import LogEntry, SystemInterface
from ..system import LinuxSystemInterface
from .log_parser import LogParser


@dataclass
class StreamingConfig:
    """Configuration for streaming log parser."""
    
    buffer_size: int = 8192  # Buffer size for reading files
    max_line_length: int = 32768  # Maximum line length to prevent memory issues
    batch_size: int = 1000  # Number of entries to process in a batch
    enable_compression: bool = True  # Enable compressed file support
    enable_mmap: bool = True  # Enable memory mapping for large files
    mmap_threshold: int = 10 * 1024 * 1024  # 10MB threshold for mmap
    max_workers: int = 2  # Number of worker threads for parallel processing
    progress_callback: Optional[Callable[[int, int], None]] = None  # Progress callback


class StreamingLogParser:
    """Optimized log parser for large files using streaming techniques."""
    
    def __init__(self, config: Optional[StreamingConfig] = None, 
                 system_interface: Optional[SystemInterface] = None):
        """Initialize streaming log parser.
        
        Args:
            config: Streaming configuration
            system_interface: System interface for command execution
        """
        self.config = config or StreamingConfig()
        self.system = system_interface or LinuxSystemInterface()
        self.base_parser = LogParser(system_interface)
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'entries_parsed': 0,
            'bytes_processed': 0,
            'processing_time': 0.0,
            'errors': 0
        }
        
    def parse_large_file(self, file_path: str, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        max_entries: Optional[int] = None) -> Iterator[LogEntry]:
        """Parse a large log file using streaming techniques.
        
        Args:
            file_path: Path to log file
            start_time: Start time filter (optional)
            end_time: End time filter (optional)
            max_entries: Maximum number of entries to return (optional)
            
        Yields:
            Parsed log entries
        """
        start_processing = time.time()
        
        try:
            file_size = os.path.getsize(file_path)
            self.stats['bytes_processed'] += file_size
            
            # Choose parsing strategy based on file size and configuration
            if (self.config.enable_mmap and 
                file_size > self.config.mmap_threshold and 
                not self._is_compressed_file(file_path)):
                yield from self._parse_with_mmap(file_path, start_time, end_time, max_entries)
            else:
                yield from self._parse_with_streaming(file_path, start_time, end_time, max_entries)
                
            self.stats['files_processed'] += 1
            
        except Exception as e:
            self.stats['errors'] += 1
            # Log error but don't stop processing
            pass
        finally:
            self.stats['processing_time'] += time.time() - start_processing
    
    def parse_multiple_files(self, file_paths: List[str],
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           max_entries: Optional[int] = None) -> Iterator[LogEntry]:
        """Parse multiple log files efficiently.
        
        Args:
            file_paths: List of file paths to parse
            start_time: Start time filter (optional)
            end_time: End time filter (optional)
            max_entries: Maximum number of entries to return (optional)
            
        Yields:
            Parsed log entries in chronological order
        """
        if self.config.max_workers > 1:
            yield from self._parse_files_parallel(file_paths, start_time, end_time, max_entries)
        else:
            yield from self._parse_files_sequential(file_paths, start_time, end_time, max_entries)
    
    def _parse_with_mmap(self, file_path: str,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        max_entries: Optional[int] = None) -> Iterator[LogEntry]:
        """Parse file using memory mapping for better performance.
        
        Args:
            file_path: Path to log file
            start_time: Start time filter
            end_time: End time filter
            max_entries: Maximum entries to return
            
        Yields:
            Parsed log entries
        """
        entries_yielded = 0
        
        try:
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    # Process file in chunks
                    position = 0
                    line_buffer = b''
                    
                    while position < len(mm):
                        # Read chunk
                        chunk_end = min(position + self.config.buffer_size, len(mm))
                        chunk = mm[position:chunk_end]
                        
                        # Combine with previous incomplete line
                        data = line_buffer + chunk
                        lines = data.split(b'\n')
                        
                        # Keep last incomplete line for next iteration
                        line_buffer = lines[-1] if chunk_end < len(mm) else b''
                        lines = lines[:-1] if chunk_end < len(mm) else lines
                        
                        # Process lines
                        for line_bytes in lines:
                            if len(line_bytes) > self.config.max_line_length:
                                continue  # Skip overly long lines
                                
                            try:
                                line = line_bytes.decode('utf-8', errors='ignore')
                                entry = self._parse_line(line, file_path)
                                
                                if entry and self._should_include_entry(entry, start_time, end_time):
                                    yield entry
                                    entries_yielded += 1
                                    self.stats['entries_parsed'] += 1
                                    
                                    if max_entries and entries_yielded >= max_entries:
                                        return
                                        
                                self.stats['lines_processed'] += 1
                                
                            except Exception:
                                self.stats['errors'] += 1
                                continue
                        
                        position = chunk_end
                        
                        # Update progress
                        if self.config.progress_callback:
                            progress = int((position / len(mm)) * 100)
                            self.config.progress_callback(progress, 100)
                            
        except Exception:
            self.stats['errors'] += 1
    
    def _parse_with_streaming(self, file_path: str,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             max_entries: Optional[int] = None) -> Iterator[LogEntry]:
        """Parse file using streaming for memory efficiency.
        
        Args:
            file_path: Path to log file
            start_time: Start time filter
            end_time: End time filter
            max_entries: Maximum entries to return
            
        Yields:
            Parsed log entries
        """
        entries_yielded = 0
        
        try:
            file_opener = self._get_file_opener(file_path)
            
            with file_opener(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                batch = []
                
                for line_num, line in enumerate(f, 1):
                    # Skip overly long lines
                    if len(line) > self.config.max_line_length:
                        continue
                    
                    try:
                        entry = self._parse_line(line.rstrip('\n\r'), file_path)
                        
                        if entry and self._should_include_entry(entry, start_time, end_time):
                            batch.append(entry)
                            
                            # Process batch when full
                            if len(batch) >= self.config.batch_size:
                                for batch_entry in batch:
                                    yield batch_entry
                                    entries_yielded += 1
                                    
                                    if max_entries and entries_yielded >= max_entries:
                                        return
                                        
                                batch.clear()
                                
                        self.stats['lines_processed'] += 1
                        
                        # Update progress periodically
                        if line_num % 10000 == 0 and self.config.progress_callback:
                            # Estimate progress based on file position
                            try:
                                current_pos = f.tell()
                                file_size = os.path.getsize(file_path)
                                progress = int((current_pos / file_size) * 100)
                                self.config.progress_callback(progress, 100)
                            except:
                                pass
                                
                    except Exception:
                        self.stats['errors'] += 1
                        continue
                
                # Process remaining batch
                for entry in batch:
                    yield entry
                    entries_yielded += 1
                    self.stats['entries_parsed'] += 1
                    
                    if max_entries and entries_yielded >= max_entries:
                        return
                        
        except Exception:
            self.stats['errors'] += 1
    
    def _parse_files_sequential(self, file_paths: List[str],
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None,
                               max_entries: Optional[int] = None) -> Iterator[LogEntry]:
        """Parse files sequentially.
        
        Args:
            file_paths: List of file paths
            start_time: Start time filter
            end_time: End time filter
            max_entries: Maximum entries to return
            
        Yields:
            Parsed log entries
        """
        entries_yielded = 0
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            for entry in self.parse_large_file(file_path, start_time, end_time):
                yield entry
                entries_yielded += 1
                
                if max_entries and entries_yielded >= max_entries:
                    return
    
    def _parse_files_parallel(self, file_paths: List[str],
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             max_entries: Optional[int] = None) -> Iterator[LogEntry]:
        """Parse files in parallel using worker threads.
        
        Args:
            file_paths: List of file paths
            start_time: Start time filter
            end_time: End time filter
            max_entries: Maximum entries to return
            
        Yields:
            Parsed log entries in chronological order
        """
        # Use a priority queue to maintain chronological order
        result_queue = queue.PriorityQueue()
        worker_threads = []
        entries_yielded = 0
        
        def worker(file_path: str, worker_id: int):
            """Worker thread function."""
            try:
                entries = list(self.parse_large_file(file_path, start_time, end_time))
                for entry in entries:
                    # Use timestamp as priority for chronological ordering
                    priority = entry.timestamp.timestamp()
                    result_queue.put((priority, worker_id, entry))
            except Exception:
                pass
        
        # Start worker threads
        for i, file_path in enumerate(file_paths[:self.config.max_workers]):
            if os.path.exists(file_path):
                thread = threading.Thread(target=worker, args=(file_path, i))
                thread.start()
                worker_threads.append(thread)
        
        # Collect results
        active_workers = len(worker_threads)
        
        while active_workers > 0 or not result_queue.empty():
            try:
                # Get entry with timeout
                priority, worker_id, entry = result_queue.get(timeout=1.0)
                yield entry
                entries_yielded += 1
                
                if max_entries and entries_yielded >= max_entries:
                    break
                    
            except queue.Empty:
                # Check if workers are still active
                active_workers = sum(1 for t in worker_threads if t.is_alive())
        
        # Wait for all threads to complete
        for thread in worker_threads:
            thread.join(timeout=1.0)
    
    def _parse_line(self, line: str, source_file: str) -> Optional[LogEntry]:
        """Parse a single log line.
        
        Args:
            line: Log line to parse
            source_file: Source file path
            
        Returns:
            Parsed log entry or None
        """
        if not line.strip():
            return None
            
        return self.base_parser._parse_syslog_line(line, source_file)
    
    def _should_include_entry(self, entry: LogEntry,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> bool:
        """Check if entry should be included based on time filters.
        
        Args:
            entry: Log entry to check
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            True if entry should be included
        """
        if start_time and entry.timestamp < start_time:
            return False
            
        if end_time and entry.timestamp > end_time:
            return False
            
        return True
    
    def _is_compressed_file(self, file_path: str) -> bool:
        """Check if file is compressed.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file is compressed
        """
        return file_path.endswith(('.gz', '.bz2', '.xz', '.lzma'))
    
    def _get_file_opener(self, file_path: str) -> Callable:
        """Get appropriate file opener based on file type.
        
        Args:
            file_path: File path
            
        Returns:
            File opener function
        """
        if not self.config.enable_compression:
            return open
            
        if file_path.endswith('.gz'):
            return gzip.open
        elif file_path.endswith('.bz2'):
            return bz2.open
        elif file_path.endswith(('.xz', '.lzma')):
            return lzma.open
        else:
            return open
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics.
        
        Returns:
            Dictionary with parsing statistics
        """
        stats = self.stats.copy()
        
        # Calculate derived statistics
        if stats['processing_time'] > 0:
            stats['lines_per_second'] = stats['lines_processed'] / stats['processing_time']
            stats['entries_per_second'] = stats['entries_parsed'] / stats['processing_time']
            stats['bytes_per_second'] = stats['bytes_processed'] / stats['processing_time']
        else:
            stats['lines_per_second'] = 0
            stats['entries_per_second'] = 0
            stats['bytes_per_second'] = 0
            
        if stats['lines_processed'] > 0:
            stats['parse_success_rate'] = stats['entries_parsed'] / stats['lines_processed']
            stats['error_rate'] = stats['errors'] / stats['lines_processed']
        else:
            stats['parse_success_rate'] = 0
            stats['error_rate'] = 0
            
        return stats
    
    def reset_statistics(self) -> None:
        """Reset parsing statistics."""
        self.stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'entries_parsed': 0,
            'bytes_processed': 0,
            'processing_time': 0.0,
            'errors': 0
        }
    
    def estimate_processing_time(self, file_paths: List[str]) -> float:
        """Estimate processing time for given files.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Estimated processing time in seconds
        """
        total_size = 0
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            except:
                continue
        
        # Estimate based on previous performance
        if self.stats['processing_time'] > 0 and self.stats['bytes_processed'] > 0:
            bytes_per_second = self.stats['bytes_processed'] / self.stats['processing_time']
            return total_size / bytes_per_second
        else:
            # Default estimate: 10MB/second
            return total_size / (10 * 1024 * 1024)


class IncrementalLogAnalyzer:
    """Incremental log analyzer for continuous processing."""
    
    def __init__(self, streaming_parser: StreamingLogParser):
        """Initialize incremental analyzer.
        
        Args:
            streaming_parser: Streaming parser instance
        """
        self.parser = streaming_parser
        self.processed_files: Dict[str, Dict[str, Any]] = {}
        self.last_analysis_time = datetime.now()
        
    def analyze_new_entries(self, file_paths: List[str],
                           since: Optional[datetime] = None) -> Iterator[LogEntry]:
        """Analyze only new log entries since last analysis.
        
        Args:
            file_paths: List of file paths to analyze
            since: Only process entries since this time
            
        Yields:
            New log entries
        """
        if since is None:
            since = self.last_analysis_time
            
        for file_path in file_paths:
            # Check if file has been modified since last analysis
            if self._file_needs_processing(file_path, since):
                # Get file position from last analysis
                last_position = self.processed_files.get(file_path, {}).get('position', 0)
                
                # Process from last position
                yield from self._process_file_from_position(file_path, last_position, since)
                
                # Update file tracking
                self._update_file_tracking(file_path)
        
        self.last_analysis_time = datetime.now()
    
    def _file_needs_processing(self, file_path: str, since: datetime) -> bool:
        """Check if file needs processing.
        
        Args:
            file_path: File path to check
            since: Check modifications since this time
            
        Returns:
            True if file needs processing
        """
        try:
            if not os.path.exists(file_path):
                return False
                
            file_stat = os.stat(file_path)
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            
            return file_mtime > since
            
        except:
            return False
    
    def _process_file_from_position(self, file_path: str, start_position: int,
                                   since: datetime) -> Iterator[LogEntry]:
        """Process file from a specific position.
        
        Args:
            file_path: File path to process
            start_position: Starting byte position
            since: Only include entries since this time
            
        Yields:
            Log entries from the specified position
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(start_position)
                
                for line in f:
                    entry = self.parser._parse_line(line.rstrip('\n\r'), file_path)
                    
                    if entry and entry.timestamp >= since:
                        yield entry
                        
        except Exception:
            pass
    
    def _update_file_tracking(self, file_path: str) -> None:
        """Update file tracking information.
        
        Args:
            file_path: File path to update
        """
        try:
            file_stat = os.stat(file_path)
            
            self.processed_files[file_path] = {
                'position': file_stat.st_size,
                'mtime': file_stat.st_mtime,
                'last_processed': datetime.now().timestamp()
            }
            
        except:
            pass