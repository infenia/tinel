#!/usr/bin/env python3
"""Tests for the Kernel Configuration Parser module.

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

from infenix.kernel.config_parser import KernelConfigParser
from infenix.interfaces import CommandResult, KernelConfig, KernelConfigOption


class TestKernelConfigParser(unittest.TestCase):
    """Test cases for the KernelConfigParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.parser = KernelConfigParser(self.mock_system)
    
    def test_parse_config(self):
        """Test parsing kernel configuration."""
        # Mock system interface responses
        self._setup_basic_mocks()
        
        # Call the method under test
        result = self.parser.parse_config()
        
        # Verify the result
        self.assertIsInstance(result, KernelConfig)
        self.assertEqual(result.version, '5.15.0-58-generic')
        self.assertIn('CONFIG_SMP', result.options)
        self.assertEqual(result.options['CONFIG_SMP'].value, 'y')
        self.assertEqual(result.options['CONFIG_SMP'].description, 'Symmetric multi-processing support')
    
    def test_parse_config_content(self):
        """Test parsing kernel configuration content."""
        config_content = """
# This is a comment
CONFIG_SMP=y
CONFIG_NR_CPUS=8
CONFIG_PREEMPT=n
CONFIG_MODULES=y
CONFIG_MODULE_UNLOAD=y
"""
        
        result = self.parser._parse_config_content(config_content)
        
        self.assertEqual(len(result), 5)
        self.assertEqual(result['CONFIG_SMP'].name, 'CONFIG_SMP')
        self.assertEqual(result['CONFIG_SMP'].value, 'y')
        self.assertEqual(result['CONFIG_NR_CPUS'].name, 'CONFIG_NR_CPUS')
        self.assertEqual(result['CONFIG_NR_CPUS'].value, '8')
        self.assertEqual(result['CONFIG_PREEMPT'].name, 'CONFIG_PREEMPT')
        self.assertEqual(result['CONFIG_PREEMPT'].value, 'n')
    
    def test_parse_modprobe_config(self):
        """Test parsing modprobe configuration."""
        # Mock system interface responses
        self.mock_system.file_exists.return_value = True
        self.mock_system.run_command.return_value = CommandResult(
            success=True,
            stdout='/etc/modprobe.d/blacklist.conf\n/etc/modprobe.d/options.conf',
            stderr='',
            returncode=0
        )
        self.mock_system.read_file.side_effect = lambda path: {
            '/etc/modprobe.d/blacklist.conf': '# Blacklist file\nblacklist nouveau\nblacklist floppy',
            '/etc/modprobe.d/options.conf': '# Options file\noptions snd_hda_intel power_save=1\noptions iwlwifi power_save=1'
        }.get(path, None)
        
        result = self.parser._parse_modprobe_config()
        
        self.assertEqual(len(result), 4)
        self.assertEqual(result['MODPROBE_BLACKLIST_NOUVEAU'].name, 'MODPROBE_BLACKLIST_NOUVEAU')
        self.assertEqual(result['MODPROBE_BLACKLIST_NOUVEAU'].value, 'y')
        self.assertEqual(result['MODPROBE_BLACKLIST_FLOPPY'].name, 'MODPROBE_BLACKLIST_FLOPPY')
        self.assertEqual(result['MODPROBE_BLACKLIST_FLOPPY'].value, 'y')
        self.assertEqual(result['MODPROBE_SND_HDA_INTEL'].name, 'MODPROBE_SND_HDA_INTEL')
        self.assertEqual(result['MODPROBE_SND_HDA_INTEL'].value, 'power_save=1')
        self.assertEqual(result['MODPROBE_IWLWIFI'].name, 'MODPROBE_IWLWIFI')
        self.assertEqual(result['MODPROBE_IWLWIFI'].value, 'power_save=1')
    
    def _setup_basic_mocks(self):
        """Set up basic mocks for system interface."""
        # Mock kernel version
        self.mock_system.run_command.side_effect = lambda cmd: {
            'uname -r': 
                CommandResult(True, '5.15.0-58-generic', '', 0),
            'ls /etc/modprobe.d/*.conf': 
                CommandResult(True, '/etc/modprobe.d/blacklist.conf', '', 0),
            'ls /boot/config-*': 
                CommandResult(True, '/boot/config-5.15.0-58-generic', '', 0),
            'zcat /proc/config.gz': 
                CommandResult(False, '', 'File not found', 1),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))
        
        # Mock file existence
        self.mock_system.file_exists.side_effect = lambda path: {
            '/proc/config.gz': False,
            '/boot/config-5.15.0-58-generic': True,
            '/etc/modprobe.d': True,
            '/etc/modprobe.d/blacklist.conf': True,
        }.get(path, False)
        
        # Mock file content
        self.mock_system.read_file.side_effect = lambda path: {
            '/boot/config-5.15.0-58-generic': """
# Linux kernel configuration
CONFIG_SMP=y
CONFIG_NR_CPUS=8
CONFIG_PREEMPT=n
CONFIG_MODULES=y
CONFIG_MODULE_UNLOAD=y
""",
            '/etc/modprobe.d/blacklist.conf': '# Blacklist file\nblacklist nouveau',
        }.get(path, None)
        
        # Set up option descriptions
        self.parser.option_descriptions = {
            'CONFIG_SMP': 'Symmetric multi-processing support',
            'CONFIG_NR_CPUS': 'Maximum number of CPUs',
            'CONFIG_PREEMPT': 'Preemptible kernel',
            'CONFIG_MODULES': 'Loadable module support',
            'CONFIG_MODULE_UNLOAD': 'Module unloading support'
        }


if __name__ == '__main__':
    unittest.main()