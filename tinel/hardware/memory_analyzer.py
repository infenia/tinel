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
from .models import MemoryDeviceDetails, MemoryInfo

"""Analyzes system memory, including virtual, swap, and physical devices.

This module provides the `MemoryAnalyzer` class, which gathers comprehensive
information about the system's memory configuration and usage. It uses `psutil`
to get high-level statistics about virtual and swap memory, and the `dmidecode`
command-line tool to retrieve detailed hardware information for each physical
memory module (e.g., DIMM, SODIMM).

The module also includes a helper function to analyze memory performance based
on the data collected from `dmidecode`.
"""


def analyze_memory_performance(info: MemoryInfo) -> Dict[str, Any]:
    """Analyzes memory performance metrics from dmidecode info.

    This function calculates effective speed and other metrics based on the
    parsed `dmidecode` data.

    Args:
        info: A dictionary containing memory device information.

    Returns:
        A dictionary with calculated performance metrics.
    """
    if not info.memory_devices:
        return {}

    analysis: Dict[str, Any] = {"effective_speed_mhz": 0}
    speeds = []

    for device in info.memory_devices:
        if not device:
            continue
        try:
            speed_str = device.speed
            if speed_str and "MT/s" in speed_str:
                # Extract numeric value from "2400 MT/s"
                match = re.match(r"(\d+)", speed_str)
                if match:
                    speed_val = int(match.group(1))
                    speeds.append(speed_val)
        except (ValueError, TypeError):
            continue

    if speeds:
        # A simplified approach to effective speed; a more complex model might
        # consider memory channels, ranks, and timings.
        analysis["effective_speed_mhz"] = sum(speeds) // len(speeds)

    return analysis


class MemoryAnalyzer:
    """Analyzes and retrieves information about the system's memory.

    This class provides methods to gather data on both virtual memory (RAM and
    swap) and physical memory devices. It leverages `psutil` for overall memory
    statistics and `dmidecode` for detailed hardware information about memory
    modules.

    The primary public method, `get_memory_info()`, returns a dictionary
    containing both high-level usage statistics and a detailed list of
    physical memory devices.

    Attributes:
        system: An instance of a `SystemInterface` for interacting with the
                underlying operating system. Defaults to `LinuxSystemInterface`.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the MemoryAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions. If not provided, a default
                              `LinuxSystemInterface` is instantiated.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_memory_info(self) -> MemoryInfo:
        """Retrieves comprehensive information about the system's memory.

        This method aggregates memory data from two primary sources:
        1.  `psutil`: For high-level statistics on virtual memory (RAM) and
            swap space, including total, used, and available amounts.
        2.  `dmidecode`: For detailed hardware information about each physical
            memory module (DIMM), such as size, type, speed, and manufacturer.

        If `dmidecode` is unavailable or fails, the method will still return
        the `psutil` data and include an error message in the 'dmidecode_error'
        field.

        Returns:
            A dictionary containing a detailed breakdown of memory information.
            Keys include 'total_memory_bytes', 'memory_usage_percent',
            'total_swap_bytes', 'swap_usage_percent', and 'memory_devices'.
            The 'memory_devices' key holds a list of dictionaries, each
            representing a physical memory module.
        """
        info = MemoryInfo()
        psutil_errors: List[str] = []

        try:
            virtual_mem = psutil.virtual_memory()
            info.total_memory_bytes = virtual_mem.total
            info.available_memory_bytes = virtual_mem.available
            info.used_memory_bytes = virtual_mem.used
            info.memory_usage_percent = virtual_mem.percent
        except Exception as e:
            psutil_errors.append(f"virtual_memory: {e}")

        try:
            swap_mem = psutil.swap_memory()
            info.total_swap_bytes = swap_mem.total
            info.used_swap_bytes = swap_mem.used
            info.free_swap_bytes = swap_mem.free
            info.swap_usage_percent = swap_mem.percent
        except Exception as e:
            psutil_errors.append(f"swap_memory: {e}")

        if psutil_errors:
            info.psutil_error = "; ".join(psutil_errors)

        dmi_info = self._get_dmidecode_info()
        if dmi_info:
            if dmi_info.get("memory_devices"):
                info.memory_devices = dmi_info["memory_devices"]
                performance_analysis = analyze_memory_performance(info)
                if performance_analysis:
                    info.performance_analysis = performance_analysis
            elif "dmidecode_error" in dmi_info:
                info.dmidecode_error = dmi_info["dmidecode_error"]
            elif "dmidecode_parse_error" in dmi_info:
                info.dmidecode_parse_error = dmi_info["dmidecode_parse_error"]

        # Add top-level memory info, similar to lshw
        if info.total_memory_bytes:
            info.size = info.total_memory_bytes
            info.units = "bytes"

        return info

    def _get_dmidecode_info(self) -> Dict[str, Any]:
        """Retrieves and parses memory information from `dmidecode`.

        This method executes the `dmidecode` command to get detailed hardware
        information about the physical memory modules and then parses the
        output.

        Returns:
            A dictionary containing the parsed `dmidecode` information, or an
            error message if the command fails or parsing fails.
        """
        result = self.system.run_command(["dmidecode", "--type", "memory"])
        if not result.success:
            # Fallback to psutil if dmidecode is not available
            if "No such file or directory" in (result.stderr or "") or (
                result.error and "not found" in result.error
            ):
                return {
                    "dmidecode_error": "dmidecode not found, using psutil fallback."
                }
            return {"dmidecode_error": result.error or "Failed to run dmidecode."}
        if not result.stdout:
            return {}
        try:
            return self._parse_dmidecode_output(result.stdout)
        except Exception as e:
            return {"dmidecode_parse_error": str(e)}

    def _parse_dmidecode_output(self, output: str) -> Dict[str, Any]:
        """Parses the output of the `dmidecode` command for memory information.

        This method processes the raw text output from `dmidecode` and extracts
        details about each physical memory device, such as size, type, speed,
        and manufacturer.

        Args:
            output: The raw string output from the `dmidecode` command.

        Returns:
            A dictionary containing a list of memory devices, where each device
            is represented by a dictionary of its attributes.
        """
        devices: List[MemoryDeviceDetails] = []
        device_blocks = re.split(r"\nHandle 0x[0-9A-Fa-f]+, DMI type 17,", output)

        for block in device_blocks:
            if "Memory Device" not in block:
                continue

            raw_details: Dict[str, str] = {}
            for line in block.splitlines():
                if ":" not in line:
                    continue

                parts = line.split(":", 1)
                key = parts[0].strip().lower().replace(" ", "_")
                value = parts[1].strip()

                if not key or not value or value in ("Unknown", "Not Specified"):
                    continue

                raw_details[key] = value

            if raw_details and raw_details.get("size") != "No Module Installed":
                devices.append(
                    MemoryDeviceDetails(
                        size=raw_details.get("size"),
                        form_factor=raw_details.get("form_factor"),
                        device_type=raw_details.get("type"),
                        speed=raw_details.get("speed"),
                        manufacturer=raw_details.get("manufacturer"),
                        serial_number=raw_details.get("serial_number"),
                        asset_tag=raw_details.get("asset_tag"),
                        part_number=raw_details.get("part_number"),
                        attributes=raw_details.get("attributes"),
                        configured_clock_speed=raw_details.get("configured_clock_speed"),
                        configured_voltage=raw_details.get("configured_voltage"),
                        min_voltage=raw_details.get("minimum_voltage"),
                        max_voltage=raw_details.get("maximum_voltage"),
                        raw_details=raw_details,
                    )
                )

        return {"memory_devices": devices}