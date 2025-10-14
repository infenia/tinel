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

"""This module defines the data models for the hardware components.

It includes dataclasses for representing structured information about PCI and
USB devices, as well as a comprehensive `HardwareInfo` dataclass that
aggregates all hardware data into a single object. These models ensure a
consistent and predictable data structure throughout the application.
"""

import dataclasses
from typing import Any, Dict, Optional


@dataclasses.dataclass
class MemoryDeviceDetails:
    """Represents the detailed attributes of a physical memory device.

    This dataclass provides a structured representation of the information
    retrieved from `dmidecode` for a single memory module.

    Attributes:
        size: The size of the memory device (e.g., "8 GB").
        form_factor: The physical form factor (e.g., "DIMM").
        device_type: The type of memory (e.g., "DDR4").
        speed: The configured speed of the memory module (e.g., "2400 MT/s").
        manufacturer: The name of the manufacturer.
        serial_number: The serial number of the module.
        part_number: The part number of the module.
        attributes: Any additional attributes of the memory device.
        raw_details: A dictionary containing all raw key-value pairs from
                     `dmidecode`.
    """

    size: Optional[str] = None
    form_factor: Optional[str] = None
    device_type: Optional[str] = None
    speed: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    part_number: Optional[str] = None
    attributes: Optional[str] = None
    raw_details: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class PCIInfo:
    """Represents information about PCI devices.

    Attributes:
        devices: A list of dictionaries, where each dictionary contains
                 details about a single PCI device.
    """

    devices: list = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class USBInfo:
    """Represents information about USB devices.

    Attributes:
        tree: A dictionary representing the hierarchical structure of USB
              devices connected to the system.
    """

    tree: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class HardwareInfo:
    """A comprehensive data model for all hardware information.

    This dataclass serves as the central container for all hardware data
    collected by the various analyzers. It provides a structured and
    consistent way to access information about different hardware components.

    Attributes:
        cpu: A dictionary containing detailed CPU information.
        memory: A dictionary containing detailed memory information.
        storage: A dictionary containing detailed storage information.
        motherboard: A dictionary containing detailed motherboard information.
        graphics: A dictionary containing detailed graphics information.
        network: A dictionary containing detailed network information.
        pci: A `PCIInfo` object containing information about PCI devices.
        usb: A `USBInfo` object containing information about USB devices.
    """

    cpu: Dict[str, Any] = dataclasses.field(default_factory=dict)
    memory: Dict[str, Any] = dataclasses.field(default_factory=dict)
    storage: Dict[str, Any] = dataclasses.field(default_factory=dict)
    motherboard: Dict[str, Any] = dataclasses.field(default_factory=dict)
    graphics: Dict[str, Any] = dataclasses.field(default_factory=dict)
    network: Dict[str, Any] = dataclasses.field(default_factory=dict)
    pci: "PCIInfo" = dataclasses.field(default_factory=PCIInfo)
    usb: "USBInfo" = dataclasses.field(default_factory=USBInfo)
