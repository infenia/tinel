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
from typing import Any, Dict, List, Optional

from tinel.hardware.models import PCIInfo
from tinel.interfaces import SystemInterface
from tinel.system import LinuxSystemInterface

"""This module provides an analyzer for PCI devices.

It includes the `PCIAnalyzer` class, which is responsible for gathering and
parsing information about the system's PCI devices. The analyzer uses the
`lspci` command to obtain the raw data and then processes it to extract
detailed information about each device.
"""


class PCIAnalyzer:
    """Analyzes and retrieves information about PCI devices.

    This class uses the `lspci` command to gather data about the devices
    connected to the PCI bus and parses the output to provide a structured
    representation of the information.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
                          If not provided, a `LinuxSystemInterface` is used.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the PCIAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_pci_info(self) -> PCIInfo:
        """Retrieves and parses information about all PCI devices.

        This method executes the `lspci -vnnk` command to get a verbose,
        numeric listing of PCI devices, including kernel driver information.
        It then parses this output to construct a `PCIInfo` object.

        Returns:
            A `PCIInfo` object containing a list of all found PCI devices. If
            the `lspci` command fails or returns no output, an empty `PCIInfo`
            object is returned.
        """
        lspci_output = self.system.run_command(["lspci", "-vnnk"])
        if lspci_output.success and lspci_output.stdout:
            devices = self._parse_lspci_vnnk_output(lspci_output.stdout)
            return PCIInfo(devices=devices)
        else:
            # Fallback to sysfs if lspci fails
            devices = self._get_pci_info_from_sysfs()
            return PCIInfo(devices=devices)

    def _get_pci_info_from_sysfs(self) -> List[Dict[str, Any]]:
        """Retrieves basic PCI device information from sysfs.

        This method serves as a fallback when `lspci` is not available. It
        parses the `/sys/bus/pci/devices` directory to gather information
        about each PCI device.

        Returns:
            A list of dictionaries, where each dictionary represents a
            single PCI device and its properties.
        """
        devices = []
        pci_path = "/sys/bus/pci/devices"
        device_dirs = self.system.list_dir(pci_path)
        if not device_dirs:
            return []

        for device_dir in device_dirs:
            try:
                device_path = f"{pci_path}/{device_dir}"
                vendor_file = self.system.read_file(f"{device_path}/vendor")
                device_file = self.system.read_file(f"{device_path}/device")
                class_file = self.system.read_file(f"{device_path}/class")

                if not (vendor_file and device_file and class_file):
                    continue

                driver_path = self.system.readlink(f"{device_path}/driver")
                driver = driver_path.split("/")[-1] if driver_path else "N/A"

                devices.append(
                    {
                        "slot": device_dir,
                        "vendor_id": vendor_file.strip(),
                        "device_id": device_file.strip(),
                        "class": class_file.strip(),
                        "driver": driver,
                        "description": "N/A (from sysfs)",
                    }
                )
            except (FileNotFoundError, PermissionError):
                continue
        return devices

    def _parse_lspci_vnnk_output(self, output: str) -> List[Dict[str, Any]]:
        """Parses the verbose output of the `lspci -vnnk` command.

        This method processes the raw text output from `lspci -vnnk` and
        extracts structured information about each PCI device, including its
        slot, description, vendor/device IDs, and kernel driver.

        Args:
            output: The raw string output from the `lspci -vnnk` command.

        Returns:
            A list of dictionaries, where each dictionary represents a single
            PCI device and its properties.
        """
        devices = []
        current_device: Dict[str, Any] = {}
        device_header_re = re.compile(
            r"^([0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.\d)\s+(.*)\s+\[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\]"
        )

        for line in output.strip().split("\n"):
            header_match = device_header_re.match(line)
            if header_match:
                if current_device:
                    devices.append(current_device)

                slot, description, vendor_id, device_id = header_match.groups()
                current_device = {
                    "slot": slot.strip(),
                    "description": description.strip(),
                    "vendor_id": vendor_id.strip(),
                    "device_id": device_id.strip(),
                }
            elif current_device and line.strip():
                line_content = line.strip()
                kv_match = re.match(r"([^:]+):\s+(.*)", line_content)
                if kv_match:
                    key, value = kv_match.groups()
                    key = key.lower().replace(" ", "_").replace("-", "_")
                    if key == "kernel_driver_in_use":
                        current_device["driver"] = value
                    else:
                        current_device[key] = value
                else:
                    if "details" not in current_device:
                        current_device["details"] = []
                    current_device["details"].append(line_content)

        if current_device:
            devices.append(current_device)

        return devices
