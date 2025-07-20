#!/usr/bin/env python3
"""Command Router for Infenix CLI.

This module provides the command routing functionality for the Infenix CLI,
dispatching commands to appropriate handlers.

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
from typing import Dict, Callable, Any

from .hardware import HardwareCommands
from .kernel import KernelCommands
from .logs import LogsCommands
from .diagnostics import DiagnosticsCommands
from .server import ServerCommands
from ..formatters import OutputFormatter
from ..error_handler import CLIErrorHandler


logger = logging.getLogger(__name__)


class CommandRouter:
    """Routes CLI commands to appropriate handlers."""
    
    def __init__(self, formatter: OutputFormatter, error_handler: CLIErrorHandler):
        """Initialize the command router.
        
        Args:
            formatter: Output formatter instance
            error_handler: Error handler instance
        """
        self.formatter = formatter
        self.error_handler = error_handler
        
        # Initialize command handlers
        self.hardware_commands = HardwareCommands(formatter, error_handler)
        self.kernel_commands = KernelCommands(formatter, error_handler)
        self.logs_commands = LogsCommands(formatter, error_handler)
        self.diagnostics_commands = DiagnosticsCommands(formatter, error_handler)
        self.server_commands = ServerCommands(formatter, error_handler)
        
        # Command routing table
        self.command_handlers: Dict[str, Callable[[argparse.Namespace], int]] = {
            'hardware': self.hardware_commands.execute,
            'hw': self.hardware_commands.execute,
            'kernel': self.kernel_commands.execute,
            'logs': self.logs_commands.execute,
            'diagnose': self.diagnostics_commands.execute,
            'diag': self.diagnostics_commands.execute,
            'server': self.server_commands.execute,
        }
    
    def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        from ..error_handler import CLIError, CommandNotFoundError, InvalidArgumentError
        
        command = args.command
        
        if not command:
            self.error_handler.handle_cli_error(
                InvalidArgumentError("No command specified")
            )
            return 1
        
        handler = self.command_handlers.get(command)
        if not handler:
            self.error_handler.handle_cli_error(
                CommandNotFoundError(command)
            )
            return 1
        
        try:
            logger.debug(f"Executing command: {command}")
            return handler(args)
        
        except CLIError as e:
            # Handle known CLI errors
            logger.debug(f"CLI error in command {command}: {e}")
            self.error_handler.handle_cli_error(e)
            return e.exit_code
        
        except KeyboardInterrupt:
            # Re-raise KeyboardInterrupt to be handled at the top level
            raise
        
        except Exception as e:
            logger.exception(f"Unexpected error executing command {command}")
            self.error_handler.handle_exception(e, f"command '{command}'")
            return 1