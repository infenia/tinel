#!/usr/bin/env python3
"""Server Commands for Infenix CLI.

This module provides server-related command implementations for the Infenix CLI.

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
import asyncio

from .base import BaseCommand


logger = logging.getLogger(__name__)


class ServerCommands(BaseCommand):
    """Handler for server-related commands."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute server command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        try:
            server_command = getattr(args, 'server_command', None)
            
            if not server_command:
                self.error_handler.handle_error("Server command requires a subcommand")
                return 1
            
            # Route to specific server command
            command_handlers = {
                'start': self._start_server,
                'list-tools': self._list_tools,
            }
            
            handler = command_handlers.get(server_command)
            if not handler:
                self.error_handler.handle_error(f"Unknown server command: {server_command}")
                return 1
            
            return handler(args)
        
        except Exception as e:
            return self._handle_tool_error(e, "server")
    
    def _start_server(self, args: argparse.Namespace) -> int:
        """Start the MCP server."""
        try:
            host = getattr(args, 'host', 'localhost')
            port = getattr(args, 'port', 8000)
            debug = getattr(args, 'debug', False)
            
            self.formatter.print_info(f"Starting Infenix MCP server on {host}:{port}")
            
            # Import and run the server
            from ...server import main as server_main
            
            # Run the server
            asyncio.run(server_main())
            
            return 0
        
        except KeyboardInterrupt:
            self.formatter.print_info("Server stopped by user")
            return 0
        except Exception as e:
            return self._handle_tool_error(e, "server_start")
    
    def _list_tools(self, args: argparse.Namespace) -> int:
        """List available MCP tools."""
        try:
            category = getattr(args, 'category', None)
            
            # Import tool providers
            from ...server import tool_providers
            
            tools_info = []
            for provider in tool_providers:
                tool_info = {
                    'name': provider.get_tool_name(),
                    'description': provider.get_tool_description(),
                    'category': self._get_tool_category(provider.get_tool_name())
                }
                
                # Filter by category if specified
                if category and tool_info['category'] != category:
                    continue
                
                tools_info.append(tool_info)
            
            # Sort by category and name
            tools_info.sort(key=lambda x: (x['category'], x['name']))
            
            if category:
                title = f"Available {category.title()} Tools"
            else:
                title = "Available MCP Tools"
            
            # Format as table
            headers = ['Name', 'Category', 'Description']
            table_data = [
                [tool['name'], tool['category'], tool['description']]
                for tool in tools_info
            ]
            
            table_output = self.formatter.format_table(table_data, headers)
            self.formatter.print_output(table_output, title)
            
            return 0
        
        except Exception as e:
            return self._handle_tool_error(e, "list_tools")
    
    def _get_tool_category(self, tool_name: str) -> str:
        """Get the category of a tool based on its name."""
        if any(keyword in tool_name for keyword in ['cpu', 'memory', 'storage', 'pci', 'usb', 'network', 'graphics', 'hardware']):
            return 'hardware'
        elif any(keyword in tool_name for keyword in ['kernel', 'config', 'modules', 'parameters']):
            return 'kernel'
        elif any(keyword in tool_name for keyword in ['log', 'pattern']):
            return 'logs'
        elif any(keyword in tool_name for keyword in ['diagnose', 'query', 'recommendation']):
            return 'diagnostics'
        else:
            return 'other'