#!/usr/bin/env python3
"""
Unit tests for device analyzer implementation.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from unittest.mock import Mock, patch

from tests.utils import unit_test
from tinel.hardware.device_analyzer import DeviceAnalyzer
from tinel.interfaces import HardwareInfo, SystemInterface


class TestDeviceAnalyzer:
    """Test cases for DeviceAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=SystemInterface)
        self.analyzer = DeviceAnalyzer(self.mock_system)

    @unit_test
    @patch('tinel.hardware.device_analyzer.CPUAnalyzer')
    def test_initialization(self, mock_cpu_analyzer_class):
        """Test device analyzer initialization."""
        # Setup mock CPU analyzer
        mock_cpu_analyzer = Mock()
        mock_cpu_analyzer_class.return_value = mock_cpu_analyzer

        # Test with mock system interface
        analyzer = DeviceAnalyzer(self.mock_system)
        assert analyzer.system == self.mock_system
        assert analyzer.cpu_analyzer == mock_cpu_analyzer

        # Test with default system interface (should create LinuxSystemInterface)
        analyzer_default = DeviceAnalyzer()
        assert analyzer_default.system is not None
        assert hasattr(analyzer_default.system, 'run_command')
        assert analyzer_default.cpu_analyzer == mock_cpu_analyzer

    @unit_test
    @patch('tinel.hardware.device_analyzer.CPUAnalyzer')
    def test_get_cpu_info(self, mock_cpu_analyzer_class):
        """Test getting CPU info delegates to CPUAnalyzer."""
        # Setup
        mock_cpu_analyzer = Mock()
        expected_cpu_info = {"model": "Test CPU", "cores": 4}
        mock_cpu_analyzer.get_cpu_info.return_value = expected_cpu_info
        mock_cpu_analyzer_class.return_value = mock_cpu_analyzer

        # Create a new analyzer to use the mocked CPUAnalyzer
        analyzer = DeviceAnalyzer(self.mock_system)

        # Execute
        result = analyzer.get_cpu_info()

        # Verify
        assert result == expected_cpu_info
        mock_cpu_analyzer.get_cpu_info.assert_called_once()

    @unit_test
    @patch('tinel.hardware.device_analyzer.CPUAnalyzer')
    def test_get_all_hardware_info(self, mock_cpu_analyzer_class):
        """Test getting all hardware info returns a HardwareInfo object."""
        # Setup
        mock_cpu_analyzer = Mock()
        expected_cpu_info = {"model": "Test CPU", "cores": 4}
        mock_cpu_analyzer.get_cpu_info.return_value = expected_cpu_info
        mock_cpu_analyzer_class.return_value = mock_cpu_analyzer

        # Create a new analyzer after the patch is applied
        analyzer = DeviceAnalyzer(self.mock_system)

        # Execute
        result = analyzer.get_all_hardware_info()

        # Verify
        assert isinstance(result, HardwareInfo)
        assert result.cpu == expected_cpu_info
        mock_cpu_analyzer.get_cpu_info.assert_called_once()

    @unit_test
    def test_unimplemented_methods(self):
        """Test that unimplemented methods return expected placeholders."""
        # Test memory info
        memory_info = self.analyzer.get_memory_info()
        assert memory_info == {"memory": "Not implemented yet"}

        # Test storage info
        storage_info = self.analyzer.get_storage_info()
        assert storage_info == {"storage": "Not implemented yet"}

        # Test PCI devices
        pci_info = self.analyzer.get_pci_devices()
        assert pci_info == {"pci_devices": "Not implemented yet"}

        # Test USB devices
        usb_info = self.analyzer.get_usb_devices()
        assert usb_info == {"usb_devices": "Not implemented yet"}

        # Test network info
        network_info = self.analyzer.get_network_info()
        assert network_info == {"network": "Not implemented yet"}

        # Test graphics info
        graphics_info = self.analyzer.get_graphics_info()
        assert graphics_info == {"graphics": "Not implemented yet"}
