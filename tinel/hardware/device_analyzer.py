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
from .models import PCIInfo, USBInfo
from .motherboard_analyzer import MotherboardAnalyzer
from .network_analyzer import NetworkAnalyzer
from .pci_analyzer import PCIAnalyzer
from .storage_analyzer import StorageAnalyzer
from .usb_analyzer import USBAnalyzer

"""This module provides a unified analyzer for all hardware components.

It includes the `DeviceAnalyzer` class, which acts as a facade for all other
hardware analyzers. This class simplifies the process of gathering
comprehensive hardware information by providing a single point of entry.
"""


class DeviceAnalyzer:
    """A unified analyzer for collecting information about all hardware components.

    This class acts as a high-level facade, aggregating data from various
    specialized analyzers (e.g., `CPUAnalyzer`, `MemoryAnalyzer`) to provide a
    complete picture of the system's hardware.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
                          If not provided, a `LinuxSystemInterface` is used.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the DeviceAnalyzer and all its sub-analyzers.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()
        self.cpu_analyzer = CPUAnalyzer(self.system)
        self.memory_analyzer = MemoryAnalyzer(self.system)
        self.storage_analyzer = StorageAnalyzer(self.system)
        self.network_analyzer = NetworkAnalyzer(self.system)
        self.graphics_analyzer = GraphicsAnalyzer(self.system)
        self.motherboard_analyzer = MotherboardAnalyzer(self.system)
        self.pci_analyzer = PCIAnalyzer(self.system)
        self.usb_analyzer = USBAnalyzer(self.system)

    def get_all_hardware_info(self) -> HardwareInfo:
        """Gathers and returns comprehensive information about all hardware components.

        This method orchestrates the collection of data from all sub-analyzers
        and aggregates it into a single `HardwareInfo` object.

        Returns:
            A `HardwareInfo` object containing a complete overview of the
            system's hardware.
        """
        return HardwareInfo(
            cpu=self.get_cpu_info(),
            memory=self.get_memory_info(),
            storage=self.get_storage_info(),
            network=self.get_network_info(),
            graphics=self.get_graphics_info(),
            motherboard=self.get_motherboard_info(),
            pci=self.get_pci_devices(),
            usb=self.get_usb_devices(),
        )

    def get_cpu_info(self) -> Dict[str, Any]:
        """Retrieves detailed CPU information.

        Returns:
            A dictionary containing comprehensive CPU details.
        """
        return self.cpu_analyzer.get_cpu_info()

    def get_memory_info(self) -> Dict[str, Any]:
        """Retrieves detailed memory information.

        Returns:
            A dictionary containing comprehensive memory details.
        """
        return self.memory_analyzer.get_memory_info()

    def get_storage_info(self) -> Dict[str, Any]:
        """Retrieves detailed storage information.

        Returns:
            A dictionary containing comprehensive storage details.
        """
        return self.storage_analyzer.get_storage_info()

    def get_network_info(self) -> Dict[str, Any]:
        """Retrieves detailed network information.

        Returns:
            A dictionary containing comprehensive network details.
        """
        return self.network_analyzer.get_network_info()

    def get_graphics_info(self) -> Dict[str, Any]:
        """Retrieves detailed graphics information.

        Returns:
            A dictionary containing comprehensive graphics details.
        """
        return self.graphics_analyzer.get_graphics_info()

    def get_pci_devices(self) -> "PCIInfo":
        """Retrieves information about PCI devices.

        Returns:
            A `PCIInfo` object containing details about all PCI devices.
        """
        return self.pci_analyzer.get_pci_info()

    def get_usb_devices(self) -> "USBInfo":
        """Retrieve information about USB devices.

        Returns:
            A `USBInfo` object containing details about all USB devices.
        """
        return self.usb_analyzer.get_usb_info()

    def get_motherboard_info(self) -> Dict[str, Any]:
        """Retrieves detailed motherboard information.

        Returns:
            A dictionary containing comprehensive motherboard details.
        """
        return self.motherboard_analyzer.get_motherboard_info()
