#!/usr/bin/env python3
"""
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

import unittest
from unittest.mock import Mock, call

from tinel.hardware.usb_analyzer import USBAnalyzer
from tinel.interfaces import CommandResult

# Sample output from 'lsusb -t' for mocking
MOCK_LSUSB_T_OUTPUT = """
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 5000M
    |__ Port 2: Dev 2, If 0, Class=Video, Driver=uvcvideo, 480M
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/10p, 480M
    |__ Port 4: Dev 2, If 0, Class=Human Interface Device, Driver=usbhid, 12M
    |__ Port 5: Dev 3, If 0, Class=Wireless, Driver=btusb, 12M
"""

# Mock data for sysfs reads
MOCK_SYSFS_DATA = {
    # Bus 2, Device 1 (Root Hub)
    "/sys/bus/usb/devices/2-1/busnum": "2",
    "/sys/bus/usb/devices/2-1/devnum": "1",
    "/sys/bus/usb/devices/2-1/idVendor": "1d6b",
    "/sys/bus/usb/devices/2-1/idProduct": "0003",
    "/sys/bus/usb/devices/2-1/manufacturer": "Linux Foundation",
    "/sys/bus/usb/devices/2-1/product": "3.0 root hub",
    # Bus 2, Device 2 (Webcam)
    "/sys/bus/usb/devices/2-2/busnum": "2",
    "/sys/bus/usb/devices/2-2/devnum": "2",
    "/sys/bus/usb/devices/2-2/idVendor": "0bda",
    "/sys/bus/usb/devices/2-2/idProduct": "579c",
    "/sys/bus/usb/devices/2-2/manufacturer": "Generic",
    "/sys/bus/usb/devices/2-2/product": "Webcam",
    # Bus 1, Device 1 (Root Hub)
    "/sys/bus/usb/devices/1-1/busnum": "1",
    "/sys/bus/usb/devices/1-1/devnum": "1",
    "/sys/bus/usb/devices/1-1/idVendor": "1d6b",
    "/sys/bus/usb/devices/1-1/idProduct": "0002",
    "/sys/bus/usb/devices/1-1/manufacturer": "Linux Foundation",
    "/sys/bus/usb/devices/1-1/product": "2.0 root hub",
    # Bus 1, Device 2 (Bluetooth)
    "/sys/bus/usb/devices/1-2/busnum": "1",
    "/sys/bus/usb/devices/1-2/devnum": "2",
    "/sys/bus/usb/devices/1-2/idVendor": "8087",
    "/sys/bus/usb/devices/1-2/idProduct": "0a2a",
    "/sys/bus/usb/devices/1-2/manufacturer": "Intel Corp.",
    "/sys/bus/usb/devices/1-2/product": "Bluetooth wireless interface",
    # Bus 1, Device 3 (Wireless)
    "/sys/bus/usb/devices/1-3/busnum": "1",
    "/sys/bus/usb/devices/1-3/devnum": "3",
    "/sys/bus/usb/devices/1-3/idVendor": "0a5c",
    "/sys/bus/usb/devices/1-3/idProduct": "21e8",
    "/sys/bus/usb/devices/1-3/manufacturer": "Broadcom Corp",
    "/sys/bus/usb/devices/1-3/product": "BCM20702A0",
}

MOCK_LSUSB_OUTPUT = """
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 002 Device 002: ID 0bda:579c Realtek Semiconductor Corp. Webcam
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 001 Device 002: ID 8087:0a2a Intel Corp.
Bus 001 Device 003: ID 0a5c:21e8 Broadcom Corp. BCM20702A0
"""


class TestUSBAnalyzer(unittest.TestCase):
    def test_get_usb_info_with_sysfs_details(self):
        """Verify that the analyzer enriches USB data with sysfs details."""
        mock_system_interface = Mock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=MOCK_LSUSB_T_OUTPUT,
            stderr="",
            returncode=0,
        )
        analyzer = USBAnalyzer(system_interface=mock_system_interface)

        def mock_read_file(path):
            if path in MOCK_SYSFS_DATA:
                return MOCK_SYSFS_DATA[path]
            raise FileNotFoundError(f"File not found: {path}")

        analyzer.system.read_file = Mock(side_effect=mock_read_file)
        # Provide a complete list of directories to search through
        analyzer.system.list_dir.return_value = [
            "1-1",
            "1-2",
            "1-3",
            "2-1",
            "2-2",
            "usb1",
            "usb2",
        ]

        usb_info = analyzer.get_usb_info()

        # Assert that lsusb was NOT called as a fallback
        mock_system_interface.run_command.assert_called_once_with(["lsusb", "-t"])

        root_hubs = usb_info.tree.get("root_hubs", [])
        self.assertEqual(len(root_hubs), 2)

        webcam = root_hubs[0]["children"][0]
        self.assertEqual(webcam["vendor_id"], "0bda")
        self.assertEqual(webcam["product_id"], "579c")
        self.assertEqual(webcam["manufacturer"], "Generic")
        self.assertEqual(webcam["product"], "Webcam")

        bluetooth = root_hubs[1]["children"][0]
        self.assertEqual(bluetooth["vendor_id"], "8087")
        self.assertEqual(bluetooth["product_id"], "0a2a")

    def test_get_usb_info_fallback_to_lsusb(self):
        """Test that the analyzer falls back to lsusb when sysfs fails."""
        mock_system_interface = Mock()
        # Mock the sequence of command calls: first lsusb -t, then lsusb
        mock_system_interface.run_command.side_effect = [
            CommandResult(
                success=True,
                stdout=MOCK_LSUSB_T_OUTPUT,
                stderr="",
                returncode=0,
            ),
            CommandResult(
                success=True,
                stdout=MOCK_LSUSB_OUTPUT,
                stderr="",
                returncode=0,
            ),
        ]
        # Simulate a sysfs failure by returning an empty list of directories
        mock_system_interface.list_dir.return_value = []
        analyzer = USBAnalyzer(system_interface=mock_system_interface)

        usb_info = analyzer.get_usb_info()

        # Assert that lsusb -t and lsusb were both called
        mock_system_interface.run_command.assert_has_calls(
            [call(["lsusb", "-t"]), call(["lsusb"])]
        )
        self.assertEqual(mock_system_interface.run_command.call_count, 2)

        root_hubs = usb_info.tree.get("root_hubs", [])
        self.assertEqual(len(root_hubs), 2)

        # Check the first root hub and its child (Webcam)
        hub1 = root_hubs[0]
        self.assertEqual(hub1["vendor_id"], "1d6b")
        self.assertEqual(hub1["product_id"], "0003")
        webcam = hub1["children"][0]
        self.assertEqual(webcam["vendor_id"], "0bda")
        self.assertEqual(webcam["product_id"], "579c")

        # Check the second root hub and its children
        hub2 = root_hubs[1]
        self.assertEqual(hub2["vendor_id"], "1d6b")
        self.assertEqual(hub2["product_id"], "0002")
        bluetooth = hub2["children"][0]
        self.assertEqual(bluetooth["vendor_id"], "8087")
        self.assertEqual(bluetooth["product_id"], "0a2a")
        wireless = hub2["children"][1]
        self.assertEqual(wireless["vendor_id"], "0a5c")
        self.assertEqual(wireless["product_id"], "21e8")

    def test_get_usb_info_handles_command_failure(self):
        """
        Test that get_usb_info returns an empty tree when the lsusb -t command fails.
        """
        mock_system_interface = Mock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="Command not found", returncode=1
        )
        analyzer = USBAnalyzer(system_interface=mock_system_interface)

        usb_info = analyzer.get_usb_info()

        self.assertEqual(usb_info.tree, {"root_hubs": []})