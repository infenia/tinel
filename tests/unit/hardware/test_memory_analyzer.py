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

# --- Test Data ---
DMIDECODE_FULL = """
Handle 0x0001, DMI type 17, 40 bytes
	Memory Device
	Size: 8 GB
"""
DMIDECODE_MULTI_INSTALLED = """
Handle 0x0001, DMI type 17, 40 bytes
	Memory Device
	Size: 8 GB
Handle 0x0002, DMI type 17, 40 bytes
	Memory Device
	Size: 16 GB
"""
DMIDECODE_UNINSTALLED = (
    "Handle 0x0001, DMI type 17, 40 bytes\n\tSize: No Module Installed"
)
DMIDECODE_GARBAGE = "some random text"
DMIDECODE_OTHER_DEVICE = "Handle 0x0001, DMI type 16, 23 bytes"


@pytest.fixture
def analyzer(mock_si):
    return MemoryAnalyzer(system_interface=mock_si)


@pytest.fixture
def mock_si():
    return MagicMock()


class TestMemoryAnalyzerFinal:
    # --- Unit Tests for _parse_dmidecode_output ---
    def test_parse_dmidecode_variants(self, analyzer):
        assert (
            len(analyzer._parse_dmidecode_output(DMIDECODE_FULL)["memory_devices"]) == 1
        )
        assert (
            len(
                analyzer._parse_dmidecode_output(DMIDECODE_MULTI_INSTALLED)[
                    "memory_devices"
                ]
            )
            == 2
        )
        assert not analyzer._parse_dmidecode_output(DMIDECODE_UNINSTALLED)[
            "memory_devices"
        ]
        assert not analyzer._parse_dmidecode_output(DMIDECODE_GARBAGE)["memory_devices"]
        assert not analyzer._parse_dmidecode_output(DMIDECODE_OTHER_DEVICE)[
            "memory_devices"
        ]

    # --- Integration Tests for get_memory_info ---
    @patch("psutil.virtual_memory")
    @patch("psutil.swap_memory")
    def test_full_success(self, mock_swap, mock_virtual, analyzer, mock_si):
        mock_virtual.return_value = MagicMock(total=1, available=1, used=1, percent=1)
        mock_swap.return_value = MagicMock(total=1, used=1, free=1, percent=1)
        mock_si.run_command.return_value = CommandResult(
            True, DMIDECODE_FULL, "", 0, None
        )
        info = analyzer.get_memory_info()
        assert "total_memory_bytes" in info and "memory_devices" in info
        assert "psutil_error" not in info and "dmidecode_error" not in info

    @patch("psutil.virtual_memory", side_effect=Exception("virtual fail"))
    @patch("psutil.swap_memory", side_effect=Exception("swap fail"))
    def test_psutil_both_fail(self, mock_swap, mock_virtual, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(True, "", "", 0, None)
        info = analyzer.get_memory_info()
        assert "psutil_error" in info
        assert (
            "virtual fail" in info["psutil_error"]
            and "swap fail" in info["psutil_error"]
        )

    @patch("psutil.virtual_memory", MagicMock())
    @patch("psutil.swap_memory", side_effect=Exception("swap fail"))
    def test_psutil_swap_fail_only(self, mock_swap, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(True, "", "", 0, None)
        info = analyzer.get_memory_info()
        assert "total_memory_bytes" in info
        assert "psutil_error" in info
        assert (
            "swap fail" in info["psutil_error"]
            and "virtual" not in info["psutil_error"]
        )

    def test_dmidecode_command_fail_with_error(self, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(False, "", "err", 1, "fail")
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = analyzer.get_memory_info()
        assert "dmidecode_error" in info and info["dmidecode_error"] == "fail"

    def test_dmidecode_command_fail_no_error(self, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(False, "", "", 1, None)
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = analyzer.get_memory_info()
        assert (
            "dmidecode_error" in info
            and "Failed to run dmidecode" in info["dmidecode_error"]
        )

    def test_dmidecode_empty_stdout(self, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(True, "", "", 0, None)
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = analyzer.get_memory_info()
        assert "memory_devices" not in info
        assert "dmidecode_error" not in info

    def test_dmidecode_parse_fail(self, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(True, "bad data", "", 0, None)
        with (
            patch.object(
                analyzer,
                "_parse_dmidecode_output",
                side_effect=Exception("parse error"),
            ),
            patch("psutil.virtual_memory"),
            patch("psutil.swap_memory"),
        ):
            info = analyzer.get_memory_info()
        assert "dmidecode_parse_error" in info

    def test_no_dmi_info_return(self, analyzer, mock_si):
        with patch.object(analyzer, "_get_dmidecode_info", return_value=None):
            with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
                info = analyzer.get_memory_info()
        assert "memory_devices" not in info
        assert "dmidecode_error" not in info

    def test_psutil_virtual_fail_only(self, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(True, "", "", 0, None)
        with (
            patch("psutil.virtual_memory", side_effect=Exception("virtual fail")),
            patch("psutil.swap_memory") as s,
        ):
            s.return_value = MagicMock(total=1, used=1, free=1, percent=1)
            info = analyzer.get_memory_info()
        assert "total_swap_bytes" in info
        assert "psutil_error" in info and "virtual fail" in info["psutil_error"]

    def test_psutil_error_concatenation(self, analyzer, mock_si):
        mock_si.run_command.return_value = CommandResult(True, "", "", 0, None)
        with (
            patch("psutil.virtual_memory", side_effect=Exception("virtual fail")),
            patch("psutil.swap_memory", side_effect=Exception("swap fail")),
        ):
            info = analyzer.get_memory_info()
        assert "psutil_error" in info
        assert (
            info["psutil_error"]
            == "virtual_memory: virtual fail; swap_memory: swap fail"
        )

    def test_parse_dmidecode_comprehensive_edge_cases(self, analyzer):
        """Test that lines with empty keys, empty values, or other irregularities are skipped."""
        dmidecode_output = """
Handle 0x0001, DMI type 17, 40 bytes
	Memory Device
	Size: 8 GB
	Manufacturer:
	: No Key
	Serial Number: 1234
	Part Number: Not Specified
    Invalid Line
"""
        parsed_info = analyzer._parse_dmidecode_output(dmidecode_output)
        devices = parsed_info.get("memory_devices", [])
        assert len(devices) == 1
        device = devices[0]
        assert "manufacturer" not in device
        assert "part_number" not in device
        assert "" not in device
        assert "serial_number" in device
        assert device["size"] == "8 GB"
        assert "invalid_line" not in device

    def test_parse_dmidecode_device_with_no_valid_info(self, analyzer):
        """Test that a device block with no valid attributes is skipped."""
        dmidecode_output = """
Handle 0x0001, DMI type 17, 40 bytes
	Memory Device
	Manufacturer:
	Part Number: Not Specified
	Size: Unknown
"""
        parsed_info = analyzer._parse_dmidecode_output(dmidecode_output)
        devices = parsed_info.get("memory_devices", [])
        assert len(devices) == 0
