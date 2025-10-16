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
from unittest.mock import MagicMock
from tinel.hardware.system_analyzer import SystemAnalyzer
from tinel.hardware.models import SystemInfo
from tinel.interfaces import CommandResult

class TestSystemAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = SystemAnalyzer(self.mock_system_interface)

    def test_get_system_info_success(self):
        # Mock the DMI path and file reads
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = self._mock_read_file
        self.mock_system_interface.run_command.side_effect = self._mock_run_command

        # Call the method under test
        system_info = self.analyzer.get_system_info()

        # Assert the results
        self.assertEqual(system_info.product, "Test Product")
        self.assertEqual(system_info.vendor, "Test Vendor")
        self.assertEqual(system_info.version, "1.0")
        self.assertEqual(system_info.serial, "12345")
        self.assertEqual(system_info.uuid, "some-uuid")
        self.assertEqual(system_info.sku_number, "SKU123")
        self.assertEqual(system_info.family, "Test Family")
        self.assertEqual(system_info.width, 64)
        self.assertIn("smp", system_info.capabilities)

    def test_get_system_info_32bit(self):
        # Mock lscpu to return 32-bit architecture
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = self._mock_read_file
        self.mock_system_interface.run_command.side_effect = self._mock_run_command_32bit

        system_info = self.analyzer.get_system_info()
        self.assertEqual(system_info.width, 32)
        self.assertNotIn("smp", system_info.capabilities)

    def test_get_system_info_exception_on_check(self):
        # Mock file_exists to raise an exception
        self.mock_system_interface.file_exists.side_effect = Exception("Test Exception")

        system_info = self.analyzer.get_system_info()

        # Should return an empty SystemInfo object
        self.assertEqual(system_info, SystemInfo())

    def test_get_system_info_dmi_file_whitespace(self):
        self.mock_system_interface.file_exists.return_value = True
        def _mock_read_file(path):
            if "product_name" in path:
                return "   "
            return "good value"
        self.mock_system_interface.read_file.side_effect = _mock_read_file

        # Make sure hostname command is successful to cover the fallback
        self.mock_system_interface.run_command.return_value = CommandResult(success=True, stdout="test-hostname", stderr="", returncode=0)

        system_info = self.analyzer.get_system_info()
        self.assertEqual(system_info.product, "test-hostname")
        self.assertEqual(system_info.vendor, "good value")

    def test_read_dmi_file_exception(self):
        self.mock_system_interface.read_file.side_effect = Exception("generic error")
        result = self.analyzer._read_dmi_file("any_file")
        self.assertIsNone(result)

    def test_read_dmi_file_returns_none(self):
        self.mock_system_interface.read_file.return_value = None
        result = self.analyzer._read_dmi_file("any_file")
        self.assertIsNone(result)

    def test_get_system_info_dmi_path_not_found(self):
        # Mock the DMI path to not exist
        self.mock_system_interface.file_exists.return_value = False
        self.mock_system_interface.run_command.side_effect = self._mock_run_command

        # Call the method under test
        system_info = self.analyzer.get_system_info()

        # Assert that the info is still populated from other sources
        self.assertEqual(system_info.product, "test-hostname")
        self.assertEqual(system_info.width, 64)

    def test_get_system_info_file_not_found(self):
        # Mock the DMI path to exist, but files to be missing
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = FileNotFoundError
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="not found", returncode=1
        )

        # Call the method under test
        system_info = self.analyzer.get_system_info()

        # Assert that the info is filled with None
        self.assertIsNone(system_info.product)
        self.assertIsNone(system_info.vendor)
        self.assertIsNone(system_info.version)
        self.assertIsNone(system_info.serial)
        self.assertIsNone(system_info.uuid)
        self.assertIsNone(system_info.sku_number)
        self.assertIsNone(system_info.family)
        self.assertIsNone(system_info.width)
        self.assertEqual(system_info.capabilities, {})

    def _mock_read_file(self, path):
        if path.endswith("product_name"):
            return "Test Product"
        elif path.endswith("sys_vendor"):
            return "Test Vendor"
        elif path.endswith("product_version"):
            return "1.0"
        elif path.endswith("product_serial"):
            return "12345"
        elif path.endswith("product_uuid"):
            return "some-uuid"
        elif path.endswith("product_sku"):
            return "SKU123"
        elif path.endswith("product_family"):
            return "Test Family"
        return None

    def _mock_run_command(self, command):
        if command == ["hostname"]:
            return CommandResult(success=True, stdout="test-hostname", stderr="", returncode=0)
        elif command == ["lscpu"]:
            return CommandResult(
                success=True,
                stdout="CPU op-mode(s): 32-bit, 64-bit\nsmp",
                stderr="",
                returncode=0,
            )
        return CommandResult(success=False, stdout="", stderr="Command not found", returncode=127)

    def _mock_run_command_32bit(self, command):
        if command == ["hostname"]:
            return CommandResult(success=True, stdout="test-hostname", stderr="", returncode=0)
        elif command == ["lscpu"]:
            return CommandResult(
                success=True,
                stdout="CPU op-mode(s): 32-bit",
                stderr="",
                returncode=0,
            )
        return CommandResult(success=False, stdout="", stderr="Command not found", returncode=127)

if __name__ == "__main__":
    unittest.main()