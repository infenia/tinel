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

import json
import unittest
from unittest.mock import MagicMock, patch

from tinel.hardware.pci_analyzer import PCIAnalyzer
from tinel.interfaces import CommandResult


class TestPCIAnalyzer(unittest.TestCase):
    def test_get_pci_info_success(self):
        mock_system_interface = MagicMock()
        mock_lshw_output = {
            "id": "computer",
            "children": [
                {
                    "id": "core",
                    "children": [
                        {
                            "id": "pci:0",
                            "businfo": "pci@0000:00:00.0",
                            "children": [
                                {
                                    "id": "pci:0",
                                    "class": "bridge",
                                    "vendor": "Intel Corporation [8086]",
                                    "product": "Device 3ec4 [3ec4]",
                                    "slot": "00:00.0",
                                    "businfo": "pci@0000:00:00.0",
                                    "version": "07",
                                    "width": 64,
                                    "configuration": {"driver": "skl_uncore"},
                                    "description": "Host bridge",
                                    "capabilities": {"msi": "Message Signalled Interrupts"},
                                    "resources": {"irq": "0", "memory": "d9000000-d9ffffff"},
                                },
                                {
                                    "id": "pci:1",
                                    "class": "display",
                                    "vendor": "NVIDIA Corporation [10de]",
                                    "product": "GP106 [GeForce GTX 1060 6GB] [1c03]",
                                    "slot": "01:00.0",
                                    "businfo": "pci@0000:01:00.0",
                                    "version": "a1",
                                    "width": 64,
                                    "configuration": {"driver": "nvidia"},
                                    "description": "VGA compatible controller",
                                    "capabilities": {"bus_master": "bus mastering"},
                                    "resources": {"memory": "da000000-daffffff"},
                                },
                            ],
                        }
                    ],
                }
            ],
        }
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=json.dumps(mock_lshw_output),
            stderr="",
            returncode=0,
        )

        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        mock_system_interface.run_command.assert_called_once_with("lshw -json -numeric")
        self.assertEqual(len(pci_info.devices), 2)

        # Device 1
        self.assertEqual(pci_info.devices[0].slot, "00:00.0")
        self.assertEqual(pci_info.devices[0].description, "Host bridge")
        self.assertEqual(pci_info.devices[0].details['vendor'], "Intel Corporation")
        self.assertEqual(pci_info.devices[0].details['device'], "Device 3ec4")
        self.assertEqual(pci_info.devices[0].vendor_id, "8086")
        self.assertEqual(pci_info.devices[0].device_id, "3ec4")
        self.assertEqual(pci_info.devices[0].driver, "skl_uncore")
        self.assertIn("msi", pci_info.devices[0].capabilities)

        # Device 2
        self.assertEqual(pci_info.devices[1].slot, "01:00.0")
        self.assertEqual(pci_info.devices[1].description, "VGA compatible controller")
        self.assertEqual(pci_info.devices[1].details['vendor'], "NVIDIA Corporation")
        self.assertEqual(pci_info.devices[1].details['device'], "GP106 [GeForce GTX 1060 6GB]")
        self.assertEqual(pci_info.devices[1].vendor_id, "10de")
        self.assertEqual(pci_info.devices[1].device_id, "1c03")
        self.assertEqual(pci_info.devices[1].driver, "nvidia")
        self.assertIn("bus_master", pci_info.devices[1].capabilities)


    @patch('tinel.hardware.pci_analyzer.log')
    def test_get_pci_info_command_failure(self, mock_log):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="lshw not found", returncode=127),
            CommandResult(success=False, stdout="", stderr="lspci not found", returncode=127)
        ]
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 0)
        mock_log.warning.assert_called_once_with("lshw failed, falling back to lspci.")
        mock_log.error.assert_called_once_with("Failed to run lspci.")

    @patch('tinel.hardware.pci_analyzer.log')
    def test_get_pci_info_json_decode_error(self, mock_log):
        mock_system_interface = MagicMock()
        # lshw gives bad json, lspci works
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="not json", stderr="", returncode=0),
            CommandResult(success=True, stdout="Slot:\t00:00.0\nClass:\tHost bridge\nVendor:\tIntel Corporation [8086]\nDevice:\tDevice 3ec4 [3ec4]\nDriver:\tskl_uncore\n", stderr="", returncode=0)
        ]
        analyzer = PCIAnalyzer(system_interface=mock_system_interface)
        pci_info = analyzer.get_pci_info()

        self.assertEqual(len(pci_info.devices), 1)
        self.assertEqual(pci_info.devices[0].vendor_id, "8086")
        self.assertEqual(pci_info.devices[0].device_id, "3ec4")
        mock_log.warning.assert_any_call("Failed to parse lshw JSON output.")
        mock_log.warning.assert_any_call("lshw failed, falling back to lspci.")


if __name__ == "__main__":
    unittest.main()