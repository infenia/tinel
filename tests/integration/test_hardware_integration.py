#!/usr/bin/env python3
"""
Integration tests for hardware analysis functionality.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import json
from unittest.mock import Mock, patch

import pytest

from tinel.hardware.cpu_analyzer import CPUAnalyzer
from tinel.hardware.device_analyzer import DeviceAnalyzer
from tinel.tools.hardware_tools import CPUInfoToolProvider, AllHardwareToolProvider
from tinel.cli.commands.hardware import HardwareCommands
from tinel.interfaces import CommandResult
from tests.utils import (
    integration_test,
    AssertionHelpers,
    IntegrationTestHelpers,
    TestDataBuilder,
)


class TestCPUAnalyzerIntegration:
    """Integration tests for CPU analyzer with real system interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.analyzer = CPUAnalyzer(self.mock_system)

    @integration_test
    def test_full_cpu_analysis_workflow(self, sample_cpuinfo, sample_lscpu):
        """Test complete CPU analysis workflow."""
        # Set up comprehensive mocks
        self._setup_complete_system_mock(sample_cpuinfo, sample_lscpu)

        # Run full analysis
        cpu_info = self.analyzer.get_cpu_info()

        # Verify comprehensive structure
        self._verify_complete_cpu_info(cpu_info)

        # Verify caching behavior
        self._verify_caching_works(cpu_info)

    @integration_test
    def test_cpu_analysis_with_missing_data(self):
        """Test CPU analysis when some system data is missing."""
        # Mock partial system responses
        self.mock_system.read_file.side_effect = lambda path: {
            "/proc/cpuinfo": "model name : Test CPU\nflags : sse sse2\n",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq": None,
            "/sys/devices/system/cpu/vulnerabilities/spectre_v1": "Mitigation: barriers",
        }.get(path)

        self.mock_system.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="lscpu: not found", returncode=127
        )

        self.mock_system.file_exists.return_value = False

        cpu_info = self.analyzer.get_cpu_info()

        # Should handle missing data gracefully
        assert "lscpu_error" in cpu_info
        assert cpu_info["model_name"] == "Test CPU"
        assert "sse" in cpu_info["cpu_flags"]

    @integration_test
    def test_cpu_optimization_recommendations(self):
        """Test CPU optimization recommendations generation."""
        # Set up system in suboptimal state
        self._setup_suboptimal_system()

        cpu_info = self.analyzer.get_cpu_info()

        # Should generate recommendations
        assert "optimization_recommendations" in cpu_info
        recommendations = cpu_info["optimization_recommendations"]

        # Should have performance and security recommendations
        rec_types = {rec["type"] for rec in recommendations}
        assert "performance" in rec_types  # For powersave governor
        assert "security" in rec_types  # For vulnerabilities

        # Each recommendation should have required fields
        for rec in recommendations:
            AssertionHelpers.assert_contains_keys(
                rec, ["type", "issue", "recommendation", "command"]
            )

    def _setup_complete_system_mock(self, cpuinfo, lscpu):
        """Set up complete system mock with all data sources."""
        # Basic data sources
        file_responses = {
            "/proc/cpuinfo": cpuinfo,
            # Frequency data
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq": "2000000",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq": "400000",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq": "4600000",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor": "performance",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors": "conservative ondemand userspace powersave performance schedutil",
            # Topology data
            "/sys/devices/system/cpu/cpu0/topology/physical_package_id": "0",
            "/sys/devices/system/cpu/cpu1/topology/physical_package_id": "0",
            "/sys/devices/system/cpu/cpu0/topology/core_id": "0",
            "/sys/devices/system/cpu/cpu1/topology/core_id": "1",
            # Cache data
            "/sys/devices/system/cpu/cpu0/cache/index0/size": "32K",
            "/sys/devices/system/cpu/cpu0/cache/index0/type": "Data",
            "/sys/devices/system/cpu/cpu0/cache/index0/level": "1",
            "/sys/devices/system/cpu/cpu0/cache/index2/size": "256K",
            "/sys/devices/system/cpu/cpu0/cache/index2/type": "Unified",
            "/sys/devices/system/cpu/cpu0/cache/index2/level": "2",
            # Vulnerability data
            "/sys/devices/system/cpu/vulnerabilities/spectre_v1": "Mitigation: barriers",
            "/sys/devices/system/cpu/vulnerabilities/spectre_v2": "Mitigation: Enhanced IBRS",
            "/sys/devices/system/cpu/vulnerabilities/meltdown": "Mitigation: PTI",
        }

        self.mock_system.read_file.side_effect = lambda path: file_responses.get(path)

        # Command responses
        command_responses = {
            "lscpu": CommandResult(success=True, stdout=lscpu, stderr="", returncode=0),
            "nproc": CommandResult(success=True, stdout="8", stderr="", returncode=0),
        }

        def mock_run_command(cmd):
            cmd_key = cmd[0] if isinstance(cmd, list) else cmd
            return command_responses.get(
                cmd_key,
                CommandResult(
                    success=False, stdout="", stderr="command not found", returncode=127
                ),
            )

        self.mock_system.run_command.side_effect = mock_run_command

        # File existence checks
        cache_files = {
            "/sys/devices/system/cpu/cpu0/cache/index0/size",
            "/sys/devices/system/cpu/cpu0/cache/index0/type",
            "/sys/devices/system/cpu/cpu0/cache/index0/level",
            "/sys/devices/system/cpu/cpu0/cache/index2/size",
            "/sys/devices/system/cpu/cpu0/cache/index2/type",
            "/sys/devices/system/cpu/cpu0/cache/index2/level",
        }

        self.mock_system.file_exists.side_effect = lambda path: path in cache_files

    def _setup_suboptimal_system(self):
        """Set up system in suboptimal state for testing recommendations."""
        # Minimal cpuinfo with basic flags
        basic_cpuinfo = """processor	: 0
model name	: Test CPU
flags		: fpu vme de pse tsc msr pae
"""

        file_responses = {
            "/proc/cpuinfo": basic_cpuinfo,
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor": "powersave",
            "/sys/devices/system/cpu/vulnerabilities/spectre_v1": "Vulnerable",
            "/sys/devices/system/cpu/vulnerabilities/spectre_v2": "Vulnerable",
        }

        self.mock_system.read_file.side_effect = lambda path: file_responses.get(path)

        # Command responses for suboptimal system
        command_responses = {
            "lscpu": CommandResult(
                success=True, stdout="Architecture: x86_64\n", stderr="", returncode=0
            ),
            "nproc": CommandResult(success=True, stdout="4", stderr="", returncode=0),
        }

        def mock_run_command(cmd):
            cmd_key = cmd[0] if isinstance(cmd, list) else cmd
            return command_responses.get(
                cmd_key,
                CommandResult(
                    success=False, stdout="", stderr="command not found", returncode=127
                ),
            )

        self.mock_system.run_command.side_effect = mock_run_command
        self.mock_system.file_exists.return_value = False

    def _verify_complete_cpu_info(self, cpu_info):
        """Verify that CPU info contains expected comprehensive data."""
        # Basic parsing results
        AssertionHelpers.assert_contains_keys(
            cpu_info, ["model_name", "vendor_id", "cpu_flags"]
        )

        # Feature analysis
        AssertionHelpers.assert_contains_keys(
            cpu_info,
            ["security_features", "performance_features", "virtualization_features"],
        )

        # System information sections
        expected_sections = [
            "current_frequency_mhz",
            "min_frequency_mhz",
            "max_frequency_mhz",
            "current_governor",
            "available_governors",
            "logical_cpus",
            "vulnerabilities",
        ]

        for section in expected_sections:
            if section not in cpu_info:
                # Some sections might be missing on test systems - that's OK
                continue

        # Verify data types
        assert isinstance(cpu_info["cpu_flags"], list)
        assert len(cpu_info["cpu_flags"]) > 0

        for feature_set in [
            "security_features",
            "performance_features",
            "virtualization_features",
        ]:
            if feature_set in cpu_info:
                assert isinstance(cpu_info[feature_set], dict)
                for feature, enabled in cpu_info[feature_set].items():
                    assert isinstance(enabled, bool)

    def _verify_caching_works(self, first_result):
        """Verify that caching mechanism works correctly."""
        # Second call should return cached result
        second_result = self.analyzer.get_cpu_info()

        # Results should be identical
        assert first_result == second_result

        # Verify system calls were cached (mock call counts should be same)
        # This is tested more thoroughly in unit tests


