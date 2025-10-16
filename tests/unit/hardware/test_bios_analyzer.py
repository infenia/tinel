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
from tinel.hardware.bios_analyzer import BIOSAnalyzer
from tinel.hardware.models import BIOSInfo
from tinel.interfaces import CommandResult

class TestBIOSAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = BIOSAnalyzer(self.mock_system_interface)

    def test_get_bios_info_success(self):
        # Mock the DMI path and file reads
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = self._mock_read_file
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=True,
            stdout="""
BIOS characteristics:
\tBIOS is upgradeable
\tBIOS shadowing is allowed
ROM Size: 16 MB
""",
            stderr="",
            returncode=0,
        )

        # Call the method under test
        bios_info = self.analyzer.get_bios_info()

        # Assert the results
        self.assertEqual(bios_info.vendor, "Test BIOS Vendor")
        self.assertEqual(bios_info.version, "2.0")
        self.assertEqual(bios_info.date, "2025-01-01")
        self.assertEqual(bios_info.size, "16 MB")
        self.assertIn("BIOS is upgradeable", bios_info.capabilities)

    def test_get_bios_info_dmi_path_not_found(self):
        # Mock the DMI path to not exist
        self.mock_system_interface.file_exists.return_value = False
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="not found", returncode=1
        )

        # Call the method under test
        bios_info = self.analyzer.get_bios_info()

        # Assert that the info is empty
        self.assertEqual(bios_info, BIOSInfo())

    def test_get_bios_info_file_not_found(self):
        # Mock the DMI path to exist, but files to be missing
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = FileNotFoundError
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="not found", returncode=1
        )

        # Call the method under test
        bios_info = self.analyzer.get_bios_info()

        # Assert that the info is filled with None
        self.assertIsNone(bios_info.vendor)
        self.assertIsNone(bios_info.version)
        self.assertIsNone(bios_info.date)

    def test_get_bios_info_exception_on_check(self):
        # Mock file_exists to raise an exception
        self.mock_system_interface.file_exists.side_effect = Exception("Test Exception")
        self.mock_system_interface.run_command.return_value = CommandResult(success=False, stdout="", stderr="", returncode=1)
        bios_info = self.analyzer.get_bios_info()
        self.assertEqual(bios_info, BIOSInfo())

    def test_dmidecode_no_size(self):
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = self._mock_read_file
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="BIOS characteristics:\n\tTest capability\n", stderr="", returncode=0
        )
        bios_info = self.analyzer.get_bios_info()
        self.assertIsNone(bios_info.size)
        self.assertIn("Test capability", bios_info.capabilities)

    def test_dmidecode_no_capabilities(self):
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = self._mock_read_file
        self.mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="ROM Size: 8 MB", stderr="", returncode=0
        )
        bios_info = self.analyzer.get_bios_info()
        self.assertEqual(bios_info.size, "8 MB")
        self.assertEqual(bios_info.capabilities, {})

    def test_read_dmi_file_whitespace(self):
        self.mock_system_interface.read_file.return_value = "   "
        result = self.analyzer._read_dmi_file("any")
        self.assertIsNone(result)

    def test_read_dmi_file_empty(self):
        self.mock_system_interface.read_file.return_value = ""
        result = self.analyzer._read_dmi_file("any")
        self.assertIsNone(result)

    def test_read_dmi_file_exception(self):
        self.mock_system_interface.read_file.side_effect = Exception("generic error")
        result = self.analyzer._read_dmi_file("any")
        self.assertIsNone(result)

    def _mock_read_file(self, path):
        if path.endswith("bios_vendor"):
            return "Test BIOS Vendor"
        elif path.endswith("bios_version"):
            return "2.0"
        elif path.endswith("bios_date"):
            return "2025-01-01"
        return None

if __name__ == "__main__":
    unittest.main()