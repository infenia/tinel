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
from tinel.hardware.models import USBInfo


class USBAnalyzer:
    """A USB device analyzer that parses output from lsusb."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize USB analyzer.

        Args:
            system_interface: System interface for command execution.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_usb_info(self) -> USBInfo:
        """Get USB device information by running and parsing 'lsusb -t'.

        Returns:
            A USBInfo object containing the device tree.
        """
        lsusb_output = self.system.run_command(["lsusb", "-t"])
        if not lsusb_output.success:
            return USBInfo(tree={"root_hubs": []})

        tree = self._parse_lsusb_t_output(lsusb_output.stdout)
        return USBInfo(tree={"root_hubs": tree})

    def _parse_lsusb_t_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse the tree-like output of the 'lsusb -t' command.

        Args:
            output: The stdout from the 'lsusb -t' command.

        Returns:
            A list of dictionaries representing the root hubs and their children.
        """
        hubs = []
        # A stack to keep track of the current parent device at each indentation level.
        parent_stack: List[Dict[str, Any]] = []

        for line in output.strip().split('\n'):
            line_content = line.strip()
            if not line_content:
                continue

            # Determine the indentation level to understand the hierarchy.
            indentation = len(line) - len(line.lstrip(' '))
            level = indentation // 4

            # Handle root hub lines, which start with '/:'
            if line_content.startswith('/:'):
                root_match = re.match(r"/:.*Bus (\d+)\.Port (\d+): Dev (\d+), Class=(.+), Driver=(.+), (.+)", line_content)
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
                cleaned_line = line_content.lstrip(' |-_')
                match = re.match(r"Port (\d+): Dev (\d+), If (\d+), Class=(.+), Driver=(.+), (.+)", cleaned_line)
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