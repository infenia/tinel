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
import unittest
from unittest.mock import patch, MagicMock

from tinel.hardware import get_all_hardware_info, HardwareInfo, PCIInfo, USBInfo


class TestGetAllHardwareInfo(unittest.TestCase):
    @patch('tinel.hardware.CPUAnalyzer')
    @patch('tinel.hardware.MemoryAnalyzer')
    @patch('tinel.hardware.StorageAnalyzer')
    @patch('tinel.hardware.GraphicsAnalyzer')
    @patch('tinel.hardware.NetworkAnalyzer')
    @patch('tinel.hardware.PCIAnalyzer')
    @patch('tinel.hardware.USBAnalyzer')
    def test_get_all_hardware_info_assembles_correctly(
        self,
        MockUSBAnalyzer,
        MockPCIAnalyzer,
        MockNetworkAnalyzer,
        MockGraphicsAnalyzer,
        MockStorageAnalyzer,
        MockMemoryAnalyzer,
        MockCPUAnalyzer,
    ):
        # Arrange: Setup mock return values for each analyzer's get_*_info method
        mock_cpu_info = {"cores": 8}
        mock_mem_info = {"total": "16GB"}
        mock_storage_info = {"disks": ["sda"]}
        mock_graphics_info = {"gpu": "NVIDIA"}
        mock_network_info = {"interfaces": ["eth0"]}
        mock_pci_info = PCIInfo(devices=[{"slot": "00:01.0"}])
        mock_usb_info = USBInfo(tree={"root_hubs": []})

        MockCPUAnalyzer.return_value.get_cpu_info.return_value = mock_cpu_info
        MockMemoryAnalyzer.return_value.get_memory_info.return_value = mock_mem_info
        MockStorageAnalyzer.return_value.get_storage_info.return_value = mock_storage_info
        MockGraphicsAnalyzer.return_value.get_graphics_info.return_value = mock_graphics_info
        MockNetworkAnalyzer.return_value.get_network_info.return_value = mock_network_info
        MockPCIAnalyzer.return_value.get_pci_info.return_value = mock_pci_info
        MockUSBAnalyzer.return_value.get_usb_info.return_value = mock_usb_info

        # Act: Call the function under test
        hardware_info = get_all_hardware_info()

        # Assert: Verify that the HardwareInfo object is created with the mock data
        self.assertIsInstance(hardware_info, HardwareInfo)
        self.assertEqual(hardware_info.cpu, mock_cpu_info)
        self.assertEqual(hardware_info.memory, mock_mem_info)
        self.assertEqual(hardware_info.storage, mock_storage_info)
        self.assertEqual(hardware_info.graphics, mock_graphics_info)
        self.assertEqual(hardware_info.network, mock_network_info)
        self.assertEqual(hardware_info.pci, mock_pci_info)
        self.assertEqual(hardware_info.usb, mock_usb_info)

        # Assert: Verify that each analyzer's get_*_info method was called once
        MockCPUAnalyzer.return_value.get_cpu_info.assert_called_once()
        MockMemoryAnalyzer.return_value.get_memory_info.assert_called_once()
        MockStorageAnalyzer.return_value.get_storage_info.assert_called_once()
        MockGraphicsAnalyzer.return_value.get_graphics_info.assert_called_once()
        MockNetworkAnalyzer.return_value.get_network_info.assert_called_once()
        MockPCIAnalyzer.return_value.get_pci_info.assert_called_once()
        MockUSBAnalyzer.return_value.get_usb_info.assert_called_once()

if __name__ == '__main__':
    unittest.main()