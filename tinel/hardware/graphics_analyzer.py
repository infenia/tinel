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

import logging
import re
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface

"""This module provides an analyzer for graphics hardware (GPUs).

It includes the `GraphicsAnalyzer` class, which is responsible for detecting
and gathering information about the system's graphics cards. The analyzer
employs a fallback mechanism, first attempting to use vendor-specific tools
like `nvidia-smi` and `rocm-smi`, and then resorting to the generic `lspci`
command if necessary.
"""


from tinel.hardware.models import GPU, GraphicsInfo


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
        self._graphics_info_cache: Optional[GraphicsInfo] = None

    def get_graphics_info(self) -> GraphicsInfo:
        """Retrieves comprehensive information about the graphics hardware.

        This method serves as the primary entry point for gathering graphics
        card data. It employs a fallback strategy, attempting to use
        vendor-specific tools like `nvidia-smi` and `rocm-smi` before
        resorting to the more generic `lspci` command. The result is cached
        to improve performance on subsequent calls.

        Returns:
            A `GraphicsInfo` object containing detailed graphics hardware
            information.
        """
        if self._graphics_info_cache is not None:
            return self._graphics_info_cache

        nvidia_info = self._get_nvidia_info()
        if nvidia_info:
            info = GraphicsInfo(gpus=nvidia_info, source="nvidia-smi")
            self._graphics_info_cache = info
            return info

        amd_info = self._get_amd_info()
        if amd_info:
            info = GraphicsInfo(gpus=amd_info, source="rocm-smi")
            self._graphics_info_cache = info
            return info

        lspci_info = self._get_lspci_info()
        if lspci_info:
            info = GraphicsInfo(gpus=lspci_info, source="lspci")
            self._graphics_info_cache = info
            return info

        self.logger.warning("No GPU information could be gathered.")
        info = GraphicsInfo()
        self._graphics_info_cache = info
        return info

    def _get_nvidia_info(self) -> Optional[List[GPU]]:
        """Retrieves GPU information using the `nvidia-smi` command."""
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
                    GPU(
                        index=int(parts[0]),
                        model=parts[1],
                        driver_version=parts[2],
                        memory_total_mb=int(parts[3]),
                        memory_used_mb=int(parts[4]),
                        memory_free_mb=int(parts[5]),
                        utilization_percent=int(parts[6]),
                        temperature_celsius=int(parts[7]),
                    )
                )
            except (ValueError, IndexError) as e:
                self.logger.warning(
                    "Failed to parse nvidia-smi output line: '%s'. Error: %s", line, e
                )

        return gpus if gpus else None

    def _get_amd_info(self) -> Optional[List[GPU]]:
        """Retrieves GPU information using the `rocm-smi` command."""
        result = self.system.run_command(["rocm-smi", "--showallinfo"])
        if not result.success:
            self.logger.info("'rocm-smi' command failed or not found.")
            return None

        gpus = [
            GPU(
                model="AMD GPU (rocm-smi placeholder)",
                details={"error": "Parsing not implemented"},
            )
        ]
        self.logger.info("rocm-smi parsing is not yet implemented.")
        return gpus

    def _get_lspci_info(self) -> Optional[List[GPU]]:
        """Retrieves basic GPU information using the `lspci` command."""
        result = self.system.run_command(["lspci", "-vnn"])
        if not result.success:
            self.logger.warning("'lspci' command failed or not found.")
            return None

        return self._parse_lspci_output(result.stdout)

    def _parse_lspci_output(self, lspci_output: str) -> List[GPU]:
        gpus: List[GPU] = []
        current_gpu: Optional[GPU] = None

        for line in lspci_output.strip().split("\n"):
            vga_match = re.search(
                r"VGA compatible controller.*\[(\w{4}):(\w{4})\]", line
            )
            if vga_match:
                if current_gpu:
                    gpus.append(current_gpu)

                model_match = re.search(r"controller:\s*(.*(?=\s\[))|:\s(.*)(?=\s\[)", line)
                model = "Unknown"
                if model_match:
                    model = (model_match.group(1) or model_match.group(2) or "Unknown").strip()

                current_gpu = GPU(
                    model=model,
                    vendor_id=vga_match.group(1),
                    device_id=vga_match.group(2),
                    details={},
                )
            elif current_gpu and line.startswith("\t"):
                key_value_match = re.match(r"\s*(.*?):\s*(.*)", line)
                if key_value_match:
                    key = key_value_match.group(1).strip().lower().replace(" ", "_")
                    value = key_value_match.group(2).strip()
                    if current_gpu.details is not None:
                        current_gpu.details[key] = value
                elif current_gpu.details is not None:
                    current_gpu.details.setdefault("misc", []).append(line.strip())

        if current_gpu:
            gpus.append(current_gpu)

        return gpus