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


import logging
import os
import sys
from enum import IntEnum
from typing import Optional, Dict, Any

from .formatters import OutputFormatter


logger = logging.getLogger(__name__)


class ExitCode(IntEnum):
    """Standard exit codes for the CLI."""

    SUCCESS = 0
    GENERAL_ERROR = 1
    MISUSE_OF_SHELL_BUILTINS = 2
    COMMAND_NOT_FOUND = 127
    INVALID_ARGUMENT = 128
    KEYBOARD_INTERRUPT = 130

    # Custom exit codes for Tinel
    PERMISSION_DENIED = 10
    FILE_NOT_FOUND = 11
    NETWORK_ERROR = 12
    CONFIGURATION_ERROR = 13
    HARDWARE_ERROR = 14
    KERNEL_ERROR = 15
    LOG_ANALYSIS_ERROR = 16
    DIAGNOSTICS_ERROR = 17


class CLIError(Exception):
    """Base exception for CLI errors."""

    def __init__(
        self,
        message: str,
        exit_code: int = ExitCode.GENERAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize CLI error.

        Args:
            message: Error message
            exit_code: Exit code to use
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.details = details or {}


class CommandNotFoundError(CLIError):
    """Raised when a command is not found."""

    def __init__(self, command: str):
        super().__init__(
            f"Command '{command}' not found",
            ExitCode.COMMAND_NOT_FOUND,
            {"command": command},
        )


class InvalidArgumentError(CLIError):
    """Raised when invalid arguments are provided."""

    def __init__(self, message: str, argument: Optional[str] = None):
        super().__init__(
            message,
            ExitCode.INVALID_ARGUMENT,
            {"argument": argument} if argument else {},
        )


class PermissionError(CLIError):
    """Raised when permission is denied."""

    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(
            message,
            ExitCode.PERMISSION_DENIED,
            {"resource": resource} if resource else {},
        )


class FileNotFoundError(CLIError):
    """Raised when a required file is not found."""

    def __init__(self, file_path: str):
        super().__init__(
            f"File not found: {file_path}",
            ExitCode.FILE_NOT_FOUND,
            {"file_path": file_path},
        )


class NetworkError(CLIError):
    """Raised when network operations fail."""

    def __init__(self, message: str, endpoint: Optional[str] = None):
        super().__init__(
            message, ExitCode.NETWORK_ERROR, {"endpoint": endpoint} if endpoint else {}
        )


class ConfigurationError(CLIError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message,
            ExitCode.CONFIGURATION_ERROR,
            {"config_key": config_key} if config_key else {},
        )


class HardwareError(CLIError):
    """Raised when hardware operations fail."""

    def __init__(self, message: str, component: Optional[str] = None):
        super().__init__(
            message,
            ExitCode.HARDWARE_ERROR,
            {"component": component} if component else {},
        )


class KernelError(CLIError):
    """Raised when kernel operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message,
            ExitCode.KERNEL_ERROR,
            {"operation": operation} if operation else {},
        )


class LogAnalysisError(CLIError):
    """Raised when log analysis fails."""

    def __init__(self, message: str, log_source: Optional[str] = None):
        super().__init__(
            message,
            ExitCode.LOG_ANALYSIS_ERROR,
            {"log_source": log_source} if log_source else {},
        )


class DiagnosticsError(CLIError):
    """Raised when diagnostics operations fail."""

    def __init__(self, message: str, diagnostic_type: Optional[str] = None):
        super().__init__(
            message,
            ExitCode.DIAGNOSTICS_ERROR,
            {"diagnostic_type": diagnostic_type} if diagnostic_type else {},
        )


class CLIErrorHandler:
    """Handles CLI errors with appropriate formatting and exit codes."""

    def __init__(self, formatter: OutputFormatter):
        """Initialize the error handler.

        Args:
            formatter: Output formatter instance
        """
        self.formatter = formatter
        self.error_suggestions = {
            ExitCode.COMMAND_NOT_FOUND: "Use 'tinel --help' to see available commands",
            ExitCode.INVALID_ARGUMENT: "Check command syntax with 'tinel <command> --help'",
            ExitCode.PERMISSION_DENIED: "Try running with elevated privileges (sudo)",
            ExitCode.FILE_NOT_FOUND: "Verify the file path and permissions",
            ExitCode.NETWORK_ERROR: "Check network connectivity and server status",
            ExitCode.CONFIGURATION_ERROR: "Review configuration file syntax and values",
            ExitCode.HARDWARE_ERROR: "Check hardware connectivity and system logs",
            ExitCode.KERNEL_ERROR: "Review kernel configuration and system state",
            ExitCode.LOG_ANALYSIS_ERROR: "Verify log file accessibility and format",
            ExitCode.DIAGNOSTICS_ERROR: "Check system state and try again",
        }

    def handle_error(
        self,
        error: str,
        exit_code: int = ExitCode.GENERAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Handle an error with appropriate formatting and exit.

        Args:
            error: Error message
            exit_code: Exit code to use
            details: Additional error details
            suggestion: Optional suggestion for fixing the error
        """
        # Log the error
        logger.error(f"CLI Error: {error}")
        if details:
            logger.debug(f"Error details: {details}")

        # Print error message
        self.formatter.print_error(error)

        # Print details if in verbose mode
        if details and self.formatter.verbose > 0:
            self.formatter.print_debug(f"Details: {details}")

        # Print suggestion
        if suggestion:
            print(f"Suggestion: {suggestion}", file=sys.stderr)
        elif exit_code in self.error_suggestions:
            print(f"Suggestion: {self.error_suggestions[exit_code]}", file=sys.stderr)

        # Save error report for debugging if this is an unexpected error
        if exit_code == ExitCode.GENERAL_ERROR and details:
            try:
                error_report_path = self.save_error_report(RuntimeError(error), details)
                if error_report_path:
                    print(
                        f"Error report saved to: {error_report_path}", file=sys.stderr
                    )
            except Exception:
                # Don't let error reporting itself cause issues
                pass

        # Exit with appropriate code
        sys.exit(exit_code)

    def handle_cli_error(self, error: CLIError) -> None:
        """Handle a CLIError instance.

        Args:
            error: CLIError instance
        """
        self.handle_error(error.message, error.exit_code, error.details)

    def handle_exception(
        self, exception: Exception, context: Optional[str] = None
    ) -> None:
        """Handle an unexpected exception.

        Args:
            exception: Exception that occurred
            context: Optional context information
        """
        error_msg = f"Unexpected error: {exception}"
        if context:
            error_msg = f"{context}: {error_msg}"

        logger.exception("Unexpected exception occurred")

        self.handle_error(
            error_msg,
            ExitCode.GENERAL_ERROR,
            {"exception_type": type(exception).__name__, "context": context},
            "This appears to be an internal error. Please report this issue.",
        )

    def validate_file_access(self, file_path: str, operation: str = "read") -> None:
        """Validate file access and raise appropriate error if not accessible.

        Args:
            file_path: Path to the file
            operation: Type of operation (read, write, execute)

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If permission is denied
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        if operation == "read" and not os.access(file_path, os.R_OK):
            raise PermissionError(
                f"Permission denied reading file: {file_path}", file_path
            )
        elif operation == "write" and not os.access(file_path, os.W_OK):
            raise PermissionError(
                f"Permission denied writing file: {file_path}", file_path
            )
        elif operation == "execute" and not os.access(file_path, os.X_OK):
            raise PermissionError(
                f"Permission denied executing file: {file_path}", file_path
            )

    def validate_command_availability(self, command: str) -> None:
        """Validate that a system command is available.

        Args:
            command: Command to check

        Raises:
            CommandNotFoundError: If command is not found
        """
        import shutil

        if not shutil.which(command):
            raise CommandNotFoundError(command)

    def validate_network_connectivity(
        self, host: str, port: int, timeout: int = 5
    ) -> None:
        """Validate network connectivity to a host.

        Args:
            host: Hostname or IP address
            port: Port number
            timeout: Connection timeout in seconds

        Raises:
            NetworkError: If connection fails
        """
        import socket

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result != 0:
                raise NetworkError(f"Cannot connect to {host}:{port}", f"{host}:{port}")

        except socket.gaierror as e:
            raise NetworkError(f"DNS resolution failed for {host}: {e}", host)
        except Exception as e:
            raise NetworkError(
                f"Network error connecting to {host}:{port}: {e}", f"{host}:{port}"
            )

    def create_error_report(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a detailed error report for debugging.

        Args:
            error: Exception that occurred
            context: Additional context information

        Returns:
            Dictionary containing error report
        """
        import traceback
        import platform
        import sys
        from datetime import datetime

        report = {
            "timestamp": datetime.now().isoformat(),
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            },
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "tinel_version": "0.1.0",  # This should be imported from version module
            },
            "context": context or {},
        }

        return report

    def save_error_report(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save an error report to a file for debugging.

        Args:
            error: Exception that occurred
            context: Additional context information

        Returns:
            Path to the saved error report file
        """
        import json
        import tempfile
        import os
        from datetime import datetime

        report = self.create_error_report(error, context)

        # Create error report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tinel_error_{timestamp}.json"

        # Try to save in user's temp directory
        try:
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)

            with open(filepath, "w") as f:
                json.dump(report, f, indent=2)

            return filepath

        except Exception as e:
            logger.warning(f"Failed to save error report: {e}")
            return ""

    def validate_system_requirements(self) -> None:
        """Validate system requirements and raise appropriate errors.

        Raises:
            ConfigurationError: If system requirements are not met
        """
        import platform
        import sys

        # Check Python version
        if sys.version_info < (3, 11):
            raise ConfigurationError(
                f"Python 3.11+ required, found {sys.version_info[0]}.{sys.version_info[1]}",
                "python_version",
            )

        # Check if running on Linux
        if platform.system() != "Linux":
            raise ConfigurationError(
                f"Tinel requires Linux, found {platform.system()}", "operating_system"
            )

        # Check for required system utilities
        required_commands = ["lscpu", "lspci", "lsusb", "lsblk", "df", "ip"]
        missing_commands = []

        for cmd in required_commands:
            try:
                self.validate_command_availability(cmd)
            except CommandNotFoundError:
                missing_commands.append(cmd)

        if missing_commands:
            raise ConfigurationError(
                f"Required system utilities not found: {', '.join(missing_commands)}",
                "system_utilities",
            )

    def handle_permission_escalation(self, operation: str, resource: str) -> None:
        """Handle permission escalation requests.

        Args:
            operation: Operation that requires elevated privileges
            resource: Resource that requires access

        Raises:
            PermissionError: If permission cannot be granted
        """
        raise PermissionError(
            f"Permission denied for {operation} on {resource}. "
            f"This operation requires elevated privileges. "
            f"Try running with elevated privileges: sudo tinel {operation}",
            resource,
        )

    def validate_cli_arguments(self, args: Any) -> None:
        """Validate CLI arguments and raise appropriate errors.

        Args:
            args: Parsed command line arguments

        Raises:
            InvalidArgumentError: If arguments are invalid
            ConfigurationError: If configuration is invalid
        """
        # Check for conflicting options first
        if (
            hasattr(args, "quiet")
            and hasattr(args, "verbose")
            and isinstance(args.quiet, bool)
            and isinstance(args.verbose, int)
            and args.quiet
            and args.verbose > 0
        ):
            raise InvalidArgumentError(
                "Cannot use both --quiet and --verbose options together"
            )

        # Validate verbosity level
        if (
            hasattr(args, "verbose")
            and isinstance(args.verbose, int)
            and args.verbose < 0
        ):
            raise InvalidArgumentError("Verbosity level cannot be negative", "verbose")

        # Validate output format (only if it's a real string, not a Mock)
        valid_formats = ["text", "json", "yaml", "csv"]
        if (
            hasattr(args, "format")
            and isinstance(args.format, str)
            and args.format not in valid_formats
        ):
            raise InvalidArgumentError(
                f"Invalid output format '{args.format}'. Valid formats: {', '.join(valid_formats)}",
                "format",
            )

    def get_error_context(self) -> Dict[str, Any]:
        """Get current system context for error reporting.

        Returns:
            Dictionary containing system context information
        """
        import os
        import pwd
        import platform
        import sys
        from datetime import datetime

        try:
            context = {
                "timestamp": datetime.now().isoformat(),
                "user": pwd.getpwuid(os.getuid()).pw_name,
                "working_directory": os.getcwd(),
                "environment": {
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", ""),
                    "USER": os.environ.get("USER", ""),
                    "SHELL": os.environ.get("SHELL", ""),
                },
                "system": {
                    "platform": platform.platform(),
                    "python_version": sys.version,
                    "python_executable": sys.executable,
                },
            }
        except Exception:
            # Fallback context if we can't get full information
            context = {
                "timestamp": datetime.now().isoformat(),
                "error": "Could not gather full system context",
            }

        return context

    def format_error_for_user(
        self, error: Exception, context: Optional[str] = None
    ) -> str:
        """Format an error message for user-friendly display.

        Args:
            error: Exception that occurred
            context: Optional context information

        Returns:
            Formatted error message
        """
        error_type = type(error).__name__
        error_message = str(error)

        if context:
            return f"{context}: {error_type}: {error_message}"
        else:
            return f"{error_type}: {error_message}"
