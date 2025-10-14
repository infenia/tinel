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

from tinel.hardware.cpu_analyzer import CPUAnalyzer
from tinel.interfaces import CommandResult

class TestCPUAnalyzer(unittest.TestCase):
    @patch("psutil.cpu_freq")
    @patch("psutil.cpu_stats")
    def test_analyze_cpu_performance(self, mock_cpu_stats, mock_cpu_freq):
        # Mock lscpu output
        lscpu_output = "Flags: avx avx2 sse4_1 sse4_2"
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout=lscpu_output, stderr="", returncode=0
        )

        # Mock psutil outputs
        mock_cpu_freq.return_value = MagicMock(current=2.5, min=1.0, max=3.0)
        mock_cpu_stats.return_value = MagicMock(
            ctx_switches=100, interrupts=200, soft_interrupts=300, syscalls=400
        )

        analyzer = CPUAnalyzer(system_interface=mock_system_interface)
        lscpu_info = analyzer._parse_lscpu(lscpu_output)
        performance_analysis = analyzer._analyze_cpu_performance(lscpu_info)

        # Assertions for feature detection
        optimizations = performance_analysis["performance_analysis"]["optimizations"]
        self.assertTrue(optimizations["avx_supported"])
        self.assertTrue(optimizations["avx2_supported"])
        self.assertFalse(optimizations["avx512f_supported"])
        self.assertTrue(optimizations["sse4_1_supported"])
        self.assertTrue(optimizations["sse4_2_supported"])

        # Assertions for CPU frequency
        cpu_freq = performance_analysis["performance_analysis"]["psutil_cpu_frequency"]
        self.assertEqual(cpu_freq["current"], 2.5)
        self.assertEqual(cpu_freq["min"], 1.0)
        self.assertEqual(cpu_freq["max"], 3.0)

        # Assertions for CPU stats
        cpu_stats = performance_analysis["performance_analysis"]["psutil_cpu_stats"]
        self.assertEqual(cpu_stats["context_switches"], 100)
        self.assertEqual(cpu_stats["interrupts"], 200)
        self.assertEqual(cpu_stats["soft_interrupts"], 300)
        self.assertEqual(cpu_stats["syscalls"], 400)

if __name__ == "__main__":
    unittest.main()