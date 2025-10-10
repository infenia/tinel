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

import re
from typing import Any, Dict, List, Optional

import psutil

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class MemoryAnalyzer:
    """A class to analyze and retrieve memory information."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """
        Initialize the MemoryAnalyzer.

        Args:
            system_interface: An optional system interface for command execution.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_memory_info(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive memory information.

        This method gathers memory details from `psutil` and, if available,
        supplements it with hardware information from `dmidecode`.

        Returns:
            A dictionary containing detailed memory information, including
            total, available, used, and swap memory, as well as details
            about physical memory modules.
        """
        info: Dict[str, Any] = {}

        # Get basic memory info from psutil
        psutil_errors = []
        try:
            virtual_mem = psutil.virtual_memory()
            info["total_memory_bytes"] = virtual_mem.total
            info["available_memory_bytes"] = virtual_mem.available
            info["used_memory_bytes"] = virtual_mem.used
            info["memory_usage_percent"] = virtual_mem.percent
        except Exception as e:
            psutil_errors.append(f"virtual_memory: {e}")

        try:
            swap_mem = psutil.swap_memory()
            info["total_swap_bytes"] = swap_mem.total
            info["used_swap_bytes"] = swap_mem.used
            info["free_swap_bytes"] = swap_mem.free
            info["swap_usage_percent"] = swap_mem.percent
        except Exception as e:
            psutil_errors.append(f"swap_memory: {e}")

        if psutil_errors:
            info["psutil_error"] = "; ".join(psutil_errors)

        # Get detailed memory module info from dmidecode
        dmi_info = self._get_dmidecode_info()
        if dmi_info:
            info.update(dmi_info)

        return info

    def _get_dmidecode_info(self) -> Dict[str, Any]:
        """
        Run dmidecode to get detailed memory hardware info.

        Returns:
            A dictionary with parsed dmidecode information or an error message.
        """
        result = self.system.run_command(["dmidecode", "--type", "memory"])

        if result.success and result.stdout:
            try:
                return self._parse_dmidecode_output(result.stdout)
            except Exception as e:
                return {"dmidecode_parse_error": str(e)}
        elif result.error:
            return {"dmidecode_error": result.error}
        else:
            return {"dmidecode_error": "Failed to run dmidecode or no output."}

    def _parse_dmidecode_output(self, output: str) -> Dict[str, Any]:
        """
        Parse the output of 'dmidecode --type memory'.

        Args:
            output: The stdout from the dmidecode command.

        Returns:
            A dictionary with structured information about memory devices.
        """
        devices: List[Dict[str, Any]] = []
        current_device: Optional[Dict[str, Any]] = None
        handle_pattern = re.compile(
            r"Handle (0x[0-9A-Fa-f]+), DMI type 17, (\d+) bytes"
        )
        is_installed_module = True

        for line in output.splitlines():
            handle_match = handle_pattern.match(line)
            if handle_match:
                # Previous device is done, add it if it was valid
                if current_device and is_installed_module:
                    devices.append(current_device)

                # Reset for new device
                current_device = {"handle": handle_match.group(1), "dmi_type": 17}
                is_installed_module = (
                    True  # Assume it's installed until proven otherwise
                )

            elif current_device and line.strip() and ":" in line:
                key, value = [v.strip() for v in line.split(":", 1)]

                if key == "Size" and value == "No Module Installed":
                    is_installed_module = False

                if value not in ("Unknown", "No Module Installed", "Not Specified"):
                    s_key = key.lower().replace(" ", "_").replace("-", "_")
                    current_device[s_key] = value

        # Add the very last device if it's valid
        if current_device and is_installed_module:
            devices.append(current_device)

        return {"memory_devices": devices}
