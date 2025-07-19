#!/usr/bin/env python3
"""Tests for the USB Analyzer module.

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

from infenix.hardware.usb_analyzer import USBAnalyzer
from infenix.interfaces import CommandResult


class TestUSBAnalyzer(unittest.TestCase):
    """Test cases for the USBAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.analyzer = USBAnalyzer(self.mock_system)
        
        # Mock the USB IDs database loading
        self.analyzer.vendor_db = {'8087': 'Intel Corp.', '046d': 'Logitech, Inc.'}
        self.analyzer.product_db = {
            '8087': {'0024': 'Integrated Rate Matching Hub'},
            '046d': {'c52b': 'Unifying Receiver'}
        }
    
    def test_get_usb_devices(self):
        """Test getting comprehensive USB device information."""
        # Mock system interface responses
        self._setup_basic_mocks()
        
        # Call the method under test
        result = self.analyzer.get_usb_devices()
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('devices', result)
        self.assertGreater(len(result['devices']), 0)
    
    def test_parse_lsusb_output(self):
        """Test parsing lsusb output."""
        lsusb_output = '''Bus 001 Device 002: ID 8087:0024 Intel Corp. Integrated Rate Matching Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 003: ID 046d:c52b Logitech, Inc. Unifying Receiver'''
        
        result = self.analyzer._parse_lsusb_output(lsusb_output)
        
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]['bus'], '001')
        self.assertEqual(result[0]['device'], '002')
        self.assertEqual(result[0]['vendor_id'], '8087')
        self.assertEqual(result[0]['product_id'], '0024')
        self.assertEqual(result[0]['description'], 'Intel Corp. Integrated Rate Matching Hub')
        self.assertEqual(result[0]['vendor'], 'Intel Corp.')
        self.assertEqual(result[0]['product'], 'Integrated Rate Matching Hub')
    
    def test_parse_usb_tree(self):
        """Test parsing lsusb -t output."""
        usb_tree_output = '''/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=ehci-pci/2p, 480M
    |__ Port 1: Dev 2, If 0, Class=Hub, Driver=hub/8p, 480M
        |__ Port 1: Dev 3, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
        |__ Port 2: Dev 4, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 5000M'''
        
        result = self.analyzer._parse_usb_tree(usb_tree_output)
        
        self.assertEqual(len(result), 2)  # Two root hubs
        self.assertEqual(result[0]['port'], '1')
        self.assertEqual(result[0]['device'], '1')
        self.assertEqual(result[0]['class'], 'root_hub')
        self.assertEqual(result[0]['driver'], 'ehci-pci/2p')
        self.assertEqual(len(result[0]['children']), 1)  # One child hub
        self.assertEqual(len(result[0]['children'][0]['children']), 2)  # Two devices on the hub
    
    def _setup_basic_mocks(self):
        """Set up basic mocks for system interface."""
        # Mock lsusb output
        lsusb_output = '''Bus 001 Device 002: ID 8087:0024 Intel Corp. Integrated Rate Matching Hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 003: ID 046d:c52b Logitech, Inc. Unifying Receiver'''
        
        # Mock lsusb -t output
        usb_tree_output = '''/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=ehci-pci/2p, 480M
    |__ Port 1: Dev 2, If 0, Class=Hub, Driver=hub/8p, 480M
        |__ Port 1: Dev 3, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
        |__ Port 2: Dev 4, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 5000M'''
        
        # Mock ls /sys/bus/usb/devices/ output
        ls_sys_usb_output = '''1-0:1.0
1-1
1-1:1.0
1-1.1
1-1.1:1.0
1-1.2
1-1.2:1.0
2-0:1.0
2-1
2-1:1.0'''
        
        # Set up mock responses
        self.mock_system.run_command.side_effect = lambda cmd: {
            'lsusb': 
                CommandResult(True, lsusb_output, '', 0),
            'lsusb -t': 
                CommandResult(True, usb_tree_output, '', 0),
            'ls /sys/bus/usb/devices/': 
                CommandResult(True, ls_sys_usb_output, '', 0),
            'uname -r': 
                CommandResult(True, '5.15.0-58-generic', '', 0),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))
        
        # Mock file_exists
        self.mock_system.file_exists.return_value = True
        
        # Mock read_file for USB IDs database
        self.mock_system.read_file.side_effect = lambda path: {
            '/usr/share/hwdata/usb.ids': '''# USB ID Database
8087  Intel Corp.
	0024  Integrated Rate Matching Hub
046d  Logitech, Inc.
	c52b  Unifying Receiver
''',
            '/sys/bus/usb/devices/1-1/idVendor': '8087',
            '/sys/bus/usb/devices/1-1/idProduct': '0024',
            '/sys/bus/usb/devices/1-1/manufacturer': 'Intel Corp.',
            '/sys/bus/usb/devices/1-1/product': 'Integrated Rate Matching Hub',
            '/sys/bus/usb/devices/1-1/speed': '480',
            '/sys/bus/usb/devices/1-1/version': '2.00',
            '/sys/bus/usb/devices/1-1/bDeviceClass': '09',
        }.get(path, None)


if __name__ == '__main__':
    unittest.main()