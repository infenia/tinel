#!/usr/bin/env python3
"""Enhanced Memory Analysis Module.

This module provides detailed memory information gathering including timing
configuration detection, performance analysis, and optimization recommendations.

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
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class MemoryAnalyzer:
    """Enhanced memory analyzer with detailed configuration detection."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize memory analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get comprehensive memory information.
        
        Returns:
            Dictionary containing detailed memory information
        """
        info: Dict[str, Any] = {}
        
        # Get basic memory info
        info.update(self._get_basic_memory_info())
        
        # Get memory hardware details
        info.update(self._get_memory_hardware_info())
        
        # Get memory timing and configuration
        info.update(self._get_memory_timing_info())
        
        # Get memory performance metrics
        info.update(self._get_memory_performance_info())
        
        # Get memory optimization analysis
        info.update(self._analyze_memory_optimization())
        
        return info
    
    def _get_basic_memory_info(self) -> Dict[str, Any]:
        """Get basic memory information from /proc/meminfo."""
        info: Dict[str, Any] = {}
        
        # Get memory info from /proc/meminfo
        meminfo_content = self.system.read_file('/proc/meminfo')
        if meminfo_content:
            info['proc_meminfo'] = meminfo_content
            info.update(self._parse_meminfo(meminfo_content))
        else:
            info['proc_meminfo_error'] = 'Failed to read /proc/meminfo'
        
        # Get memory info using free command
        free_result = self.system.run_command(['free', '-h'])
        if free_result.success:
            info['free_output'] = free_result.stdout
            info.update(self._parse_free_output(free_result.stdout))
        else:
            info['free_error'] = free_result.error or 'Failed to run free command'
        
        return info
    
    def _get_memory_hardware_info(self) -> Dict[str, Any]:
        """Get detailed memory hardware information using dmidecode."""
        info: Dict[str, Any] = {}
        
        # Get memory hardware info using dmidecode
        dmidecode_result = self.system.run_command(['sudo', 'dmidecode', '-t', 'memory'])
        if dmidecode_result.success:
            info['dmidecode_memory'] = dmidecode_result.stdout
            info.update(self._parse_dmidecode_memory(dmidecode_result.stdout))
        else:
            info['dmidecode_memory_error'] = dmidecode_result.error or 'Failed to run dmidecode'
        
        # Get memory controller info
        dmidecode_mc_result = self.system.run_command(['sudo', 'dmidecode', '-t', '16'])
        if dmidecode_mc_result.success:
            info['memory_controller'] = dmidecode_mc_result.stdout
            info.update(self._parse_memory_controller(dmidecode_mc_result.stdout))
        
        return info
    
    def _get_memory_timing_info(self) -> Dict[str, Any]:
        """Get memory timing and configuration information."""
        info: Dict[str, Any] = {}
        
        # Try to get memory timing from various sources
        # Check for memory timing in /sys/devices/system/edac/
        edac_info = self._get_edac_info()
        if edac_info:
            info['edac_info'] = edac_info
        
        # Check for memory bandwidth information
        bandwidth_info = self._get_memory_bandwidth_info()
        if bandwidth_info:
            info['bandwidth_info'] = bandwidth_info
        
        return info
    
    def _get_memory_performance_info(self) -> Dict[str, Any]:
        """Get memory performance metrics."""
        info: Dict[str, Any] = {}
        
        # Get memory statistics from /proc/vmstat
        vmstat_content = self.system.read_file('/proc/vmstat')
        if vmstat_content:
            info['vmstat'] = vmstat_content
            info.update(self._parse_vmstat(vmstat_content))
        
        # Get memory pressure information
        pressure_info = self._get_memory_pressure_info()
        if pressure_info:
            info['memory_pressure'] = pressure_info
        
        # Get NUMA information
        numa_info = self._get_numa_info()
        if numa_info:
            info['numa_info'] = numa_info
        
        return info
    
    def _analyze_memory_optimization(self) -> Dict[str, Any]:
        """Analyze memory for optimization opportunities."""
        info: Dict[str, Any] = {}
        recommendations = []
        
        # Check swap usage
        meminfo_content = self.system.read_file('/proc/meminfo')
        if meminfo_content:
            swap_total = self._extract_meminfo_value(meminfo_content, 'SwapTotal')
            swap_free = self._extract_meminfo_value(meminfo_content, 'SwapFree')
            
            if swap_total and swap_free:
                swap_used = swap_total - swap_free
                swap_usage_percent = (swap_used / swap_total) * 100 if swap_total > 0 else 0
                
                if swap_usage_percent > 50:
                    recommendations.append({
                        'type': 'performance',
                        'issue': f'High swap usage: {swap_usage_percent:.1f}%',
                        'recommendation': 'Consider adding more RAM or optimizing memory usage',
                        'severity': 'high' if swap_usage_percent > 80 else 'medium'
                    })
        
        # Check for memory fragmentation
        buddyinfo_content = self.system.read_file('/proc/buddyinfo')
        if buddyinfo_content:
            fragmentation_analysis = self._analyze_memory_fragmentation(buddyinfo_content)
            if fragmentation_analysis['fragmented']:
                recommendations.append({
                    'type': 'performance',
                    'issue': 'Memory fragmentation detected',
                    'recommendation': 'Consider enabling memory compaction or restarting services',
                    'severity': 'medium'
                })
        
        # Check transparent huge pages
        thp_enabled = self.system.read_file('/sys/kernel/mm/transparent_hugepage/enabled')
        if thp_enabled and 'never' in thp_enabled:
            recommendations.append({
                'type': 'performance',
                'issue': 'Transparent Huge Pages disabled',
                'recommendation': 'Consider enabling THP for better memory performance',
                'command': 'echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled'
            })
        
        info['optimization_recommendations'] = recommendations
        return info
    
    def _parse_meminfo(self, meminfo_content: str) -> Dict[str, Any]:
        """Parse /proc/meminfo content."""
        info: Dict[str, Any] = {}
        
        # Extract key memory values
        mem_total = self._extract_meminfo_value(meminfo_content, 'MemTotal')
        mem_free = self._extract_meminfo_value(meminfo_content, 'MemFree')
        mem_available = self._extract_meminfo_value(meminfo_content, 'MemAvailable')
        buffers = self._extract_meminfo_value(meminfo_content, 'Buffers')
        cached = self._extract_meminfo_value(meminfo_content, 'Cached')
        swap_total = self._extract_meminfo_value(meminfo_content, 'SwapTotal')
        swap_free = self._extract_meminfo_value(meminfo_content, 'SwapFree')
        
        if mem_total:
            info['memory_total_kb'] = mem_total
            info['memory_total_gb'] = round(mem_total / 1024 / 1024, 2)
        
        if mem_free:
            info['memory_free_kb'] = mem_free
            info['memory_free_gb'] = round(mem_free / 1024 / 1024, 2)
        
        if mem_available:
            info['memory_available_kb'] = mem_available
            info['memory_available_gb'] = round(mem_available / 1024 / 1024, 2)
        
        if buffers:
            info['buffers_kb'] = buffers
        
        if cached:
            info['cached_kb'] = cached
        
        if swap_total:
            info['swap_total_kb'] = swap_total
            info['swap_total_gb'] = round(swap_total / 1024 / 1024, 2)
        
        if swap_free:
            info['swap_free_kb'] = swap_free
            info['swap_used_kb'] = swap_total - swap_free if swap_total else 0
        
        # Calculate memory usage percentage
        if mem_total and mem_available:
            mem_used = mem_total - mem_available
            info['memory_usage_percent'] = round((mem_used / mem_total) * 100, 2)
        
        return info
    
    def _parse_free_output(self, free_output: str) -> Dict[str, Any]:
        """Parse free command output."""
        info: Dict[str, Any] = {}
        
        lines = free_output.strip().split('\n')
        if len(lines) >= 2:
            # Parse the memory line
            mem_line = lines[1].split()
            if len(mem_line) >= 7:
                info['free_memory_total'] = mem_line[1]
                info['free_memory_used'] = mem_line[2]
                info['free_memory_free'] = mem_line[3]
                info['free_memory_shared'] = mem_line[4]
                info['free_memory_buff_cache'] = mem_line[5]
                info['free_memory_available'] = mem_line[6]
        
        return info
    
    def _parse_dmidecode_memory(self, dmidecode_output: str) -> Dict[str, Any]:
        """Parse dmidecode memory output."""
        info: Dict[str, Any] = {}
        memory_devices = []
        
        # Split into individual memory device sections
        sections = re.split(r'Handle 0x[0-9A-Fa-f]+, DMI type 17,', dmidecode_output)
        
        for section in sections[1:]:  # Skip the first empty section
            device_info = self._parse_memory_device_section(section)
            if device_info:
                memory_devices.append(device_info)
        
        if memory_devices:
            info['memory_devices'] = memory_devices
            info['memory_device_count'] = len(memory_devices)
            
            # Calculate total installed memory
            total_size = 0
            for device in memory_devices:
                if device.get('size_mb'):
                    total_size += device['size_mb']
            
            if total_size > 0:
                info['total_installed_memory_mb'] = total_size
                info['total_installed_memory_gb'] = round(total_size / 1024, 2)
        
        return info
    
    def _parse_memory_device_section(self, section: str) -> Optional[Dict[str, Any]]:
        """Parse a single memory device section from dmidecode."""
        device_info = {}
        
        # Extract size
        size_match = re.search(r'Size:\s*(.+)', section)
        if size_match:
            size_str = size_match.group(1).strip()
            if 'No Module Installed' not in size_str and size_str != '0':
                device_info['size'] = size_str
                # Convert to MB for calculations
                if 'GB' in size_str:
                    size_gb = float(re.search(r'(\d+)', size_str).group(1))
                    device_info['size_mb'] = int(size_gb * 1024)
                elif 'MB' in size_str:
                    device_info['size_mb'] = int(re.search(r'(\d+)', size_str).group(1))
        
        # Extract type
        type_match = re.search(r'Type:\s*(.+)', section)
        if type_match:
            device_info['type'] = type_match.group(1).strip()
        
        # Extract speed
        speed_match = re.search(r'Speed:\s*(.+)', section)
        if speed_match:
            device_info['speed'] = speed_match.group(1).strip()
        
        # Extract manufacturer
        manufacturer_match = re.search(r'Manufacturer:\s*(.+)', section)
        if manufacturer_match:
            device_info['manufacturer'] = manufacturer_match.group(1).strip()
        
        # Extract part number
        part_match = re.search(r'Part Number:\s*(.+)', section)
        if part_match:
            device_info['part_number'] = part_match.group(1).strip()
        
        # Extract locator
        locator_match = re.search(r'Locator:\s*(.+)', section)
        if locator_match:
            device_info['locator'] = locator_match.group(1).strip()
        
        return device_info if device_info else None
    
    def _parse_memory_controller(self, controller_output: str) -> Dict[str, Any]:
        """Parse memory controller information."""
        info: Dict[str, Any] = {}
        
        # Extract maximum capacity
        max_capacity_match = re.search(r'Maximum Capacity:\s*(.+)', controller_output)
        if max_capacity_match:
            info['max_capacity'] = max_capacity_match.group(1).strip()
        
        # Extract number of devices
        num_devices_match = re.search(r'Number Of Devices:\s*(.+)', controller_output)
        if num_devices_match:
            info['max_memory_devices'] = int(num_devices_match.group(1).strip())
        
        return info
    
    def _extract_meminfo_value(self, meminfo_content: str, key: str) -> Optional[int]:
        """Extract a value from /proc/meminfo."""
        pattern = rf'{key}:\s*(\d+)\s*kB'
        match = re.search(pattern, meminfo_content)
        return int(match.group(1)) if match else None
    
    def _parse_vmstat(self, vmstat_content: str) -> Dict[str, Any]:
        """Parse /proc/vmstat content."""
        info: Dict[str, Any] = {}
        
        # Extract key VM statistics
        vm_stats = {}
        for line in vmstat_content.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) == 2:
                    vm_stats[parts[0]] = int(parts[1])
        
        # Extract relevant memory statistics
        if 'pgfault' in vm_stats:
            info['page_faults'] = vm_stats['pgfault']
        
        if 'pgmajfault' in vm_stats:
            info['major_page_faults'] = vm_stats['pgmajfault']
        
        if 'pswpin' in vm_stats:
            info['swap_in_pages'] = vm_stats['pswpin']
        
        if 'pswpout' in vm_stats:
            info['swap_out_pages'] = vm_stats['pswpout']
        
        return info
    
    def _get_edac_info(self) -> Optional[Dict[str, Any]]:
        """Get EDAC (Error Detection and Correction) information."""
        edac_info = {}
        
        # Check if EDAC is available
        if not self.system.file_exists('/sys/devices/system/edac'):
            return None
        
        # Get memory controller information
        mc_dirs = []
        for i in range(10):  # Check for up to 10 memory controllers
            mc_path = f'/sys/devices/system/edac/mc/mc{i}'
            if self.system.file_exists(mc_path):
                mc_dirs.append(mc_path)
        
        if mc_dirs:
            edac_info['memory_controllers'] = []
            for mc_path in mc_dirs:
                mc_info = {}
                
                # Get memory controller size
                size_mb = self.system.read_file(f'{mc_path}/size_mb')
                if size_mb:
                    mc_info['size_mb'] = int(size_mb)
                
                # Get memory controller type
                mc_name = self.system.read_file(f'{mc_path}/mc_name')
                if mc_name:
                    mc_info['name'] = mc_name
                
                edac_info['memory_controllers'].append(mc_info)
        
        return edac_info if edac_info else None
    
    def _get_memory_bandwidth_info(self) -> Optional[Dict[str, Any]]:
        """Get memory bandwidth information if available."""
        # This would typically require specialized tools or hardware counters
        # For now, return None as this requires more advanced implementation
        return None
    
    def _get_memory_pressure_info(self) -> Optional[Dict[str, Any]]:
        """Get memory pressure information."""
        pressure_info = {}
        
        # Check for PSI (Pressure Stall Information)
        memory_pressure = self.system.read_file('/proc/pressure/memory')
        if memory_pressure:
            pressure_info['psi_memory'] = memory_pressure
            # Parse PSI data
            for line in memory_pressure.split('\n'):
                if line.startswith('some'):
                    # Extract pressure percentages
                    parts = line.split()
                    for part in parts[1:]:
                        if '=' in part:
                            key, value = part.split('=')
                            if key in ['avg10', 'avg60', 'avg300']:
                                pressure_info[f'memory_pressure_{key}'] = float(value)
        
        return pressure_info if pressure_info else None
    
    def _get_numa_info(self) -> Optional[Dict[str, Any]]:
        """Get NUMA (Non-Uniform Memory Access) information."""
        numa_info = {}
        
        # Check if NUMA is available
        if not self.system.file_exists('/sys/devices/system/node'):
            return None
        
        # Get NUMA node information
        numactl_result = self.system.run_command(['numactl', '--hardware'])
        if numactl_result.success:
            numa_info['numactl_hardware'] = numactl_result.stdout
            numa_info.update(self._parse_numactl_output(numactl_result.stdout))
        
        return numa_info if numa_info else None
    
    def _parse_numactl_output(self, numactl_output: str) -> Dict[str, Any]:
        """Parse numactl --hardware output."""
        info = {}
        
        # Extract number of nodes
        nodes_match = re.search(r'available: (\d+) nodes', numactl_output)
        if nodes_match:
            info['numa_nodes'] = int(nodes_match.group(1))
        
        # Extract node distances
        distances_section = re.search(r'node distances:(.*?)(?=\n\w|\Z)', numactl_output, re.DOTALL)
        if distances_section:
            info['node_distances'] = distances_section.group(1).strip()
        
        return info
    
    def _analyze_memory_fragmentation(self, buddyinfo_content: str) -> Dict[str, Any]:
        """Analyze memory fragmentation from /proc/buddyinfo."""
        fragmentation_info = {'fragmented': False, 'analysis': []}
        
        for line in buddyinfo_content.split('\n'):
            if line.strip() and 'Node' in line:
                parts = line.split()
                if len(parts) >= 4:
                    # Check higher order pages availability
                    higher_order_pages = [int(x) for x in parts[4:]]
                    total_higher_order = sum(higher_order_pages)
                    
                    if total_higher_order < 100:  # Arbitrary threshold
                        fragmentation_info['fragmented'] = True
                        fragmentation_info['analysis'].append({
                            'node': parts[1].rstrip(','),
                            'zone': parts[3],
                            'higher_order_pages': total_higher_order
                        })
        
        return fragmentation_info