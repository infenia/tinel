#!/usr/bin/env python3
"""Kernel information tool providers."""

from typing import Any, Dict
from .base import BaseToolProvider
from ..kernel.config_parser import KernelConfigParser
from ..kernel.config_analyzer import KernelConfigAnalyzer
from ..interfaces import SystemInterface


class KernelToolProvider(BaseToolProvider):
    """Base class for kernel information tools."""
    
    def __init__(self, name: str, description: str, system_interface: SystemInterface):
        """Initialize kernel tool provider.
        
        Args:
            name: Tool name
            description: Tool description
            system_interface: System interface for command execution
        """
        super().__init__(name, description)
        self.system = system_interface


class KernelInfoToolProvider(KernelToolProvider):
    """Tool provider for basic kernel information."""
    
    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_kernel_info",
            "Get basic kernel information including version, command line, and loaded modules",
            system_interface
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get kernel information."""
        info: Dict[str, Any] = {}
        
        # Get kernel version
        uname_result = self.system.run_command(['uname', '-a'])
        if uname_result.success:
            info['uname'] = uname_result.stdout
        
        # Get kernel version from /proc/version
        proc_version = self.system.read_file('/proc/version')
        if proc_version:
            info['proc_version'] = proc_version
        else:
            info['proc_version_error'] = 'Could not read /proc/version'
        
        # Get kernel command line
        cmdline = self.system.read_file('/proc/cmdline')
        if cmdline:
            info['cmdline'] = cmdline
        else:
            info['cmdline_error'] = 'Could not read /proc/cmdline'
        
        # Get loaded modules
        lsmod_result = self.system.run_command(['lsmod'])
        if lsmod_result.success:
            info['loaded_modules'] = lsmod_result.stdout
        
        return info


class KernelConfigToolProvider(KernelToolProvider):
    """Tool provider for kernel configuration."""
    
    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_kernel_config",
            "Get detailed kernel configuration options and settings",
            system_interface
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get kernel configuration."""
        info: Dict[str, Any] = {}
        
        try:
            parser = KernelConfigParser(self.system)
            
            # Parse kernel configuration
            config = parser.parse_config()
            if config:
                # Convert to serializable format
                config_dict = {
                    'version': config.version,
                    'options': {
                        name: {
                            'name': opt.name,
                            'value': opt.value,
                            'description': opt.description,
                            'recommended': opt.recommended,
                            'security_impact': opt.security_impact,
                            'performance_impact': opt.performance_impact
                        }
                        for name, opt in config.options.items()
                    },
                    'analysis': config.analysis,
                    'recommendations': config.recommendations
                }
                info['config'] = config_dict
            else:
                info['error'] = 'Could not parse kernel configuration'
        
        except Exception as e:
            info['error'] = f'Error parsing kernel configuration: {str(e)}'
        
        return info


class KernelConfigAnalysisToolProvider(KernelToolProvider):
    """Tool provider for kernel configuration analysis."""
    
    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "analyze_kernel_config",
            "Analyze kernel configuration for security and performance recommendations",
            system_interface
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to analyze kernel configuration."""
        info: Dict[str, Any] = {}
        
        try:
            parser = KernelConfigParser(self.system)
            analyzer = KernelConfigAnalyzer()
            
            # Parse and analyze kernel configuration
            config = parser.parse_config()
            if config:
                analysis = analyzer.analyze_config(config)
                info['analysis'] = analysis
            else:
                info['error'] = 'Could not parse kernel configuration for analysis'
        
        except Exception as e:
            info['error'] = f'Error analyzing kernel configuration: {str(e)}'
        
        return info


class KernelModulesToolProvider(KernelToolProvider):
    """Tool provider for kernel module information."""
    
    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_kernel_modules",
            "Get detailed information about kernel modules (loaded and available)",
            system_interface
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get kernel module information."""
        info: Dict[str, Any] = {}
        
        # Get loaded modules with details
        lsmod_result = self.system.run_command(['lsmod'])
        if lsmod_result.success:
            info['loaded_modules'] = lsmod_result.stdout
        
        # Get module information
        modinfo_results = {}
        
        # Get list of loaded modules
        if lsmod_result.success:
            lines = lsmod_result.stdout.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    module_name = line.split()[0]
                    modinfo_result = self.system.run_command(['modinfo', module_name])
                    if modinfo_result.success:
                        modinfo_results[module_name] = modinfo_result.stdout
        
        info['module_details'] = modinfo_results
        
        # Get available modules
        find_modules = self.system.run_command(['find', '/lib/modules', '-name', '*.ko', '-type', 'f'])
        if find_modules.success:
            info['available_modules'] = find_modules.stdout.split('\n')
        
        return info


class KernelParametersToolProvider(KernelToolProvider):
    """Tool provider for kernel runtime parameters."""
    
    def __init__(self, system_interface: SystemInterface):
        super().__init__(
            "get_kernel_parameters",
            "Get kernel runtime parameters and sysctl settings",
            system_interface
        )
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool to get kernel parameters."""
        info: Dict[str, Any] = {}
        
        # Get sysctl parameters
        sysctl_result = self.system.run_command(['sysctl', '-a'])
        if sysctl_result.success:
            info['sysctl_all'] = sysctl_result.stdout
        
        # Get specific important parameters
        important_params = [
            'kernel.version',
            'kernel.ostype',
            'kernel.osrelease',
            'vm.swappiness',
            'vm.dirty_ratio',
            'net.core.rmem_max',
            'net.core.wmem_max',
            'fs.file-max'
        ]
        
        param_values = {}
        for param in important_params:
            param_result = self.system.run_command(['sysctl', param])
            if param_result.success:
                param_values[param] = param_result.stdout
        
        info['important_parameters'] = param_values
        
        return info