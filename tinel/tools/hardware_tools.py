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

"""Hardware information tool providers."""

from typing import Any, Dict
from .base import BaseToolProvider
from ..hardware.device_analyzer import DeviceAnalyzer
from ..interfaces import SystemInterface


class HardwareToolProvider(BaseToolProvider):
    """Base class for hardware information tools."""

    def __init__(self, name: str, description: str, system_interface: SystemInterface):
        """Initialize hardware tool provider.

        Args:
            name: Tool name
            description: Tool description
            system_interface: System interface for command execution
        """
        super().__init__(name, description)
        self.device_analyzer = DeviceAnalyzer(system_interface)


class AllHardwareToolProvider(HardwareToolProvider):
    """Tool provider for comprehensive hardware information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_all_hardware",
            "Get comprehensive hardware information for the entire system",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get all hardware information."""
        hardware_info = self.device_analyzer.get_all_hardware_info()
        return {
            "cpu": hardware_info.cpu,
            # 'memory': hardware_info.memory,
            # 'storage': hardware_info.storage,
            # 'pci_devices': hardware_info.pci_devices,
            # 'usb_devices': hardware_info.usb_devices,
            # 'network': hardware_info.network,
            # 'graphics': hardware_info.graphics,
        }


class CPUInfoToolProvider(HardwareToolProvider):
    """Tool provider for CPU information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_cpu_info",
            "Get detailed CPU information including model, cores, frequency, and features",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get CPU information."""
        return self.device_analyzer.get_cpu_info()


class MemoryInfoToolProvider(HardwareToolProvider):
    """Tool provider for memory information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_memory_info",
            "Get detailed memory information including RAM size, type, and configuration",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get memory information."""
        return self.device_analyzer.get_memory_info()


class StorageInfoToolProvider(HardwareToolProvider):
    """Tool provider for storage information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_storage_info",
            "Get detailed storage information including disks, partitions, and usage",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get storage information."""
        return self.device_analyzer.get_storage_info()


class PCIDevicesToolProvider(HardwareToolProvider):
    """Tool provider for PCI device information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_pci_devices",
            "Get information about all PCI devices in the system",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get PCI device information."""
        return self.device_analyzer.get_pci_devices()


class USBDevicesToolProvider(HardwareToolProvider):
    """Tool provider for USB device information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_usb_devices",
            "Get information about all USB devices connected to the system",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get USB device information."""
        return self.device_analyzer.get_usb_devices()


class NetworkInfoToolProvider(HardwareToolProvider):
    """Tool provider for network information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_network_info",
            "Get network hardware and interface information",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get network information."""
        return self.device_analyzer.get_network_info()


class GraphicsInfoToolProvider(HardwareToolProvider):
    """Tool provider for graphics information."""

    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_graphics_info",
            "Get graphics hardware information including GPU details",
            system_interface,
        )

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get graphics information."""
        return self.device_analyzer.get_graphics_info()
