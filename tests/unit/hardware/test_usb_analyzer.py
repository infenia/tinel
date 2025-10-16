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
from tinel.hardware.usb_analyzer import USBAnalyzer
from tinel.hardware.models import USBInfo, USBDevice
from tinel.interfaces import CommandResult

class TestUSBAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = USBAnalyzer(self.mock_system_interface)

    def test_get_usb_info_with_lshw_success(self):
        lshw_output = json.dumps(
            {"id": "core", "class": "bus", "children": [
                {"id": "usb", "class": "bus", "children": [
                    {"id": "usb:0", "class": "generic", "vendor": "Vendor [1234]", "product": "Product [5678]"}
                ]}
            ]}
        )
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout=lshw_output, stderr="", returncode=0)

        usb_info = self.analyzer.get_usb_info()

        self.assertEqual(len(usb_info.devices), 1)
        self.assertEqual(usb_info.devices[0].vendor_id, "1234")
        self.assertEqual(usb_info.devices[0].product_id, "5678")

    def test_get_usb_info_fallback_to_lsusb(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="lshw failed", returncode=1),
            CommandResult(success=True, stdout="/: Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 480M", stderr="", returncode=0)
        ]

        # Mock sysfs to fail
        self.mock_system_interface.list_dir.side_effect = OSError("sysfs error")

        usb_info = self.analyzer.get_usb_info()

        self.assertEqual(len(usb_info.devices), 1)
        self.assertEqual(usb_info.devices[0].bus, "01")
        self.assertEqual(usb_info.devices[0].device_class, "root_hub")

    def test_get_usb_info_handles_all_failures(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="lshw failed", returncode=1),
            CommandResult(success=False, stdout="", stderr="lsusb failed", returncode=1)
        ]
        # Mock sysfs to fail
        self.mock_system_interface.list_dir.side_effect = OSError("sysfs error")

        usb_info = self.analyzer.get_usb_info()
        self.assertEqual(usb_info.devices, [])

    def test_get_usb_info_with_sysfs_details(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        self.mock_system_interface.list_dir.return_value = ["1-1", "2-2:1.0"] # one valid, one invalid
        self.mock_system_interface.file_exists.return_value = True

        def read_file_mock(path):
            if "busnum" in path: return "1"
            if "devnum" in path: return "2"
            if "idVendor" in path: return "abcd"
            if "idProduct" in path: return "1234"
            return ""
        self.mock_system_interface.read_file.side_effect = read_file_mock

        usb_info = self.analyzer.get_usb_info()
        self.assertEqual(len(usb_info.devices), 1)
        self.assertEqual(usb_info.devices[0].bus, "1")
        self.assertEqual(usb_info.devices[0].vendor_id, "abcd")

    def test_parse_lsusb_t_with_complex_tree(self):
        lsusb_output = """
/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/12p, 5000M
    |__ Port 1: Dev 2, If 0, Class=Hub, Driver=hub/4p, 5000M
        |__ Port 1: Dev 3, If 0, Class=Vendor Specific Class, Driver=, 12M
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 480M
"""
        devices = self.analyzer._parse_lsusb_t_output(lsusb_output)
        self.assertEqual(len(devices), 2)
        self.assertEqual(len(devices[0].children), 1)
        self.assertEqual(len(devices[0].children[0].children), 1)
        self.assertEqual(devices[0].children[0].children[0].device_class, "Vendor Specific Class")

    def test_parse_id_helper(self):
        vid, vname = self.analyzer._parse_id("Vendor [1a2b]")
        self.assertEqual(vid, "1a2b")
        self.assertEqual(vname, "Vendor")

        pid, pname = self.analyzer._parse_id("Product")
        self.assertIsNone(pid)
        self.assertEqual(pname, "Product")

    def test_lshw_json_decode_error(self):
        self.mock_system_interface.list_dir.side_effect = OSError("sysfs error")
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="{not json}", stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="lsusb failed", returncode=1)
        ]
        usb_info = self.analyzer.get_usb_info()
        self.assertEqual(usb_info.devices, [])

    def test_sysfs_read_file_error(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        self.mock_system_interface.list_dir.return_value = ["1-1"]
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = IOError("cannot read")

        usb_info = self.analyzer.get_usb_info()
        self.assertIsNone(usb_info.devices[0].bus)

    def test_parse_lshw_no_children(self):
        node = {"id": "usb:1", "vendor": "V [1111]", "children": []}
        device = self.analyzer._parse_lshw_node(node)
        self.assertEqual(len(device.children), 0)

    def test_parse_lshw_child_is_none(self):
        node = {"id": "usb:1", "vendor": "V [1111]", "children": [{"id": "not-usb"}]}
        device = self.analyzer._parse_lshw_node(node)
        self.assertEqual(len(device.children), 0)

    def test_parse_lsusb_t_empty_and_no_file(self):
        self.assertEqual(self.analyzer._parse_lsusb_t_output(""), [])
        self.assertEqual(self.analyzer._parse_lsusb_t_output("no such file"), [])

    def test_parse_lsusb_line_no_matches(self):
        device = self.analyzer._parse_lsusb_line("some random line")
        self.assertIsNone(device.port)
        self.assertIsNone(device.device_class)
        self.assertIsNone(device.driver)
        self.assertIsNone(device.speed)

    def test_parse_lshw_json_output_with_list(self):
        devices = self.analyzer._parse_lshw_json_output([{"id": "not a dict"}])
        self.assertEqual(devices, [])

    def test_parse_lsusb_t_output_with_empty_line(self):
        lsusb_output = """
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 480M

    |__ Port 1: Dev 2, If 0, Class=Hub, Driver=hub/4p, 480M
"""
        devices = self.analyzer._parse_lsusb_t_output(lsusb_output)
        self.assertEqual(len(devices), 1)
        self.assertEqual(len(devices[0].children), 1)

    def test_parse_lshw_node_not_dict(self):
        device = self.analyzer._parse_lshw_node([])
        self.assertIsNone(device)

    def test_lshw_no_usb_devices(self):
        lshw_output = json.dumps({"id": "core", "class": "bus", "children": []})
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout=lshw_output, stderr="", returncode=0)
        self.mock_system_interface.list_dir.side_effect = OSError("sysfs error")
        self.mock_system_interface.run_command.side_effect = [
             CommandResult(success=True, stdout=lshw_output, stderr="", returncode=0),
             CommandResult(success=False, stdout="", stderr="lsusb failed", returncode=1)
        ]
        usb_info = self.analyzer.get_usb_info()
        self.assertEqual(usb_info.devices, [])

    def test_get_usb_info_from_fallback_with_colon_dir(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        self.mock_system_interface.list_dir.return_value = ["1-1:1.0", "1-2"]
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.return_value = "test"
        usb_info = self.analyzer.get_usb_info()
        self.assertEqual(len(usb_info.devices), 1)

    def test_parse_lsusb_t_output_complex_indentation(self):
        output = """
/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 480M
    |__ Port 1: Dev 2, If 0, Class=Hub, Driver=hub/4p, 480M
        |__ Port 2: Dev 3, If 0, Class=Vendor Specific Class, Driver=, 12M
    |__ Port 3: Dev 4, If 0, Class=Hub, Driver=hub/4p, 480M
"""
        devices = self.analyzer._parse_lsusb_t_output(output)
        self.assertEqual(len(devices), 1)
        self.assertEqual(len(devices[0].children), 2)
        self.assertEqual(len(devices[0].children[0].children), 1)

if __name__ == "__main__":
    unittest.main()