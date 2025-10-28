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

import psutil
import pytest

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
MOCK_DF_OUTPUT = (
    "Filesystem Size Used Avail Use% Mounted on\n/dev/sda1 10G 5G 5G 50% /\n"
)
MOCK_DF_I_OUTPUT = (
    "Filesystem Inodes IUsed IFree IUse% Mounted on\n/dev/sda1 1000 500 500 50% /\n"
)
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


from tinel.hardware.models import BlockDevice, StorageInfo


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
    assert isinstance(info, StorageInfo)
    assert info.block_devices
    assert info.disk_usage
    assert info.inode_usage
    assert info.block_devices[0].health


@patch("psutil.disk_partitions")
def test_lsblk_fallback_psutil_success(
    mock_disk_partitions, analyzer, mock_system_interface
):
    """Test lsblk fallback to psutil successfully."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    mock_disk_partitions.return_value = [
        psutil._common.sdiskpart("/dev/sda1", "/", "ext4", "rw")
    ]
    result = analyzer._get_lsblk_info_with_fallback()
    assert result is not None
    assert len(result) == 1
    assert isinstance(result[0], BlockDevice)


@patch("psutil.disk_partitions", side_effect=Exception("psutil error"))
def test_lsblk_fallback_psutil_fail(
    mock_disk_partitions, analyzer, mock_system_interface
):
    """Test lsblk fallback to psutil when psutil fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_lsblk_info_with_fallback() is None


@patch("psutil.disk_partitions")
@patch("psutil.disk_usage")
def test_df_fallback_psutil_success(
    mock_disk_usage, mock_disk_partitions, analyzer, mock_system_interface
):
    """Test df fallback to psutil successfully."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    mock_disk_partitions.return_value = [
        psutil._common.sdiskpart("/dev/sda1", "/", "ext4", "rw")
    ]
    mock_disk_usage.return_value = psutil._common.sdiskusage(10**10, 5**10, 5**10, 50.0)
    assert analyzer._get_df_info_with_fallback() is not None


@patch("psutil.disk_partitions", side_effect=Exception("psutil error"))
def test_df_fallback_psutil_fail(mock_disk_partitions, analyzer, mock_system_interface):
    """Test df fallback to psutil when psutil fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    assert analyzer._get_df_info_with_fallback() is None


@patch("psutil.disk_partitions", side_effect=Exception("psutil error"))
def test_get_storage_info_all_fail(
    mock_disk_partitions, analyzer, mock_system_interface
):
    """Test get_storage_info when all underlying commands fail."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    info = analyzer.get_storage_info()
    assert not info.block_devices
    assert not info.disk_usage
    assert not info.inode_usage


def test_analyze_storage_health_no_block_devices(analyzer):
    """Test analyze_storage_health when there are no block devices."""
    result = analyzer.analyze_storage_health([])
    assert result == []


@patch("psutil.disk_usage")
def test_smartctl_fallback_to_psutil(mock_disk_usage, analyzer, mock_system_interface):
    """Test that smartctl failure falls back to psutil.disk_usage."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    mock_disk_usage.return_value = psutil._common.sdiskusage(100, 50, 50, 50.0)

    devices = [
        BlockDevice(
            name="sda",
            type="disk",
            children=[BlockDevice(name="sda1", mountpoint="/")],
        )
    ]
    result = analyzer.analyze_storage_health(devices)
    health_info = result[0].health
    assert health_info["status"] == "FALLBACK_PSUTIL_USAGE"
    assert len(health_info["partitions"]) == 1
    expected_percent = 50.0
    assert health_info["partitions"][0]["percent"] == expected_percent


