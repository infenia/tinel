#!/usr/bin/env python3
"""Log Commands for Infenix CLI.

This module provides log analysis command implementations for the Infenix CLI.

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
from ...tools.log_tools import (
    SystemLogsToolProvider,
    LogAnalysisToolProvider,
    LogSummaryToolProvider,
    LogEntryAnalysisToolProvider,
    HardwareLogPatternToolProvider,
    KernelLogPatternToolProvider,
)


logger = logging.getLogger(__name__)


class LogsCommands(BaseCommand):
    """Handler for log analysis commands."""
    
    def __init__(self, formatter, error_handler):
        """Initialize logs commands handler."""
        super().__init__(formatter, error_handler)
        
        # Initialize tool providers
        self.system_logs_tool = SystemLogsToolProvider(self.system)
        self.log_analysis_tool = LogAnalysisToolProvider(self.system)
        self.log_summary_tool = LogSummaryToolProvider(self.system)
        self.log_entry_tool = LogEntryAnalysisToolProvider(self.system)
        self.hardware_pattern_tool = HardwareLogPatternToolProvider(self.system)
        self.kernel_pattern_tool = KernelLogPatternToolProvider(self.system)
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute logs command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        try:
            logs_command = getattr(args, 'logs_command', None)
            
            if not logs_command:
                # Show system logs by default
                return self._show_system_logs(args)
            
            # Route to specific logs command
            command_handlers = {
                'system': self._show_system_logs,
                'hardware': self._show_hardware_logs,
                'kernel': self._show_kernel_logs,
                'summary': self._show_log_summary,
                'analyze': self._analyze_log_file,
            }
            
            handler = command_handlers.get(logs_command)
            if not handler:
                self.error_handler.handle_error(f"Unknown logs command: {logs_command}")
                return 1
            
            return handler(args)
        
        except Exception as e:
            return self._handle_tool_error(e, "logs")
    
    def _show_system_logs(self, args: argparse.Namespace) -> int:
        """Show system logs."""
        try:
            parameters = {
                'lines': getattr(args, 'lines', 100),
                'since': getattr(args, 'since', None),
                'until': getattr(args, 'until', None),
                'source': getattr(args, 'source', 'journald')
            }
            
            result = self._execute_tool(self.system_logs_tool, parameters)
            self.formatter.print_output(result, "System Logs")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "system_logs")
    
    def _show_hardware_logs(self, args: argparse.Namespace) -> int:
        """Show hardware-related logs."""
        try:
            parameters = {
                'lines': getattr(args, 'lines', 100),
                'since': getattr(args, 'since', None),
                'until': getattr(args, 'until', None),
                'component': getattr(args, 'component', None)
            }
            
            result = self._execute_tool(self.hardware_pattern_tool, parameters)
            self.formatter.print_output(result, "Hardware Logs")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "hardware_logs")
    
    def _show_kernel_logs(self, args: argparse.Namespace) -> int:
        """Show kernel logs."""
        try:
            parameters = {
                'lines': getattr(args, 'lines', 100),
                'since': getattr(args, 'since', None),
                'until': getattr(args, 'until', None),
                'errors_only': getattr(args, 'errors_only', False)
            }
            
            result = self._execute_tool(self.kernel_pattern_tool, parameters)
            self.formatter.print_output(result, "Kernel Logs")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "kernel_logs")
    
    def _show_log_summary(self, args: argparse.Namespace) -> int:
        """Show log summary."""
        try:
            parameters = {
                'lines': getattr(args, 'lines', 1000),
                'since': getattr(args, 'since', None),
                'until': getattr(args, 'until', None),
                'critical_only': getattr(args, 'critical_only', False)
            }
            
            result = self._execute_tool(self.log_summary_tool, parameters)
            self.formatter.print_output(result, "Log Summary")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "log_summary")
    
    def _analyze_log_file(self, args: argparse.Namespace) -> int:
        """Analyze specific log file."""
        try:
            file_path = getattr(args, 'file', None)
            if not file_path:
                self.error_handler.handle_error("Log file path is required for analyze command")
                return 1
            
            # Validate file access
            self.error_handler.validate_file_access(file_path, "read")
            
            parameters = {
                'file_path': file_path,
                'show_patterns': getattr(args, 'patterns', False)
            }
            
            result = self._execute_tool(self.log_analysis_tool, parameters)
            self.formatter.print_output(result, f"Log Analysis: {file_path}")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "log_analysis")