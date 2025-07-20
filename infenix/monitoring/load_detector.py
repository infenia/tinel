#!/usr/bin/env python3
"""Load Detection and Throttling for Infenix.

This module provides system load detection and adaptive throttling capabilities
to prevent system overload during intensive operations.

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
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .resource_monitor import ResourceMonitor, SystemLoad


class LoadLevel(Enum):
    """System load levels."""
    IDLE = "idle"
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    OVERLOADED = "overloaded"


@dataclass
class ThrottleSettings:
    """Throttling settings for different load levels."""
    
    # Load thresholds (normalized load average)
    idle_threshold: float = 0.2
    light_threshold: float = 0.5
    moderate_threshold: float = 1.0
    heavy_threshold: float = 1.5
    overload_threshold: float = 2.0
    
    # Throttling delays (seconds)
    idle_delay: float = 0.0
    light_delay: float = 0.01
    moderate_delay: float = 0.05
    heavy_delay: float = 0.1
    overload_delay: float = 0.25
    
    # Operation limits
    idle_max_ops: int = 10
    light_max_ops: int = 8
    moderate_max_ops: int = 4
    heavy_max_ops: int = 2
    overload_max_ops: int = 1


class LoadDetector:
    """Detects system load levels and provides load information."""
    
    def __init__(self, monitor: ResourceMonitor, settings: Optional[ThrottleSettings] = None):
        """Initialize the load detector.
        
        Args:
            monitor: Resource monitor instance
            settings: Throttle settings (uses defaults if None)
        """
        self.monitor = monitor
        self.settings = settings or ThrottleSettings()
        
        self._current_load_level = LoadLevel.LIGHT
        self._load_history = []
        self._load_callbacks: Dict[LoadLevel, list] = {
            level: [] for level in LoadLevel
        }
        
    def add_load_change_callback(self, level: LoadLevel, callback: Callable[[], None]) -> None:
        """Add a callback for when load level changes to specified level.
        
        Args:
            level: Load level to monitor
            callback: Function to call when level is reached
        """
        self._load_callbacks[level].append(callback)
        
    def remove_load_change_callback(self, level: LoadLevel, callback: Callable[[], None]) -> None:
        """Remove a load change callback.
        
        Args:
            level: Load level
            callback: Function to remove
        """
        if callback in self._load_callbacks[level]:
            self._load_callbacks[level].remove(callback)
    
    def get_current_load_level(self) -> LoadLevel:
        """Get current load level.
        
        Returns:
            Current system load level
        """
        load = self.monitor.get_system_load()
        return self.determine_load_level(load)
    
    def determine_load_level(self, load: SystemLoad) -> LoadLevel:
        """Determine load level from system load.
        
        Args:
            load: System load information
            
        Returns:
            Determined load level
        """
        normalized_load = load.normalized_load_1min
        
        if normalized_load >= self.settings.overload_threshold:
            return LoadLevel.OVERLOADED
        elif normalized_load >= self.settings.heavy_threshold:
            return LoadLevel.HEAVY
        elif normalized_load >= self.settings.moderate_threshold:
            return LoadLevel.MODERATE
        elif normalized_load >= self.settings.light_threshold:
            return LoadLevel.LIGHT
        else:
            return LoadLevel.IDLE
    
    def get_load_info(self) -> Dict[str, Any]:
        """Get detailed load information.
        
        Returns:
            Dictionary with load information
        """
        load = self.monitor.get_system_load()
        level = self.determine_load_level(load)
        
        return {
            "load_level": level.value,
            "load_1min": load.load_1min,
            "load_5min": load.load_5min,
            "load_15min": load.load_15min,
            "normalized_load_1min": load.normalized_load_1min,
            "normalized_load_5min": load.normalized_load_5min,
            "normalized_load_15min": load.normalized_load_15min,
            "cpu_count": load.cpu_count,
            "recommended_delay": self.get_recommended_delay(level),
            "max_concurrent_ops": self.get_max_concurrent_operations(level)
        }
    
    def get_recommended_delay(self, level: Optional[LoadLevel] = None) -> float:
        """Get recommended delay for current or specified load level.
        
        Args:
            level: Load level (uses current if None)
            
        Returns:
            Recommended delay in seconds
        """
        if level is None:
            level = self.get_current_load_level()
            
        delay_map = {
            LoadLevel.IDLE: self.settings.idle_delay,
            LoadLevel.LIGHT: self.settings.light_delay,
            LoadLevel.MODERATE: self.settings.moderate_delay,
            LoadLevel.HEAVY: self.settings.heavy_delay,
            LoadLevel.OVERLOADED: self.settings.overload_delay
        }
        
        return delay_map.get(level, self.settings.moderate_delay)
    
    def get_max_concurrent_operations(self, level: Optional[LoadLevel] = None) -> int:
        """Get maximum concurrent operations for current or specified load level.
        
        Args:
            level: Load level (uses current if None)
            
        Returns:
            Maximum number of concurrent operations
        """
        if level is None:
            level = self.get_current_load_level()
            
        ops_map = {
            LoadLevel.IDLE: self.settings.idle_max_ops,
            LoadLevel.LIGHT: self.settings.light_max_ops,
            LoadLevel.MODERATE: self.settings.moderate_max_ops,
            LoadLevel.HEAVY: self.settings.heavy_max_ops,
            LoadLevel.OVERLOADED: self.settings.overload_max_ops
        }
        
        return ops_map.get(level, self.settings.moderate_max_ops)
    
    def is_overloaded(self) -> bool:
        """Check if system is currently overloaded.
        
        Returns:
            True if system is overloaded
        """
        return self.get_current_load_level() == LoadLevel.OVERLOADED
    
    def should_throttle(self) -> bool:
        """Check if operations should be throttled.
        
        Returns:
            True if throttling is recommended
        """
        level = self.get_current_load_level()
        return level in [LoadLevel.HEAVY, LoadLevel.OVERLOADED]


class LoadThrottler:
    """Provides throttling capabilities based on system load."""
    
    def __init__(self, detector: LoadDetector):
        """Initialize the load throttler.
        
        Args:
            detector: Load detector instance
        """
        self.detector = detector
        self._operation_count = 0
        self._operation_lock = threading.Lock()
        self._last_throttle_time = 0.0
        
    def throttle_if_needed(self) -> None:
        """Apply throttling delay if needed based on current load."""
        delay = self.detector.get_recommended_delay()
        if delay > 0:
            time.sleep(delay)
            self._last_throttle_time = time.time()
    
    def can_start_operation(self) -> bool:
        """Check if a new operation can be started.
        
        Returns:
            True if operation can be started
        """
        max_ops = self.detector.get_max_concurrent_operations()
        
        with self._operation_lock:
            return self._operation_count < max_ops
    
    def start_operation(self) -> bool:
        """Start a new operation if possible.
        
        Returns:
            True if operation was started
        """
        max_ops = self.detector.get_max_concurrent_operations()
        
        with self._operation_lock:
            if self._operation_count < max_ops:
                self._operation_count += 1
                return True
            return False
    
    def finish_operation(self) -> None:
        """Mark an operation as finished."""
        with self._operation_lock:
            if self._operation_count > 0:
                self._operation_count -= 1
    
    def get_operation_count(self) -> int:
        """Get current number of active operations.
        
        Returns:
            Number of active operations
        """
        with self._operation_lock:
            return self._operation_count
    
    def wait_for_capacity(self, timeout: Optional[float] = None) -> bool:
        """Wait until there's capacity for a new operation.
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
            
        Returns:
            True if capacity became available, False if timeout
        """
        start_time = time.time()
        
        while not self.can_start_operation():
            if timeout and (time.time() - start_time) > timeout:
                return False
                
            time.sleep(0.1)  # Small delay between checks
            
        return True
    
    def get_throttle_stats(self) -> Dict[str, Any]:
        """Get throttling statistics.
        
        Returns:
            Dictionary with throttling statistics
        """
        load_info = self.detector.get_load_info()
        
        return {
            "current_operations": self.get_operation_count(),
            "max_operations": self.detector.get_max_concurrent_operations(),
            "recommended_delay": self.detector.get_recommended_delay(),
            "last_throttle_time": self._last_throttle_time,
            "load_info": load_info,
            "is_throttling": self.detector.should_throttle()
        }
    
    def adaptive_sleep(self, base_delay: float = 0.1) -> None:
        """Sleep with adaptive delay based on system load.
        
        Args:
            base_delay: Base delay to use when system is not loaded
        """
        load_level = self.detector.get_current_load_level()
        
        if load_level == LoadLevel.OVERLOADED:
            time.sleep(base_delay * 4)
        elif load_level == LoadLevel.HEAVY:
            time.sleep(base_delay * 2)
        elif load_level == LoadLevel.MODERATE:
            time.sleep(base_delay * 1.5)
        elif load_level == LoadLevel.LIGHT:
            time.sleep(base_delay)
        # No sleep for IDLE level