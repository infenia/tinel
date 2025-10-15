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
from typing import Any, Dict, List, Optional

import psutil

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface

"""This module provides a detailed analyzer for network hardware.

It includes the `NetworkAnalyzer` class, which is responsible for gathering
and processing comprehensive information about network interfaces. The
analyzer uses a variety of system commands, including `ip`, `iwconfig`,
`ethtool`, and `netstat`, as well as the `/sys/class/net` filesystem, to
provide a complete picture of the network hardware and its configuration.
"""


class NetworkAnalyzer:
    """Analyzes and retrieves detailed information about network hardware.

    This class provides a comprehensive analysis of network interfaces,
    including their configuration, drivers, performance metrics, and wireless
    capabilities. It uses a variety of system tools and files to gather this
    information.

    Args:
        system_interface: An optional `SystemInterface` for system interactions.
                          If not provided, a `LinuxSystemInterface` is used.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the NetworkAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
        """
        self.system = system_interface or LinuxSystemInterface()
        self.logger = logging.getLogger(__name__)
        self._network_info_cache: Optional[Dict[str, Any]] = None

    def get_network_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive information about the network hardware.

        This is the main public method of the class, which orchestrates the
        gathering of all network-related data. It collects basic and detailed
        interface information, wireless capabilities, driver details, and
        performance metrics. The result is cached to improve performance on
        subsequent calls.

        Returns:
            A dictionary containing a detailed breakdown of network information.
        """
        if self._network_info_cache is not None:
            return self._network_info_cache

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

        # Get network performance capabilities
        info.update(self.analyze_network_performance())

        self._network_info_cache = info
        return info

    def _get_basic_network_info(self) -> Dict[str, Any]:
        """Gathers basic network interface information using `ip` or `psutil`.

        This method first attempts to use `ip addr` and `ip -s link` to
        collect fundamental details about each network interface. If these
        commands fail, it falls back to using `psutil` to gather similar
        information.

        Returns:
            A dictionary containing the basic network information.
        """
        info: Dict[str, Any] = {}

        # Get network interface information using ip addr
        ip_addr_result = self.system.run_command(["ip", "-s", "addr"])
        if ip_addr_result.success:
            info["ip_addr"] = ip_addr_result.stdout
            info["interfaces"] = self._parse_ip_addr_output(ip_addr_result.stdout)
        else:
            self.logger.warning(
                "Failed to run 'ip addr', falling back to psutil: %s",
                ip_addr_result.stderr,
            )
            info["ip_addr_error"] = (
                ip_addr_result.stderr or "Failed to run ip addr, using psutil fallback"
            )
            info["interfaces"] = self._get_interfaces_from_psutil()

        # Get network interface statistics using ip -s link
        ip_link_result = self.system.run_command(["ip", "-s", "link"])
        if ip_link_result.success:
            info["ip_link"] = ip_link_result.stdout
            info.update(self._parse_ip_link_output(ip_link_result.stdout))
        else:
            self.logger.warning(
                "Failed to run 'ip -s link', skipping statistics: %s",
                ip_link_result.stderr,
            )
            info["ip_link_error"] = (
                ip_link_result.stderr or "Failed to run ip -s link"
            )

        return info

    def _get_interfaces_from_psutil(self) -> List[Dict[str, Any]]:
        """
        Retrieves network interface information using `psutil`.

        This method serves as a fallback for when the `ip` command is not
        available. It gathers interface names, addresses, and states from
        `psutil`. It handles failures in gathering addresses and stats
        gracefully.

        Returns:
            A list of dictionaries, where each dictionary represents a
            network interface. Returns an empty list if addresses cannot be
            retrieved.
        """
        interfaces: Dict[str, Dict[str, Any]] = {}
        try:
            # Get addresses
            addrs = psutil.net_if_addrs()
            for name, snics in addrs.items():
                interfaces[name] = {"name": name, "addresses": []}
                for snic in snics:
                    family_map = {
                        psutil.AF_LINK: "link",
                        2: "inet",  # AF_INET
                        10: "inet6",  # AF_INET6
                    }
                    interfaces[name]["addresses"].append(
                        {
                            "family": family_map.get(snic.family, "unknown"),
                            "address": snic.address,
                        }
                    )
        except Exception as e:
            self.logger.error("Failed to get interface addresses from psutil: %s", e)
            return []

        try:
            # Get stats for state, this is non-critical
            stats = psutil.net_if_stats()
            for name, stat in stats.items():
                if name in interfaces:
                    interfaces[name]["state"] = "UP" if stat.isup else "DOWN"
        except Exception as e:
            self.logger.warning("Could not get interface stats from psutil: %s", e)

        return list(interfaces.values())

    def _get_detailed_network_info(self) -> Dict[str, Any]:
        """Gathers detailed information about each network interface from sysfs.

        This method inspects the `/sys/class/net` directory to retrieve in-depth
        details about each network interface, such as type, speed, duplex, MTU,
        and various statistics.

        Returns:
            A dictionary containing a list of detailed interface information.
        """
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
        """Gathers information about wireless network interfaces.

        This method uses `iwconfig` and `iw` to collect details about wireless
        interfaces, including ESSID, mode, frequency, and other capabilities.

        Returns:
            A dictionary containing wireless network information.
        """
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
        elif not iw_result.success:  # pragma: no branch
            self.logger.info(
                "'iw' command not found or failed, skipping detailed wireless info."
            )

        return info

    def _get_driver_info(self) -> Dict[str, Any]:
        """Gathers information about network interface drivers.

        This method uses `ethtool` and `modinfo` to identify the driver for
        each network interface and retrieve details about the driver module.

        Returns:
            A dictionary containing driver information for each interface.
        """
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
                    driver_entry: Dict[str, Any] = {
                        "interface": interface_name,
                        "driver": driver,
                    }
                    if driver_details:
                        driver_entry["driver_details"] = driver_details
                    driver_info.append(driver_entry)

        if driver_info:
            info["driver_info"] = driver_info

        return info

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Gathers network performance metrics using `netstat` or `psutil`.

        This method first attempts to use `netstat` to collect a wide range of
        performance data. If `netstat` fails, it falls back to `psutil` to
        gather I/O statistics. It also tries to get detailed driver-specific
        statistics using `ethtool`.

        Returns:
            A dictionary containing network performance metrics.
        """
        info: Dict[str, Any] = {}

        # Get network statistics using netstat
        netstat_result = self.system.run_command(["netstat", "-i"])
        if netstat_result.success:
            info["netstat"] = netstat_result.stdout
            info["netstat_statistics"] = self._parse_netstat_output(
                netstat_result.stdout
            )
        else:
            self.logger.info(
                "'netstat' command failed, falling back to psutil: %s",
                netstat_result.stderr,
            )
            info["netstat_error"] = (
                netstat_result.stderr or "Failed to run netstat, using psutil fallback"
            )
            info["psutil_io_counters"] = self._get_psutil_io_counters()

        # Get detailed network statistics using ethtool (no psutil fallback for this)
        ls_result = self.system.run_command(["ls", "/sys/class/net/"])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
            ethtool_stats: Dict[str, Dict[str, Any]] = {}

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

    def _get_psutil_io_counters(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves network I/O counters using `psutil`.

        This method serves as a fallback for when `netstat` is not available.
        It gathers byte and packet counts, as well as errors and dropped
        packets for all network interfaces.

        Returns:
            A dictionary where keys are interface names and values are their
            I/O statistics.
        """
        try:
            io_counters = psutil.net_io_counters(pernic=True)
            return {
                iface: {
                    "bytes_sent": stats.bytes_sent,
                    "bytes_recv": stats.bytes_recv,
                    "packets_sent": stats.packets_sent,
                    "packets_recv": stats.packets_recv,
                    "errin": stats.errin,
                    "errout": stats.errout,
                    "dropin": stats.dropin,
                    "dropout": stats.dropout,
                }
                for iface, stats in io_counters.items()
            }
        except Exception as e:
            self.logger.error("Failed to get I/O counters from psutil: %s", e)
            return {}

    def _parse_ip_addr_output(self, ip_addr_output: str) -> List[Dict[str, Any]]:
        """Parses the output of the `ip addr` command.

        This method processes the raw text output from `ip addr` and extracts
        details about each network interface, including its name, state, MAC
        address, and IP addresses (both IPv4 and IPv6).

        Args:
            ip_addr_output: The raw string output from the `ip addr` command.

        Returns:
            A list of dictionaries, where each dictionary represents a network
            interface.
        """
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
        """Parses the output of the `ip -s link` command.

        This method processes the raw text output from `ip -s link` to extract
        detailed statistics for each interface, such as bytes, packets, errors,
        and dropped packets for both received (RX) and transmitted (TX) traffic.

        Args:
            ip_link_output: The raw string output from the `ip -s link` command.

        Returns:
            A dictionary containing the parsed interface statistics.
        """
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
                    if section == "rx" and len(values) >= 6:  # noqa: PLR2004
                        stats[current_interface]["rx"] = {
                            "bytes": int(values[0]),
                            "packets": int(values[1]),
                            "errors": int(values[2]),
                            "dropped": int(values[3]),
                            "overrun": int(values[4]),
                            "mcast": int(values[5]),
                        }
                        section = None  # Move to next section
                    elif section == "tx" and len(values) >= 6:  # noqa: PLR2004
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

    def _get_interface_details(self, interface_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves detailed information for a specific network interface from sysfs.

        This method reads various files from the `/sys/class/net/<interface>`
        directory to gather low-level details about an interface, including its
        type, state, speed, MTU, and hardware flags.

        Args:
            interface_name: The name of the network interface.

        Returns:
            A dictionary containing the detailed information for the specified
            interface, or None if the interface type cannot be determined.
        """
        interface_info: Dict[str, Any] = {"name": interface_name}
        sys_path = f"/sys/class/net/{interface_name}"

        def read_sys_file(file: str) -> Optional[str]:
            content = self.system.read_file(f"{sys_path}/{file}")
            return content.strip() if content else None

        type_val = read_sys_file("type")
        if not type_val:
            return None  # Skip interfaces without a type

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
        """Parses the output of the `iwconfig` command.

        This method processes the raw text output from `iwconfig` to extract
        key information about wireless interfaces, such as ESSID, mode,
        frequency, access point, bit rate, and signal level.

        Args:
            iwconfig_output: The raw string output from the `iwconfig` command.

        Returns:
            A list of dictionaries, where each dictionary represents a wireless
            interface.
        """
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
        """Parses the output of the `iw list` command.

        This method is intended to process the detailed output of `iw list` to
        extract advanced wireless capabilities. Currently, it serves as a
        placeholder and returns the raw text.

        Args:
            iw_list_output: The raw string output from the `iw list` command.

        Returns:
            A dictionary containing the parsed wireless capabilities.
        """
        # This is a placeholder for a more complex parser.
        # For now, we just return the raw text.
        return {"raw": iw_list_output}

    def _get_interface_driver(self, interface_name: str) -> Optional[str]:
        """Retrieves the driver for a specific network interface using `ethtool`.

        Args:
            interface_name: The name of the network interface.

        Returns:
            The name of the driver as a string, or None if it cannot be determined.
        """
        ethtool_result = self.system.run_command(["ethtool", "-i", interface_name])
        if ethtool_result.success:
            driver_match = re.search(r"driver:\s*(\S+)", ethtool_result.stdout)
            if driver_match:
                return driver_match.group(1)
        self.logger.info("Could not get driver for %s via ethtool.", interface_name)
        return None

    def _get_driver_details(self, driver_name: str) -> Dict[str, Any]:
        """Retrieves details for a specific network driver using `modinfo`.

        Args:
            driver_name: The name of the driver module.

        Returns:
            A dictionary containing the details of the driver module.
        """
        details = {}
        modinfo_result = self.system.run_command(["modinfo", driver_name])
        if modinfo_result.success:
            for line in modinfo_result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    details[key.strip()] = value.strip()
        return details

    def _parse_netstat_output(self, netstat_output: str) -> List[Dict[str, Any]]:
        """Parses the output of the `netstat -i` command.

        This method processes the raw text output from `netstat -i` to extract
        interface statistics, such as MTU, packet counts, and error counts.

        Args:
            netstat_output: The raw string output from the `netstat -i` command.

        Returns:
            A list of dictionaries, where each dictionary represents the
            statistics for a network interface.
        """
        interfaces: List[Dict[str, Any]] = []
        lines = netstat_output.strip().split("\n")
        if len(lines) < 2:  # noqa: PLR2004
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
        """Parses the output of the `ethtool -S` command.

        This method processes the raw text output from `ethtool -S` to extract
        detailed, driver-specific statistics for a network interface.

        Args:
            ethtool_output: The raw string output from the `ethtool -S` command.

        Returns:
            A dictionary of the parsed statistics.
        """
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

    def analyze_network_performance(self) -> Dict[str, Any]:
        """Analyzes network performance and capabilities.

        This method enriches the network information dictionary with
        performance data, such as speed and duplex, using `ethtool`. If `ethtool`
        is not available, it falls back to `psutil` for basic metrics.

        Returns:
            A dictionary containing performance capabilities.
        """
        capabilities: Dict[str, Any] = {}
        ls_result = self.system.run_command(["ls", "/sys/class/net/"])

        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
            for interface_name in interface_names:
                if interface_name == "lo":
                    continue

                ethtool_result = self.system.run_command(["ethtool", interface_name])
                if ethtool_result.success:
                    capabilities[interface_name] = self._parse_ethtool_capabilities(
                        ethtool_result.stdout
                    )
                else:
                    self.logger.info(
                        "Could not get ethtool data for %s, falling back to psutil.",
                        interface_name,
                    )
                    try:
                        stats = psutil.net_if_stats()
                        if interface_name in stats:
                            capabilities[interface_name] = {
                                "speed": stats[interface_name].speed,
                                "duplex": stats[interface_name].duplex,
                                "mtu": stats[interface_name].mtu,
                            }
                    except Exception as e:
                        self.logger.error(
                            "Failed to get psutil stats for %s: %s", interface_name, e
                        )

        if capabilities:
            return {"performance_capabilities": capabilities}
        return {}

    def _parse_ethtool_capabilities(self, ethtool_output: str) -> Dict[str, Any]:
        """Parses the output of the `ethtool` command for capabilities.

        Args:
            ethtool_output: The raw string output from the `ethtool` command.

        Returns:
            A dictionary of the parsed capabilities.
        """
        capabilities: Dict[str, Any] = {}
        for line_raw in ethtool_output.strip().split("\n"):
            line = line_raw.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                if key in ["speed", "duplex"]:
                    capabilities[key] = value
        return capabilities
