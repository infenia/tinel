#!/usr/bin/env python3
"""Tests for the Log Analyzer module.

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
from unittest.mock import MagicMock, patch

from infenix.logs.log_analyzer import LogAnalyzer
from infenix.interfaces import LogAnalysis, LogEntry


class TestLogAnalyzer(unittest.TestCase):
    """Test cases for the LogAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.analyzer = LogAnalyzer(self.mock_system)
        
        # Create test log entries
        base_time = datetime.now()
        self.test_entries = [
            LogEntry(
                timestamp=base_time,
                facility='kernel',
                severity='critical',
                message='kernel panic - not syncing: Fatal exception',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=10),
                facility='kernel',
                severity='error',
                message='Machine Check Exception: CPU 0 Bank 1',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=20),
                facility='kernel',
                severity='warning',
                message='OOM killer activated: killed process firefox',
                source='kernel'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=30),
                facility='daemon',
                severity='info',
                message='Service started successfully',
                source='systemd'
            ),
            LogEntry(
                timestamp=base_time + timedelta(seconds=40),
                facility='kernel',
                severity='error',
                message='ata1: I/O error, dev sda, sector 12345',
                source='kernel'
            )
        ]
    
    def test_analyze_logs(self):
        """Test comprehensive log analysis."""
        # Mock the parser and detector
        with patch.object(self.analyzer.parser, 'parse_logs', return_value=self.test_entries):
            with patch.object(self.analyzer.detector, 'detect_hardware_patterns', return_value={'storage_issues': []}):
                with patch.object(self.analyzer.detector, 'detect_kernel_patterns', return_value={'kernel_panics': []}):
                    
                    # Call the method under test
                    result = self.analyzer.analyze_logs(['syslog'])
                    
                    # Verify the result
                    self.assertIsInstance(result, LogAnalysis)
                    self.assertEqual(len(result.entries), 5)
                    self.assertIn('hardware', result.patterns)
                    self.assertIn('kernel', result.patterns)
                    self.assertIn('statistics', result.summary)
    
    def test_generate_critical_issues_summary(self):
        """Test generating critical issues summary."""
        # Mock the detector methods
        hardware_patterns = {
            'cpu_issues': [
                {
                    'type': 'machine_check_exception',
                    'severity': 'critical',
                    'timestamp': datetime.now(),
                    'description': 'Machine Check Exception detected',
                    'recommendation': 'Check CPU health'
                }
            ],
            'storage_issues': [
                {
                    'type': 'io_error',
                    'severity': 'high',
                    'timestamp': datetime.now(),
                    'description': 'I/O error detected',
                    'recommendation': 'Check storage devices'
                }
            ]
        }
        
        kernel_patterns = {
            'kernel_panics': [
                {
                    'type': 'kernel_panic',
                    'severity': 'critical',
                    'timestamp': datetime.now(),
                    'description': 'Kernel panic detected',
                    'recommendation': 'Check hardware and update kernel'
                }
            ]
        }
        
        with patch.object(self.analyzer.detector, 'detect_hardware_patterns', return_value=hardware_patterns):
            with patch.object(self.analyzer.detector, 'detect_kernel_patterns', return_value=kernel_patterns):
                
                # Call the method under test
                result = self.analyzer.generate_critical_issues_summary(self.test_entries)
                
                # Verify the result
                self.assertIsInstance(result, dict)
                self.assertIn('total_critical_issues', result)
                self.assertIn('issues', result)
                self.assertIn('statistics', result)
                self.assertIn('recommendations', result)
                
                # Verify critical issues are included
                self.assertGreater(result['total_critical_issues'], 0)
                self.assertGreater(len(result['issues']), 0)
    
    def test_analyze_specific_entry(self):
        """Test detailed analysis of a specific log entry."""
        entry = self.test_entries[0]  # Kernel panic entry
        
        # Call the method under test
        result = self.analyzer.analyze_specific_entry(entry)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('entry', result)
        self.assertIn('classification', result)
        self.assertIn('context', result)
        self.assertIn('recommendations', result)
        
        # Verify entry details
        self.assertEqual(result['entry']['severity'], 'critical')
        self.assertEqual(result['entry']['facility'], 'kernel')
        
        # Verify classification
        self.assertIn('category', result['classification'])
        self.assertIn('urgency', result['classification'])
        
        # Verify context
        self.assertIn('timestamp_info', result['context'])
        self.assertIn('source_info', result['context'])
        
        # Verify recommendations
        self.assertIsInstance(result['recommendations'], list)
        self.assertGreater(len(result['recommendations']), 0)
    
    def test_generate_basic_statistics(self):
        """Test generating basic statistics."""
        # Call the method under test
        result = self.analyzer._generate_basic_statistics(self.test_entries)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('total_entries', result)
        self.assertIn('severity_distribution', result)
        self.assertIn('facility_distribution', result)
        self.assertIn('source_distribution', result)
        self.assertIn('time_range', result)
        
        # Verify statistics
        self.assertEqual(result['total_entries'], 5)
        self.assertIn('critical', result['severity_distribution'])
        self.assertIn('error', result['severity_distribution'])
        self.assertIn('kernel', result['facility_distribution'])
    
    def test_generate_health_assessment(self):
        """Test generating health assessment."""
        issues = {
            'critical': [{'type': 'kernel_panic', 'severity': 'critical'}],
            'high': [{'type': 'io_error', 'severity': 'high'}],
            'medium': [{'type': 'warning', 'severity': 'medium'}],
            'low': []
        }
        
        # Call the method under test
        result = self.analyzer._generate_health_assessment(issues)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('health_score', result)
        self.assertIn('health_status', result)
        self.assertIn('total_issues', result)
        self.assertIn('critical_issues', result)
        self.assertIn('assessment', result)
        
        # Verify health assessment
        self.assertIsInstance(result['health_score'], int)
        self.assertGreaterEqual(result['health_score'], 0)
        self.assertLessEqual(result['health_score'], 100)
        self.assertEqual(result['total_issues'], 3)
        self.assertEqual(result['critical_issues'], 1)
    
    def test_classify_log_entry(self):
        """Test classifying log entries."""
        # Test kernel entry
        kernel_entry = self.test_entries[0]
        result = self.analyzer._classify_log_entry(kernel_entry)
        
        self.assertEqual(result['category'], 'kernel')
        self.assertEqual(result['urgency'], 'critical')
        
        # Test storage entry
        storage_entry = self.test_entries[4]
        result = self.analyzer._classify_log_entry(storage_entry)
        
        self.assertEqual(result['category'], 'storage')
        self.assertEqual(result['component'], 'storage')
    
    def test_provide_entry_context(self):
        """Test providing context for log entries."""
        entry = self.test_entries[0]
        
        # Call the method under test
        result = self.analyzer._provide_entry_context(entry)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('timestamp_info', result)
        self.assertIn('source_info', result)
        self.assertIn('message_info', result)
        
        # Verify timestamp info
        self.assertIn('formatted', result['timestamp_info'])
        self.assertIn('age_hours', result['timestamp_info'])
        self.assertIn('time_of_day', result['timestamp_info'])
        
        # Verify source info
        self.assertEqual(result['source_info']['facility'], 'kernel')
        self.assertTrue(result['source_info']['is_kernel'])
        
        # Verify message info
        self.assertGreater(result['message_info']['length'], 0)
        self.assertGreater(result['message_info']['word_count'], 0)
    
    def test_classify_time_of_day(self):
        """Test time of day classification."""
        # Test morning
        morning_time = datetime.now().replace(hour=9, minute=0, second=0)
        self.assertEqual(self.analyzer._classify_time_of_day(morning_time), 'morning')
        
        # Test afternoon
        afternoon_time = datetime.now().replace(hour=15, minute=0, second=0)
        self.assertEqual(self.analyzer._classify_time_of_day(afternoon_time), 'afternoon')
        
        # Test evening
        evening_time = datetime.now().replace(hour=20, minute=0, second=0)
        self.assertEqual(self.analyzer._classify_time_of_day(evening_time), 'evening')
        
        # Test night
        night_time = datetime.now().replace(hour=2, minute=0, second=0)
        self.assertEqual(self.analyzer._classify_time_of_day(night_time), 'night')


if __name__ == '__main__':
    unittest.main()