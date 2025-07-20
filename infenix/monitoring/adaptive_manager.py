#!/usr/bin/env python3
"""Adaptive Resource Management for Infenix.

This module provides adaptive resource management capabilities that adjust
system behavior based on current resource usage and system load.

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
from enum import Enum
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from .resource_monitor import ResourceMonitor, ResourceUsage, SystemLoad


class ResourceLevel(Enum):
    """Resource usage levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AdaptiveSettings:
    """Adaptive resource management settings."""
    
    # CPU thresholds
    cpu_low_threshold: float = 25.0
    cpu_normal_threshold: float = 50.0
    cpu_high_threshold: float = 75.0
    cpu_critical_threshold: float = 90.0
    
    # Memory thresholds
    memory_low_threshold: float = 30.0
    memory_normal_threshold: float = 60.0
    memory_high_threshold: float = 80.0
    memory_critical_threshold: float = 95.0
    
    # Load thresholds (normalized)
    load_low_threshold: float = 0.5
    load_normal_threshold: float = 1.0
    load_high_threshold: float = 1.5
    load_critical_threshold: float = 2.0
    
    # Adaptation parameters
    adaptation_window: int = 10  # Number of samples to consider
    stability_threshold: int = 3  # Consecutive samples needed for level change


class AdaptiveResourceManager:
    """Manages adaptive resource usage based on system conditions."""
    
    def __init__(self, monitor: ResourceMonitor, settings: Optional[AdaptiveSettings] = None):
        """Initialize the adaptive resource manager.
        
        Args:
            monitor: Resource monitor instance
            settings: Adaptive settings (uses defaults if None)
        """
        self.monitor = monitor
        self.settings = settings or AdaptiveSettings()
        
        self._current_level = ResourceLevel.NORMAL
        self._level_history = []
        self._level_change_callbacks: Dict[ResourceLevel, list] = {
            level: [] for level in ResourceLevel
        }
        
        # Register for resource updates
        self.monitor.add_callback(self._on_resource_update)
        
    def add_level_change_callback(self, level: ResourceLevel, callback: Callable[[], None]) -> None:
        """Add a callback for when resource level changes to specified level.
        
        Args:
            level: Resource level to monitor
            callback: Function to call when level is reached
        """
        self._level_change_callbacks[level].append(callback)
        
    def remove_level_change_callback(self, level: ResourceLevel, callback: Callable[[], None]) -> None:
        """Remove a level change callback.
        
        Args:
            level: Resource level
            callback: Function to remove
        """
        if callback in self._level_change_callbacks[level]:
            self._level_change_callbacks[level].remove(callback)
    
    def get_current_level(self) -> ResourceLevel:
        """Get current resource level.
        
        Returns:
            Current resource usage level
        """
        return self._current_level
    
    def determine_resource_level(self, usage: ResourceUsage, load: SystemLoad) -> ResourceLevel:
        """Determine resource level based on usage and load.
        
        Args:
            usage: Current resource usage
            load: Current system load
            
        Returns:
            Determined resource level
        """
        # Check CPU usage
        cpu_level = self._get_level_from_value(
            usage.cpu_percent,
            self.settings.cpu_low_threshold,
            self.settings.cpu_normal_threshold,
            self.settings.cpu_high_threshold,
            self.settings.cpu_critical_threshold
        )
        
        # Check memory usage
        memory_level = self._get_level_from_value(
            usage.memory_percent,
            self.settings.memory_low_threshold,
            self.settings.memory_normal_threshold,
            self.settings.memory_high_threshold,
            self.settings.memory_critical_threshold
        )
        
        # Check system load
        load_level = self._get_level_from_value(
            load.normalized_load_1min,
            self.settings.load_low_threshold,
            self.settings.load_normal_threshold,
            self.settings.load_high_threshold,
            self.settings.load_critical_threshold
        )
        
        # Return the highest level among all metrics
        levels = [cpu_level, memory_level, load_level]
        level_values = {
            ResourceLevel.LOW: 0,
            ResourceLevel.NORMAL: 1,
            ResourceLevel.HIGH: 2,
            ResourceLevel.CRITICAL: 3
        }
        
        max_level = max(levels, key=lambda l: level_values[l])
        return max_level
    
    def _get_level_from_value(self, value: float, low: float, normal: float, high: float, critical: float) -> ResourceLevel:
        """Get resource level from a value and thresholds.
        
        Args:
            value: Value to check
            low: Low threshold
            normal: Normal threshold
            high: High threshold
            critical: Critical threshold
            
        Returns:
            Resource level for the value
        """
        if value >= critical:
            return ResourceLevel.CRITICAL
        elif value >= high:
            return ResourceLevel.HIGH
        elif value >= normal:
            return ResourceLevel.NORMAL
        else:
            return ResourceLevel.LOW
    
    def _on_resource_update(self, usage: ResourceUsage) -> None:
        """Handle resource usage updates.
        
        Args:
            usage: Updated resource usage
        """
        # Get current system load
        load = self.monitor.get_system_load()
        
        # Determine new level
        new_level = self.determine_resource_level(usage, load)
        
        # Add to history
        self._level_history.append(new_level)
        if len(self._level_history) > self.settings.adaptation_window:
            self._level_history.pop(0)
        
        # Check if we should change levels (need stability)
        if self._should_change_level(new_level):
            old_level = self._current_level
            self._current_level = new_level
            
            # Notify callbacks if level actually changed
            if old_level != new_level:
                self._notify_level_change(new_level)
    
    def _should_change_level(self, new_level: ResourceLevel) -> bool:
        """Check if we should change to a new level.
        
        Args:
            new_level: Proposed new level
            
        Returns:
            True if level should be changed
        """
        if len(self._level_history) < self.settings.stability_threshold:
            return False
            
        # Check if the last N samples are all the same level
        recent_levels = self._level_history[-self.settings.stability_threshold:]
        return all(level == new_level for level in recent_levels)
    
    def _notify_level_change(self, new_level: ResourceLevel) -> None:
        """Notify callbacks about level change.
        
        Args:
            new_level: New resource level
        """
        for callback in self._level_change_callbacks[new_level]:
            try:
                callback()
            except Exception:
                # Don't let callback errors affect the manager
                pass
    
    def get_adaptive_settings(self) -> Dict[str, Any]:
        """Get current adaptive settings based on resource level.
        
        Returns:
            Dictionary with adaptive settings for current level
        """
        level = self._current_level
        
        if level == ResourceLevel.LOW:
            return {
                "max_concurrent_operations": 8,
                "buffer_size": 8192,
                "processing_delay": 0.0,
                "enable_caching": True,
                "log_level": "DEBUG"
            }
        elif level == ResourceLevel.NORMAL:
            return {
                "max_concurrent_operations": 4,
                "buffer_size": 4096,
                "processing_delay": 0.1,
                "enable_caching": True,
                "log_level": "INFO"
            }
        elif level == ResourceLevel.HIGH:
            return {
                "max_concurrent_operations": 2,
                "buffer_size": 2048,
                "processing_delay": 0.2,
                "enable_caching": False,
                "log_level": "WARNING"
            }
        else:  # CRITICAL
            return {
                "max_concurrent_operations": 1,
                "buffer_size": 1024,
                "processing_delay": 0.5,
                "enable_caching": False,
                "log_level": "ERROR"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the adaptive manager.
        
        Returns:
            Dictionary with current status information
        """
        current_usage = self.monitor.get_current_usage()
        current_load = self.monitor.get_system_load()
        
        return {
            "current_level": self._current_level.value,
            "level_history": [level.value for level in self._level_history],
            "current_usage": {
                "cpu_percent": current_usage.cpu_percent,
                "memory_percent": current_usage.memory_percent,
                "process_cpu_percent": current_usage.process_cpu_percent,
                "process_memory_mb": current_usage.process_memory_mb
            },
            "current_load": {
                "load_1min": current_load.load_1min,
                "normalized_load_1min": current_load.normalized_load_1min
            },
            "adaptive_settings": self.get_adaptive_settings()
        }