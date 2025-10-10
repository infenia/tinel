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

from tinel.hardware.pci_analyzer import PCIAnalyzer
from tinel.interfaces import CommandResult

# Sample output from 'lspci -v' for mocking
MOCK_LSPCI_V_OUTPUT = """
00:00.0 Host bridge: Intel Corporation 8th Gen Core Processor Host Bridge/DRAM
Registers (rev 07)
	Subsystem: Dell Inc. 8th Gen Core Processor Host Bridge/DRAM Registers
	Flags: bus master, fast devsel, latency 0
	Memory at d0000000 (64-bit, non-prefetchable) [size=16M]
	Capabilities: [e0] Vendor Specific Information: id=0001 Rev=0 Len=014 <?>

00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 620 (rev 07)
	Subsystem: Dell Inc. UHD Graphics 620
	Flags: bus master, fast devsel, latency 0, IRQ 129
	Memory at c0000000 (64-bit, non-prefetchable) [size=16M]
	Memory at b0000000 (64-bit, prefetchable) [size=256M]
	I/O ports at 3000 [size=64]
	Capabilities: [40] Vendor Specific Information: Len=0c <?>
"""


class TestPCIAnalyzer(unittest.TestCase):
    def test_get_pci_info_parses_lspci_output_correctly(self):
        """
        Verify that the PCI analyzer correctly parses the output of 'lspci -v'.
        """
        # Arrange
        mock_system_interface = Mock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=MOCK_LSPCI_V_OUTPUT,
            stderr="",
            returncode=0,
            error=None,
        )
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)

        # Act
        pci_info = analyzer.get_pci_info()

        # Assert
        mock_system_interface.run_command.assert_called_once_with(["lspci", "-v"])
        self.assertEqual(len(pci_info.devices), 2)

        # Check the first device
        device1 = pci_info.devices[0]
        self.assertEqual(device1["slot"], "00:00.0")
        self.assertEqual(
            device1["description"],
            (
                "Host bridge: Intel Corporation 8th Gen Core Processor "
                "Host Bridge/DRAM Registers (rev 07)"
            ),
        )
        self.assertEqual(
            device1["subsystem"],
            "Dell Inc. 8th Gen Core Processor Host Bridge/DRAM Registers",
        )
        self.assertIn(
            "Memory at d0000000 (64-bit, non-prefetchable) [size=16M]",
            device1["details"],
        )

        # Check the second device
        device2 = pci_info.devices[1]
        self.assertEqual(device2["slot"], "00:02.0")
        self.assertEqual(
            device2["description"],
            "VGA compatible controller: Intel Corporation UHD Graphics 620 (rev 07)",
        )
        self.assertEqual(device2["subsystem"], "Dell Inc. UHD Graphics 620")
        self.assertIn("I/O ports at 3000 [size=64]", device2["details"])
        self.assertIn("capabilities", device2)

    def test_get_pci_info_handles_command_failure(self):
        """
        Test that get_pci_info returns an empty list when the command fails.
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
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)

        # Act
        pci_info = analyzer.get_pci_info()

        # Assert
        self.assertEqual(pci_info.devices, [])

    def test_get_pci_info_with_malformed_output(self):
        """
        Test that get_pci_info returns an empty list for malformed output.
        """
        # Arrange
        mock_system_interface = Mock()
        malformed_output = "This is not valid lspci output\nJust some random text."
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=malformed_output,
            stderr="",
            returncode=0,
            error=None,
        )
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)

        # Act
        pci_info = analyzer.get_pci_info()

        # Assert
        self.assertEqual(pci_info.devices, [])

    def test_get_pci_info_with_empty_output(self):
        """
        Test that get_pci_info returns an empty list for empty command output.
        """
        # Arrange
        mock_system_interface = Mock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="", stderr="", returncode=0, error=None
        )
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)

        # Act
        pci_info = analyzer.get_pci_info()

        # Assert
        self.assertEqual(pci_info.devices, [])
