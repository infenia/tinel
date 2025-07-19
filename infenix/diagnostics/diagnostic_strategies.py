#!/usr/bin/env python3
"""Diagnostic Strategy Pattern Implementation.

Copyright 2024 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface


class DiagnosticStrategy(ABC):
    """Abstract base class for diagnostic strategies."""
    
    def __init__(self, system_interface: SystemInterface):
        """Initialize diagnostic strategy."""
        self.system = system_interface
    
    @abstractmethod
    def run_diagnostic(self) -> Dict[str, Any]:
        """Run the diagnostic check."""
        pass
    
    @abstractmethod
    def get_thresholds(self) -> Dict[str, Any]:
        """Get diagnostic thresholds."""
        pass


class TemperatureDiagnosticStrategy(DiagnosticStrategy):
    """Strategy for temperature-based diagnostics."""
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """Check system temperatures."""
        result = {'status': 'normal', 'temperatures': {}, 'issues': []}
        
        # Check CPU temperature
        cpu_temp = self._check_cpu_temperature()
        if cpu_temp:
            result['temperatures']['cpu'] = cpu_temp
            if cpu_temp > self.get_thresholds()['cpu']['critical']:
                result['status'] = 'critical'
                result['issues'].append({
                    'component': 'cpu',
                    'severity': 'high',
                    'message': f'CPU temperature critical: {cpu_temp}°C'
                })
            elif cpu_temp > self.get_thresholds()['cpu']['warning']:
                result['status'] = 'warning'
                result['issues'].append({
                    'component': 'cpu',
                    'severity': 'medium',
                    'message': f'CPU temperature high: {cpu_temp}°C'
                })
        
        return result
    
    def get_thresholds(self) -> Dict[str, Any]:
        """Get temperature thresholds."""
        return {
            'cpu': {'warning': 70, 'critical': 80},
            'gpu': {'warning': 75, 'critical': 85}
        }
    
    def _check_cpu_temperature(self) -> Optional[float]:
        """Check CPU temperature from thermal zones."""
        import os
        
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
                        return int(f.read().strip()) / 1000  # Convert from millidegrees
        except Exception:
            pass
        
        return None


class ResourceUsageDiagnosticStrategy(DiagnosticStrategy):
    """Strategy for resource usage diagnostics."""
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """Check resource usage."""
        result = {'status': 'normal', 'usage': {}, 'issues': []}
        
        # Check memory usage
        memory_usage = self._check_memory_usage()
        if memory_usage:
            result['usage']['memory'] = memory_usage
            thresholds = self.get_thresholds()['memory']
            
            if memory_usage > thresholds['critical']:
                result['status'] = 'critical'
                result['issues'].append({
                    'component': 'memory',
                    'severity': 'high',
                    'message': f'Memory usage critical: {memory_usage}%'
                })
            elif memory_usage > thresholds['warning']:
                result['status'] = 'warning'
                result['issues'].append({
                    'component': 'memory',
                    'severity': 'medium',
                    'message': f'Memory usage high: {memory_usage}%'
                })
        
        # Check disk usage
        disk_usage = self._check_disk_usage()
        if disk_usage:
            result['usage']['disk'] = disk_usage
            for mount_point, usage_percent in disk_usage.items():
                thresholds = self.get_thresholds()['disk']
                
                if usage_percent > thresholds['critical']:
                    result['status'] = 'critical'
                    result['issues'].append({
                        'component': 'storage',
                        'severity': 'high',
                        'message': f'Disk usage critical on {mount_point}: {usage_percent}%'
                    })
                elif usage_percent > thresholds['warning']:
                    if result['status'] == 'normal':
                        result['status'] = 'warning'
                    result['issues'].append({
                        'component': 'storage',
                        'severity': 'medium',
                        'message': f'Disk usage high on {mount_point}: {usage_percent}%'
                    })
        
        return result
    
    def get_thresholds(self) -> Dict[str, Any]:
        """Get resource usage thresholds."""
        return {
            'memory': {'warning': 80, 'critical': 90},
            'disk': {'warning': 85, 'critical': 95},
            'cpu': {'warning': 80, 'critical': 95}
        }
    
    def _check_memory_usage(self) -> Optional[float]:
        """Check memory usage percentage."""
        import re
        
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
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
                return round((used / total) * 100, 1)
        except Exception:
            pass
        
        return None
    
    def _check_disk_usage(self) -> Dict[str, float]:
        """Check disk usage for all mounted filesystems."""
        usage = {}
        
        df_result = self.system.run_command(['df', '-h'])
        if df_result.success:
            lines = df_result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    mount_point = parts[5]
                    use_percent_str = parts[4]
                    
                    try:
                        use_percent = int(use_percent_str.rstrip('%'))
                        usage[mount_point] = use_percent
                    except ValueError:
                        continue
        
        return usage


class NetworkDiagnosticStrategy(DiagnosticStrategy):
    """Strategy for network diagnostics."""
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """Check network connectivity and interfaces."""
        result = {'status': 'normal', 'interfaces': {}, 'issues': []}
        
        # Check interface status
        interface_status = self._check_interface_status()
        result['interfaces'] = interface_status
        
        # Check for down interfaces
        down_interfaces = [name for name, status in interface_status.items() 
                          if status.get('state') == 'DOWN']
        
        if down_interfaces:
            result['status'] = 'warning'
            result['issues'].append({
                'component': 'network',
                'severity': 'medium',
                'message': f'Network interfaces down: {", ".join(down_interfaces)}'
            })
        
        return result
    
    def get_thresholds(self) -> Dict[str, Any]:
        """Get network diagnostic thresholds."""
        return {
            'packet_loss': {'warning': 1.0, 'critical': 5.0},
            'latency': {'warning': 100, 'critical': 500}
        }
    
    def _check_interface_status(self) -> Dict[str, Dict[str, Any]]:
        """Check status of network interfaces."""
        interfaces = {}
        
        ip_result = self.system.run_command(['ip', 'link', 'show'])
        if ip_result.success:
            current_interface = None
            
            for line in ip_result.stdout.split('\n'):
                # New interface line
                if not line.startswith(' '):
                    import re
                    match = re.match(r'^\d+: ([^:@]+)[@:].*state (\w+)', line)
                    if match:
                        interface_name = match.group(1)
                        interface_state = match.group(2)
                        
                        interfaces[interface_name] = {
                            'state': interface_state,
                            'type': 'unknown'
                        }
                        current_interface = interface_name
        
        return interfaces


class DiagnosticContext:
    """Context class for managing diagnostic strategies."""
    
    def __init__(self, system_interface: SystemInterface):
        """Initialize diagnostic context."""
        self.system = system_interface
        self.strategies = {
            'temperature': TemperatureDiagnosticStrategy(system_interface),
            'resource_usage': ResourceUsageDiagnosticStrategy(system_interface),
            'network': NetworkDiagnosticStrategy(system_interface)
        }
    
    def run_diagnostic(self, strategy_name: str) -> Dict[str, Any]:
        """Run a specific diagnostic strategy."""
        if strategy_name not in self.strategies:
            raise ValueError(f"Unknown diagnostic strategy: {strategy_name}")
        
        return self.strategies[strategy_name].run_diagnostic()
    
    def run_all_diagnostics(self) -> Dict[str, Any]:
        """Run all available diagnostic strategies."""
        results = {}
        overall_status = 'normal'
        all_issues = []
        
        for name, strategy in self.strategies.items():
            result = strategy.run_diagnostic()
            results[name] = result
            
            # Aggregate status
            if result['status'] == 'critical':
                overall_status = 'critical'
            elif result['status'] == 'warning' and overall_status == 'normal':
                overall_status = 'warning'
            
            # Aggregate issues
            all_issues.extend(result.get('issues', []))
        
        return {
            'overall_status': overall_status,
            'results': results,
            'issues': all_issues
        }