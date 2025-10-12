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

import pytest
from unittest.mock import MagicMock, patch
from tinel.hardware.graphics_analyzer import GraphicsAnalyzer
from tinel.interfaces import CommandResult

# --- MOCK DATA ---

MOCK_NVIDIA_SMI_OUTPUT = """
0, NVIDIA GeForce RTX 3080, 510.47.03, 10240, 2048, 8192, 50, 65
1, NVIDIA GeForce RTX 3080, 510.47.03, 10240, 4096, 6144, 80, 75
"""

MOCK_LSPCI_OUTPUT = """
00:02.0 VGA compatible controller: Intel Corporation HD Graphics 530 [8086:191b] (rev 06) (prog-if 00 [VGA controller])
	Subsystem: Dell HD Graphics 530 [1028:06e0]
	Flags: bus master, fast devsel, latency 0, IRQ 128
	Memory at a0000000 (64-bit, non-prefetchable) [size=16M]
	Memory at 90000000 (64-bit, prefetchable) [size=256M]
	I/O ports at 3000 [size=64]
	[virtual] Expansion ROM at 000c0000 [disabled] [size=128K]
	Capabilities: <access denied>
	Kernel driver in use: i915
	Kernel modules: i915
01:00.0 VGA compatible controller: NVIDIA Corporation GP107 [GeForce GTX 1050 Ti] [10de:1c82] (rev a1) (prog-if 00 [VGA controller])
	Subsystem: ZOTAC International (MCO) Ltd. GP107 [GeForce GTX 1050 Ti] [19da:1435]
	Flags: bus master, fast devsel, latency 0, IRQ 129
	Memory at a2000000 (32-bit, non-prefetchable) [size=16M]
	Memory at b0000000 (64-bit, prefetchable) [size=256M]
	Memory at c0000000 (64-bit, prefetchable) [size=32M]
	I/O ports at 4000 [size=128]
	Expansion ROM at a3080000 [disabled] [size=512K]
	Capabilities: <access denied>
	Kernel driver in use: nvidia
	Kernel modules: nvidiafb, nouveau, nvidia_drm, nvidia
"""


@pytest.fixture
def mock_si():
    """Fixture for a mocked SystemInterface."""
    return MagicMock()


@pytest.fixture
def analyzer(mock_si):
    """Fixture for a GraphicsAnalyzer with a mocked SystemInterface."""
    return GraphicsAnalyzer(system_interface=mock_si)


class TestGraphicsAnalyzer:

    def test_get_graphics_info_caching(self, analyzer, mock_si):
        """Test that the main get_graphics_info method caches results."""
        # Provide valid nvidia-smi output so it succeeds on the first try
        mock_si.run_command.return_value = CommandResult(True, MOCK_NVIDIA_SMI_OUTPUT, "", 0)
        analyzer.get_graphics_info()
        analyzer.get_graphics_info()
        # The underlying command should only be called once due to caching
        mock_si.run_command.assert_called_once_with([
            'nvidia-smi',
            '--query-gpu=index,name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu',
            '--format=csv,noheader,nounits'
        ])

    def test_nvidia_smi_success(self, analyzer, mock_si):
        """Test successful parsing of nvidia-smi output."""
        mock_si.run_command.return_value = CommandResult(True, MOCK_NVIDIA_SMI_OUTPUT, "", 0)
        info = analyzer.get_graphics_info()

        assert info['source'] == 'nvidia-smi'
        assert len(info['gpus']) == 2
        assert info['gpus'][0]['model'] == 'NVIDIA GeForce RTX 3080'
        assert info['gpus'][0]['memory_total_mb'] == 10240
        assert info['gpus'][0]['utilization_percent'] == 50
        assert info['gpus'][1]['temperature_celsius'] == 75

    def test_rocm_smi_fallback(self, analyzer, mock_si):
        """Test fallback to rocm-smi when nvidia-smi fails."""
        # This test currently only checks the placeholder implementation
        mock_si.run_command.side_effect = [
            CommandResult(False, "", "not found", 1),  # nvidia-smi fails
            CommandResult(True, "some rocm output", "", 0)   # rocm-smi succeeds
        ]
        info = analyzer.get_graphics_info()
        assert info['source'] == 'rocm-smi'
        assert info['gpus'][0]['model'] == 'AMD GPU (rocm-smi placeholder)'

    def test_lspci_fallback(self, analyzer, mock_si):
        """Test fallback to lspci when both nvidia-smi and rocm-smi fail."""
        mock_si.run_command.side_effect = [
            CommandResult(False, "", "not found", 1),  # nvidia-smi fails
            CommandResult(False, "", "not found", 1),  # rocm-smi fails
            CommandResult(True, MOCK_LSPCI_OUTPUT, "", 0)      # lspci succeeds
        ]
        info = analyzer.get_graphics_info()
        assert info['source'] == 'lspci'
        assert len(info['gpus']) == 2
        assert 'Intel Corporation HD Graphics 530' in info['gpus'][0]['model']
        assert info['gpus'][0]['vendor_id'] == '8086'
        assert 'NVIDIA Corporation GP107' in info['gpus'][1]['model']
        assert info['gpus'][1]['device_id'] == '1c82'
        assert 'kernel_driver_in_use' in info['gpus'][1]['details']

    def test_all_tools_fail(self, analyzer, mock_si):
        """Test the case where all underlying commands fail."""
        with patch.object(analyzer, 'logger') as mock_logger:
            mock_si.run_command.return_value = CommandResult(False, "", "error", 1)
            info = analyzer.get_graphics_info()
            assert 'gpus' not in info
            assert 'source' not in info
            assert mock_logger.warning.called

    def test_parse_lspci_output_no_vga(self, analyzer):
        """Test lspci output that contains no VGA devices."""
        output = "00:00.0 Host bridge: Intel Corporation Sky Lake Host Bridge/DRAM Registers (rev 07)"
        # This is an integration-style test of a private method.
        with patch.object(analyzer, 'system') as mock_system:
            mock_system.run_command.return_value = CommandResult(True, output, "", 0)
            gpus = analyzer._get_lspci_info()
            assert gpus is None

    def test_parse_nvidia_smi_malformed_line(self, analyzer, mock_si):
        """Test that malformed lines in nvidia-smi output are skipped and fallback fails."""
        with patch.object(analyzer, 'logger') as mock_logger:
            malformed_output = "0, GPU, 510, 10240, 2048, 8192, 50\n" # Missing one field
            mock_si.run_command.side_effect = [
                CommandResult(True, malformed_output, "", 0),  # nvidia-smi with bad data
                CommandResult(False, "", "not found", 1),      # rocm-smi fails
                CommandResult(False, "", "not found", 1)       # lspci fails
            ]
            info = analyzer.get_graphics_info()
            assert not info.get('gpus') # Should be empty as all tools fail
            assert mock_logger.warning.called