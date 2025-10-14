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

from typing import Any, Dict, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class MotherboardAnalyzer:
    """Analyzes and retrieves information about the motherboard.

    This class uses the `dmidecode` command to gather information about the
    motherboard, such as the manufacturer, product name, and version.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the MotherboardAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()

    def get_motherboard_info(self) -> Dict[str, Any]:
        """Retrieves detailed motherboard information using `dmidecode`.

        This method attempts to use `dmidecode` to get baseboard information.
        If `dmidecode` is not available or fails, it returns an error message.

        Returns:
            A dictionary containing motherboard details or an error message.
        """
        info: Dict[str, Any] = {}
        result = self.system.run_command(["dmidecode", "-t", "baseboard"])

        if not result.success:
            info["error"] = f"Failed to run dmidecode: {result.stderr}"
            return info

        info["manufacturer"] = self._parse_dmi_output(result.stdout, "Manufacturer")
        info["product_name"] = self._parse_dmi_output(result.stdout, "Product Name")
        info["version"] = self._parse_dmi_output(result.stdout, "Version")
        info["serial_number"] = self._parse_dmi_output(result.stdout, "Serial Number")

        return info

    def _parse_dmi_output(self, output: str, field: str) -> Optional[str]:
        """Parses the output of `dmidecode` to find a specific field.

        Args:
            output: The stdout from the `dmidecode` command.
            field: The field to search for (e.g., "Manufacturer").

        Returns:
            The value of the field if found, otherwise None.
        """
        for line in output.splitlines():
            if field in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return None
