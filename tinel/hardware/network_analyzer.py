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

import functools
import logging
import re
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class NetworkAnalyzer:
    """Enhanced network analyzer with detailed capabilities detection."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize network analyzer.

        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        self.logger = logging.getLogger(__name__)

    @functools.lru_cache(maxsize=None)
    def get_network_info(self) -> Dict[str, Any]:
        """Get comprehensive network hardware information.

        Returns:
            Dictionary containing detailed network hardware information
        """
        info: Dict[str, Any] = {}

        # Get basic network interface info
        info.update(self._get_basic_network_info())

        # Get detailed network interface information
        info.update(self._get_detailed_network_info())

        # Get wireless network information
        info.update(self._get_wireless_info())

        # Get network driver information
        info.update(self._get_driver_info())

        # Get network performance metrics
        info.update(self._get_performance_metrics())

        return info

    def _get_basic_network_info(self) -> Dict[str, Any]:
        """Get basic network interface information using ip command."""
        info: Dict[str, Any] = {}

        # Get network interface information using ip addr
        ip_addr_result = self.system.run_command(["ip", "-s", "addr"])
        if ip_addr_result.success:
            info["ip_addr"] = ip_addr_result.stdout
            info["interfaces"] = self._parse_ip_addr_output(ip_addr_result.stdout)
        else:
            self.logger.warning("Failed to run 'ip addr': %s", ip_addr_result.stderr)
            info["ip_addr_error"] = ip_addr_result.stderr or "Failed to run ip addr"

        # Get network interface statistics using ip -s link
        ip_link_result = self.system.run_command(["ip", "-s", "link"])
        if ip_link_result.success:
            info["ip_link"] = ip_link_result.stdout
            info.update(self._parse_ip_link_output(ip_link_result.stdout))
        else:
            self.logger.warning("Failed to run 'ip -s link': %s", ip_link_result.stderr)
            info["ip_link_error"] = ip_link_result.stderr or "Failed to run ip -s link"

        return info

    def _get_detailed_network_info(self) -> Dict[str, Any]:
        """Get detailed network interface information."""
        info: Dict[str, Any] = {}
        interfaces = []

        # Get list of network interfaces
        ls_result = self.system.run_command(["ls", "/sys/class/net/"])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()

            for interface_name in interface_names:
                if interface_name == "lo":
                    continue

                interface_info = self._get_interface_details(interface_name)
                if interface_info:
                    interfaces.append(interface_info)
        else:
            self.logger.warning("Failed to list network interfaces in /sys/class/net/")

        if interfaces:
            info["detailed_interfaces"] = interfaces

        return info

    def _get_wireless_info(self) -> Dict[str, Any]:
        """Get wireless network information."""
        info: Dict[str, Any] = {}

        # Get wireless interface information using iwconfig
        iwconfig_result = self.system.run_command(["iwconfig"])
        if iwconfig_result.success and iwconfig_result.stdout.strip():
            info["iwconfig"] = iwconfig_result.stdout
            info["wireless_interfaces"] = self._parse_iwconfig_output(
                iwconfig_result.stdout
            )
        elif not iwconfig_result.success:
            self.logger.info(
                "'iwconfig' command not found or failed, skipping wireless info."
            )

        # Get detailed wireless information using iw
        iw_result = self.system.run_command(["iw", "list"])
        if iw_result.success:
            info["iw_list"] = iw_result.stdout
            info["wireless_capabilities"] = self._parse_iw_list_output(iw_result.stdout)
        elif not iw_result.success: # pragma: no branch
            self.logger.info(
                "'iw' command not found or failed, skipping detailed wireless info."
            )

        return info

    def _get_driver_info(self) -> Dict[str, Any]:
        """Get network interface driver information."""
        info: Dict[str, Any] = {}
        driver_info = []

        # Get list of network interfaces
        ls_result = self.system.run_command(["ls", "/sys/class/net/"])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()

            for interface_name in interface_names:  # pragma: no branch
                if interface_name == "lo":
                    continue

                driver = self._get_interface_driver(interface_name)
                if driver:
                    driver_details = self._get_driver_details(driver)
                    driver_entry = {"interface": interface_name, "driver": driver}
                    if driver_details:
                        driver_entry["driver_details"] = driver_details
                    driver_info.append(driver_entry)

        if driver_info:
            info["driver_info"] = driver_info

        return info

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get network performance metrics."""
        info: Dict[str, Any] = {}

        # Get network statistics using netstat
        netstat_result = self.system.run_command(["netstat", "-i"])
        if netstat_result.success:
            info["netstat"] = netstat_result.stdout
            info["interface_statistics"] = self._parse_netstat_output(
                netstat_result.stdout
            )
        else:
            self.logger.info(
                "'netstat' command not found or failed, skipping netstat info."
            )

        # Get detailed network statistics using ethtool
        ls_result = self.system.run_command(["ls", "/sys/class/net/"])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
            ethtool_stats = {}

            for interface_name in interface_names:
                if interface_name == "lo":
                    continue

                ethtool_result = self.system.run_command(
                    ["ethtool", "-S", interface_name]
                )
                if ethtool_result.success:
                    ethtool_stats[interface_name] = self._parse_ethtool_output(
                        ethtool_result.stdout
                    )
                else:
                    self.logger.info(
                        "Could not get ethtool stats for %s.", interface_name
                    )

            if ethtool_stats:
                info["ethtool_statistics"] = ethtool_stats

        return info

    def _parse_ip_addr_output(self, ip_addr_output: str) -> List[Dict[str, Any]]:
        """Parse ip addr output."""
        interfaces = []
        current_interface: Optional[Dict[str, Any]] = None

        for line in ip_addr_output.strip().split("\n"):
            # A new interface block starts with a number and a colon.
            if not line.startswith(" "):
                # If we were processing an interface, add it to the list
                if current_interface:
                    interfaces.append(current_interface)
                current_interface = None  # Reset

                match = re.match(r"^\d+: ([^:@]+)(@[^:]+)?:", line)
                if match:
                    interface_name = match.group(1)
                    current_interface = {"name": interface_name, "addresses": []}

                    state_match = re.search(r"state (\w+)", line)
                    if state_match:
                        current_interface["state"] = state_match.group(1)

            # These lines belong to the current interface
            elif current_interface:
                mac_match = re.search(r"link/\w+ ([0-9a-fA-F:]+)", line)
                if mac_match:
                    current_interface["mac"] = mac_match.group(1)

                if "inet " in line:
                    ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", line)
                    if ip_match:
                        current_interface["addresses"].append(
                            {"family": "inet", "address": ip_match.group(1)}
                        )
                elif "inet6 " in line:
                    ip_match = re.search(r"inet6 ([0-9a-fA-F:]+/\d+)", line)
                    if ip_match:
                        current_interface["addresses"].append(
                            {"family": "inet6", "address": ip_match.group(1)}
                        )

        # Add the last interface processed
        if current_interface:
            interfaces.append(current_interface)

        return interfaces

    def _parse_ip_link_output(self, ip_link_output: str) -> Dict[str, Any]:
        """Parse ip -s link output."""
        stats: Dict[str, Any] = {}
        current_interface = None
        section = None

        for line in ip_link_output.strip().split("\n"):
            if not line.startswith(" "):
                match = re.match(r"^\d+: ([^:@]+)", line)
                if match:
                    current_interface = match.group(1)
                    stats[current_interface] = {}
            elif current_interface:
                if "RX:" in line:
                    section = "rx"
                elif "TX:" in line:
                    section = "tx"
                elif section:
                    values = line.strip().split()
                    if section == "rx" and len(values) >= 6:
                        stats[current_interface]["rx"] = {
                            "bytes": int(values[0]),
                            "packets": int(values[1]),
                            "errors": int(values[2]),
                            "dropped": int(values[3]),
                            "overrun": int(values[4]),
                            "mcast": int(values[5]),
                        }
                        section = None  # Move to next section
                    elif section == "tx" and len(values) >= 6:
                        stats[current_interface]["tx"] = {
                            "bytes": int(values[0]),
                            "packets": int(values[1]),
                            "errors": int(values[2]),
                            "dropped": int(values[3]),
                            "carrier": int(values[4]),
                            "collsns": int(values[5]),
                        }
                        section = None
        return {"interface_statistics": stats}

    def _get_interface_details(self, interface_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific network interface."""
        interface_info: Dict[str, Any] = {"name": interface_name}
        sys_path = f"/sys/class/net/{interface_name}"

        def read_sys_file(file: str) -> Optional[str]:
            content = self.system.read_file(f"{sys_path}/{file}")
            return content.strip() if content else None

        type_val = read_sys_file("type")
        if type_val:
            type_map = {"1": "ethernet", "772": "loopback"}
            interface_info["type"] = type_map.get(type_val, f"unknown ({type_val})")

        for key in ["speed", "duplex", "mtu", "carrier", "operstate", "address"]:
            value = read_sys_file(key)
            if value:
                interface_info[key] = int(value) if value.isdigit() else value

        flags_val = read_sys_file("flags")
        if flags_val:
            flags = int(flags_val, 16)
            interface_info["flags"] = flags
            flag_map = {
                0x1: "UP",
                0x2: "BROADCAST",
                0x8: "LOOPBACK",
                0x40: "RUNNING",
                0x1000: "MULTICAST",
                0x10000: "LOWER_UP",
            }
            decoded = [name for val, name in flag_map.items() if flags & val]
            interface_info["decoded_flags"] = decoded

        stats: Dict[str, Any] = {}
        stats_path = f"{sys_path}/statistics"
        ls_result = self.system.run_command(["ls", stats_path])
        if ls_result.success:
            for stat_file in ls_result.stdout.strip().split():
                stat_value = self.system.read_file(f"{stats_path}/{stat_file}")
                if stat_value:
                    stats[stat_file] = int(stat_value.strip())
        if stats:
            interface_info["statistics"] = stats

        return interface_info

    def _parse_iwconfig_output(self, iwconfig_output: str) -> List[Dict[str, Any]]:
        """Parse iwconfig output."""
        interfaces = []
        for block in iwconfig_output.strip().split("\n\n"):
            if not block.strip():
                continue

            interface_name_match = re.match(r"^(\S+)", block)
            if not interface_name_match:
                continue

            name = interface_name_match.group(1)
            if "no wireless extensions" in block:
                continue

            interface_info: Dict[str, Any] = {"name": name}

            essid_match = re.search(r'ESSID:"([^"]*)"', block)
            if essid_match:
                interface_info["essid"] = essid_match.group(1)

            mode_match = re.search(r"Mode:(\S+)", block)
            if mode_match:
                interface_info["mode"] = mode_match.group(1)

            freq_match = re.search(r"Frequency:(\d+\.\d+ GHz)", block)
            if freq_match:
                interface_info["frequency"] = freq_match.group(1)

            ap_match = re.search(r"Access Point: ([0-9A-Fa-f:]+)", block)
            if ap_match:
                interface_info["access_point"] = ap_match.group(1)

            bitrate_match = re.search(r"Bit Rate=([\d\.]+\s\w+/s)", block)
            if bitrate_match:
                interface_info["bit_rate"] = bitrate_match.group(1)

            signal_match = re.search(r"Signal level=(-?\d+ dBm)", block)
            if signal_match:
                interface_info["signal_level"] = signal_match.group(1)

            interfaces.append(interface_info)
        return interfaces

    def _parse_iw_list_output(self, iw_list_output: str) -> Dict[str, Any]:
        """Parse iw list output."""
        # This is a placeholder for a more complex parser.
        # For now, we just return the raw text.
        return {"raw": iw_list_output}

    def _get_interface_driver(self, interface_name: str) -> Optional[str]:
        """Get driver for a specific network interface."""
        ethtool_result = self.system.run_command(["ethtool", "-i", interface_name])
        if ethtool_result.success:
            driver_match = re.search(r"driver:\s*(\S+)", ethtool_result.stdout)
            if driver_match:
                return driver_match.group(1)
        self.logger.info("Could not get driver for %s via ethtool.", interface_name)
        return None

    def _get_driver_details(self, driver_name: str) -> Dict[str, Any]:
        """Get details for a specific network driver."""
        details = {}
        modinfo_result = self.system.run_command(["modinfo", driver_name])
        if modinfo_result.success:
            for line in modinfo_result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    details[key.strip()] = value.strip()
        return details

    def _parse_netstat_output(self, netstat_output: str) -> List[Dict[str, Any]]:
        """Parse netstat -i output."""
        interfaces = []
        lines = netstat_output.strip().split("\n")
        if len(lines) < 2:
            return interfaces

        headers = re.split(r"\s+", lines[0].strip())

        for line in lines[1:]:
            values = re.split(r"\s+", line.strip())
            if len(values) >= len(headers):
                interface_stats = {
                    h.lower(): v for h, v in zip(headers, values, strict=False)
                }
                interfaces.append(interface_stats)

        return interfaces

    def _parse_ethtool_output(self, ethtool_output: str) -> Dict[str, Any]:
        """Parse ethtool -S output."""
        stats = {}
        # Skip the first line which is a header
        for line in ethtool_output.strip().split("\n")[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key and value.isdigit():
                    stats[key] = int(value)
        return stats
