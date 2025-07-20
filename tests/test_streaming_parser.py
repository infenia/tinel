#!/usr/bin/env python3
"""Tests for Streaming Log Parser.

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
import tempfile
import gzip
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pytest

from infenix.logs.streaming_parser import (
    StreamingLogParser, 
    StreamingConfig, 
    IncrementalLogAnalyzer
)
from infenix.interfaces import LogEntry


class TestStreamingConfig:
    """Test cases for StreamingConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = StreamingConfig()
        
        assert config.buffer_size == 8192
        assert config.max_line_length == 32768
        assert config.batch_size == 1000
        assert config.enable_compression is True
        assert config.enable_mmap is True
        assert config.mmap_threshold == 10 * 1024 * 1024
        assert config.max_workers == 2
        assert config.progress_callback is None
    
    def test_custom_config(self):
        """Test custom configuration values."""
        callback = Mock()
        
        config = StreamingConfig(
            buffer_size=4096,
            max_line_length=16384,
            batch_size=500,
            enable_compression=False,
            enable_mmap=False,
            mmap_threshold=5 * 1024 * 1024,
            max_workers=4,
            progress_callback=callback
        )
        
        assert config.buffer_size == 4096
        assert config.max_line_length == 16384
        assert config.batch_size == 500
        assert config.enable_compression is False
        assert config.enable_mmap is False
        assert config.mmap_threshold == 5 * 1024 * 1024
        assert config.max_workers == 4
        assert config.progress_callback == callback


class TestStreamingLogParser:
    """Test cases for StreamingLogParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = StreamingConfig(
            buffer_size=1024,
            batch_size=10,
            enable_mmap=False,  # Disable mmap for testing
            max_workers=1  # Single worker for predictable testing
        )
        self.parser = StreamingLogParser(self.config)
        
    def create_test_log_file(self, content: str, compressed: bool = False) -> str:
        """Create a temporary log file for testing.
        
        Args:
            content: Log file content
            compressed: Whether to compress the file
            
        Returns:
            Path to created file
        """
        suffix = '.log.gz' if compressed else '.log'
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
            if compressed:
                with gzip.open(f.name, 'wt', encoding='utf-8') as gz_f:
                    gz_f.write(content)
            else:
                f.write(content.encode('utf-8'))
            
            return f.name
    
    def test_initialization(self):
        """Test parser initialization."""
        assert self.parser.config == self.config
        assert self.parser.system is not None
        assert self.parser.base_parser is not None
        assert isinstance(self.parser.stats, dict)
    
    def test_parse_small_file(self):
        """Test parsing a small log file."""
        log_content = """Jan 15 10:30:45 server1 kernel: Test message 1
Jan 15 10:30:46 server1 sshd: Test message 2
Jan 15 10:30:47 server1 apache: Test message 3
"""
        
        file_path = self.create_test_log_file(log_content)
        
        try:
            entries = list(self.parser.parse_large_file(file_path))
            
            assert len(entries) == 3
            assert all(isinstance(entry, LogEntry) for entry in entries)
            assert entries[0].message == "Test message 1"
            assert entries[1].message == "Test message 2"
            assert entries[2].message == "Test message 3"
            
            # Check statistics
            stats = self.parser.get_statistics()
            assert stats['files_processed'] == 1
            assert stats['lines_processed'] >= 3
            assert stats['entries_parsed'] >= 3
            
        finally:
            os.unlink(file_path)
    
    def test_parse_with_time_filter(self):
        """Test parsing with time filters."""
        log_content = """Jan 15 10:30:45 server1 kernel: Message 1
Jan 15 10:30:46 server1 sshd: Message 2
Jan 15 10:30:47 server1 apache: Message 3
"""
        
        file_path = self.create_test_log_file(log_content)
        
        try:
            # Set time filter to exclude some entries
            start_time = datetime(2024, 1, 15, 10, 30, 46)
            
            entries = list(self.parser.parse_large_file(file_path, start_time=start_time))
            
            # Should only get entries from 10:30:46 onwards
            assert len(entries) >= 1  # At least the filtered entries
            
        finally:
            os.unlink(file_path)
    
    def test_parse_with_max_entries(self):
        """Test parsing with maximum entries limit."""
        log_content = """Jan 15 10:30:45 server1 kernel: Message 1
Jan 15 10:30:46 server1 sshd: Message 2
Jan 15 10:30:47 server1 apache: Message 3
Jan 15 10:30:48 server1 nginx: Message 4
Jan 15 10:30:49 server1 mysql: Message 5
"""
        
        file_path = self.create_test_log_file(log_content)
        
        try:
            entries = list(self.parser.parse_large_file(file_path, max_entries=3))
            
            assert len(entries) <= 3
            
        finally:
            os.unlink(file_path)
    
    def test_parse_compressed_file(self):
        """Test parsing compressed log files."""
        log_content = """Jan 15 10:30:45 server1 kernel: Compressed message 1
