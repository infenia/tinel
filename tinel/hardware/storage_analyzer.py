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

"""This module provides an analyzer for storage devices.

It includes the `StorageAnalyzer` class, which is responsible for gathering
and processing information about the system's storage devices. The analyzer
uses a combination of `lsblk`, `df`, and `smartctl` to provide a
comprehensive overview of block devices, disk usage, and device health.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface

logger = logging.getLogger(__name__)


class StorageAnalyzer:
    """Analyzes and retrieves information about the system's storage devices.

    This class provides methods to gather data on block devices, filesystems,
    and their health status. It uses `lsblk` for device enumeration, `df` for
    usage statistics, and `smartctl` for health diagnostics.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
                          If not provided, a `LinuxSystemInterface` is used.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the StorageAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_storage_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive information about the system's storage.

        This method orchestrates the collection of data from `lsblk`, `df`, and
        `smartctl` to build a complete picture of the storage landscape,
        including block devices, disk usage, and health status.

        Returns:
            A dictionary containing a detailed breakdown of storage information.
        """
        lsblk_info = self._get_lsblk_info()
        df_info = self._get_df_info()

        storage_info: Dict[str, Any] = {
            "block_devices": lsblk_info,
            "disk_usage": df_info,
        }

        if lsblk_info:
            for device in lsblk_info:
                if device.get("type") == "disk":
                    device_name = device.get("name")
                    if device_name:
                        health_info = self._get_smartctl_info(f"/dev/{device_name}")
                        if health_info:
                            device["health"] = health_info
        return {k: v for k, v in storage_info.items() if v is not None}

    def _get_lsblk_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieves block device information using `lsblk`.

        This method executes `lsblk` with JSON output to get a structured list
        of all block devices and their properties, such as name, size, type,
        and model.

        Returns:
            A list of dictionaries, where each dictionary represents a block
            device, or None if the command fails or parsing fails.
        """
        cmd = ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL"]
        result = self.system.run_command(cmd)
        if not result.success or not result.stdout:
            return None
        try:
            lsblk_data = json.loads(result.stdout)
            return lsblk_data.get("blockdevices")
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse lsblk JSON output: %s", e)
            return None

    def _get_df_info(self) -> Optional[List[Dict[str, str]]]:
        """Retrieves disk usage information using `df`.

        This method executes `df -h` to get a human-readable summary of disk
        usage for all mounted filesystems and then parses the output.

        Returns:
            A list of dictionaries, where each dictionary represents a
            filesystem and its usage, or None if the command fails.
        """
        cmd = ["df", "-h"]
        result = self.system.run_command(cmd)
        if result.success and result.stdout:
            return self._parse_df_output(result.stdout)
        return None

    def _parse_df_output(self, df_output: str) -> List[Dict[str, str]]:
        """Parses the output of the `df` command.

        This method processes the raw text output from `df` and extracts
        structured information about each mounted filesystem.

        Args:
            df_output: The raw string output from the `df` command.

        Returns:
            A list of dictionaries, where each dictionary represents a
            filesystem and its usage statistics.
        """
        lines = df_output.strip().split("\n")
        filesystems = []
        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 6:
                filesystem_info = {
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use%": parts[4],
                    "mounted_on": " ".join(parts[5:]),
                }
                filesystems.append(filesystem_info)
        return filesystems

    def _get_smartctl_info(self, device: str) -> Optional[Dict[str, str]]:
        """Retrieves health information for a device using `smartctl`.

        This method executes `smartctl -H` to get the overall health
        self-assessment for a given storage device.

        Args:
            device: The path to the device (e.g., `/dev/sda`).

        Returns:
            A dictionary containing the health status, or None if the command
            fails.
        """
        cmd = ["smartctl", "-H", device]
        result = self.system.run_command(cmd)
        if result.success and result.stdout:
            return self._parse_smartctl_output(result.stdout)
        return None

    def _parse_smartctl_output(self, smartctl_output: str) -> Dict[str, str]:
        """Parses the output of the `smartctl -H` command.

        This method processes the raw text output from `smartctl` to extract
        the overall health self-assessment test result.

        Args:
            smartctl_output: The raw string output from the `smartctl` command.

        Returns:
            A dictionary containing the parsed health status.
        """
        health_status = "UNKNOWN"
        for line in smartctl_output.strip().split("\n"):
            if "SMART overall-health self-assessment test result" in line:
                status = line.split(":")[-1].strip()
                if status:
                    health_status = status
                    break
        return {"health_status": health_status}
