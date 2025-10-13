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

"""This module defines the base class for all CLI commands.

It includes the `BaseCommand` abstract base class, which provides a common
framework and shared functionality for all command handlers. This ensures a
consistent structure and simplifies the implementation of new commands.
"""

import argparse
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, NoReturn

from ...system import LinuxSystemInterface
from ..error_handler import (
    CLIError,
    CLIErrorHandler,
    DiagnosticsError,
    HardwareError,
    KernelError,
    LogAnalysisError,
)
from ..formatters import OutputFormatter

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    """An abstract base class for all CLI commands.

    This class provides a common interface and shared functionality for all
    command handlers, such as access to the output formatter and error
    handler.

    Args:
        formatter: An `OutputFormatter` instance for displaying output.
        error_handler: A `CLIErrorHandler` instance for managing errors.
    """

    def __init__(self, formatter: OutputFormatter, error_handler: CLIErrorHandler):
        """Initializes the BaseCommand.

        Args:
            formatter: An `OutputFormatter` instance.
            error_handler: A `CLIErrorHandler` instance.
        """
        self.formatter = formatter
        self.error_handler = error_handler
        self.system = LinuxSystemInterface()

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Executes the command.

        This is an abstract method that must be implemented by all subclasses.
        It contains the core logic for the command.

        Args:
            args: The parsed command-line arguments.

        Returns:
            An integer exit code (0 for success, non-zero for errors).
        """
        pass

    def _handle_tool_error(self, error: Exception, tool_name: str) -> NoReturn:
        """Handles errors that occur during the execution of a tool.

        This method maps the tool name to an appropriate `CLIError` type and
        raises it, ensuring that tool-related errors are handled consistently.

        Args:
            error: The exception that occurred.
            tool_name: The name of the tool that failed.

        Raises:
            CLIError: An appropriate subclass of `CLIError` based on the
                      tool's category.
        """
        # Imports moved to top

        logger.exception(f"Tool {tool_name} failed")

        # If it's already a CLIError, re-raise it
        if isinstance(error, CLIError):
            raise error

        # Map tool names to appropriate error types using a more maintainable approach
        error_mapping = {
            "hardware": (
                [
                    "cpu",
                    "memory",
                    "storage",
                    "pci",
                    "usb",
                    "network",
                    "graphics",
                    "hardware",
                ],
                HardwareError,
            ),
            "kernel": (["kernel", "config"], KernelError),
            "logs": (["log", "syslog", "journal"], LogAnalysisError),
            "diagnostics": (["diagnose", "diagnostic"], DiagnosticsError),
        }

        tool_name_lower = tool_name.lower()

        for error_type, (keywords, error_class) in error_mapping.items():
            if any(keyword in tool_name_lower for keyword in keywords):
                # Use consistent error message format
                if error_type == "logs":
                    error_msg = "Log analysis failed"
                else:
                    error_msg = f"{error_type.title()} analysis failed"
                raise error_class(f"{error_msg}: {error}", tool_name)

        # Default case
        raise CLIError(f"Tool '{tool_name}' execution failed: {error}")

    def _execute_tool(
        self, tool_provider: Any, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes a tool provider with standardized error handling.

        This method provides a consistent way to execute tool providers,
        catching any exceptions and delegating them to `_handle_tool_error`.

        Args:
            tool_provider: The tool provider instance to be executed.
            parameters: The parameters to be passed to the tool.

        Returns:
            A dictionary containing the result of the tool's execution.

        Raises:
            CLIError: If the tool execution fails.
        """
        try:
            self.formatter.print_debug(
                f"Executing tool: {tool_provider.get_tool_name()}"
            )
            result = tool_provider.execute(parameters)

            if not result.get("success", True):
                error_msg = result.get("error", "Unknown error")
                raise RuntimeError(error_msg)

            return result  # type: ignore[no-any-return]

        except Exception as error:
            self._handle_tool_error(error, tool_provider.get_tool_name())
            # This should never be reached due to _handle_tool_error raising/exiting
            return {}
