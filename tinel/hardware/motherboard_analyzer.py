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
from typing import Optional

from tinel.hardware.models import MotherboardInfo
from tinel.interfaces import SystemInterface

log = logging.getLogger(__name__)

class MotherboardAnalyzer:
    """
    Analyzes motherboard information, including product, vendor, and version.
    """

    def __init__(self, system_interface: SystemInterface):
        self.system = system_interface

    def get_motherboard_info(self) -> MotherboardInfo:
        """
        Gathers motherboard information from DMI.
        """
        log.debug("Gathering motherboard information")
        info = MotherboardInfo()
        dmi_path = "/sys/class/dmi/id/"
        info.physid = "0"

        try:
            if not self.system.file_exists(dmi_path):
                return info
        except Exception as e:
            log.error(f"Failed to check for motherboard info: {e}")
            return info

        info.product = self._read_dmi_file("board_name")
        info.vendor = self._read_dmi_file("board_vendor")
        info.version = self._read_dmi_file("board_version")
        info.serial = self._read_dmi_file("board_serial")
        info.asset_tag = self._read_dmi_file("board_asset_tag")

        return info

    def _read_dmi_file(self, filename: str) -> Optional[str]:
        """
        Reads a file from the DMI path.
        """
        path = f"/sys/class/dmi/id/{filename}"
        try:
            content = self.system.read_file(path)
            return content.strip() if content and content.strip() else None
        except (FileNotFoundError, IOError, OSError) as e:
            log.warning(f"Could not read DMI file {path}: {e}")
            return None