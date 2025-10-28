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

from tinel.hardware.models import BIOSInfo
from tinel.interfaces import SystemInterface

log = logging.getLogger(__name__)

class BIOSAnalyzer:
    """
    Analyzes BIOS information, including vendor, version, and release date.
    """

    def __init__(self, system_interface: SystemInterface):
        self.system_interface = system_interface

    def get_bios_info(self) -> BIOSInfo:
        """
        Gathers BIOS information from DMI.
        """
        log.debug("Gathering BIOS information")
        info = BIOSInfo()
        dmi_path = "/sys/class/dmi/id/"

        try:
            if self.system_interface.file_exists(dmi_path):
                info.vendor = self._read_dmi_file("bios_vendor")
                info.version = self._read_dmi_file("bios_version")
                info.date = self._read_dmi_file("bios_date")
        except Exception as e:
            log.error(f"Failed to gather BIOS info from DMI: {e}")

        # Use dmidecode for capabilities and size
        dmidecode_result = self.system_interface.run_command(["dmidecode", "-t", "bios"])
        if dmidecode_result.success:
            output = dmidecode_result.stdout
            size_match = re.search(r"ROM Size:\s*(.*)", output)
            if size_match:
                info.size = size_match.group(1).strip()

            capabilities_match = re.search(r"BIOS characteristics:\s*\n((?:\s+.*\n)+)", output)
            if capabilities_match:
                capabilities_str = capabilities_match.group(1)
                for line in capabilities_str.strip().split("\n"):
                    info.capabilities[line.strip()] = True
        else:
            log.warning("Failed to get BIOS info from dmidecode.")

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