#!/usr/bin/env python3
"""Pattern Detector Module.

This module provides pattern detection capabilities for hardware issues
and correlates hardware events with log entries.

Copyright 2024 Infenia Private Limited

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

import re
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Pattern, Tuple

from ..interfaces import LogEntry, SystemInterface
from ..system import LinuxSystemInterface


# Constants for severity levels
class Severity:
    """Severity level constants."""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


# Constants for issue types
class IssueType:
    """Issue type constants."""
    MACHINE_CHECK_EXCEPTION = 'machine_check_exception'
    THERMAL_THROTTLING = 'thermal_throttling'
    FREQUENCY_SCALING = 'frequency_scaling'
    OUT_OF_MEMORY = 'out_of_memory'
    MEMORY_CORRUPTION = 'memory_corruption'
    SEGMENTATION_FAULT = 'segmentation_fault'
    IO_ERROR = 'io_error'
    SMART_ERROR = 'smart_error'
    FILESYSTEM_CORRUPTION = 'filesystem_corruption'


class PatternConfig:
    """Configuration class for pattern detection rules."""
    
    # Classification rules as class constants for better maintainability
    KERNEL_WARNING_PATTERNS = {
        Severity.HIGH: [
            'rcu stall', 'soft lockup', 'hard lockup', 'nmi watchdog',
            'call trace', 'stack trace', 'backtrace'
        ],
        Severity.MEDIUM: [
            'deprecated', 'tainted', 'firmware', 'microcode',
            'temperature', 'thermal', 'voltage'
        ]
    }
    
    KERNEL_ERROR_PATTERNS = {
        Severity.CRITICAL: [
            'fatal', 'critical', 'severe', 'corruption',
            'unable to handle', 'null pointer', 'segfault'
        ],
        Severity.HIGH: [
            'i/o error', 'timeout', 'failed', 'cannot',
            'invalid', 'bad', 'broken'
        ]
    }


class KernelMessageClassifier:
    """Strategy class for classifying kernel messages."""
    
    @classmethod
    @lru_cache(maxsize=1000)
    def classify_warning_severity(cls, message: str) -> str:
        """Classify kernel warning severity based on message content."""
        message_lower = message.lower()
        
        for severity, keywords in PatternConfig.KERNEL_WARNING_PATTERNS.items():
            if any(keyword in message_lower for keyword in keywords):
                return severity
        
        return Severity.LOW
    
    @classmethod
    @lru_cache(maxsize=1000)
    def classify_error_severity(cls, message: str) -> str:
        """Classify kernel error severity based on message content."""
        message_lower = message.lower()
        
        for severity, keywords in PatternConfig.KERNEL_ERROR_PATTERNS.items():
            if any(keyword in message_lower for keyword in keywords):
                return severity
        
        return Severity.MEDIUM


class PatternDetector:
    """Log pattern detector for hardware issues."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize pattern detector.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # Initialize pattern configuration
        self.config = PatternConfig()
        self.classifier = KernelMessageClassifier()
    
    def detect_hardware_patterns(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Detect patterns indicating hardware issues.
        
        Args:
            entries: List of log entries to analyze
            
        Returns:
            Dictionary containing detected hardware patterns
            
        Raises:
            ValueError: If entries is None or empty
            TypeError: If entries contains invalid types
        """
        if not entries:
            raise ValueError("Entries list cannot be None or empty")
        
        if not all(isinstance(entry, LogEntry) for entry in entries):
            raise TypeError("All entries must be LogEntry instances")
        patterns = {
            'cpu_issues': [],
            'memory_issues': [],
            'storage_issues': [],
            'network_issues': [],
            'graphics_issues': [],
            'power_issues': [],
            'thermal_issues': [],
            'usb_issues': [],
            'pci_issues': []
        }
        
        # Group entries by category for analysis
        categorized_entries = self._categorize_entries(entries)
        
        # Detect CPU issues
        patterns['cpu_issues'] = self._detect_cpu_issues(categorized_entries.get('cpu', []))
        
        # Detect memory issues
        patterns['memory_issues'] = self._detect_memory_issues(categorized_entries.get('memory', []))
        
        # Detect storage issues
        patterns['storage_issues'] = self._detect_storage_issues(categorized_entries.get('storage', []))
        
        # Detect network issues
        patterns['network_issues'] = self._detect_network_issues(categorized_entries.get('network', []))
        
        # Detect graphics issues
        patterns['graphics_issues'] = self._detect_graphics_issues(categorized_entries.get('graphics', []))
        
        # Detect power issues
        patterns['power_issues'] = self._detect_power_issues(categorized_entries.get('power', []))
        
        # Detect thermal issues
        patterns['thermal_issues'] = self._detect_thermal_issues(categorized_entries.get('thermal', []))
        
        # Detect USB issues
        patterns['usb_issues'] = self._detect_usb_issues(categorized_entries.get('usb', []))
        
        # Detect PCI issues
        patterns['pci_issues'] = self._detect_pci_issues(categorized_entries.get('pci', []))
        
        return patterns
    
    def detect_kernel_patterns(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Detect patterns indicating kernel issues.
        
        Args:
            entries: List of log entries to analyze
            
        Returns:
            Dictionary containing detected kernel patterns
        """
        patterns = {
            'kernel_panics': [],
            'oops': [],
            'warnings': [],
            'errors': [],
            'deadlocks': [],
            'memory_corruption': [],
            'driver_issues': []
        }
        
        # Filter kernel entries
        kernel_entries = [entry for entry in entries if entry.facility == 'kernel' or 'kernel' in entry.source.lower()]
        
        # Detect kernel panics
        patterns['kernel_panics'] = self._detect_kernel_panics(kernel_entries)
        
        # Detect kernel oops
        patterns['oops'] = self._detect_kernel_oops(kernel_entries)
        
        # Detect kernel warnings
        patterns['warnings'] = self._detect_kernel_warnings(kernel_entries)
        
        # Detect kernel errors
        patterns['errors'] = self._detect_kernel_errors(kernel_entries)
        
        # Detect deadlocks
        patterns['deadlocks'] = self._detect_deadlocks(kernel_entries)
        
        # Detect memory corruption
        patterns['memory_corruption'] = self._detect_memory_corruption(kernel_entries)
        
        # Detect driver issues
        patterns['driver_issues'] = self._detect_driver_issues(kernel_entries)
        
        return patterns
    
    def correlate_hardware_events(self, entries: List[LogEntry], time_window: int = 300) -> List[Dict[str, Any]]:
        """Correlate hardware events within a time window.
        
        Args:
            entries: List of log entries to analyze
            time_window: Time window in seconds for correlation
            
        Returns:
            List of correlated hardware events
        """
        correlations = []
        
        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda x: x.timestamp)
        
        # Group entries by time windows
        time_groups = self._group_by_time_window(sorted_entries, time_window)
        
        # Analyze each time group for correlations
        for group in time_groups:
            correlation = self._analyze_time_group(group)
            if correlation:
                correlations.append(correlation)
        
        return correlations
    
    def _detect_issues_by_patterns(
        self, 
        entries: List[LogEntry], 
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generic method to detect issues based on keyword patterns.
        
        Args:
            entries: Log entries to analyze
            patterns: List of pattern dictionaries with keywords and metadata
            
        Returns:
            List of detected issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            for pattern in patterns:
                # Check primary keywords
                if any(keyword in message_lower for keyword in pattern['keywords']):
                    # Check additional keywords if specified
                    if 'additional_keywords' in pattern:
                        if not any(keyword in message_lower for keyword in pattern['additional_keywords']):
                            continue
                    
                    issues.append({
                        'type': pattern['type'],
                        'severity': pattern['severity'],
                        'timestamp': entry.timestamp,
                        'message': entry.message,
                        'description': pattern['description'],
                        'recommendation': pattern['recommendation']
                    })
                    break  # Only match first pattern per entry
        
        return issues

    def _categorize_entries(self, entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
        """Categorize log entries by hardware component.
        
        Args:
            entries: List of log entries
            
        Returns:
            Dictionary of categorized entries
        """
        categories = defaultdict(list)
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # CPU-related entries
            if any(keyword in message_lower for keyword in ['cpu', 'processor', 'core', 'mce', 'thermal throttling']):
                categories['cpu'].append(entry)
            
            # Memory-related entries
            elif any(keyword in message_lower for keyword in ['memory', 'ram', 'oom', 'page fault', 'segfault', 'malloc']):
                categories['memory'].append(entry)
            
            # Storage-related entries
            elif any(keyword in message_lower for keyword in ['disk', 'sda', 'sdb', 'nvme', 'ata', 'scsi', 'filesystem', 'ext4', 'xfs']):
                categories['storage'].append(entry)
            
            # Network-related entries
            elif any(keyword in message_lower for keyword in ['network', 'eth', 'wlan', 'wifi', 'tcp', 'udp', 'dhcp']):
                categories['network'].append(entry)
            
            # Graphics-related entries
            elif any(keyword in message_lower for keyword in ['gpu', 'graphics', 'nvidia', 'amd', 'intel', 'drm', 'x11', 'wayland']):
                categories['graphics'].append(entry)
            
            # Power-related entries
            elif any(keyword in message_lower for keyword in ['power', 'battery', 'acpi', 'suspend', 'hibernate']):
                categories['power'].append(entry)
            
            # Thermal-related entries
            elif any(keyword in message_lower for keyword in ['thermal', 'temperature', 'overheat', 'cooling']):
                categories['thermal'].append(entry)
            
            # USB-related entries
            elif any(keyword in message_lower for keyword in ['usb', 'hub']):
                categories['usb'].append(entry)
            
            # PCI-related entries
            elif any(keyword in message_lower for keyword in ['pci', 'pcie']):
                categories['pci'].append(entry)
        
        return dict(categories)
    
    def _detect_cpu_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect CPU-related issues.
        
        Args:
            entries: CPU-related log entries
            
        Returns:
            List of detected CPU issues
        """
        cpu_patterns = [
            {
                'keywords': ['mce', 'machine check'],
                'type': 'machine_check_exception',
                'severity': 'high',
                'description': 'Machine Check Exception detected - possible CPU hardware error',
                'recommendation': 'Check CPU health, update microcode, consider hardware replacement'
            },
            {
                'keywords': ['thermal throttling', 'cpu throttling'],
                'type': 'thermal_throttling',
                'severity': 'medium',
                'description': 'CPU thermal throttling detected',
                'recommendation': 'Check CPU cooling, clean fans, verify thermal paste'
            },
            {
                'keywords': ['cpufreq'],
                'additional_keywords': ['error', 'failed'],
                'type': 'frequency_scaling',
                'severity': 'low',
                'description': 'CPU frequency scaling issue detected',
                'recommendation': 'Check CPU governor settings and power management configuration'
            }
        ]
        
        return self._detect_issues_by_patterns(entries, cpu_patterns)
    
    def _detect_memory_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect memory-related issues.
        
        Args:
            entries: Memory-related log entries
            
        Returns:
            List of detected memory issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # Out of Memory (OOM) killer
            if 'oom' in message_lower and 'killed' in message_lower:
                issues.append({
                    'type': 'out_of_memory',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Out of Memory condition - system killed processes',
                    'recommendation': 'Add more RAM, optimize memory usage, check for memory leaks'
                })
            
            # Memory corruption
            elif any(keyword in message_lower for keyword in ['memory corruption', 'bad page', 'memory error']):
                issues.append({
                    'type': 'memory_corruption',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Memory corruption detected',
                    'recommendation': 'Run memory test (memtest86+), check RAM modules, consider replacement'
                })
            
            # Segmentation fault
            elif 'segfault' in message_lower or 'segmentation fault' in message_lower:
                issues.append({
                    'type': 'segmentation_fault',
                    'severity': 'medium',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Segmentation fault detected',
                    'recommendation': 'Check application stability, update software, verify memory integrity'
                })
        
        return issues
    
    def _detect_storage_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect storage-related issues.
        
        Args:
            entries: Storage-related log entries
            
        Returns:
            List of detected storage issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # Disk I/O errors
            if any(keyword in message_lower for keyword in ['i/o error', 'read error', 'write error']):
                issues.append({
                    'type': 'io_error',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Disk I/O error detected',
                    'recommendation': 'Check disk health with SMART, run filesystem check, consider disk replacement'
                })
            
            # SMART errors
            elif 'smart' in message_lower and ('error' in message_lower or 'failed' in message_lower):
                issues.append({
                    'type': 'smart_error',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'SMART error detected - disk may be failing',
                    'recommendation': 'Backup data immediately, replace disk'
                })
            
            # Filesystem corruption
            elif any(keyword in message_lower for keyword in ['filesystem corruption', 'superblock', 'inode error']):
                issues.append({
                    'type': 'filesystem_corruption',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Filesystem corruption detected',
                    'recommendation': 'Run filesystem check (fsck), restore from backup if necessary'
                })
        
        return issues
    
    def _detect_network_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect network-related issues.
        
        Args:
            entries: Network-related log entries
            
        Returns:
            List of detected network issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # Network interface down
            if 'link down' in message_lower or 'interface down' in message_lower:
                issues.append({
                    'type': 'interface_down',
                    'severity': 'medium',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Network interface went down',
                    'recommendation': 'Check network cable, driver, and network configuration'
                })
            
            # DHCP failures
            elif 'dhcp' in message_lower and ('failed' in message_lower or 'timeout' in message_lower):
                issues.append({
                    'type': 'dhcp_failure',
                    'severity': 'medium',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'DHCP failure detected',
                    'recommendation': 'Check DHCP server, network connectivity, and configuration'
                })
            
            # WiFi connection issues
            elif 'wifi' in message_lower and ('disconnected' in message_lower or 'failed' in message_lower):
                issues.append({
                    'type': 'wifi_issue',
                    'severity': 'low',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'WiFi connection issue detected',
                    'recommendation': 'Check WiFi signal strength, driver, and configuration'
                })
        
        return issues
    
    def _detect_graphics_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect graphics-related issues.
        
        Args:
            entries: Graphics-related log entries
            
        Returns:
            List of detected graphics issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # GPU hang or reset
            if any(keyword in message_lower for keyword in ['gpu hang', 'gpu reset', 'graphics hang']):
                issues.append({
                    'type': 'gpu_hang',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'GPU hang or reset detected',
                    'recommendation': 'Update graphics drivers, check GPU cooling, reduce graphics settings'
                })
            
            # Display issues
            elif any(keyword in message_lower for keyword in ['display', 'monitor']) and 'error' in message_lower:
                issues.append({
                    'type': 'display_error',
                    'severity': 'medium',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Display error detected',
                    'recommendation': 'Check display connection, update drivers, verify display settings'
                })
        
        return issues
    
    def _detect_power_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect power-related issues.
        
        Args:
            entries: Power-related log entries
            
        Returns:
            List of detected power issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # Battery issues
            if 'battery' in message_lower and ('low' in message_lower or 'critical' in message_lower):
                issues.append({
                    'type': 'battery_low',
                    'severity': 'medium',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Low battery condition detected',
                    'recommendation': 'Connect power adapter, check battery health'
                })
            
            # Power supply issues
            elif any(keyword in message_lower for keyword in ['power supply', 'psu']) and 'error' in message_lower:
                issues.append({
                    'type': 'power_supply_error',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Power supply error detected',
                    'recommendation': 'Check power connections, consider PSU replacement'
                })
        
        return issues
    
    def _detect_thermal_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect thermal-related issues.
        
        Args:
            entries: Thermal-related log entries
            
        Returns:
            List of detected thermal issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # Overheating
            if any(keyword in message_lower for keyword in ['overheat', 'thermal shutdown', 'temperature critical']):
                issues.append({
                    'type': 'overheating',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'System overheating detected',
                    'recommendation': 'Check cooling system, clean fans, verify thermal paste'
                })
        
        return issues
    
    def _detect_usb_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect USB-related issues.
        
        Args:
            entries: USB-related log entries
            
        Returns:
            List of detected USB issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # USB device errors
            if 'usb' in message_lower and any(keyword in message_lower for keyword in ['error', 'failed', 'timeout']):
                issues.append({
                    'type': 'usb_error',
                    'severity': 'low',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'USB device error detected',
                    'recommendation': 'Check USB connections, try different port, update drivers'
                })
        
        return issues
    
    def _detect_pci_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect PCI-related issues.
        
        Args:
            entries: PCI-related log entries
            
        Returns:
            List of detected PCI issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            # PCI errors
            if 'pci' in message_lower and any(keyword in message_lower for keyword in ['error', 'failed', 'timeout']):
                issues.append({
                    'type': 'pci_error',
                    'severity': 'medium',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'PCI device error detected',
                    'recommendation': 'Check PCI device connections, update drivers, verify hardware compatibility'
                })
        
        return issues
    
    def _detect_kernel_panics(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect kernel panics.
        
        Args:
            entries: Kernel log entries
            
        Returns:
            List of detected kernel panics
        """
        panics = []
        
        for entry in entries:
            if 'panic' in entry.message.lower():
                panics.append({
                    'type': 'kernel_panic',
                    'severity': 'critical',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Kernel panic detected - system crash',
                    'recommendation': 'Check hardware, update kernel, review system logs for root cause'
                })
        
        return panics
    
    def _detect_kernel_oops(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect kernel oops.
        
        Args:
            entries: Kernel log entries
            
        Returns:
            List of detected kernel oops
        """
        oops = []
        
        for entry in entries:
            if 'oops' in entry.message.lower():
                oops.append({
                    'type': 'kernel_oops',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Kernel oops detected - kernel error',
                    'recommendation': 'Check hardware, update drivers, review kernel configuration'
                })
        
        return oops
    
    def _detect_kernel_warnings(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect kernel warnings with enhanced severity classification.
        
        Args:
            entries: Kernel log entries
            
        Returns:
            List of detected kernel warnings
        """
        warnings = []
        
        for entry in entries:
            try:
                message_lower = entry.message.lower()
                
                if entry.severity == 'warning' or 'warning' in message_lower:
                    # Classify warning severity and type based on content
                    severity = self._classify_kernel_warning_severity(message_lower)
                    warning_type = self._classify_kernel_warning_type(message_lower)
                    
                    warning_info = {
                        'type': warning_type,
                        'severity': severity,
                        'timestamp': entry.timestamp,
                        'message': entry.message,
                        'description': self._get_warning_description(warning_type),
                        'recommendation': self._get_warning_recommendation(warning_type)
                    }
                    
                    # Add additional context if available
                    if hasattr(entry, 'source') and entry.source:
                        warning_info['source'] = entry.source
                    
                    warnings.append(warning_info)
                    
            except (AttributeError, TypeError) as e:
                # Log the error but continue processing other entries
                # In a production system, you might want to use proper logging
                continue
        
        return warnings
    
    def _detect_kernel_errors(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect kernel errors with enhanced severity classification.
        
        Args:
            entries: Kernel log entries
            
        Returns:
            List of detected kernel errors
        """
        errors = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            
            if entry.severity == 'error' or 'error' in message_lower:
                # Classify error severity based on content
                severity = self._classify_kernel_error_severity(message_lower)
                error_type = self._classify_kernel_error_type(message_lower)
                
                errors.append({
                    'type': error_type,
                    'severity': severity,
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': self._get_error_description(error_type),
                    'recommendation': self._get_error_recommendation(error_type)
                })
        
        return errors
    
    def _detect_deadlocks(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect deadlocks.
        
        Args:
            entries: Kernel log entries
            
        Returns:
            List of detected deadlocks
        """
        deadlocks = []
        
        for entry in entries:
            if 'deadlock' in entry.message.lower():
                deadlocks.append({
                    'type': 'deadlock',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Deadlock detected',
                    'recommendation': 'Review system processes, check for resource contention'
                })
        
        return deadlocks
    
    def _detect_memory_corruption(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect memory corruption in kernel logs.
        
        Args:
            entries: Kernel log entries
            
        Returns:
            List of detected memory corruption issues
        """
        corruption = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            if any(keyword in message_lower for keyword in ['memory corruption', 'bad page', 'page fault']):
                corruption.append({
                    'type': 'memory_corruption',
                    'severity': 'high',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Memory corruption detected in kernel',
                    'recommendation': 'Run memory test, check RAM modules, update kernel'
                })
        
        return corruption
    
    def _detect_driver_issues(self, entries: List[LogEntry]) -> List[Dict[str, Any]]:
        """Detect driver issues.
        
        Args:
            entries: Kernel log entries
            
        Returns:
            List of detected driver issues
        """
        issues = []
        
        for entry in entries:
            message_lower = entry.message.lower()
            if 'driver' in message_lower and any(keyword in message_lower for keyword in ['error', 'failed', 'timeout']):
                issues.append({
                    'type': 'driver_issue',
                    'severity': 'medium',
                    'timestamp': entry.timestamp,
                    'message': entry.message,
                    'description': 'Driver issue detected',
                    'recommendation': 'Update drivers, check hardware compatibility'
                })
        
        return issues
    
    def _group_by_time_window(self, entries: List[LogEntry], window_seconds: int) -> List[List[LogEntry]]:
        """Group log entries by time windows.
        
        Args:
            entries: Sorted list of log entries
            window_seconds: Time window in seconds
            
        Returns:
            List of entry groups
        """
        if not entries:
            return []
        
        groups = []
        current_group = [entries[0]]
        window_start = entries[0].timestamp
        
        for entry in entries[1:]:
            if (entry.timestamp - window_start).total_seconds() <= window_seconds:
                current_group.append(entry)
            else:
                groups.append(current_group)
                current_group = [entry]
                window_start = entry.timestamp
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _analyze_time_group(self, group: List[LogEntry]) -> Optional[Dict[str, Any]]:
        """Analyze a time group for correlations.
        
        Args:
            group: List of log entries in the same time window
            
        Returns:
            Correlation information or None if no correlation found
        """
        if len(group) < 2:
            return None
        
        # Count entries by category
        categories = defaultdict(int)
        for entry in group:
            message_lower = entry.message.lower()
            
            if any(keyword in message_lower for keyword in ['cpu', 'processor']):
                categories['cpu'] += 1
            elif any(keyword in message_lower for keyword in ['memory', 'ram']):
                categories['memory'] += 1
            elif any(keyword in message_lower for keyword in ['disk', 'storage']):
                categories['storage'] += 1
            elif any(keyword in message_lower for keyword in ['network', 'eth']):
                categories['network'] += 1
        
        # Look for correlations
        if len(categories) >= 2:
            return {
                'timestamp': group[0].timestamp,
                'duration': (group[-1].timestamp - group[0].timestamp).total_seconds(),
                'categories': dict(categories),
                'entry_count': len(group),
                'description': f'Multiple hardware components affected simultaneously',
                'entries': [entry.message for entry in group[:5]]  # Limit to first 5 entries
            }
        
        return None
    
    def _get_hardware_patterns(self) -> Dict[str, List[Pattern]]:
        """Get compiled regex patterns for hardware issues.
        
        Returns:
            Dictionary of compiled patterns
        """
        return {
            'cpu': [
                re.compile(r'mce|machine check', re.IGNORECASE),
                re.compile(r'thermal throttling', re.IGNORECASE),
                re.compile(r'cpu.*error', re.IGNORECASE)
            ],
            'memory': [
                re.compile(r'oom.*killed', re.IGNORECASE),
                re.compile(r'memory corruption', re.IGNORECASE),
                re.compile(r'segfault', re.IGNORECASE)
            ],
            'storage': [
                re.compile(r'i/o error', re.IGNORECASE),
                re.compile(r'smart.*error', re.IGNORECASE),
                re.compile(r'filesystem.*corruption', re.IGNORECASE)
            ]
        }
    
    def _classify_kernel_warning_severity(self, message: str) -> str:
        """Classify kernel warning severity based on message content.
        
        Args:
            message: Warning message
            
        Returns:
            Severity level
        """
        return KernelMessageClassifier.classify_warning_severity(message)
    
    def _classify_kernel_warning_type(self, message: str) -> str:
        """Classify kernel warning type based on message content.
        
        Args:
            message: Warning message in lowercase
            
        Returns:
            Warning type
        """
        if 'rcu stall' in message:
            return 'rcu_stall_warning'
        elif any(keyword in message for keyword in ['soft lockup', 'hard lockup']):
            return 'lockup_warning'
        elif 'nmi watchdog' in message:
            return 'nmi_watchdog_warning'
        elif 'deprecated' in message:
            return 'deprecated_warning'
        elif 'tainted' in message:
            return 'kernel_tainted_warning'
        elif any(keyword in message for keyword in ['firmware', 'microcode']):
            return 'firmware_warning'
        elif any(keyword in message for keyword in ['temperature', 'thermal']):
            return 'thermal_warning'
        else:
            return 'general_kernel_warning'
    
    def _classify_kernel_error_severity(self, message: str) -> str:
        """Classify kernel error severity based on message content.
        
        Args:
            message: Error message
            
        Returns:
            Severity level
        """
        return KernelMessageClassifier.classify_error_severity(message)
    
    def _classify_kernel_error_type(self, message: str) -> str:
        """Classify kernel error type based on message content.
        
        Args:
            message: Error message in lowercase
            
        Returns:
            Error type
        """
        if any(keyword in message for keyword in ['i/o error', 'read error', 'write error']):
            return 'io_error'
        elif 'timeout' in message:
            return 'timeout_error'
        elif any(keyword in message for keyword in ['null pointer', 'segfault']):
            return 'memory_error'
        elif 'firmware' in message:
            return 'firmware_error'
        elif 'driver' in message:
            return 'driver_error'
        elif any(keyword in message for keyword in ['pci', 'usb', 'device']):
            return 'device_error'
        elif 'filesystem' in message:
            return 'filesystem_error'
        elif 'network' in message:
            return 'network_error'
        else:
            return 'general_kernel_error'
    
    def _get_warning_description(self, warning_type: str) -> str:
        """Get description for warning type.
        
        Args:
            warning_type: Type of warning
            
        Returns:
            Warning description
        """
        descriptions = {
            'rcu_stall_warning': 'RCU stall detected - system may be unresponsive',
            'lockup_warning': 'CPU lockup detected - system may hang',
            'nmi_watchdog_warning': 'NMI watchdog triggered - system monitoring issue',
            'deprecated_warning': 'Deprecated kernel feature in use',
            'kernel_tainted_warning': 'Kernel is tainted - non-GPL modules loaded',
            'firmware_warning': 'Firmware or microcode issue detected',
            'thermal_warning': 'Thermal management warning',
            'general_kernel_warning': 'General kernel warning detected'
        }
        return descriptions.get(warning_type, 'Kernel warning detected')
    
    def _get_warning_recommendation(self, warning_type: str) -> str:
        """Get recommendation for warning type.
        
        Args:
            warning_type: Type of warning
            
        Returns:
            Warning recommendation
        """
        recommendations = {
            'rcu_stall_warning': 'Check system load, disable unnecessary services, update kernel',
            'lockup_warning': 'Check hardware, update drivers, review system configuration',
            'nmi_watchdog_warning': 'Check hardware monitoring, update BIOS/UEFI',
            'deprecated_warning': 'Update software to use current kernel APIs',
            'kernel_tainted_warning': 'Remove proprietary modules or accept reduced support',
            'firmware_warning': 'Update firmware/microcode, check hardware compatibility',
            'thermal_warning': 'Check cooling system, monitor temperatures',
            'general_kernel_warning': 'Review warning details, update drivers if necessary'
        }
        return recommendations.get(warning_type, 'Review warning details, update drivers if necessary')
    
    def _get_error_description(self, error_type: str) -> str:
        """Get description for error type.
        
        Args:
            error_type: Type of error
            
        Returns:
            Error description
        """
        descriptions = {
            'io_error': 'Input/Output error detected - storage or device issue',
            'timeout_error': 'Operation timeout - device or network issue',
            'memory_error': 'Memory access error - possible hardware issue',
            'firmware_error': 'Firmware error - hardware or driver issue',
            'driver_error': 'Device driver error - compatibility or bug issue',
            'device_error': 'Hardware device error detected',
            'filesystem_error': 'Filesystem error - corruption or access issue',
            'network_error': 'Network subsystem error detected',
            'general_kernel_error': 'General kernel error detected'
        }
        return descriptions.get(error_type, 'Kernel error detected')
    
    def _get_error_recommendation(self, error_type: str) -> str:
        """Get recommendation for error type.
        
        Args:
            error_type: Type of error
            
        Returns:
            Error recommendation
        """
        recommendations = {
            'io_error': 'Check storage devices, run filesystem check, replace failing hardware',
            'timeout_error': 'Check device connections, update drivers, verify hardware',
            'memory_error': 'Run memory test, check RAM modules, update kernel',
            'firmware_error': 'Update firmware, check hardware compatibility, replace if necessary',
            'driver_error': 'Update drivers, check hardware compatibility, report bug if persistent',
            'device_error': 'Check device connections, update drivers, replace failing hardware',
            'filesystem_error': 'Run filesystem check, restore from backup, check storage health',
            'network_error': 'Check network configuration, update drivers, verify connectivity',
            'general_kernel_error': 'Review error details, check hardware, update drivers'
        }
        return recommendations.get(error_type, 'Review error details, check hardware, update drivers')
    
    def _get_kernel_patterns(self) -> Dict[str, List[Pattern]]:
        """Get compiled regex patterns for kernel issues.
        
        Returns:
            Dictionary of compiled patterns
        """
        return {
            'panic': [
                re.compile(r'kernel panic', re.IGNORECASE),
                re.compile(r'panic.*not syncing', re.IGNORECASE)
            ],
            'oops': [
                re.compile(r'oops:', re.IGNORECASE),
                re.compile(r'unable to handle', re.IGNORECASE)
            ],
            'deadlock': [
                re.compile(r'deadlock', re.IGNORECASE),
                re.compile(r'hung task', re.IGNORECASE)
            ],
            'rcu_stall': [
                re.compile(r'rcu.*stall', re.IGNORECASE),
                re.compile(r'rcu.*detected', re.IGNORECASE)
            ],
            'lockup': [
                re.compile(r'soft lockup', re.IGNORECASE),
                re.compile(r'hard lockup', re.IGNORECASE)
            ],
            'memory_corruption': [
                re.compile(r'memory corruption', re.IGNORECASE),
                re.compile(r'bad page', re.IGNORECASE),
                re.compile(r'page fault', re.IGNORECASE)
            ]
        }