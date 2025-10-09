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
from unittest.mock import Mock

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

class TestUSBAnalyzer(unittest.TestCase):
    def test_get_usb_info_parses_lsusb_t_output_correctly(self):
        """
        Verify that the USB analyzer correctly parses the hierarchical output of 'lsusb -t'.
        """
        # Arrange
        mock_system_interface = Mock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=MOCK_LSUSB_T_OUTPUT,
            stderr="",
            returncode=0,
            error=None,
        )
        analyzer = USBAnalyzer(system_interface=mock_system_interface)

        # Act
        usb_info = analyzer.get_usb_info()

        # Assert
        mock_system_interface.run_command.assert_called_once_with(["lsusb", "-t"])

        root_hubs = usb_info.tree.get("root_hubs", [])
        self.assertEqual(len(root_hubs), 2)

        # Check the first root hub and its child
        hub1 = root_hubs[0]
        self.assertEqual(hub1["bus"], "02")
        self.assertEqual(hub1["class"], "root_hub")
        self.assertEqual(len(hub1["children"]), 1)

        child1 = hub1["children"][0]
        self.assertEqual(child1["class"], "Video")
        self.assertEqual(child1["driver"], "uvcvideo")

        # Check the second root hub and its children
        hub2 = root_hubs[1]
        self.assertEqual(hub2["bus"], "01")
        self.assertEqual(len(hub2["children"]), 2)

        child2 = hub2["children"][0]
        self.assertEqual(child2["class"], "Human Interface Device")

        child3 = hub2["children"][1]
        self.assertEqual(child3["driver"], "btusb")

    def test_get_usb_info_handles_command_failure(self):
        """
        Test that get_usb_info returns an empty tree when the command fails.
        """
        # Arrange
        mock_system_interface = Mock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False,
            stdout="",
            stderr="Command not found",
            returncode=1,
            error="Command not found",
        )
        analyzer = USBAnalyzer(system_interface=mock_system_interface)

        # Act
        usb_info = analyzer.get_usb_info()

        # Assert
        self.assertEqual(usb_info.tree, {"root_hubs": []})

    def test_get_usb_info_with_malformed_output(self):
        """
        Test that get_usb_info handles malformed lines gracefully.
        """
        # Arrange
        mock_system_interface = Mock()
        malformed_output = "/: Malformed root hub line\n    |__ Malformed child line"
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=malformed_output,
            stderr="",
            returncode=0,
            error=None,
        )
        analyzer = USBAnalyzer(system_interface=mock_system_interface)

        # Act
        usb_info = analyzer.get_usb_info()

        # Assert
        self.assertEqual(usb_info.tree, {"root_hubs": []})

    def test_get_usb_info_with_empty_output(self):
        """
        Test that get_usb_info returns an empty tree for empty command output.
        """
        # Arrange
        mock_system_interface = Mock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="", stderr="", returncode=0, error=None
        )
        analyzer = USBAnalyzer(system_interface=mock_system_interface)

        # Act
        usb_info = analyzer.get_usb_info()

        # Assert
        self.assertEqual(usb_info.tree, {"root_hubs": []})