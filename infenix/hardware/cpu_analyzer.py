#!/usr/bin/env python3
"""Enhanced CPU Analysis Module.

This module provides detailed CPU information gathering including feature
detection, optimization analysis, and performance metrics.

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

import re
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface


class CPUAnalyzer:
    """Enhanced CPU analyzer with detailed feature detection."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize CPU analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get comprehensive CPU information.
        
        Returns:
            Dictionary containing detailed CPU information
        """
        info: Dict[str, Any] = {}
        
        # Get basic CPU info
        info.update(self._get_basic_cpu_info())
        
        # Get CPU features and capabilities
        info.update(self._get_cpu_features())
        
        # Get CPU frequency information
        info.update(self._get_frequency_info())
        
        # Get CPU topology information
        info.update(self._get_topology_info())
        
        # Get CPU cache information
        info.update(self._get_cache_info())
        
        # Get CPU optimization analysis
        info.update(self._analyze_cpu_optimization())
        
        return info
    
    def _get_basic_cpu_info(self) -> Dict[str, Any]:
        """Get basic CPU information from /proc/cpuinfo and lscpu."""
        info: Dict[str, Any] = {}
        
        # Get CPU info from /proc/cpuinfo
        cpuinfo_content = self.system.read_file('/proc/cpuinfo')
        if cpuinfo_content:
            info['proc_cpuinfo'] = cpuinfo_content
            info.update(self._parse_cpuinfo(cpuinfo_content))
        else:
            info['proc_cpuinfo_error'] = 'Failed to read /proc/cpuinfo'
        
        # Get CPU info using lscpu
        lscpu_result = self.system.run_command(['lscpu'])
        if lscpu_result.success:
            info['lscpu'] = lscpu_result.stdout
            info.update(self._parse_lscpu(lscpu_result.stdout))
        else:
            info['lscpu_error'] = lscpu_result.error or 'Failed to run lscpu'
        
        return info
    
    def _get_cpu_features(self) -> Dict[str, Any]:
        """Get detailed CPU features and capabilities."""
        info: Dict[str, Any] = {}
        
        # Get CPU flags from /proc/cpuinfo
        cpuinfo_content = self.system.read_file('/proc/cpuinfo')
        if cpuinfo_content:
            flags = self._extract_cpu_flags(cpuinfo_content)
            info['cpu_flags'] = flags
            info['security_features'] = self._analyze_security_features(flags)
            info['performance_features'] = self._analyze_performance_features(flags)
            info['virtualization_features'] = self._analyze_virtualization_features(flags)
        
        # Get CPU vulnerabilities
        info['vulnerabilities'] = self._get_cpu_vulnerabilities()
        
        return info
    
    def _get_frequency_info(self) -> Dict[str, Any]:
        """Get detailed CPU frequency information."""
        info: Dict[str, Any] = {}
        
        # Get current frequency
        current_freq = self.system.read_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq')
        if current_freq:
            info['current_frequency_khz'] = int(current_freq)
            info['current_frequency_mhz'] = round(int(current_freq) / 1000, 2)
        
        # Get min/max frequencies
        min_freq = self.system.read_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq')
        if min_freq:
            info['min_frequency_khz'] = int(min_freq)
            info['min_frequency_mhz'] = round(int(min_freq) / 1000, 2)
        
        max_freq = self.system.read_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq')
        if max_freq:
            info['max_frequency_khz'] = int(max_freq)
            info['max_frequency_mhz'] = round(int(max_freq) / 1000, 2)
        
        # Get available governors
        governors = self.system.read_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors')
        if governors:
            info['available_governors'] = governors.split()
        
        # Get current governor
        current_governor = self.system.read_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')
        if current_governor:
            info['current_governor'] = current_governor
        
        return info
    
    def _get_topology_info(self) -> Dict[str, Any]:
        """Get CPU topology information."""
        info: Dict[str, Any] = {}
        
        # Get number of CPUs
        nproc_result = self.system.run_command(['nproc'])
        if nproc_result.success:
            info['logical_cpus'] = int(nproc_result.stdout)
        
        # Get physical CPU count
        physical_cpus = self.system.read_file('/sys/devices/system/cpu/cpu0/topology/physical_package_id')
        if physical_cpus is not None:
            # Count unique physical package IDs
            package_ids = set()
            cpu_num = 0
            while True:
                package_id = self.system.read_file(f'/sys/devices/system/cpu/cpu{cpu_num}/topology/physical_package_id')
                if package_id is None:
                    break
                package_ids.add(package_id)
                cpu_num += 1
            info['physical_cpus'] = len(package_ids)
        
        # Get cores per socket
        core_id = self.system.read_file('/sys/devices/system/cpu/cpu0/topology/core_id')
        if core_id is not None:
            core_ids = set()
            cpu_num = 0
            while True:
                core_id = self.system.read_file(f'/sys/devices/system/cpu/cpu{cpu_num}/topology/core_id')
                if core_id is None:
                    break
                core_ids.add(core_id)
                cpu_num += 1
            info['cores_per_socket'] = len(core_ids)
        
        return info
    
    def _get_cache_info(self) -> Dict[str, Any]:
        """Get CPU cache information."""
        info: Dict[str, Any] = {}
        cache_info = {}
        
        # Check for cache information in /sys/devices/system/cpu/cpu0/cache/
        for cache_level in ['index0', 'index1', 'index2', 'index3']:
            cache_path = f'/sys/devices/system/cpu/cpu0/cache/{cache_level}'
            if self.system.file_exists(f'{cache_path}/size'):
                cache_size = self.system.read_file(f'{cache_path}/size')
                cache_type = self.system.read_file(f'{cache_path}/type')
                cache_level_num = self.system.read_file(f'{cache_path}/level')
                
                if cache_size and cache_type and cache_level_num:
                    cache_info[f'L{cache_level_num}'] = {
                        'size': cache_size,
                        'type': cache_type
                    }
        
        if cache_info:
            info['cache'] = cache_info
        
        return info
    
    def _analyze_cpu_optimization(self) -> Dict[str, Any]:
        """Analyze CPU for optimization opportunities."""
        info: Dict[str, Any] = {}
        recommendations = []
        
        # Check governor settings
        current_governor = self.system.read_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')
        if current_governor == 'powersave':
            recommendations.append({
                'type': 'performance',
                'issue': 'CPU governor set to powersave',
                'recommendation': 'Consider using performance or ondemand governor for better performance',
                'command': 'echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
            })
        
        # Check for CPU vulnerabilities
        vulnerabilities = self._get_cpu_vulnerabilities()
        vulnerable_count = sum(1 for vuln in vulnerabilities.values() if 'Vulnerable' in str(vuln))
        if vulnerable_count > 0:
            recommendations.append({
                'type': 'security',
                'issue': f'{vulnerable_count} CPU vulnerabilities detected',
                'recommendation': 'Update kernel and microcode to mitigate CPU vulnerabilities',
                'command': 'sudo apt update && sudo apt upgrade linux-generic intel-microcode'
            })
        
        info['optimization_recommendations'] = recommendations
        return info
    
    def _parse_cpuinfo(self, cpuinfo_content: str) -> Dict[str, Any]:
        """Parse /proc/cpuinfo content."""
        info: Dict[str, Any] = {}
        
        # Extract model name
        model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo_content)
        if model_match:
            info['model_name'] = model_match.group(1).strip()
        
        # Extract vendor ID
        vendor_match = re.search(r'vendor_id\s*:\s*(.+)', cpuinfo_content)
        if vendor_match:
            info['vendor_id'] = vendor_match.group(1).strip()
        
        # Extract CPU family
        family_match = re.search(r'cpu family\s*:\s*(.+)', cpuinfo_content)
        if family_match:
            info['cpu_family'] = family_match.group(1).strip()
        
        # Extract model
        model_match = re.search(r'^model\s*:\s*(.+)', cpuinfo_content, re.MULTILINE)
        if model_match:
            info['model'] = model_match.group(1).strip()
        
        # Extract stepping
        stepping_match = re.search(r'stepping\s*:\s*(.+)', cpuinfo_content)
        if stepping_match:
            info['stepping'] = stepping_match.group(1).strip()
        
        return info
    
    def _parse_lscpu(self, lscpu_output: str) -> Dict[str, Any]:
        """Parse lscpu output."""
        info: Dict[str, Any] = {}
        
        # Extract architecture
        arch_match = re.search(r'Architecture:\s*(.+)', lscpu_output)
        if arch_match:
            info['architecture'] = arch_match.group(1).strip()
        
        # Extract CPU op-modes
        opmode_match = re.search(r'CPU op-mode\(s\):\s*(.+)', lscpu_output)
        if opmode_match:
            info['cpu_op_modes'] = opmode_match.group(1).strip()
        
        # Extract byte order
        byte_order_match = re.search(r'Byte Order:\s*(.+)', lscpu_output)
        if byte_order_match:
            info['byte_order'] = byte_order_match.group(1).strip()
        
        return info
    
    def _extract_cpu_flags(self, cpuinfo_content: str) -> List[str]:
        """Extract CPU flags from /proc/cpuinfo."""
        flags_match = re.search(r'flags\s*:\s*(.+)', cpuinfo_content)
        if flags_match:
            return flags_match.group(1).strip().split()
        return []
    
    def _analyze_security_features(self, flags: List[str]) -> Dict[str, bool]:
        """Analyze security-related CPU features."""
        security_features = {
            'nx_bit': 'nx' in flags,  # No-execute bit
            'smep': 'smep' in flags,  # Supervisor Mode Execution Prevention
            'smap': 'smap' in flags,  # Supervisor Mode Access Prevention
            'intel_pt': 'intel_pt' in flags,  # Intel Processor Trace
            'cet_ss': 'cet_ss' in flags,  # Control-flow Enforcement Technology Shadow Stack
            'cet_ibt': 'cet_ibt' in flags,  # Control-flow Enforcement Technology Indirect Branch Tracking
        }
        return security_features
    
    def _analyze_performance_features(self, flags: List[str]) -> Dict[str, bool]:
        """Analyze performance-related CPU features."""
        performance_features = {
            'sse': 'sse' in flags,
            'sse2': 'sse2' in flags,
            'sse3': 'pni' in flags,  # pni = Prescott New Instructions (SSE3)
            'ssse3': 'ssse3' in flags,
            'sse4_1': 'sse4_1' in flags,
            'sse4_2': 'sse4_2' in flags,
            'avx': 'avx' in flags,
            'avx2': 'avx2' in flags,
            'avx512f': 'avx512f' in flags,
            'aes': 'aes' in flags,  # AES acceleration
            'rdrand': 'rdrand' in flags,  # Hardware random number generator
            'rdseed': 'rdseed' in flags,  # Hardware random seed generator
        }
        return performance_features
    
    def _analyze_virtualization_features(self, flags: List[str]) -> Dict[str, bool]:
        """Analyze virtualization-related CPU features."""
        virt_features = {
            'vmx': 'vmx' in flags,  # Intel VT-x
            'svm': 'svm' in flags,  # AMD-V
            'ept': 'ept' in flags,  # Extended Page Tables
            'vpid': 'vpid' in flags,  # Virtual Processor ID
        }
        return virt_features
    
    def _get_cpu_vulnerabilities(self) -> Dict[str, str]:
        """Get CPU vulnerability information."""
        vulnerabilities = {}
        
        # Common CPU vulnerabilities to check
        vuln_files = [
            'spectre_v1', 'spectre_v2', 'meltdown', 'spec_store_bypass',
            'l1tf', 'mds', 'tsx_async_abort', 'itlb_multihit', 'srbds'
        ]
        
        for vuln in vuln_files:
            vuln_path = f'/sys/devices/system/cpu/vulnerabilities/{vuln}'
            vuln_status = self.system.read_file(vuln_path)
            if vuln_status:
                vulnerabilities[vuln] = vuln_status
        
        return vulnerabilities