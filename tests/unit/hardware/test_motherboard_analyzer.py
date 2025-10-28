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
from tinel.hardware.motherboard_analyzer import MotherboardAnalyzer
from tinel.hardware.models import MotherboardInfo

class TestMotherboardAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_system_interface = MagicMock()
        self.analyzer = MotherboardAnalyzer(self.mock_system_interface)

    def test_get_motherboard_info_success(self):
        # Mock the DMI path and file reads
        self.mock_system_interface.file_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = self._mock_read_file

        # Call the method under test
        motherboard_info = self.analyzer.get_motherboard_info()

        # Assert the results
        self.assertEqual(motherboard_info.product, "Test Board")
        self.assertEqual(motherboard_info.vendor, "Test Board Vendor")
        self.assertEqual(motherboard_info.version, "3.0")
        self.assertEqual(motherboard_info.serial, "67890")
        self.assertEqual(motherboard_info.asset_tag, "Asset123")
        self.assertEqual(motherboard_info.physid, "0")

    def test_get_motherboard_info_dmi_path_not_found(self):
        # Mock the DMI path to not exist
        self.mock_system_interface.file_exists.return_value = False

        # Call the method under test
        motherboard_info = self.analyzer.get_motherboard_info()

        # Assert that the info is empty except for the physid
        self.assertEqual(motherboard_info.physid, "0")
        self.assertIsNone(motherboard_info.product)

    def test_get_motherboard_info_file_not_found(self):
        # Mock the DMI path to exist, but files to be missing
        self.mock_system_interface.path_exists.return_value = True
        self.mock_system_interface.read_file.side_effect = FileNotFoundError

        # Call the method under test
        motherboard_info = self.analyzer.get_motherboard_info()

        # Assert that the info is filled with None
        self.assertIsNone(motherboard_info.product)
        self.assertIsNone(motherboard_info.vendor)
        self.assertIsNone(motherboard_info.version)
        self.assertIsNone(motherboard_info.serial)
        self.assertIsNone(motherboard_info.asset_tag)

    def _mock_read_file(self, path):
        if path.endswith("board_name"):
            return "Test Board"
        elif path.endswith("board_vendor"):
            return "Test Board Vendor"
        elif path.endswith("board_version"):
            return "3.0"
        elif path.endswith("board_serial"):
            return "67890"
        elif path.endswith("board_asset_tag"):
            return "Asset123"
        return None

if __name__ == "__main__":
    unittest.main()