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
from unittest.mock import MagicMock, patch

from tinel.tools.hardware_tools import (
    AllHardwareToolProvider,
    CPUInfoToolProvider,
    GraphicsInfoToolProvider,
    MemoryInfoToolProvider,
    NetworkInfoToolProvider,
    PCIDevicesToolProvider,
    StorageInfoToolProvider,
    USBDevicesToolProvider,
)


class TestHardwareToolProviders(unittest.TestCase):
    """Test cases for hardware tool providers."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_system_interface = MagicMock()

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_all_hardware_tool_provider(self, mock_device_analyzer_class):
        """Test AllHardwareToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_all_hardware_info.return_value = MagicMock(cpu="Test CPU")

        provider = AllHardwareToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_all_hardware_info.assert_called_once()
        self.assertEqual(result, {"cpu": "Test CPU"})
        self.assertEqual(provider._name, "get_all_hardware")

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_cpu_info_tool_provider(self, mock_device_analyzer_class):
        """Test CPUInfoToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_cpu_info.return_value = {"cpu": "info"}

        provider = CPUInfoToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_cpu_info.assert_called_once()
        self.assertEqual(result, {"cpu": "info"})
        self.assertEqual(provider._name, "get_cpu_info")

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_memory_info_tool_provider(self, mock_device_analyzer_class):
        """Test MemoryInfoToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_memory_info.return_value = {"memory": "info"}

        provider = MemoryInfoToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_memory_info.assert_called_once()
        self.assertEqual(result, {"memory": "info"})
        self.assertEqual(provider._name, "get_memory_info")

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_storage_info_tool_provider(self, mock_device_analyzer_class):
        """Test StorageInfoToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_storage_info.return_value = {"storage": "info"}

        provider = StorageInfoToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_storage_info.assert_called_once()
        self.assertEqual(result, {"storage": "info"})
        self.assertEqual(provider._name, "get_storage_info")

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_pci_devices_tool_provider(self, mock_device_analyzer_class):
        """Test PCIDevicesToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_pci_devices.return_value = {"pci": "devices"}

        provider = PCIDevicesToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_pci_devices.assert_called_once()
        self.assertEqual(result, {"pci": "devices"})
        self.assertEqual(provider._name, "get_pci_devices")

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_usb_devices_tool_provider(self, mock_device_analyzer_class):
        """Test USBDevicesToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_usb_devices.return_value = {"usb": "devices"}

        provider = USBDevicesToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_usb_devices.assert_called_once()
        self.assertEqual(result, {"usb": "devices"})
        self.assertEqual(provider._name, "get_usb_devices")

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_network_info_tool_provider(self, mock_device_analyzer_class):
        """Test NetworkInfoToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_network_info.return_value = {"network": "info"}

        provider = NetworkInfoToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_network_info.assert_called_once()
        self.assertEqual(result, {"network": "info"})
        self.assertEqual(provider._name, "get_network_info")

    @patch("tinel.tools.hardware_tools.DeviceAnalyzer")
    def test_graphics_info_tool_provider(self, mock_device_analyzer_class):
        """Test GraphicsInfoToolProvider."""
        mock_analyzer = mock_device_analyzer_class.return_value
        mock_analyzer.get_graphics_info.return_value = {"graphics": "info"}

        provider = GraphicsInfoToolProvider(self.mock_system_interface)
        result = provider.execute({})

        mock_analyzer.get_graphics_info.assert_called_once()
        self.assertEqual(result, {"graphics": "info"})
        self.assertEqual(provider._name, "get_graphics_info")


if __name__ == "__main__":
    unittest.main()
