#!/usr/bin/env python3
"""Tests for Load Detector and Throttler.

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
from unittest.mock import Mock, patch
import pytest

from infenix.monitoring.resource_monitor import ResourceMonitor, SystemLoad
from infenix.monitoring.load_detector import (
    LoadDetector, 
    LoadThrottler, 
    LoadLevel, 
    ThrottleSettings
)


class TestLoadDetector:
    """Test cases for LoadDetector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = Mock(spec=ResourceMonitor)
        self.settings = ThrottleSettings(
            idle_threshold=0.2,
            light_threshold=0.5,
            moderate_threshold=1.0,
            heavy_threshold=1.5,
            overload_threshold=2.0
        )
        self.detector = LoadDetector(self.monitor, self.settings)
    
    def test_initialization(self):
        """Test detector initialization."""
        assert self.detector.monitor == self.monitor
        assert self.detector.settings == self.settings
        assert self.detector._current_load_level == LoadLevel.LIGHT
    
    def test_determine_load_level_idle(self):
        """Test load level determination for idle system."""
        load = SystemLoad(
            load_1min=0.4,
            load_5min=0.3,
            load_15min=0.2,
            cpu_count=4,
            normalized_load_1min=0.1,
            normalized_load_5min=0.075,
            normalized_load_15min=0.05
        )
        
        level = self.detector.determine_load_level(load)
        assert level == LoadLevel.IDLE
    
    def test_determine_load_level_light(self):
        """Test load level determination for light load."""
        load = SystemLoad(
            load_1min=2.4,
            load_5min=2.0,
            load_15min=1.8,
            cpu_count=4,
            normalized_load_1min=0.6,
            normalized_load_5min=0.5,
            normalized_load_15min=0.45
        )
        
        level = self.detector.determine_load_level(load)
        assert level == LoadLevel.LIGHT
    
    def test_determine_load_level_moderate(self):
        """Test load level determination for moderate load."""
        load = SystemLoad(
            load_1min=4.4,
            load_5min=4.2,
            load_15min=4.0,
            cpu_count=4,
            normalized_load_1min=1.1,
            normalized_load_5min=1.05,
            normalized_load_15min=1.0
        )
        
        level = self.detector.determine_load_level(load)
        assert level == LoadLevel.MODERATE
    
    def test_determine_load_level_heavy(self):
        """Test load level determination for heavy load."""
        load = SystemLoad(
            load_1min=6.4,
            load_5min=6.2,
            load_15min=6.0,
            cpu_count=4,
            normalized_load_1min=1.6,
            normalized_load_5min=1.55,
            normalized_load_15min=1.5
        )
        
        level = self.detector.determine_load_level(load)
        assert level == LoadLevel.HEAVY
    
    def test_determine_load_level_overloaded(self):
        """Test load level determination for overloaded system."""
        load = SystemLoad(
            load_1min=10.0,
            load_5min=9.5,
            load_15min=9.0,
            cpu_count=4,
            normalized_load_1min=2.5,
            normalized_load_5min=2.375,
            normalized_load_15min=2.25
        )
        
        level = self.detector.determine_load_level(load)
        assert level == LoadLevel.OVERLOADED
    
    def test_get_current_load_level(self):
        """Test getting current load level."""
        load = SystemLoad(
            load_1min=4.4,
            load_5min=4.2,
            load_15min=4.0,
            cpu_count=4,
            normalized_load_1min=1.1,
            normalized_load_5min=1.05,
            normalized_load_15min=1.0
        )
        
        self.monitor.get_system_load.return_value = load
        
        level = self.detector.get_current_load_level()
        assert level == LoadLevel.MODERATE
        self.monitor.get_system_load.assert_called_once()
    
    def test_get_load_info(self):
        """Test getting detailed load information."""
        load = SystemLoad(
            load_1min=6.4,
            load_5min=6.2,
            load_15min=6.0,
            cpu_count=4,
            normalized_load_1min=1.6,
            normalized_load_5min=1.55,
            normalized_load_15min=1.5
        )
        
        self.monitor.get_system_load.return_value = load
        
        info = self.detector.get_load_info()
        
        assert info["load_level"] == "heavy"
        assert info["load_1min"] == 6.4
        assert info["load_5min"] == 6.2
        assert info["load_15min"] == 6.0
        assert info["normalized_load_1min"] == 1.6
        assert info["normalized_load_5min"] == 1.55
        assert info["normalized_load_15min"] == 1.5
        assert info["cpu_count"] == 4
        assert info["recommended_delay"] == self.settings.heavy_delay
        assert info["max_concurrent_ops"] == self.settings.heavy_max_ops
    
    def test_get_recommended_delay(self):
        """Test getting recommended delay for different load levels."""
        assert self.detector.get_recommended_delay(LoadLevel.IDLE) == self.settings.idle_delay
        assert self.detector.get_recommended_delay(LoadLevel.LIGHT) == self.settings.light_delay
        assert self.detector.get_recommended_delay(LoadLevel.MODERATE) == self.settings.moderate_delay
        assert self.detector.get_recommended_delay(LoadLevel.HEAVY) == self.settings.heavy_delay
        assert self.detector.get_recommended_delay(LoadLevel.OVERLOADED) == self.settings.overload_delay
    
    def test_get_max_concurrent_operations(self):
        """Test getting max concurrent operations for different load levels."""
        assert self.detector.get_max_concurrent_operations(LoadLevel.IDLE) == self.settings.idle_max_ops
        assert self.detector.get_max_concurrent_operations(LoadLevel.LIGHT) == self.settings.light_max_ops
        assert self.detector.get_max_concurrent_operations(LoadLevel.MODERATE) == self.settings.moderate_max_ops
        assert self.detector.get_max_concurrent_operations(LoadLevel.HEAVY) == self.settings.heavy_max_ops
        assert self.detector.get_max_concurrent_operations(LoadLevel.OVERLOADED) == self.settings.overload_max_ops
    
    def test_is_overloaded(self):
        """Test overload detection."""
        # Mock overloaded system
        overloaded_load = SystemLoad(
            load_1min=10.0, load_5min=9.5, load_15min=9.0,
            cpu_count=4, normalized_load_1min=2.5,
            normalized_load_5min=2.375, normalized_load_15min=2.25
        )
        self.monitor.get_system_load.return_value = overloaded_load
        assert self.detector.is_overloaded() is True
        
        # Mock normal system
        normal_load = SystemLoad(
            load_1min=2.0, load_5min=1.8, load_15min=1.5,
            cpu_count=4, normalized_load_1min=0.5,
            normalized_load_5min=0.45, normalized_load_15min=0.375
        )
        self.monitor.get_system_load.return_value = normal_load
        assert self.detector.is_overloaded() is False
    
    def test_should_throttle(self):
        """Test throttling recommendation."""
        # Mock heavy load (should throttle)
        heavy_load = SystemLoad(
            load_1min=6.0, load_5min=5.8, load_15min=5.5,
            cpu_count=4, normalized_load_1min=1.5,
            normalized_load_5min=1.45, normalized_load_15min=1.375
        )
        self.monitor.get_system_load.return_value = heavy_load
        assert self.detector.should_throttle() is True
        
        # Mock light load (should not throttle)
        light_load = SystemLoad(
            load_1min=1.0, load_5min=0.8, load_15min=0.6,
            cpu_count=4, normalized_load_1min=0.25,
            normalized_load_5min=0.2, normalized_load_15min=0.15
        )
        self.monitor.get_system_load.return_value = light_load
        assert self.detector.should_throttle() is False
    
    def test_callback_management(self):
        """Test callback management for load changes."""
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        self.detector.add_load_change_callback(LoadLevel.HEAVY, callback1)
        self.detector.add_load_change_callback(LoadLevel.HEAVY, callback2)
        
        assert len(self.detector._load_callbacks[LoadLevel.HEAVY]) == 2
        
        # Remove callback
        self.detector.remove_load_change_callback(LoadLevel.HEAVY, callback1)
        assert len(self.detector._load_callbacks[LoadLevel.HEAVY]) == 1
        assert callback2 in self.detector._load_callbacks[LoadLevel.HEAVY]


