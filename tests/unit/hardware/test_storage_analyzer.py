#!/usr/bin/env python3
"""
Unit tests for storage analyzer implementation.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from unittest.mock import Mock, patch

import psutil

from tests.utils import unit_test
from tinel.hardware.storage_analyzer import StorageAnalyzer


class TestStorageAnalyzer:
    """Test cases for StorageAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.analyzer = StorageAnalyzer(self.mock_system)

    @unit_test
    @patch("tinel.hardware.storage_analyzer.psutil")
    def test_get_storage_info_success(self, mock_psutil):
        """Test successful retrieval of storage information."""
        # Arrange
        mock_psutil.disk_partitions.return_value = [
            psutil._common.sdiskpart(
                device="/dev/sda1", mountpoint="/", fstype="ext4", opts="rw"
            )
        ]
        mock_psutil.disk_usage.return_value = psutil._common.sdiskusage(
            total=100, used=50, free=50, percent=50.0
        )
        mock_psutil.disk_io_counters.return_value = {
            "sda1": psutil._common.sdiskio(
                read_count=1,
                write_count=2,
                read_bytes=3,
                write_bytes=4,
                read_time=5,
                write_time=6,
            )
        }

        # Act
        storage_info = self.analyzer.get_storage_info()

        # Assert
        assert "disk_partitions" in storage_info
        assert "/dev/sda1" in storage_info["disk_partitions"]
        assert "disk_usage" in storage_info
        assert "/" in storage_info["disk_usage"]
        assert storage_info["disk_usage"]["/"]["percent"] == 50.0
        assert "disk_io_counters" in storage_info
        assert "sda1" in storage_info["disk_io_counters"]

    @unit_test
    @patch("tinel.hardware.storage_analyzer.psutil")
    def test_get_disk_partitions_error(self, mock_psutil):
        """Test error handling for disk partitions."""
        # Arrange
        mock_psutil.disk_partitions.side_effect = Exception("Test error")

        # Act
        partitions = self.analyzer._get_disk_partitions()

        # Assert
        assert "error" in partitions
        assert "Test error" in partitions["error"]

    @unit_test
    @patch("tinel.hardware.storage_analyzer.psutil")
    def test_get_disk_usage_error(self, mock_psutil):
        """Test error handling for disk usage."""
        # Arrange
        mock_psutil.disk_partitions.side_effect = Exception("Test error")

        # Act
        usage = self.analyzer._get_disk_usage()

        # Assert
        assert "error" in usage
        assert "Test error" in usage["error"]

    @unit_test
    @patch("tinel.hardware.storage_analyzer.psutil")
    def test_get_disk_io_counters_error(self, mock_psutil):
        """Test error handling for disk I/O counters."""
        # Arrange
        mock_psutil.disk_io_counters.side_effect = Exception("Test error")

        # Act
        io_counters = self.analyzer._get_disk_io_counters()

        # Assert
        assert "error" in io_counters
        assert "Test error" in io_counters["error"]
