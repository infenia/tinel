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
    A class to analyze and retrieve memory information.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        self.system = system_interface or LinuxSystemInterface()

    def get_memory_info(self) -> Dict[str, Any]:
        info: Dict[str, Any] = {}
        psutil_errors: List[str] = []

        try:
            virtual_mem = psutil.virtual_memory()
            info['total_memory_bytes'] = virtual_mem.total
            info['available_memory_bytes'] = virtual_mem.available
            info['used_memory_bytes'] = virtual_mem.used
            info['memory_usage_percent'] = virtual_mem.percent
        except Exception as e:
            psutil_errors.append(f"virtual_memory: {e}")

        try:
            swap_mem = psutil.swap_memory()
            info['total_swap_bytes'] = swap_mem.total
            info['used_swap_bytes'] = swap_mem.used
            info['free_swap_bytes'] = swap_mem.free
            info['swap_usage_percent'] = swap_mem.percent
        except Exception as e:
            psutil_errors.append(f"swap_memory: {e}")

        if psutil_errors:
            info['psutil_error'] = "; ".join(psutil_errors)

        dmi_info = self._get_dmidecode_info()
        if dmi_info:
            info.update(dmi_info)

        return info

    def _get_dmidecode_info(self) -> Dict[str, Any]:
        result = self.system.run_command(["dmidecode", "--type", "memory"])
        if not result.success:
            return {"dmidecode_error": result.error or "Failed to run dmidecode."}
        if not result.stdout:
            return {}
        try:
            return self._parse_dmidecode_output(result.stdout)
        except Exception as e:
            return {"dmidecode_parse_error": str(e)}

    def _parse_dmidecode_output(self, output: str) -> Dict[str, Any]:
        devices = []
        device_blocks = re.split(r'\nHandle 0x[0-9A-Fa-f]+, DMI type 17,', output)

        for block in device_blocks:
            if "Memory Device" not in block:
                continue

            device_info = {}
            for line in block.splitlines():
                if ":" not in line:
                    continue

                parts = line.split(":", 1)
                key = parts[0].strip()
                value = parts[1].strip()

                if not key or not value:
                    continue

                if value in ("Unknown", "Not Specified", "Not Provided"):
                    continue

                device_info[key.lower().replace(" ", "_")] = value

            if device_info and device_info.get("size") != "No Module Installed":
                devices.append(device_info)

        return {"memory_devices": devices}