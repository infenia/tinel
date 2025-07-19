#!/usr/bin/env python3
"""Hardware Diagnostics Module.

Copyright 2024 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import os
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface
from .constants import TEMPERATURE_THRESHOLDS, RESOURCE_THRESHOLDS
from .exceptions import HardwareDiagnosticsError


class HardwareDiagnostics:
    """Handles hardware-specific diagnostic checks."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize hardware diagnostics."""
        self.system = system_interface or LinuxSystemInterface()
        self.thresholds = self._load_thresholds()
    
    def run_comprehensive_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive hardware diagnostics."""
        results = {}
        issues = []
        recommendations = []
        
        # Run individual component diagnostics
        components = ['cpu', 'memory', 'storage', 'network']
        for component in components:
            result = getattr(self, f'_run_{component}_diagnostics')()
            results[component] = result
            
            if result.get('issues'):
                issues.extend(result['issues'])
            if result.get('recommendations'):
                recommendations.extend(result['recommendations'])
        
        return {
            'status': 'failed' if issues else 'passed',
            'results': results,
            'issues': issues,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_cpu_diagnostics(self) -> Dict[str, Any]:
        """Run CPU-specific diagnostics."""
        results = {'status': 'passed', 'issues': [], 'recommendations': []}
        
        # Temperature check
        temp_result = self._check_cpu_temperature()
        self._process_diagnostic_result(results, temp_result, 'cpu', 'temperature')
        
        # Load check
        load_result = self._check_cpu_load()
        self._process_diagnostic_result(results, load_result, 'cpu', 'load')
        
        return results
    
    def _run_memory_diagnostics(self) -> Dict[str, Any]:
        """Run memory-specific diagnostics."""
        results = {'status': 'passed', 'issues': [], 'recommendations': []}
        
        usage_result = self._check_memory_usage()
        self._process_diagnostic_result(results, usage_result, 'memory', 'usage')
        
        return results
    
    def _run_storage_diagnostics(self) -> Dict[str, Any]:
        """Run storage-specific diagnostics."""
        results = {'status': 'passed', 'issues': [], 'recommendations': []}
        
        fs_result = self._check_filesystem_usage()
        for fs_path, fs_data in fs_result.items():
            if fs_data.get('status') in ['warning', 'critical']:
                severity = 'high' if fs_data.get('status') == 'critical' else 'medium'
                results['issues'].append({
                    'component': 'storage',
                    'severity': severity,
                    'message': f"Disk usage on {fs_path}: {fs_data.get('used_percent', 'unknown')}%"
                })
                results['recommendations'].append({
                    'component': 'storage',
                    'priority': severity,
                    'action': f"Free up space on {fs_path}",
                    'details': 'Remove unnecessary files or expand storage'
                })
        
        if results['issues']:
            results['status'] = 'failed'
        
        return results
    
    def _run_network_diagnostics(self) -> Dict[str, Any]:
        """Run network-specific diagnostics."""
        results = {'status': 'passed', 'issues': [], 'recommendations': []}
        
        net_result = self._check_network_interfaces()
        if net_result.get('issues'):
            for issue in net_result['issues']:
                results['issues'].append({
                    'component': 'network',
                    'severity': issue.get('severity', 'medium'),
                    'message': issue.get('message', 'Network issue detected')
                })
                results['recommendations'].append({
                    'component': 'network',
                    'priority': issue.get('severity', 'medium'),
                    'action': issue.get('recommendation', 'Check network configuration'),
                    'details': issue.get('details', 'Review network settings')
                })
        
        if results['issues']:
            results['status'] = 'failed'
        
        return results
    
    def _check_cpu_temperature(self) -> Dict[str, Any]:
        """Check CPU temperature using thermal zones."""
        result = {'status': 'normal', 'temperature': None, 'metric': 'temperature'}
        
        try:
            thermal_zones = [d for d in os.listdir('/sys/class/thermal/') 
                           if d.startswith('thermal_zone')]
            
            for zone in thermal_zones:
                zone_path = f'/sys/class/thermal/{zone}'
                type_path = f'{zone_path}/type'
                temp_path = f'{zone_path}/temp'
                
                if not (os.path.exists(type_path) and os.path.exists(temp_path)):
                    continue
                
                with open(type_path, 'r') as f:
                    zone_type = f.read().strip()
                
                if any(cpu_type in zone_type.lower() for cpu_type in ['cpu', 'x86', 'acpi']):
                    with open(temp_path, 'r') as f:
                        temp = int(f.read().strip()) / 1000  # Convert from millidegrees
                        result['temperature'] = temp
                        
                        if temp > self.thresholds['cpu']['temperature']['critical']:
                            result['status'] = 'critical'
                        elif temp > self.thresholds['cpu']['temperature']['warning']:
                            result['status'] = 'warning'
                        
                        return result
        except Exception:
            result['status'] = 'error'
            result['error'] = 'Unable to read CPU temperature'
        
        return result
    
    def _check_cpu_load(self) -> Dict[str, Any]:
        """Check CPU load average."""
        result = {'status': 'normal', 'metric': 'load'}
        
        try:
            with open('/proc/loadavg', 'r') as f:
                load_data = f.read().strip().split()
                
            if len(load_data) >= 3:
                load_1min = float(load_data[0])
                result['load_avg_1min'] = load_1min
                
                cpu_count = os.cpu_count() or 1
                load_per_core = load_1min / cpu_count
                
                if load_per_core > self.thresholds['cpu']['load']['warning']:
                    result['status'] = 'warning'
        except Exception:
            result['status'] = 'error'
            result['error'] = 'Unable to read CPU load'
        
        return result
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage from /proc/meminfo."""
        result = {'status': 'normal', 'metric': 'usage'}
        
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # Parse memory information
            memory_values = {}
            for key in ['MemTotal', 'MemFree', 'Buffers', 'Cached']:
                match = re.search(rf'{key}:\s+(\d+)', meminfo)
                if match:
                    memory_values[key] = int(match.group(1))
            
            if len(memory_values) == 4:
                total = memory_values['MemTotal']
                free = memory_values['MemFree']
                buffers = memory_values['Buffers']
                cached = memory_values['Cached']
                
                used = total - free - buffers - cached
                used_percent = (used / total) * 100
                
                result['used_percent'] = round(used_percent, 1)
                
                if used_percent > self.thresholds['memory']['usage']['critical']:
                    result['status'] = 'critical'
                elif used_percent > self.thresholds['memory']['usage']['warning']:
                    result['status'] = 'warning'
        except Exception:
            result['status'] = 'error'
            result['error'] = 'Unable to read memory usage'
        
        return result
    
    def _check_filesystem_usage(self) -> Dict[str, Dict[str, Any]]:
        """Check filesystem usage using df command."""
        result = {}
        
        df_result = self.system.run_command(['df', '-h'])
        if not df_result.success:
            return result
        
        lines = df_result.stdout.strip().split('\n')[1:]  # Skip header
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                filesystem = parts[0]
                size = parts[1]
                used = parts[2]
                available = parts[3]
                use_percent_str = parts[4]
                mount_point = parts[5]
                
                try:
                    use_percent = int(use_percent_str.rstrip('%'))
                    
                    status = 'normal'
                    if use_percent > self.thresholds['storage']['usage']['critical']:
                        status = 'critical'
                    elif use_percent > self.thresholds['storage']['usage']['warning']:
                        status = 'warning'
                    
                    result[mount_point] = {
                        'filesystem': filesystem,
                        'size': size,
                        'used': used,
                        'available': available,
                        'used_percent': use_percent,
                        'status': status
                    }
                except ValueError:
                    continue
        
        return result
    
    def _check_network_interfaces(self) -> Dict[str, Any]:
        """Check network interface status."""
        result = {'status': 'normal', 'issues': []}
        
        ip_result = self.system.run_command(['ip', 'link', 'show'])
        if ip_result.success and 'state DOWN' in ip_result.stdout:
            result['issues'].append({
                'severity': 'medium',
                'message': 'Some network interfaces are down',
                'recommendation': 'Check network interface configuration',
                'details': 'Review network settings and cable connections'
            })
        
        return result
    
    def _process_diagnostic_result(
        self, 
        results: Dict[str, Any], 
        check_result: Dict[str, Any], 
        component: str, 
        check_type: str
    ) -> None:
        """Process diagnostic check result and update results."""
        status = check_result.get('status', 'normal')
        
        if status in ['warning', 'critical']:
            severity = 'high' if status == 'critical' else 'medium'
            
            # Create issue message based on check type
            if check_type == 'temperature':
                temp = check_result.get('temperature', 'unknown')
                message = f"CPU temperature: {temp}°C"
                action = 'Check CPU cooling system'
                details = 'Clean fans, verify thermal paste, ensure proper airflow'
            elif check_type == 'load':
                load = check_result.get('load_avg_1min', 'unknown')
                message = f"High CPU load: {load}"
                action = 'Investigate high CPU usage'
                details = 'Check for resource-intensive processes'
            elif check_type == 'usage':
                usage = check_result.get('used_percent', 'unknown')
                message = f"Memory usage: {usage}%"
                action = 'Address high memory usage'
                details = 'Close unnecessary applications or add more RAM'
            else:
                message = f"{component} {check_type} issue"
                action = f"Check {component} {check_type}"
                details = f"Review {component} configuration"
            
            results['issues'].append({
                'component': component,
                'severity': severity,
                'message': message
            })
            
            results['recommendations'].append({
                'component': component,
                'priority': severity,
                'action': action,
                'details': details
            })
            
            results['status'] = 'failed'
    
    @lru_cache(maxsize=1)
    def _load_thresholds(self) -> Dict[str, Any]:
        """Load diagnostic thresholds from constants."""
        return {
            'cpu': {
                'temperature': {
                    'warning': TEMPERATURE_THRESHOLDS['CPU']['WARNING'],
                    'critical': TEMPERATURE_THRESHOLDS['CPU']['CRITICAL']
                },
                'load': {'warning': 1.5, 'critical': 2.0}
            },
            'memory': {
                'usage': {
                    'warning': RESOURCE_THRESHOLDS['MEMORY']['WARNING'],
                    'critical': RESOURCE_THRESHOLDS['MEMORY']['CRITICAL']
                }
            },
            'storage': {
                'usage': {
                    'warning': RESOURCE_THRESHOLDS['DISK']['WARNING'],
                    'critical': RESOURCE_THRESHOLDS['DISK']['CRITICAL']
                }
            }
        }