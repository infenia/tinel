#!/usr/bin/env python3
"""Tests for the Kernel Optimizer module.

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

from infenix.kernel.optimization import KernelOptimizer
from infenix.interfaces import HardwareInfo, KernelConfig, KernelConfigOption


class TestKernelOptimizer(unittest.TestCase):
    """Test cases for the KernelOptimizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.optimizer = KernelOptimizer(self.mock_system)
        
        # Create a test kernel configuration
        self.test_config = KernelConfig(
            version='5.15.0-58-generic',
            options={
                'CONFIG_PREEMPT': KernelConfigOption(
                    name='CONFIG_PREEMPT',
                    value='n',
                    description='Preemptible Kernel'
                ),
                'CONFIG_HZ_1000': KernelConfigOption(
                    name='CONFIG_HZ_1000',
                    value='n',
                    description='1000 Hz tick rate'
                ),
                'CONFIG_HZ': KernelConfigOption(
                    name='CONFIG_HZ',
                    value='250',
                    description='Timer frequency'
                ),
                'CONFIG_SMP': KernelConfigOption(
                    name='CONFIG_SMP',
                    value='y',
                    description='Symmetric multi-processing support'
                ),
                'CONFIG_NR_CPUS': KernelConfigOption(
                    name='CONFIG_NR_CPUS',
                    value='8',
                    description='Maximum number of CPUs'
                )
            },
            analysis={},
            recommendations={}
        )
        
        # Create test hardware information
        self.test_hardware = HardwareInfo(
            cpu={
                'model_name': 'Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz',
                'logical_cpus': 12,
                'physical_cpus': 6
            },
            memory={
                'memory_total_gb': 32,
                'memory_free_gb': 16
            },
            storage={
                'disks': [
                    {
                        'name': 'sda',
                        'is_ssd': True,
                        'size': '500GB'
                    }
                ]
            },
            pci_devices={
                'devices': [
                    {
                        'vendor': 'Intel Corporation',
                        'device': 'UHD Graphics 630'
                    }
                ]
            },
            usb_devices={
                'devices': []
            },
            network={
                'interfaces': [
                    {
                        'name': 'eth0',
                        'type': 'ethernet',
                        'speed': '1000 Mbps'
                    }
                ]
            },
            graphics={
                'gpus': [
                    {
                        'vendor': 'Intel',
                        'model': 'UHD Graphics 630'
                    }
                ]
            }
        )
    
    def test_get_recommendations(self):
        """Test getting optimization recommendations."""
        # Call the method under test
        result = self.optimizer.get_recommendations(self.test_config, self.test_hardware)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('general', result)
        self.assertIn('cpu', result)
        self.assertIn('memory', result)
        self.assertIn('storage', result)
        self.assertIn('network', result)
        self.assertIn('graphics', result)
        
        # Verify general recommendations
        general_recs = result['general']
        self.assertGreater(len(general_recs), 0)
        preempt_rec = next((r for r in general_recs if r['option'] == 'CONFIG_PREEMPT'), None)
        self.assertIsNotNone(preempt_rec)
        self.assertEqual(preempt_rec['current_value'], 'n')
        self.assertEqual(preempt_rec['recommended_value'], 'y')
        
        # Verify CPU recommendations
        cpu_recs = result['cpu']
        self.assertGreater(len(cpu_recs), 0)
        
        # Verify that recommendations were added to the config
        self.assertEqual(self.test_config.recommendations, result)
    
    def test_determine_hardware_profile(self):
        """Test determining hardware profile."""
        # Call the method under test
        result = self.optimizer._determine_hardware_profile(self.test_hardware)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('system_type', result)
        self.assertIn('cpu_cores', result)
        self.assertIn('memory_size', result)
        self.assertIn('storage_type', result)
        self.assertIn('network_type', result)
        self.assertIn('graphics_type', result)
        
        # Verify profile values
        self.assertEqual(result['system_type'], 'desktop')
        self.assertEqual(result['cpu_cores'], 'multi')
        self.assertEqual(result['memory_size'], 'large')
        self.assertEqual(result['storage_type'], 'ssd')
        self.assertEqual(result['network_type'], 'ethernet')
        self.assertEqual(result['graphics_type'], 'integrated')
    
    def test_get_profile_best_practices(self):
        """Test getting best practices for a hardware profile."""
        # Create a test profile
        profile = {
            'system_type': 'desktop',
            'cpu_cores': 'multi',
            'memory_size': 'large',
            'storage_type': 'ssd',
            'network_type': 'ethernet',
            'graphics_type': 'integrated'
        }
        
        # Call the method under test
        result = self.optimizer._get_profile_best_practices(profile)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('general', result)
        self.assertIn('cpu', result)
        self.assertIn('memory', result)
        self.assertIn('storage', result)
        self.assertIn('network', result)
        self.assertIn('graphics', result)
        
        # Verify that best practices were selected based on profile
        self.assertIn('CONFIG_PREEMPT', result['general'])
        self.assertIn('CONFIG_SMP', result['cpu'])
        self.assertIn('CONFIG_TRANSPARENT_HUGEPAGE', result['memory'])
        self.assertIn('CONFIG_IOSCHED_DEADLINE', result['storage'])
        self.assertIn('CONFIG_NET_SCHED', result['network'])
        self.assertIn('CONFIG_DRM', result['graphics'])
    
    def test_get_sysctl_recommendations(self):
        """Test getting sysctl recommendations."""
        # Call the method under test
        result = self.optimizer._get_sysctl_recommendations(self.test_hardware)
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('memory', result)
        self.assertIn('network', result)
        self.assertIn('storage', result)
        
        # Verify memory recommendations for large memory
        memory_recs = result['memory']
        self.assertGreater(len(memory_recs), 0)
        vm_dirty_ratio_rec = next((r for r in memory_recs if r['option'] == 'vm.dirty_ratio'), None)
        self.assertIsNotNone(vm_dirty_ratio_rec)
        
        # Verify network recommendations
        network_recs = result['network']
        self.assertGreater(len(network_recs), 0)
        rmem_max_rec = next((r for r in network_recs if r['option'] == 'net.core.rmem_max'), None)
        self.assertIsNotNone(rmem_max_rec)
        
        # Verify storage recommendations for SSD
        storage_recs = result['storage']
        self.assertGreater(len(storage_recs), 0)
        vfs_cache_pressure_rec = next((r for r in storage_recs if r['option'] == 'vm.vfs_cache_pressure'), None)
        self.assertIsNotNone(vfs_cache_pressure_rec)
    
    def test_is_value_compliant(self):
        """Test checking if a value is compliant with a recommended value."""
        # Test exact match
        self.assertTrue(self.optimizer._is_value_compliant('y', 'y'))
        self.assertTrue(self.optimizer._is_value_compliant('n', 'n'))
        self.assertTrue(self.optimizer._is_value_compliant('1000', '1000'))
        
        # Test boolean values
        self.assertTrue(self.optimizer._is_value_compliant('1', 'y'))
        self.assertTrue(self.optimizer._is_value_compliant('yes', 'y'))
        self.assertTrue(self.optimizer._is_value_compliant('true', 'y'))
        self.assertTrue(self.optimizer._is_value_compliant('0', 'n'))
        self.assertTrue(self.optimizer._is_value_compliant('no', 'n'))
        self.assertTrue(self.optimizer._is_value_compliant('false', 'n'))
        
        # Test numeric values with minimum requirement
        self.assertTrue(self.optimizer._is_value_compliant('1000', '>=500'))
        self.assertTrue(self.optimizer._is_value_compliant('500', '>=500'))
        self.assertFalse(self.optimizer._is_value_compliant('499', '>=500'))
        
        # Test numeric values with maximum requirement
        self.assertTrue(self.optimizer._is_value_compliant('500', '<=1000'))
        self.assertTrue(self.optimizer._is_value_compliant('1000', '<=1000'))
        self.assertFalse(self.optimizer._is_value_compliant('1001', '<=1000'))
        
        # Test non-compliant values
        self.assertFalse(self.optimizer._is_value_compliant('y', 'n'))
        self.assertFalse(self.optimizer._is_value_compliant('n', 'y'))
        self.assertFalse(self.optimizer._is_value_compliant('500', '1000'))


if __name__ == '__main__':
    unittest.main()