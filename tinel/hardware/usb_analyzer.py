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

"""This module provides an analyzer for USB devices.

It includes the `USBAnalyzer` class, which is responsible for gathering and
parsing information about the system's USB devices. The analyzer uses the
`lsusb` command to obtain the raw data and then processes it to build a
hierarchical representation of the USB device tree.
"""

import re
from typing import Any, Dict, List, Optional

from tinel.hardware.models import USBInfo
from tinel.interfaces import SystemInterface
from tinel.system import LinuxSystemInterface


class USBAnalyzer:
    """Analyzes and retrieves information about USB devices.

    This class uses the `lsusb` command to gather data about the devices
    connected to the USB bus and parses the output to provide a structured,
    hierarchical representation of the device tree.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
                          If not provided, a `LinuxSystemInterface` is used.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the USBAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_usb_info(self) -> USBInfo:
        """Retrieves and parses information about all USB devices.

        This method executes the `lsusb -t` command to get a tree-like view of
        USB devices and then parses this output to construct a `USBInfo` object
        containing a hierarchical representation of the devices.

        Returns:
            A `USBInfo` object containing the USB device tree. If the `lsusb`
            command fails, an empty tree is returned.
        """
        lsusb_output = self.system.run_command(["lsusb", "-t"])
        if not lsusb_output.success:
            return USBInfo(tree={"root_hubs": []})

        tree = self._parse_lsusb_t_output(lsusb_output.stdout)
        return USBInfo(tree={"root_hubs": tree})

    def _parse_lsusb_t_output(self, output: str) -> List[Dict[str, Any]]:
        """Parses the tree-like output of the `lsusb -t` command.

        This method processes the raw text output from `lsusb -t` to build a
        hierarchical data structure representing the USB device tree. It handles
        the indentation and structure of the output to correctly nest child
        devices under their parent hubs.

        Args:
            output: The raw string output from the `lsusb -t` command.

        Returns:
            A list of dictionaries, where each dictionary represents a root hub
            and contains its children in a nested structure.
        """
        hubs = []
        # A stack to keep track of the current parent device at each indentation level.
        parent_stack: List[Dict[str, Any]] = []

        for line in output.strip().split("\n"):
            line_content = line.strip()
            if not line_content:
                continue

            # Determine the indentation level to understand the hierarchy.
            indentation = len(line) - len(line.lstrip(" "))
            level = indentation // 4

            # Handle root hub lines, which start with '/:'
            if line_content.startswith("/:"):
                root_match = re.match(
                    (
                        r"/:.*Bus (\d+)\.Port (\d+): Dev (\d+), Class=([^,]+), "
                        r"Driver=([^,]*), (.+)"
                    ),
                    line_content,
                )
                if not root_match:
                    continue
                bus, port, dev, dev_class, driver, speed = root_match.groups()
                node: Dict[str, Any] = {
                    "bus": bus,
                    "port": port,
                    "device_id": dev,
                    "class": dev_class,
                    "driver": driver,
                    "speed": speed,
                    "children": [],
                }
                hubs.append(node)
                parent_stack = [node]  # Reset stack for this hub
            else:
                # Handle child device lines
                cleaned_line = line_content.lstrip(" |-_")
                match = re.match(
                    (
                        r"Port (\d+): Dev (\d+), If (\d+), Class=([^,]+), "
                        r"Driver=([^,]*), (.+)"
                    ),
                    cleaned_line,
                )
                if not match:
                    continue

                port, dev, interface, dev_class, driver, speed = match.groups()
                node = {
                    "port": port,
                    "device_id": dev,
                    "interface": interface,
                    "class": dev_class,
                    "driver": driver,
                    "speed": speed,
                    "children": [],
                }

                # Adjust parent stack based on the current indentation level
                # The parent is at `level - 1`, so the stack should be `level` deep.
                while len(parent_stack) > level:
                    parent_stack.pop()

                # Add the new node to its parent's children list
                if parent_stack:
                    parent_stack[-1]["children"].append(node)

                # Add the current node to the stack for subsequent children
                parent_stack.append(node)

        return hubs
