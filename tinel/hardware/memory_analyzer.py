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
from typing import Any, Dict, List, Optional, Tuple

import psutil

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class MemoryAnalyzer:
    """
    A class to analyze and retrieve memory information, prioritizing native
    system files and using psutil for verification and fallback.
    """

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

        This method gathers memory details from /proc/meminfo as the primary
        source, cross-verifies with psutil, and supplements with hardware
        information from dmidecode.

        Returns:
            A dictionary containing detailed memory information.
        """
        info: Dict[str, Any] = {}

        # Get memory info from /proc/meminfo
        meminfo_content = self.system.read_file("/proc/meminfo")
        if meminfo_content:
            info.update(self._parse_meminfo(meminfo_content))
        else:
            info['proc_meminfo_error'] = "Failed to read /proc/meminfo"

        # Get memory info from psutil for cross-verification and fallback
        psutil_info, psutil_error = self._get_psutil_memory_info()
        if psutil_error:
            info['psutil_error'] = psutil_error

        if psutil_info:
            info.update(self._cross_verify_and_supplement(info, psutil_info))

        # Get detailed memory module info from dmidecode
        dmi_info = self._get_dmidecode_info()
        if dmi_info:
            info.update(dmi_info)

        return info

    def _parse_meminfo(self, content: str) -> Dict[str, Any]:
        """
        Parse the content of /proc/meminfo.

        Args:
            content: The string content of /proc/meminfo.

        Returns:
            A dictionary with parsed memory information.
        """
        meminfo: Dict[str, int] = {}
        for line in content.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].replace(":", "")
                value = int(parts[1])
                meminfo[key] = value

        parsed_info: Dict[str, Any] = {'proc_meminfo_raw': meminfo}

        if 'MemTotal' in meminfo:
            parsed_info['total_memory_kb'] = meminfo['MemTotal']
        if 'MemAvailable' in meminfo:
            parsed_info['available_memory_kb'] = meminfo['MemAvailable']
            if 'MemTotal' in meminfo:
                used = meminfo['MemTotal'] - meminfo['MemAvailable']
                parsed_info['used_memory_kb'] = used
                parsed_info['memory_usage_percent'] = round((used / meminfo['MemTotal']) * 100, 2)

        if 'SwapTotal' in meminfo:
            parsed_info['total_swap_kb'] = meminfo['SwapTotal']
        if 'SwapFree' in meminfo:
            parsed_info['free_swap_kb'] = meminfo['SwapFree']
            if 'SwapTotal' in meminfo and meminfo['SwapTotal'] > 0:
                 used_swap = meminfo['SwapTotal'] - meminfo['SwapFree']
                 parsed_info['used_swap_kb'] = used_swap
                 parsed_info['swap_usage_percent'] = round((used_swap / meminfo['SwapTotal']) * 100, 2)
            else:
                 parsed_info['swap_usage_percent'] = 0.0

        return parsed_info

    def _get_psutil_memory_info(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Get memory information using psutil.

        Returns:
            A tuple containing a dictionary of psutil memory info and an
            optional error string.
        """
        info: Dict[str, Any] = {}
        errors: List[str] = []

        try:
            virtual = psutil.virtual_memory()
            info['psutil_total_memory_bytes'] = virtual.total
            info['psutil_available_memory_bytes'] = virtual.available
            info['psutil_used_memory_bytes'] = virtual.used
            info['psutil_memory_usage_percent'] = virtual.percent
        except Exception as e:
            errors.append(f"psutil.virtual_memory: {e}")

        try:
            swap = psutil.swap_memory()
            info['psutil_total_swap_bytes'] = swap.total
            info['psutil_used_swap_bytes'] = swap.used
            info['psutil_swap_usage_percent'] = swap.percent
        except Exception as e:
            errors.append(f"psutil.swap_memory: {e}")

        return info, "; ".join(errors) if errors else None

    def _cross_verify_and_supplement(self, info: Dict[str, Any], psutil_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use psutil data to supplement and verify existing info.

        Args:
            info: The dictionary with info from /proc/meminfo.
            psutil_info: The dictionary with info from psutil.

        Returns:
            The updated info dictionary.
        """
        # If primary data source failed, use psutil as fallback
        if 'total_memory_kb' not in info and 'psutil_total_memory_bytes' in psutil_info:
            info['total_memory_bytes'] = psutil_info['psutil_total_memory_bytes']
            info['available_memory_bytes'] = psutil_info['psutil_available_memory_bytes']
            info['used_memory_bytes'] = psutil_info['psutil_used_memory_bytes']
            info['memory_usage_percent'] = psutil_info['psutil_memory_usage_percent']

        if 'total_swap_kb' not in info and 'psutil_total_swap_bytes' in psutil_info:
             info['total_swap_bytes'] = psutil_info['psutil_total_swap_bytes']
             info['used_swap_bytes'] = psutil_info['psutil_used_swap_bytes']
             info['swap_usage_percent'] = psutil_info['psutil_swap_usage_percent']

        # Add psutil data for cross-verification
        info.update(psutil_info)
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
        handle_pattern = re.compile(r"Handle (0x[0-9A-Fa-f]+), DMI type 17, (\d+) bytes")
        is_installed_module = True

        for line in output.splitlines():
            handle_match = handle_pattern.match(line)
            if handle_match:
                if current_device and is_installed_module:
                    devices.append(current_device)

                current_device = {"handle": handle_match.group(1), "dmi_type": 17}
                is_installed_module = True

            elif current_device and line.strip() and ":" in line:
                key, value = [v.strip() for v in line.split(":", 1)]

                if key == "Size" and value == "No Module Installed":
                    is_installed_module = False

                if value not in ("Unknown", "No Module Installed", "Not Specified"):
                    s_key = key.lower().replace(" ", "_").replace("-", "_")
                    current_device[s_key] = value

        if current_device and is_installed_module:
            devices.append(current_device)

        return {"memory_devices": devices}