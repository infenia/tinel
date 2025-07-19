#!/usr/bin/env python3
"""Kernel Configuration Parser Module.

This module provides kernel configuration parsing capabilities for Linux kernel
configurations from various sources including /proc/config.gz, /boot/config-*,
and modprobe configuration files.

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

import os
import re
import gzip
import glob
from typing import Dict, List, Optional, Tuple

from ..interfaces import KernelConfig, KernelConfigOption, SystemInterface
from ..system import LinuxSystemInterface


class KernelConfigParser:
    """Kernel configuration parser for Linux kernel configurations."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize kernel configuration parser.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # Configuration option descriptions
        self.option_descriptions = {}
        self._load_option_descriptions()
    
    def parse_config(self) -> Optional[KernelConfig]:
        """Parse kernel configuration from available sources.
        
        Returns:
            KernelConfig object or None if parsing fails
        """
        # Try to find kernel configuration from various sources
        config_content = self._get_kernel_config_content()
        if not config_content:
            return None
        
        # Parse kernel configuration
        kernel_version = self._get_kernel_version()
        if not kernel_version:
            return None
        
        # Parse configuration options
        options = self._parse_config_content(config_content)
        
        # Parse modprobe configuration
        modprobe_options = self._parse_modprobe_config()
        options.update(modprobe_options)
        
        # Create KernelConfig object
        return KernelConfig(
            version=kernel_version,
            options=options,
            analysis={},
            recommendations={}
        )
    
    def _get_kernel_config_content(self) -> Optional[str]:
        """Get kernel configuration content from available sources.
        
        Returns:
            Kernel configuration content as string or None if not found
        """
        # Try /proc/config.gz first (if kernel is compiled with CONFIG_IKCONFIG)
        if self.system.file_exists('/proc/config.gz'):
            try:
                # Use gzip to decompress the config file
                result = self.system.run_command(['zcat', '/proc/config.gz'])
                if result.success:
                    return result.stdout
            except Exception:
                pass
        
        # Try /boot/config-* files
        kernel_version = self._get_kernel_version()
        if kernel_version:
            config_path = f'/boot/config-{kernel_version}'
            if self.system.file_exists(config_path):
                config_content = self.system.read_file(config_path)
                if config_content:
                    return config_content
        
        # Try to find any config file in /boot
        result = self.system.run_command(['ls', '/boot/config-*'])
        if result.success:
            config_files = result.stdout.strip().split('\\n')
            if config_files:
                # Use the most recent config file
                config_files.sort()
                config_content = self.system.read_file(config_files[-1])
                if config_content:
                    return config_content
        
        # Try /usr/src/linux/.config
        if self.system.file_exists('/usr/src/linux/.config'):
            config_content = self.system.read_file('/usr/src/linux/.config')
            if config_content:
                return config_content
        
        return None
    
    def _get_kernel_version(self) -> Optional[str]:
        """Get current kernel version.
        
        Returns:
            Kernel version as string or None if not found
        """
        result = self.system.run_command(['uname', '-r'])
        if result.success:
            return result.stdout.strip()
        return None
    
    def _parse_config_content(self, content: str) -> Dict[str, KernelConfigOption]:
        """Parse kernel configuration content.
        
        Args:
            content: Kernel configuration content as string
            
        Returns:
            Dictionary of configuration options
        """
        options = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse configuration option
            if '=' in line:
                name, value = line.split('=', 1)
                name = name.strip()
                value = value.strip()
                
                # Get option description
                description = self.option_descriptions.get(name, '')
                
                # Create KernelConfigOption object
                options[name] = KernelConfigOption(
                    name=name,
                    value=value,
                    description=description
                )
        
        return options
    
    def _parse_modprobe_config(self) -> Dict[str, KernelConfigOption]:
        """Parse modprobe configuration files.
        
        Returns:
            Dictionary of modprobe configuration options
        """
        options = {}
        
        # Check for modprobe.d directory
        if not self.system.file_exists('/etc/modprobe.d'):
            return options
        
        # List modprobe configuration files
        result = self.system.run_command(['ls', '/etc/modprobe.d/*.conf'])
        if not result.success:
            return options
        
        # Parse each modprobe configuration file
        for file_path in result.stdout.strip().split('\n'):
            if not file_path:
                continue
            
            content = self.system.read_file(file_path)
            if not content:
                continue
            
            # Parse modprobe configuration file
            for line in content.split('\n'):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse options line
                if line.startswith('options '):
                    parts = line.split(' ', 2)
                    if len(parts) >= 3:
                        module = parts[1]
                        module_options = parts[2]
                        
                        # Create KernelConfigOption object
                        option_name = f"MODPROBE_{module.upper()}"
                        options[option_name] = KernelConfigOption(
                            name=option_name,
                            value=module_options,
                            description=f"Modprobe options for {module} module"
                        )
                
                # Parse blacklist line
                elif line.startswith('blacklist '):
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        module = parts[1]
                        
                        # Create KernelConfigOption object
                        option_name = f"MODPROBE_BLACKLIST_{module.upper()}"
                        options[option_name] = KernelConfigOption(
                            name=option_name,
                            value="y",
                            description=f"Blacklist for {module} module"
                        )
        
        return options
    
    def _load_option_descriptions(self) -> None:
        """Load kernel configuration option descriptions."""
        # Try to find kernel documentation
        doc_paths = [
            '/usr/src/linux/Documentation/admin-guide/kernel-parameters.txt',
            '/usr/share/doc/kernel-doc/Documentation/admin-guide/kernel-parameters.txt'
        ]
        
        for path in doc_paths:
            if self.system.file_exists(path):
                content = self.system.read_file(path)
                if content:
                    self._parse_kernel_parameters(content)
                    break
        
        # Try to find Kconfig files
        kconfig_paths = [
            '/usr/src/linux/Kconfig',
            '/usr/src/linux*/Kconfig'
        ]
        
        for path in kconfig_paths:
            if '*' in path:
                # Use glob to find matching files
                result = self.system.run_command(['ls', path])
                if result.success:
                    for kconfig_path in result.stdout.strip().split('\n'):
                        if kconfig_path and self.system.file_exists(kconfig_path):
                            content = self.system.read_file(kconfig_path)
                            if content:
                                self._parse_kconfig(content)
            elif self.system.file_exists(path):
                content = self.system.read_file(path)
                if content:
                    self._parse_kconfig(content)
    
    def _parse_kernel_parameters(self, content: str) -> None:
        """Parse kernel parameters documentation.
        
        Args:
            content: Kernel parameters documentation content
        """
        current_param = None
        current_description = []
        
        for line in content.split('\n'):
            # New parameter
            if not line.startswith(' ') and ':' in line:
                # Save previous parameter
                if current_param and current_description:
                    self.option_descriptions[f"CONFIG_{current_param}"] = ' '.join(current_description)
                
                # Extract new parameter
                parts = line.split(':', 1)
                current_param = parts[0].strip()
                current_description = [parts[1].strip()] if len(parts) > 1 else []
            
            # Continuation of description
            elif line.startswith(' ') and current_param:
                current_description.append(line.strip())
        
        # Save last parameter
        if current_param and current_description:
            self.option_descriptions[f"CONFIG_{current_param}"] = ' '.join(current_description)
    
    def _parse_kconfig(self, content: str) -> None:
        """Parse Kconfig file.
        
        Args:
            content: Kconfig file content
        """
        current_config = None
        current_description = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Config definition
            if line.startswith('config '):
                # Save previous config
                if current_config and current_description:
                    self.option_descriptions[f"CONFIG_{current_config}"] = ' '.join(current_description)
                
                # Extract new config
                current_config = line.split(' ', 1)[1].strip()
                current_description = []
            
            # Help text
            elif line == 'help' or line == '---help---':
                in_help = True
            
            # Description line
            elif current_config and line and not line.startswith('config '):
                current_description.append(line)
        
        # Save last config
        if current_config and current_description:
            self.option_descriptions[f"CONFIG_{current_config}"] = ' '.join(current_description)