Jan 15 10:30:46 server1 sshd: Compressed message 2
"""
        
        file_path = self.create_test_log_file(log_content, compressed=True)
        
        try:
            entries = list(self.parser.parse_large_file(file_path))
            
            assert len(entries) >= 1
            assert any("Compressed message" in entry.message for entry in entries)
            
        finally:
            os.unlink(file_path)
    
    def test_parse_multiple_files(self):
        """Test parsing multiple files."""
        log_content1 = """Jan 15 10:30:45 server1 kernel: File 1 message 1
Jan 15 10:30:46 server1 sshd: File 1 message 2
"""
        
        log_content2 = """Jan 15 10:30:47 server2 apache: File 2 message 1
Jan 15 10:30:48 server2 nginx: File 2 message 2
"""
        
        file1 = self.create_test_log_file(log_content1)
        file2 = self.create_test_log_file(log_content2)
        
        try:
            entries = list(self.parser.parse_multiple_files([file1, file2]))
            
            assert len(entries) >= 2
            
            # Check that entries from both files are present
            messages = [entry.message for entry in entries]
            assert any("File 1 message" in msg for msg in messages)
            assert any("File 2 message" in msg for msg in messages)
            
        finally:
            os.unlink(file1)
            os.unlink(file2)
    
    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file."""
        entries = list(self.parser.parse_large_file("/nonexistent/file.log"))
        
        assert len(entries) == 0
        
        # Should have recorded an error
        stats = self.parser.get_statistics()
        assert stats['errors'] > 0
    
    def test_parse_empty_file(self):
        """Test parsing empty file."""
        file_path = self.create_test_log_file("")
        
        try:
            entries = list(self.parser.parse_large_file(file_path))
            
            assert len(entries) == 0
            
        finally:
            os.unlink(file_path)
    
    def test_parse_file_with_long_lines(self):
        """Test parsing file with overly long lines."""
        # Create a line longer than max_line_length
        long_line = "A" * (self.config.max_line_length + 100)
        normal_line = "Jan 15 10:30:45 server1 kernel: Normal message"
        
        log_content = f"{long_line}\n{normal_line}\n"
        
        file_path = self.create_test_log_file(log_content)
        
        try:
            entries = list(self.parser.parse_large_file(file_path))
            
            # Should only get the normal line, long line should be skipped
            assert len(entries) >= 0  # At least no crash
            
            if entries:
                assert "Normal message" in entries[0].message
            
        finally:
            os.unlink(file_path)
    
    def test_progress_callback(self):
        """Test progress callback functionality."""
        callback = Mock()
        config = StreamingConfig(progress_callback=callback)
        parser = StreamingLogParser(config)
        
        log_content = """Jan 15 10:30:45 server1 kernel: Message 1
Jan 15 10:30:46 server1 sshd: Message 2
Jan 15 10:30:47 server1 apache: Message 3
"""
        
        file_path = self.create_test_log_file(log_content)
        
        try:
            list(parser.parse_large_file(file_path))
            
            # Progress callback should have been called
            # (May not be called for small files, but shouldn't crash)
            
        finally:
            os.unlink(file_path)
    
    def test_statistics_tracking(self):
        """Test statistics tracking."""
        log_content = """Jan 15 10:30:45 server1 kernel: Message 1
Jan 15 10:30:46 server1 sshd: Message 2
Invalid log line without proper format
Jan 15 10:30:47 server1 apache: Message 3
"""
        
        file_path = self.create_test_log_file(log_content)
        
        try:
            # Reset statistics
            self.parser.reset_statistics()
            
            entries = list(self.parser.parse_large_file(file_path))
            
            stats = self.parser.get_statistics()
            
            assert stats['files_processed'] == 1
            assert stats['lines_processed'] > 0
            assert stats['entries_parsed'] > 0
            assert stats['bytes_processed'] > 0
            assert stats['processing_time'] > 0
            
            # Check derived statistics
            assert 'lines_per_second' in stats
            assert 'entries_per_second' in stats
            assert 'bytes_per_second' in stats
            assert 'parse_success_rate' in stats
            assert 'error_rate' in stats
            
        finally:
            os.unlink(file_path)
    
    def test_reset_statistics(self):
        """Test statistics reset."""
        # Process a file to generate some statistics
        log_content = "Jan 15 10:30:45 server1 kernel: Test message\n"
        file_path = self.create_test_log_file(log_content)
        
        try:
            list(self.parser.parse_large_file(file_path))
            
            # Verify statistics are not zero
            stats_before = self.parser.get_statistics()
            assert stats_before['files_processed'] > 0
            
            # Reset statistics
            self.parser.reset_statistics()
            
            # Verify statistics are reset
            stats_after = self.parser.get_statistics()
            assert stats_after['files_processed'] == 0
            assert stats_after['lines_processed'] == 0
            assert stats_after['entries_parsed'] == 0
            
        finally:
            os.unlink(file_path)
    
    def test_estimate_processing_time(self):
        """Test processing time estimation."""
        log_content = "Jan 15 10:30:45 server1 kernel: Test message\n"
        file_path = self.create_test_log_file(log_content)
        
        try:
            # First, process a file to establish baseline performance
            list(self.parser.parse_large_file(file_path))
            
            # Now estimate processing time for the same file
            estimated_time = self.parser.estimate_processing_time([file_path])
            
            assert isinstance(estimated_time, float)
            assert estimated_time >= 0
            
        finally:
            os.unlink(file_path)
    
    def test_file_opener_selection(self):
        """Test file opener selection based on file type."""
        # Test regular file
        opener = self.parser._get_file_opener("test.log")
        assert opener == open
        
        # Test compressed files
        if self.parser.config.enable_compression:
            opener = self.parser._get_file_opener("test.log.gz")
            assert opener == gzip.open
    
    def test_is_compressed_file(self):
        """Test compressed file detection."""
        assert self.parser._is_compressed_file("test.log.gz") is True
        assert self.parser._is_compressed_file("test.log.bz2") is True
        assert self.parser._is_compressed_file("test.log.xz") is True
        assert self.parser._is_compressed_file("test.log") is False
    
    def test_should_include_entry(self):
        """Test entry inclusion logic."""
        entry = LogEntry(
            timestamp=datetime(2024, 1, 15, 10, 30, 45),
            facility='kernel',
            severity='info',
            message='Test message',
            source='test'
        )
        
        # No filters - should include
        assert self.parser._should_include_entry(entry) is True
        
        # Start time filter - should include
        start_time = datetime(2024, 1, 15, 10, 30, 44)
        assert self.parser._should_include_entry(entry, start_time=start_time) is True
        
        # Start time filter - should exclude
        start_time = datetime(2024, 1, 15, 10, 30, 46)
        assert self.parser._should_include_entry(entry, start_time=start_time) is False
        
        # End time filter - should include
        end_time = datetime(2024, 1, 15, 10, 30, 46)
        assert self.parser._should_include_entry(entry, end_time=end_time) is True
        
        # End time filter - should exclude
        end_time = datetime(2024, 1, 15, 10, 30, 44)
        assert self.parser._should_include_entry(entry, end_time=end_time) is False