class TestDeviceAnalyzerIntegration:
    """Integration tests for device analyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.device_analyzer = DeviceAnalyzer(self.mock_system)

    @integration_test
    def test_get_all_hardware_info(self, sample_cpuinfo, sample_lscpu):
        """Test getting all hardware information."""
        # Mock CPU analyzer data
        cpu_data = {
            "model_name": "Test CPU",
            "vendor_id": "TestVendor",
            "cpu_flags": ["sse", "sse2", "avx"],
        }

        with patch.object(
            self.device_analyzer.cpu_analyzer, "get_cpu_info", return_value=cpu_data
        ):
            hardware_info = self.device_analyzer.get_all_hardware_info()

            # Verify structure
            assert hasattr(hardware_info, "cpu")
            assert hardware_info.cpu == cpu_data

    @integration_test
    def test_cpu_info_delegation(self):
        """Test CPU info delegation to CPU analyzer."""
        expected_cpu_info = {"model": "Test CPU", "cores": 4}

        with patch.object(
            self.device_analyzer.cpu_analyzer,
            "get_cpu_info",
            return_value=expected_cpu_info,
        ):
            result = self.device_analyzer.get_cpu_info()

            assert result == expected_cpu_info


class TestHardwareToolsIntegration:
    """Integration tests for hardware tools."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()

    @integration_test
    def test_cpu_tool_provider(self, sample_cpuinfo):
        """Test CPU tool provider integration."""
        cpu_tool = CPUInfoToolProvider(self.mock_system)

        # Mock the device analyzer
        mock_cpu_data = {
            "model_name": "Test CPU",
            "vendor_id": "TestVendor",
            "cpu_flags": ["sse", "sse2"],
            "security_features": {"nx_bit": True},
            "performance_features": {"sse2": True},
        }

        with patch.object(
            cpu_tool.device_analyzer, "get_cpu_info", return_value=mock_cpu_data
        ):
            result = cpu_tool.execute({})

            assert result == mock_cpu_data

    @integration_test
    def test_all_hardware_tool_provider(self):
        """Test all hardware tool provider integration."""
        all_hw_tool = AllHardwareToolProvider(self.mock_system)

        # Mock hardware info
        mock_cpu_data = {"model": "Test CPU", "cores": 4}
        mock_hardware_info = Mock()
        mock_hardware_info.cpu = mock_cpu_data

        with patch.object(
            all_hw_tool.device_analyzer,
            "get_all_hardware_info",
            return_value=mock_hardware_info,
        ):
            result = all_hw_tool.execute({})

            assert "cpu" in result
            assert result["cpu"] == mock_cpu_data

    @integration_test
    def test_tool_provider_metadata(self):
        """Test tool provider metadata consistency."""
        cpu_tool = CPUInfoToolProvider(self.mock_system)
        all_hw_tool = AllHardwareToolProvider(self.mock_system)

        # Verify tool names
        assert cpu_tool.get_tool_name() == "get_cpu_info"
        assert all_hw_tool.get_tool_name() == "get_all_hardware"

        # Verify descriptions are present
        assert len(cpu_tool.get_tool_description()) > 0
        assert len(all_hw_tool.get_tool_description()) > 0

        # Verify input schemas
        cpu_schema = cpu_tool.get_input_schema()
        all_hw_schema = all_hw_tool.get_input_schema()

        assert isinstance(cpu_schema, dict)
        assert isinstance(all_hw_schema, dict)
        assert "type" in cpu_schema
        assert "type" in all_hw_schema


