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

from tinel.hardware.models import (
    DriverInfo,
    NetworkInfo,
    NetworkInterface,
    PerformanceMetrics,
    WirelessInterface,
)


class NetworkAnalyzer:
    """Analyzes and retrieves detailed information about network hardware."""

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the NetworkAnalyzer."""
        self.system = system_interface or LinuxSystemInterface()
        self.logger = logging.getLogger(__name__)
        self._network_info_cache: Optional[NetworkInfo] = None

    def get_network_info(self) -> NetworkInfo:
        """Retrieves comprehensive information about the network hardware."""
        if self._network_info_cache is not None:
            return self._network_info_cache

        interfaces = self._get_basic_network_info()
        detailed_interfaces = self._get_detailed_network_info()
        wireless_info = self._get_wireless_info()
        driver_info = self._get_driver_info()
        performance_metrics = self._get_performance_metrics()
        performance_caps = self.analyze_network_performance()

        merged_interfaces: Dict[str, NetworkInterface] = {
            iface.name: iface for iface in interfaces if iface.name
        }
        for det_iface in detailed_interfaces:
            if det_iface.name in merged_interfaces:
                existing = merged_interfaces[det_iface.name]
                for key, value in det_iface.__dict__.items():
                    if value is not None:
                        setattr(existing, key, value)
            else:
                merged_interfaces[det_iface.name] = det_iface

        info = NetworkInfo(
            interfaces=list(merged_interfaces.values()),
            wireless_interfaces=wireless_info,
            driver_info=driver_info,
            performance_metrics=performance_metrics,
            performance_capabilities=performance_caps,
        )

        self._network_info_cache = info
        return info

    def _get_basic_network_info(self) -> List[NetworkInterface]:
        """Gathers basic network interface information."""
        ip_addr_result = self.system.run_command(["ip", "-s", "addr"])
        if ip_addr_result.success:
            interfaces = self._parse_ip_addr_output(ip_addr_result.stdout)
        else:
            self.logger.warning(
                "Failed to run 'ip addr', falling back to psutil: %s",
                ip_addr_result.stderr,
            )
            interfaces = self._get_interfaces_from_psutil()

        ip_link_result = self.system.run_command(["ip", "-s", "link"])
        if ip_link_result.success:
            link_stats = self._parse_ip_link_output(ip_link_result.stdout)
            for iface in interfaces:
                if iface.name and iface.name in link_stats:
                    iface.statistics = link_stats[iface.name]
        else:
            self.logger.warning(
                "Failed to run 'ip -s link', skipping statistics: %s",
                ip_link_result.stderr,
            )
        return interfaces

    def _get_interfaces_from_psutil(self) -> List[NetworkInterface]:
        """Retrieves network interface information using `psutil`."""
        interfaces: Dict[str, NetworkInterface] = {}
        try:
            addrs = psutil.net_if_addrs()
            for name, snics in addrs.items():
                interfaces[name] = NetworkInterface(name=name, addresses=[])
                for snic in snics:
                    family_map = {
                        psutil.AF_LINK: "link",
                        2: "inet",
                        10: "inet6",
                    }
                    if interfaces[name].addresses is not None:
                        interfaces[name].addresses.append(
                            {
                                "family": family_map.get(snic.family, "unknown"),
                                "address": snic.address,
                            }
                        )
        except Exception as e:
            self.logger.error("Failed to get interface addresses from psutil: %s", e)
            return []

        try:
            stats = psutil.net_if_stats()
            for name, stat in stats.items():
                if name in interfaces:
                    interfaces[name].state = "UP" if stat.isup else "DOWN"
        except Exception as e:
            self.logger.warning("Could not get interface stats from psutil: %s", e)

        return list(interfaces.values())

    def _get_detailed_network_info(self) -> List[NetworkInterface]:
        """Gathers detailed information about each network interface from sysfs."""
        interfaces = []
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
        return interfaces

    def _get_wireless_info(self) -> List[WirelessInterface]:
        """Gathers information about wireless network interfaces."""
        iwconfig_result = self.system.run_command(["iwconfig"])
        if iwconfig_result.success and iwconfig_result.stdout.strip():
            return self._parse_iwconfig_output(iwconfig_result.stdout)

        self.logger.info(
            "'iwconfig' command not found or failed, skipping wireless info."
        )
        return []

    def _get_driver_info(self) -> List[DriverInfo]:
        """Gathers information about network interface drivers."""
        driver_info = []
        ls_result = self.system.run_command(["ls", "/sys/class/net/"])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
            for interface_name in interface_names:
                if interface_name == "lo":
                    continue
                driver = self._get_interface_driver(interface_name)
                if driver:
                    driver_details = self._get_driver_details(driver)
                    driver_info.append(
                        DriverInfo(
                            interface=interface_name,
                            driver=driver,
                            driver_details=driver_details,
                        )
                    )
        return driver_info

    def _get_performance_metrics(self) -> PerformanceMetrics:
        """Gathers network performance metrics."""
        netstat_stats = []
        psutil_counters = {}
        ethtool_stats: Dict[str, Dict[str, Any]] = {}

        netstat_result = self.system.run_command(["netstat", "-i"])
        if netstat_result.success:
            netstat_stats = self._parse_netstat_output(netstat_result.stdout)
        else:
            self.logger.info(
                "'netstat' command failed, falling back to psutil: %s",
                netstat_result.stderr,
            )
            psutil_counters = self._get_psutil_io_counters()

        ls_result = self.system.run_command(["ls", "/sys/class/net/"])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
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
        return PerformanceMetrics(
            netstat_statistics=netstat_stats,
            psutil_io_counters=psutil_counters,
            ethtool_statistics=ethtool_stats,
        )

    def _get_psutil_io_counters(self) -> Dict[str, Any]:
        """Retrieves network I/O counters using `psutil`."""
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

    def _parse_ip_addr_output(self, ip_addr_output: str) -> List[NetworkInterface]:
        """Parses the output of the `ip addr` command."""
        interfaces = []
        current_interface: Optional[NetworkInterface] = None

        for line in ip_addr_output.strip().split("\n"):
            if not line.startswith(" "):
                if current_interface:
                    interfaces.append(current_interface)
                current_interface = None

                match = re.match(r"^\d+: ([^:@]+)(@[^:]+)?:", line)
                if match:
                    interface_name = match.group(1)
                    current_interface = NetworkInterface(
                        name=interface_name, addresses=[]
                    )
                    state_match = re.search(r"state (\w+)", line)
                    if state_match:
                        current_interface.state = state_match.group(1)

            elif current_interface:
                mac_match = re.search(r"link/\w+ ([0-9a-fA-F:]+)", line)
                if mac_match:
                    current_interface.mac = mac_match.group(1)

                if "inet " in line:
                    ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+/\d+)", line)
                    if ip_match and current_interface.addresses is not None:
                        current_interface.addresses.append(
                            {"family": "inet", "address": ip_match.group(1)}
                        )
                elif "inet6 " in line:
                    ip_match = re.search(r"inet6 ([0-9a-fA-F:]+/\d+)", line)
                    if ip_match and current_interface.addresses is not None:
                        current_interface.addresses.append(
                            {"family": "inet6", "address": ip_match.group(1)}
                        )

        if current_interface:
            interfaces.append(current_interface)

        return interfaces

    def _parse_ip_link_output(self, ip_link_output: str) -> Dict[str, Any]:
        """Parses the output of the `ip -s link` command."""
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
                        section = None
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
        return stats

    def _get_interface_details(self, interface_name: str) -> Optional[NetworkInterface]:
        """Retrieves detailed information for a specific network interface."""
        sys_path = f"/sys/class/net/{interface_name}"

        def read_sys_file(file: str) -> Optional[str]:
            content = self.system.read_file(f"{sys_path}/{file}")
            return content.strip() if content else None

        type_val = read_sys_file("type")
        if not type_val:
            return None

        type_map = {"1": "ethernet", "772": "loopback"}
        iface_type = type_map.get(type_val, f"unknown ({type_val})")
        interface_info = NetworkInterface(name=interface_name, type=iface_type)

        for key in ["speed", "duplex", "mtu", "carrier", "operstate"]:
            value = read_sys_file(key)
            if value:
                setattr(
                    interface_info, key, int(value) if value.isdigit() else value
                )

        interface_info.address = read_sys_file("address")
        businfo_path = self.system.readlink(f"{sys_path}/device")
        if businfo_path:
            interface_info.businfo = businfo_path.split("/")[-1]

        driver_version = read_sys_file("device/driver/module/version")
        if driver_version:
            interface_info.driverversion = driver_version

        flags_val = read_sys_file("flags")
        if flags_val and isinstance(flags_val, str):
            flags = int(flags_val, 16)
            interface_info.flags = flags
            flag_map = {
                0x1: "UP",
                0x2: "BROADCAST",
                0x8: "LOOPBACK",
                0x40: "RUNNING",
                0x1000: "MULTICAST",
                0x10000: "LOWER_UP",
            }
            interface_info.decoded_flags = [
                name for val, name in flag_map.items() if flags & val
            ]

        stats: Dict[str, Any] = {}
        stats_path = f"{sys_path}/statistics"
        ls_result = self.system.run_command(["ls", stats_path])
        if ls_result.success:
            for stat_file in ls_result.stdout.strip().split():
                stat_value = self.system.read_file(f"{stats_path}/{stat_file}")
                if stat_value:
                    stats[stat_file] = int(stat_value.strip())
        if stats:
            interface_info.statistics = stats

        return interface_info

    def _parse_iwconfig_output(self, iwconfig_output: str) -> List[WirelessInterface]:
        """Parses the output of the `iwconfig` command."""
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

            interface_info = WirelessInterface(name=name)

            essid_match = re.search(r'ESSID:"([^"]*)"', block)
            if essid_match:
                interface_info.essid = essid_match.group(1)

            mode_match = re.search(r"Mode:(\S+)", block)
            if mode_match:
                interface_info.mode = mode_match.group(1)

            freq_match = re.search(r"Frequency:(\d+\.\d+ GHz)", block)
            if freq_match:
                interface_info.frequency = freq_match.group(1)

            ap_match = re.search(r"Access Point: ([0-9A-Fa-f:]+)", block)
            if ap_match:
                interface_info.access_point = ap_match.group(1)

            bitrate_match = re.search(r"Bit Rate=([\d\.]+\s\w+/s)", block)
            if bitrate_match:
                interface_info.bit_rate = bitrate_match.group(1)

            signal_match = re.search(r"Signal level=(-?\d+ dBm)", block)
            if signal_match:
                interface_info.signal_level = signal_match.group(1)

            interfaces.append(interface_info)
        return interfaces

    def _parse_iw_list_output(self, iw_list_output: str) -> Dict[str, Any]:
        """Parses the output of the `iw list` command."""
        return {"raw": iw_list_output}

    def _get_interface_driver(self, interface_name: str) -> Optional[str]:
        """Retrieves the driver for a specific network interface."""
        ethtool_result = self.system.run_command(["ethtool", "-i", interface_name])
        if ethtool_result.success:
            driver_match = re.search(r"driver:\s*(\S+)", ethtool_result.stdout)
            if driver_match:
                return driver_match.group(1)
        self.logger.info("Could not get driver for %s via ethtool.", interface_name)
        return None

    def _get_driver_details(self, driver_name: str) -> Dict[str, Any]:
        """Retrieves details for a specific network driver using `modinfo`."""
        details = {}
        modinfo_result = self.system.run_command(["modinfo", driver_name])
        if modinfo_result.success:
            for line in modinfo_result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    details[key.strip()] = value.strip()
        return details

    def _parse_netstat_output(
        self, netstat_output: str
    ) -> List[Dict[str, Any]]:
        """Parses the output of the `netstat -i` command."""
        interfaces: List[Dict[str, Any]] = []
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
        """Parses the output of the `ethtool -S` command."""
        stats = {}
        for line in ethtool_output.strip().split("\n")[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key and value.isdigit():
                    stats[key] = int(value)
        return stats

    def analyze_network_performance(self) -> Dict[str, Any]:
        """Analyzes network performance and capabilities."""
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
        return capabilities

    def _parse_ethtool_capabilities(self, ethtool_output: str) -> Dict[str, Any]:
        """Parses the output of the `ethtool` command for capabilities."""
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