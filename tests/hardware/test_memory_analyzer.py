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

from unittest.mock import MagicMock, patch

import pytest

from tinel.hardware.memory_analyzer import MemoryAnalyzer
from tinel.interfaces import CommandResult

# Test constants for memory sizes
SIXTEEN_GB_IN_BYTES = 16 * 1024**3
EIGHT_GB_IN_BYTES = 8 * 1024**3
TWO_GB_IN_BYTES = 2 * 1024**3
ONE_GB_IN_BYTES = 1 * 1024**3
FIFTY_PERCENT = 50.0


@pytest.fixture
def mock_system_interface():
    """Fixture for a mocked SystemInterface."""
    return MagicMock()


@pytest.fixture
def memory_analyzer(mock_system_interface):
    """Fixture for a MemoryAnalyzer with a mocked system interface."""
    return MemoryAnalyzer(system_interface=mock_system_interface)


# Sample dmidecode output for testing
DMIDECODE_OUTPUT = """
Handle 0x003E, DMI type 17, 40 bytes
Memory Device
	Array Handle: 0x003D
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16384 MB
	Form Factor: SODIMM
	Set: None
	Locator: ChannelA-DIMM0
	Bank Locator: BANK 0
	Type: DDR4
	Type Detail: Synchronous
	Speed: 2400 MT/s
	Manufacturer: Hynix
	Serial Number: 12345678
	Asset Tag: 9876543210
	Part Number: HMA82GS6AFR8N-UH
	Rank: 2
	Configured Memory Speed: 2400 MT/s
	Minimum Voltage: 1.2 V
	Maximum Voltage: 1.2 V
	Configured Voltage: 1.2 V

Handle 0x003F, DMI type 17, 40 bytes
Memory Device
	Array Handle: 0x003D
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: SODIMM
	Set: None
	Locator: ChannelB-DIMM0
	Bank Locator: BANK 2
	Type: Unknown
	Type Detail: None
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown
"""


@patch("psutil.virtual_memory")
@patch("psutil.swap_memory")
def test_get_memory_info_success(
    mock_swap, mock_virtual, memory_analyzer, mock_system_interface
):
    """Test get_memory_info with successful psutil and dmidecode calls."""
    # Mock psutil
    mock_virtual.return_value = MagicMock(
        total=SIXTEEN_GB_IN_BYTES,
        available=EIGHT_GB_IN_BYTES,
        used=EIGHT_GB_IN_BYTES,
        percent=FIFTY_PERCENT,
    )
    mock_swap.return_value = MagicMock(
        total=TWO_GB_IN_BYTES,
        used=ONE_GB_IN_BYTES,
        free=ONE_GB_IN_BYTES,
        percent=FIFTY_PERCENT,
    )

    # Mock dmidecode
    mock_system_interface.run_command.return_value = CommandResult(
        success=True, stdout=DMIDECODE_OUTPUT, stderr="", returncode=0
    )

    info = memory_analyzer.get_memory_info()

    # Assert psutil data
    assert info["total_memory_bytes"] == SIXTEEN_GB_IN_BYTES
    assert info["memory_usage_percent"] == FIFTY_PERCENT

    # Assert dmidecode data
    assert "memory_devices" in info
    assert len(info["memory_devices"]) == 1  # "No Module Installed" should be skipped
    device = info["memory_devices"][0]
    assert device["manufacturer"] == "Hynix"
    assert device["size"] == "16384 MB"
    assert (
        "size" not in info["memory_devices"][0]
        or info["memory_devices"][0]["size"] != "No Module Installed"
    )

    mock_system_interface.run_command.assert_called_once_with(
        ["dmidecode", "--type", "memory"]
    )


@patch("psutil.virtual_memory", side_effect=Exception("psutil failed"))
@patch("psutil.swap_memory")
def test_get_memory_info_psutil_fails(
    mock_swap, mock_virtual, memory_analyzer, mock_system_interface
):
    """Test get_memory_info when psutil calls fail."""
    mock_system_interface.run_command.return_value = CommandResult(
        success=False, stdout="", stderr="error", returncode=1
    )

    info = memory_analyzer.get_memory_info()

    assert "psutil_error" in info
    assert "dmidecode_error" in info


def test_get_memory_info_dmidecode_fails(memory_analyzer, mock_system_interface):
    """Test get_memory_info when the dmidecode command fails."""
    # Mock dmidecode failure
    mock_system_interface.run_command.return_value = CommandResult(
        success=False,
        stdout="",
        stderr="command not found",
        returncode=127,
        error="command not found",
    )

    with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
        info = memory_analyzer.get_memory_info()

    assert "dmidecode_error" in info
    assert info["dmidecode_error"] == "command not found"


