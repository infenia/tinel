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

import dataclasses
from typing import Any, Dict, List, Optional

"""This module defines the data models for the hardware components.

It includes dataclasses for representing structured information about PCI and
USB devices, as well as a comprehensive `HardwareInfo` dataclass that
aggregates all hardware data into a single object. These models ensure a
consistent and predictable data structure throughout the application.
"""


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
    asset_tag: Optional[str] = None
    part_number: Optional[str] = None
    attributes: Optional[str] = None
    configured_clock_speed: Optional[str] = None
    configured_voltage: Optional[str] = None
    min_voltage: Optional[str] = None
    max_voltage: Optional[str] = None
    raw_details: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class BIOSInfo:
    """Represents BIOS/firmware information.
    Attributes:
        vendor: The vendor of the BIOS.
        version: The version of the BIOS.
        date: The release date of the BIOS.
        size: The size of the BIOS ROM.
        capabilities: A dictionary of BIOS capabilities.
    """

    vendor: Optional[str] = None
    version: Optional[str] = None
    date: Optional[str] = None
    size: Optional[str] = None
    capabilities: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class MotherboardInfo:
    """Represents motherboard information.
    Attributes:
        product: The product name of the motherboard.
        vendor: The vendor of the motherboard.
        version: The version of the motherboard.
        serial: The serial number of the motherboard.
        asset_tag: The asset tag of the motherboard.
        physid: The physical ID of the motherboard.
    """

    product: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    serial: Optional[str] = None
    asset_tag: Optional[str] = None
    physid: Optional[str] = None


@dataclasses.dataclass
class CPUInfo:
    """Represents CPU information."""

    product: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    width: Optional[int] = None
    architecture: Optional[str] = None
    cpu_op_modes: Optional[str] = None
    byte_order: Optional[str] = None
    lscpu_flags: List[str] = dataclasses.field(default_factory=list)
    cpu_flags: List[str] = dataclasses.field(default_factory=list)
    security_features: Dict[str, bool] = dataclasses.field(default_factory=dict)
    performance_features: Dict[str, bool] = dataclasses.field(default_factory=dict)
    virtualization_features: Dict[str, bool] = dataclasses.field(default_factory=dict)
    vulnerabilities: Dict[str, str] = dataclasses.field(default_factory=dict)
    topology: Dict[str, Any] = dataclasses.field(default_factory=dict)
    cache: Dict[str, Any] = dataclasses.field(default_factory=dict)
    optimization_recommendations: List[Dict[str, Any]] = dataclasses.field(
        default_factory=list
    )
    performance_analysis: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SystemInfo:
    """Represents top-level system information.
    Attributes:
        product: The product name of the system.
        vendor: The vendor of the system.
        version: The version of the system.
        serial: The serial number of the system.
        uuid: The UUID of the system.
        sku_number: The SKU number of the system.
        family: The family of the system.
        width: The width of the system (e.g., 64).
        capabilities: A dictionary of system capabilities.
    """

    product: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    serial: Optional[str] = None
    uuid: Optional[str] = None
    sku_number: Optional[str] = None
    family: Optional[str] = None
    width: Optional[int] = None
    capabilities: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class PCIDevice:
    """Represents a single PCI device."""

    slot: Optional[str] = None
    description: Optional[str] = None
    vendor_id: Optional[str] = None
    device_id: Optional[str] = None
    driver: Optional[str] = None
    width: Optional[int] = None
    details: Dict[str, Any] = dataclasses.field(default_factory=dict)
    subsystem: Optional[str] = None
    physical_slot: Optional[str] = None
    flags: Optional[str] = None
    memory: List[str] = dataclasses.field(default_factory=list)
    i_o_ports: List[str] = dataclasses.field(default_factory=list)
    expansion_rom: Optional[str] = None
    capabilities: List[str] = dataclasses.field(default_factory=list)
    kernel_driver_in_use: Optional[str] = None
    kernel_modules: Optional[str] = None


@dataclasses.dataclass
class PCIInfo:
    """Represents information about PCI devices.

    Attributes:
        devices: A list of `PCIDevice` objects, where each object contains
                 details about a single PCI device.
    """

    devices: List[PCIDevice] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class MemoryInfo:
    """Represents the memory information of the system."""

    total_memory_bytes: Optional[int] = None
    available_memory_bytes: Optional[int] = None
    used_memory_bytes: Optional[int] = None
    memory_usage_percent: Optional[float] = None
    total_swap_bytes: Optional[int] = None
    used_swap_bytes: Optional[int] = None
    free_swap_bytes: Optional[int] = None
    swap_usage_percent: Optional[float] = None
    memory_devices: List[MemoryDeviceDetails] = dataclasses.field(default_factory=list)
    performance_analysis: Dict[str, Any] = dataclasses.field(default_factory=dict)
    psutil_error: Optional[str] = None
    dmidecode_error: Optional[str] = None
    dmidecode_parse_error: Optional[str] = None
    size: Optional[int] = None
    units: Optional[str] = None


