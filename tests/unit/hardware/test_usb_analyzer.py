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
from tinel.interfaces import CommandResult


class TestUSBAnalyzer(unittest.TestCase):
    def test_get_usb_info_with_lshw_success(self):
        mock_system_interface = MagicMock()
        mock_lshw_output = {
            "id": "computer",
            "children": [
                {
                    "id": "core",
                    "children": [
                        {
                            "id": "usbhost",
                            "class": "bus",
                            "children": [
                                {
                                    "id": "usb:0",
                                    "businfo": "usb@2",
                                    "vendor": "Linux Foundation [1d6b]",
                                    "product": "2.0 root hub [0002]",
                                    "children": [
                                        {
                                            "id": "usb:0:1",
                                            "businfo": "usb@2:1.4",
                                            "vendor": "Dell [413c]",
                                            "product": "KB216 Wired Keyboard [2113]",
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout=json.dumps(mock_lshw_output),
            stderr="",
            returncode=0,
        )
        analyzer = USBAnalyzer(system_interface=mock_system_interface)
        usb_info = analyzer.get_usb_info()

        self.assertEqual(len(usb_info.devices), 1)
        root_hub = usb_info.devices[0]
        self.assertEqual(root_hub.vendor_id, "1d6b")
        self.assertEqual(root_hub.product_id, "0002")
        self.assertEqual(root_hub.manufacturer, "Linux Foundation")
        self.assertEqual(root_hub.product, "2.0 root hub")
        self.assertEqual(len(root_hub.children), 1)

        keyboard = root_hub.children[0]
        self.assertEqual(keyboard.vendor_id, "413c")
        self.assertEqual(keyboard.product_id, "2113")
        self.assertEqual(keyboard.manufacturer, "Dell")
        self.assertEqual(keyboard.product, "KB216 Wired Keyboard")

    def test_parse_id_helper(self):
        analyzer = USBAnalyzer(MagicMock())
        vid, vname = analyzer._parse_id("Vendor Name [1234]")
        self.assertEqual(vid, "1234")
        self.assertEqual(vname, "Vendor Name")
        vid, vname = analyzer._parse_id("Product Name")
        self.assertIsNone(vid)
        self.assertEqual(vname, "Product Name")
        vid, vname = analyzer._parse_id("")
        self.assertIsNone(vid)
        self.assertEqual(vname, "")

    @patch('tinel.hardware.usb_analyzer.log')
    def test_get_usb_info_fallback_to_lsusb(self, mock_log):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="lshw failed", returncode=1),
            CommandResult(success=True, stdout="/:  Bus 02.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/12p, 480M\n    |__ Port 4: Dev 2, If 0, Class=Human Interface Device, Driver=usbhid, 1.5M", stderr="", returncode=0),
        ]
        mock_system_interface.list_dir.side_effect = OSError("sysfs not available")

        analyzer = USBAnalyzer(system_interface=mock_system_interface)
        usb_info = analyzer.get_usb_info()

        mock_log.warning.assert_any_call("lshw failed or found no USB devices, falling back to lsusb and sysfs.")
        mock_log.warning.assert_any_call("Error accessing sysfs for USB devices: sysfs not available, falling back to lsusb.")

        self.assertEqual(len(usb_info.devices), 1)
        self.assertEqual(usb_info.devices[0].bus, "02")
        self.assertEqual(len(usb_info.devices[0].children), 1)
        self.assertEqual(usb_info.devices[0].children[0].driver, "usbhid")

    @patch('tinel.hardware.usb_analyzer.log')
    def test_get_usb_info_handles_all_failures(self, mock_log):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="command not found", returncode=127)
        mock_system_interface.list_dir.side_effect = OSError("Cannot access")

        analyzer = USBAnalyzer(system_interface=mock_system_interface)
        usb_info = analyzer.get_usb_info()

        self.assertEqual(len(usb_info.devices), 0)
        mock_log.error.assert_called_once_with("Failed to run lsusb.")

    def test_get_usb_info_with_sysfs_details(self):
        mock_system_interface = MagicMock()
        mock_system_interface.list_dir.return_value = ['2-1']
        mock_system_interface.file_exists.return_value = True

        def mock_read_file(path):
            if "busnum" in path: return "2"
            if "devnum" in path: return "1"
            if "idVendor" in path: return "8087"
            if "idProduct" in path: return "8001"
            if "manufacturer" in path: return "Linux Foundation"
            if "product" in path: return "2.0 root hub"
            if "speed" in path: return "480"
            return ""

        mock_system_interface.read_file.side_effect = mock_read_file
        mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)

        analyzer = USBAnalyzer(system_interface=mock_system_interface)
        usb_info = analyzer.get_usb_info()

        self.assertEqual(len(usb_info.devices), 1)
        device = usb_info.devices[0]
        self.assertEqual(device.bus, "2")
        self.assertEqual(device.port, "1")
        self.assertEqual(device.vendor_id, "8087")

    def test_parse_lsusb_t_with_complex_tree(self):
        analyzer = USBAnalyzer(MagicMock())
        output = """
        /:  Bus 04.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 10000M
        /:  Bus 03.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd/4p, 480M
            |__ Port 3: Dev 2, If 0, Class=Video, Driver=uvcvideo, 480M
            |__ Port 4: Dev 3, If 0, Class=Human Interface Device, Driver=usbhid, 12M
        """
        devices = analyzer._parse_lsusb_t_output(output)
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].bus, "04")
        self.assertEqual(len(devices[0].children), 0)
        self.assertEqual(devices[1].bus, "03")
        self.assertEqual(len(devices[1].children), 2)
        self.assertEqual(devices[1].children[0].driver, "uvcvideo")
        self.assertEqual(devices[1].children[1].driver, "usbhid")


if __name__ == "__main__":
    unittest.main()