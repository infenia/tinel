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

from tinel.interfaces import SystemInterface
from tinel.system import LinuxSystemInterface
from tinel.hardware.models import PCIInfo


class PCIAnalyzer:
    """A PCI device analyzer that parses output from lspci."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize PCI analyzer.

        Args:
            system_interface: System interface for command execution.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_pci_info(self) -> PCIInfo:
        """Get PCI device information by running and parsing 'lspci -v'.

        Returns:
            A PCIInfo object containing the list of devices.
        """
        lspci_output = self.system.run_command(["lspci", "-v"])
        if not lspci_output.success or not lspci_output.stdout:
            return PCIInfo(devices=[])

        devices = self._parse_lspci_v_output(lspci_output.stdout)
        return PCIInfo(devices=devices)

    def _parse_lspci_v_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse the verbose output of the 'lspci -v' command.

        Args:
            output: The stdout from the 'lspci -v' command.

        Returns:
            A list of dictionaries, where each dictionary represents a PCI device.
        """
        devices = []
        current_device: Dict[str, Any] = {}
        # Regex to identify the start of a new device entry, e.g., "00:01.0 ..."
        device_header_re = re.compile(r"^([0-9a-f]{2}:[0-9a-f]{2}\.\d)\s+(.*)")

        for line in output.strip().split('\n'):
            header_match = device_header_re.match(line)
            if header_match:
                # If a new device header is found, save the previous one and start a new one.
                if current_device:
                    devices.append(current_device)

                slot, description = header_match.groups()
                current_device = {"slot": slot.strip(), "description": description.strip()}
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