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

import dataclasses
import logging
from typing import Any, Dict

from tinel.system import LinuxSystemInterface

from .bios_analyzer import BIOSAnalyzer
from .cpu_analyzer import CPUAnalyzer
from .graphics_analyzer import GraphicsAnalyzer
from .memory_analyzer import MemoryAnalyzer
from .models import HardwareInfo, PCIInfo, USBInfo
from .motherboard_analyzer import MotherboardAnalyzer
from .network_analyzer import NetworkAnalyzer
from .pci_analyzer import PCIAnalyzer
from .storage_analyzer import StorageAnalyzer
from .system_analyzer import SystemAnalyzer
from .usb_analyzer import USBAnalyzer

__all__ = [
    "BIOSAnalyzer",
    "CPUAnalyzer",
    "GraphicsAnalyzer",
    "HardwareInfo",
    "MemoryAnalyzer",
    "MotherboardAnalyzer",
    "NetworkAnalyzer",
    "PCIAnalyzer",
    "PCIInfo",
    "StorageAnalyzer",
    "SystemAnalyzer",
    "USBAnalyzer",
    "USBInfo",
    "get_all_hardware_info",
]


def get_all_hardware_info() -> Dict[str, Any]:
    """Gathers and aggregates hardware information from all available analyzers.

    This function instantiates each hardware analyzer, calls its data-gathering
    methods, and aggregates the results into a hierarchical structure that
    mimics the output of `lshw`.

    Returns:
        A dictionary containing aggregated hardware information from all
        analyzers, structured to be similar to `lshw`.
    """
    logger = logging.getLogger(__name__)
    system_interface = LinuxSystemInterface()

    # Analyzers
    cpu_analyzer = CPUAnalyzer(system_interface)
    mem_analyzer = MemoryAnalyzer(system_interface)
    storage_analyzer = StorageAnalyzer(system_interface)
    gfx_analyzer = GraphicsAnalyzer(system_interface)
    net_analyzer = NetworkAnalyzer(system_interface)
    pci_analyzer = PCIAnalyzer(system_interface)
    usb_analyzer = USBAnalyzer(system_interface)
    sys_analyzer = SystemAnalyzer(system_interface)
    bios_analyzer = BIOSAnalyzer(system_interface)
    mb_analyzer = MotherboardAnalyzer(system_interface)

    # Build the core node
    core_children = []
    try:
        cpu_info = cpu_analyzer.get_cpu_info()
        cpu_dict = dataclasses.asdict(cpu_info)
        cpu_dict["id"] = "cpu"
        core_children.append(cpu_dict)
    except Exception as e:
        logger.error(f"Failed to get CPU info: {e}", exc_info=True)

    try:
        bios_info = bios_analyzer.get_bios_info()
        bios_dict = dataclasses.asdict(bios_info)
        bios_dict["id"] = "firmware"
        core_children.append(bios_dict)
    except Exception as e:
        logger.error(f"Failed to get BIOS info: {e}", exc_info=True)

    try:
        memory_info = mem_analyzer.get_memory_info()
        memory_dict = dataclasses.asdict(memory_info)
        memory_dict["id"] = "memory"
        core_children.append(memory_dict)
    except Exception as e:
        logger.error(f"Failed to get memory info: {e}", exc_info=True)

    pci_root = {"id": "pci", "class": "bridge", "children": []}
    try:
        pci_info = pci_analyzer.get_pci_info()
        if pci_info.devices:
            pci_root["children"].extend(
                [dataclasses.asdict(dev) for dev in pci_info.devices]
            )
    except Exception as e:
        logger.error(f"Failed to get PCI info: {e}", exc_info=True)

    try:
        graphics_info = gfx_analyzer.get_graphics_info()
        if graphics_info and graphics_info.gpus:
            # Graphics cards are PCI devices, so they should be children of the PCI bus
            pci_root["children"].append(dataclasses.asdict(graphics_info))
    except Exception as e:
        logger.error(f"Failed to get graphics info: {e}", exc_info=True)

    try:
        storage_info = storage_analyzer.get_storage_info()
        if storage_info.block_devices:
            for i, dev in enumerate(storage_info.block_devices):
                dev_dict = dataclasses.asdict(dev)
                dev_dict["id"] = f"disk:{i}"
                core_children.append(dev_dict)
    except Exception as e:
        logger.error(f"Failed to get storage info: {e}", exc_info=True)

    try:
        network_info = net_analyzer.get_network_info()
        if network_info.interfaces:
            for i, iface in enumerate(network_info.interfaces):
                iface_dict = dataclasses.asdict(iface)
                iface_dict["id"] = f"network:{i}"
                core_children.append(iface_dict)
    except Exception as e:
        logger.error(f"Failed to get network info: {e}", exc_info=True)

    try:
        usb_info = usb_analyzer.get_usb_info()
        if usb_info.devices:
            core_children.append(
                {
                    "id": "usb",
                    "class": "bus",
                    "children": [
                        dataclasses.asdict(dev) for dev in usb_info.devices
                    ],
                }
            )
    except Exception as e:
        logger.error(f"Failed to get USB info: {e}", exc_info=True)

    if pci_root["children"]:
        core_children.append(pci_root)

    # Build the main system node
    system_info = sys_analyzer.get_system_info()
    motherboard_info = mb_analyzer.get_motherboard_info()

    lshw_dict = {
        "id": system_info.product or "system",
        "class": "system",
        "description": "Computer",
        "children": [
            {
                "id": "core",
                "class": "bus",
                "description": "Motherboard",
                "product": motherboard_info.product,
                "vendor": motherboard_info.vendor,
                "version": motherboard_info.version,
                "serial": motherboard_info.serial,
                "children": core_children,
            }
        ],
    }

    return lshw_dict