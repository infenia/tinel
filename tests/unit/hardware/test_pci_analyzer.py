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
from unittest.mock import MagicMock
import json

from tinel.hardware.pci_analyzer import PCIAnalyzer
from tinel.interfaces import CommandResult


class TestPCIAnalyzer(unittest.TestCase):
    def test_get_pci_info_lshw_success(self):
        """Test successful parsing of lshw JSON output."""
        mock_system_interface = MagicMock()
        lshw_output = {
            "id": "computer",
            "children": [
                {
                    "id": "core",
                    "children": [
                        {
                            "id": "pci",
                            "children": [
                                {
                                    "id": "pci:0",
                                    "businfo": "pci@0000:00:00.0",
                                    "slot": "00:00.0",
                                    "class": "bridge",
                                    "vendor": "Intel Corporation [8086]",
                                    "product": "Host Bridge [3ec4]",
                                    "description": "Host bridge",
                                    "configuration": {"driver": "skl_uncore"},
                                    "width": 64,
                                    "capabilities": {"pci": "PCI Express"},
                                    "resources": {"memory": "f0000000-ffffffff"},
                                },
                                {
                                    "id": "pci:1",
                                    "businfo": "pci@0000:01:00.0",
                                    "slot": "01:00.0",
                                    "class": "display",
                                    "vendor": "NVIDIA Corporation [10de]",
                                    "product": "VGA Controller [1c8c]",
                                    "description": "VGA compatible controller",
                                    "configuration": {"driver": "nvidia"},
                                    "width": 64,
                                    "capabilities": {"vga_controller": "VGA controller"},
                                    "resources": {"memory": "a0000000-afffffff"},
                                },
                            ],
                        }
                    ],
                }
            ],
        }
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=json.dumps(lshw_output),
            stderr="",
            returncode=0,
        )

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 2)
        device1 = pci_info.devices[0]
        self.assertEqual(device1.slot, "00:00.0")
        self.assertEqual(device1.vendor_id, "8086")
        self.assertEqual(device1.device_id, "3ec4")
        self.assertEqual(device1.driver, "skl_uncore")
        self.assertEqual(device1.details["vendor"], "Intel Corporation")
        self.assertEqual(device1.details["device"], "Host Bridge")

        device2 = pci_info.devices[1]
        self.assertEqual(device2.slot, "01:00.0")
        self.assertEqual(device2.vendor_id, "10de")
        self.assertEqual(device2.device_id, "1c8c")
        self.assertEqual(device2.driver, "nvidia")

    def test_get_pci_info_lshw_fail_fallback_to_lspci(self):
        """Test fallback to lspci when lshw fails."""
        mock_system_interface = MagicMock()
        # First call for lshw fails
        # Second call for lspci succeeds
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="lshw not found", returncode=127),
            CommandResult(
                success=True,
                stdout="""Slot:\t00:00.0
Class:\tHost bridge
Vendor:\tIntel Corporation [8086]
Device:\tDevice [3ec4]
Driver:\tskl_uncore

Slot:\t01:00.0
Class:\tVGA compatible controller
Vendor:\tNVIDIA Corporation [10de]
Device:\tDevice [1c8c]
Driver:\tnvidia
""",
                stderr="",
                returncode=0,
            ),
        ]

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 2)
        self.assertEqual(pci_info.devices[0].slot, "00:00.0")
        self.assertEqual(pci_info.devices[0].vendor_id, "8086")
        self.assertEqual(pci_info.devices[0].device_id, "3ec4")
        self.assertEqual(pci_info.devices[0].driver, "skl_uncore")
        self.assertEqual(pci_info.devices[1].slot, "01:00.0")
        self.assertEqual(pci_info.devices[1].vendor_id, "10de")
        self.assertEqual(pci_info.devices[1].device_id, "1c8c")
        self.assertEqual(pci_info.devices[1].driver, "nvidia")

    def test_get_pci_info_all_tools_fail(self):
        """Test that an empty list is returned when both lshw and lspci fail."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="command not found", returncode=127
        )

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 0)

    def test_parse_lspci_correctly_populates_details(self):
        """Test that lspci output correctly populates the details dictionary."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="", returncode=1),
            CommandResult(
                success=True,
                stdout="""Slot:\t00:02.0
Class:\tVGA compatible controller
Vendor:\tIntel Corporation [8086]
Device:\tHD Graphics [1916]
SVendor:\tDell Inc.
SDevice:\tDevice [06e2]
Driver:\ti915
""",
                stderr="",
                returncode=0,
            ),
        ]
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 1)
        device = pci_info.devices[0]
        self.assertIsNotNone(device.details)
        self.assertEqual(device.details.get("vendor"), "Intel Corporation")
        self.assertEqual(device.details.get("device"), "HD Graphics")
        self.assertEqual(device.details.get("class"), "VGA compatible controller")
        self.assertEqual(device.subsystem, "Dell Inc. Device 06e2")

    def test_parse_lspci_with_leading_junk(self):
        """Test that the lspci parser skips leading junk lines."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
             CommandResult(success=False, stdout="", stderr="", returncode=1),
             CommandResult(
                success=True,
                stdout="""
Junk line that should be skipped because it doesn't contain a tab
Slot:\t00:00.0
Class:\tHost bridge
Vendor:\tIntel Corporation [8086]
Device:\tDevice [1234]
Rev:\t01
""",
                stderr="",
                returncode=0,
            )
        ]
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()
        self.assertEqual(len(pci_info.devices), 1)
        self.assertEqual(pci_info.devices[0].slot, "00:00.0")

    def test_get_pci_info_no_devices_found(self):
        """Test handling of empty output from lspci."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="", returncode=1),
            CommandResult(success=True, stdout="", stderr="", returncode=0)
        ]

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 0)

    def test_parse_lspci_no_device_at_end(self):
        """Test parsing when output ends with no current_device (empty lines only)."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="", returncode=1),
            CommandResult(success=True, stdout="\n\n", stderr="", returncode=0)
        ]

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 0)


if __name__ == "__main__":
    unittest.main()