@dataclasses.dataclass
class USBDevice:
    """Represents a single USB device."""

    bus: Optional[str] = None
    port: Optional[str] = None
    device_id: Optional[str] = None
    device_class: Optional[str] = None
    driver: Optional[str] = None
    speed: Optional[str] = None
    vendor_id: Optional[str] = None
    product_id: Optional[str] = None
    manufacturer: Optional[str] = None
    product: Optional[str] = None
    interface: Optional[str] = None
    physid: Optional[str] = None
    version: Optional[str] = None
    capabilities: Dict[str, Any] = dataclasses.field(default_factory=dict)
    configuration: Dict[str, Any] = dataclasses.field(default_factory=dict)
    children: List["USBDevice"] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class USBInfo:
    """Represents information about USB devices.

    Attributes:
        devices: A list of `USBDevice` objects representing the root hubs.
    """

    devices: List[USBDevice] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class BlockDevice:
    """Represents a block device and its partitions."""

    name: Optional[str] = None
    size: Optional[int] = None
    type: Optional[str] = None
    mountpoint: Optional[str] = None
    fstype: Optional[str] = None
    model: Optional[str] = None
    path: Optional[str] = None
    businfo: Optional[str] = None
    logicalname: Optional[str] = None
    units: Optional[str] = None
    health: Dict[str, Any] = dataclasses.field(default_factory=dict)
    children: List["BlockDevice"] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class DiskUsage:
    """Represents disk usage for a filesystem."""

    filesystem: Optional[str] = None
    size: Optional[str] = None
    used: Optional[str] = None
    available: Optional[str] = None
    use_percent: Optional[str] = None
    mounted_on: Optional[str] = None


@dataclasses.dataclass
class InodeUsage:
    """Represents inode usage for a filesystem."""

    filesystem: Optional[str] = None
    inodes: Optional[str] = None
    iused: Optional[str] = None
    ifree: Optional[str] = None
    iuse_percent: Optional[str] = None
    mounted_on: Optional[str] = None


@dataclasses.dataclass
class StorageInfo:
    """Represents all storage-related information."""

    block_devices: List[BlockDevice] = dataclasses.field(default_factory=list)
    disk_usage: List[DiskUsage] = dataclasses.field(default_factory=list)
    inode_usage: List[InodeUsage] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class NetworkInterface:
    """Represents a network interface."""

    name: Optional[str] = None
    state: Optional[str] = None
    mac: Optional[str] = None
    addresses: List[Dict[str, str]] = dataclasses.field(default_factory=list)
    type: Optional[str] = None
    speed: Optional[int] = None
    duplex: Optional[str] = None
    mtu: Optional[int] = None
    carrier: Optional[int] = None
    operstate: Optional[str] = None
    address: Optional[str] = None
    businfo: Optional[str] = None
    driverversion: Optional[str] = None
    flags: Optional[int] = None
    decoded_flags: List[str] = dataclasses.field(default_factory=list)
    statistics: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class WirelessInterface:
    """Represents a wireless network interface."""

    name: Optional[str] = None
    essid: Optional[str] = None
    mode: Optional[str] = None
    frequency: Optional[str] = None
    access_point: Optional[str] = None
    bit_rate: Optional[str] = None
    signal_level: Optional[str] = None


@dataclasses.dataclass
class DriverInfo:
    """Represents network driver information."""

    interface: Optional[str] = None
    driver: Optional[str] = None
    driver_details: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class PerformanceMetrics:
    """Represents network performance metrics."""

    netstat_statistics: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    psutil_io_counters: Dict[str, Any] = dataclasses.field(default_factory=dict)
    ethtool_statistics: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class NetworkInfo:
    """Represents all network-related information."""

    interfaces: List[NetworkInterface] = dataclasses.field(default_factory=list)
    detailed_interfaces: List[NetworkInterface] = dataclasses.field(
        default_factory=list
    )
    wireless_interfaces: List[WirelessInterface] = dataclasses.field(
        default_factory=list
    )
    driver_info: List[DriverInfo] = dataclasses.field(default_factory=list)
    performance_metrics: PerformanceMetrics = dataclasses.field(
        default_factory=PerformanceMetrics
    )
    performance_capabilities: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class GPU:
    """Represents a single GPU."""

    index: Optional[int] = None
    model: Optional[str] = None
    vendor_id: Optional[str] = None
    device_id: Optional[str] = None
    driver_version: Optional[str] = None
    memory_total_mb: Optional[int] = None
    memory_used_mb: Optional[int] = None
    memory_free_mb: Optional[int] = None
    utilization_percent: Optional[int] = None
    temperature_celsius: Optional[int] = None
    details: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class GraphicsInfo:
    """Represents all graphics-related information."""

    gpus: List[GPU] = dataclasses.field(default_factory=list)
    source: Optional[str] = None


@dataclasses.dataclass
class HardwareInfo:
    """A comprehensive data model for all hardware information.

    This dataclass serves as the central container for all hardware data
    collected by the various analyzers. It provides a structured and
    consistent way to access information about different hardware components.

    Attributes:
        bios: A `BIOSInfo` object containing BIOS/firmware information.
        cpu: A dictionary containing detailed CPU information.
        graphics: A dictionary containing detailed graphics information.
        memory: A dictionary containing detailed memory information.
        motherboard: A `MotherboardInfo` object containing motherboard information.
        network: A dictionary containing detailed network information.
        pci: A `PCIInfo` object containing information about PCI devices.
        storage: A dictionary containing detailed storage information.
        system: A `SystemInfo` object containing top-level system information.
        usb: A `USBInfo` object containing information about USB devices.
    """

    bios: "BIOSInfo" = dataclasses.field(default_factory=BIOSInfo)
    cpu: Dict[str, Any] = dataclasses.field(default_factory=dict)
    graphics: Dict[str, Any] = dataclasses.field(default_factory=dict)
    memory: Dict[str, Any] = dataclasses.field(default_factory=dict)
    motherboard: "MotherboardInfo" = dataclasses.field(
        default_factory=MotherboardInfo
    )
    network: Dict[str, Any] = dataclasses.field(default_factory=dict)
    pci: "PCIInfo" = dataclasses.field(default_factory=PCIInfo)
    storage: Dict[str, Any] = dataclasses.field(default_factory=dict)
    system: "SystemInfo" = dataclasses.field(default_factory=SystemInfo)
    usb: "USBInfo" = dataclasses.field(default_factory=USBInfo)
