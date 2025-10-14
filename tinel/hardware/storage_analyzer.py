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

from typing import Any, Dict, Optional

import psutil

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class StorageAnalyzer:
    """Analyzes and retrieves detailed information about storage devices.

    This class provides a comprehensive analysis of storage devices, including
    disk partitions, usage, and I/O statistics. It primarily uses `psutil`
    for its data, ensuring cross-platform compatibility and robustness.

    Args:
        system_interface: An optional `SystemInterface` implementation.
                          While this class primarily uses `psutil`, this
                          parameter is included for consistency and future
                          use with command-line tools.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the StorageAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_storage_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive information about storage devices.

        This method gathers data on disk partitions, usage, and I/O counters
        using `psutil`.

        Returns:
            A dictionary containing a detailed breakdown of storage information.
        """
        storage_info: Dict[str, Any] = {
            "disk_partitions": self._get_disk_partitions(),
            "disk_usage": self._get_disk_usage(),
            "disk_io_counters": self._get_disk_io_counters(),
        }
        return storage_info

    def _get_disk_partitions(self) -> Dict[str, Any]:
        """Retrieves information about all mounted disk partitions.

        Returns:
            A dictionary of partition details or an error message.
        """
        try:
            partitions = psutil.disk_partitions()
            return {
                p.device: {
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "opts": p.opts,
                }
                for p in partitions
            }
        except Exception as e:
            return {"error": f"Failed to get disk partitions: {e}"}

    def _get_disk_usage(self) -> Dict[str, Any]:
        """Retrieves usage statistics for all mounted partitions.

        Returns:
            A dictionary of disk usage details or an error message.
        """
        usage_info = {}
        try:
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    usage_info[part.mountpoint] = {
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    }
                except Exception:
                    continue  # Ignore errors for specific mountpoints (e.g., CD-ROMs)
            return usage_info
        except Exception as e:
            return {"error": f"Failed to get disk usage: {e}"}

    def _get_disk_io_counters(self) -> Dict[str, Any]:
        """Retrieves disk I/O statistics.

        Returns:
            A dictionary of disk I/O counters or an error message.
        """
        try:
            io_counters = psutil.disk_io_counters(perdisk=True)
            return {
                disk: {
                    "read_count": counters.read_count,
                    "write_count": counters.write_count,
                    "read_bytes": counters.read_bytes,
                    "write_bytes": counters.write_bytes,
                    "read_time": counters.read_time,
                    "write_time": counters.write_time,
                }
                for disk, counters in io_counters.items()
            }
        except Exception as e:
            return {"error": f"Failed to get disk I/O counters: {e}"}
