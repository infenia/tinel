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
from dataclasses import asdict

from tinel.hardware.models import PCIInfo
from tinel.hardware.models import PCIDevice
from tinel.interfaces import SystemInterface

log = logging.getLogger(__name__)


class PCIAnalyzer:
    def __init__(self, system_interface: SystemInterface, use_cache: bool = True):
        self.system = system_interface
        self.use_cache = use_cache
        self._cache = None

    def get_pci_info(self) -> PCIInfo:
        if self.use_cache and self._cache:
            return self._cache

        # Try lshw first
        result = self.system.run_command("lshw -json -numeric")
        if result.success and result.stdout:
            try:
                hardware_data = json.loads(result.stdout)
                devices = self._parse_lshw_json_output(hardware_data)
                pci_info = PCIInfo(devices=devices)
                if self.use_cache:
                    self._cache = pci_info
                return pci_info
            except json.JSONDecodeError:
                log.warning("Failed to parse lshw JSON output.")

        # Fallback or if lshw fails
        log.warning("lshw failed, falling back to lspci.")
        return self._get_pci_info_from_lspci()

    def _get_pci_info_from_lspci(self) -> PCIInfo:
        result = self.system.run_command("lspci -vmmk")
        if not result.success:
            log.error("Failed to run lspci.")
            return PCIInfo(devices=[])

        devices = self._parse_lspci_vmmk_output(result.stdout)
        return PCIInfo(devices=devices)

    def _parse_id(self, text: str, is_vendor: bool) -> tuple[str | None, str | None]:
        # Tries to find [vendor:device] first
        match = re.search(r'\[([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\]', text)
        if match:
            return match.group(1).lower(), match.group(2).lower()

        # Then tries to find [xxxx]
        match = re.search(r'\[([0-9a-fA-F]{4})\]', text)
        if match:
            if is_vendor:
                return match.group(1).lower(), None
            else:
                return None, match.group(1).lower()

        return None, None

    def _clean_name(self, text: str) -> str:
        return re.sub(r'\s*\[[0-9a-fA-F:]+\]', '', text).strip()

    def _parse_lshw_json_output(self, hardware_data: dict) -> list[PCIDevice]:
        devices = []

        def find_pci_devices(node):
            if isinstance(node, dict) and node.get("businfo", "").startswith("pci@") and "slot" in node:
                vendor_str = node.get("vendor", "")
                product_str = node.get("product", "")

                vendor_id_from_vendor, _ = self._parse_id(vendor_str, is_vendor=True)
                vendor_id_from_product, device_id_from_product = self._parse_id(product_str, is_vendor=False)

                vendor_id = vendor_id_from_vendor or vendor_id_from_product
                device_id = device_id_from_product

                vendor_name = self._clean_name(vendor_str)
                product_name = self._clean_name(product_str)

                devices.append(
                    PCIDevice(
                        slot=node.get("slot"),
                        description=node.get("description"),
                        vendor_id=vendor_id,
                        device_id=device_id,
                        driver=node.get("configuration", {}).get("driver"),
                        width=node.get("width"),
                        details={
                            "vendor": vendor_name,
                            "device": product_name,
                            "class": node.get("class"),
                            "version": node.get("version"),
                        },
                        capabilities=list(node.get("capabilities", {}).keys()),
                        memory=[node.get("resources", {}).get("memory")],
                    )
                )

            if isinstance(node, dict) and "children" in node:
                for child in node["children"]:
                    find_pci_devices(child)
            elif isinstance(node, list):
                for item in node:
                    find_pci_devices(item)

        find_pci_devices(hardware_data)
        return devices

    def _parse_lspci_vmmk_output(self, output: str) -> list[PCIDevice]:
        devices = []
        current_device = {}
        for line in output.splitlines():
            if not line.strip():
                if current_device:
                    devices.append(self._create_pci_device_from_lspci(current_device))
                    current_device = {}
                continue
            try:
                key, value = line.split("\t", 1)
                key = key.strip().replace(":", "").lower()
                current_device[key] = value.strip()
            except ValueError:
                log.debug(f"Skipping malformed line in lspci output: {line}")
        if current_device:
            devices.append(self._create_pci_device_from_lspci(current_device))
        return devices

    def _create_pci_device_from_lspci(self, data: dict) -> PCIDevice:
        vendor_id, _ = self._parse_id(data.get("vendor", ""), is_vendor=True)
        _, device_id = self._parse_id(data.get("device", ""), is_vendor=False)

        return PCIDevice(
            slot=data.get("slot"),
            subsystem=self._clean_name(data.get("subsystem", "")),
            driver=data.get("driver"),
            vendor_id=vendor_id,
            device_id=device_id,
            details={
                "vendor": self._clean_name(data.get("vendor", "")),
                "device": self._clean_name(data.get("device", "")),
                "class": self._clean_name(data.get("class", "")),
            }
        )