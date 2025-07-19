#!/usr/bin/env python3
"""Enhanced USB Device Analysis Module.

This module provides detailed USB device information gathering including vendor
information, driver details, and hierarchy analysis.

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
from typing import Any, Dict, List, Optional, Tuple

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class USBAnalyzer:
    """Enhanced USB device analyzer with detailed vendor information."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize USB analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # USB vendor and product ID database
        self.vendor_db = {}
        self.product_db = {}
        self._load_usb_ids()
    
    def get_usb_devices(self) -> Dict[str, Any]:
        """Get comprehensive USB device information.
        
        Returns:
            Dictionary containing detailed USB device information
        """
        info: Dict[str, Any] = {}
        
        # Get basic USB device info
        info.update(self._get_basic_usb_info())
        
        # Get USB device hierarchy
        info.update(self._get_usb_hierarchy())
        
        # Get driver information
        info.update(self._get_driver_info())
        
        # Get compatibility analysis
        info.update(self._analyze_compatibility())
        
        return info
    
    def _get_basic_usb_info(self) -> Dict[str, Any]:
        """Get basic USB device information using lsusb."""
        info: Dict[str, Any] = {}
        
        # Get USB device information using lsusb
        lsusb_result = self.system.run_command(['lsusb'])
        if lsusb_result.success:
            info['lsusb'] = lsusb_result.stdout
            info['devices'] = self._parse_lsusb_output(lsusb_result.stdout)
        else:
            info['lsusb_error'] = lsusb_result.error or 'Failed to run lsusb'
        
        return info
    
    def _get_usb_hierarchy(self) -> Dict[str, Any]:
        """Get USB device hierarchy."""
        info: Dict[str, Any] = {}
        
        # Get USB device tree using lsusb -t
        lsusb_tree_result = self.system.run_command(['lsusb', '-t'])
        if lsusb_tree_result.success:
            info['usb_tree'] = lsusb_tree_result.stdout
            info['hierarchy'] = self._parse_usb_tree(lsusb_tree_result.stdout)
        else:
            info['usb_tree_error'] = lsusb_tree_result.error or 'Failed to run lsusb -t'
        
        return info
    
    def _get_driver_info(self) -> Dict[str, Any]:
        """Get USB device driver information."""
        info: Dict[str, Any] = {}
        driver_info = []
        
        # Get detailed USB device information
        for device in self._get_usb_devices_from_sys():
            driver = self._get_device_driver(device['syspath'])
            if driver:
                device['driver'] = driver
                driver_info.append(device)
        
        if driver_info:
            info['driver_info'] = driver_info
        
        return info
    
    def _analyze_compatibility(self) -> Dict[str, Any]:
        """Analyze USB device compatibility."""
        info: Dict[str, Any] = {}
        compatibility_issues = []
        
        # Get kernel version
        kernel_version_result = self.system.run_command(['uname', '-r'])
        if kernel_version_result.success:
            kernel_version = kernel_version_result.stdout.strip()
            info['kernel_version'] = kernel_version
        
        # Get list of USB devices with their drivers
        devices = self._get_usb_devices_from_sys()
        
        # Check for devices without drivers
        for device in devices:
            if not self._get_device_driver(device['syspath']):
                compatibility_issues.append({
                    'type': 'missing_driver',
                    'device': f"{device.get('vendor_id', 'unknown')}:{device.get('product_id', 'unknown')} {device.get('product', 'Unknown Device')}",
                    'recommendation': 'Install appropriate driver for this device'
                })
        
        # Check for devices with known compatibility issues
        compatibility_issues.extend(self._check_known_compatibility_issues(devices))
        
        if compatibility_issues:
            info['compatibility_issues'] = compatibility_issues
        
        return info
    
    def _parse_lsusb_output(self, lsusb_output: str) -> List[Dict[str, Any]]:
        """Parse lsusb output."""
        devices = []
        
        for line in lsusb_output.strip().split('\n'):
            if line.strip():
                # Parse the standard lsusb output format
                # Example: Bus 001 Device 002: ID 8087:0024 Intel Corp. Integrated Rate Matching Hub
                match = re.match(r'Bus (\d+) Device (\d+): ID ([0-9a-f]{4}):([0-9a-f]{4}) (.+)?', line)
                if match:
                    bus = match.group(1)
                    device = match.group(2)
                    vendor_id = match.group(3)
                    product_id = match.group(4)
                    description = match.group(5) if match.group(5) else 'Unknown Device'
                    
                    device_info = {
                        'bus': bus,
                        'device': device,
                        'vendor_id': vendor_id,
                        'product_id': product_id,
                        'description': description
                    }
                    
                    # Add vendor and product names from database
                    if vendor_id in self.vendor_db:
                        device_info['vendor'] = self.vendor_db[vendor_id]
                    
                    if vendor_id in self.product_db and product_id in self.product_db[vendor_id]:
                        device_info['product'] = self.product_db[vendor_id][product_id]
                    
                    devices.append(device_info)
        
        return devices
    
    def _parse_usb_tree(self, usb_tree_output: str) -> List[Dict[str, Any]]:
        """Parse lsusb -t output to get USB device hierarchy."""
        tree = []
        current_path = []
        
        for line in usb_tree_output.strip().split('\n'):
            if not line.strip():
                continue
            
            # Calculate the depth based on leading spaces
            depth = (len(line) - len(line.lstrip())) // 4
            
            # Adjust the current path based on depth
            if depth < len(current_path):
                current_path = current_path[:depth]
            
            # Parse the line
            match = re.search(r'Port (\d+): Dev (\d+), If (\d+), Class=([^,]+), Driver=([^,]+),', line)
            if match:
                port = match.group(1)
                dev = match.group(2)
                interface = match.group(3)
                device_class = match.group(4)
                driver = match.group(5)
                
                device_info = {
                    'port': port,
                    'device': dev,
                    'interface': interface,
                    'class': device_class,
                    'driver': driver,
                    'depth': depth,
                    'children': []
                }
                
                # Add to the tree
                if depth == 0:
                    tree.append(device_info)
                    current_path = [device_info]
                else:
                    parent = current_path[-1]
                    parent['children'].append(device_info)
                    current_path.append(device_info)
        
        return tree
    
    def _get_usb_devices_from_sys(self) -> List[Dict[str, Any]]:
        """Get USB devices from /sys/bus/usb/devices."""
        devices = []
        
        # List USB devices in sysfs
        ls_result = self.system.run_command(['ls', '/sys/bus/usb/devices/'])
        if not ls_result.success:
            return devices
        
        for device_name in ls_result.stdout.strip().split():
            # Skip interfaces, we only want devices
            if ':' in device_name:
                continue
            
            device_path = f'/sys/bus/usb/devices/{device_name}'
            device_info = self._get_device_info_from_sys(device_path)
            if device_info:
                devices.append(device_info)
        
        return devices
    
    def _get_device_info_from_sys(self, device_path: str) -> Optional[Dict[str, Any]]:
        """Get device information from sysfs."""
        device_info = {'syspath': device_path}
        
        # Get vendor ID
        vendor_id = self.system.read_file(f'{device_path}/idVendor')
        if vendor_id:
            device_info['vendor_id'] = vendor_id
            if vendor_id in self.vendor_db:
                device_info['vendor'] = self.vendor_db[vendor_id]
        
        # Get product ID
        product_id = self.system.read_file(f'{device_path}/idProduct')
        if product_id:
            device_info['product_id'] = product_id
            if vendor_id and vendor_id in self.product_db and product_id in self.product_db[vendor_id]:
                device_info['product'] = self.product_db[vendor_id][product_id]
        
        # Get manufacturer
        manufacturer = self.system.read_file(f'{device_path}/manufacturer')
        if manufacturer:
            device_info['manufacturer'] = manufacturer
        
        # Get product name
        product = self.system.read_file(f'{device_path}/product')
        if product:
            device_info['product_name'] = product
        
        # Get serial number
        serial = self.system.read_file(f'{device_path}/serial')
        if serial:
            device_info['serial'] = serial
        
        # Get speed
        speed = self.system.read_file(f'{device_path}/speed')
        if speed:
            device_info['speed'] = f'{speed} Mbps'
        
        # Get version
        version = self.system.read_file(f'{device_path}/version')
        if version:
            device_info['version'] = version
        
        # Get device class
        bDeviceClass = self.system.read_file(f'{device_path}/bDeviceClass')
        if bDeviceClass:
            device_info['device_class'] = bDeviceClass
        
        return device_info if device_info else None
    
    def _get_device_driver(self, device_path: str) -> Optional[str]:
        """Get driver for a specific USB device."""
        # Check if driver information is available in sysfs
        driver_path = f'{device_path}/driver'
        if self.system.file_exists(driver_path):
            # Get the driver name (last part of the symlink)
            driver_link = self.system.run_command(['readlink', '-f', driver_path])
            if driver_link.success:
                driver_parts = driver_link.stdout.strip().split('/')
                if driver_parts:
                    return driver_parts[-1]
        
        return None
    
    def _check_known_compatibility_issues(self, devices: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Check for known compatibility issues with USB devices."""
        issues = []
        
        # This would typically contain a database of known issues
        # For now, we'll just check for a few common problematic devices
        
        for device in devices:
            vendor_id = device.get('vendor_id')
            product_id = device.get('product_id')
            
            if not vendor_id or not product_id:
                continue
            
            # Example: Check for problematic Realtek WiFi adapters
            if vendor_id == '0bda':  # Realtek
                if product_id in ['8172', '8192', '8723', '8821']:
                    issues.append({
                        'type': 'realtek_wifi',
                        'device': f"{vendor_id}:{product_id} {device.get('product', 'Realtek WiFi Adapter')}",
                        'recommendation': 'May need firmware installation or driver update'
                    })
            
            # Example: Check for problematic Broadcom Bluetooth adapters
            if vendor_id == '0a5c':  # Broadcom
                issues.append({
                    'type': 'broadcom_bluetooth',
                    'device': f"{vendor_id}:{product_id} {device.get('product', 'Broadcom Bluetooth Adapter')}",
                    'recommendation': 'May need firmware installation from linux-firmware package'
                })
        
        return issues
    
    def _load_usb_ids(self) -> None:
        """Load USB vendor and product IDs from system database."""
        # Try to load from /usr/share/hwdata/usb.ids or /usr/share/misc/usb.ids
        usb_ids_paths = ['/usr/share/hwdata/usb.ids', '/usr/share/misc/usb.ids']
        usb_ids_content = None
        
        for path in usb_ids_paths:
            content = self.system.read_file(path)
            if content:
                usb_ids_content = content
                break
        
        if not usb_ids_content:
            return
        
        current_vendor = None
        
        for line in usb_ids_content.split('\n'):
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
                    self.product_db[vendor_id] = {}
            
            # Product line
            elif line.startswith('\t') and not line.startswith('\t\t') and current_vendor:
                product_match = re.match(r'^\t([0-9a-f]{4})\s+(.+)$', line)
                if product_match:
                    product_id = product_match.group(1)
                    product_name = product_match.group(2)
                    self.product_db[current_vendor][product_id] = product_name