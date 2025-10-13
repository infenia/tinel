#!/usr/bin/env python3
"""
Unit tests for device analyzer implementation.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from unittest.mock import Mock, patch

from tests.utils import unit_test
from tinel.hardware.device_analyzer import DeviceAnalyzer
from tinel.interfaces import SystemInterface


class TestDeviceAnalyzer:
    """Test cases for DeviceAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=SystemInterface)
        self.analyzer = DeviceAnalyzer(self.mock_system)

    @unit_test
    @patch("tinel.hardware.device_analyzer.CPUAnalyzer")
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
        assert hasattr(analyzer_default.system, "run_command")
        assert analyzer_default.cpu_analyzer == mock_cpu_analyzer

    @unit_test
    @patch("tinel.hardware.device_analyzer.CPUAnalyzer")
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
    @patch("tinel.hardware.device_analyzer.CPUAnalyzer")
    @patch("tinel.hardware.device_analyzer.MemoryAnalyzer")
    @patch("tinel.hardware.device_analyzer.NetworkAnalyzer")
    @patch("tinel.hardware.device_analyzer.GraphicsAnalyzer")
    def test_get_all_hardware_info(
        self, mock_graphics_class, mock_network_class, mock_memory_class, mock_cpu_class
    ):
        """Test the aggregation of all hardware information."""
        # Setup mocks for each analyzer's get_info method
        mock_cpu_class.return_value.get_cpu_info.return_value = {"cpu": "data"}
        mock_memory_class.return_value.get_memory_info.return_value = {"memory": "data"}
        mock_network_class.return_value.get_network_info.return_value = {
            "network": "data"
        }
        mock_graphics_class.return_value.get_graphics_info.return_value = {
            "graphics": "data"
        }

        analyzer = DeviceAnalyzer(self.mock_system)

        # Mock the other info methods that are not yet implemented
        with (
            patch.object(analyzer, "get_storage_info", return_value={"disks": "data"}),
            patch.object(
                analyzer, "get_motherboard_info", return_value={"motherboard": "data"}
            ),
        ):
            result = analyzer.get_all_hardware_info()

            from tinel.hardware import HardwareInfo as HardwareInfoFromSource

            assert isinstance(result, HardwareInfoFromSource)
            assert result.cpu == {"cpu": "data"}
            assert result.memory == {"memory": "data"}
            assert result.network == {"network": "data"}
            assert result.graphics == {"graphics": "data"}
            assert result.disks == {"disks": "data"}
            assert result.motherboard == {"motherboard": "data"}

            mock_cpu_class.return_value.get_cpu_info.assert_called_once()
            mock_memory_class.return_value.get_memory_info.assert_called_once()
            mock_network_class.return_value.get_network_info.assert_called_once()
            mock_graphics_class.return_value.get_graphics_info.assert_called_once()

    @unit_test
    def test_unimplemented_methods_return_placeholders(self, mock_system_interface):
        """Test that unimplemented methods return the correct placeholder."""
        analyzer = DeviceAnalyzer(system_interface=mock_system_interface)
        storage_info = analyzer.get_storage_info()
        motherboard_info = analyzer.get_motherboard_info()

        assert storage_info == {"storage": "Not implemented yet"}
        assert motherboard_info == {"motherboard": "Not implemented yet"}
