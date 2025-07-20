#!/usr/bin/env python3
"""Diagnostics Commands for Infenix CLI.

This module provides diagnostics command implementations for the Infenix CLI.

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
from ...tools.diagnostics_tools import (
    SystemDiagnosticsToolProvider,
    QueryProcessorToolProvider,
    RecommendationGeneratorToolProvider,
    HardwareDiagnosticsToolProvider,
)


logger = logging.getLogger(__name__)


class DiagnosticsCommands(BaseCommand):
    """Handler for diagnostics commands."""
    
    def __init__(self, formatter, error_handler):
        """Initialize diagnostics commands handler."""
        super().__init__(formatter, error_handler)
        
        # Initialize tool providers
        self.system_diagnostics_tool = SystemDiagnosticsToolProvider(self.system)
        self.query_processor_tool = QueryProcessorToolProvider(self.system)
        self.recommendations_tool = RecommendationGeneratorToolProvider(self.system)
        self.hardware_diagnostics_tool = HardwareDiagnosticsToolProvider(self.system)
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute diagnostics command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        try:
            diag_command = getattr(args, 'diag_command', None)
            
            if not diag_command:
                # Run system diagnostics by default
                return self._run_system_diagnostics(args)
            
            # Route to specific diagnostics command
            command_handlers = {
                'system': self._run_system_diagnostics,
                'hardware': self._run_hardware_diagnostics,
                'query': self._process_query,
                'recommendations': self._generate_recommendations,
                'rec': self._generate_recommendations,
            }
            
            handler = command_handlers.get(diag_command)
            if not handler:
                self.error_handler.handle_error(f"Unknown diagnostics command: {diag_command}")
                return 1
            
            return handler(args)
        
        except Exception as e:
            return self._handle_tool_error(e, "diagnostics")
    
    def _run_system_diagnostics(self, args: argparse.Namespace) -> int:
        """Run comprehensive system diagnostics."""
        try:
            parameters = {
                'include_hardware': getattr(args, 'include_hardware', True),
                'include_kernel': getattr(args, 'include_kernel', True),
                'include_logs': getattr(args, 'include_logs', True),
                'generate_recommendations': getattr(args, 'recommendations', True),
                'comprehensive': getattr(args, 'comprehensive', False)
            }
            
            self.formatter.print_info("Running comprehensive system diagnostics...")
            result = self._execute_tool(self.system_diagnostics_tool, parameters)
            self.formatter.print_output(result, "System Diagnostics Report")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "system_diagnostics")
    
    def _run_hardware_diagnostics(self, args: argparse.Namespace) -> int:
        """Run hardware-specific diagnostics."""
        try:
            parameters = {
                'components': getattr(args, 'components', ['all']),
                'include_temperature': getattr(args, 'temperature', True),
                'include_performance': getattr(args, 'performance', True),
                'include_health': getattr(args, 'health', True),
                'comprehensive': getattr(args, 'comprehensive', False)
            }
            
            self.formatter.print_info("Running hardware diagnostics...")
            result = self._execute_tool(self.hardware_diagnostics_tool, parameters)
            self.formatter.print_output(result, "Hardware Diagnostics Report")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "hardware_diagnostics")
    
    def _process_query(self, args: argparse.Namespace) -> int:
        """Process natural language query."""
        try:
            query = getattr(args, 'query', None)
            if not query:
                self.error_handler.handle_error("Query is required for query command")
                return 1
            
            parameters = {
                'query': query,
                'include_tool_routing': True,
                'execute_tools': getattr(args, 'execute', False)
            }
            
            self.formatter.print_info(f"Processing query: {query}")
            result = self._execute_tool(self.query_processor_tool, parameters)
            self.formatter.print_output(result, "Query Processing Result")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "query_processing")
    
    def _generate_recommendations(self, args: argparse.Namespace) -> int:
        """Generate system recommendations."""
        try:
            parameters = {
                'focus_areas': getattr(args, 'focus', ['all']),
                'priority_filter': getattr(args, 'priority', ['critical', 'high', 'medium', 'low']),
                'max_recommendations': getattr(args, 'max_recommendations', 20),
                'include_implementation_guides': getattr(args, 'implementation_guides', True)
            }
            
            self.formatter.print_info("Generating system recommendations...")
            result = self._execute_tool(self.recommendations_tool, parameters)
            self.formatter.print_output(result, "System Recommendations")
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "recommendations")