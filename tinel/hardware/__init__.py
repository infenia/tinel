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


def get_all_hardware_info() -> Dict[str, Any]:
    """Gathers and aggregates hardware information from all available analyzers.

    This function instantiates each hardware analyzer, calls its data-gathering
    methods, and aggregates the results. It is designed to be resilient,
    handling exceptions from individual analyzers gracefully by logging the
    error and including an error message in the final report.

    Returns:
        A dictionary containing aggregated hardware information from all
        analyzers. Each key corresponds to a hardware component (e.g., 'cpu',
        'memory'), and its value is a dictionary of the collected data.
    """
    logger = logging.getLogger(__name__)
    info = HardwareInfo()

    # List of analyzer instances and the corresponding attribute name in HardwareInfo
    analyzers = [
        (CPUAnalyzer(), "cpu"),
        (MemoryAnalyzer(), "memory"),
        (StorageAnalyzer(), "storage"),
        (GraphicsAnalyzer(), "graphics"),
        (NetworkAnalyzer(), "network"),
        (PCIAnalyzer(), "pci"),
        (USBAnalyzer(), "usb"),
    ]

    for analyzer, component_name in analyzers:
        try:
            # The method name is consistently get_<component>_info
            method_name = f"get_{component_name}_info"
            data = getattr(analyzer, method_name)()
            setattr(info, component_name, data)
        except Exception as e:
            error_msg = f"Failed to get {component_name} info: {e}"
            logger.error(error_msg)
            # Set an error message in the corresponding field
            setattr(info, component_name, {"error": error_msg})

    return dataclasses.asdict(info)
