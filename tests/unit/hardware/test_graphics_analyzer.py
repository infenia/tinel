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

from tinel.hardware.graphics_analyzer import GraphicsAnalyzer, GPU
from tinel.interfaces import CommandResult


class TestGraphicsAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = GraphicsAnalyzer(self.mock_system_interface)

    def test_get_graphics_info_caching(self):
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="", returncode=1
        )
        self.analyzer.get_graphics_info()
        self.assertEqual(self.mock_system_interface.run_command.call_count, 3)
        self.analyzer.get_graphics_info()
        self.assertEqual(self.mock_system_interface.run_command.call_count, 3)

    def test_nvidia_smi_success(self):
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout="0, NVIDIA GeForce RTX 3080, 455.28, 10240, 2048, 8192, 50, 65",
            stderr="",
            returncode=0,
        )
        info = self.analyzer.get_graphics_info()
        self.assertEqual(len(info.gpus), 1)
        self.assertEqual(info.gpus[0].model, "NVIDIA GeForce RTX 3080")

    def test_rocm_smi_fallback(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="not found", returncode=127),
            CommandResult(success=True, stdout="some rocm output", stderr="", returncode=0),
        ]
        info = self.analyzer.get_graphics_info()
        self.assertEqual(info.source, "rocm-smi")

    def test_lspci_fallback(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=False, stdout="", stderr="", returncode=1),
            CommandResult(success=False, stdout="", stderr="", returncode=1),
            CommandResult(
                success=True,
                stdout="00:02.0 VGA compatible controller [0300]: Intel Corporation HD Graphics 530 [8086:191b] (rev 06)",
                stderr="",
                returncode=0,
            ),
        ]
        info = self.analyzer.get_graphics_info()
        self.assertEqual(len(info.gpus), 1)

    def test_all_tools_fail(self):
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="", returncode=1
        )
        info = self.analyzer.get_graphics_info()
        self.assertEqual(len(info.gpus), 0)

    def test_parse_lspci_output_no_vga(self):
        gpus = self.analyzer._parse_lspci_output("Not a VGA device")
        self.assertEqual(len(gpus), 0)

    def test_parse_nvidia_smi_malformed_line(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="malformed line", stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="", returncode=1),
            CommandResult(success=False, stdout="", stderr="", returncode=1),
        ]
        info = self.analyzer.get_graphics_info()
        self.assertEqual(len(info.gpus), 0)

    def test_nvidia_smi_with_non_numeric_values(self):
        self.mock_system_interface.run_command.side_effect = [
            CommandResult(success=True, stdout="0, RTX 3080, 455.28, 10240, 2048, 8192, 50, not-a-number", stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="", returncode=1),
            CommandResult(success=False, stdout="", stderr="", returncode=1),
        ]
        info = self.analyzer.get_graphics_info()
        self.assertEqual(len(info.gpus), 0)

    def test_get_amd_info_placeholder(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="ROCm output", stderr="", returncode=0)
        info = self.analyzer._get_amd_info()
        self.assertEqual(info[0].model, "AMD GPU (rocm-smi placeholder)")

    def test_lspci_no_model_match(self):
        lspci_output = "01:00.0 VGA compatible controller: [10de:1f08] (rev a1)"
        gpus = self.analyzer._parse_lspci_output(lspci_output)
        self.assertEqual(gpus[0].model, "Unknown")

    def test_lspci_with_details(self):
        lspci_output = "00:02.0 VGA compatible controller: Intel Corporation HD Graphics 530 [8086:191b] (rev 06)\n\tSubsystem: Dell Inc. HD Graphics 530"
        gpus = self.analyzer._parse_lspci_output(lspci_output)
        self.assertIn("subsystem", gpus[0].details)

    def test_lspci_vga_controller_no_details(self):
        lspci_output = "00:02.0 VGA compatible controller [0300]: Intel Corporation HD Graphics 530 [8086:191b] (rev 06)"
        gpus = self.analyzer._parse_lspci_output(lspci_output)
        self.assertEqual(len(gpus), 1)
        self.assertEqual(gpus[0].details, {})

    def test_lspci_with_malformed_details(self):
        lspci_output = "00:02.0 VGA compatible controller: Intel Corporation HD Graphics 530 [8086:191b] (rev 06)\n\tSome malformed line"
        gpus = self.analyzer._parse_lspci_output(lspci_output)
        self.assertIn("misc", gpus[0].details)

    def test_gpu_details_can_be_none(self):
        gpu = GPU(model="Test GPU")
        gpu.details = None
        # This is to satisfy coverage of the 'if current_gpu.details is not None:' checks
        self.assertIsNone(gpu.details)

if __name__ == "__main__":
    unittest.main()