#!/usr/bin/env python3
"""
Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUTHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import unittest
from unittest.mock import MagicMock
from tinel.hardware.pci_analyzer import PCIAnalyzer
from tinel.hardware.models import PCIInfo, PCIDevice
from tinel.interfaces import CommandResult

class TestPCIAnalyzerCoverage(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = PCIAnalyzer(self.mock_system_interface)

    def test_get_pci_info_lshw_fails_and_lspci_fails(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="lshw failed", returncode=1),
            CommandResult(success=False, stdout="", stderr="lspci failed", returncode=1)
        ]
        pci_info = self.analyzer.get_pci_info()
        self.assertEqual(pci_info.devices, [])

    def test_get_pci_info_from_lspci_empty_output(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)
        devices = self.analyzer._get_pci_info_from_lspci()
        self.assertEqual(devices.devices, [])

    def test_parse_lshw_json_output_list_of_nodes(self):
        hardware_data = [{"businfo": "pci@0000:00:00.0", "slot": "00:00.0"}]
        devices = self.analyzer._parse_lshw_json_output(hardware_data)
        self.assertEqual(len(devices), 1)

    def test_parse_lspci_vmmk_output_malformed_line(self):
        output = "Slot:\t00:00.0\nVendor\tIntel Corporation" # Malformed line
        devices = self.analyzer._parse_lspci_vmmk_output(output)
        self.assertEqual(len(devices), 1)

    def test_create_pci_device_from_lspci_no_vendor(self):
        data = {"device": "Device [8086]"}
        device = self.analyzer._create_pci_device_from_lspci(data)
        self.assertIsNone(device.vendor_id)
        self.assertEqual(device.device_id, "8086")

    def test_create_pci_device_from_lspci_no_device(self):
        data = {"vendor": "Vendor [1234]"}
        device = self.analyzer._create_pci_device_from_lspci(data)
        self.assertEqual(device.vendor_id, "1234")
        self.assertIsNone(device.device_id)

    def test_parse_id_no_match(self):
        self.assertEqual(self.analyzer._parse_id("no id", is_vendor=True), (None, None))

    def test_parse_lshw_vendor_id_in_product(self):
        node = {"businfo": "pci@0000:00:01.0", "slot": "00:01.0", "product": "Device [8086:1234]"}
        devices = self.analyzer._parse_lshw_json_output(node)
        self.assertEqual(devices[0].vendor_id, "8086")
        self.assertEqual(devices[0].device_id, "1234")

    def test_parse_lshw_json_output_no_slot(self):
        node = {"businfo": "pci@0000:00:01.0"} # no slot
        devices = self.analyzer._parse_lshw_json_output(node)
        self.assertEqual(len(devices), 0)

    def test_get_pci_info_json_decode_error(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="{not json}", stderr="", returncode=0),
            CommandResult(success=True, stdout="", stderr="", returncode=0)
        ]
        pci_info = self.analyzer.get_pci_info()
        self.assertEqual(pci_info.devices, [])

    def test_parse_id_vendor_only(self):
        vendor_id, device_id = self.analyzer._parse_id("Vendor [1234]", is_vendor=True)
        self.assertEqual(vendor_id, "1234")
        self.assertIsNone(device_id)

    def test_create_pci_device_from_lspci_with_subsystem_id(self):
        data = {"svendor": "SubVendor", "sdevice": "SubDevice [5678]"}
        device = self.analyzer._create_pci_device_from_lspci(data)
        self.assertEqual(device.subsystem, "SubVendor SubDevice 5678")

    def test_get_pci_info_lshw_no_devices(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout='{}', stderr="", returncode=0)
        pci_info = self.analyzer.get_pci_info()
        self.assertEqual(pci_info.devices, [])

    def test_create_pci_device_from_lspci_no_sdevice(self):
        data = {"svendor": "SubVendor"}
        device = self.analyzer._create_pci_device_from_lspci(data)
        self.assertEqual(device.subsystem, "SubVendor")

    def test_parse_id_device_only(self):
        vendor_id, device_id = self.analyzer._parse_id("Device [5678]", is_vendor=False)
        self.assertIsNone(vendor_id)
        self.assertEqual(device_id, "5678")

    def test_create_pci_device_from_lspci_no_subsystem_id(self):
        data = {"svendor": "SubVendor", "sdevice": "SubDevice"}
        device = self.analyzer._create_pci_device_from_lspci(data)
        self.assertEqual(device.subsystem, "SubVendor SubDevice")

    def test_get_pci_info_lshw_empty_json(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="{}", stderr="", returncode=0)
        pci_info = self.analyzer.get_pci_info()
        self.assertEqual(pci_info.devices, [])

    def test_create_pci_device_from_lspci_missing_sdevice_key(self):
        data = {"svendor": "SubVendor"}
        device = self.analyzer._create_pci_device_from_lspci(data)
        self.assertEqual(device.subsystem, "SubVendor")

if __name__ == "__main__":
    unittest.main()