class TestLoadThrottler:
    """Test cases for LoadThrottler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = Mock(spec=LoadDetector)
        self.throttler = LoadThrottler(self.detector)
    
    def test_initialization(self):
        """Test throttler initialization."""
        assert self.throttler.detector == self.detector
        assert self.throttler._operation_count == 0
        assert isinstance(self.throttler._operation_lock, type(threading.Lock()))
    
    @patch('time.sleep')
    def test_throttle_if_needed(self, mock_sleep):
        """Test throttling when needed."""
        # Mock detector to return delay
        self.detector.get_recommended_delay.return_value = 0.1
        
        self.throttler.throttle_if_needed()
        
        self.detector.get_recommended_delay.assert_called_once()
        mock_sleep.assert_called_once_with(0.1)
    
    @patch('time.sleep')
    def test_throttle_if_needed_no_delay(self, mock_sleep):
        """Test no throttling when delay is zero."""
        # Mock detector to return no delay
        self.detector.get_recommended_delay.return_value = 0.0
        
        self.throttler.throttle_if_needed()
        
        self.detector.get_recommended_delay.assert_called_once()
        mock_sleep.assert_not_called()
    
    def test_operation_management(self):
        """Test operation count management."""
        # Mock max operations
        self.detector.get_max_concurrent_operations.return_value = 3
        
        # Initially should be able to start operations
        assert self.throttler.can_start_operation() is True
        assert self.throttler.get_operation_count() == 0
        
        # Start operations
        assert self.throttler.start_operation() is True
        assert self.throttler.get_operation_count() == 1
        
        assert self.throttler.start_operation() is True
        assert self.throttler.get_operation_count() == 2
        
        assert self.throttler.start_operation() is True
        assert self.throttler.get_operation_count() == 3
        
        # Should not be able to start more operations
        assert self.throttler.can_start_operation() is False
        assert self.throttler.start_operation() is False
        assert self.throttler.get_operation_count() == 3
        
        # Finish an operation
        self.throttler.finish_operation()
        assert self.throttler.get_operation_count() == 2
        assert self.throttler.can_start_operation() is True
    
    def test_finish_operation_underflow_protection(self):
        """Test that finishing operations doesn't go below zero."""
        assert self.throttler.get_operation_count() == 0
        
        # Try to finish operation when count is already 0
        self.throttler.finish_operation()
        assert self.throttler.get_operation_count() == 0
    
    def test_wait_for_capacity(self):
        """Test waiting for capacity."""
        # Mock max operations to 1
        self.detector.get_max_concurrent_operations.return_value = 1
        
        # Start one operation to fill capacity
        assert self.throttler.start_operation() is True
        
        # Start a thread that will free capacity after a short delay
        def free_capacity():
            time.sleep(0.1)
            self.throttler.finish_operation()
        
        thread = threading.Thread(target=free_capacity)
        thread.start()
        
        # Wait for capacity should succeed
        start_time = time.time()
        result = self.throttler.wait_for_capacity(timeout=0.5)
        end_time = time.time()
        
        assert result is True
        assert 0.05 < (end_time - start_time) < 0.3  # Should wait around 0.1 seconds
        
        thread.join()
    
    def test_wait_for_capacity_timeout(self):
        """Test waiting for capacity with timeout."""
        # Mock max operations to 1
        self.detector.get_max_concurrent_operations.return_value = 1
        
        # Start one operation to fill capacity
        assert self.throttler.start_operation() is True
        
        # Wait for capacity should timeout
        result = self.throttler.wait_for_capacity(timeout=0.1)
        assert result is False
    
    def test_get_throttle_stats(self):
        """Test getting throttle statistics."""
        # Mock detector responses
        load_info = {
            "load_level": "moderate",
            "load_1min": 3.0,
            "normalized_load_1min": 0.75
        }
        self.detector.get_load_info.return_value = load_info
        self.detector.get_max_concurrent_operations.return_value = 4
        self.detector.get_recommended_delay.return_value = 0.05
        self.detector.should_throttle.return_value = False
        
        # Start some operations
        self.throttler.start_operation()
        self.throttler.start_operation()
        
        stats = self.throttler.get_throttle_stats()
        
        assert stats["current_operations"] == 2
        assert stats["max_operations"] == 4
        assert stats["recommended_delay"] == 0.05
        assert stats["load_info"] == load_info
        assert stats["is_throttling"] is False
        assert "last_throttle_time" in stats
    
    @patch('time.sleep')
    def test_adaptive_sleep(self, mock_sleep):
        """Test adaptive sleep based on load level."""
        base_delay = 0.1
        
        # Test different load levels
        test_cases = [
            (LoadLevel.IDLE, 0),  # No sleep for idle
            (LoadLevel.LIGHT, base_delay),
            (LoadLevel.MODERATE, base_delay * 1.5),
            (LoadLevel.HEAVY, base_delay * 2),
            (LoadLevel.OVERLOADED, base_delay * 4)
        ]
        
        for load_level, expected_delay in test_cases:
            mock_sleep.reset_mock()
            self.detector.get_current_load_level.return_value = load_level
            
            self.throttler.adaptive_sleep(base_delay)
            
            if expected_delay > 0:
                mock_sleep.assert_called_once_with(expected_delay)
            else:
                mock_sleep.assert_not_called()
    
    def test_thread_safety(self):
        """Test thread safety of operation management."""
        # Mock max operations
        self.detector.get_max_concurrent_operations.return_value = 10
        
        # Start multiple threads that start and finish operations
        def worker():
            for _ in range(100):
                if self.throttler.start_operation():
                    time.sleep(0.001)  # Simulate work
                    self.throttler.finish_operation()
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All operations should be finished
        assert self.throttler.get_operation_count() == 0