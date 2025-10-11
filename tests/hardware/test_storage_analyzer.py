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

import json
import unittest
from unittest.mock import MagicMock

from tinel.hardware.storage_analyzer import StorageAnalyzer
from tinel.interfaces import CommandResult

MOCK_LSBLK_OUTPUT = {
    "blockdevices": [
        {
            "name": "sda",
            "size": "238.5G",
            "type": "disk",
            "mountpoint": None,
            "fstype": None,
            "model": "SAMSUNG MZ7LF256HCHP-000L1",
            "children": [
                {
                    "name": "sda1",
                    "size": "512M",
                    "type": "part",
                    "mountpoint": "/boot/efi",
                    "fstype": "vfat",
                    "model": None,
                },
                {
                    "name": "sda2",
                    "size": "238G",
                    "type": "part",
                    "mountpoint": "/",
                    "fstype": "ext4",
                    "model": None,
                },
            ],
        }
    ]
}

MOCK_DF_OUTPUT = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2       238G   24G  202G  11% /
/dev/sda1       511M  4.0K  511M   1% /boot/efi
"""

MOCK_SMARTCTL_OUTPUT_PASSED = """
smartctl 7.2 2020-12-30 r5155 [x86_64-linux-5.15.0-41-generic] (local build)
Copyright (C) 2002-20, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED
"""

MOCK_SMARTCTL_OUTPUT_FAILED = """
smartctl 7.2 2020-12-30 r5155 [x86_64-linux-5.15.0-41-generic] (local build)
Copyright (C) 2002-20, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: FAILED
"""


class TestStorageAnalyzer(unittest.TestCase):
    def test_get_storage_info_success(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(
                success=True,
                stdout=json.dumps(MOCK_LSBLK_OUTPUT),
                stderr="",
                returncode=0,
            ),
            CommandResult(success=True, stdout=MOCK_DF_OUTPUT, stderr="", returncode=0),
            CommandResult(
                success=True,
                stdout=MOCK_SMARTCTL_OUTPUT_PASSED,
                stderr="",
                returncode=0,
            ),
        ]

        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        storage_info = analyzer.get_storage_info()

        self.assertIn("block_devices", storage_info)
        self.assertIn("disk_usage", storage_info)
        self.assertEqual(len(storage_info["block_devices"]), 1)
        self.assertEqual(storage_info["block_devices"][0]["name"], "sda")
        self.assertIn("health", storage_info["block_devices"][0])
        self.assertEqual(
            storage_info["block_devices"][0]["health"]["health_status"], "PASSED"
        )
        self.assertEqual(len(storage_info["disk_usage"]), 2)
        self.assertEqual(storage_info["disk_usage"][0]["filesystem"], "/dev/sda2")

    def test_get_storage_info_lsblk_fail(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="error", returncode=1
        )
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        storage_info = analyzer.get_storage_info()
        self.assertEqual(storage_info, {})

    def test_get_storage_info_df_fail(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(
                success=True,
                stdout=json.dumps(MOCK_LSBLK_OUTPUT),
                stderr="",
                returncode=0,
            ),
            CommandResult(success=False, stdout="", stderr="error", returncode=1),
            CommandResult(
                success=True,
                stdout=MOCK_SMARTCTL_OUTPUT_PASSED,
                stderr="",
                returncode=0,
            ),
        ]
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        storage_info = analyzer.get_storage_info()
        self.assertIn("block_devices", storage_info)
        self.assertNotIn("disk_usage", storage_info)

    def test_get_storage_info_smartctl_fail(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(
                success=True,
                stdout=json.dumps(MOCK_LSBLK_OUTPUT),
                stderr="",
                returncode=0,
            ),
            CommandResult(success=True, stdout=MOCK_DF_OUTPUT, stderr="", returncode=0),
            CommandResult(success=False, stdout="", stderr="error", returncode=1),
        ]

        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        storage_info = analyzer.get_storage_info()

        self.assertIn("block_devices", storage_info)
        self.assertNotIn("health", storage_info["block_devices"][0])

    def test_parse_df_output(self):
        analyzer = StorageAnalyzer()
        parsed_output = analyzer._parse_df_output(MOCK_DF_OUTPUT)
        self.assertEqual(len(parsed_output), 2)
        self.assertEqual(parsed_output[0]["filesystem"], "/dev/sda2")
        self.assertEqual(parsed_output[0]["size"], "238G")
        self.assertEqual(parsed_output[0]["mounted_on"], "/")
        self.assertEqual(parsed_output[1]["filesystem"], "/dev/sda1")
        self.assertEqual(parsed_output[1]["mounted_on"], "/boot/efi")

    def test_parse_smartctl_output_passed(self):
        analyzer = StorageAnalyzer()
        parsed_output = analyzer._parse_smartctl_output(MOCK_SMARTCTL_OUTPUT_PASSED)
        self.assertEqual(parsed_output["health_status"], "PASSED")

    def test_parse_smartctl_output_failed(self):
        analyzer = StorageAnalyzer()
        parsed_output = analyzer._parse_smartctl_output(MOCK_SMARTCTL_OUTPUT_FAILED)
        self.assertEqual(parsed_output["health_status"], "FAILED")

    def test_parse_smartctl_output_unknown(self):
        analyzer = StorageAnalyzer()
        parsed_output = analyzer._parse_smartctl_output("some other output")
        self.assertEqual(parsed_output["health_status"], "UNKNOWN")

    def test_lsblk_json_error(self):
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="{invalid json}", stderr="", returncode=0
        )
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        lsblk_info = analyzer._get_lsblk_info()
        self.assertIsNone(lsblk_info)

    def test_lsblk_no_blockdevices_key(self):
        """Test _get_lsblk_info when JSON has no 'blockdevices' key."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout='{"other_key": "value"}', stderr="", returncode=0
        )
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        lsblk_info = analyzer._get_lsblk_info()
        self.assertIsNone(lsblk_info)

    def test_get_info_with_non_disk_device(self):
        """Test that devices not of type 'disk' are skipped for health checks."""
        mock_lsblk_output_no_disk = {
            "blockdevices": [
                {
                    "name": "loop0",
                    "size": "100M",
                    "type": "loop",
                    "mountpoint": "/snap/test/1",
                }
            ]
        }
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(
                success=True,
                stdout=json.dumps(mock_lsblk_output_no_disk),
                stderr="",
                returncode=0,
            ),
            CommandResult(success=True, stdout=MOCK_DF_OUTPUT, stderr="", returncode=0),
        ]
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        storage_info = analyzer.get_storage_info()
        self.assertIn("block_devices", storage_info)
        # smartctl should not have been called
        self.assertEqual(mock_system_interface.run_command.call_count, 2)
        self.assertNotIn("health", storage_info["block_devices"][0])

    def test_get_info_with_disk_no_name(self):
        """Test that disks with no name are handled gracefully."""
        mock_lsblk_output_no_name = {"blockdevices": [{"size": "10G", "type": "disk"}]}
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.side_effect = [
            CommandResult(
                success=True,
                stdout=json.dumps(mock_lsblk_output_no_name),
                stderr="",
                returncode=0,
            ),
            CommandResult(success=True, stdout=MOCK_DF_OUTPUT, stderr="", returncode=0),
        ]
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        storage_info = analyzer.get_storage_info()
        self.assertIn("block_devices", storage_info)
        # smartctl should not have been called
        self.assertEqual(mock_system_interface.run_command.call_count, 2)
        self.assertNotIn("health", storage_info["block_devices"][0])

    def test_get_df_info_empty_stdout(self):
        """Test _get_df_info with successful command but empty output."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="", stderr="", returncode=0
        )
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        df_info = analyzer._get_df_info()
        self.assertIsNone(df_info)

    def test_get_smartctl_info_empty_stdout(self):
        """Test _get_smartctl_info with successful command but empty output."""
        mock_system_interface = MagicMock()
        mock_system_interface.run_command.return_value = CommandResult(
            success=True, stdout="", stderr="", returncode=0
        )
        analyzer = StorageAnalyzer(system_interface=mock_system_interface)
        health_info = analyzer._get_smartctl_info("/dev/sda")
        self.assertIsNone(health_info)

    def test_parse_smartctl_output_empty_status(self):
        """Test parsing smartctl output with an empty status."""
        output = "SMART overall-health self-assessment test result: "
        analyzer = StorageAnalyzer()
        parsed_output = analyzer._parse_smartctl_output(output)
        self.assertEqual(parsed_output["health_status"], "UNKNOWN")

    def test_parse_df_output_malformed_line(self):
        """Test that malformed lines in df output are skipped."""
        malformed_df_output = (
            "Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda2       238G  24G  202G  11% /\n"
            "malformed line\n"
            "/dev/sda1       511M  4.0K  511M   1% /boot/efi\n"
        )
        analyzer = StorageAnalyzer()
        parsed_output = analyzer._parse_df_output(malformed_df_output)
        self.assertEqual(len(parsed_output), 2)
        self.assertEqual(parsed_output[0]["filesystem"], "/dev/sda2")
        self.assertEqual(parsed_output[1]["filesystem"], "/dev/sda1")


if __name__ == "__main__":
    unittest.main()
