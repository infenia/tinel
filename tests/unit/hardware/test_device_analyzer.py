#!/usr/bin/env python3
"""
Unit tests for device analyzer implementation.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from unittest.mock import Mock, patch

from tests.utils import unit_test
from tinel.hardware.device_analyzer import DeviceAnalyzer
from tinel.hardware.models import HardwareInfo
from tinel.interfaces import SystemInterface


class TestDeviceAnalyzer:
    """Test cases for DeviceAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=SystemInterface)

    @unit_test
    @patch("tinel.hardware.device_analyzer.USBAnalyzer")
    @patch("tinel.hardware.device_analyzer.PCIAnalyzer")
    @patch("tinel.hardware.device_analyzer.CPUAnalyzer")
    def test_initialization(
        self, mock_cpu_analyzer_class, mock_pci_analyzer_class, mock_usb_analyzer_class
    ):
        """Test device analyzer initialization."""
        # Setup mock analyzers
        mock_cpu_analyzer = Mock()
        mock_pci_analyzer = Mock()
        mock_usb_analyzer = Mock()
        mock_cpu_analyzer_class.return_value = mock_cpu_analyzer
        mock_pci_analyzer_class.return_value = mock_pci_analyzer
        mock_usb_analyzer_class.return_value = mock_usb_analyzer

        # Test with mock system interface
        analyzer = DeviceAnalyzer(self.mock_system)
        assert analyzer.system == self.mock_system
        assert analyzer.cpu_analyzer == mock_cpu_analyzer
        assert analyzer.pci_analyzer == mock_pci_analyzer
        assert analyzer.usb_analyzer == mock_usb_analyzer

        # Test with default system interface
        analyzer_default = DeviceAnalyzer()
        assert analyzer_default.system is not None
        assert hasattr(analyzer_default.system, "run_command")
        mock_cpu_analyzer_class.assert_called()
        mock_pci_analyzer_class.assert_called()
        mock_usb_analyzer_class.assert_called()

    @unit_test
    @patch("tinel.hardware.device_analyzer.CPUAnalyzer")
    def test_get_cpu_info(self, mock_cpu_analyzer_class):
        """Test getting CPU info delegates to CPUAnalyzer."""
        # Setup
        mock_cpu_analyzer = Mock()
        expected_cpu_info = {"model": "Test CPU", "cores": 4}
        mock_cpu_analyzer.get_cpu_info.return_value = expected_cpu_info
        mock_cpu_analyzer_class.return_value = mock_cpu_analyzer
        analyzer = DeviceAnalyzer(self.mock_system)

        # Execute
        result = analyzer.get_cpu_info()

        # Verify
        assert result == expected_cpu_info
        mock_cpu_analyzer.get_cpu_info.assert_called_once()

    @unit_test
    @patch("tinel.hardware.device_analyzer.CPUAnalyzer")
    @patch("tinel.hardware.device_analyzer.MemoryAnalyzer")
    @patch("tinel.hardware.device_analyzer.NetworkAnalyzer")
    @patch("tinel.hardware.device_analyzer.GraphicsAnalyzer")
    @patch("tinel.hardware.device_analyzer.PCIAnalyzer")
    @patch("tinel.hardware.device_analyzer.USBAnalyzer")
    def test_get_all_hardware_info(self, *mocks):
        """Test the aggregation of all hardware information."""
        # Setup mocks for each analyzer's get_info method
        (
            mock_usb_class,
            mock_pci_class,
            mock_graphics_class,
            mock_network_class,
            mock_memory_class,
            mock_cpu_class,
        ) = mocks

        mock_cpu_class.return_value.get_cpu_info.return_value = {"cpu": "data"}
        mock_memory_class.return_value.get_memory_info.return_value = {"memory": "data"}
        mock_network_class.return_value.get_network_info.return_value = {
            "network": "data"
        }
        mock_graphics_class.return_value.get_graphics_info.return_value = {
            "graphics": "data"
        }
        mock_pci_class.return_value.get_pci_info.return_value = {"pci": "data"}
        mock_usb_class.return_value.get_usb_info.return_value = {"usb": "data"}

        analyzer = DeviceAnalyzer(self.mock_system)

        # Mock the other info methods that are not yet implemented
        with (
            patch.object(analyzer, "get_storage_info", return_value={"disks": "data"}),
            patch.object(
                analyzer, "get_motherboard_info", return_value={"motherboard": "data"}
            ),
        ):
            result = analyzer.get_all_hardware_info()

            assert isinstance(result, HardwareInfo)
            assert result.cpu == {"cpu": "data"}
            assert result.memory == {"memory": "data"}
            assert result.network == {"network": "data"}
            assert result.graphics == {"graphics": "data"}
            assert result.storage == {"disks": "data"}
            assert result.motherboard == {"motherboard": "data"}
            assert result.pci == {"pci": "data"}
            assert result.usb == {"usb": "data"}

            mock_cpu_class.return_value.get_cpu_info.assert_called_once()
            mock_memory_class.return_value.get_memory_info.assert_called_once()
            mock_network_class.return_value.get_network_info.assert_called_once()
            mock_graphics_class.return_value.get_graphics_info.assert_called_once()
            mock_pci_class.return_value.get_pci_info.assert_called_once()
            mock_usb_class.return_value.get_usb_info.assert_called_once()

    @unit_test
    def test_unimplemented_methods_return_placeholders(self):
        """Test that unimplemented methods return the correct placeholder."""
        analyzer = DeviceAnalyzer(system_interface=self.mock_system)
        storage_info = analyzer.get_storage_info()
        motherboard_info = analyzer.get_motherboard_info()

        assert storage_info == {"storage": "Not implemented yet"}
        assert motherboard_info == {"motherboard": "Not implemented yet"}

    @unit_test
    @patch("tinel.hardware.device_analyzer.MemoryAnalyzer")
    def test_get_memory_info(self, mock_memory_analyzer_class):
        """Test getting memory info delegates to MemoryAnalyzer."""
        # Setup
        mock_memory_analyzer = Mock()
        expected_memory_info = {"total": "16GB"}
        mock_memory_analyzer.get_memory_info.return_value = expected_memory_info
        mock_memory_analyzer_class.return_value = mock_memory_analyzer
        analyzer = DeviceAnalyzer(self.mock_system)

        # Execute
        result = analyzer.get_memory_info()

        # Verify
        assert result == expected_memory_info
        mock_memory_analyzer.get_memory_info.assert_called_once()

    @unit_test
    def test_get_storage_info(self):
        """Test getting storage info returns placeholder implementation."""
        analyzer = DeviceAnalyzer(self.mock_system)
        result = analyzer.get_storage_info()
        assert result == {"storage": "Not implemented yet"}

    @unit_test
    @patch("tinel.hardware.device_analyzer.NetworkAnalyzer")
    def test_get_network_info(self, mock_network_analyzer_class):
        """Test getting network info delegates to NetworkAnalyzer."""
        # Setup
        mock_network_analyzer = Mock()
        expected_network_info = {"interfaces": []}
        mock_network_analyzer.get_network_info.return_value = expected_network_info
        mock_network_analyzer_class.return_value = mock_network_analyzer
        analyzer = DeviceAnalyzer(self.mock_system)

        # Execute
        result = analyzer.get_network_info()

        # Verify
        assert result == expected_network_info
        mock_network_analyzer.get_network_info.assert_called_once()

    @unit_test
    @patch("tinel.hardware.device_analyzer.GraphicsAnalyzer")
    def test_get_graphics_info(self, mock_graphics_analyzer_class):
        """Test getting graphics info delegates to GraphicsAnalyzer."""
        # Setup
        mock_graphics_analyzer = Mock()
        expected_graphics_info = {"gpus": []}
        mock_graphics_analyzer.get_graphics_info.return_value = expected_graphics_info
        mock_graphics_analyzer_class.return_value = mock_graphics_analyzer
        analyzer = DeviceAnalyzer(self.mock_system)

        # Execute
        result = analyzer.get_graphics_info()

        # Verify
        assert result == expected_graphics_info
        mock_graphics_analyzer.get_graphics_info.assert_called_once()
