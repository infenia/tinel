#!/usr/bin/env python3
"""Enhanced Network Hardware Analysis Module.

This module provides detailed network interface information gathering including
capabilities detection, driver information, and performance metrics.

Copyright 2024 Infenia Private Limited

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

import re
import json
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
        ip_addr_result = self.system.run_command(['ip', '-s', 'addr'])
        if ip_addr_result.success:
            info['ip_addr'] = ip_addr_result.stdout
            info['interfaces'] = self._parse_ip_addr_output(ip_addr_result.stdout)
        else:
            info['ip_addr_error'] = ip_addr_result.error or 'Failed to run ip addr'
        
        # Get network interface statistics using ip -s link
        ip_link_result = self.system.run_command(['ip', '-s', 'link'])
        if ip_link_result.success:
            info['ip_link'] = ip_link_result.stdout
            info.update(self._parse_ip_link_output(ip_link_result.stdout))
        else:
            info['ip_link_error'] = ip_link_result.error or 'Failed to run ip -s link'
        
        return info
    
    def _get_detailed_network_info(self) -> Dict[str, Any]:
        """Get detailed network interface information."""
        info: Dict[str, Any] = {}
        interfaces = []
        
        # Get list of network interfaces
        ls_result = self.system.run_command(['ls', '/sys/class/net/'])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
            
            for interface_name in interface_names:
                # Skip loopback interface
                if interface_name == 'lo':
                    continue
                
                interface_info = self._get_interface_details(interface_name)
                if interface_info:
                    interfaces.append(interface_info)
        
        if interfaces:
            info['detailed_interfaces'] = interfaces
        
        return info
    
    def _get_wireless_info(self) -> Dict[str, Any]:
        """Get wireless network information."""
        info: Dict[str, Any] = {}
        
        # Get wireless interface information using iwconfig
        iwconfig_result = self.system.run_command(['iwconfig'])
        if iwconfig_result.success and iwconfig_result.stdout.strip():
            info['iwconfig'] = iwconfig_result.stdout
            info['wireless_interfaces'] = self._parse_iwconfig_output(iwconfig_result.stdout)
        
        # Get detailed wireless information using iw
        iw_result = self.system.run_command(['iw', 'list'])
        if iw_result.success:
            info['iw_list'] = iw_result.stdout
            info['wireless_capabilities'] = self._parse_iw_list_output(iw_result.stdout)
        
        return info
    
    def _get_driver_info(self) -> Dict[str, Any]:
        """Get network interface driver information."""
        info: Dict[str, Any] = {}
        driver_info = []
        
        # Get list of network interfaces
        ls_result = self.system.run_command(['ls', '/sys/class/net/'])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
            
            for interface_name in interface_names:
                # Skip loopback interface
                if interface_name == 'lo':
                    continue
                
                driver = self._get_interface_driver(interface_name)
                if driver:
                    driver_info.append({
                        'interface': interface_name,
                        'driver': driver
                    })
                    
                    # Get driver details
                    driver_details = self._get_driver_details(driver)
                    if driver_details:
                        driver_info[-1]['driver_details'] = driver_details
        
        if driver_info:
            info['driver_info'] = driver_info
        
        return info
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get network performance metrics."""
        info: Dict[str, Any] = {}
        
        # Get network statistics using netstat
        netstat_result = self.system.run_command(['netstat', '-i'])
        if netstat_result.success:
            info['netstat'] = netstat_result.stdout
            info['interface_statistics'] = self._parse_netstat_output(netstat_result.stdout)
        
        # Get detailed network statistics using ethtool
        ls_result = self.system.run_command(['ls', '/sys/class/net/'])
        if ls_result.success:
            interface_names = ls_result.stdout.strip().split()
            ethtool_stats = {}
            
            for interface_name in interface_names:
                # Skip loopback interface
                if interface_name == 'lo':
                    continue
                
                # Get interface statistics using ethtool
                ethtool_result = self.system.run_command(['sudo', 'ethtool', '-S', interface_name])
                if ethtool_result.success:
                    ethtool_stats[interface_name] = self._parse_ethtool_output(ethtool_result.stdout)
            
            if ethtool_stats:
                info['ethtool_statistics'] = ethtool_stats
        
        return info
    
    def _parse_ip_addr_output(self, ip_addr_output: str) -> List[Dict[str, Any]]:
        """Parse ip addr output."""
        interfaces = []
        current_interface = None
        
        for line in ip_addr_output.strip().split('\n'):
            # New interface
            if not line.startswith(' '):
                if current_interface:
                    interfaces.append(current_interface)
                
                # Extract interface name and index
                match = re.match(r'^\d+: ([^:@]+)(@[^:]+)?:', line)
                if match:
                    interface_name = match.group(1)
                    current_interface = {
                        'name': interface_name,
                        'addresses': []
                    }
                    
                    # Extract interface state
                    state_match = re.search(r'state (\w+)', line)
                    if state_match:
                        current_interface['state'] = state_match.group(1)
                    
                    # Extract MAC address
                    mac_match = re.search(r'link/\w+ ([0-9a-f:]+)', line)
                    if mac_match:
                        current_interface['mac'] = mac_match.group(1)
            
            # IP address line
            elif current_interface and 'inet' in line:
                # IPv4 address
                if 'inet ' in line:
                    ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+/\d+)', line)
                    if ip_match:
                        current_interface['addresses'].append({
                            'family': 'inet',
                            'address': ip_match.group(1)
                        })
                
                # IPv6 address
                elif 'inet6' in line:
                    ip_match = re.search(r'inet6 ([0-9a-f:]+/\d+)', line)
                    if ip_match:
                        current_interface['addresses'].append({
                            'family': 'inet6',
                            'address': ip_match.group(1)
                        })
        
        # Add the last interface
        if current_interface:
            interfaces.append(current_interface)
        
        return interfaces
    
    def _parse_ip_link_output(self, ip_link_output: str) -> Dict[str, Any]:
        """Parse ip -s link output."""
        info: Dict[str, Any] = {}
        interface_stats = {}
        current_interface = None
        
        for line in ip_link_output.strip().split('\n'):
            # New interface
            if not line.startswith(' '):
                # Extract interface name and index
                match = re.match(r'^\d+: ([^:@]+)(@[^:]+)?:', line)
                if match:
                    current_interface = match.group(1)
                    interface_stats[current_interface] = {
                        'rx': {},
                        'tx': {}
                    }
            
            # RX statistics
            elif current_interface and 'RX:' in line:
                rx_match = re.search(r'RX:\s+bytes\s+packets\s+errors\s+dropped\s+overrun\s+mcast\s*', line)
                if rx_match:
                    # Next line contains the values
                    continue
            
            # RX values
            elif current_interface and 'rx_stats' not in interface_stats[current_interface]:
                values = line.strip().split()
                if len(values) >= 6:
                    interface_stats[current_interface]['rx_stats'] = {
                        'bytes': int(values[0]),
                        'packets': int(values[1]),
                        'errors': int(values[2]),
                        'dropped': int(values[3]),
                        'overrun': int(values[4]),
                        'mcast': int(values[5])
                    }
            
            # TX statistics
            elif current_interface and 'TX:' in line:
                tx_match = re.search(r'TX:\s+bytes\s+packets\s+errors\s+dropped\s+carrier\s+collsns\s*', line)
                if tx_match:
                    # Next line contains the values
                    continue
            
            # TX values
            elif current_interface and 'tx_stats' not in interface_stats[current_interface] and 'rx_stats' in interface_stats[current_interface]:
                values = line.strip().split()
                if len(values) >= 6:
                    interface_stats[current_interface]['tx_stats'] = {
                        'bytes': int(values[0]),
                        'packets': int(values[1]),
                        'errors': int(values[2]),
                        'dropped': int(values[3]),
                        'carrier': int(values[4]),
                        'collisions': int(values[5])
                    }
        
        info['interface_statistics'] = interface_stats
        return info
    
    def _get_interface_details(self, interface_name: str) -> Dict[str, Any]:
        """Get detailed information for a specific network interface."""
        interface_info = {'name': interface_name}
        
        # Get interface type
        type_path = f'/sys/class/net/{interface_name}/type'
        interface_type = self.system.read_file(type_path)
        if interface_type:
            # Convert type number to human-readable form
            type_map = {
                '1': 'ethernet',
                '772': 'loopback',
                '801': 'wireless',
                '24': 'firewire',
                '32': 'infiniband'
            }
            interface_info['type'] = type_map.get(interface_type.strip(), interface_type.strip())
        
        # Get interface speed
        speed_path = f'/sys/class/net/{interface_name}/speed'
        speed = self.system.read_file(speed_path)
        if speed and speed.strip() != '-1':
            interface_info['speed'] = f'{speed.strip()} Mbps'
        
        # Get interface duplex mode
        duplex_path = f'/sys/class/net/{interface_name}/duplex'
        duplex = self.system.read_file(duplex_path)
        if duplex:
            interface_info['duplex'] = duplex.strip()
        
        # Get interface MTU
        mtu_path = f'/sys/class/net/{interface_name}/mtu'
        mtu = self.system.read_file(mtu_path)
        if mtu:
            interface_info['mtu'] = int(mtu.strip())
        
        # Get interface carrier status
        carrier_path = f'/sys/class/net/{interface_name}/carrier'
        carrier = self.system.read_file(carrier_path)
        if carrier:
            interface_info['carrier'] = carrier.strip() == '1'
        
        # Get interface operstate
        operstate_path = f'/sys/class/net/{interface_name}/operstate'
        operstate = self.system.read_file(operstate_path)
        if operstate:
            interface_info['operstate'] = operstate.strip()
        
        # Get interface address
        address_path = f'/sys/class/net/{interface_name}/address'
        address = self.system.read_file(address_path)
        if address:
            interface_info['mac'] = address.strip()
        
        # Get interface flags
        flags_path = f'/sys/class/net/{interface_name}/flags'
        flags = self.system.read_file(flags_path)
        if flags:
            interface_info['flags'] = int(flags.strip(), 16)
            
            # Decode common flags
            flag_map = {
                0x1: 'UP',
                0x2: 'BROADCAST',
                0x4: 'DEBUG',
                0x8: 'LOOPBACK',
                0x10: 'POINTOPOINT',
                0x20: 'NOTRAILERS',
                0x40: 'RUNNING',
                0x80: 'NOARP',
                0x100: 'PROMISC',
                0x200: 'ALLMULTI',
                0x400: 'MASTER',
                0x800: 'SLAVE',
                0x1000: 'MULTICAST',
                0x2000: 'PORTSEL',
                0x4000: 'AUTOMEDIA',
                0x8000: 'DYNAMIC',
                0x10000: 'LOWER_UP',
                0x20000: 'DORMANT',
                0x40000: 'ECHO'
            }
            
            decoded_flags = []
            for flag_value, flag_name in flag_map.items():
                if int(flags.strip(), 16) & flag_value:
                    decoded_flags.append(flag_name)
            
            interface_info['decoded_flags'] = decoded_flags
        
        # Get interface statistics
        statistics = {}
        statistics_path = f'/sys/class/net/{interface_name}/statistics'
        if self.system.file_exists(statistics_path):
            # List statistics files
            ls_result = self.system.run_command(['ls', statistics_path])
            if ls_result.success:
                for stat_file in ls_result.stdout.strip().split():
                    stat_value = self.system.read_file(f'{statistics_path}/{stat_file}')
                    if stat_value:
                        statistics[stat_file] = int(stat_value.strip())
        
        if statistics:
            interface_info['statistics'] = statistics
        
        return interface_info
    
    def _parse_iwconfig_output(self, iwconfig_output: str) -> List[Dict[str, Any]]:
        """Parse iwconfig output."""
        interfaces = []
        current_interface = None
        
        for line in iwconfig_output.strip().split('\n'):
            # New interface
            if not line.startswith(' '):
                if current_interface:
                    interfaces.append(current_interface)
                
                # Extract interface name
                match = re.match(r'^(\S+)', line)
                if match:
                    interface_name = match.group(1)
                    
                    # Skip interfaces without wireless extensions
                    if 'no wireless extensions' in line:
                        current_interface = None
                        continue
                    
                    current_interface = {
                        'name': interface_name
                    }
                    
                    # Extract ESSID
                    essid_match = re.search(r'ESSID:"([^"]*)"', line)
                    if essid_match:
                        current_interface['essid'] = essid_match.group(1)
                    
                    # Extract mode
                    mode_match = re.search(r'Mode:(\S+)', line)
                    if mode_match:
                        current_interface['mode'] = mode_match.group(1)
            
            # Additional wireless information
            elif current_interface:
                # Extract frequency
                freq_match = re.search(r'Frequency[=:]\s*(\d+\.\d+)\s*GHz', line)
                if freq_match:
                    current_interface['frequency'] = float(freq_match.group(1))
                
                # Extract access point
                ap_match = re.search(r'Access Point:\s*([0-9A-Fa-f:]+)', line)
                if ap_match:
                    current_interface['access_point'] = ap_match.group(1)
                
                # Extract bit rate
                bitrate_match = re.search(r'Bit Rate[=:]\s*(\d+\.?\d*)\s*([GMk]b/s)', line)
                if bitrate_match:
                    rate = float(bitrate_match.group(1))
                    unit = bitrate_match.group(2)
                    current_interface['bit_rate'] = f'{rate} {unit}'
                
                # Extract signal level
                signal_match = re.search(r'Signal level[=:]\s*(-?\d+)\s*dBm', line)
                if signal_match:
                    current_interface['signal_level'] = int(signal_match.group(1))
        
        # Add the last interface
        if current_interface:
            interfaces.append(current_interface)
        
        return interfaces
    
    def _parse_iw_list_output(self, iw_list_output: str) -> Dict[str, Any]:
        """Parse iw list output."""
        capabilities = {}
        current_phy = None
        
        for line in iw_list_output.strip().split('\n'):
            # New PHY
            if line.startswith('Wiphy '):
                phy_match = re.match(r'Wiphy (\S+)', line)
                if phy_match:
                    current_phy = phy_match.group(1)
                    capabilities[current_phy] = {}
            
            # Supported interface modes
            elif current_phy and 'Supported interface modes' in line:
                modes = []
                # Read the next lines for modes
                mode_section = iw_list_output.split('Supported interface modes')[1].split('\n\t')[0]
                for mode_line in mode_section.strip().split('\n'):
                    mode_match = re.search(r'\* (\S+)', mode_line)
                    if mode_match:
                        modes.append(mode_match.group(1))
                
                if modes:
                    capabilities[current_phy]['supported_modes'] = modes
            
            # Supported bands
            elif current_phy and 'Band ' in line:
                band_match = re.match(r'\tBand (\d+):', line)
                if band_match:
                    band = band_match.group(1)
                    if 'bands' not in capabilities[current_phy]:
                        capabilities[current_phy]['bands'] = {}
                    
                    capabilities[current_phy]['bands'][band] = {}
                    
                    # Extract frequencies
                    freq_section = iw_list_output.split(f'Band {band}:')[1].split('Band')[0] if 'Band' in iw_list_output.split(f'Band {band}:')[1] else iw_list_output.split(f'Band {band}:')[1]
                    frequencies = []
                    
                    for freq_line in freq_section.strip().split('\n'):
                        freq_match = re.search(r'(\d+) MHz', freq_line)
                        if freq_match:
                            frequencies.append(int(freq_match.group(1)))
                    
                    if frequencies:
                        capabilities[current_phy]['bands'][band]['frequencies'] = frequencies
        
        return capabilities
    
    def _get_interface_driver(self, interface_name: str) -> Optional[str]:
        """Get driver for a specific network interface."""
        # Check if driver information is available in sysfs
        driver_path = f'/sys/class/net/{interface_name}/device/driver'
        if self.system.file_exists(driver_path):
            # Get the driver name (last part of the symlink)
            driver_link = self.system.run_command(['readlink', '-f', driver_path])
            if driver_link.success:
                driver_parts = driver_link.stdout.strip().split('/')
                if driver_parts:
                    return driver_parts[-1]
        
        # Alternative method using ethtool
        ethtool_result = self.system.run_command(['ethtool', '-i', interface_name])
        if ethtool_result.success:
            driver_match = re.search(r'driver:\s*(\S+)', ethtool_result.stdout)
            if driver_match:
                return driver_match.group(1)
        
        return None
    
    def _get_driver_details(self, driver_name: str) -> Dict[str, Any]:
        """Get details for a specific network driver."""
        details = {}
        
        # Check if driver module information is available
        modinfo_result = self.system.run_command(['modinfo', driver_name])
        if modinfo_result.success:
            # Extract version
            version_match = re.search(r'version:\s*(.+)', modinfo_result.stdout)
            if version_match:
                details['version'] = version_match.group(1).strip()
            
            # Extract author
            author_match = re.search(r'author:\s*(.+)', modinfo_result.stdout)
            if author_match:
                details['author'] = author_match.group(1).strip()
            
            # Extract description
            description_match = re.search(r'description:\s*(.+)', modinfo_result.stdout)
            if description_match:
                details['description'] = description_match.group(1).strip()
            
            # Extract license
            license_match = re.search(r'license:\s*(.+)', modinfo_result.stdout)
            if license_match:
                details['license'] = license_match.group(1).strip()
            
            # Extract firmware
            firmware_match = re.search(r'firmware:\s*(.+)', modinfo_result.stdout)
            if firmware_match:
                details['firmware'] = firmware_match.group(1).strip()
        
        return details
    
    def _parse_netstat_output(self, netstat_output: str) -> List[Dict[str, Any]]:
        """Parse netstat -i output."""
        interfaces = []
        
        lines = netstat_output.strip().split('\n')
        if len(lines) < 2:
            return interfaces
        
        # Get headers
        headers = re.split(r'\s+', lines[0].strip())
        
        # Parse interface statistics
        for line in lines[1:]:
            if not line.strip():
                continue
            
            values = re.split(r'\s+', line.strip())
            if len(values) >= len(headers):
                interface_stats = {}
                for i, header in enumerate(headers):
                    interface_stats[header.lower()] = values[i]
                
                interfaces.append(interface_stats)
        
        return interfaces
    
    def _parse_ethtool_output(self, ethtool_output: str) -> Dict[str, Any]:
        """Parse ethtool -S output."""
        stats = {}
        
        for line in ethtool_output.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                stats[key.strip()] = int(value.strip())
        
        return stats