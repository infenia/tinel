#!/usr/bin/env python3
"""Tests for Resource Monitor.

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

import time
import threading
from unittest.mock import Mock, patch, MagicMock
import pytest

from infenix.monitoring.resource_monitor import ResourceMonitor, ResourceUsage, SystemLoad


class TestResourceMonitor:
    """Test cases for ResourceMonitor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = ResourceMonitor(history_size=5, monitoring_interval=0.1)
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.monitor._monitoring:
            self.monitor.stop_monitoring()
    
    @patch('infenix.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('infenix.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('infenix.monitoring.resource_monitor.psutil.Process')
    def test_get_current_usage(self, mock_process_class, mock_virtual_memory, mock_cpu_percent):
        """Test getting current resource usage."""
        # Mock system metrics
        mock_cpu_percent.return_value = 45.5
        mock_memory = Mock()
        mock_memory.percent = 60.2
        mock_memory.used = 8 * 1024 * 1024 * 1024  # 8GB in bytes
        mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB in bytes
        mock_virtual_memory.return_value = mock_memory
        
        # Mock process metrics
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 12.3
        mock_memory_info = Mock()
        mock_memory_info.rss = 256 * 1024 * 1024  # 256MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.num_threads.return_value = 4
        mock_process_class.return_value = mock_process
        
        usage = self.monitor.get_current_usage()
        
        assert isinstance(usage, ResourceUsage)
        assert usage.cpu_percent == 45.5
        assert usage.memory_percent == 60.2
        assert usage.memory_used_mb == 8192.0  # 8GB in MB
        assert usage.memory_available_mb == 4096.0  # 4GB in MB
        assert usage.process_cpu_percent == 12.3
        assert usage.process_memory_mb == 256.0  # 256MB
        assert usage.process_threads == 4
        assert isinstance(usage.timestamp, float)
    
    @patch('infenix.monitoring.resource_monitor.os.getloadavg')
    @patch('infenix.monitoring.resource_monitor.psutil.cpu_count')
    def test_get_system_load(self, mock_cpu_count, mock_getloadavg):
        """Test getting system load information."""
        mock_getloadavg.return_value = (1.5, 1.2, 0.8)
        mock_cpu_count.return_value = 4
        
        load = self.monitor.get_system_load()
        
        assert isinstance(load, SystemLoad)
        assert load.load_1min == 1.5
        assert load.load_5min == 1.2
        assert load.load_15min == 0.8
        assert load.cpu_count == 4
        assert load.normalized_load_1min == 1.5 / 4
        assert load.normalized_load_5min == 1.2 / 4
        assert load.normalized_load_15min == 0.8 / 4
    
    def test_callback_management(self):
        """Test adding and removing callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        self.monitor.add_callback(callback1)
        self.monitor.add_callback(callback2)
        assert len(self.monitor._callbacks) == 2
        
        # Remove callback
        self.monitor.remove_callback(callback1)
        assert len(self.monitor._callbacks) == 1
        assert callback2 in self.monitor._callbacks
        
        # Remove non-existent callback (should not raise error)
        self.monitor.remove_callback(callback1)
        assert len(self.monitor._callbacks) == 1
    
    @patch('infenix.monitoring.resource_monitor.psutil.cpu_percent')
    @patch('infenix.monitoring.resource_monitor.psutil.virtual_memory')
    @patch('infenix.monitoring.resource_monitor.psutil.Process')
    def test_monitoring_loop(self, mock_process_class, mock_virtual_memory, mock_cpu_percent):
        """Test continuous monitoring loop."""
        # Mock system metrics
        mock_cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 70.0
        mock_memory.used = 8 * 1024 * 1024 * 1024
        mock_memory.available = 4 * 1024 * 1024 * 1024
        mock_virtual_memory.return_value = mock_memory
        
        # Mock process metrics
        mock_process = Mock()
        mock_process.cpu_percent.return_value = 10.0
        mock_memory_info = Mock()
        mock_memory_info.rss = 128 * 1024 * 1024
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.num_threads.return_value = 2
        mock_process_class.return_value = mock_process
        
        # Add callback to verify it's called
        callback = Mock()
        self.monitor.add_callback(callback)
        
        # Start monitoring
        self.monitor.start_monitoring()
        assert self.monitor._monitoring is True
        assert self.monitor._monitor_thread is not None
        
        # Wait for some data to be collected
        time.sleep(0.3)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        assert self.monitor._monitoring is False
        
        # Verify data was collected
        assert len(self.monitor.usage_history) > 0
        assert len(self.monitor.load_history) > 0
        
        # Verify callback was called
        assert callback.call_count > 0
    
    def test_usage_history(self):
        """Test usage history management."""
        # Create mock usage data
        usage1 = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=30.0,
            memory_percent=40.0,
            memory_used_mb=4000.0,
            memory_available_mb=4000.0,
            process_cpu_percent=5.0,
            process_memory_mb=100.0,
            process_threads=2
        )
        
        usage2 = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=6000.0,
            memory_available_mb=2000.0,
            process_cpu_percent=10.0,
            process_memory_mb=150.0,
            process_threads=3
        )
        
        # Add to history
        self.monitor.usage_history.append(usage1)
        self.monitor.usage_history.append(usage2)
        
        # Test get_usage_history
        history = self.monitor.get_usage_history()
        assert len(history) == 2
        assert history[0] == usage1
        assert history[1] == usage2
        
        # Test get_average_usage
        avg = self.monitor.get_average_usage()
        assert avg is not None
        assert avg.cpu_percent == 40.0  # (30 + 50) / 2
        assert avg.memory_percent == 50.0  # (40 + 60) / 2
        assert avg.process_threads == 2  # int((2 + 3) / 2)
    
    def test_average_usage_with_window(self):
        """Test average usage calculation with window size."""
        # Add multiple usage entries
        for i in range(10):
            usage = ResourceUsage(
                timestamp=time.time(),
                cpu_percent=float(i * 10),
                memory_percent=float(i * 5),
                memory_used_mb=1000.0,
                memory_available_mb=1000.0,
                process_cpu_percent=1.0,
                process_memory_mb=100.0,
                process_threads=1
            )
            self.monitor.usage_history.append(usage)
        
        # Test with window size
        avg = self.monitor.get_average_usage(window_size=3)
        assert avg is not None
        # Should average the last 3 entries: 70, 80, 90 -> 80
        assert avg.cpu_percent == 80.0
        # Should average the last 3 entries: 35, 40, 45 -> 40
        assert avg.memory_percent == 40.0
    
    def test_average_usage_empty_history(self):
        """Test average usage with empty history."""
        avg = self.monitor.get_average_usage()
        assert avg is None
    
    def test_is_high_usage(self):
        """Test high usage detection."""
        with patch.object(self.monitor, 'get_current_usage') as mock_get_usage:
            # Test normal usage
            mock_get_usage.return_value = ResourceUsage(
                timestamp=time.time(),
                cpu_percent=50.0,
                memory_percent=60.0,
                memory_used_mb=4000.0,
                memory_available_mb=4000.0,
                process_cpu_percent=5.0,
                process_memory_mb=100.0,
                process_threads=2
            )
            assert not self.monitor.is_high_usage()
            
            # Test high CPU usage
            mock_get_usage.return_value = ResourceUsage(
                timestamp=time.time(),
                cpu_percent=85.0,
                memory_percent=60.0,
                memory_used_mb=4000.0,
                memory_available_mb=4000.0,
                process_cpu_percent=5.0,
                process_memory_mb=100.0,
                process_threads=2
            )
            assert self.monitor.is_high_usage()
            
            # Test high memory usage
            mock_get_usage.return_value = ResourceUsage(
                timestamp=time.time(),
                cpu_percent=50.0,
                memory_percent=85.0,
                memory_used_mb=4000.0,
                memory_available_mb=4000.0,
                process_cpu_percent=5.0,
                process_memory_mb=100.0,
                process_threads=2
            )
            assert self.monitor.is_high_usage()
    
    def test_usage_stats(self):
        """Test usage statistics calculation."""
        # Add test data
        cpu_values = [20.0, 40.0, 60.0, 80.0]
        memory_values = [30.0, 50.0, 70.0, 90.0]
        
        for cpu, mem in zip(cpu_values, memory_values):
            usage = ResourceUsage(
                timestamp=time.time(),
                cpu_percent=cpu,
                memory_percent=mem,
                memory_used_mb=4000.0,
                memory_available_mb=4000.0,
                process_cpu_percent=5.0,
                process_memory_mb=100.0,
                process_threads=2
            )
            self.monitor.usage_history.append(usage)
        
        stats = self.monitor.get_usage_stats()
        
        assert stats["cpu_min"] == 20.0
        assert stats["cpu_max"] == 80.0
        assert stats["cpu_avg"] == 50.0
        assert stats["memory_min"] == 30.0
        assert stats["memory_max"] == 90.0
        assert stats["memory_avg"] == 60.0
        assert stats["samples"] == 4
    
    def test_usage_stats_empty_history(self):
        """Test usage statistics with empty history."""
        stats = self.monitor.get_usage_stats()
        assert stats == {}
    
    def test_process_error_handling(self):
        """Test handling of process errors."""
        with patch('infenix.monitoring.resource_monitor.psutil.Process') as mock_process_class:
            # Mock process that raises NoSuchProcess
            mock_process = Mock()
            mock_process.cpu_percent.side_effect = Exception("Process error")
            mock_process.memory_info.side_effect = Exception("Process error")
            mock_process.num_threads.side_effect = Exception("Process error")
            mock_process_class.return_value = mock_process
            
            with patch('infenix.monitoring.resource_monitor.psutil.cpu_percent', return_value=50.0):
                with patch('infenix.monitoring.resource_monitor.psutil.virtual_memory') as mock_vm:
                    mock_memory = Mock()
                    mock_memory.percent = 60.0
                    mock_memory.used = 8 * 1024 * 1024 * 1024
                    mock_memory.available = 4 * 1024 * 1024 * 1024
                    mock_vm.return_value = mock_memory
                    
                    usage = self.monitor.get_current_usage()
                    
                    # Should handle error gracefully
                    assert usage.process_cpu_percent == 0.0
                    assert usage.process_memory_mb == 0.0
                    assert usage.process_threads == 0