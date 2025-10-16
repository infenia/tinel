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
from unittest.mock import patch, MagicMock
from tinel.hardware import get_all_hardware_info
from tinel.hardware.models import (
    CPUInfo, BIOSInfo, MemoryInfo, PCIInfo, GraphicsInfo, StorageInfo,
    NetworkInfo, USBInfo, SystemInfo, MotherboardInfo, BlockDevice,
    NetworkInterface, USBDevice, PCIDevice, GPU
)

class TestGetAllHardwareInfo(unittest.TestCase):

    @patch('tinel.hardware.LinuxSystemInterface')
    @patch('tinel.hardware.CPUAnalyzer')
    @patch('tinel.hardware.BIOSAnalyzer')
    @patch('tinel.hardware.MemoryAnalyzer')
    @patch('tinel.hardware.PCIAnalyzer')
    @patch('tinel.hardware.GraphicsAnalyzer')
    @patch('tinel.hardware.StorageAnalyzer')
    @patch('tinel.hardware.NetworkAnalyzer')
    @patch('tinel.hardware.USBAnalyzer')
    @patch('tinel.hardware.SystemAnalyzer')
    @patch('tinel.hardware.MotherboardAnalyzer')
    def test_get_all_hardware_info_assembles_correctly(
        self, MockMotherboardAnalyzer, MockSystemAnalyzer, MockUSBAnalyzer,
        MockNetworkAnalyzer, MockStorageAnalyzer, MockGraphicsAnalyzer,
        MockPCIAnalyzer, MockMemoryAnalyzer, MockBIOSAnalyzer,
        MockCPUAnalyzer, MockLinuxSystemInterface
    ):
        # Setup mock return values for each analyzer
        MockCPUAnalyzer.return_value.get_cpu_info.return_value = CPUInfo()
        MockBIOSAnalyzer.return_value.get_bios_info.return_value = BIOSInfo()
        MockMemoryAnalyzer.return_value.get_memory_info.return_value = MemoryInfo()
        MockPCIAnalyzer.return_value.get_pci_info.return_value = PCIInfo(devices=[PCIDevice()])
        MockGraphicsAnalyzer.return_value.get_graphics_info.return_value = GraphicsInfo(gpus=[GPU()])
        MockStorageAnalyzer.return_value.get_storage_info.return_value = StorageInfo(block_devices=[BlockDevice(name="sda")])
        MockNetworkAnalyzer.return_value.get_network_info.return_value = NetworkInfo(interfaces=[NetworkInterface(name="eth0")])
        MockUSBAnalyzer.return_value.get_usb_info.return_value = USBInfo(devices=[USBDevice()])
        MockSystemAnalyzer.return_value.get_system_info.return_value = SystemInfo(product="MyPC")
        MockMotherboardAnalyzer.return_value.get_motherboard_info.return_value = MotherboardInfo(product="Z390")

        # Call the function
        hardware_info = get_all_hardware_info()

        # Assertions to ensure the dictionary is built as expected
        self.assertEqual(hardware_info['id'], 'MyPC')
        core = hardware_info['children'][0]['children']

        # Check for presence of each component
        self.assertTrue(any(c.get('id') == 'cpu' for c in core))
        self.assertTrue(any(c.get('id') == 'firmware' for c in core))
        self.assertTrue(any(c.get('id') == 'memory' for c in core))
        self.assertTrue(any(c.get('id') == 'pci' for c in core))
        self.assertTrue(any(c.get('id') == 'usb' for c in core))
        self.assertTrue(any("disk" in c.get('id') for c in core))
        self.assertTrue(any("network" in c.get('id') for c in core))

        # Check that graphics card is under PCI
        pci_bus = next(c for c in core if c.get('id') == 'pci')
        self.assertTrue(any(d.get('gpus') for d in pci_bus['children']))

    @patch('tinel.hardware.LinuxSystemInterface')
    @patch('tinel.hardware.CPUAnalyzer')
    @patch('tinel.hardware.BIOSAnalyzer')
    @patch('tinel.hardware.MemoryAnalyzer')
    @patch('tinel.hardware.PCIAnalyzer')
    @patch('tinel.hardware.GraphicsAnalyzer')
    @patch('tinel.hardware.StorageAnalyzer')
    @patch('tinel.hardware.NetworkAnalyzer')
    @patch('tinel.hardware.USBAnalyzer')
    @patch('tinel.hardware.SystemAnalyzer')
    @patch('tinel.hardware.MotherboardAnalyzer')
    def test_handles_analyzer_exception_gracefully(
        self, MockMotherboardAnalyzer, MockSystemAnalyzer, MockUSBAnalyzer,
        MockNetworkAnalyzer, MockStorageAnalyzer, MockGraphicsAnalyzer,
        MockPCIAnalyzer, MockMemoryAnalyzer, MockBIOSAnalyzer,
        MockCPUAnalyzer, MockLinuxSystemInterface
    ):
        # Setup one analyzer to fail
        MockCPUAnalyzer.return_value.get_cpu_info.side_effect = Exception("CPU Failure")
        MockBIOSAnalyzer.return_value.get_bios_info.side_effect = Exception("BIOS Failure")
        MockMemoryAnalyzer.return_value.get_memory_info.side_effect = Exception("Memory Failure")
        MockPCIAnalyzer.return_value.get_pci_info.side_effect = Exception("PCI Failure")
        MockGraphicsAnalyzer.return_value.get_graphics_info.side_effect = Exception("Graphics Failure")
        MockStorageAnalyzer.return_value.get_storage_info.side_effect = Exception("Storage Failure")
        MockNetworkAnalyzer.return_value.get_network_info.side_effect = Exception("Network Failure")
        MockUSBAnalyzer.return_value.get_usb_info.side_effect = Exception("USB Failure")

        # Mock the rest to succeed
        MockSystemAnalyzer.return_value.get_system_info.return_value = SystemInfo(product="MyPC")
        MockMotherboardAnalyzer.return_value.get_motherboard_info.return_value = MotherboardInfo(product="Z390")

        # Call the function
        hardware_info = get_all_hardware_info()

        # Assert that the main structure is still present
        self.assertEqual(hardware_info['id'], 'MyPC')
        core = hardware_info['children'][0]['children']

        # Assert that the failed components are not present
        self.assertFalse(any(c.get('id') == 'cpu' for c in core))
        self.assertFalse(any(c.get('id') == 'firmware' for c in core))
        self.assertFalse(any(c.get('id') == 'memory' for c in core))
        self.assertFalse(any(c.get('id') == 'pci' for c in core))
        self.assertFalse(any(c.get('id') == 'usb' for c in core))
        self.assertFalse(any("disk" in c.get('id') for c in core))
        self.assertFalse(any("network" in c.get('id') for c in core))

    @patch('tinel.hardware.LinuxSystemInterface')
    @patch('tinel.hardware.CPUAnalyzer')
    @patch('tinel.hardware.BIOSAnalyzer')
    @patch('tinel.hardware.MemoryAnalyzer')
    @patch('tinel.hardware.PCIAnalyzer')
    @patch('tinel.hardware.GraphicsAnalyzer')
    @patch('tinel.hardware.StorageAnalyzer')
    @patch('tinel.hardware.NetworkAnalyzer')
    @patch('tinel.hardware.USBAnalyzer')
    @patch('tinel.hardware.SystemAnalyzer')
    @patch('tinel.hardware.MotherboardAnalyzer')
    def test_get_all_hardware_info_with_empty_lists(
        self, MockMotherboardAnalyzer, MockSystemAnalyzer, MockUSBAnalyzer,
        MockNetworkAnalyzer, MockStorageAnalyzer, MockGraphicsAnalyzer,
        MockPCIAnalyzer, MockMemoryAnalyzer, MockBIOSAnalyzer,
        MockCPUAnalyzer, MockLinuxSystemInterface
    ):
        # Setup mock return values for each analyzer to return empty lists
        MockCPUAnalyzer.return_value.get_cpu_info.return_value = CPUInfo()
        MockBIOSAnalyzer.return_value.get_bios_info.return_value = BIOSInfo()
        MockMemoryAnalyzer.return_value.get_memory_info.return_value = MemoryInfo()
        MockPCIAnalyzer.return_value.get_pci_info.return_value = PCIInfo(devices=[])
        MockGraphicsAnalyzer.return_value.get_graphics_info.return_value = GraphicsInfo(gpus=[])
        MockStorageAnalyzer.return_value.get_storage_info.return_value = StorageInfo(block_devices=[])
        MockNetworkAnalyzer.return_value.get_network_info.return_value = NetworkInfo(interfaces=[])
        MockUSBAnalyzer.return_value.get_usb_info.return_value = USBInfo(devices=[])
        MockSystemAnalyzer.return_value.get_system_info.return_value = SystemInfo(product="MyPC")
        MockMotherboardAnalyzer.return_value.get_motherboard_info.return_value = MotherboardInfo(product="Z390")

        hardware_info = get_all_hardware_info()
        core = hardware_info['children'][0]['children']

        # Assert that components that can be empty are not present
        self.assertFalse(any(c.get('id') == 'pci' for c in core))
        self.assertFalse(any(c.get('id') == 'usb' for c in core))
        self.assertFalse(any("disk" in c.get('id') for c in core))
        self.assertFalse(any("network" in c.get('id') for c in core))

if __name__ == '__main__':
    unittest.main()