import json
import unittest
from unittest.mock import MagicMock, patch

from tinel.hardware.pci_analyzer import PCIAnalyzer
from tinel.interfaces import CommandResult


class TestPCIAnalyzerCoverage(unittest.TestCase):
    def test_get_pci_info_lshw_fails_and_lspci_fails(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="lshw not found", returncode=1),
            CommandResult(success=False, stdout="", stderr="lspci not found", returncode=1)
        ]
        analyzer = PCIAnalyzer(mock_system_interface)
        with self.assertLogs('tinel.hardware.pci_analyzer', level='WARNING') as cm:
            pci_info = analyzer.get_pci_info()
            self.assertTrue(any("lshw failed, falling back to lspci" in s for s in cm.output))
            self.assertTrue(any("Failed to run lspci" in s for s in cm.output))
            self.assertEqual(len(pci_info.devices), 0)

    def test_parse_lspci_vmmk_output_malformed_line(self):
        analyzer = PCIAnalyzer(MagicMock())
        output = "Slot:\t00:01.0\nVendor\nDevice:\tDevice [5678]"
        with self.assertLogs('tinel.hardware.pci_analyzer', level='DEBUG') as cm:
            devices = analyzer._parse_lspci_vmmk_output(output)
            self.assertTrue(any("Skipping malformed line" in s for s in cm.output))
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].slot, "00:01.0")

    def test_parse_id_no_match(self):
        analyzer = PCIAnalyzer(MagicMock())
        vendor_id, device_id = analyzer._parse_id("No IDs here", is_vendor=True)
        self.assertIsNone(vendor_id)
        self.assertIsNone(device_id)

    def test_parse_lshw_json_output_list_of_nodes(self):
        analyzer = PCIAnalyzer(MagicMock())
        hardware_data = [
            {
                "businfo": "pci@0000:00:01.0",
                "slot": "00:01.0",
                "vendor": "Vendor [1234]",
                "product": "Product [5678]",
            }
        ]
        devices = analyzer._parse_lshw_json_output(hardware_data)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].vendor_id, "1234")
        self.assertEqual(devices[0].device_id, "5678")

    def test_parse_lshw_json_output_no_slot(self):
        analyzer = PCIAnalyzer(MagicMock())
        hardware_data = {
            "businfo": "pci@0000:00:01.0",
            "vendor": "Vendor [1234]",
            "product": "Product [5678]",
        }
        devices = analyzer._parse_lshw_json_output(hardware_data)
        self.assertEqual(len(devices), 0)

    def test_parse_lshw_vendor_id_in_product(self):
        analyzer = PCIAnalyzer(MagicMock())
        hardware_data = {
            "businfo": "pci@0000:00:01.0",
            "slot": "00:01.0",
            "vendor": "Vendor",
            "product": "Product [1234:5678]",
        }
        devices = analyzer._parse_lshw_json_output(hardware_data)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].vendor_id, "1234")
        self.assertEqual(devices[0].device_id, "5678")

    def test_create_pci_device_from_lspci_no_vendor(self):
        analyzer = PCIAnalyzer(MagicMock())
        data = {
            "slot": "00:01.0",
            "device": "Device [5678]",
        }
        device = analyzer._create_pci_device_from_lspci(data)
        self.assertIsNone(device.vendor_id)
        self.assertEqual(device.device_id, "5678")

    def test_create_pci_device_from_lspci_no_device(self):
        analyzer = PCIAnalyzer(MagicMock())
        data = {
            "slot": "00:01.0",
            "vendor": "Vendor [1234]",
        }
        device = analyzer._create_pci_device_from_lspci(data)
        self.assertEqual(device.vendor_id, "1234")
        self.assertIsNone(device.device_id)

    def test_get_pci_info_from_lspci_empty_output(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="", stderr="", returncode=0
        )
        analyzer = PCIAnalyzer(mock_system_interface)
        pci_info = analyzer._get_pci_info_from_lspci()
        self.assertEqual(len(pci_info.devices), 0)