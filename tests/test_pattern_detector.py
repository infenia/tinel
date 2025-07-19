#!/usr/bin/env python3
"""Tests for the Pattern Detector module.

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

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from infenix.logs.pattern_detector import PatternDetector
from infenix.interfaces import LogEntry


class TestPatternDetector(unittest.TestCase):
    """Test cases for the PatternDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.detector = PatternDetector(self.mock_system)
        
        # Create test log entries
        base_time = datetime.now()
        self.test_entries = [
            LogEntry(
                timestamp=base_time,
                facility='kernel',
                severity='error',
                message='Machine Check Exception: CPU 0 Bank 1',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=10),
                facility='kernel',
                severity='warning',
                message='OOM killer activated: killed process firefox',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=20),
                facility='kernel',
                severity='error',
                message='ata1: I/O error, dev sda, sector 12345',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=30),
                facility='kernel',
                severity='info',
                message='eth0: link down',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=40),
                facility='kernel',
                severity='critical',
                message='kernel panic - not syncing: Fatal exception',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=50),
                facility='kernel',
                severity='error',
                message='GPU hang detected on device 0000:01:00.0',
                source='kernel'
            )
        ]
    
    def test_detect_hardware_patterns(self):
        """Test detecting hardware patterns."""
        # Call the method under test
        result = self.detector.detect_hardware_patterns(self.test_entries)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('cpu_issues', result)
        self.assertIn('memory_issues', result)
        self.assertIn('storage_issues', result)
        self.assertIn('network_issues', result)
        self.assertIn('graphics_issues', result)
        
        # Verify CPU issues
        cpu_issues = result['cpu_issues']
        self.assertGreater(len(cpu_issues), 0)
        self.assertEqual(cpu_issues[0]['type'], 'machine_check_exception')
        self.assertEqual(cpu_issues[0]['severity'], 'high')
        
        # Verify memory issues
        memory_issues = result['memory_issues']
        self.assertGreater(len(memory_issues), 0)
        self.assertEqual(memory_issues[0]['type'], 'out_of_memory')
        self.assertEqual(memory_issues[0]['severity'], 'high')
        
        # Verify storage issues
        storage_issues = result['storage_issues']
        self.assertGreater(len(storage_issues), 0)
        self.assertEqual(storage_issues[0]['type'], 'io_error')
        self.assertEqual(storage_issues[0]['severity'], 'high')
        
        # Verify network issues
        network_issues = result['network_issues']
        self.assertGreater(len(network_issues), 0)
        self.assertEqual(network_issues[0]['type'], 'interface_down')
        self.assertEqual(network_issues[0]['severity'], 'medium')
        
        # Verify graphics issues
        graphics_issues = result['graphics_issues']
        self.assertGreater(len(graphics_issues), 0)
        self.assertEqual(graphics_issues[0]['type'], 'gpu_hang')
        self.assertEqual(graphics_issues[0]['severity'], 'high')
    
    def test_detect_kernel_patterns(self):
        """Test detecting kernel patterns."""
        # Call the method under test
        result = self.detector.detect_kernel_patterns(self.test_entries)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('kernel_panics', result)
        self.assertIn('oops', result)
        self.assertIn('warnings', result)
        self.assertIn('errors', result)
        
        # Verify kernel panics
        panics = result['kernel_panics']
        self.assertGreater(len(panics), 0)
        self.assertEqual(panics[0]['type'], 'kernel_panic')
        self.assertEqual(panics[0]['severity'], 'critical')
        
        # Verify kernel errors with enhanced classification
        errors = result['errors']
        self.assertGreater(len(errors), 0)
        # The error type should be classified based on content
        self.assertIn(errors[0]['type'], ['io_error', 'memory_error', 'general_kernel_error'])
        self.assertIn(errors[0]['severity'], ['critical', 'high', 'medium'])
    
    def test_categorize_entries(self):
        """Test categorizing log entries."""
        # Call the method under test
        result = self.detector._categorize_entries(self.test_entries)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('cpu', result)
        self.assertIn('memory', result)
        self.assertIn('storage', result)
        self.assertIn('network', result)
        self.assertIn('graphics', result)
        
        # Verify categorization
        self.assertEqual(len(result['cpu']), 1)
        self.assertEqual(len(result['memory']), 1)
        self.assertEqual(len(result['storage']), 1)
        self.assertEqual(len(result['network']), 1)
        self.assertEqual(len(result['graphics']), 1)
    
    def test_detect_cpu_issues(self):
        """Test detecting CPU issues."""
        cpu_entries = [entry for entry in self.test_entries if 'cpu' in entry.message.lower() or 'mce' in entry.message.lower()]
        
        # Call the method under test
        result = self.detector._detect_cpu_issues(cpu_entries)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]['type'], 'machine_check_exception')
        self.assertEqual(result[0]['severity'], 'high')
        self.assertIn('Machine Check Exception', result[0]['description'])
    
    def test_detect_memory_issues(self):
        """Test detecting memory issues."""
        memory_entries = [entry for entry in self.test_entries if 'oom' in entry.message.lower()]
        
        # Call the method under test
        result = self.detector._detect_memory_issues(memory_entries)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]['type'], 'out_of_memory')
        self.assertEqual(result[0]['severity'], 'high')
        self.assertIn('Out of Memory', result[0]['description'])
    
    def test_detect_storage_issues(self):
        """Test detecting storage issues."""
        storage_entries = [entry for entry in self.test_entries if 'i/o error' in entry.message.lower()]
        
        # Call the method under test
        result = self.detector._detect_storage_issues(storage_entries)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]['type'], 'io_error')
        self.assertEqual(result[0]['severity'], 'high')
        self.assertIn('Disk I/O error', result[0]['description'])
    
    def test_correlate_hardware_events(self):
        """Test correlating hardware events."""
        # Call the method under test with a 60-second time window
        result = self.detector.correlate_hardware_events(self.test_entries, 60)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Verify correlation
        correlation = result[0]
        self.assertIn('timestamp', correlation)
        self.assertIn('duration', correlation)
        self.assertIn('categories', correlation)
        self.assertIn('entry_count', correlation)
        self.assertIn('description', correlation)
        self.assertGreater(correlation['entry_count'], 1)
    
    def test_group_by_time_window(self):
        """Test grouping entries by time window."""
        # Call the method under test with a 30-second time window
        result = self.detector._group_by_time_window(self.test_entries, 30)
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
        # Verify grouping
        for group in result:
            self.assertIsInstance(group, list)
            self.assertGreater(len(group), 0)
            
            # Verify time window constraint
            if len(group) > 1:
                time_diff = (group[-1].timestamp - group[0].timestamp).total_seconds()
                self.assertLessEqual(time_diff, 30)
    
    def test_analyze_time_group(self):
        """Test analyzing time groups for correlations."""
        # Create a group with multiple categories
        group = self.test_entries[:4]  # CPU, memory, storage, network
        
        # Call the method under test
        result = self.detector._analyze_time_group(group)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('timestamp', result)
        self.assertIn('duration', result)
        self.assertIn('categories', result)
        self.assertIn('entry_count', result)
        self.assertIn('description', result)
        self.assertEqual(result['entry_count'], 4)
        self.assertGreater(len(result['categories']), 1)
    
    def test_classify_kernel_warning_severity(self):
        """Test classifying kernel warning severity."""
        # Test high severity warnings
        self.assertEqual(self.detector._classify_kernel_warning_severity('rcu stall detected'), 'high')
        self.assertEqual(self.detector._classify_kernel_warning_severity('soft lockup detected'), 'high')
        self.assertEqual(self.detector._classify_kernel_warning_severity('call trace follows'), 'high')
        
        # Test medium severity warnings
        self.assertEqual(self.detector._classify_kernel_warning_severity('deprecated function used'), 'medium')
        self.assertEqual(self.detector._classify_kernel_warning_severity('kernel tainted'), 'medium')
        self.assertEqual(self.detector._classify_kernel_warning_severity('firmware loading failed'), 'medium')
        
        # Test low severity warnings
        self.assertEqual(self.detector._classify_kernel_warning_severity('general warning message'), 'low')
    
    def test_classify_kernel_error_severity(self):
        """Test classifying kernel error severity."""
        # Test critical severity errors
        self.assertEqual(self.detector._classify_kernel_error_severity('fatal error occurred'), 'critical')
        self.assertEqual(self.detector._classify_kernel_error_severity('memory corruption detected'), 'critical')
        self.assertEqual(self.detector._classify_kernel_error_severity('unable to handle kernel paging request'), 'critical')
        
        # Test high severity errors
        self.assertEqual(self.detector._classify_kernel_error_severity('i/o error on device'), 'high')
        self.assertEqual(self.detector._classify_kernel_error_severity('operation timeout'), 'high')
        self.assertEqual(self.detector._classify_kernel_error_severity('device failed to respond'), 'high')
        
        # Test medium severity errors
        self.assertEqual(self.detector._classify_kernel_error_severity('general error message'), 'medium')
    
    def test_classify_kernel_warning_type(self):
        """Test classifying kernel warning types."""
        self.assertEqual(self.detector._classify_kernel_warning_type('rcu stall detected'), 'rcu_stall_warning')
        self.assertEqual(self.detector._classify_kernel_warning_type('soft lockup detected'), 'lockup_warning')
        self.assertEqual(self.detector._classify_kernel_warning_type('nmi watchdog triggered'), 'nmi_watchdog_warning')
        self.assertEqual(self.detector._classify_kernel_warning_type('deprecated function'), 'deprecated_warning')
        self.assertEqual(self.detector._classify_kernel_warning_type('kernel tainted'), 'kernel_tainted_warning')
        self.assertEqual(self.detector._classify_kernel_warning_type('firmware error'), 'firmware_warning')
        self.assertEqual(self.detector._classify_kernel_warning_type('thermal warning'), 'thermal_warning')
        self.assertEqual(self.detector._classify_kernel_warning_type('general warning'), 'general_kernel_warning')
    
    def test_classify_kernel_error_type(self):
        """Test classifying kernel error types."""
        self.assertEqual(self.detector._classify_kernel_error_type('i/o error on device'), 'io_error')
        self.assertEqual(self.detector._classify_kernel_error_type('operation timeout'), 'timeout_error')
        self.assertEqual(self.detector._classify_kernel_error_type('null pointer dereference'), 'memory_error')
        self.assertEqual(self.detector._classify_kernel_error_type('firmware loading failed'), 'firmware_error')
        self.assertEqual(self.detector._classify_kernel_error_type('driver initialization failed'), 'driver_error')
        self.assertEqual(self.detector._classify_kernel_error_type('pci device error'), 'device_error')
        self.assertEqual(self.detector._classify_kernel_error_type('filesystem corruption'), 'filesystem_error')
        self.assertEqual(self.detector._classify_kernel_error_type('network interface error'), 'network_error')
        self.assertEqual(self.detector._classify_kernel_error_type('general error'), 'general_kernel_error')


if __name__ == '__main__':
    unittest.main()