@patch("psutil.disk_usage", side_effect=FileNotFoundError)
def test_smartctl_fallback_psutil_fails(
    mock_disk_usage, analyzer, mock_system_interface
):
    """Test smartctl fallback when psutil also fails."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    devices = [
        BlockDevice(
            name="sda",
            type="disk",
            children=[BlockDevice(name="sda1", mountpoint="/nonexistent")],
        )
    ]
    result = analyzer.analyze_storage_health(devices)
    assert not result[0].health


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
    mock_system_interface.run_command.return_value = CommandResult(
        True, "{invalid}", "", 0
    )
    assert analyzer._get_lsblk_info() is None


def test_lsblk_blockdevices_not_list(analyzer, mock_system_interface):
    """Test _get_lsblk_info when 'blockdevices' is not a list."""
    mock_system_interface.run_command.return_value = CommandResult(
        True, '{"blockdevices": "string"}', "", 0
    )
    assert analyzer._get_lsblk_info() is None


def test_empty_outputs(analyzer):
    """Test parsing functions with empty strings."""
    assert analyzer._parse_df_output("") == []
    assert analyzer._parse_df_i_output("") == []
    assert analyzer._parse_smartctl_output("") == {"health_status": "UNKNOWN"}
    assert analyzer._parse_detailed_smartctl_output("") == {}


def test_analyze_storage_health_skip_non_disk_devices(analyzer, mock_system_interface):
    """Test that non-disk devices are skipped in health analysis."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)

    devices = [
        BlockDevice(name="sda1", type="part"),
        BlockDevice(name="loop0", type="loop"),
        BlockDevice(type="disk"),
    ]
    result = analyzer.analyze_storage_health(devices)
    assert not result[0].health
    assert not result[1].health
    assert not result[2].health


@patch("psutil.disk_usage")
def test_analyze_storage_health_partition_without_mountpoint(
    mock_disk_usage, analyzer, mock_system_interface
):
    """Test partitions without mountpoints are skipped in fallback."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)
    mock_disk_usage.return_value = psutil._common.sdiskusage(100, 50, 50, 50.0)

    devices = [
        BlockDevice(
            name="sda",
            type="disk",
            children=[
                BlockDevice(name="sda1", mountpoint=None),
                BlockDevice(name="sda2", mountpoint=""),
                BlockDevice(name="sda3", mountpoint="/"),
            ],
        )
    ]
    result = analyzer.analyze_storage_health(devices)
    health_info = result[0].health
    assert len(health_info["partitions"]) == 1
    assert health_info["partitions"][0]["partition"] == "sda3"


def test_parse_df_output_malformed_lines(analyzer):
    """Test _parse_df_output skips malformed lines."""
    malformed_output = (
        "Filesystem Size Used Avail Use% Mounted on\n"
        "/dev/sda1 10G 5G 5G 50% /\n"
        "/dev/sdb1 20G\n"
        "tmpfs 1G 0 1G 0% /tmp\n"
        "incomplete line\n"
    )
    result = analyzer._parse_df_output(malformed_output)
    assert len(result) == 2
    assert result[0].filesystem == "/dev/sda1"
    assert result[1].filesystem == "tmpfs"


def test_parse_smartctl_output_empty_status(analyzer):
    """Test _parse_smartctl_output with empty status."""
    empty_status_output = "SMART overall-health self-assessment test result:\n"
    result = analyzer._parse_smartctl_output(empty_status_output)
    assert result["health_status"] == "UNKNOWN"

    multiple_empty = (
        "Some other line\n"
        "SMART overall-health self-assessment test result:\n"
        "Another line\n"
    )
    result = analyzer._parse_smartctl_output(multiple_empty)
    assert result["health_status"] == "UNKNOWN"


def test_parse_df_i_output_malformed_lines(analyzer):
    """Test _parse_df_i_output skips malformed lines."""
    malformed_output = (
        "Filesystem Inodes IUsed IFree IUse% Mounted on\n"
        "/dev/sda1 1000 500 500 50% /\n"
        "/dev/sdb1 2000\n"
        "tmpfs 5000 100 4900 2% /tmp\n"
        "short\n"
    )
    result = analyzer._parse_df_i_output(malformed_output)
    assert len(result) == 2
    assert result[0].filesystem == "/dev/sda1"
    assert result[1].filesystem == "tmpfs"


def test_analyze_storage_health_disk_without_children(analyzer, mock_system_interface):
    """Test analyze_storage_health when disk has no children."""
    mock_system_interface.run_command.return_value = CommandResult(False, "", "err", 1)

    devices = [BlockDevice(name="sdb", type="disk")]
    result = analyzer.analyze_storage_health(devices)
    assert not result[0].health

    devices_empty_children = [BlockDevice(name="sdc", type="disk", children=[])]
    result = analyzer.analyze_storage_health(devices_empty_children)
    assert not result[0].health
