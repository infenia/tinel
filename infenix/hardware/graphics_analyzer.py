#!/usr/bin/env python3
"""Enhanced Graphics Hardware Analysis Module.

This module provides detailed graphics hardware information gathering including
GPU detection, driver information, and performance metrics.

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


class GraphicsAnalyzer:
    """Enhanced graphics analyzer with detailed GPU detection."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize graphics analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
    
    def get_graphics_info(self) -> Dict[str, Any]:
        """Get comprehensive graphics hardware information.
        
        Returns:
            Dictionary containing detailed graphics hardware information
        """
        info: Dict[str, Any] = {}
        
        # Get basic graphics hardware info
        info.update(self._get_basic_graphics_info())
        
        # Get detailed GPU information
        info.update(self._get_detailed_gpu_info())
        
        # Get driver information
        info.update(self._get_driver_info())
        
        # Get display information
        info.update(self._get_display_info())
        
        # Get performance metrics
        info.update(self._get_performance_metrics())
        
        return info
    
    def _get_basic_graphics_info(self) -> Dict[str, Any]:
        """Get basic graphics hardware information using lspci."""
        info: Dict[str, Any] = {}
        
        # Get graphics hardware information using lspci
        lspci_result = self.system.run_command(['lspci', '-nn', '-v', '-d', '::0300'])
        if lspci_result.success:
            info['lspci_vga'] = lspci_result.stdout
            info['gpus'] = self._parse_lspci_vga_output(lspci_result.stdout)
        else:
            info['lspci_vga_error'] = lspci_result.error or 'Failed to run lspci for VGA devices'
        
        # Get 3D controller information (e.g., NVIDIA Optimus)
        lspci_3d_result = self.system.run_command(['lspci', '-nn', '-v', '-d', '::0302'])
        if lspci_3d_result.success and lspci_3d_result.stdout.strip():
            info['lspci_3d'] = lspci_3d_result.stdout
            info['3d_controllers'] = self._parse_lspci_vga_output(lspci_3d_result.stdout)
            
            # Merge with GPUs list
            if '3d_controllers' in info and 'gpus' in info:
                info['gpus'].extend(info['3d_controllers'])
        
        return info
    
    def _get_detailed_gpu_info(self) -> Dict[str, Any]:
        """Get detailed GPU information."""
        info: Dict[str, Any] = {}
        
        # Check for NVIDIA GPUs
        nvidia_gpus = self._get_nvidia_gpu_info()
        if nvidia_gpus:
            info['nvidia_gpus'] = nvidia_gpus
        
        # Check for AMD GPUs
        amd_gpus = self._get_amd_gpu_info()
        if amd_gpus:
            info['amd_gpus'] = amd_gpus
        
        # Check for Intel GPUs
        intel_gpus = self._get_intel_gpu_info()
        if intel_gpus:
            info['intel_gpus'] = intel_gpus
        
        return info
    
    def _get_driver_info(self) -> Dict[str, Any]:
        """Get graphics driver information."""
        info: Dict[str, Any] = {}
        
        # Get loaded graphics drivers
        lsmod_result = self.system.run_command(['lsmod'])
        if lsmod_result.success:
            # Look for common graphics drivers
            graphics_drivers = []
            
            # NVIDIA drivers
            if re.search(r'nvidia\s+', lsmod_result.stdout):
                nvidia_driver = self._get_nvidia_driver_info()
                if nvidia_driver:
                    graphics_drivers.append(nvidia_driver)
            
            # AMD drivers
            if re.search(r'amdgpu\s+', lsmod_result.stdout):
                amd_driver = self._get_amd_driver_info()
                if amd_driver:
                    graphics_drivers.append(amd_driver)
            
            # Intel drivers
            if re.search(r'i915\s+', lsmod_result.stdout):
                intel_driver = self._get_intel_driver_info()
                if intel_driver:
                    graphics_drivers.append(intel_driver)
            
            # Nouveau driver (open-source NVIDIA)
            if re.search(r'nouveau\s+', lsmod_result.stdout):
                nouveau_driver = self._get_nouveau_driver_info()
                if nouveau_driver:
                    graphics_drivers.append(nouveau_driver)
            
            if graphics_drivers:
                info['graphics_drivers'] = graphics_drivers
        
        return info
    
    def _get_display_info(self) -> Dict[str, Any]:
        """Get display information."""
        info: Dict[str, Any] = {}
        
        # Get X11 display information using xrandr
        xrandr_result = self.system.run_command(['xrandr', '--verbose'])
        if xrandr_result.success:
            info['xrandr'] = xrandr_result.stdout
            info['displays'] = self._parse_xrandr_output(xrandr_result.stdout)
        
        # Get Wayland display information
        if self._is_wayland_session():
            wayland_info = self._get_wayland_display_info()
            if wayland_info:
                info['wayland'] = wayland_info
        
        return info
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get graphics performance metrics."""
        info: Dict[str, Any] = {}
        
        # Get NVIDIA performance metrics
        if self._has_nvidia_gpu():
            nvidia_metrics = self._get_nvidia_performance_metrics()
            if nvidia_metrics:
                info['nvidia_metrics'] = nvidia_metrics
        
        # Get AMD performance metrics
        if self._has_amd_gpu():
            amd_metrics = self._get_amd_performance_metrics()
            if amd_metrics:
                info['amd_metrics'] = amd_metrics
        
        # Get Intel performance metrics
        if self._has_intel_gpu():
            intel_metrics = self._get_intel_performance_metrics()
            if intel_metrics:
                info['intel_metrics'] = intel_metrics
        
        return info
    
    def _parse_lspci_vga_output(self, lspci_output: str) -> List[Dict[str, Any]]:
        """Parse lspci output for VGA devices."""
        gpus = []
        current_gpu = None
        
        for line in lspci_output.strip().split('\n'):
            # New GPU
            if not line.startswith('\t'):
                if current_gpu:
                    gpus.append(current_gpu)
                
                # Extract GPU information
                match = re.match(r'^([0-9a-f:.]+) (.+) \[([0-9a-f]+):([0-9a-f]+)\]', line)
                if match:
                    address = match.group(1)
                    description = match.group(2)
                    vendor_id = match.group(3)
                    device_id = match.group(4)
                    
                    current_gpu = {
                        'address': address,
                        'description': description,
                        'vendor_id': vendor_id,
                        'device_id': device_id
                    }
                    
                    # Determine vendor
                    if 'NVIDIA' in description:
                        current_gpu['vendor'] = 'NVIDIA'
                    elif 'AMD' in description or 'ATI' in description:
                        current_gpu['vendor'] = 'AMD'
                    elif 'Intel' in description:
                        current_gpu['vendor'] = 'Intel'
                    else:
                        current_gpu['vendor'] = 'Unknown'
            
            # Additional GPU information
            elif current_gpu:
                # Extract subsystem
                subsystem_match = re.search(r'Subsystem: (.+) \[([0-9a-f]+):([0-9a-f]+)\]', line)
                if subsystem_match:
                    current_gpu['subsystem'] = subsystem_match.group(1)
                    current_gpu['subsystem_vendor_id'] = subsystem_match.group(2)
                    current_gpu['subsystem_device_id'] = subsystem_match.group(3)
                
                # Extract kernel driver
                driver_match = re.search(r'Kernel driver in use: (.+)', line)
                if driver_match:
                    current_gpu['driver'] = driver_match.group(1)
                
                # Extract kernel modules
                modules_match = re.search(r'Kernel modules: (.+)', line)
                if modules_match:
                    current_gpu['modules'] = [m.strip() for m in modules_match.group(1).split(',')]
                
                # Extract memory
                memory_match = re.search(r'Memory at ([0-9a-f]+) \((\w+), (\w+)-bit, (\w+)\)', line)
                if memory_match:
                    if 'memory_regions' not in current_gpu:
                        current_gpu['memory_regions'] = []
                    
                    current_gpu['memory_regions'].append({
                        'address': memory_match.group(1),
                        'type': memory_match.group(2),
                        'width': memory_match.group(3),
                        'mode': memory_match.group(4)
                    })
        
        # Add the last GPU
        if current_gpu:
            gpus.append(current_gpu)
        
        return gpus
    
    def _get_nvidia_gpu_info(self) -> List[Dict[str, Any]]:
        """Get detailed NVIDIA GPU information."""
        gpus = []
        
        # Check if nvidia-smi is available
        nvidia_smi_result = self.system.run_command(['nvidia-smi', '-q'])
        if not nvidia_smi_result.success:
            return gpus
        
        # Parse nvidia-smi output
        current_gpu = None
        
        for line in nvidia_smi_result.stdout.strip().split('\n'):
            line = line.strip()
            
            # New GPU
            if line.startswith('GPU ') and ':' in line:
                if current_gpu:
                    gpus.append(current_gpu)
                
                current_gpu = {'vendor': 'NVIDIA'}
            
            # GPU information
            elif current_gpu and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                if key == 'product_name':
                    current_gpu['model'] = value
                elif key == 'gpu_uuid':
                    current_gpu['uuid'] = value
                elif key == 'pci_bus_id':
                    current_gpu['pci_bus_id'] = value
                elif key == 'gpu_serial':
                    current_gpu['serial'] = value
                elif key == 'vbios_version':
                    current_gpu['vbios_version'] = value
                elif key == 'driver_version':
                    current_gpu['driver_version'] = value
                elif key == 'memory_total':
                    current_gpu['memory_total'] = value
                elif key == 'memory_used':
                    current_gpu['memory_used'] = value
                elif key == 'memory_free':
                    current_gpu['memory_free'] = value
                elif key == 'gpu_current_temp':
                    current_gpu['temperature'] = value
                elif key == 'gpu_utilization':
                    current_gpu['utilization'] = value
        
        # Add the last GPU
        if current_gpu:
            gpus.append(current_gpu)
        
        return gpus
    
    def _get_amd_gpu_info(self) -> List[Dict[str, Any]]:
        """Get detailed AMD GPU information."""
        gpus = []
        
        # Check for AMD GPUs in sysfs
        ls_result = self.system.run_command(['ls', '/sys/class/drm/'])
        if not ls_result.success:
            return gpus
        
        for device in ls_result.stdout.strip().split():
            # Only process card devices
            if not device.startswith('card'):
                continue
            
            # Check if it's an AMD GPU
            device_path = f'/sys/class/drm/{device}'
            vendor_file = f'{device_path}/device/vendor'
            
            vendor = self.system.read_file(vendor_file)
            if vendor and vendor.strip() == '0x1002':  # AMD vendor ID
                gpu_info = {'vendor': 'AMD'}
                
                # Get device ID
                device_id = self.system.read_file(f'{device_path}/device/device')
                if device_id:
                    gpu_info['device_id'] = device_id.strip()
                
                # Get model name
                model = self.system.read_file(f'{device_path}/device/uevent')
                if model:
                    model_match = re.search(r'DRIVER=(\w+)', model)
                    if model_match:
                        gpu_info['driver'] = model_match.group(1)
                
                # Get memory information
                vram_total = self.system.read_file(f'{device_path}/device/mem_info_vram_total')
                if vram_total:
                    gpu_info['memory_total'] = int(vram_total.strip()) // (1024 * 1024)  # Convert to MB
                
                # Get firmware version
                firmware = self.system.read_file(f'{device_path}/device/firmware_version')
                if firmware:
                    gpu_info['firmware_version'] = firmware.strip()
                
                gpus.append(gpu_info)
        
        return gpus
    
    def _get_intel_gpu_info(self) -> List[Dict[str, Any]]:
        """Get detailed Intel GPU information."""
        gpus = []
        
        # Check for Intel GPUs in sysfs
        ls_result = self.system.run_command(['ls', '/sys/class/drm/'])
        if not ls_result.success:
            return gpus
        
        for device in ls_result.stdout.strip().split():
            # Only process card devices
            if not device.startswith('card'):
                continue
            
            # Check if it's an Intel GPU
            device_path = f'/sys/class/drm/{device}'
            vendor_file = f'{device_path}/device/vendor'
            
            vendor = self.system.read_file(vendor_file)
            if vendor and vendor.strip() == '0x8086':  # Intel vendor ID
                gpu_info = {'vendor': 'Intel'}
                
                # Get device ID
                device_id = self.system.read_file(f'{device_path}/device/device')
                if device_id:
                    gpu_info['device_id'] = device_id.strip()
                
                # Get model name
                model = self.system.read_file(f'{device_path}/device/uevent')
                if model:
                    model_match = re.search(r'DRIVER=(\w+)', model)
                    if model_match:
                        gpu_info['driver'] = model_match.group(1)
                
                # Get firmware version (GuC/HuC firmware for Intel)
                guc_version = self.system.read_file(f'{device_path}/gt/uc/guc_firmware_version')
                if guc_version:
                    gpu_info['guc_firmware_version'] = guc_version.strip()
                
                huc_version = self.system.read_file(f'{device_path}/gt/uc/huc_firmware_version')
                if huc_version:
                    gpu_info['huc_firmware_version'] = huc_version.strip()
                
                gpus.append(gpu_info)
        
        return gpus
    
    def _get_nvidia_driver_info(self) -> Dict[str, Any]:
        """Get NVIDIA driver information."""
        driver_info = {'name': 'nvidia'}
        
        # Get NVIDIA driver version
        nvidia_smi_result = self.system.run_command(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'])
        if nvidia_smi_result.success:
            driver_info['version'] = nvidia_smi_result.stdout.strip()
        
        # Get CUDA version
        nvidia_smi_cuda_result = self.system.run_command(['nvidia-smi', '--query-gpu=cuda_version', '--format=csv,noheader'])
        if nvidia_smi_cuda_result.success:
            driver_info['cuda_version'] = nvidia_smi_cuda_result.stdout.strip()
        
        # Get module information
        modinfo_result = self.system.run_command(['modinfo', 'nvidia'])
        if modinfo_result.success:
            # Extract author
            author_match = re.search(r'author:\s*(.+)', modinfo_result.stdout)
            if author_match:
                driver_info['author'] = author_match.group(1).strip()
            
            # Extract description
            description_match = re.search(r'description:\s*(.+)', modinfo_result.stdout)
            if description_match:
                driver_info['description'] = description_match.group(1).strip()
            
            # Extract license
            license_match = re.search(r'license:\s*(.+)', modinfo_result.stdout)
            if license_match:
                driver_info['license'] = license_match.group(1).strip()
        
        return driver_info
    
    def _get_amd_driver_info(self) -> Dict[str, Any]:
        """Get AMD driver information."""
        driver_info = {'name': 'amdgpu'}
        
        # Get module information
        modinfo_result = self.system.run_command(['modinfo', 'amdgpu'])
        if modinfo_result.success:
            # Extract version
            version_match = re.search(r'version:\s*(.+)', modinfo_result.stdout)
            if version_match:
                driver_info['version'] = version_match.group(1).strip()
            
            # Extract author
            author_match = re.search(r'author:\s*(.+)', modinfo_result.stdout)
            if author_match:
                driver_info['author'] = author_match.group(1).strip()
            
            # Extract description
            description_match = re.search(r'description:\s*(.+)', modinfo_result.stdout)
            if description_match:
                driver_info['description'] = description_match.group(1).strip()
            
            # Extract license
            license_match = re.search(r'license:\s*(.+)', modinfo_result.stdout)
            if license_match:
                driver_info['license'] = license_match.group(1).strip()
            
            # Extract firmware
            firmware_matches = re.finditer(r'firmware:\s*(.+)', modinfo_result.stdout)
            firmware_files = []
            for match in firmware_matches:
                firmware_files.append(match.group(1).strip())
            
            if firmware_files:
                driver_info['firmware_files'] = firmware_files
        
        return driver_info
    
    def _get_intel_driver_info(self) -> Dict[str, Any]:
        """Get Intel driver information."""
        driver_info = {'name': 'i915'}
        
        # Get module information
        modinfo_result = self.system.run_command(['modinfo', 'i915'])
        if modinfo_result.success:
            # Extract version
            version_match = re.search(r'version:\s*(.+)', modinfo_result.stdout)
            if version_match:
                driver_info['version'] = version_match.group(1).strip()
            
            # Extract author
            author_match = re.search(r'author:\s*(.+)', modinfo_result.stdout)
            if author_match:
                driver_info['author'] = author_match.group(1).strip()
            
            # Extract description
            description_match = re.search(r'description:\s*(.+)', modinfo_result.stdout)
            if description_match:
                driver_info['description'] = description_match.group(1).strip()
            
            # Extract license
            license_match = re.search(r'license:\s*(.+)', modinfo_result.stdout)
            if license_match:
                driver_info['license'] = license_match.group(1).strip()
            
            # Extract firmware
            firmware_matches = re.finditer(r'firmware:\s*(.+)', modinfo_result.stdout)
            firmware_files = []
            for match in firmware_matches:
                firmware_files.append(match.group(1).strip())
            
            if firmware_files:
                driver_info['firmware_files'] = firmware_files
        
        return driver_info
    
    def _get_nouveau_driver_info(self) -> Dict[str, Any]:
        """Get Nouveau driver information."""
        driver_info = {'name': 'nouveau'}
        
        # Get module information
        modinfo_result = self.system.run_command(['modinfo', 'nouveau'])
        if modinfo_result.success:
            # Extract version
            version_match = re.search(r'version:\s*(.+)', modinfo_result.stdout)
            if version_match:
                driver_info['version'] = version_match.group(1).strip()
            
            # Extract author
            author_match = re.search(r'author:\s*(.+)', modinfo_result.stdout)
            if author_match:
                driver_info['author'] = author_match.group(1).strip()
            
            # Extract description
            description_match = re.search(r'description:\s*(.+)', modinfo_result.stdout)
            if description_match:
                driver_info['description'] = description_match.group(1).strip()
            
            # Extract license
            license_match = re.search(r'license:\s*(.+)', modinfo_result.stdout)
            if license_match:
                driver_info['license'] = license_match.group(1).strip()
        
        return driver_info
    
    def _parse_xrandr_output(self, xrandr_output: str) -> List[Dict[str, Any]]:
        """Parse xrandr output."""
        displays = []
        current_display = None
        
        for line in xrandr_output.strip().split('\n'):
            # New display
            if not line.startswith(' '):
                if current_display:
                    displays.append(current_display)
                
                # Extract display name and status
                match = re.match(r'^(\S+) (connected|disconnected) (.+)?', line)
                if match:
                    display_name = match.group(1)
                    status = match.group(2)
                    
                    current_display = {
                        'name': display_name,
                        'status': status
                    }
                    
                    # Extract primary flag
                    if 'primary' in line:
                        current_display['primary'] = True
                    
                    # Extract resolution and position
                    res_match = re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)
                    if res_match:
                        current_display['width'] = int(res_match.group(1))
                        current_display['height'] = int(res_match.group(2))
                        current_display['x'] = int(res_match.group(3))
                        current_display['y'] = int(res_match.group(4))
            
            # Additional display information
            elif current_display:
                # Extract EDID
                if line.strip().startswith('EDID:'):
                    edid_lines = []
                    i = xrandr_output.strip().split('\n').index(line) + 1
                    while i < len(xrandr_output.strip().split('\n')) and xrandr_output.strip().split('\n')[i].startswith('\t\t'):
                        edid_lines.append(xrandr_output.strip().split('\n')[i].strip())
                        i += 1
                    
                    if edid_lines:
                        current_display['edid'] = ''.join(edid_lines)
                
                # Extract properties
                prop_match = re.search(r'(\S+):\s*(.+)', line)
                if prop_match:
                    prop_name = prop_match.group(1)
                    prop_value = prop_match.group(2)
                    
                    if 'properties' not in current_display:
                        current_display['properties'] = {}
                    
                    current_display['properties'][prop_name] = prop_value
        
        # Add the last display
        if current_display:
            displays.append(current_display)
        
        return displays
    
    def _is_wayland_session(self) -> bool:
        """Check if the current session is Wayland."""
        # Check XDG_SESSION_TYPE environment variable
        session_type = self.system.run_command(['echo', '$XDG_SESSION_TYPE'])
        if session_type.success and 'wayland' in session_type.stdout.lower():
            return True
        
        # Check if Wayland display server is running
        ps_result = self.system.run_command(['ps', 'aux'])
        if ps_result.success and ('wayland' in ps_result.stdout.lower() or 'weston' in ps_result.stdout.lower()):
            return True
        
        return False
    
    def _get_wayland_display_info(self) -> Dict[str, Any]:
        """Get Wayland display information."""
        info = {}
        
        # Check for weston-info command
        weston_info_result = self.system.run_command(['weston-info'])
        if weston_info_result.success:
            info['weston_info'] = weston_info_result.stdout
        
        return info
    
    def _has_nvidia_gpu(self) -> bool:
        """Check if the system has an NVIDIA GPU."""
        lspci_result = self.system.run_command(['lspci'])
        return lspci_result.success and 'NVIDIA' in lspci_result.stdout
    
    def _has_amd_gpu(self) -> bool:
        """Check if the system has an AMD GPU."""
        lspci_result = self.system.run_command(['lspci'])
        return lspci_result.success and ('AMD' in lspci_result.stdout or 'ATI' in lspci_result.stdout)
    
    def _has_intel_gpu(self) -> bool:
        """Check if the system has an Intel GPU."""
        lspci_result = self.system.run_command(['lspci'])
        return lspci_result.success and 'Intel Corporation' in lspci_result.stdout and ('VGA' in lspci_result.stdout or '3D controller' in lspci_result.stdout)
    
    def _get_nvidia_performance_metrics(self) -> Dict[str, Any]:
        """Get NVIDIA GPU performance metrics."""
        metrics = {}
        
        # Get GPU utilization
        nvidia_smi_result = self.system.run_command([
            'nvidia-smi', 
            '--query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw,clocks.current.graphics,clocks.current.memory', 
            '--format=csv,noheader'
        ])
        
        if nvidia_smi_result.success:
            values = nvidia_smi_result.stdout.strip().split(',')
            if len(values) >= 6:
                metrics['gpu_utilization'] = values[0].strip()
                metrics['memory_utilization'] = values[1].strip()
                metrics['temperature'] = values[2].strip()
                metrics['power_draw'] = values[3].strip()
                metrics['graphics_clock'] = values[4].strip()
                metrics['memory_clock'] = values[5].strip()
        
        return metrics
    
    def _get_amd_performance_metrics(self) -> Dict[str, Any]:
        """Get AMD GPU performance metrics."""
        metrics = {}
        
        # Check for AMD GPUs in sysfs
        ls_result = self.system.run_command(['ls', '/sys/class/drm/'])
        if not ls_result.success:
            return metrics
        
        for device in ls_result.stdout.strip().split():
            # Only process card devices
            if not device.startswith('card'):
                continue
            
            # Check if it's an AMD GPU
            device_path = f'/sys/class/drm/{device}'
            vendor_file = f'{device_path}/device/vendor'
            
            vendor = self.system.read_file(vendor_file)
            if vendor and vendor.strip() == '0x1002':  # AMD vendor ID
                # Get GPU temperature
                temp = self.system.read_file(f'{device_path}/device/hwmon/hwmon*/temp1_input')
                if temp:
                    metrics['temperature'] = int(temp.strip()) / 1000  # Convert from millidegrees to degrees
                
                # Get GPU utilization
                gpu_busy = self.system.read_file(f'{device_path}/device/gpu_busy_percent')
                if gpu_busy:
                    metrics['gpu_utilization'] = f"{gpu_busy.strip()}%"
                
                # Get memory utilization
                mem_busy = self.system.read_file(f'{device_path}/device/mem_busy_percent')
                if mem_busy:
                    metrics['memory_utilization'] = f"{mem_busy.strip()}%"
                
                # Get power consumption
                power = self.system.read_file(f'{device_path}/device/hwmon/hwmon*/power1_average')
                if power:
                    metrics['power_draw'] = f"{int(power.strip()) / 1000000} W"  # Convert from microwatts to watts
                
                break  # Only get metrics for the first AMD GPU
        
        return metrics
    
    def _get_intel_performance_metrics(self) -> Dict[str, Any]:
        """Get Intel GPU performance metrics."""
        metrics = {}
        
        # Intel GPU metrics are limited in sysfs
        # Most require specialized tools or kernel modules
        
        # Check for Intel GPUs in sysfs
        ls_result = self.system.run_command(['ls', '/sys/class/drm/'])
        if not ls_result.success:
            return metrics
        
        for device in ls_result.stdout.strip().split():
            # Only process card devices
            if not device.startswith('card'):
                continue
            
            # Check if it's an Intel GPU
            device_path = f'/sys/class/drm/{device}'
            vendor_file = f'{device_path}/device/vendor'
            
            vendor = self.system.read_file(vendor_file)
            if vendor and vendor.strip() == '0x8086':  # Intel vendor ID
                # Get GPU frequency
                freq = self.system.read_file(f'{device_path}/gt_cur_freq_mhz')
                if freq:
                    metrics['current_frequency'] = f"{freq.strip()} MHz"
                
                # Get min/max frequency
                min_freq = self.system.read_file(f'{device_path}/gt_min_freq_mhz')
                if min_freq:
                    metrics['min_frequency'] = f"{min_freq.strip()} MHz"
                
                max_freq = self.system.read_file(f'{device_path}/gt_max_freq_mhz')
                if max_freq:
                    metrics['max_frequency'] = f"{max_freq.strip()} MHz"
                
                break  # Only get metrics for the first Intel GPU
        
        return metrics