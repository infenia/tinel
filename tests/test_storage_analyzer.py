#!/usr/bin/env python3
"""Tests for the Storage Analyzer module.

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

import json
import unittest
from unittest.mock import MagicMock, patch

from infenix.hardware.storage_analyzer import StorageAnalyzer
from infenix.interfaces import CommandResult


class TestStorageAnalyzer(unittest.TestCase):
    """Test cases for the StorageAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.analyzer = StorageAnalyzer(self.mock_system)
    
    def test_get_storage_info(self):
        """Test getting comprehensive storage information."""
        # Mock system interface responses
        self._setup_basic_mocks()
        
        # Call the method under test
        result = self.analyzer.get_storage_info()
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('lsblk', result)
        self.assertIn('filesystems', result)
    
    def test_parse_df_output(self):
        """Test parsing df command output."""
        df_output = """Filesystem     Size  Used Avail Use% Mounted on
/dev/sda1       50G   20G   30G  40% /
/dev/sdb1      100G   50G   50G  50% /data
"""
        result = self.analyzer._parse_df_output(df_output)
        
        self.assertIn('filesystems', result)
        self.assertEqual(len(result['filesystems']), 2)
        self.assertEqual(result['filesystems'][0]['filesystem'], '/dev/sda1')
        self.assertEqual(result['filesystems'][0]['size'], '50G')
        self.assertEqual(result['filesystems'][0]['used'], '20G')
        self.assertEqual(result['filesystems'][0]['available'], '30G')
        self.assertEqual(result['filesystems'][0]['use_percent'], '40%')
        self.assertEqual(result['filesystems'][0]['mountpoint'], '/')
    
    def test_parse_smart_health(self):
        """Test parsing SMART health status."""
        passed_output = "SMART overall-health self-assessment test result: PASSED"
        failed_output = "SMART overall-health self-assessment test result: FAILED"
        unknown_output = "SMART overall-health self-assessment test result: UNKNOWN"
        
        self.assertEqual(self.analyzer._parse_smart_health(passed_output), "PASSED")
        self.assertEqual(self.analyzer._parse_smart_health(failed_output), "FAILED")
        self.assertEqual(self.analyzer._parse_smart_health(unknown_output), "UNKNOWN")
    
    def test_check_high_usage_filesystems(self):
        """Test checking for filesystems with high usage."""
        df_output = """Filesystem     Size  Used Avail Use% Mounted on
/dev/sda1       50G   20G   30G  40% /
/dev/sdb1      100G   90G   10G  90% /data
/dev/sdc1      200G  180G   20G  90% /backup
"""
        result = self.analyzer._check_high_usage_filesystems(df_output)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['filesystem'], '/dev/sdb1')
        self.assertEqual(result[0]['mountpoint'], '/data')
        self.assertEqual(result[0]['usage_percent'], '90')
    
    def test_is_ssd(self):
        """Test SSD detection."""
        # Mock system interface
        self.mock_system.read_file.return_value = '0'  # 0 means non-rotational (SSD)
        
        # Test with SSD device
        self.assertTrue(self.analyzer._is_ssd('/dev/sda'))
        
        # Test with rotational device
        self.mock_system.read_file.return_value = '1'  # 1 means rotational (HDD)
        self.assertFalse(self.analyzer._is_ssd('/dev/sdb'))
    
    def _setup_basic_mocks(self):
        """Set up basic mocks for system interface."""
        # Mock lsblk JSON output
        lsblk_json = {
            "blockdevices": [
                {
                    "name": "sda",
                    "size": "100G",
                    "type": "disk",
                    "mountpoint": None,
                    "children": [
                        {
                            "name": "sda1",
                            "size": "100G",
                            "type": "part",
                            "mountpoint": "/"
                        }
                    ]
                }
            ]
        }
        
        # Mock df output
        df_output = """Filesystem     Size  Used Avail Use% Mounted on
/dev/sda1       100G   50G   50G  50% /
"""
        
        # Mock mount output
        mount_output = """/dev/sda1 on / type ext4 (rw,relatime)
"""
        
        # Set up mock responses
        self.mock_system.run_command.side_effect = lambda cmd: {
            'lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,SERIAL,VENDOR,ROTA,TRAN': 
                CommandResult(True, json.dumps(lsblk_json), '', 0),
            'df -h': 
                CommandResult(True, df_output, '', 0),
            'mount': 
                CommandResult(True, mount_output, '', 0),
            'lsblk -d -n -o NAME':
                CommandResult(True, 'sda\n', '', 0),
            'iostat -x -d':
                CommandResult(True, 'Device  r/s  w/s\nsda  10.0  20.0\n', '', 0),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))


if __name__ == '__main__':
    unittest.main()