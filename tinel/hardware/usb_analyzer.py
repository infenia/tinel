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

import json
import logging
import re
from typing import List, Optional, Tuple

from tinel.hardware.models import USBDevice, USBInfo
from tinel.interfaces import SystemInterface

log = logging.getLogger(__name__)


class USBAnalyzer:
    def __init__(self, system_interface: SystemInterface, use_cache: bool = True):
        self.system = system_interface
        self.use_cache = use_cache
        self._cache = None

    def get_usb_info(self) -> USBInfo:
        if self.use_cache and self._cache:
            return self._cache

        result = self.system.run_command("lshw -json -numeric")
        if result.success and result.stdout:
            try:
                hardware_data = json.loads(result.stdout)
                devices = self._parse_lshw_json_output(hardware_data)
                if devices:
                    usb_info = USBInfo(devices=devices)
                    if self.use_cache:
                        self._cache = usb_info
                    return usb_info
            except json.JSONDecodeError:
                log.warning("Failed to parse lshw JSON output for USB devices.")

        log.warning("lshw failed or found no USB devices, falling back to lsusb and sysfs.")
        return self._get_usb_info_from_fallback()

    def _get_usb_info_from_fallback(self) -> USBInfo:
        try:
            # First try sysfs
            devices = []
            bus_dirs = self.system.list_dir("/sys/bus/usb/devices")
            for bus_dir in bus_dirs:
                if ":" in bus_dir:
                    continue
                path = f"/sys/bus/usb/devices/{bus_dir}"
                if self.system.file_exists(f"{path}/busnum") and self.system.file_exists(f"{path}/devnum"):
                    devices.append(self._get_sysfs_usb_details(path))
            return USBInfo(devices=devices)
        except (OSError, IOError) as e:
            log.warning(f"Error accessing sysfs for USB devices: {e}, falling back to lsusb.")
            return self._get_usb_info_from_lsusb()

    def _get_sysfs_usb_details(self, path: str) -> USBDevice:
        def read_file(file_path):
            try:
                return self.system.read_file(file_path).strip()
            except (IOError, OSError):
                return None

        busnum = read_file(f"{path}/busnum")
        devnum = read_file(f"{path}/devnum")

        return USBDevice(
            bus=busnum,
            port=devnum,
            vendor_id=read_file(f"{path}/idVendor"),
            product_id=read_file(f"{path}/idProduct"),
            manufacturer=read_file(f"{path}/manufacturer"),
            product=read_file(f"{path}/product"),
            speed=read_file(f"{path}/speed"),
        )

    def _get_usb_info_from_lsusb(self) -> USBInfo:
        result = self.system.run_command("lsusb -t")
        if not result.success:
            log.error("Failed to run lsusb.")
            return USBInfo(devices=[])

        return USBInfo(devices=self._parse_lsusb_t_output(result.stdout))

    def _parse_id(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        match = re.search(r'\[([0-9a-fA-F]{4})\]', text)
        return (match.group(1).lower() if match else None, self._clean_name(text))

    def _clean_name(self, text: str) -> str:
        return re.sub(r'\s*\[[0-9a-fA-F:]+\]', '', text).strip()

    def _parse_lshw_node(self, node: dict) -> Optional[USBDevice]:
        if not isinstance(node, dict) or not (node.get("id", "").startswith("usb")):
            return None

        vendor_id, vendor_name = self._parse_id(node.get("vendor", ""))
        product_id, product_name = self._parse_id(node.get("product", ""))

        children = []
        if "children" in node:
            for child_node in node["children"]:
                child_device = self._parse_lshw_node(child_node)
                if child_device:
                    children.append(child_device)

        return USBDevice(
            bus=node.get("businfo"),
            port=node.get("slot"),
            device_id=node.get("id"),
            device_class=node.get("class"),
            driver=node.get("configuration", {}).get("driver"),
            speed=node.get("configuration", {}).get("speed"),
            vendor_id=vendor_id,
            product_id=product_id,
            manufacturer=vendor_name,
            product=product_name,
            physid=node.get("physid"),
            version=node.get("version"),
            capabilities=node.get("capabilities", {}),
            configuration=node.get("configuration", {}),
            children=children,
        )

    def _parse_lshw_json_output(self, hardware_data: dict) -> List[USBDevice]:
        devices = []

        def find_usb_bus(node):
            if isinstance(node, dict):
                # A USB bus might be identified by class 'bus' and an id containing 'usb'.
                if node.get("class") == "bus" and "usb" in node.get("id", ""):
                    for child in node.get("children", []):
                        device = self._parse_lshw_node(child)
                        if device:
                            devices.append(device)
                elif "children" in node:
                    for child in node.get("children", []):
                        find_usb_bus(child)

        find_usb_bus(hardware_data)
        return devices

    def _parse_lsusb_t_output(self, output: str) -> List[USBDevice]:
        lines = output.strip().split("\n")
        if not lines or "no such file" in lines[0].lower():
            return []

        root_devices = []
        parent_stack: List[Tuple[int, USBDevice]] = []

        current_bus = None
        for line in lines:
            line_content = line.strip()
            if not line_content:
                continue

            indent = len(line) - len(line.lstrip(" "))
            if line_content.startswith("/:"):
                bus_match = re.search(r"Bus\s+(\d+)", line_content)
                if bus_match:
                    current_bus = bus_match.group(1)

                device = self._parse_lsusb_line(line_content)
                device.bus = current_bus
                root_devices.append(device)
                parent_stack = [(indent, device)]
            else:
                device = self._parse_lsusb_line(line_content)
                device.bus = current_bus

                while parent_stack and parent_stack[-1][0] >= indent:
                    parent_stack.pop()

                if parent_stack:
                    parent_device = parent_stack[-1][1]
                    parent_device.children.append(device)

                parent_stack.append((indent, device))

        return root_devices

    def _parse_lsusb_line(self, line: str) -> USBDevice:
        port_match = re.search(r"Port\s+(\d+)", line)
        class_match = re.search(r"Class=([^,]+)", line)
        driver_match = re.search(r"Driver=([^,]+)", line)
        speed_match = re.search(r"(\d+M)", line)

        return USBDevice(
            port=port_match.group(1) if port_match else None,
            device_class=class_match.group(1).strip() if class_match else None,
            driver=driver_match.group(1).strip() if driver_match else None,
            speed=speed_match.group(1) if speed_match else None,
        )

        return root_devices