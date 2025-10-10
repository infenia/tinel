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

# --- Fixtures ---

@pytest.fixture
def mock_system_interface():
    """Fixture for a mocked SystemInterface."""
    return MagicMock()

@pytest.fixture
def memory_analyzer(mock_system_interface):
    """Fixture for a MemoryAnalyzer with a mocked system interface."""
    return MemoryAnalyzer(system_interface=mock_system_interface)

# --- Sample Data ---

MEMINFO_OUTPUT = """
MemTotal:       16327664 kB
MemFree:         8036696 kB
MemAvailable:   10000000 kB
Buffers:          100000 kB
Cached:           2000000 kB
SwapTotal:       2097148 kB
SwapFree:        1048572 kB
"""

MEMINFO_NO_SWAP_OUTPUT = """
MemTotal:       16327664 kB
MemFree:         8036696 kB
MemAvailable:   10000000 kB
SwapTotal:             0 kB
SwapFree:              0 kB
"""

DMIDECODE_OUTPUT = """
Handle 0x003E, DMI type 17, 40 bytes
Memory Device
	Array Handle: 0x003D
	Size: 16384 MB
	Type: DDR4
	Manufacturer: Hynix
"""

# --- Test Cases ---

class TestMemoryAnalyzer:
    """Test suite for the refactored MemoryAnalyzer."""

    def test_parse_meminfo_full(self, memory_analyzer):
        """Test parsing of a complete /proc/meminfo output."""
        info = memory_analyzer._parse_meminfo(MEMINFO_OUTPUT)
        assert info['total_memory_kb'] == 16327664
        assert info['available_memory_kb'] == 10000000
        assert info['used_memory_kb'] == 6327664
        assert info['memory_usage_percent'] == 38.75
        assert info['total_swap_kb'] == 2097148
        assert info['free_swap_kb'] == 1048572
        assert info['used_swap_kb'] == 1048576
        assert info['swap_usage_percent'] == 50.0

    def test_parse_meminfo_no_swap(self, memory_analyzer):
        """Test parsing of /proc/meminfo content with no swap space."""
        info = memory_analyzer._parse_meminfo(MEMINFO_NO_SWAP_OUTPUT)
        assert info['total_swap_kb'] == 0
        assert info['swap_usage_percent'] == 0.0
        assert 'used_swap_kb' not in info

    def test_parse_meminfo_empty_input(self, memory_analyzer):
        """Test that parsing empty content does not raise an error."""
        info = memory_analyzer._parse_meminfo("")
        assert 'total_memory_kb' not in info

    @patch('psutil.virtual_memory')
    @patch('psutil.swap_memory')
    def test_get_memory_info_happy_path(self, mock_swap, mock_virtual, memory_analyzer, mock_system_interface):
        """Test the full get_memory_info flow with all data sources succeeding."""
        mock_system_interface.read_file.return_value = MEMINFO_OUTPUT
        mock_system_interface.run_command.return_value = CommandResult(success=True, stdout=DMIDECODE_OUTPUT, stderr="", returncode=0)
        mock_virtual.return_value = MagicMock(total=16 * 1024**3, available=1, used=1, percent=1)
        mock_swap.return_value = MagicMock(total=2 * 1024**3, used=1, percent=1)

        info = memory_analyzer.get_memory_info()

        assert info['total_memory_kb'] == 16327664
        assert info['psutil_total_memory_bytes'] == 16 * 1024**3
        assert len(info['memory_devices']) == 1
        assert info['memory_devices'][0]['manufacturer'] == 'Hynix'

    def test_get_memory_info_meminfo_fails_fallback_to_psutil(self, memory_analyzer, mock_system_interface):
        """Test fallback to psutil when reading /proc/meminfo fails."""
        mock_system_interface.read_file.return_value = None

        with patch('psutil.virtual_memory') as mock_virtual, patch('psutil.swap_memory') as mock_swap:
            mock_virtual.return_value = MagicMock(total=8*1024**3, available=4*1024**3, used=4*1024**3, percent=50.0)
            mock_swap.return_value = MagicMock(total=1*1024**3, used=0, percent=0.0, free=1*1024**3)
            mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)

            info = memory_analyzer.get_memory_info()

        assert 'proc_meminfo_error' in info
        assert info['total_memory_bytes'] == 8 * 1024**3
        assert info['memory_usage_percent'] == 50.0
        assert info['total_swap_bytes'] == 1 * 1024**3
        assert 'psutil_total_memory_bytes' in info

    def test_get_memory_info_psutil_fails(self, memory_analyzer, mock_system_interface):
        """Test graceful handling of psutil failures."""
        mock_system_interface.read_file.return_value = MEMINFO_OUTPUT
        mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)

        with patch('psutil.virtual_memory', side_effect=Exception("virtual fail")), \
             patch('psutil.swap_memory', side_effect=Exception("swap fail")):

            info = memory_analyzer.get_memory_info()

        assert 'total_memory_kb' in info
        assert 'psutil_error' in info
        assert "psutil.virtual_memory: virtual fail" in info['psutil_error']
        assert "psutil.swap_memory: swap fail" in info['psutil_error']

    def test_get_memory_info_dmidecode_fails(self, memory_analyzer, mock_system_interface):
        """Test graceful handling of dmidecode failures."""
        mock_system_interface.read_file.return_value = MEMINFO_OUTPUT
        mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="command not found", error="dmidecode not found", returncode=127)

        with patch('psutil.virtual_memory'), patch('psutil.swap_memory'):
            info = memory_analyzer.get_memory_info()

        assert 'total_memory_kb' in info
        assert 'dmidecode_error' in info
        assert info['dmidecode_error'] == "dmidecode not found"

    def test_dmidecode_parse_error(self, memory_analyzer, mock_system_interface):
        """Test graceful handling of dmidecode parsing errors."""
        mock_system_interface.read_file.return_value = MEMINFO_OUTPUT
        mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="invalid output", stderr="", returncode=0)

        with patch.object(memory_analyzer, '_parse_dmidecode_output', side_effect=ValueError("Parse Error")):
            with patch('psutil.virtual_memory'), patch('psutil.swap_memory'):
                info = memory_analyzer.get_memory_info()

        assert 'total_memory_kb' in info
        assert 'dmidecode_parse_error' in info
        assert info['dmidecode_parse_error'] == "Parse Error"

    def test_dmidecode_empty_output(self, memory_analyzer, mock_system_interface):
        """Test handling of empty but successful dmidecode output."""
        mock_system_interface.read_file.return_value = MEMINFO_OUTPUT
        mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="", stderr="", returncode=0)

        with patch('psutil.virtual_memory'), patch('psutil.swap_memory'):
            info = memory_analyzer.get_memory_info()

        assert 'total_memory_kb' in info
        assert info['dmidecode_error'] == "Failed to run dmidecode or no output."

    def test_parse_dmidecode_output_last_device_installed(self, memory_analyzer):
        """Test dmidecode parsing when the last device in the output is an installed one."""
        single_device_output = '''
Handle 0x003E, DMI type 17, 40 bytes
Memory Device
	Size: 8192 MB
	Type: DDR4
'''
        parsed = memory_analyzer._parse_dmidecode_output(single_device_output)
        assert len(parsed['memory_devices']) == 1
        assert parsed['memory_devices'][0]['type'] == 'DDR4'