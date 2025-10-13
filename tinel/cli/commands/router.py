#!/usr/bin/env python3
"""
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

"""This module defines the command router for the Tinel CLI.

It includes the `CommandRouter` class, which is responsible for mapping
command-line arguments to the appropriate command handler and executing it.
This provides a centralized and extensible way to manage all the commands
supported by the CLI.
"""

import argparse
import logging
from typing import Callable, Dict

from ..error_handler import (
    CLIError,
    CLIErrorHandler,
    CommandNotFoundError,
    InvalidArgumentError,
)
from ..formatters import OutputFormatter
from .hardware import HardwareCommands

logger = logging.getLogger(__name__)


class CommandRouter:
    """A class for routing CLI commands to their appropriate handlers.

    This class maintains a mapping of command names to handler functions and is
    responsible for executing the correct handler based on the parsed
    command-line arguments.

    Args:
        formatter: An `OutputFormatter` instance to be passed to the command
                   handlers.
        error_handler: A `CLIErrorHandler` instance to be passed to the command
                       handlers.
    """

    def __init__(self, formatter: OutputFormatter, error_handler: CLIErrorHandler):
        """Initializes the CommandRouter.

        Args:
            formatter: An `OutputFormatter` instance.
            error_handler: A `CLIErrorHandler` instance.
        """
        self.formatter = formatter
        self.error_handler = error_handler

        # Initialize command handlers
        self.hardware_commands = HardwareCommands(formatter, error_handler)

        # Command routing table
        self.command_handlers: Dict[str, Callable[[argparse.Namespace], int]] = {
            "hardware": self.hardware_commands.execute,
            "hw": self.hardware_commands.execute,
        }

    def execute_command(self, args: argparse.Namespace) -> int:
        """Executes the command specified in the parsed arguments.

        This method looks up the appropriate handler for the given command and
        executes it, passing along the parsed arguments. It also includes
        comprehensive error handling for both known and unexpected exceptions.

        Args:
            args: The namespace object returned by `ArgumentParser.parse_args()`.

        Returns:
            An integer exit code (0 for success, non-zero for errors).
        """
        # Imports moved to top

        command = args.command

        if not command:
            self.error_handler.handle_cli_error(
                InvalidArgumentError("No command specified")
            )
            return 1

        handler = self.command_handlers.get(command)
        if not handler:
            self.error_handler.handle_cli_error(CommandNotFoundError(command))
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
