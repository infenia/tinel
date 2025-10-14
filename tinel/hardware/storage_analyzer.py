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
from typing import Any, Dict, List, Optional

import psutil

from tinel.interfaces import SystemInterface
from tinel.system import LinuxSystemInterface


class StorageAnalyzer:
    """Analyzes and retrieves information about the system's storage devices."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the StorageAnalyzer."""
        self.system = system_interface or LinuxSystemInterface()

    def get_storage_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive information about the system's storage."""
        storage_info: Dict[str, Any] = {
            "block_devices": self._get_lsblk_info_with_fallback(),
            "disk_usage": self._get_df_info_with_fallback(),
            "inode_usage": self._get_inode_info(),
        }

        if storage_info.get("block_devices"):
            storage_info = self.analyze_storage_health(storage_info)

        return {k: v for k, v in storage_info.items() if v is not None}

    def analyze_storage_health(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the health of storage devices and extends the provided info.

        This method iterates through block devices, retrieves health data
        using `smartctl`, and integrates it into the device information.
        If `smartctl` is unavailable, it falls back to providing disk usage
        statistics for the device's partitions using `psutil`.

        Args:
            info: A dictionary containing existing storage information,
                  including a 'block_devices' key.

        Returns:
            The extended dictionary with health or usage information.
        """
        block_devices = info.get("block_devices", [])
        if not block_devices:
            return info

        for device in block_devices:
            if device.get("type") == "disk" and device.get("name"):
                device_path = f"/dev/{device['name']}"
                health_info = self._get_smartctl_info(device_path)
                detailed_health_info = self._get_detailed_smartctl_info(device_path)

                if health_info or detailed_health_info:
                    device["health"] = {
                        **(health_info or {}),
                        **(detailed_health_info or {}),
                    }
                else:  # Fallback to psutil
                    partitions = device.get("children", [])
                    fallback_usage = []
                    if partitions:
                        for part in partitions:
                            mountpoint = part.get("mountpoint")
                            if mountpoint:
                                try:
                                    usage = psutil.disk_usage(mountpoint)
                                    fallback_usage.append(
                                        {
                                            "partition": part.get("name"),
                                            "mountpoint": mountpoint,
                                            "total": usage.total,
                                            "used": usage.used,
                                            "free": usage.free,
                                            "percent": usage.percent,
                                        }
                                    )
                                except (
                                    FileNotFoundError,
                                    PermissionError,
                                ):
                                    continue  # Skip partitions we can't access
                    if fallback_usage:
                        device["health"] = {
                            "status": "FALLBACK_PSUTIL_USAGE",
                            "partitions": fallback_usage,
                        }
        info["block_devices"] = block_devices
        return info

    def _get_lsblk_info_with_fallback(self) -> Optional[List[Dict[str, Any]]]:
        """Tries to get block device info from `lsblk`, falls back to `psutil`."""
        lsblk_info = self._get_lsblk_info()
        if lsblk_info is not None:
            return lsblk_info

        try:
            partitions = psutil.disk_partitions()
            return [
                {
                    "name": part.device.split("/")[-1],
                    "size": None,
                    "type": "part",
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "model": "N/A (from psutil)",
                }
                for part in partitions
            ]
        except Exception:
            return None

    def _get_df_info_with_fallback(self) -> Optional[List[Dict[str, str]]]:
        """Tries to get disk usage from `df`, falls back to `psutil`."""
        df_info = self._get_df_info()
        if df_info is not None:
            return df_info

        try:
            partitions = psutil.disk_partitions()
            usage_info = []
            for part in partitions:
                usage = psutil.disk_usage(part.mountpoint)
                usage_info.append(
                    {
                        "filesystem": part.device,
                        "size": f"{usage.total // (1024**3)}G",
                        "used": f"{usage.used // (1024**3)}G",
                        "available": f"{usage.free // (1024**3)}G",
                        "use%": f"{usage.percent}%",
                        "mounted_on": part.mountpoint,
                    }
                )
            return usage_info
        except Exception:
            return None

    def _get_lsblk_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieves block device information using `lsblk`."""
        cmd = ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL"]
        result = self.system.run_command(cmd)

        if not result.success or not result.stdout:
            return None

        try:
            lsblk_data = json.loads(result.stdout)
            block_devices = lsblk_data.get("blockdevices")
            return block_devices if isinstance(block_devices, list) else None
        except json.JSONDecodeError:
            return None

    def _get_df_info(self) -> Optional[List[Dict[str, str]]]:
        """Retrieves disk usage information using `df`."""
        cmd = ["df", "-h"]
        result = self.system.run_command(cmd)
        return self._parse_df_output(result.stdout) if result.success else None

    def _parse_df_output(self, df_output: str) -> List[Dict[str, str]]:
        """Parses the output of the `df` command."""
        lines = (df_output or "").strip().split("\n")
        filesystems = []
        min_df_parts = 6
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= min_df_parts:
                filesystems.append(
                    {
                        "filesystem": parts[0],
                        "size": parts[1],
                        "used": parts[2],
                        "available": parts[3],
                        "use%": parts[4],
                        "mounted_on": " ".join(parts[5:]),
                    }
                )
        return filesystems

    def _get_smartctl_info(self, device: str) -> Optional[Dict[str, str]]:
        """Retrieves health information for a device using `smartctl`."""
        cmd = ["smartctl", "-H", device]
        result = self.system.run_command(cmd)
        return self._parse_smartctl_output(result.stdout) if result.success else None

    def _parse_smartctl_output(self, smartctl_output: str) -> Dict[str, str]:
        """Parses the output of the `smartctl -H` command."""
        health_status = "UNKNOWN"
        for line in (smartctl_output or "").strip().split("\n"):
            if "SMART overall-health self-assessment test result" in line:
                status = line.split(":")[-1].strip()
                if status:
                    health_status = status
                    break
        return {"health_status": health_status}

    def _get_detailed_smartctl_info(self, device: str) -> Optional[Dict[str, Any]]:
        """Retrieves detailed health information using `smartctl -i`."""
        cmd = ["smartctl", "-i", device]
        result = self.system.run_command(cmd)
        return (
            self._parse_detailed_smartctl_output(result.stdout)
            if result.success
            else None
        )

    def _parse_detailed_smartctl_output(self, output: str) -> Dict[str, Any]:
        """Parses the output of `smartctl -i`."""
        attributes = {}
        for line in (output or "").strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_").replace("-", "_")
                attributes[key] = value.strip()
        return attributes

    def _get_inode_info(self) -> Optional[List[Dict[str, str]]]:
        """Retrieves filesystem inode usage using `df -i`."""
        cmd = ["df", "-i"]
        result = self.system.run_command(cmd)
        return self._parse_df_i_output(result.stdout) if result.success else None

    def _parse_df_i_output(self, df_output: str) -> List[Dict[str, str]]:
        """Parses the output of the `df -i` command."""
        lines = (df_output or "").strip().split("\n")
        filesystems = []
        min_df_parts = 6
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= min_df_parts:
                filesystems.append(
                    {
                        "filesystem": parts[0],
                        "inodes": parts[1],
                        "iused": parts[2],
                        "ifree": parts[3],
                        "iuse%": parts[4],
                        "mounted_on": " ".join(parts[5:]),
                    }
                )
        return filesystems
