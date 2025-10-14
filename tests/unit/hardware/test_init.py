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
from unittest.mock import patch

import dataclasses
from tinel.hardware import HardwareInfo, PCIInfo, USBInfo, get_all_hardware_info


class TestGetAllHardwareInfo(unittest.TestCase):
    @patch("tinel.hardware.USBAnalyzer")
    @patch("tinel.hardware.PCIAnalyzer")
    @patch("tinel.hardware.NetworkAnalyzer")
    @patch("tinel.hardware.GraphicsAnalyzer")
    @patch("tinel.hardware.StorageAnalyzer")
    @patch("tinel.hardware.MemoryAnalyzer")
    @patch("tinel.hardware.CPUAnalyzer")
    def test_get_all_hardware_info_assembles_correctly(self, *mocks):
        # Arrange: Setup mock return values for each analyzer's get_*_info method
        (
            mock_cpu_analyzer,
            mock_memory_analyzer,
            mock_storage_analyzer,
            mock_graphics_analyzer,
            mock_network_analyzer,
            mock_pci_analyzer,
            mock_usb_analyzer,
        ) = mocks

        mock_cpu_info = {"cores": 8}
        mock_mem_info = {"total": "16GB"}
        mock_storage_info = {"disks": ["sda"]}
        mock_graphics_info = {"gpu": "NVIDIA"}
        mock_network_info = {"interfaces": ["eth0"]}
        mock_pci_info = PCIInfo(devices=[{"slot": "00:01.0"}])
        mock_usb_info = USBInfo(tree={"root_hubs": []})

        mock_cpu_analyzer.return_value.get_cpu_info.return_value = mock_cpu_info
        mock_memory_analyzer.return_value.get_memory_info.return_value = mock_mem_info
        mock_storage_analyzer.return_value.get_storage_info.return_value = (
            mock_storage_info
        )
        mock_graphics_analyzer.return_value.get_graphics_info.return_value = (
            mock_graphics_info
        )
        mock_network_analyzer.return_value.get_network_info.return_value = (
            mock_network_info
        )
        mock_pci_analyzer.return_value.get_pci_info.return_value = mock_pci_info
        mock_usb_analyzer.return_value.get_usb_info.return_value = mock_usb_info

        # Act: Call the function under test
        hardware_info = get_all_hardware_info()

        # Assert: Verify that the result is a dictionary with the correct data
        self.assertIsInstance(hardware_info, dict)
        self.assertEqual(hardware_info["cpu"], mock_cpu_info)
        self.assertEqual(hardware_info["memory"], mock_mem_info)
        self.assertEqual(hardware_info["storage"], mock_storage_info)
        self.assertEqual(hardware_info["graphics"], mock_graphics_info)
        self.assertEqual(hardware_info["network"], mock_network_info)
        self.assertEqual(hardware_info["pci"], dataclasses.asdict(mock_pci_info))
        self.assertEqual(hardware_info["usb"], dataclasses.asdict(mock_usb_info))

        # Assert: Verify that each analyzer's get_*_info method was called once
        mock_cpu_analyzer.return_value.get_cpu_info.assert_called_once()
        mock_memory_analyzer.return_value.get_memory_info.assert_called_once()
        mock_storage_analyzer.return_value.get_storage_info.assert_called_once()
        mock_graphics_analyzer.return_value.get_graphics_info.assert_called_once()
        mock_network_analyzer.return_value.get_network_info.assert_called_once()
        mock_pci_analyzer.return_value.get_pci_info.assert_called_once()
        mock_usb_analyzer.return_value.get_usb_info.assert_called_once()

    @patch("tinel.hardware.CPUAnalyzer")
    def test_get_all_hardware_info_handles_exception(self, mock_cpu_analyzer):
        # Arrange: Setup one of the analyzers to raise an exception
        mock_cpu_analyzer.return_value.get_cpu_info.side_effect = Exception(
            "Test Exception"
        )

        # Act: Call the function
        hardware_info = get_all_hardware_info()

        # Assert: Verify that the 'cpu' key contains an error message
        self.assertIn("error", hardware_info["cpu"])
        self.assertIn("Test Exception", hardware_info["cpu"]["error"])


if __name__ == "__main__":
    unittest.main()
