#!/usr/bin/env python3
"""Tests for the Kernel Configuration Analyzer module.

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
from unittest.mock import MagicMock, patch

from infenix.kernel.config_analyzer import KernelConfigAnalyzer
from infenix.interfaces import KernelConfig, KernelConfigOption


class TestKernelConfigAnalyzer(unittest.TestCase):
    """Test cases for the KernelConfigAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.analyzer = KernelConfigAnalyzer(self.mock_system)
        
        # Create a test kernel configuration
        self.test_config = KernelConfig(
            version='5.15.0-58-generic',
            options={
                'CONFIG_SECURITY': KernelConfigOption(
                    name='CONFIG_SECURITY',
                    value='y',
                    description='Enable different security models'
                ),
                'CONFIG_SECURITY_SELINUX': KernelConfigOption(
                    name='CONFIG_SECURITY_SELINUX',
                    value='y',
                    description='NSA SELinux Support'
                ),
                'CONFIG_SECURITY_APPARMOR': KernelConfigOption(
                    name='CONFIG_SECURITY_APPARMOR',
                    value='n',
                    description='AppArmor support'
                ),
                'CONFIG_PREEMPT': KernelConfigOption(
                    name='CONFIG_PREEMPT',
                    value='n',
                    description='Preemptible Kernel'
                ),
                'CONFIG_HZ': KernelConfigOption(
                    name='CONFIG_HZ',
                    value='250',
                    description='Timer frequency'
                ),
                'CONFIG_CPU_FREQ': KernelConfigOption(
                    name='CONFIG_CPU_FREQ',
                    value='y',
                    description='CPU frequency scaling'
                )
            },
            analysis={},
            recommendations={}
        )
    
    def test_analyze_config(self):
        """Test analyzing kernel configuration."""
        # Call the method under test
        result = self.analyzer.analyze_config(self.test_config)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('security', result)
        self.assertIn('performance', result)
        self.assertIn('security_score', result)
        self.assertIn('performance_score', result)
        
        # Verify security analysis
        security = result['security']
        self.assertIn('issues', security)
        self.assertIn('recommendations', security)
        self.assertIn('good_practices', security)
        
        # Verify performance analysis
        performance = result['performance']
        self.assertIn('issues', performance)
        self.assertIn('recommendations', performance)
        self.assertIn('good_practices', performance)
        
        # Verify scores
        self.assertIsInstance(result['security_score'], int)
        self.assertIsInstance(result['performance_score'], int)
        self.assertGreaterEqual(result['security_score'], 0)
        self.assertLessEqual(result['security_score'], 100)
        self.assertGreaterEqual(result['performance_score'], 0)
        self.assertLessEqual(result['performance_score'], 100)
    
    def test_analyze_security_options(self):
        """Test analyzing security-related configuration options."""
        # Call the method under test
        result = self.analyzer._analyze_security_options(self.test_config)
        
        # Verify the result
        self.assertIn('issues', result)
        self.assertIn('recommendations', result)
        self.assertIn('good_practices', result)
        
        # Verify good practices
        good_practices = result['good_practices']
        self.assertGreater(len(good_practices), 0)
        self.assertEqual(good_practices[0]['option'], 'CONFIG_SECURITY')
        self.assertEqual(good_practices[0]['value'], 'y')
        
        # Verify issues
        issues = result['issues']
        self.assertGreater(len(issues), 0)
        apparmor_issue = next((i for i in issues if i['option'] == 'CONFIG_SECURITY_APPARMOR'), None)
        self.assertIsNotNone(apparmor_issue)
        self.assertEqual(apparmor_issue['current_value'], 'n')
        self.assertEqual(apparmor_issue['recommended_value'], 'y')
        
        # Verify recommendations
        recommendations = result['recommendations']
        self.assertGreater(len(recommendations), 0)
        apparmor_rec = next((r for r in recommendations if r['option'] == 'CONFIG_SECURITY_APPARMOR'), None)
        self.assertIsNotNone(apparmor_rec)
        self.assertEqual(apparmor_rec['current_value'], 'n')
        self.assertEqual(apparmor_rec['recommended_value'], 'y')
    
    def test_analyze_performance_options(self):
        """Test analyzing performance-related configuration options."""
        # Call the method under test
        result = self.analyzer._analyze_performance_options(self.test_config)
        
        # Verify the result
        self.assertIn('issues', result)
        self.assertIn('recommendations', result)
        self.assertIn('good_practices', result)
        
        # Verify good practices
        good_practices = result['good_practices']
        self.assertGreater(len(good_practices), 0)
        self.assertEqual(good_practices[0]['option'], 'CONFIG_CPU_FREQ')
        self.assertEqual(good_practices[0]['value'], 'y')
        
        # Verify issues
        issues = result['issues']
        self.assertGreater(len(issues), 0)
        preempt_issue = next((i for i in issues if i['option'] == 'CONFIG_PREEMPT'), None)
        self.assertIsNotNone(preempt_issue)
        self.assertEqual(preempt_issue['current_value'], 'n')
        self.assertEqual(preempt_issue['recommended_value'], 'y')
        
        # Verify recommendations
        recommendations = result['recommendations']
        self.assertGreater(len(recommendations), 0)
        preempt_rec = next((r for r in recommendations if r['option'] == 'CONFIG_PREEMPT'), None)
        self.assertIsNotNone(preempt_rec)
        self.assertEqual(preempt_rec['current_value'], 'n')
        self.assertEqual(preempt_rec['recommended_value'], 'y')
    
    def test_is_value_compliant(self):
        """Test checking if a value is compliant with a recommended value."""
        # Test exact match
        self.assertTrue(self.analyzer._is_value_compliant('y', 'y'))
        self.assertTrue(self.analyzer._is_value_compliant('n', 'n'))
        self.assertTrue(self.analyzer._is_value_compliant('1000', '1000'))
        
        # Test boolean values
        self.assertTrue(self.analyzer._is_value_compliant('1', 'y'))
        self.assertTrue(self.analyzer._is_value_compliant('yes', 'y'))
        self.assertTrue(self.analyzer._is_value_compliant('true', 'y'))
        self.assertTrue(self.analyzer._is_value_compliant('0', 'n'))
        self.assertTrue(self.analyzer._is_value_compliant('no', 'n'))
        self.assertTrue(self.analyzer._is_value_compliant('false', 'n'))
        
        # Test numeric values with minimum requirement
        self.assertTrue(self.analyzer._is_value_compliant('1000', '>=500'))
        self.assertTrue(self.analyzer._is_value_compliant('500', '>=500'))
        self.assertFalse(self.analyzer._is_value_compliant('499', '>=500'))
        
        # Test numeric values with maximum requirement
        self.assertTrue(self.analyzer._is_value_compliant('500', '<=1000'))
        self.assertTrue(self.analyzer._is_value_compliant('1000', '<=1000'))
        self.assertFalse(self.analyzer._is_value_compliant('1001', '<=1000'))
        
        # Test non-compliant values
        self.assertFalse(self.analyzer._is_value_compliant('y', 'n'))
        self.assertFalse(self.analyzer._is_value_compliant('n', 'y'))
        self.assertFalse(self.analyzer._is_value_compliant('500', '1000'))
    
    def test_calculate_security_score(self):
        """Test calculating security score."""
        # Test with no options
        score = self.analyzer._calculate_security_score({
            'issues': [],
            'recommendations': [],
            'good_practices': []
        })
        self.assertEqual(score, 0)
        
        # Test with all good practices
        score = self.analyzer._calculate_security_score({
            'issues': [],
            'recommendations': [],
            'good_practices': [{'option': 'CONFIG_SECURITY'}, {'option': 'CONFIG_SECURITY_SELINUX'}]
        })
        self.assertEqual(score, 100)
        
        # Test with mixed issues and good practices
        score = self.analyzer._calculate_security_score({
            'issues': [{'option': 'CONFIG_SECURITY_APPARMOR'}],
            'recommendations': [{'option': 'CONFIG_SECURITY_APPARMOR'}],
            'good_practices': [{'option': 'CONFIG_SECURITY'}, {'option': 'CONFIG_SECURITY_SELINUX'}]
        })
        self.assertEqual(score, 66)  # 2 out of 3 options are good practices
    
    def test_calculate_performance_score(self):
        """Test calculating performance score."""
        # Test with no options
        score = self.analyzer._calculate_performance_score({
            'issues': [],
            'recommendations': [],
            'good_practices': []
        })
        self.assertEqual(score, 0)
        
        # Test with all good practices
        score = self.analyzer._calculate_performance_score({
            'issues': [],
            'recommendations': [],
            'good_practices': [{'option': 'CONFIG_PREEMPT'}, {'option': 'CONFIG_CPU_FREQ'}]
        })
        self.assertEqual(score, 100)
        
        # Test with mixed issues and good practices
        score = self.analyzer._calculate_performance_score({
            'issues': [{'option': 'CONFIG_PREEMPT'}],
            'recommendations': [{'option': 'CONFIG_PREEMPT'}],
            'good_practices': [{'option': 'CONFIG_CPU_FREQ'}]
        })
        self.assertEqual(score, 50)  # 1 out of 2 options are good practices


if __name__ == '__main__':
    unittest.main()