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

# This mock data is formatted to avoid line length issues in the source code,
# while still representing the single-line output from the actual command.
MOCK_LSPCI_V_OUTPUT = (
    "00:00.0 Host bridge: Intel Corporation 8th Gen Core Processor "
    "Host Bridge/DRAM Registers (rev 07)\n"
    "\tSubsystem: Dell Inc. 8th Gen Core Processor Host Bridge/DRAM Registers\n"
    "\tFlags: bus master, fast devsel, latency 0\n"
    "\tMemory at d0000000 (64-bit, non-prefetchable) [size=16M]\n"
    "\tCapabilities: [e0] Vendor Specific Information: id=0001 Rev=0 Len=014 <?>\n\n"
    "00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 620 (rev 07)\n"
    "\tSubsystem: Dell Inc. UHD Graphics 620\n"
    "\tFlags: bus master, fast devsel, latency 0, IRQ 129\n"
    "\tMemory at c0000000 (64-bit, non-prefetchable) [size=16M]\n"
    "\tMemory at b0000000 (64-bit, prefetchable) [size=256M]\n"
    "\tI/O ports at 3000 [size=64]\n"
    "\tCapabilities: [40] Vendor Specific Information: Len=0c <?>\n"
)


class TestPCIAnalyzer(unittest.TestCase):
    def test_get_pci_info_parses_lspci_output_correctly(self):
        """Verify that the PCI analyzer correctly parses 'lspci -v' output."""
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
        """Test that get_pci_info returns an empty list when the command fails."""
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

    def test_get_pci_info_with_empty_output(self):
        """Test that get_pci_info returns an empty list for empty command output."""
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

    def test_get_pci_info_with_malformed_output(self):
        """Test that get_pci_info returns an empty list for malformed output."""
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