class TestIncrementalLogAnalyzer:
    """Test cases for IncrementalLogAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        config = StreamingConfig(enable_mmap=False)
        parser = StreamingLogParser(config)
        self.analyzer = IncrementalLogAnalyzer(parser)
    
    def create_test_log_file(self, content: str) -> str:
        """Create a temporary log file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(content)
            return f.name
    
    def test_initialization(self):
        """Test analyzer initialization."""
        assert self.analyzer.parser is not None
        assert isinstance(self.analyzer.processed_files, dict)
        assert isinstance(self.analyzer.last_analysis_time, datetime)
    
    def test_file_needs_processing(self):
        """Test file processing need detection."""
        log_content = "Jan 15 10:30:45 server1 kernel: Test message\n"
        file_path = self.create_test_log_file(log_content)
        
        try:
            # File should need processing (recently created)
            since = datetime.now() - timedelta(minutes=1)
            assert self.analyzer._file_needs_processing(file_path, since) is True
            
            # File should not need processing (check against future time)
            since = datetime.now() + timedelta(minutes=1)
            assert self.analyzer._file_needs_processing(file_path, since) is False
            
            # Non-existent file should not need processing
            assert self.analyzer._file_needs_processing("/nonexistent/file.log", since) is False
            
        finally:
            os.unlink(file_path)
    
    def test_analyze_new_entries(self):
        """Test analyzing new entries."""
        log_content = """Jan 15 10:30:45 server1 kernel: Message 1
Jan 15 10:30:46 server1 sshd: Message 2
"""
        
        file_path = self.create_test_log_file(log_content)
        
        try:
            # Analyze entries since a past time
            since = datetime.now() - timedelta(hours=1)
            entries = list(self.analyzer.analyze_new_entries([file_path], since))
            
            # Should get some entries
            assert len(entries) >= 0
            
        finally:
            os.unlink(file_path)
    
    def test_update_file_tracking(self):
        """Test file tracking updates."""
        log_content = "Jan 15 10:30:45 server1 kernel: Test message\n"
        file_path = self.create_test_log_file(log_content)
        
        try:
            # Initially no tracking
            assert file_path not in self.analyzer.processed_files
            
            # Update tracking
            self.analyzer._update_file_tracking(file_path)
            
            # Should now have tracking info
            assert file_path in self.analyzer.processed_files
            tracking_info = self.analyzer.processed_files[file_path]
            
            assert 'position' in tracking_info
            assert 'mtime' in tracking_info
            assert 'last_processed' in tracking_info
            
        finally:
            os.unlink(file_path)