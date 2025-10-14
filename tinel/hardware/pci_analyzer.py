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

        This method executes the `lspci -v` command to get a verbose listing of
        PCI devices and then parses this output to construct a `PCIInfo` object.

        Returns:
            A `PCIInfo` object containing a list of all found PCI devices. If
            the `lspci` command fails or returns no output, an empty `PCIInfo`
            object is returned.
        """
        lspci_output = self.system.run_command(["lspci", "-v"])
        if not lspci_output.success or not lspci_output.stdout:
            return PCIInfo(devices=[])

        devices = self._parse_lspci_v_output(lspci_output.stdout)
        return PCIInfo(devices=devices)

    def _parse_lspci_v_output(self, output: str) -> List[Dict[str, Any]]:
        """Parses the verbose output of the `lspci -v` command.

        This method processes the raw text output from `lspci -v` and extracts
        structured information about each PCI device, including its slot,
        description, and various attributes.

        Args:
            output: The raw string output from the `lspci -v` command.

        Returns:
            A list of dictionaries, where each dictionary represents a single
            PCI device and its properties.
        """
        devices = []
        current_device: Dict[str, Any] = {}
        # Regex to identify the start of a new device entry, e.g., "00:01.0 ..."
        device_header_re = re.compile(r"^([0-9a-f]{2}:[0-9a-f]{2}\.\d)\s+(.*)")

        for line in output.strip().split("\n"):
            header_match = device_header_re.match(line)
            if header_match:
                # A new device header is found.
                # Save the previous device and start a new one.
                if current_device:
                    devices.append(current_device)

                slot, description = header_match.groups()
                current_device = {
                    "slot": slot.strip(),
                    "description": description.strip(),
                }
            elif current_device and line.strip():
                # This is a detail line for the current device.
                line_content = line.strip()
                if ":" in line_content:
                    key, value = [part.strip() for part in line_content.split(":", 1)]
                    # Normalize the key: lowercase, replace spaces with underscores.
                    key = key.lower().replace(" ", "_")
                    current_device[key] = value
                else:
                    # For lines without a colon, add them to a 'details' list.
                    if "details" not in current_device:
                        current_device["details"] = []
                    current_device["details"].append(line_content)

        # Append the last processed device
        if current_device:
            devices.append(current_device)

        return devices
