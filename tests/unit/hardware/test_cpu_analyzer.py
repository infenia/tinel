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

import time
import unittest
from unittest.mock import MagicMock, patch

import psutil
from tinel.hardware.cpu_analyzer import CPUAnalyzer
from tinel.hardware.models import CPUInfo
from tinel.interfaces import CommandResult


class TestCPUAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = CPUAnalyzer(self.mock_system_interface)

    def test_initialization(self):
        self.assertIsNotNone(self.analyzer.system)

    @patch("time.time", return_value=100)
    def test_cache_functionality(self, mock_time):
        self.analyzer._cache_ttl = 60
        self.mock_system_interface.read_file.return_value = "test_data"
        # First call, should compute
        result1 = self.analyzer._get_cached_or_compute(
            "test_key", lambda: self.mock_system_interface.read_file("/test")
        )
        self.mock_system_interface.read_file.assert_called_once_with("/test")
        self.assertEqual(result1, "test_data")
        # Second call, should be cached
        result2 = self.analyzer._get_cached_or_compute(
            "test_key", lambda: self.mock_system_interface.read_file("/test")
        )
        self.mock_system_interface.read_file.assert_called_once()
        self.assertEqual(result2, "test_data")

    @patch("time.time")
    def test_cache_expiration(self, mock_time):
        self.analyzer._cache_ttl = 60
        self.mock_system_interface.read_file.return_value = "first_call"
        mock_time.return_value = 100
        self.analyzer._get_cached_or_compute("test_key", lambda: self.mock_system_interface.read_file("/test"))
        self.mock_system_interface.read_file.assert_called_once_with("/test")
        mock_time.return_value = 170
        self.mock_system_interface.read_file.return_value = "second_call"
        result = self.analyzer._get_cached_or_compute("test_key", lambda: self.mock_system_interface.read_file("/test"))
        self.assertEqual(self.mock_system_interface.read_file.call_count, 2)
        self.assertEqual(result, "second_call")

    def test_get_cpu_info_structure(self):
        with patch.object(self.analyzer, "_compute_cpu_info", return_value=CPUInfo(product="Test CPU")) as mock_compute:
            info = self.analyzer.get_cpu_info()
            self.assertEqual(info.product, "Test CPU")
            mock_compute.assert_called_once()

    def test_parse_cpuinfo(self):
        content = "model name\t: Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz\n"
        content += "vendor_id\t: GenuineIntel\n"
        content += "cpu family\t: 6\n"
        content += "model\t\t: 158\n"
        content += "stepping\t: 13\n"
        info = self.analyzer._parse_cpuinfo(content)
        self.assertEqual(info["model_name"], "Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz")

    def test_parse_lscpu(self):
        output = "Architecture: x86_64\nCPU op-mode(s): 32-bit, 64-bit\nByte Order: Little Endian\nFlags: fpu vme de pse"
        info = self.analyzer._parse_lscpu(output)
        self.assertEqual(info["architecture"], "x86_64")

    def test_extract_cpu_flags(self):
        content = "flags\t\t: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov"
        flags = self.analyzer._extract_cpu_flags(content)
        self.assertIn("fpu", flags)

    def test_analyze_security_features(self):
        flags = ["nx", "smep", "smap", "cet_ss"]
        features = self.analyzer._analyze_security_features(flags)
        self.assertTrue(features["nx_bit"])

    def test_analyze_performance_features(self):
        flags = ["sse", "avx", "aes"]
        features = self.analyzer._analyze_performance_features(flags)
        self.assertTrue(features["avx"])

    def test_analyze_virtualization_features(self):
        flags = ["vmx", "ept"]
        features = self.analyzer._analyze_virtualization_features(flags)
        self.assertTrue(features["vmx"])

    def test_frequency_info_parsing(self):
        info = CPUInfo()
        self.mock_system_interface.read_file.return_value = "3600000"
        self.analyzer._get_frequency_info(info)
        self.assertEqual(info.performance_analysis["current_frequency_khz"], 3600000)

    def test_topology_info_parsing(self):
        info = CPUInfo()
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="16", stderr="", returncode=0)
        self.analyzer._get_topology_info(info)
        self.assertEqual(info.topology["logical_cpus"], 16)

    def test_cache_info_parsing(self):
        info = CPUInfo()
        def mock_read(path):
            if "size" in path: return "32K"
            if "type" in path: return "Data"
            if "level" in path: return "1"
            return "N/A"
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = mock_read
        self.analyzer._get_cache_info(info)
        self.assertIn("L1d", info.cache)

    def test_enhanced_cache_info_parsing(self):
        info = CPUInfo()
        def mock_read(path):
            if "index0/size" in path: return "32K"
            if "index0/type" in path: return "Data"
            if "index0/level" in path: return "1"
            if "index1/size" in path: return "32K"
            if "index1/type" in path: return "Instruction"
            if "index1/level" in path: return "1"
            if "index2/size" in path: return "256K"
            if "index2/type" in path: return "Unified"
            if "index2/level" in path: return "2"
            return "N/A"
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = mock_read
        self.analyzer._get_cache_info(info)
        self.assertIn("L1i", info.cache)

    def test_optimization_analysis(self):
        info = CPUInfo()
        mock_read_values = ["powersave"] + ["Vulnerable"] * 9
        self.mock_system_interface.read_file.side_effect = mock_read_values
        self.analyzer._analyze_cpu_optimization(info)
        self.assertEqual(len(info.optimization_recommendations), 2)

    def test_error_handling_missing_files(self):
        self.mock_system_interface.read_file.return_value = None
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="Error", returncode=1)
        info = self.analyzer.get_cpu_info()
        self.assertIsNone(info.product)

    @patch("time.time")
    def test_performance_with_caching(self, mock_time):
        def run_command_mock(command):
            if "nproc" in command:
                return CommandResult(success=True, stdout="16", stderr="", returncode=0)
            return CommandResult(success=True, stdout="Architecture: x86_64\nModel name: Test CPU", stderr="", returncode=0)
        def read_file_mock(path):
            if "scaling_cur_freq" in path: return "3600000"
            return "some_string"
        self.mock_system_interface.run_command.side_effect = run_command_mock
        self.mock_system_interface.read_file.side_effect = read_file_mock
        self.analyzer._cache_ttl = 10
        mock_time.return_value = 100
        self.analyzer.get_cpu_info()
        mock_time.return_value = 101
        start_time = time.perf_counter()
        self.analyzer.get_cpu_info()
        end_time = time.perf_counter()
        self.assertLess(end_time - start_time, 0.01)

    def test_parse_cpuinfo_edge_cases(self):
        self.assertEqual(self.analyzer._parse_cpuinfo(""), {})
        self.assertEqual(self.analyzer._parse_cpuinfo("random text"), {})
        info = self.analyzer._parse_cpuinfo("model name : X\nvendor_id : Y\ncpu family : 6\nmodel\t: 123\nstepping:4")
        self.assertEqual(info['model_name'], 'X')

    def test_parse_lscpu_edge_cases(self):
        self.assertEqual(self.analyzer._parse_lscpu(""), {})
        self.assertEqual(self.analyzer._parse_lscpu("random text"), {})

    def test_extract_cpu_flags_edge_cases(self):
        self.assertEqual(self.analyzer._extract_cpu_flags("no flags here"), [])

    def test_analyze_security_features_empty(self):
        self.assertFalse(any(self.analyzer._analyze_security_features([]).values()))

    def test_analyze_performance_features_empty(self):
        self.assertFalse(any(self.analyzer._analyze_performance_features([]).values()))

    def test_analyze_virtualization_features_empty(self):
        self.assertFalse(any(self.analyzer._analyze_virtualization_features([]).values()))

    def test_get_cache_info_missing_files(self):
        self.mock_system_interface.file_exists.return_value = False
        self.assertEqual(self.analyzer._compute_cache_info(), {})

    def test_get_cache_info_io_error(self):
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = IOError("cannot read")
        self.assertEqual(self.analyzer._compute_cache_info(), {})

    def test_get_cache_info_parsing_incomplete(self):
        def mock_read(path):
            if "size" in path: return ""
            return "valid"
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = mock_read
        self.assertEqual(self.analyzer._compute_cache_info(), {})

    def test_get_topology_info_missing_files(self):
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        self.assertEqual(self.analyzer._compute_topology_info(), {})

    @patch('psutil.cpu_freq', side_effect=Exception("Generic psutil error"))
    def test_analyze_cpu_performance_generic_psutil_exception(self, mock_cpu_freq):
        result = self.analyzer._analyze_cpu_performance({})
        self.assertIn("psutil_cpu_frequency_error", result['performance_analysis'])

    @patch('psutil.cpu_freq', side_effect=PermissionError("Permission denied"))
    def test_analyze_cpu_performance_psutil_permission_error(self, mock_cpu_freq):
        result = self.analyzer._analyze_cpu_performance({})
        self.assertEqual(result['performance_analysis']['psutil_cpu_frequency_error'], "Permission denied")

    @patch('psutil.cpu_freq', return_value=None)
    def test_analyze_cpu_performance_psutil_returns_none(self, mock_cpu_freq):
        result = self.analyzer._analyze_cpu_performance({})
        self.assertNotIn("psutil_cpu_frequency", result['performance_analysis'])

    @patch('psutil.cpu_stats', side_effect=NotImplementedError("Stats not supported"))
    def test_analyze_cpu_performance_psutil_error(self, mock_cpu_stats):
        result = self.analyzer._analyze_cpu_performance({})
        self.assertIn('psutil_cpu_stats_error', result['performance_analysis'])

    @patch('psutil.cpu_stats', side_effect=Exception("Generic psutil error"))
    def test_analyze_cpu_performance_generic_psutil_stats_exception(self, mock_cpu_stats):
        result = self.analyzer._analyze_cpu_performance({})
        self.assertIn("psutil_cpu_stats_error", result['performance_analysis'])

    @patch('psutil.cpu_stats', side_effect=PermissionError("Permission denied"))
    def test_analyze_cpu_performance_psutil_stats_permission_error(self, mock_cpu_stats):
        result = self.analyzer._analyze_cpu_performance({})
        self.assertEqual(result['performance_analysis']['psutil_cpu_stats_error'], "Permission denied")

    def test_get_cpu_vulnerabilities_all_missing(self):
        self.mock_system_interface.read_file.return_value = None
        self.assertEqual(self.analyzer._get_cpu_vulnerabilities(), {})

    def test_process_basic_cpu_info_lscpu_fails(self):
        info = CPUInfo()
        self.analyzer._process_basic_cpu_info(info, "model name: Test CPU", CommandResult(success=False, stdout="", stderr="", returncode=1))
        self.assertEqual(info.product, "Test CPU")

    def test_process_basic_cpu_info_no_version_match(self):
        info = CPUInfo()
        lscpu_result = CommandResult(success=True, stdout="Model name: Another CPU", stderr="", returncode=0)
        self.analyzer._process_basic_cpu_info(info, "", lscpu_result)
        self.assertEqual(info.version, "Another CPU")

    def test_process_basic_cpu_info_no_width_match(self):
        info = CPUInfo()
        lscpu_output = "Model name: Another CPU"
        lscpu_result = CommandResult(success=True, stdout=lscpu_output, stderr="", returncode=0)
        self.analyzer._process_basic_cpu_info(info, "", lscpu_result)
        self.assertIsNone(info.width)

    def test_optimization_analysis_not_powersave(self):
        info = CPUInfo()
        mock_read_values = ["performance"] + ["Not affected"] * 9
        self.mock_system_interface.read_file.side_effect = mock_read_values
        self.analyzer._analyze_cpu_optimization(info)
        self.assertEqual(len(info.optimization_recommendations), 0)

    def test_process_basic_cpu_info_no_cpuinfo(self):
        info = CPUInfo()
        lscpu_result = CommandResult(success=True, stdout="Architecture: arm64", stderr="", returncode=0)
        self.analyzer._process_basic_cpu_info(info, None, lscpu_result)
        self.assertIsNone(info.product)
        self.assertEqual(info.architecture, "arm64")

    def test_process_basic_cpu_info_no_width_in_lscpu(self):
        info = CPUInfo()
        lscpu_result = CommandResult(success=True, stdout="Model name: Another CPU", stderr="", returncode=0)
        self.analyzer._process_basic_cpu_info(info, "model name: Another CPU", lscpu_result)
        self.assertIsNone(info.width)

    def test_optimization_analysis_no_powersave_no_vulns(self):
        info = CPUInfo()
        mock_read_values = ["performance"] + ["Not affected"] * 9
        self.mock_system_interface.read_file.side_effect = mock_read_values
        with patch.object(self.analyzer, '_get_cpu_vulnerabilities', return_value={}):
            self.analyzer._analyze_cpu_optimization(info)
            self.assertEqual(len(info.optimization_recommendations), 0)

if __name__ == "__main__":
    unittest.main()