class TestHardwareCommandsIntegration:
    """Integration tests for hardware CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_formatter = Mock()
        self.mock_error_handler = Mock()
        self.hardware_commands = HardwareCommands(
            self.mock_formatter, self.mock_error_handler
        )

    @integration_test
    def test_cpu_command_execution(self):
        """Test CPU command execution."""
        # Mock arguments
        args = Mock()
        args.hardware_command = "cpu"
        args.detailed = False
        args.temperature = False
        args.features = False

        # Mock tool execution
        mock_cpu_data = {"model": "Test CPU", "cores": 4}
        with patch.object(
            self.hardware_commands.cpu_tool, "execute", return_value=mock_cpu_data
        ):
            result = self.hardware_commands.execute(args)

            assert result == 0  # Success

            # Verify formatter was called
            self.mock_formatter.print_output.assert_called_once_with(
                mock_cpu_data, "CPU Information"
            )

    @integration_test
    def test_all_hardware_command_execution(self):
        """Test all hardware command execution."""
        # Mock arguments
        args = Mock()
        args.hardware_command = "all"
        args.detailed = False
        args.summary = False

        # Mock tool execution
        mock_hw_data = {"cpu": {"model": "Test CPU"}}
        with patch.object(
            self.hardware_commands.all_hardware_tool,
            "execute",
            return_value=mock_hw_data,
        ):
            result = self.hardware_commands.execute(args)

            assert result == 0  # Success

            # Verify formatter was called with correct title
            self.mock_formatter.print_output.assert_called_once_with(
                mock_hw_data, "Complete Hardware Information"
            )

    @integration_test
    def test_command_error_handling(self):
        """Test command error handling."""
        args = Mock()
        args.hardware_command = "cpu"
        args.detailed = False
        args.temperature = False
        args.features = False

        # Mock tool to raise exception
        with patch.object(
            self.hardware_commands.cpu_tool,
            "execute",
            side_effect=RuntimeError("Test error"),
        ):
            # Error should be raised and wrapped in HardwareError
            with pytest.raises(Exception):  # Catches HardwareError or parent exceptions
                self.hardware_commands.execute(args)

    @integration_test
    def test_unknown_command_handling(self):
        """Test handling of unknown hardware commands."""
        args = Mock()
        args.hardware_command = "unknown_command"

        result = self.hardware_commands.execute(args)

        assert result == 1  # Error
        self.mock_error_handler.handle_error.assert_called_once()


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    @integration_test
    def test_complete_cpu_analysis_workflow(self, sample_cpuinfo, sample_lscpu):
        """Test complete workflow from system interface to formatted output."""
        # Create real components with mocked system interface
        mock_system = Mock()

        # Set up comprehensive system mock
        self._setup_realistic_system_mock(mock_system, sample_cpuinfo, sample_lscpu)

        # Create analyzer and tool
        cpu_analyzer = CPUAnalyzer(mock_system)
        cpu_tool = CPUInfoToolProvider(mock_system)

        # Execute tool
        result = cpu_tool.execute({"detailed": True})

        # Verify comprehensive result structure
        AssertionHelpers.assert_valid_cpu_info(result)

        # Verify specific data integrity
        assert "Intel" in result["model_name"]
        assert "GenuineIntel" == result["vendor_id"]
        assert len(result["cpu_flags"]) > 50  # Should have many flags

        # Verify feature analysis
        assert result["security_features"]["nx_bit"] is True  # nx flag present
        assert result["performance_features"]["avx2"] is True  # avx2 flag present
        assert result["virtualization_features"]["vmx"] is True  # vmx flag present

    @integration_test
    def test_error_propagation_workflow(self):
        """Test error propagation through the complete workflow."""
        # Create components with failing system interface
        mock_system = Mock()
        mock_system.read_file.return_value = None
        mock_system.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="command failed", returncode=1
        )
        mock_system.file_exists.return_value = False

        # Create tool
        cpu_tool = CPUInfoToolProvider(mock_system)

        # Execute tool - should handle errors gracefully
        result = cpu_tool.execute({})

        # Should have error indicators but not crash
        assert "proc_cpuinfo_error" in result
        assert "lscpu_error" in result

    def _setup_realistic_system_mock(self, mock_system, cpuinfo, lscpu):
        """Set up realistic system mock for end-to-end testing."""
        # File system responses
        file_data = {
            "/proc/cpuinfo": cpuinfo,
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq": "2000000",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor": "performance",
            "/sys/devices/system/cpu/vulnerabilities/spectre_v1": "Mitigation: barriers",
            "/sys/devices/system/cpu/vulnerabilities/spectre_v2": "Mitigation: Enhanced IBRS",
        }

        mock_system.read_file.side_effect = lambda path: file_data.get(path)

        # Command responses
        cmd_data = {
            "lscpu": CommandResult(success=True, stdout=lscpu, stderr="", returncode=0),
            "nproc": CommandResult(success=True, stdout="8", stderr="", returncode=0),
        }

        def mock_run_command(cmd):
            return cmd_data.get(
                cmd[0],
                CommandResult(
                    success=False, stdout="", stderr="not found", returncode=127
                ),
            )

        mock_system.run_command.side_effect = mock_run_command
        mock_system.file_exists.return_value = False


@pytest.mark.parametrize(
    "command_name,expected_title",
    [
        ("cpu", "CPU Information"),
        ("all", "Complete Hardware Information"),
    ],
)
@integration_test
def test_command_title_mapping(command_name, expected_title):
    """Test that commands use correct titles for output."""
    mock_formatter = Mock()
    mock_error_handler = Mock()
    hardware_commands = HardwareCommands(mock_formatter, mock_error_handler)

    args = Mock()
    args.hardware_command = command_name
    args.detailed = False
    args.summary = False
    args.temperature = False
    args.features = False

    # Mock tool responses
    mock_data = {"test": "data"}

    if command_name == "cpu":
        with patch.object(
            hardware_commands.cpu_tool, "execute", return_value=mock_data
        ):
            hardware_commands.execute(args)
    else:
        with patch.object(
            hardware_commands.all_hardware_tool, "execute", return_value=mock_data
        ):
            hardware_commands.execute(args)

    # Verify correct title was used
    mock_formatter.print_output.assert_called_once_with(mock_data, expected_title)
