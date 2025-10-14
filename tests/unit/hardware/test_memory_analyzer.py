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

from tinel.hardware.memory_analyzer import MemoryAnalyzer, analyze_memory_performance
from tinel.interfaces import CommandResult


class TestMemoryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.system_interface = MagicMock()
        self.analyzer = MemoryAnalyzer(system_interface=self.system_interface)

    @patch("psutil.virtual_memory")
    @patch("psutil.swap_memory")
    def test_get_memory_info_success(self, mock_swap_memory, mock_virtual_memory):
        # Mock psutil calls
        mock_virtual_memory.return_value = MagicMock(
            total=8589934592, available=4294967296, used=4294967296, percent=50.0
        )
        mock_swap_memory.return_value = MagicMock(
            total=2147483648, used=1073741824, free=1073741824, percent=50.0
        )

        # Mock dmidecode command
        dmidecode_output = """
Handle 0x003E, DMI type 17, 40 bytes
Memory Device
	Array Handle: 0x003D
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 8192 MB
	Form Factor: SODIMM
	Set: None
	Locator: ChannelA-DIMM0
	Bank Locator: BANK 0
	Type: DDR4
	Type Detail: Synchronous
	Speed: 2400 MT/s
	Manufacturer: Hynix
	Serial Number: 12345678
	Asset Tag: 98765432
	Part Number: HMA81GS6AFR8N-UH
	Rank: 1
	Configured Memory Speed: 2400 MT/s
	Minimum Voltage: 1.2 V
	Maximum Voltage: 1.2 V
	Configured Voltage: 1.2 V
"""
        self.system_interface.run_command.return_value = CommandResult(
            success=True, stdout=dmidecode_output, stderr="", returncode=0
        )

        # Run the method
        info = self.analyzer.get_memory_info()

        # Assertions for psutil data
        self.assertEqual(info["total_memory_bytes"], 8589934592)
        self.assertEqual(info["memory_usage_percent"], 50.0)
        self.assertEqual(info["total_swap_bytes"], 2147483648)
        self.assertEqual(info["swap_usage_percent"], 50.0)

        # Assertions for dmidecode data
        self.assertIn("memory_devices", info)
        self.assertEqual(len(info["memory_devices"]), 1)
        device = info["memory_devices"][0]
        self.assertEqual(device["size"], "8192 MB")
        self.assertEqual(device["speed"], "2400 MT/s")
        self.assertEqual(device["manufacturer"], "Hynix")

        # Assertions for performance analysis
        self.assertIn("performance_analysis", info)
        self.assertEqual(info["performance_analysis"]["effective_speed_mhz"], 2400)

    @patch("psutil.virtual_memory")
    @patch("psutil.swap_memory")
    def test_get_memory_info_dmidecode_fail(self, mock_swap_memory, mock_virtual_memory):
        # Mock psutil calls
        mock_virtual_memory.return_value = MagicMock(
            total=8589934592, available=4294967296, used=4294967296, percent=50.0
        )
        mock_swap_memory.return_value = MagicMock(
            total=2147483648, used=1073741824, free=1073741824, percent=50.0
        )

        # Mock dmidecode command failure
        self.system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="dmidecode error", returncode=1, error="dmidecode error"
        )

        # Run the method
        info = self.analyzer.get_memory_info()

        # Assertions for psutil data
        self.assertEqual(info["total_memory_bytes"], 8589934592)

        # Assertions for dmidecode failure
        self.assertIn("dmidecode_error", info)
        self.assertNotIn("memory_devices", info)
        self.assertNotIn("performance_analysis", info)

    def test_analyze_memory_performance(self):
        # Test with multiple devices
        info = {
            "memory_devices": [
                {"speed": "2400 MT/s"},
                {"speed": "2666 MT/s"},
            ]
        }
        analysis = analyze_memory_performance(info)
        self.assertEqual(analysis["effective_speed_mhz"], 2533)

        # Test with no devices
        info = {"memory_devices": []}
        analysis = analyze_memory_performance(info)
        self.assertEqual(analysis, {})

        # Test with devices but no speed
        info = {"memory_devices": [{"size": "8 GB"}]}
        analysis = analyze_memory_performance(info)
        self.assertEqual(analysis["effective_speed_mhz"], 0)

        # Test with malformed speed
        info = {"memory_devices": [{"speed": "Unknown"}]}
        analysis = analyze_memory_performance(info)
        self.assertEqual(analysis["effective_speed_mhz"], 0)

    @patch("psutil.virtual_memory", side_effect=Exception("psutil_vm_error"))
    @patch("psutil.swap_memory", side_effect=Exception("psutil_swap_error"))
    def test_psutil_exceptions(self, mock_swap_memory, mock_virtual_memory):
        self.system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="", returncode=1
        )
        info = self.analyzer.get_memory_info()
        self.assertIn("psutil_vm_error", info["psutil_error"])
        self.assertIn("psutil_swap_error", info["psutil_error"])

    def test_dmidecode_empty_stdout(self):
        self.system_interface.run_command.return_value = CommandResult(
            success=True, stdout="", stderr="", returncode=0
        )
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = self.analyzer.get_memory_info()
        self.assertNotIn("dmidecode_error", info)
        self.assertNotIn("memory_devices", info)

    @patch("tinel.hardware.memory_analyzer.MemoryAnalyzer._parse_dmidecode_output", side_effect=Exception("parse_error"))
    def test_dmidecode_parse_error(self, mock_parse):
        self.system_interface.run_command.return_value = CommandResult(
            success=True, stdout="valid output", stderr="", returncode=0
        )
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = self.analyzer.get_memory_info()
        self.assertEqual(info["dmidecode_parse_error"], "parse_error")

    def test_analyze_memory_performance_edge_cases(self):
        # Test with a None device
        info = {"memory_devices": [None, {"speed": "2400 MT/s"}]}
        analysis = analyze_memory_performance(info)
        self.assertEqual(analysis["effective_speed_mhz"], 2400)

        # Test with TypeError
        info = {"memory_devices": [{"speed": 1234}]}
        analysis = analyze_memory_performance(info)
        self.assertEqual(analysis["effective_speed_mhz"], 0)

    def test_parse_dmidecode_empty_and_unknown_values(self):
        dmidecode_output = """
Handle 0x003E, DMI type 17, 40 bytes
Memory Device
    Size: 8192 MB
    Manufacturer:
    Part Number: Not Specified
    Key: Value
    Another: Unknown
"""
        result = self.analyzer._parse_dmidecode_output(dmidecode_output)
        self.assertEqual(len(result["memory_devices"]), 1)
        device = result["memory_devices"][0]
        self.assertNotIn("manufacturer", device.raw_details)
        self.assertNotIn("part_number", device.raw_details)
        self.assertNotIn("another", device.raw_details)
        self.assertEqual(device.raw_details["key"], "Value")

    def test_dmidecode_fail_no_error_string(self):
        self.system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="some error", returncode=1, error=None
        )
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = self.analyzer.get_memory_info()
        self.assertIn("dmidecode_error", info)
        self.assertEqual(info["dmidecode_error"], "Failed to run dmidecode.")

    def test_dmidecode_not_found(self):
        self.system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="No such file or directory", returncode=1, error=None
        )
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = self.analyzer.get_memory_info()
        self.assertIn("dmidecode_error", info)
        self.assertEqual(info["dmidecode_error"], "dmidecode not found, using psutil fallback.")

    def test_dmidecode_not_found_error_message(self):
        self.system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="", returncode=1, error="command not found"
        )
        with patch("psutil.virtual_memory"), patch("psutil.swap_memory"):
            info = self.analyzer.get_memory_info()
        self.assertIn("dmidecode_error", info)
        self.assertEqual(info["dmidecode_error"], "dmidecode not found, using psutil fallback.")

if __name__ == "__main__":
    unittest.main()