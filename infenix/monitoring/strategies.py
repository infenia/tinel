#!/usr/bin/env python3
"""Strategy Pattern Implementation for Load Detection and Resource Management.

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

from abc import ABC, abstractmethod
from typing import Dict, Any
from .resource_monitor import ResourceUsage, SystemLoad
from .load_detector import LoadLevel
from .adaptive_manager import ResourceLevel


class LoadDetectionStrategy(ABC):
    """Abstract strategy for load detection."""
    
    @abstractmethod
    def detect_load_level(self, usage: ResourceUsage, load: SystemLoad) -> LoadLevel:
        """Detect load level based on usage and load data.
        
        Args:
            usage: Current resource usage
            load: Current system load
            
        Returns:
            Detected load level
        """
        pass


class ConservativeLoadStrategy(LoadDetectionStrategy):
    """Conservative load detection strategy - triggers throttling early."""
    
    def detect_load_level(self, usage: ResourceUsage, load: SystemLoad) -> LoadLevel:
        """Detect load level using conservative thresholds."""
        normalized_load = load.normalized_load_1min
        
        # More conservative thresholds
        if normalized_load >= 1.2 or usage.cpu_percent >= 70:
            return LoadLevel.OVERLOADED
        elif normalized_load >= 0.8 or usage.cpu_percent >= 50:
            return LoadLevel.HEAVY
        elif normalized_load >= 0.4 or usage.cpu_percent >= 30:
            return LoadLevel.MODERATE
        elif normalized_load >= 0.2 or usage.cpu_percent >= 15:
            return LoadLevel.LIGHT
        else:
            return LoadLevel.IDLE


class AggressiveLoadStrategy(LoadDetectionStrategy):
    """Aggressive load detection strategy - allows higher resource usage."""
    
    def detect_load_level(self, usage: ResourceUsage, load: SystemLoad) -> LoadLevel:
        """Detect load level using aggressive thresholds."""
        normalized_load = load.normalized_load_1min
        
        # More aggressive thresholds
        if normalized_load >= 2.5 or usage.cpu_percent >= 95:
            return LoadLevel.OVERLOADED
        elif normalized_load >= 2.0 or usage.cpu_percent >= 85:
            return LoadLevel.HEAVY
        elif normalized_load >= 1.5 or usage.cpu_percent >= 70:
            return LoadLevel.MODERATE
        elif normalized_load >= 0.8 or usage.cpu_percent >= 40:
            return LoadLevel.LIGHT
        else:
            return LoadLevel.IDLE


class AdaptiveLoadStrategy(LoadDetectionStrategy):
    """Adaptive load detection that adjusts based on system characteristics."""
    
    def __init__(self):
        self._cpu_count = load.cpu_count if 'load' in locals() else 1
        self._memory_gb = 8  # Default, should be detected
        
    def detect_load_level(self, usage: ResourceUsage, load: SystemLoad) -> LoadLevel:
        """Detect load level using adaptive thresholds based on system specs."""
        normalized_load = load.normalized_load_1min
        
        # Adjust thresholds based on CPU count
        cpu_factor = min(2.0, max(0.5, load.cpu_count / 4.0))
        
        # Adjust thresholds based on memory
        memory_factor = min(2.0, max(0.5, usage.memory_available_mb / 4096))
        
        base_load_threshold = 1.0 * cpu_factor
        base_cpu_threshold = 60.0 * memory_factor
        
        if (normalized_load >= base_load_threshold * 2.0 or 
            usage.cpu_percent >= base_cpu_threshold * 1.4):
            return LoadLevel.OVERLOADED
        elif (normalized_load >= base_load_threshold * 1.5 or 
              usage.cpu_percent >= base_cpu_threshold * 1.2):
            return LoadLevel.HEAVY
        elif (normalized_load >= base_load_threshold or 
              usage.cpu_percent >= base_cpu_threshold):
            return LoadLevel.MODERATE
        elif (normalized_load >= base_load_threshold * 0.5 or 
              usage.cpu_percent >= base_cpu_threshold * 0.5):
            return LoadLevel.LIGHT
        else:
            return LoadLevel.IDLE


class ResourceManagementStrategy(ABC):
    """Abstract strategy for resource management."""
    
    @abstractmethod
    def get_settings(self, level: ResourceLevel) -> Dict[str, Any]:
        """Get resource management settings for a given level.
        
        Args:
            level: Current resource level
            
        Returns:
            Dictionary with management settings
        """
        pass


class DefaultResourceStrategy(ResourceManagementStrategy):
    """Default resource management strategy."""
    
    def get_settings(self, level: ResourceLevel) -> Dict[str, Any]:
        """Get default settings based on resource level."""
        settings_map = {
            ResourceLevel.LOW: {
                "max_concurrent_operations": 8,
                "buffer_size": 8192,
                "processing_delay": 0.0,
                "enable_caching": True,
                "log_level": "DEBUG",
                "gc_threshold": 1000
            },
            ResourceLevel.NORMAL: {
                "max_concurrent_operations": 4,
                "buffer_size": 4096,
                "processing_delay": 0.1,
                "enable_caching": True,
                "log_level": "INFO",
                "gc_threshold": 500
            },
            ResourceLevel.HIGH: {
                "max_concurrent_operations": 2,
                "buffer_size": 2048,
                "processing_delay": 0.2,
                "enable_caching": False,
                "log_level": "WARNING",
                "gc_threshold": 100
            },
            ResourceLevel.CRITICAL: {
                "max_concurrent_operations": 1,
                "buffer_size": 1024,
                "processing_delay": 0.5,
                "enable_caching": False,
                "log_level": "ERROR",
                "gc_threshold": 50
            }
        }
        
        return settings_map.get(level, settings_map[ResourceLevel.NORMAL])


class MemoryOptimizedStrategy(ResourceManagementStrategy):
    """Resource management strategy optimized for low-memory systems."""
    
    def get_settings(self, level: ResourceLevel) -> Dict[str, Any]:
        """Get memory-optimized settings."""
        base_settings = DefaultResourceStrategy().get_settings(level)
        
        # Reduce buffer sizes and enable more aggressive garbage collection
        base_settings["buffer_size"] = base_settings["buffer_size"] // 2
        base_settings["max_concurrent_operations"] = max(1, base_settings["max_concurrent_operations"] // 2)
        base_settings["gc_threshold"] = base_settings["gc_threshold"] // 2
        base_settings["enable_caching"] = False  # Disable caching to save memory
        
        return base_settings