def test_parse_dmidecode_output_empty(memory_analyzer):
    """Test _parse_dmidecode_output with empty input."""
    parsed = memory_analyzer._parse_dmidecode_output("")
    assert parsed == {"memory_devices": []}


def test_parse_dmidecode_output_no_devices(memory_analyzer):
    """Test _parse_dmidecode_output with output containing no memory devices."""
    output = "Some other dmidecode output"
    parsed = memory_analyzer._parse_dmidecode_output(output)
    assert parsed == {"memory_devices": []}


@patch("psutil.virtual_memory")
@patch("psutil.swap_memory")
def test_get_memory_info_dmidecode_parse_error(
    mock_swap, mock_virtual, memory_analyzer, mock_system_interface
):
    """Test get_memory_info when dmidecode output parsing fails."""
    mock_system_interface.run_command.return_value = CommandResult(
        success=True, stdout="invalid output", stderr="", returncode=0
    )

    # Make the parser raise an exception
    with patch.object(
        memory_analyzer,
        "_parse_dmidecode_output",
        side_effect=ValueError("Parsing failed"),
    ):
        info = memory_analyzer.get_memory_info()

    assert "dmidecode_parse_error" in info
    assert info["dmidecode_parse_error"] == "Parsing failed"


def test_get_memory_info_dmidecode_empty_output(memory_analyzer, mock_system_interface):
    """Test get_memory_info when dmidecode returns success but empty output."""
    mock_system_interface.run_command.return_value = CommandResult(
        success=True, stdout="", stderr="", returncode=0
    )

    with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
        info = memory_analyzer.get_memory_info()

    assert "dmidecode_error" in info
    assert info["dmidecode_error"] == "Failed to run dmidecode or no output."


@patch("psutil.virtual_memory")
@patch("psutil.swap_memory", side_effect=Exception("swap failed"))
def test_get_memory_info_psutil_swap_fails(
    mock_swap, mock_virtual, memory_analyzer, mock_system_interface
):
    """Test get_memory_info when only the swap memory call fails."""
    mock_virtual.return_value = MagicMock(total=1, available=1, used=1, percent=1)
    mock_system_interface.run_command.return_value = CommandResult(
        success=True, stdout="", stderr="", returncode=0
    )

    info = memory_analyzer.get_memory_info()

    # psutil data for virtual_memory should exist
    assert "total_memory_bytes" in info
    # but swap data should be missing, and the error should be logged
    assert "total_swap_bytes" not in info
    assert "psutil_error" in info
    assert info["psutil_error"] == "swap_memory: swap failed"


@patch("psutil.virtual_memory", side_effect=Exception("virtual failed"))
@patch("psutil.swap_memory", side_effect=Exception("swap failed"))
def test_get_memory_info_psutil_both_fail(
    mock_swap, mock_virtual, memory_analyzer, mock_system_interface
):
    """Test get_memory_info when both psutil calls fail."""
    mock_system_interface.run_command.return_value = CommandResult(
        success=True, stdout="", stderr="", returncode=0
    )
    info = memory_analyzer.get_memory_info()

    assert "total_memory_bytes" not in info
    assert "total_swap_bytes" not in info
    assert "psutil_error" in info
    assert "virtual_memory: virtual failed" in info["psutil_error"]
    assert "swap_memory: swap failed" in info["psutil_error"]


DMIDECODE_SINGLE_INSTALLED_OUTPUT = """
Handle 0x003E, DMI type 17, 40 bytes
Memory Device
	Array Handle: 0x003D
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 16384 MB
	Form Factor: SODIMM
	Set: None
	Locator: ChannelA-DIMM0
	Bank Locator: BANK 0
	Type: DDR4
"""


def test_parse_dmidecode_output_last_device_installed(memory_analyzer):
    """Test _parse_dmidecode_output where the last device is installed."""
    parsed = memory_analyzer._parse_dmidecode_output(DMIDECODE_SINGLE_INSTALLED_OUTPUT)
    assert "memory_devices" in parsed
    assert len(parsed["memory_devices"]) == 1
    assert parsed["memory_devices"][0]["type"] == "DDR4"


@patch("psutil.virtual_memory")
@patch("psutil.swap_memory")
def test_get_memory_info_no_dmi_info(mock_swap, mock_virtual, memory_analyzer):
    """Test get_memory_info when _get_dmidecode_info returns a falsy value."""
    with patch.object(memory_analyzer, "_get_dmidecode_info", return_value=None):
        info = memory_analyzer.get_memory_info()

    assert "dmidecode_error" not in info
    assert "memory_devices" not in info
    assert "total_memory_bytes" in info  # psutil info should still be present
