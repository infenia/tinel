#!/usr/bin/env python3
"""
Unit tests for device analyzer implementation.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from unittest.mock import Mock, patch

from tests.utils import unit_test
from tinel.hardware.device_analyzer import DeviceAnalyzer
from tinel.hardware.models import HardwareInfo, PCIInfo, USBInfo
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
    @patch("tinel.hardware.device_analyzer.USBAnalyzer")
    @patch("tinel.hardware.device_analyzer.PCIAnalyzer")
    @patch("tinel.hardware.device_analyzer.CPUAnalyzer")
    @patch("tinel.hardware.device_analyzer.DeviceAnalyzer.get_memory_info")
    @patch("tinel.hardware.device_analyzer.DeviceAnalyzer.get_storage_info")
    def test_get_all_hardware_info(
        self,
        mock_get_storage,
        mock_get_memory,
        mock_cpu_analyzer_class,
        mock_pci_analyzer_class,
        mock_usb_analyzer_class,
    ):
        """Test getting all hardware info returns a complete HardwareInfo object."""
        # Setup mocks for all analyzers
        mock_cpu_analyzer = Mock()
        mock_pci_analyzer = Mock()
        mock_usb_analyzer = Mock()

        expected_cpu_info = {"model": "Test CPU"}
        expected_pci_info = PCIInfo(devices=[{"slot": "00:00.0"}])
        expected_usb_info = USBInfo(tree={"bus": "01"})
        expected_mem_info = {"memory": "4GB"}
        expected_storage_info = {"storage": "1TB SSD"}

        mock_cpu_analyzer.get_cpu_info.return_value = expected_cpu_info
        mock_pci_analyzer.get_pci_info.return_value = expected_pci_info
        mock_usb_analyzer.get_usb_info.return_value = expected_usb_info
        mock_get_memory.return_value = expected_mem_info
        mock_get_storage.return_value = expected_storage_info

        mock_cpu_analyzer_class.return_value = mock_cpu_analyzer
        mock_pci_analyzer_class.return_value = mock_pci_analyzer
        mock_usb_analyzer_class.return_value = mock_usb_analyzer

        analyzer = DeviceAnalyzer(self.mock_system)

        # Execute
        result = analyzer.get_all_hardware_info()

        # Verify
        assert isinstance(result, HardwareInfo)
        assert result.cpu == expected_cpu_info
        assert result.pci == expected_pci_info
        assert result.usb == expected_usb_info
        assert result.memory == expected_mem_info
        assert result.storage == expected_storage_info

        mock_cpu_analyzer.get_cpu_info.assert_called_once()
        mock_pci_analyzer.get_pci_info.assert_called_once()
        mock_usb_analyzer.get_usb_info.assert_called_once()
        mock_get_memory.assert_called_once()
        mock_get_storage.assert_called_once()

    @unit_test
    def test_get_memory_info(self):
        """Test getting memory info returns placeholder implementation."""
        analyzer = DeviceAnalyzer(self.mock_system)
        result = analyzer.get_memory_info()
        assert result == {"memory": "Not implemented yet"}

    @unit_test
    def test_get_storage_info(self):
        """Test getting storage info returns placeholder implementation."""
        analyzer = DeviceAnalyzer(self.mock_system)
        result = analyzer.get_storage_info()
        assert result == {"storage": "Not implemented yet"}

    @unit_test
    def test_get_network_info(self):
        """Test getting network info returns placeholder implementation."""
        analyzer = DeviceAnalyzer(self.mock_system)
        result = analyzer.get_network_info()
        assert result == {"network": "Not implemented yet"}

    @unit_test
    def test_get_graphics_info(self):
        """Test getting graphics info returns placeholder implementation."""
        analyzer = DeviceAnalyzer(self.mock_system)
        result = analyzer.get_graphics_info()
        assert result == {"graphics": "Not implemented yet"}
