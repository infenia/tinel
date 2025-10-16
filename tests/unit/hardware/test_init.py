#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the hardware __init__ module.

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

import dataclasses
import unittest
from unittest.mock import patch

from tinel.hardware import get_all_hardware_info
from tinel.hardware.models import (
    BIOSInfo,
    BlockDevice,
    CPUInfo,
    GraphicsInfo,
    GPU,
    MemoryInfo,
    MotherboardInfo,
    NetworkInfo,
    NetworkInterface,
    PCIDevice,
    PCIInfo,
    StorageInfo,
    SystemInfo,
    USBDevice,
    USBInfo,
)


class TestGetAllHardwareInfo(unittest.TestCase):
    """Unit tests for the get_all_hardware_info function."""

    @patch("tinel.hardware.MotherboardAnalyzer")
    @patch("tinel.hardware.BIOSAnalyzer")
    @patch("tinel.hardware.SystemAnalyzer")
    @patch("tinel.hardware.USBAnalyzer")
    @patch("tinel.hardware.PCIAnalyzer")
    @patch("tinel.hardware.NetworkAnalyzer")
    @patch("tinel.hardware.GraphicsAnalyzer")
    @patch("tinel.hardware.StorageAnalyzer")
    @patch("tinel.hardware.MemoryAnalyzer")
    @patch("tinel.hardware.CPUAnalyzer")
    def test_get_all_hardware_info_assembles_correctly(self, *mocks):
        """Verify that hardware info is assembled correctly from all analyzers."""
        # Arrange: Setup mock return values for each analyzer
        (
            mock_cpu_analyzer,
            mock_memory_analyzer,
            mock_storage_analyzer,
            mock_graphics_analyzer,
            mock_network_analyzer,
            mock_pci_analyzer,
            mock_usb_analyzer,
            mock_system_analyzer,
            mock_bios_analyzer,
            mock_motherboard_analyzer,
        ) = mocks

        mock_cpu_info = CPUInfo(product="Test CPU")
        mock_memory_info = MemoryInfo(size=16 * 1024**3, units="bytes")
        mock_storage_info = StorageInfo(block_devices=[BlockDevice(name="sda")])
        mock_network_info = NetworkInfo(interfaces=[NetworkInterface(name="eth0")])
        mock_pci_info = PCIInfo(devices=[PCIDevice(slot="00:01.0")])
        mock_usb_info = USBInfo(devices=[USBDevice(bus="usb@1")])
        mock_system_info = SystemInfo(product="Test System")
        mock_bios_info = BIOSInfo(vendor="Test BIOS")
        mock_motherboard_info = MotherboardInfo(product="Test Mobo")
        mock_graphics_info = GraphicsInfo(gpus=[GPU(model="Test GPU")])

        mock_cpu_analyzer.return_value.get_cpu_info.return_value = mock_cpu_info
        mock_memory_analyzer.return_value.get_memory_info.return_value = mock_memory_info
        mock_storage_analyzer.return_value.get_storage_info.return_value = mock_storage_info
        mock_network_analyzer.return_value.get_network_info.return_value = mock_network_info
        mock_pci_analyzer.return_value.get_pci_info.return_value = mock_pci_info
        mock_usb_analyzer.return_value.get_usb_info.return_value = mock_usb_info
        mock_system_analyzer.return_value.get_system_info.return_value = mock_system_info
        mock_bios_analyzer.return_value.get_bios_info.return_value = mock_bios_info
        mock_motherboard_analyzer.return_value.get_motherboard_info.return_value = mock_motherboard_info
        mock_graphics_analyzer.return_value.get_graphics_info.return_value = mock_graphics_info

        # Act: Call the function under test
        hardware_info = get_all_hardware_info()

        # Assert: Verify the hierarchical structure
        self.assertEqual(hardware_info["id"], "Test System")
        core_node = hardware_info["children"][0]
        self.assertEqual(core_node["product"], "Test Mobo")

        # Assert that each major component has its own node with an ID
        self.assertIsNotNone(
            next((c for c in core_node["children"] if c.get("id") == "cpu"), None)
        )
        self.assertIsNotNone(
            next((c for c in core_node["children"] if c.get("id") == "memory"), None)
        )
        self.assertIsNotNone(
            next((c for c in core_node["children"] if c.get("id") == "firmware"), None)
        )
        self.assertIsNotNone(
            next((c for c in core_node["children"] if c.get("id") == "disk:0"), None)
        )
        self.assertIsNotNone(
            next(
                (c for c in core_node["children"] if c.get("id") == "network:0"), None
            )
        )

        # Assert PCI bus and its children
        pci_node = next(
            (c for c in core_node["children"] if c.get("id") == "pci"), None
        )
        self.assertIsNotNone(pci_node)
        self.assertTrue(
            any(d.get("slot") == "00:01.0" for d in pci_node.get("children", []))
        )
        self.assertTrue(
            any(
                "Test GPU" in gpu.get("model", "")
                for d in pci_node.get("children", [])
                if "gpus" in d
                for gpu in d["gpus"]
            )
        )

        # Assert USB bus and its children
        usb_node = next(
            (c for c in core_node["children"] if c.get("id") == "usb"), None
        )
        self.assertIsNotNone(usb_node)
        self.assertTrue(
            any(d.get("bus") == "usb@1" for d in usb_node.get("children", []))
        )

    @patch("tinel.hardware.MotherboardAnalyzer")
    @patch("tinel.hardware.BIOSAnalyzer")
    @patch("tinel.hardware.SystemAnalyzer")
    @patch("tinel.hardware.USBAnalyzer")
    @patch("tinel.hardware.PCIAnalyzer")
    @patch("tinel.hardware.NetworkAnalyzer")
    @patch("tinel.hardware.GraphicsAnalyzer")
    @patch("tinel.hardware.StorageAnalyzer")
    @patch("tinel.hardware.MemoryAnalyzer")
    @patch("tinel.hardware.CPUAnalyzer")
    def test_handles_analyzer_exception_gracefully(self, *mocks):
        """Verify that an exception in one analyzer does not affect others."""
        # Arrange: Setup one analyzer to raise an exception
        (
            mock_cpu_analyzer,
            mock_memory_analyzer,
            mock_storage_analyzer,
            mock_graphics_analyzer,
            mock_network_analyzer,
            mock_pci_analyzer,
            mock_usb_analyzer,
            mock_system_analyzer,
            mock_bios_analyzer,
            mock_motherboard_analyzer,
        ) = mocks

        mock_cpu_analyzer.return_value.get_cpu_info.return_value = CPUInfo(product="Test CPU")
        mock_memory_analyzer.return_value.get_memory_info.side_effect = Exception("Memory Read Error")
        mock_storage_analyzer.return_value.get_storage_info.return_value = StorageInfo(block_devices=[])
        mock_network_analyzer.return_value.get_network_info.return_value = NetworkInfo(interfaces=[])
        mock_pci_analyzer.return_value.get_pci_info.return_value = PCIInfo(devices=[])
        mock_usb_analyzer.return_value.get_usb_info.return_value = USBInfo(devices=[])
        mock_system_analyzer.return_value.get_system_info.return_value = SystemInfo(product="Test System")
        mock_bios_analyzer.return_value.get_bios_info.return_value = BIOSInfo(vendor="Test BIOS")
        mock_motherboard_analyzer.return_value.get_motherboard_info.return_value = MotherboardInfo(product="Test Mobo")
        mock_graphics_analyzer.return_value.get_graphics_info.return_value = GraphicsInfo()

        # Act: Call the function and check the logs
        with self.assertLogs("tinel.hardware", level="ERROR") as cm:
            result = get_all_hardware_info()
            self.assertTrue(any("Failed to get memory info: Memory Read Error" in s for s in cm.output))

        # Assert: Verify that the error is handled gracefully and other data is present
        core_children = result["children"][0]["children"]
        self.assertTrue(any(c.get("product") == "Test CPU" for c in core_children))
        self.assertFalse(any("size" in c and c["size"] == 16 * 1024**3 for c in core_children))


if __name__ == "__main__":
    unittest.main()