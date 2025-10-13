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

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface
from . import HardwareInfo
from .cpu_analyzer import CPUAnalyzer
from .graphics_analyzer import GraphicsAnalyzer
from .memory_analyzer import MemoryAnalyzer
from .network_analyzer import NetworkAnalyzer


class DeviceAnalyzer:
    """Unified device analyzer for all hardware components."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize device analyzer.

        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        self.cpu_analyzer = CPUAnalyzer(self.system)
        self.memory_analyzer = MemoryAnalyzer(self.system)
        self.network_analyzer = NetworkAnalyzer(self.system)
        self.graphics_analyzer = GraphicsAnalyzer(self.system)

    def get_all_hardware_info(self) -> HardwareInfo:
        """Get comprehensive hardware information.

        Returns:
            HardwareInfo object containing all hardware information
        """
        return HardwareInfo(
            cpu=self.get_cpu_info(),
            memory=self.get_memory_info(),
            disks=self.get_storage_info(),
            network=self.get_network_info(),
            graphics=self.get_graphics_info(),
            motherboard=self.get_motherboard_info(),
        )

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information."""
        return self.cpu_analyzer.get_cpu_info()

    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information."""
        return self.memory_analyzer.get_memory_info()

    def get_storage_info(self) -> Dict[str, Any]:
        """Get detailed storage information."""
        # TODO: Implement storage information gathering
        return {"storage": "Not implemented yet"}

    def get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        return self.network_analyzer.get_network_info()

    def get_graphics_info(self) -> Dict[str, Any]:
        """Get graphics information."""
        return self.graphics_analyzer.get_graphics_info()

    def get_motherboard_info(self) -> Dict[str, Any]:
        """Get motherboard information."""
        # TODO: Implement motherboard information gathering
        return {"motherboard": "Not implemented yet"}
