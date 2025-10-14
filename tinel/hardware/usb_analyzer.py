#!/usr/bin/env python3
"""
Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may- obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import re
from typing import Any, Dict, List, Optional

import psutil

from tinel.hardware.models import USBInfo
from tinel.interfaces import CommandResult, SystemInterface
from tinel.system import LinuxSystemInterface

"""This module provides an analyzer for USB devices.

It includes the `USBAnalyzer` class, which is responsible for gathering and
parsing information about the system's USB devices. It uses `lsusb` to get a
hierarchical view and falls back to `psutil` for a flat list if `lsusb` fails.
"""


class USBAnalyzer:
    """Analyzes and retrieves information about USB devices.

    This class uses a fallback mechanism to gather USB device data:
    1. `lsusb -t` to get a hierarchical tree of devices, enriched with details
       from `/sys/bus/usb/devices` or `lsusb`.
    2. `psutil.usb.devices()` as a fallback to get a flat list of devices if
       `lsusb` is not available.

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
        self._lsusb_output_cache: Optional[CommandResult] = None

    def get_usb_info(self) -> USBInfo:
        """Retrieves and parses information about all USB devices.

        This method orchestrates the fallback chain to get USB information.

        Returns:
            A `USBInfo` object containing the USB device tree or list.
        """
        # 1. Try lsusb
        lsusb_output = self.system.run_command(["lsusb", "-t"])
        if lsusb_output.success:
            tree = self._parse_lsusb_t_output(lsusb_output.stdout)
            return USBInfo(tree={"root_hubs": tree})

        # 2. Fallback to psutil
        psutil_devices = self._get_usb_info_from_psutil()
        if psutil_devices:
            return USBInfo(tree={"devices": psutil_devices})

        return USBInfo(tree={"root_hubs": []})

    def _get_device_details(self, bus: str, dev_id: str) -> Dict[str, Any]:
        """Retrieves detailed information for a specific USB device from sysfs.

        This function reads device attributes such as vendor ID, product ID,
        manufacturer, and product name from the corresponding sysfs directory.
        If sysfs is unavailable or a match is not found, it falls back to
        parsing `lsusb` output.

        Args:
            bus: The USB bus number.
            dev_id: The device ID on the bus.

        Returns:
            A dictionary containing the detailed device information.
        """
        sysfs_base = "/sys/bus/usb/devices"
        device_dirs = self.system.list_dir(sysfs_base)

        if device_dirs:
            for dev_dir in device_dirs:
                dev_path = f"{sysfs_base}/{dev_dir}"
                try:
                    busnum_path = f"{dev_path}/busnum"
                    devnum_path = f"{dev_path}/devnum"

                    bus_num_content_raw = self.system.read_file(busnum_path)
                    dev_num_content_raw = self.system.read_file(devnum_path)

                    if not bus_num_content_raw or not dev_num_content_raw:
                        continue

                    bus_num_content = bus_num_content_raw.strip()
                    dev_num_content = dev_num_content_raw.strip()

                    if int(bus_num_content) == int(bus) and int(dev_num_content) == int(
                        dev_id
                    ):
                        vendor_id_raw = self.system.read_file(f"{dev_path}/idVendor")
                        product_id_raw = self.system.read_file(f"{dev_path}/idProduct")
                        manufacturer_raw = self.system.read_file(
                            f"{dev_path}/manufacturer"
                        )
                        product_raw = self.system.read_file(f"{dev_path}/product")

                        details: Dict[str, Any] = {
                            "vendor_id": vendor_id_raw.strip()
                            if vendor_id_raw
                            else None,
                            "product_id": product_id_raw.strip()
                            if product_id_raw
                            else None,
                            "manufacturer": manufacturer_raw.strip()
                            if manufacturer_raw
                            else None,
                            "product": product_raw.strip() if product_raw else None,
                        }
                        return details
                except (IOError, OSError, FileNotFoundError):
                    continue

        # Fallback to lsusb if sysfs fails or device not found
        return self._get_details_from_lsusb(bus, dev_id)

    def _get_details_from_lsusb(self, bus: str, dev_id: str) -> Dict[str, str]:
        """
        Fallback method to get vendor and product IDs from `lsusb` output.

        This method caches the output of the `lsusb` command to avoid
        running it multiple times during a single analysis.
        """
        details: Dict[str, str] = {}
        if self._lsusb_output_cache is None:
            self._lsusb_output_cache = self.system.run_command(["lsusb"])

        lsusb_output = self._lsusb_output_cache
        if not lsusb_output.success:
            return details

        pattern = re.compile(
            r"Bus\s+{0:03d}\s+Device\s+{1:03d}:\s+ID\s+([0-9a-fA-F]{{4}}):([0-9a-fA-F]{{4}})".format(
                int(bus), int(dev_id)
            )
        )

        for line in lsusb_output.stdout.split("\n"):
            match = pattern.search(line)
            if match:
                details["vendor_id"] = match.group(1)
                details["product_id"] = match.group(2)
                return details
        return details

    def _parse_lsusb_t_output(self, output: str) -> List[Dict[str, Any]]:
        """Parses the tree-like output of the `lsusb -t` command.

        This method processes the raw text output from `lsusb -t` to build a
        hierarchical data structure representing the USB device tree.
        """
        hubs = []
        parent_stack: List[Dict[str, Any]] = []

        for line in output.strip().split("\n"):
            line_content = line.strip()
            if not line_content:
                continue

            indentation = len(line) - len(line.lstrip(" "))
            level = indentation // 4

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
                details = self._get_device_details(bus, dev)
                node.update(details)
                hubs.append(node)
                parent_stack = [node]
            else:
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
                while len(parent_stack) > level:
                    parent_stack.pop()

                if parent_stack:
                    bus_num = parent_stack[0]["bus"]
                    details = self._get_device_details(bus_num, dev)
                    node.update(details)
                    parent_stack[-1]["children"].append(node)

                parent_stack.append(node)

        return hubs

    def _get_usb_info_from_psutil(self) -> List[Dict[str, Any]]:
        """Retrieves a flat list of USB devices using `psutil`.

        This method serves as a fallback when `lsusb` is not available.
        It uses `psutil.usb.devices()` to get a list of devices.

        Returns:
            A list of dictionaries, where each dictionary represents a
            single USB device and its properties.
        """
        devices = []
        try:
            usb_devices = psutil.usb.devices()
            for dev in usb_devices:
                devices.append(
                    {
                        "vendor_id": dev.vendor_id,
                        "product_id": dev.product_id,
                        "name": dev.name,
                        "manufacturer": dev.manufacturer,
                        "product": dev.product,
                        "serial": dev.serial,
                    }
                )
        except (ImportError, AttributeError, Exception):
            # psutil might not be installed or might not support usb.devices()
            return []
        return devices
