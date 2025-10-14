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
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import psutil

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface
from .models import MemoryDeviceDetails


def analyze_memory_performance(info: Dict[str, Any]) -> Dict[str, Any]:
    """Analyzes memory performance metrics from dmidecode info.

    This function calculates effective speed and other metrics based on the
    parsed `dmidecode` data.

    Args:
        info: A dictionary containing memory device information.

    Returns:
        A dictionary with calculated performance metrics.
    """
    if "memory_devices" not in info or not info["memory_devices"]:
        return {}

    analysis: Dict[str, Any] = {"effective_speed_mhz": 0}
    speeds = []

    for device in info["memory_devices"]:
        if not device:
            continue
        try:
            speed_str = device.get("speed")
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

    This class provides a comprehensive analysis of the system's memory. It uses
    `psutil` as the primary source for overall memory and swap usage statistics.
    For detailed information about physical memory modules (RAM sticks), it uses
    the `dmidecode` command. If `dmidecode` is not available or fails, the
    physical device information will be omitted, but the `psutil` data will
    still be returned.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
                          If not provided, a `LinuxSystemInterface` is used.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the MemoryAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_memory_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive memory info from psutil and dmidecode.

        Gathers virtual memory and swap statistics from `psutil`. It then
        attempts to gather physical memory device details from `dmidecode`.
        Failures in one do not prevent the other from being returned.

        Returns:
            A dictionary containing a detailed breakdown of memory information.
        """
        info: Dict[str, Any] = {}
        psutil_errors: List[str] = []

        # --- Primary Source: psutil for memory usage ---
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

        # --- Secondary Source: dmidecode for hardware details ---
        dmi_info = self._get_dmidecode_info()
        if dmi_info:
            if dmi_info.get("memory_devices"):
                # Convert list of dataclasses to list of dicts for JSON serialization
                info["memory_devices"] = [asdict(d) for d in dmi_info["memory_devices"]]
                performance_analysis = analyze_memory_performance(info)
                if performance_analysis:
                    info["performance_analysis"] = performance_analysis
            elif "error" in dmi_info:
                info["dmidecode_error"] = dmi_info["error"]

        return info

    def _get_dmidecode_info(self) -> Dict[str, Any]:
        """Retrieves and parses memory info from `dmidecode`.

        Returns:
            A dictionary with parsed data or an error key if it fails.
        """
        try:
            result = self.system.run_command(["dmidecode", "--type", "memory"])
            if not result.success:
                if "not found" in (result.stderr or "") or "No such file" in (
                    result.stderr or ""
                ):
                    return {"error": "`dmidecode` command not found."}
                return {
                    "error": f"`dmidecode` failed: {result.stderr or 'Unknown error'}"
                }
            if not result.stdout:
                return {}
            return self._parse_dmidecode_output(result.stdout)
        except Exception as e:
            return {
                "error": f"An unexpected error occurred while running dmidecode: {e}"
            }

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
                        part_number=raw_details.get("part_number"),
                        attributes=raw_details.get("attributes"),
                        raw_details=raw_details,
                    )
                )

        return {"memory_devices": devices}
