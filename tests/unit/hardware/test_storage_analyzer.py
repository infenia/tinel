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
from unittest.mock import MagicMock, patch

import pytest
import psutil

from tinel.hardware.storage_analyzer import StorageAnalyzer
from tinel.interfaces import CommandResult

# --- Mock Data ---
MOCK_LSBLK_OUTPUT = {
    "blockdevices": [
        {
            "name": "sda",
            "type": "disk",
            "model": "SAMSUNG-SSD",
            "children": [
                {"name": "sda1", "type": "part", "mountpoint": "/"},
                {"name": "sda2", "type": "part", "mountpoint": "/home"},
            ],
        },
        {"name": "sdb", "type": "disk", "model": "SEAGATE-HDD"},
    ]
}
MOCK_DF_OUTPUT = "Filesystem Size Used Avail Use% Mounted on\n/dev/sda1 10G 5G 5G 50% /\n"
MOCK_DF_I_OUTPUT = "Filesystem Inodes IUsed IFree IUse% Mounted on\n/dev/sda1 1000 500 500 50% /\n"
MOCK_SMARTCTL_H_OUTPUT = "SMART overall-health self-assessment test result: PASSED\n"
MOCK_SMARTCTL_I_OUTPUT = "Device Model: MOCK-MODEL-123\n"


@pytest.fixture
def mock_system_interface():
    """Fixture for a mocked SystemInterface."""
    return MagicMock()


@pytest.fixture
def analyzer(mock_system_interface):
    """Fixture for StorageAnalyzer with a mocked system interface."""
    return StorageAnalyzer(system_interface=mock_system_interface)


def test_get_storage_info_full_success(analyzer, mock_system_interface):
    """Test get_storage_info with all commands succeeding."""
    mock_system_interface.run_command.side_effect = [
        CommandResult(True, json.dumps(MOCK_LSBLK_OUTPUT), "", 0),
        CommandResult(True, MOCK_DF_OUTPUT, "", 0),
        CommandResult(True, MOCK_DF_I_OUTPUT, "", 0),
        CommandResult(True, MOCK_SMARTCTL_H_OUTPUT, "", 0),
        CommandResult(True, MOCK_SMARTCTL_I_OUTPUT, "", 0),
        CommandResult(True, MOCK_SMARTCTL_H_OUTPUT, "", 0),
        CommandResult(True, MOCK_SMARTCTL_I_OUTPUT, "", 0),
    ]
    info = analyzer.get_storage_info()
    assert "block_devices" in info
    assert "disk_usage" in info
    assert "inode_usage" in info
    assert "health" in info["block_devices"][0]


@patch("psutil.disk_partitions")
def test_lsblk_fallback_psutil_success(mock_disk_partitions, analyzer, mock_system_interface):
    """Test lsblk fallback to psutil successfully."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    mock_disk_partitions.return_value = [psutil._common.sdiskpart("/dev/sda1", "/", "ext4", "rw")]
    assert analyzer._get_lsblk_info_with_fallback() is not None


@patch("psutil.disk_partitions", side_effect=Exception("psutil error"))
def test_lsblk_fallback_psutil_fail(mock_disk_partitions, analyzer, mock_system_interface):
    """Test lsblk fallback to psutil when psutil fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_lsblk_info_with_fallback() is None


@patch("psutil.disk_partitions")
@patch("psutil.disk_usage")
def test_df_fallback_psutil_success(mock_disk_usage, mock_disk_partitions, analyzer, mock_system_interface):
    """Test df fallback to psutil successfully."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    mock_disk_partitions.return_value = [psutil._common.sdiskpart("/dev/sda1", "/", "ext4", "rw")]
    mock_disk_usage.return_value = psutil._common.sdiskusage(10**10, 5**10, 5**10, 50.0)
    assert analyzer._get_df_info_with_fallback() is not None


@patch("psutil.disk_partitions", side_effect=Exception("psutil error"))
def test_df_fallback_psutil_fail(mock_disk_partitions, analyzer, mock_system_interface):
    """Test df fallback to psutil when psutil fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_df_info_with_fallback() is None


