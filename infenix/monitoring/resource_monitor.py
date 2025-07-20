#!/usr/bin/env python3
"""Resource Usage Monitoring for Infenix.

This module provides CPU and memory usage tracking capabilities with
real-time monitoring and historical data collection.

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
import time
import threading
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple
from collections import deque
import psutil


@dataclass
class ResourceUsage:
    """Resource usage information."""
    
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    process_cpu_percent: float
    process_memory_mb: float
    process_threads: int


@dataclass
class SystemLoad:
    """System load information."""
    
    load_1min: float
    load_5min: float
    load_15min: float
    cpu_count: int
    normalized_load_1min: float
    normalized_load_5min: float
    normalized_load_15min: float


class ResourceMonitor:
    """Monitors system and process resource usage."""
    
    def __init__(self, history_size: int = 100, monitoring_interval: float = 1.0):
        """Initialize the resource monitor.
        
        Args:
            history_size: Number of historical measurements to keep
            monitoring_interval: Interval between measurements in seconds
        """
        self.history_size = history_size
        self.monitoring_interval = monitoring_interval
        self.usage_history: deque = deque(maxlen=history_size)
        self.load_history: deque = deque(maxlen=history_size)
        
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[ResourceUsage], None]] = []
        self._callbacks_lock = threading.RLock()  # Thread-safe callback management
        self._process = None
        self._logger = logging.getLogger(self.__class__.__name__)
        
    def add_callback(self, callback: Callable[[ResourceUsage], None]) -> None:
        """Add a callback to be called when new usage data is available.
        
        Args:
            callback: Function to call with ResourceUsage data
        """
        with self._callbacks_lock:
            self._callbacks.append(callback)
            self._logger.debug(f"Added callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")
        
    def remove_callback(self, callback: Callable[[ResourceUsage], None]) -> None:
        """Remove a callback.
        
        Args:
            callback: Function to remove from callbacks
        """
        with self._callbacks_lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
                self._logger.debug(f"Removed callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current resource usage.
        
        Returns:
            Current resource usage information
        """
        timestamp = time.time()
        
        # Get system-wide metrics with minimal interval for better performance
        cpu_percent = psutil.cpu_percent(interval=0.01)  # Reduced from 0.1
        memory = psutil.virtual_memory()
        
        # Get process-specific metrics with better error handling
        process_cpu, process_memory, process_threads = self._get_process_metrics()
        
        return ResourceUsage(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),  # More efficient calculation
            memory_available_mb=memory.available / (1024 * 1024),
            process_cpu_percent=process_cpu,
            process_memory_mb=process_memory,
            process_threads=process_threads
        )
    
    def _get_process_metrics(self) -> Tuple[float, float, int]:
        """Get process-specific metrics with caching and error handling.
        
        Returns:
            Tuple of (cpu_percent, memory_mb, thread_count)
        """
        try:
            if self._process is None:
                self._process = psutil.Process()
            
            # Use oneshot() context manager for efficient multiple attribute access
            with self._process.oneshot():
                cpu_percent = self._process.cpu_percent()
                memory_mb = self._process.memory_info().rss / (1024 * 1024)
                thread_count = self._process.num_threads()
                
            return cpu_percent, memory_mb, thread_count
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            # Log specific process access issues
            if hasattr(self, '_logger'):
                self._logger.debug(f"Process access error: {e}")
            self._process = None  # Reset process reference
            return 0.0, 0.0, 0
        except Exception as e:
            # Log unexpected errors
            if hasattr(self, '_logger'):
                self._logger.warning(f"Unexpected error getting process metrics: {e}")
            return 0.0, 0.0, 0
    
    def get_system_load(self) -> SystemLoad:
        """Get current system load information.
        
        Returns:
            Current system load information
        """
        load_avg = os.getloadavg()
        cpu_count = psutil.cpu_count()
        
        return SystemLoad(
            load_1min=load_avg[0],
            load_5min=load_avg[1], 
            load_15min=load_avg[2],
            cpu_count=cpu_count,
            normalized_load_1min=load_avg[0] / cpu_count,
            normalized_load_5min=load_avg[1] / cpu_count,
            normalized_load_15min=load_avg[2] / cpu_count
        )
    
    def start_monitoring(self) -> None:
        """Start continuous resource monitoring."""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop continuous resource monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop with improved error handling."""
        self._logger.info("Resource monitoring started")
        error_count = 0
        max_consecutive_errors = 5
        
        while self._monitoring:
            try:
                # Collect usage data
                usage = self.get_current_usage()
                self.usage_history.append(usage)
                
                # Collect load data
                load = self.get_system_load()
                self.load_history.append(load)
                
                # Notify callbacks with thread-safe iteration
                with self._callbacks_lock:
                    callbacks_snapshot = list(self._callbacks)
                
                for callback in callbacks_snapshot:
                    try:
                        callback(usage)
                    except Exception as e:
                        self._logger.warning(f"Callback error: {e}")
                
                # Reset error count on successful iteration
                error_count = 0
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                error_count += 1
                self._logger.error(f"Monitoring error ({error_count}/{max_consecutive_errors}): {e}")
                
                if error_count >= max_consecutive_errors:
                    self._logger.critical("Too many consecutive monitoring errors, stopping monitoring")
                    self._monitoring = False
                    break
                
                # Exponential backoff on errors
                time.sleep(min(self.monitoring_interval * (2 ** error_count), 30.0))
        
        self._logger.info("Resource monitoring stopped")
    
    def get_usage_history(self) -> List[ResourceUsage]:
        """Get historical resource usage data.
        
        Returns:
            List of historical resource usage measurements
        """
        return list(self.usage_history)
    
    def get_load_history(self) -> List[SystemLoad]:
        """Get historical system load data.
        
        Returns:
            List of historical system load measurements
        """
        return list(self.load_history)
    
    def get_average_usage(self, window_size: Optional[int] = None) -> Optional[ResourceUsage]:
        """Get average resource usage over a window.
        
        Args:
            window_size: Number of recent measurements to average (None for all)
            
        Returns:
            Average resource usage or None if no data available
        """
        if not self.usage_history:
            return None
            
        history = list(self.usage_history)
        if window_size:
            history = history[-window_size:]
            
        if not history:
            return None
        
        # Calculate averages
        avg_cpu = sum(u.cpu_percent for u in history) / len(history)
        avg_memory_percent = sum(u.memory_percent for u in history) / len(history)
        avg_memory_used = sum(u.memory_used_mb for u in history) / len(history)
        avg_memory_available = sum(u.memory_available_mb for u in history) / len(history)
        avg_process_cpu = sum(u.process_cpu_percent for u in history) / len(history)
        avg_process_memory = sum(u.process_memory_mb for u in history) / len(history)
        avg_process_threads = sum(u.process_threads for u in history) / len(history)
        
        return ResourceUsage(
            timestamp=time.time(),
            cpu_percent=avg_cpu,
            memory_percent=avg_memory_percent,
            memory_used_mb=avg_memory_used,
            memory_available_mb=avg_memory_available,
            process_cpu_percent=avg_process_cpu,
            process_memory_mb=avg_process_memory,
            process_threads=int(avg_process_threads)
        )
    
    def is_high_usage(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0) -> bool:
        """Check if current usage is high.
        
        Args:
            cpu_threshold: CPU usage threshold percentage
            memory_threshold: Memory usage threshold percentage
            
        Returns:
            True if usage is above thresholds
        """
        usage = self.get_current_usage()
        return usage.cpu_percent > cpu_threshold or usage.memory_percent > memory_threshold
    
    def get_usage_stats(self) -> Dict[str, float]:
        """Get usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        if not self.usage_history:
            return {}
            
        history = list(self.usage_history)
        cpu_values = [u.cpu_percent for u in history]
        memory_values = [u.memory_percent for u in history]
        
        return {
            "cpu_min": min(cpu_values),
            "cpu_max": max(cpu_values),
            "cpu_avg": sum(cpu_values) / len(cpu_values),
            "memory_min": min(memory_values),
            "memory_max": max(memory_values),
            "memory_avg": sum(memory_values) / len(memory_values),
            "samples": len(history)
        }