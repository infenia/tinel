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
from typing import Any, Dict, List, Optional, cast

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class StorageAnalyzer:
    """A class to analyze and retrieve storage information."""

    MIN_DF_PARTS = 6

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """
        Initialize the StorageAnalyzer.
        Args:
            system_interface: An optional system interface for running commands.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get comprehensive storage information.
        Returns:
            A dictionary containing detailed storage information.
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
        """
        Get block device information using lsblk.
        Returns:
            A list of dictionaries, where each dictionary represents a block device.
        """
        cmd = ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL"]
        result = self.system.run_command(cmd)

        if result.success and result.stdout:
            try:
                lsblk_data = json.loads(result.stdout)
                blockdevices = lsblk_data.get("blockdevices")
                if blockdevices is not None:
                    return cast(List[Dict[str, Any]], blockdevices)
                return None
            except json.JSONDecodeError:
                return None
        return None

    def _get_df_info(self) -> Optional[List[Dict[str, str]]]:
        """
        Get disk usage information using df.
        Returns:
            A list of dictionaries, where each dictionary represents a filesystem.
        """
        cmd = ["df", "-h"]
        result = self.system.run_command(cmd)

        if result.success and result.stdout:
            return self._parse_df_output(result.stdout)
        return None

    def _parse_df_output(self, df_output: str) -> List[Dict[str, str]]:
        """
        Parse the output of the df command.
        Args:
            df_output: The stdout of the df command.
        Returns:
            A list of dictionaries representing filesystems.
        """
        lines = df_output.strip().split("\n")
        filesystems = []
        # Skip header line
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= self.MIN_DF_PARTS:
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
        """
        Get health information for a device using smartctl.
        Args:
            device: The device path (e.g., /dev/sda).
        Returns:
            A dictionary containing the health status.
        """
        cmd = ["smartctl", "-H", device]
        result = self.system.run_command(cmd)

        if result.success and result.stdout:
            return self._parse_smartctl_output(result.stdout)
        return None

    def _parse_smartctl_output(self, smartctl_output: str) -> Dict[str, str]:
        """
        Parse the output of the smartctl command.
        Args:
            smartctl_output: The stdout of the smartctl command.
        Returns:
            A dictionary containing the health status.
        """
        health_status = "UNKNOWN"
        for line in smartctl_output.strip().split("\n"):
            if "SMART overall-health self-assessment test result" in line:
                status = line.split(":")[-1].strip()
                if status:
                    health_status = status
                    break
        return {"health_status": health_status}
