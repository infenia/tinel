#!/usr/bin/env python3
"""Tests for Adaptive Resource Manager.

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
from unittest.mock import Mock, patch
import pytest

from infenix.monitoring.resource_monitor import ResourceMonitor, ResourceUsage, SystemLoad
from infenix.monitoring.adaptive_manager import (
    AdaptiveResourceManager, 
    AdaptiveSettings, 
    ResourceLevel
)


class TestAdaptiveResourceManager:
    """Test cases for AdaptiveResourceManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = Mock(spec=ResourceMonitor)
        self.settings = AdaptiveSettings(
            cpu_low_threshold=25.0,
            cpu_normal_threshold=50.0,
            cpu_high_threshold=75.0,
            cpu_critical_threshold=90.0,
            adaptation_window=3,
            stability_threshold=2
        )
        self.manager = AdaptiveResourceManager(self.monitor, self.settings)
    
    def test_initialization(self):
        """Test manager initialization."""
        assert self.manager.monitor == self.monitor
        assert self.manager.settings == self.settings
        assert self.manager._current_level == ResourceLevel.NORMAL
        assert len(self.manager._level_history) == 0
        
        # Verify callback was registered with monitor
        self.monitor.add_callback.assert_called_once()
    
    def test_determine_resource_level_low(self):
        """Test resource level determination for low usage."""
        usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=20.0,
            memory_percent=25.0,
            memory_used_mb=2000.0,
            memory_available_mb=6000.0,
            process_cpu_percent=5.0,
            process_memory_mb=100.0,
            process_threads=2
        )
        
        load = SystemLoad(
            load_1min=0.4,
            load_5min=0.3,
            load_15min=0.2,
            cpu_count=4,
            normalized_load_1min=0.1,
            normalized_load_5min=0.075,
            normalized_load_15min=0.05
        )
        
        level = self.manager.determine_resource_level(usage, load)
        assert level == ResourceLevel.LOW
    
    def test_determine_resource_level_normal(self):
        """Test resource level determination for normal usage."""
        usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=40.0,
            memory_percent=45.0,
            memory_used_mb=4000.0,
            memory_available_mb=4000.0,
            process_cpu_percent=10.0,
            process_memory_mb=200.0,
            process_threads=3
        )
        
        load = SystemLoad(
            load_1min=4.0,
            load_5min=3.8,
            load_15min=3.5,
            cpu_count=4,
            normalized_load_1min=1.0,
            normalized_load_5min=0.95,
            normalized_load_15min=0.875
        )
        
        level = self.manager.determine_resource_level(usage, load)
        assert level == ResourceLevel.NORMAL
    
    def test_determine_resource_level_high(self):
        """Test resource level determination for high usage."""
        usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=80.0,
            memory_percent=70.0,
            memory_used_mb=6000.0,
            memory_available_mb=2000.0,
            process_cpu_percent=20.0,
            process_memory_mb=400.0,
            process_threads=5
        )
        
        load = SystemLoad(
            load_1min=3.0,
            load_5min=2.8,
            load_15min=2.5,
            cpu_count=4,
            normalized_load_1min=0.75,
            normalized_load_5min=0.7,
            normalized_load_15min=0.625
        )
        
        level = self.manager.determine_resource_level(usage, load)
        assert level == ResourceLevel.HIGH
    
    def test_determine_resource_level_critical(self):
        """Test resource level determination for critical usage."""
        usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=95.0,
            memory_percent=92.0,
            memory_used_mb=7500.0,
            memory_available_mb=500.0,
            process_cpu_percent=30.0,
            process_memory_mb=600.0,
            process_threads=8
        )
        
        load = SystemLoad(
            load_1min=8.0,
            load_5min=7.5,
            load_15min=7.0,
            cpu_count=4,
            normalized_load_1min=2.0,
            normalized_load_5min=1.875,
            normalized_load_15min=1.75
        )
        
        level = self.manager.determine_resource_level(usage, load)
        assert level == ResourceLevel.CRITICAL
    
    def test_determine_resource_level_mixed(self):
        """Test resource level determination with mixed metrics."""
        # High CPU, normal memory, low load - should be HIGH (highest)
        usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=80.0,  # HIGH
            memory_percent=45.0,  # NORMAL
            memory_used_mb=4000.0,
            memory_available_mb=4000.0,
            process_cpu_percent=15.0,
            process_memory_mb=300.0,
            process_threads=4
        )
        
        load = SystemLoad(
            load_1min=0.8,
            load_5min=0.7,
            load_15min=0.6,
            cpu_count=4,
            normalized_load_1min=0.2,  # LOW
            normalized_load_5min=0.175,
            normalized_load_15min=0.15
        )
        
        level = self.manager.determine_resource_level(usage, load)
        assert level == ResourceLevel.HIGH
    
    def test_callback_management(self):
        """Test callback management for level changes."""
        callback_low = Mock()
        callback_high = Mock()
        
        # Add callbacks
        self.manager.add_level_change_callback(ResourceLevel.LOW, callback_low)
        self.manager.add_level_change_callback(ResourceLevel.HIGH, callback_high)
        
        assert len(self.manager._level_change_callbacks[ResourceLevel.LOW]) == 1
        assert len(self.manager._level_change_callbacks[ResourceLevel.HIGH]) == 1
        
        # Remove callback
        self.manager.remove_level_change_callback(ResourceLevel.LOW, callback_low)
        assert len(self.manager._level_change_callbacks[ResourceLevel.LOW]) == 0
    
    def test_level_change_stability(self):
        """Test that level changes require stability."""
        # Mock get_system_load to return consistent load
        self.monitor.get_system_load.return_value = SystemLoad(
            load_1min=1.0, load_5min=1.0, load_15min=1.0,
            cpu_count=4, normalized_load_1min=0.25,
            normalized_load_5min=0.25, normalized_load_15min=0.25
        )
        
        # Create usage that would indicate HIGH level
        high_usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=80.0,
            memory_percent=70.0,
            memory_used_mb=6000.0,
            memory_available_mb=2000.0,
            process_cpu_percent=20.0,
            process_memory_mb=400.0,
            process_threads=5
        )
        
        # First update - should not change level yet
        self.manager._on_resource_update(high_usage)
        assert self.manager._current_level == ResourceLevel.NORMAL
        assert len(self.manager._level_history) == 1
        
        # Second update - should change level (stability_threshold=2)
        self.manager._on_resource_update(high_usage)
        assert self.manager._current_level == ResourceLevel.HIGH
        assert len(self.manager._level_history) == 2
    
    def test_adaptive_settings_by_level(self):
        """Test adaptive settings for different resource levels."""
        # Test LOW level settings
        self.manager._current_level = ResourceLevel.LOW
        settings = self.manager.get_adaptive_settings()
        assert settings["max_concurrent_operations"] == 8
        assert settings["buffer_size"] == 8192
        assert settings["processing_delay"] == 0.0
        assert settings["enable_caching"] is True
        assert settings["log_level"] == "DEBUG"
        
        # Test NORMAL level settings
        self.manager._current_level = ResourceLevel.NORMAL
        settings = self.manager.get_adaptive_settings()
        assert settings["max_concurrent_operations"] == 4
        assert settings["buffer_size"] == 4096
        assert settings["processing_delay"] == 0.1
        assert settings["enable_caching"] is True
        assert settings["log_level"] == "INFO"
        
        # Test HIGH level settings
        self.manager._current_level = ResourceLevel.HIGH
        settings = self.manager.get_adaptive_settings()
        assert settings["max_concurrent_operations"] == 2
        assert settings["buffer_size"] == 2048
        assert settings["processing_delay"] == 0.2
        assert settings["enable_caching"] is False
        assert settings["log_level"] == "WARNING"
        
        # Test CRITICAL level settings
        self.manager._current_level = ResourceLevel.CRITICAL
        settings = self.manager.get_adaptive_settings()
        assert settings["max_concurrent_operations"] == 1
        assert settings["buffer_size"] == 1024
        assert settings["processing_delay"] == 0.5
        assert settings["enable_caching"] is False
        assert settings["log_level"] == "ERROR"
    
    def test_get_status(self):
        """Test status reporting."""
        # Mock current usage and load
        current_usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=60.0,
            memory_percent=55.0,
            memory_used_mb=5000.0,
            memory_available_mb=3000.0,
            process_cpu_percent=15.0,
            process_memory_mb=300.0,
            process_threads=4
        )
        
        current_load = SystemLoad(
            load_1min=2.5,
            load_5min=2.2,
            load_15min=2.0,
            cpu_count=4,
            normalized_load_1min=0.625,
            normalized_load_5min=0.55,
            normalized_load_15min=0.5
        )
        
        self.monitor.get_current_usage.return_value = current_usage
        self.monitor.get_system_load.return_value = current_load
        
        # Add some history
        self.manager._level_history = [ResourceLevel.NORMAL, ResourceLevel.HIGH]
        self.manager._current_level = ResourceLevel.HIGH
        
        status = self.manager.get_status()
        
        assert status["current_level"] == "high"
        assert status["level_history"] == ["normal", "high"]
        assert status["current_usage"]["cpu_percent"] == 60.0
        assert status["current_usage"]["memory_percent"] == 55.0
        assert status["current_load"]["load_1min"] == 2.5
        assert status["current_load"]["normalized_load_1min"] == 0.625
        assert "adaptive_settings" in status
    
    def test_level_change_callbacks_called(self):
        """Test that level change callbacks are called."""
        callback = Mock()
        self.manager.add_level_change_callback(ResourceLevel.HIGH, callback)
        
        # Mock get_system_load
        self.monitor.get_system_load.return_value = SystemLoad(
            load_1min=1.0, load_5min=1.0, load_15min=1.0,
            cpu_count=4, normalized_load_1min=0.25,
            normalized_load_5min=0.25, normalized_load_15min=0.25
        )
        
        # Create usage that indicates HIGH level
        high_usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=80.0,
            memory_percent=70.0,
            memory_used_mb=6000.0,
            memory_available_mb=2000.0,
            process_cpu_percent=20.0,
            process_memory_mb=400.0,
            process_threads=5
        )
        
        # Trigger level change (need stability_threshold=2 calls)
        self.manager._on_resource_update(high_usage)
        self.manager._on_resource_update(high_usage)
        
        # Verify callback was called
        callback.assert_called_once()
    
    def test_callback_error_handling(self):
        """Test that callback errors don't affect the manager."""
        # Create a callback that raises an exception
        def failing_callback():
            raise Exception("Callback error")
        
        self.manager.add_level_change_callback(ResourceLevel.HIGH, failing_callback)
        
        # Mock get_system_load
        self.monitor.get_system_load.return_value = SystemLoad(
            load_1min=1.0, load_5min=1.0, load_15min=1.0,
            cpu_count=4, normalized_load_1min=0.25,
            normalized_load_5min=0.25, normalized_load_15min=0.25
        )
        
        # Create usage that indicates HIGH level
        high_usage = ResourceUsage(
            timestamp=time.time(),
            cpu_percent=80.0,
            memory_percent=70.0,
            memory_used_mb=6000.0,
            memory_available_mb=2000.0,
            process_cpu_percent=20.0,
            process_memory_mb=400.0,
            process_threads=5
        )
        
        # This should not raise an exception despite the failing callback
        self.manager._on_resource_update(high_usage)
        self.manager._on_resource_update(high_usage)
        
        # Level should still change
        assert self.manager._current_level == ResourceLevel.HIGH