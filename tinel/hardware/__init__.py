#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware information module for Tinel.

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

from .cpu_analyzer import CPUAnalyzer
from .graphics_analyzer import GraphicsAnalyzer
from .memory_analyzer import MemoryAnalyzer
from .models import HardwareInfo, PCIInfo, USBInfo
from .network_analyzer import NetworkAnalyzer
from .pci_analyzer import PCIAnalyzer
from .storage_analyzer import StorageAnalyzer
from .usb_analyzer import USBAnalyzer

__all__ = [
    "HardwareInfo",
    "CPUAnalyzer",
    "NetworkAnalyzer",
    "GraphicsAnalyzer",
    "MemoryAnalyzer",
    "StorageAnalyzer",
    "PCIAnalyzer",
    "USBAnalyzer",
    "PCIInfo",
    "USBInfo",
    "get_all_hardware_info",
]


def get_all_hardware_info() -> HardwareInfo:
    """Gathers and aggregates hardware information from all available analyzers.

        This function instantiates each of the hardware analyzer classes, calls
        their respective data-gathering methods, and compiles the results into a
        single `HardwareInfo` object. It serves as the main entry point for
    t
        collecting a comprehensive overview of the system's hardware.

        Returns:
            A `HardwareInfo` dataclass instance containing detailed information
            about all major hardware components.
    """
    cpu_analyzer = CPUAnalyzer()
    memory_analyzer = MemoryAnalyzer()
    storage_analyzer = StorageAnalyzer()
    graphics_analyzer = GraphicsAnalyzer()
    network_analyzer = NetworkAnalyzer()
    pci_analyzer = PCIAnalyzer()
    usb_analyzer = USBAnalyzer()

    return HardwareInfo(
        cpu=cpu_analyzer.get_cpu_info(),
        memory=memory_analyzer.get_memory_info(),
        storage=storage_analyzer.get_storage_info(),
        graphics=graphics_analyzer.get_graphics_info(),
        network=network_analyzer.get_network_info(),
        pci=pci_analyzer.get_pci_info(),
        usb=usb_analyzer.get_usb_info(),
    )
