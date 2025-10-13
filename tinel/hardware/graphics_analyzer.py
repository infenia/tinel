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

"""This module provides an analyzer for graphics hardware (GPUs).

It includes the `GraphicsAnalyzer` class, which is responsible for detecting
and gathering information about the system's graphics cards. The analyzer
employs a fallback mechanism, first attempting to use vendor-specific tools
like `nvidia-smi` and `rocm-smi`, and then resorting to the generic `lspci`
command if necessary.
"""

import functools
import logging
import re
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class GraphicsAnalyzer:
    """Analyzes and retrieves information about graphics hardware (GPUs).

    This class is designed to detect and report on the system's graphics
    cards. It uses a multi-tiered approach, prioritizing vendor-specific tools
    for detailed information and falling back to more generic utilities.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
                          If not provided, a `LinuxSystemInterface` is used.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the GraphicsAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()
        self.logger = logging.getLogger(__name__)

    @functools.lru_cache(maxsize=None)
    def get_graphics_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive information about the graphics hardware.

        This method serves as the primary entry point for gathering graphics
        card data. It employs a fallback strategy, attempting to use
        vendor-specific tools like `nvidia-smi` and `rocm-smi` before
        resorting to the more generic `lspci` command. The result is cached
        to improve performance on subsequent calls.

        Returns:
            A dictionary containing detailed graphics hardware information,
            including the source of the data (e.g., 'nvidia-smi', 'lspci').
        """
        info: Dict[str, Any] = {}

        # Try NVIDIA's tool first
        nvidia_info = self._get_nvidia_info()
        if nvidia_info:
            info["gpus"] = nvidia_info
            info["source"] = "nvidia-smi"
            return info

        # Try AMD's tool next
        amd_info = self._get_amd_info()
        if amd_info:
            info["gpus"] = amd_info
            info["source"] = "rocm-smi"
            return info

        # Fallback to lspci
        lspci_info = self._get_lspci_info()
        if lspci_info:
            info["gpus"] = lspci_info
            info["source"] = "lspci"
            return info

        self.logger.warning("No GPU information could be gathered.")
        return info

    def _get_nvidia_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieves GPU information using the `nvidia-smi` command.

        This method queries the `nvidia-smi` utility for detailed information
        about NVIDIA GPUs, including model, driver version, memory usage,
        utilization, and temperature.

        Returns:
            A list of dictionaries, where each dictionary represents an NVIDIA
            GPU, or None if `nvidia-smi` is not available or fails.
        """
        command = [
            "nvidia-smi",
            "--query-gpu=index,name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits",
        ]
        result = self.system.run_command(command)

        if not result.success:
            self.logger.info("'nvidia-smi' command failed or not found.")
            return None

        gpus = []
        for line in result.stdout.strip().split("\n"):
            try:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) != 8:
                    continue
                gpus.append(
                    {
                        "index": int(parts[0]),
                        "model": parts[1],
                        "driver_version": parts[2],
                        "memory_total_mb": int(parts[3]),
                        "memory_used_mb": int(parts[4]),
                        "memory_free_mb": int(parts[5]),
                        "utilization_percent": int(parts[6]),
                        "temperature_celsius": int(parts[7]),
                    }
                )
            except (ValueError, IndexError) as e:
                self.logger.warning(
                    "Failed to parse nvidia-smi output line: '%s'. Error: %s", line, e
                )

        return gpus if gpus else None

    def _get_amd_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieves GPU information using the `rocm-smi` command.

        This method is intended to query the `rocm-smi` utility for detailed
        information about AMD GPUs. Currently, it serves as a placeholder
        as `rocm-smi` is not available in the test environment.

        Returns:
            A list of dictionaries, where each dictionary represents an AMD
            GPU, or None if `rocm-smi` is not available or fails.
        """
        # rocm-smi is not installed in the test environment, so this is a placeholder.
        # In a real environment, this would parse the output of `rocm-smi`.
        # For example, `rocm-smi --showproductname --showmeminfo vram --showdriverversion --showtemp --showuse`
        result = self.system.run_command(
            ["rocm-smi", "--showallinfo"]
        )  # A bit generic for a placeholder

        if not result.success:
            self.logger.info("'rocm-smi' command failed or not found.")
            return None

        # Placeholder for parsing logic
        # Since I cannot run the command, I will assume a hypothetical output structure.
        # This part would need to be implemented and tested on a system with an AMD GPU and rocm-smi.
        gpus = [
            {
                "model": "AMD GPU (rocm-smi placeholder)",
                "error": "Parsing not implemented",
            }
        ]
        self.logger.info("rocm-smi parsing is not yet implemented.")

        return gpus

    def _get_lspci_info(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieves basic GPU information using the `lspci` command.

        This method serves as a fallback for when vendor-specific tools are not
        available. It parses the output of `lspci` to identify VGA-compatible
        controllers and extracts basic information such as the model, vendor ID,
        and device ID.

        Returns:
            A list of dictionaries, where each dictionary represents a GPU
            found by `lspci`, or None if the command fails.
        """
        result = self.system.run_command(["lspci", "-vnn"])

        if not result.success:
            self.logger.warning("'lspci' command failed or not found.")
            return None

        gpus = []
        current_gpu = None

        for line in result.stdout.strip().split("\n"):
            vga_match = re.search(
                r"VGA compatible controller.*\[(\w{4}):(\w{4})\]", line
            )
            if vga_match:
                if current_gpu:
                    gpus.append(current_gpu)

                model_match = re.search(r"controller:\s*(.*)", line)
                model = model_match.group(1).strip() if model_match else "Unknown"

                current_gpu = {
                    "model": model,
                    "vendor_id": vga_match.group(1),
                    "device_id": vga_match.group(2),
                    "details": {},
                }
            elif current_gpu and line.startswith("\t"):
                key_value_match = re.match(r"\s*(.*?):\s*(.*)", line)
                if key_value_match:
                    key = key_value_match.group(1).strip().lower().replace(" ", "_")
                    value = key_value_match.group(2).strip()
                    current_gpu["details"][key] = value

        if current_gpu:
            gpus.append(current_gpu)

        return gpus if gpus else None
