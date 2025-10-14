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

from tinel.hardware.pci_analyzer import PCIAnalyzer
from tinel.interfaces import CommandResult


class TestPCIAnalyzer(unittest.TestCase):
    def test_get_pci_info_success(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout="""00:00.0 Host bridge: Intel [8086:3ec4] (rev 07)
	Subsystem: Dell Inc. Device [1028:085b]
	Kernel driver in use: skl_uncore
01:00.0 VGA compatible controller: NVIDIA [10de:1c8c] (rev a1)
	Subsystem: Dell Inc. Device [1028:085b]
	Kernel driver in use: nvidia
""",
            stderr="",
            returncode=0,
        )

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 2)
        self.assertEqual(pci_info.devices[0]["slot"], "00:00.0")
        self.assertEqual(pci_info.devices[0]["vendor_id"], "8086")
        self.assertEqual(pci_info.devices[0]["device_id"], "3ec4")
        self.assertEqual(pci_info.devices[0]["driver"], "skl_uncore")
        self.assertEqual(pci_info.devices[1]["slot"], "01:00.0")
        self.assertEqual(pci_info.devices[1]["vendor_id"], "10de")
        self.assertEqual(pci_info.devices[1]["device_id"], "1c8c")
        self.assertEqual(pci_info.devices[1]["driver"], "nvidia")

    def test_get_pci_info_lspci_fail_fallback_to_sysfs(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="lspci not found", returncode=127
        )

        mock_system_interface.list_dir.return_value = ["0000:00:00.0", "0000:01:00.0"]
        mock_system_interface.read_file.side_effect = [
            "0x8086",
            "0x3ec4",
            "0x060000",
            "0x10de",
            "0x1c8c",
            "0x030000",
        ]
        mock_system_interface.readlink.side_effect = [
            "/sys/bus/pci/drivers/skl_uncore",
            "/sys/bus/pci/drivers/nvidia",
        ]

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 2)
        self.assertEqual(pci_info.devices[0]["slot"], "0000:00:00.0")
        self.assertEqual(pci_info.devices[0]["vendor_id"], "0x8086")
        self.assertEqual(pci_info.devices[0]["device_id"], "0x3ec4")
        self.assertEqual(pci_info.devices[0]["driver"], "skl_uncore")
        self.assertEqual(pci_info.devices[1]["slot"], "0000:01:00.0")
        self.assertEqual(pci_info.devices[1]["vendor_id"], "0x10de")
        self.assertEqual(pci_info.devices[1]["device_id"], "0x1c8c")
        self.assertEqual(pci_info.devices[1]["driver"], "nvidia")

    def test_get_pci_info_sysfs_fallback_missing_files(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="lspci not found", returncode=127
        )

        mock_system_interface.list_dir.return_value = ["0000:00:00.0"]
        # Simulate missing device file
        mock_system_interface.read_file.side_effect = ["0x8086", None, "0x060000"]
        mock_system_interface.readlink.return_value = ""

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 0)

    def test_get_pci_info_sysfs_fallback_no_devices(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="lspci not found", returncode=127
        )
        # Simulate no devices found in sysfs
        mock_system_interface.list_dir.return_value = []
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()
        self.assertEqual(len(pci_info.devices), 0)

    def test_get_pci_info_sysfs_fallback_device_permission_error(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="lspci not found", returncode=127
        )
        mock_system_interface.list_dir.return_value = ["0000:00:00.0"]
        mock_system_interface.read_file.side_effect = PermissionError("Denied")
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()
        self.assertEqual(len(pci_info.devices), 0)

    def test_get_pci_info_sysfs_fallback_no_driver(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="lspci not found", returncode=127
        )

        mock_system_interface.list_dir.return_value = ["0000:00:00.0"]
        mock_system_interface.read_file.side_effect = ["0x8086", "0x3ec4", "0x060000"]
        # Simulate no driver link
        mock_system_interface.readlink.return_value = ""

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 1)
        self.assertEqual(pci_info.devices[0]["driver"], "N/A")

    def test_parse_lspci_with_details_line(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout="""00:02.0 VGA compatible controller: Intel HD Graphics [8086:1916]
	Subsystem: Dell Inc. Device [1028:06e2]
	Kernel driver in use: i915
	some detail line
""",
            stderr="",
            returncode=0,
        )
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()
        self.assertIn("details", pci_info.devices[0])
        self.assertIn("some detail line", pci_info.devices[0]["details"])

    def test_parse_lspci_with_multiple_details_lines(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout="""00:02.0 VGA compatible controller: Intel HD Graphics [8086:1916]
	Subsystem: Dell Inc. Device [1028:06e2]
	detail 1
	detail 2
""",
            stderr="",
            returncode=0,
        )
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()
        self.assertIn("details", pci_info.devices[0])
        self.assertEqual(pci_info.devices[0]["details"], ["detail 1", "detail 2"])

    def test_parse_lspci_with_leading_junk(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout="""
Junk line
00:00.0 Host bridge: Intel Corporation Device [8086:1234] (rev 01)
""",
            stderr="",
            returncode=0,
        )
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()
        self.assertEqual(len(pci_info.devices), 1)
        self.assertEqual(pci_info.devices[0]["slot"], "00:00.0")

    def test_get_pci_info_no_devices_found(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="", stderr="", returncode=0
        )

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 0)

    def test_parse_lspci_no_device_at_end(self):
        """Test parsing when output ends with no current_device (empty lines only)."""
        mock_system_interface = MagicMock()
        # Output with only whitespace/empty lines, no device header
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout="""


""",
            stderr="",
            returncode=0,
        )

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        # Should handle gracefully with no devices
        self.assertEqual(len(pci_info.devices), 0)


if __name__ == "__main__":
    unittest.main()
