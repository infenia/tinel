#!/usr/bin/env python3
"""Kernel Commands for Infenix CLI.

This module provides kernel-related command implementations for the Infenix CLI.

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

from .base import BaseCommand
from ...tools.kernel_tools import (
    KernelInfoToolProvider,
    KernelConfigToolProvider,
    KernelConfigAnalysisToolProvider,
    KernelModulesToolProvider,
    KernelParametersToolProvider,
)


logger = logging.getLogger(__name__)


class KernelCommands(BaseCommand):
    """Handler for kernel-related commands."""
    
    def __init__(self, formatter, error_handler):
        """Initialize kernel commands handler."""
        super().__init__(formatter, error_handler)
        
        # Initialize tool providers
        self.kernel_info_tool = KernelInfoToolProvider(self.system)
        self.kernel_config_tool = KernelConfigToolProvider(self.system)
        self.kernel_analysis_tool = KernelConfigAnalysisToolProvider(self.system)
        self.kernel_modules_tool = KernelModulesToolProvider(self.system)
        self.kernel_params_tool = KernelParametersToolProvider(self.system)
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute kernel command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        try:
            kernel_command = getattr(args, 'kernel_command', None)
            
            if not kernel_command:
                # Show basic kernel information
                return self._show_kernel_info(args)
            
            # Route to specific kernel command
            command_handlers = {
                'info': self._show_kernel_info,
                'config': self._show_kernel_config,
                'modules': self._show_kernel_modules,
                'parameters': self._show_kernel_parameters,
                'params': self._show_kernel_parameters,
            }
            
            handler = command_handlers.get(kernel_command)
            if not handler:
                self.error_handler.handle_error(f"Unknown kernel command: {kernel_command}")
                return 1
            
            return handler(args)
        
        except Exception as e:
            return self._handle_tool_error(e, "kernel")
    
    def _show_kernel_info(self, args: argparse.Namespace) -> int:
        """Show kernel information."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False)
            }
            
            result = self._execute_tool(self.kernel_info_tool, parameters)
            self.formatter.print_output(result, "Kernel Information")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "kernel_info")
    
    def _show_kernel_config(self, args: argparse.Namespace) -> int:
        """Show kernel configuration."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'analyze': getattr(args, 'analyze', False),
                'recommendations': getattr(args, 'recommendations', False),
                'option': getattr(args, 'option', None)
            }
            
            if parameters['analyze'] or parameters['recommendations']:
                result = self._execute_tool(self.kernel_analysis_tool, parameters)
                title = "Kernel Configuration Analysis"
            else:
                result = self._execute_tool(self.kernel_config_tool, parameters)
                title = "Kernel Configuration"
            
            self.formatter.print_output(result, title)
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "kernel_config")
    
    def _show_kernel_modules(self, args: argparse.Namespace) -> int:
        """Show kernel modules."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'loaded_only': getattr(args, 'loaded', False),
                'available_only': getattr(args, 'available', False)
            }
            
            result = self._execute_tool(self.kernel_modules_tool, parameters)
            self.formatter.print_output(result, "Kernel Modules")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "kernel_modules")
    
    def _show_kernel_parameters(self, args: argparse.Namespace) -> int:
        """Show kernel parameters."""
        try:
            parameters = {
                'detailed': getattr(args, 'detailed', False),
                'parameter': getattr(args, 'parameter', None)
            }
            
            result = self._execute_tool(self.kernel_params_tool, parameters)
            self.formatter.print_output(result, "Kernel Parameters")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "kernel_parameters")