@patch("psutil.disk_partitions", side_effect=Exception("psutil error"))
def test_get_storage_info_all_fail(mock_disk_partitions, analyzer, mock_system_interface):
    """Test get_storage_info when all underlying commands fail."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer.get_storage_info() == {}


def test_analyze_storage_health_no_block_devices(analyzer):
    """Test analyze_storage_health when there are no block devices."""
    info_missing_key = {"other_key": "value"}
    result_missing_key = analyzer.analyze_storage_health(info_missing_key)
    assert result_missing_key == info_missing_key

    info_empty_list = {"block_devices": []}
    result_empty_list = analyzer.analyze_storage_health(info_empty_list)
    assert result_empty_list == info_empty_list


@patch("psutil.disk_usage")
def test_smartctl_fallback_to_psutil(mock_disk_usage, analyzer, mock_system_interface):
    """Test that smartctl failure falls back to psutil.disk_usage."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    mock_disk_usage.return_value = psutil._common.sdiskusage(100, 50, 50, 50.0)

    info = {"block_devices": [
        {
            "name": "sda",
            "type": "disk",
            "children": [{"name": "sda1", "mountpoint": "/"}]
        }
    ]}
    result = analyzer.analyze_storage_health(info)
    health_info = result["block_devices"][0]["health"]
    assert health_info["status"] == "FALLBACK_PSUTIL_USAGE"
    assert len(health_info["partitions"]) == 1
    assert health_info["partitions"][0]["percent"] == 50.0


@patch("psutil.disk_usage", side_effect=FileNotFoundError)
def test_smartctl_fallback_psutil_fails(mock_disk_usage, analyzer, mock_system_interface):
    """Test smartctl fallback when psutil also fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    info = {"block_devices": [
        {
            "name": "sda",
            "type": "disk",
            "children": [{"name": "sda1", "mountpoint": "/nonexistent"}]
        }
    ]}
    result = analyzer.analyze_storage_health(info)
    assert "health" not in result["block_devices"][0]


def test_get_lsblk_info_failure(analyzer, mock_system_interface):
    """Test _get_lsblk_info returns None when command fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_lsblk_info() is None


def test_get_df_info_failure(analyzer, mock_system_interface):
    """Test _get_df_info returns None when command fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_df_info() is None


def test_get_smartctl_info_failure(analyzer, mock_system_interface):
    """Test _get_smartctl_info returns None when command fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_smartctl_info("/dev/sda") is None


def test_get_detailed_smartctl_info_failure(analyzer, mock_system_interface):
    """Test _get_detailed_smartctl_info returns None when command fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_detailed_smartctl_info("/dev/sda") is None


def test_get_inode_info_failure(analyzer, mock_system_interface):
    """Test _get_inode_info returns None when command fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_inode_info() is None


def test_invalid_json_lsblk(analyzer, mock_system_interface):
    """Test _get_lsblk_info with invalid JSON output."""
    mock_system_interface.run_command.return_value = CommandResult(True, "{invalid}", "", 0)
    assert analyzer._get_lsblk_info() is None


def test_lsblk_blockdevices_not_list(analyzer, mock_system_interface):
    """Test _get_lsblk_info when 'blockdevices' is not a list."""
    mock_system_interface.run_command.return_value = CommandResult(True, '{"blockdevices": "string"}', "", 0)
    assert analyzer._get_lsblk_info() is None


def test_empty_outputs(analyzer):
    """Test parsing functions with empty strings."""
    assert analyzer._parse_df_output("") == []
    assert analyzer._parse_df_i_output("") == []
    assert analyzer._parse_smartctl_output("") == {"health_status": "UNKNOWN"}
    assert analyzer._parse_detailed_smartctl_output("") == {}