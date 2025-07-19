#!/usr/bin/env python3
"""Enhanced PCI Device Analysis Module.

This module provides detailed PCI device information gathering including vendor
information, driver details, and compatibility analysis.

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


class PCIAnalyzer:
    """Enhanced PCI device analyzer with detailed vendor information."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize PCI analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # PCI vendor and device ID database
        self.vendor_db = {}
        self.device_db = {}
        self._load_pci_ids()
    
    def get_pci_devices(self) -> Dict[str, Any]:
        """Get comprehensive PCI device information.
        
        Returns:
            Dictionary containing detailed PCI device information
        """
        info: Dict[str, Any] = {}
        
        # Get basic PCI device info
        info.update(self._get_basic_pci_info())
        
        # Get detailed PCI device information
        info.update(self._get_detailed_pci_info())
        
        # Get driver information
        info.update(self._get_driver_info())
        
        # Get compatibility analysis
        info.update(self._analyze_compatibility())
        
        return info
    
    def _get_basic_pci_info(self) -> Dict[str, Any]:
        """Get basic PCI device information using lspci."""
        info: Dict[str, Any] = {}
        
        # Get PCI device information using lspci
        lspci_result = self.system.run_command(['lspci', '-mm'])
        if lspci_result.success:
            info['lspci'] = lspci_result.stdout
            info['devices'] = self._parse_lspci_output(lspci_result.stdout)
        else:
            info['lspci_error'] = lspci_result.error or 'Failed to run lspci'
        
        return info
    
    def _get_detailed_pci_info(self) -> Dict[str, Any]:
        """Get detailed PCI device information."""
        info: Dict[str, Any] = {}
        devices = []
        
        # Get detailed PCI device information using lspci -vvv
        lspci_detailed_result = self.system.run_command(['lspci', '-vvv'])
        if lspci_detailed_result.success:
            info['lspci_detailed'] = lspci_detailed_result.stdout
            devices = self._parse_lspci_detailed(lspci_detailed_result.stdout)
            info['detailed_devices'] = devices
        else:
            info['lspci_detailed_error'] = lspci_detailed_result.error or 'Failed to run lspci -vvv'
        
        return info
    
    def _get_driver_info(self) -> Dict[str, Any]:
        """Get PCI device driver information."""
        info: Dict[str, Any] = {}
        driver_info = []
        
        # Get list of PCI devices
        lspci_result = self.system.run_command(['lspci', '-n'])
        if lspci_result.success:
            pci_addresses = self._extract_pci_addresses(lspci_result.stdout)
            
            for address in pci_addresses:
                driver = self._get_device_driver(address)
                if driver:
                    driver_info.append({
                        'address': address,
                        'driver': driver
                    })
        
        if driver_info:
            info['driver_info'] = driver_info
        
        return info
    
    def _analyze_compatibility(self) -> Dict[str, Any]:
        """Analyze PCI device compatibility."""
        info: Dict[str, Any] = {}
        compatibility_issues = []
        
        # Get kernel version
        kernel_version_result = self.system.run_command(['uname', '-r'])
        if kernel_version_result.success:
            kernel_version = kernel_version_result.stdout.strip()
            info['kernel_version'] = kernel_version
        
        # Get list of PCI devices with their drivers
        lspci_result = self.system.run_command(['lspci', '-k'])
        if lspci_result.success:
            # Check for devices without drivers
            no_driver_devices = self._find_devices_without_drivers(lspci_result.stdout)
            for device in no_driver_devices:
                compatibility_issues.append({
                    'type': 'missing_driver',
                    'device': device,
                    'recommendation': 'Install appropriate driver for this device'
                })
            
            # Check for devices with known compatibility issues
            compatibility_issues.extend(self._check_known_compatibility_issues(lspci_result.stdout))
        
        if compatibility_issues:
            info['compatibility_issues'] = compatibility_issues
        
        return info
    
    def _parse_lspci_output(self, lspci_output: str) -> List[Dict[str, Any]]:
        """Parse lspci -mm output."""
        devices = []
        
        for line in lspci_output.strip().split('\n'):
            if line.strip():
                # Parse the machine-readable format
                parts = re.findall(r'"([^"]*)"', line)
                if len(parts) >= 4:
                    address = parts[0]
                    device_class = parts[1]
                    vendor = parts[2]
                    device = parts[3]
                    
                    device_info = {
                        'address': address,
                        'class': device_class,
                        'vendor': vendor,
                        'device': device
                    }
                    
                    # Add subsystem information if available
                    if len(parts) >= 6:
                        device_info['subsystem_vendor'] = parts[4]
                        device_info['subsystem_device'] = parts[5]
                    
                    devices.append(device_info)
        
        return devices
    
    def _parse_lspci_detailed(self, lspci_output: str) -> List[Dict[str, Any]]:
        """Parse lspci -vvv output."""
        devices = []
        device_sections = re.split(r'\n(?=[\da-f]{2}:[\da-f]{2}\.[\da-f] )', lspci_output)
        
        for section in device_sections:
            if not section.strip():
                continue
            
            device_info = {}
            
            # Extract address and basic info
            address_match = re.match(r'^([\da-f]{2}:[\da-f]{2}\.[\da-f}) (.+):', section)
            if address_match:
                device_info['address'] = address_match.group(1)
                device_info['description'] = address_match.group(2)
            
            # Extract device and vendor IDs
            id_match = re.search(r'^\s*Device: (\w+):(\w+)', section, re.MULTILINE)
            if id_match:
                vendor_id = id_match.group(1)
                device_id = id_match.group(2)
                device_info['vendor_id'] = vendor_id
                device_info['device_id'] = device_id
                
                # Add vendor and device names from database
                if vendor_id in self.vendor_db:
                    device_info['vendor_name'] = self.vendor_db[vendor_id]
                
                vendor_device_key = f"{vendor_id}:{device_id}"
                if vendor_id in self.device_db and device_id in self.device_db[vendor_id]:
                    device_info['device_name'] = self.device_db[vendor_id][device_id]
            
            # Extract subsystem information
            subsys_match = re.search(r'^\s*Subsystem: (\w+):(\w+)', section, re.MULTILINE)
            if subsys_match:
                device_info['subsystem_vendor_id'] = subsys_match.group(1)
                device_info['subsystem_device_id'] = subsys_match.group(2)
            
            # Extract kernel driver
            driver_match = re.search(r'^\s*Kernel driver in use: (.+)$', section, re.MULTILINE)
            if driver_match:
                device_info['driver'] = driver_match.group(1)
            
            # Extract kernel modules
            modules_match = re.search(r'^\s*Kernel modules: (.+)$', section, re.MULTILINE)
            if modules_match:
                device_info['modules'] = [m.strip() for m in modules_match.group(1).split(',')]
            
            # Extract capabilities
            capabilities = []
            cap_matches = re.finditer(r'^\s*Capabilities: \[(.+?)\](.+)$', section, re.MULTILINE)
            for match in cap_matches:
                capabilities.append({
                    'id': match.group(1),
                    'description': match.group(2).strip()
                })
            
            if capabilities:
                device_info['capabilities'] = capabilities
            
            devices.append(device_info)
        
        return devices
    
    def _extract_pci_addresses(self, lspci_output: str) -> List[str]:
        """Extract PCI addresses from lspci output."""
        addresses = []
        
        for line in lspci_output.strip().split('\n'):
            if line.strip():
                address_match = re.match(r'^([\da-f]{2}:[\da-f]{2}\.[\da-f}])', line)
                if address_match:
                    addresses.append(address_match.group(1))
        
        return addresses
    
    def _get_device_driver(self, pci_address: str) -> Optional[str]:
        """Get driver for a specific PCI device."""
        # Check if driver information is available in sysfs
        driver_path = f'/sys/bus/pci/devices/{pci_address}/driver'
        if self.system.file_exists(driver_path):
            # Get the driver name (last part of the symlink)
            driver_link = self.system.run_command(['readlink', '-f', driver_path])
            if driver_link.success:
                driver_parts = driver_link.stdout.strip().split('/')
                if driver_parts:
                    return driver_parts[-1]
        
        return None
    
    def _find_devices_without_drivers(self, lspci_k_output: str) -> List[Dict[str, str]]:
        """Find PCI devices without drivers."""
        no_driver_devices = []
        
        device_sections = re.split(r'\n(?=[\da-f]{2}:[\da-f]{2}\.[\da-f] )', lspci_k_output)
        for section in device_sections:
            if not section.strip():
                continue
            
            # Extract address and description
            address_match = re.match(r'^([\da-f]{2}:[\da-f]{2}\.[\da-f}) (.+):', section)
            if not address_match:
                continue
            
            address = address_match.group(1)
            description = address_match.group(2)
            
            # Check if driver is mentioned
            if 'Kernel driver in use:' not in section:
                no_driver_devices.append({
                    'address': address,
                    'description': description
                })
        
        return no_driver_devices
    
    def _check_known_compatibility_issues(self, lspci_k_output: str) -> List[Dict[str, str]]:
        """Check for known compatibility issues with PCI devices."""
        issues = []
        
        # This would typically contain a database of known issues
        # For now, we'll just check for a few common problematic devices/drivers
        
        # Example: Check for Nvidia Optimus systems (dual GPU)
        if 'NVIDIA' in lspci_k_output and 'Intel' in lspci_k_output and 'VGA' in lspci_k_output:
            # Count how many VGA devices we have
            vga_count = len(re.findall(r'VGA compatible controller', lspci_k_output))
            if vga_count > 1:
                issues.append({
                    'type': 'optimus_system',
                    'description': 'Multiple GPUs detected (possibly Optimus)',
                    'recommendation': 'Consider installing nvidia-prime or bumblebee for GPU switching'
                })
        
        # Example: Check for problematic wireless cards
        if 'Broadcom' in lspci_k_output and 'Network controller' in lspci_k_output:
            if 'wl' not in lspci_k_output and 'b43' not in lspci_k_output:
                issues.append({
                    'type': 'broadcom_wireless',
                    'description': 'Broadcom wireless card without proper driver',
                    'recommendation': 'Install broadcom-wl or b43 driver'
                })
        
        return issues
    
    def _load_pci_ids(self) -> None:
        """Load PCI vendor and device IDs from system database."""
        # Try to load from /usr/share/hwdata/pci.ids or /usr/share/misc/pci.ids
        pci_ids_paths = ['/usr/share/hwdata/pci.ids', '/usr/share/misc/pci.ids']
        pci_ids_content = None
        
        for path in pci_ids_paths:
            content = self.system.read_file(path)
            if content:
                pci_ids_content = content
                break
        
        if not pci_ids_content:
            return
        
        current_vendor = None
        
        for line in pci_ids_content.split('\n'):
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Vendor line
            if not line.startswith('\t'):
                vendor_match = re.match(r'^([0-9a-f]{4})\s+(.+)$', line)
                if vendor_match:
                    vendor_id = vendor_match.group(1)
                    vendor_name = vendor_match.group(2)
                    self.vendor_db[vendor_id] = vendor_name
                    current_vendor = vendor_id
                    self.device_db[vendor_id] = {}
            
            # Device line
            elif line.startswith('\t') and not line.startswith('\t\t') and current_vendor:
                device_match = re.match(r'^\t([0-9a-f]{4})\s+(.+)$', line)
                if device_match:
                    device_id = device_match.group(1)
                    device_name = device_match.group(2)
                    self.device_db[current_vendor][device_id] = device_name