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

import logging
import re
from typing import Optional

from tinel.hardware.models import SystemInfo
from tinel.interfaces import SystemInterface

log = logging.getLogger(__name__)

class SystemAnalyzer:
    """
    Analyzes system information, including product, vendor, and version.
    """

    def __init__(self, system_interface: SystemInterface):
        self.system_interface = system_interface

    def get_system_info(self) -> SystemInfo:
        """
        Gathers system information from DMI and other sources.
        """
        log.debug("Gathering system information")
        info = SystemInfo()
        dmi_path = "/sys/class/dmi/id/"

        try:
            if self.system_interface.file_exists(dmi_path):
                info.product = self._read_dmi_file("product_name")
                info.vendor = self._read_dmi_file("sys_vendor")
                info.version = self._read_dmi_file("product_version")
                info.serial = self._read_dmi_file("product_serial")
                info.uuid = self._read_dmi_file("product_uuid")
                info.sku_number = self._read_dmi_file("product_sku")
                info.family = self._read_dmi_file("product_family")

            # Get hostname
            hostname_result = self.system_interface.run_command(["hostname"])
            if hostname_result.success:
                info.product = hostname_result.stdout.strip()

            # Get width and capabilities from lscpu
            lscpu_result = self.system_interface.run_command(["lscpu"])
            if lscpu_result.success:
                lscpu_output = lscpu_result.stdout
                width_match = re.search(r"CPU op-mode\(s\):\s*.*(64-bit)", lscpu_output)
                if width_match:
                    info.width = 64
                else:
                    info.width = 32

                # A simple capability mapping
                if "smp" in lscpu_output:
                    info.capabilities["smp"] = "Symmetric Multi-Processing"
        except Exception as e:
            log.error(f"Failed to gather system info: {e}")

        return info

    def _read_dmi_file(self, filename: str) -> Optional[str]:
        """
        Reads a file from the DMI path.
        """
        path = f"/sys/class/dmi/id/{filename}"
        try:
            content = self.system_interface.read_file(path)
            if content:
                stripped = content.strip()
                if stripped:
                    return stripped
            return None
        except FileNotFoundError:
            log.debug(f"DMI file not found: {path}")
            return None
        except Exception as e:
            log.warning(f"Could not read DMI file {path}: {e}")
            return None