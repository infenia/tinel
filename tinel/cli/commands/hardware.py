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
from typing import Any

from ...tools.hardware_tools import (
    AllHardwareToolProvider,
    CPUInfoToolProvider,
)
from .base import BaseCommand

logger = logging.getLogger(__name__)


class HardwareCommands(BaseCommand):
    """Handler for hardware-related commands."""

    def __init__(self, formatter: Any, error_handler: Any):
        """Initialize hardware commands handler."""
        super().__init__(formatter, error_handler)

        # Initialize tool providers
        self.all_hardware_tool = AllHardwareToolProvider(self.system)
        self.cpu_tool = CPUInfoToolProvider(self.system)

    def execute(self, args: argparse.Namespace) -> int:
        """Execute hardware command.

        Args:
            args: Parsed command line arguments

        Returns:
            Exit code
        """
        try:
            hardware_command = getattr(args, "hardware_command", None)

            if not hardware_command:
                # Show all hardware information
                return self._show_all_hardware(args)

            # Route to specific hardware command
            command_handlers = {
                "cpu": self._show_cpu_info,
                "all": self._show_all_hardware,
            }

            handler = command_handlers.get(hardware_command)
            if not handler:
                self.error_handler.handle_error(
                    f"Unknown hardware command: {hardware_command}"
                )
                return 1

            return handler(args)

        except Exception as e:
            self._handle_tool_error(e, "hardware")
            return 1  # This should never be reached

    def _show_all_hardware(self, args: argparse.Namespace) -> int:
        """Show all hardware information."""
        try:
            parameters = {
                "detailed": getattr(args, "detailed", False),
                "summary": getattr(args, "summary", False),
            }

            result = self._execute_tool(self.all_hardware_tool, parameters)

            title = (
                "Hardware Information Summary"
                if parameters.get("summary")
                else "Complete Hardware Information"
            )
            self.formatter.print_output(result, title)

            return 0

        except Exception as e:
            self._handle_tool_error(e, "all_hardware")
            return 1  # This should never be reached

    def _show_cpu_info(self, args: argparse.Namespace) -> int:
        """Show CPU information."""
        try:
            parameters = {
                "detailed": getattr(args, "detailed", False),
                "include_temperature": getattr(args, "temperature", False),
                "include_features": getattr(args, "features", False),
            }

            result = self._execute_tool(self.cpu_tool, parameters)
            self.formatter.print_output(result, "CPU Information")

            return 0

        except Exception as e:
            self._handle_tool_error(e, "cpu_info")
            return 1  # This should never be reached
