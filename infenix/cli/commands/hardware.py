#!/usr/bin/env python3
"""Hardware Commands for Infenix CLI.

This module provides hardware-related command implementations for the Infenix CLI.

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

import argparse
import logging
from typing import Dict, Any

from .base import BaseCommand
from ...tools.hardware_tools import (
    AllHardwareToolProvider,
    CPUInfoToolProvider,
    MemoryInfoToolProvider,
    StorageInfoToolProvider,
    PCIDevicesToolProvider,
    USBDevicesToolProvider,
    NetworkInfoToolProvider,
    GraphicsInfoToolProvider,
)


logger = logging.getLogger(__name__)


class HardwareCommands(BaseCommand):
    """Handler for hardware-related commands."""
    
    def __init__(self, formatter, error_handler):
        """Initialize hardware commands handler."""
        super().__init__(formatter, error_handler)
        
        # Initialize tool providers
        self.all_hardware_tool = AllHardwareToolProvider(self.system)
        self.cpu_tool = CPUInfoToolProvider(self.system)
        self.memory_tool = MemoryInfoToolProvider(self.system)
        self.storage_tool = StorageInfoToolProvider(self.system)
        self.pci_tool = PCIDevicesToolProvider(self.system)
        self.usb_tool = USBDevicesToolProvider(self.system)
        self.network_tool = NetworkInfoToolProvider(self.system)
        self.graphics_tool = GraphicsInfoToolProvider(self.system)
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute hardware command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        try:
            hardware_command = getattr(args, 'hardware_command', None)
            
            if not hardware_command:
                # Show all hardware information
                return self._show_all_hardware(args)
            
            # Route to specific hardware command
            command_handlers = {
                'cpu': self._show_cpu_info,
                'memory': self._show_memory_info,
                'mem': self._show_memory_info,
                'storage': self._show_storage_info,
                'disk': self._show_storage_info,
                'network': self._show_network_info,
                'net': self._show_network_info,
                'graphics': self._show_graphics_info,
                'gpu': self._show_graphics_info,
                'pci': self._show_pci_devices,
                'usb': self._show_usb_devices,
                'all': self._show_all_hardware,
            }
            
            handler = command_handlers.get(hardware_command)
            if not handler:
                self.error_handler.handle_error(f"Unknown hardware command: {hardware_command}")
                return 1
            
            return handler(args)
        
        except Exception as e:
            return self._handle_tool_error(e, "hardware")
    
    def _show_all_hardware(self, args: argparse.Namespace) -> int:
        """Show all hardware information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'summary': getattr(args, 'summary', False)
            }
            
            result = self._execute_tool(self.all_hardware_tool, parameters)
            
            title = "Hardware Information Summary" if parameters.get('summary') else "Complete Hardware Information"
            self.formatter.print_output(result, title)
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "all_hardware")
    
    def _show_cpu_info(self, args: argparse.Namespace) -> int:
        """Show CPU information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'include_temperature': getattr(args, 'temperature', False),
                'include_features': getattr(args, 'features', False)
            }
            
            result = self._execute_tool(self.cpu_tool, parameters)
            self.formatter.print_output(result, "CPU Information")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "cpu_info")
    
    def _show_memory_info(self, args: argparse.Namespace) -> int:
        """Show memory information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'include_usage': getattr(args, 'usage', False),
                'include_timing': getattr(args, 'timing', False)
            }
            
            result = self._execute_tool(self.memory_tool, parameters)
            self.formatter.print_output(result, "Memory Information")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "memory_info")
    
    def _show_storage_info(self, args: argparse.Namespace) -> int:
        """Show storage information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'include_health': getattr(args, 'health', False),
                'include_performance': getattr(args, 'performance', False)
            }
            
            result = self._execute_tool(self.storage_tool, parameters)
            self.formatter.print_output(result, "Storage Information")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "storage_info")
    
    def _show_network_info(self, args: argparse.Namespace) -> int:
        """Show network information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'include_interfaces': getattr(args, 'interfaces', False)
            }
            
            result = self._execute_tool(self.network_tool, parameters)
            self.formatter.print_output(result, "Network Information")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "network_info")
    
    def _show_graphics_info(self, args: argparse.Namespace) -> int:
        """Show graphics information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'include_drivers': getattr(args, 'drivers', False)
            }
            
            result = self._execute_tool(self.graphics_tool, parameters)
            self.formatter.print_output(result, "Graphics Information")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "graphics_info")
    
    def _show_pci_devices(self, args: argparse.Namespace) -> int:
        """Show PCI devices information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'tree_format': getattr(args, 'tree', False)
            }
            
            result = self._execute_tool(self.pci_tool, parameters)
            self.formatter.print_output(result, "PCI Devices")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "pci_devices")
    
    def _show_usb_devices(self, args: argparse.Namespace) -> int:
        """Show USB devices information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'tree_format': getattr(args, 'tree', False)
            }
            
            result = self._execute_tool(self.usb_tool, parameters)
            self.formatter.print_output(result, "USB Devices")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "usb_devices")