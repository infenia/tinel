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
    """Base class for all CLI commands."""

    def __init__(self, formatter: OutputFormatter, error_handler: CLIErrorHandler):
        """Initialize the base command.

        Args:
            formatter: Output formatter instance
            error_handler: Error handler instance
        """
        self.formatter = formatter
        self.error_handler = error_handler
        self.system = LinuxSystemInterface()

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass

    def _handle_tool_error(self, error: Exception, tool_name: str) -> NoReturn:
        """Handle tool execution errors.

        Args:
            error: Exception that occurred
            tool_name: Name of the tool that failed

        Raises:
            Appropriate CLIError based on tool type
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
        """Execute a tool provider with error handling.

        Args:
            tool_provider: Tool provider instance
            parameters: Parameters to pass to the tool

        Returns:
            Tool execution result

        Raises:
            CLIError: If tool execution fails
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
