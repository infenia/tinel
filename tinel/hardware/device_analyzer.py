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
from .cpu_analyzer import CPUAnalyzer
from .models import HardwareInfo, PCIInfo, USBInfo
from .pci_analyzer import PCIAnalyzer
from .usb_analyzer import USBAnalyzer


class DeviceAnalyzer:
    """Unified device analyzer for all hardware components."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize device analyzer.

        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        self.cpu_analyzer = CPUAnalyzer(self.system)
        self.pci_analyzer = PCIAnalyzer(self.system)
        self.usb_analyzer = USBAnalyzer(self.system)

    def get_all_hardware_info(self) -> HardwareInfo:
        """Get comprehensive hardware information.

        Returns:
            HardwareInfo object containing all hardware information
        """
        return HardwareInfo(
            cpu=self.get_cpu_info(),
            memory=self.get_memory_info(),
            storage=self.get_storage_info(),
            pci=self.get_pci_devices(),
            usb=self.get_usb_devices(),
        )

    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information.

        Returns:
            Dictionary containing CPU information
        """
        return self.cpu_analyzer.get_cpu_info()

    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information.

        Returns:
            Dictionary containing memory information
        """
        # TODO: Implement memory information gathering
        return {"memory": "Not implemented yet"}

    def get_storage_info(self) -> Dict[str, Any]:
        """Get detailed storage information.

        Returns:
            Dictionary containing storage information
        """
        # TODO: Implement storage information gathering
        return {"storage": "Not implemented yet"}

    def get_pci_devices(self) -> "PCIInfo":
        """Get PCI device information.

        Returns:
            A PCIInfo object containing PCI device information.
        """
        return self.pci_analyzer.get_pci_info()

    def get_usb_devices(self) -> "USBInfo":
        """Get USB device information.

        Returns:
            A USBInfo object containing USB device information.
        """
        return self.usb_analyzer.get_usb_info()
