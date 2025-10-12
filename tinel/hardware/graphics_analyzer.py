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
import logging
import functools
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class GraphicsAnalyzer:
    """Analyzer for graphics hardware (GPUs)."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize graphics analyzer.

        Args:
            system_interface: System interface for command execution.
        """
        self.system = system_interface or LinuxSystemInterface()
        self.logger = logging.getLogger(__name__)

    @functools.lru_cache(maxsize=None)
    def get_graphics_info(self) -> Dict[str, Any]:
        """Get comprehensive graphics hardware information.

        This method attempts to use vendor-specific tools first (`nvidia-smi`, `rocm-smi`)
        and falls back to a generic tool (`lspci`) if they are not available.

        Returns:
            A dictionary containing detailed graphics hardware information.
        """
        info: Dict[str, Any] = {}

        # Try NVIDIA's tool first
        nvidia_info = self._get_nvidia_info()
        if nvidia_info:
            info['gpus'] = nvidia_info
            info['source'] = 'nvidia-smi'
            return info

        # Try AMD's tool next
        amd_info = self._get_amd_info()
        if amd_info:
            info['gpus'] = amd_info
            info['source'] = 'rocm-smi'
            return info

        # Fallback to lspci
        lspci_info = self._get_lspci_info()
        if lspci_info:
            info['gpus'] = lspci_info
            info['source'] = 'lspci'
            return info

        self.logger.warning("No GPU information could be gathered.")
        return info

    def _get_nvidia_info(self) -> Optional[List[Dict[str, Any]]]:
        """Get GPU info using nvidia-smi."""
        command = [
            'nvidia-smi',
            '--query-gpu=index,name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu',
            '--format=csv,noheader,nounits'
        ]
        result = self.system.run_command(command)

        if not result.success:
            self.logger.info("'nvidia-smi' command failed or not found.")
            return None

        gpus = []
        for line in result.stdout.strip().split('\n'):
            try:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) != 8:
                    continue
                gpus.append({
                    'index': int(parts[0]),
                    'model': parts[1],
                    'driver_version': parts[2],
                    'memory_total_mb': int(parts[3]),
                    'memory_used_mb': int(parts[4]),
                    'memory_free_mb': int(parts[5]),
                    'utilization_percent': int(parts[6]),
                    'temperature_celsius': int(parts[7]),
                })
            except (ValueError, IndexError) as e:
                self.logger.warning("Failed to parse nvidia-smi output line: '%s'. Error: %s", line, e)

        return gpus if gpus else None

    def _get_amd_info(self) -> Optional[List[Dict[str, Any]]]:
        """Get GPU info using rocm-smi."""
        # rocm-smi is not installed in the test environment, so this is a placeholder.
        # In a real environment, this would parse the output of `rocm-smi`.
        # For example, `rocm-smi --showproductname --showmeminfo vram --showdriverversion --showtemp --showuse`
        result = self.system.run_command(['rocm-smi', '--showallinfo']) # A bit generic for a placeholder

        if not result.success:
            self.logger.info("'rocm-smi' command failed or not found.")
            return None

        # Placeholder for parsing logic
        # Since I cannot run the command, I will assume a hypothetical output structure.
        # This part would need to be implemented and tested on a system with an AMD GPU and rocm-smi.
        gpus = [{'model': 'AMD GPU (rocm-smi placeholder)', 'error': 'Parsing not implemented'}]
        self.logger.info("rocm-smi parsing is not yet implemented.")

        return gpus

    def _get_lspci_info(self) -> Optional[List[Dict[str, Any]]]:
        """Get basic GPU info using lspci as a fallback."""
        result = self.system.run_command(['lspci', '-vnn'])

        if not result.success:
            self.logger.warning("'lspci' command failed or not found.")
            return None

        gpus = []
        current_gpu = None

        for line in result.stdout.strip().split('\n'):
            vga_match = re.search(r'VGA compatible controller.*\[(\w{4}):(\w{4})\]', line)
            if vga_match:
                if current_gpu:
                    gpus.append(current_gpu)

                model_match = re.search(r'controller:\s*(.*)', line)
                model = model_match.group(1).strip() if model_match else 'Unknown'

                current_gpu = {
                    'model': model,
                    'vendor_id': vga_match.group(1),
                    'device_id': vga_match.group(2),
                    'details': {}
                }
            elif current_gpu and line.startswith('\t'):
                key_value_match = re.match(r'\s*(.*?):\s*(.*)', line)
                if key_value_match:
                    key = key_value_match.group(1).strip().lower().replace(' ', '_')
                    value = key_value_match.group(2).strip()
                    current_gpu['details'][key] = value

        if current_gpu:
            gpus.append(current_gpu)

        return gpus if gpus else None