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

import json
import logging
import os
import platform
import pwd
import shutil
import socket
import sys
import tempfile
import traceback
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, Optional

from .formatters import OutputFormatter

"""This module provides a comprehensive error handling system for the Tinel CLI.

It defines custom exception classes for various error scenarios, an `ExitCode`
enum for standardized exit codes, and a `CLIErrorHandler` class to manage
error reporting, formatting, and graceful termination of the application. The
error handler is designed to provide informative feedback to the user and
generate detailed reports for debugging.
"""

logger = logging.getLogger(__name__)


class ExitCode(IntEnum):
    """Defines standard and custom exit codes for the Tinel CLI.

    This enumeration provides a set of standardized exit codes to be used
    throughout the application, ensuring consistent and meaningful termination
    statuses. It includes both common POSIX exit codes and custom codes
    specific to Tinel's functionality.
    """

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
    """A base exception class for all custom CLI errors in Tinel.

    This class provides a foundation for creating more specific error types.
    It encapsulates an error message, an exit code, and optional details,
    ensuring that all custom errors have a consistent structure.

    Args:
        message: The error message to be displayed to the user.
        exit_code: The exit code to be used when the application terminates.
        details: An optional dictionary of additional details for debugging.
    """

    def __init__(
        self,
        message: str,
        exit_code: int = ExitCode.GENERAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initializes the CLIError.

        Args:
            message: The error message.
            exit_code: The exit code.
            details: Additional details about the error.
        """
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.details = details or {}


class CommandNotFoundError(CLIError):
    """An exception raised when a specified command is not found."""

    def __init__(self, command: str):
        """Initializes the CommandNotFoundError.

        Args:
            command: The name of the command that was not found.
        """
        super().__init__(
            f"Command '{command}' not found",
            ExitCode.COMMAND_NOT_FOUND,
            {"command": command},
        )


class InvalidArgumentError(CLIError):
    """An exception raised when an invalid argument is provided to a command."""

    def __init__(self, message: str, argument: Optional[str] = None):
        """Initializes the InvalidArgumentError.

        Args:
            message: The error message to display.
            argument: The name of the invalid argument, if applicable.
        """
        super().__init__(
            message,
            ExitCode.INVALID_ARGUMENT,
            {"argument": argument} if argument else {},
        )


class PermissionError(CLIError):
    """An exception raised when a required permission is not granted."""

    def __init__(self, message: str, resource: Optional[str] = None):
        """Initializes the PermissionError.

        Args:
            message: The error message to display.
            resource: The resource for which permission was denied.
        """
        super().__init__(
            message,
            ExitCode.PERMISSION_DENIED,
            {"resource": resource} if resource else {},
        )


class FileNotFoundError(CLIError):
    """An exception raised when a required file is not found."""

    def __init__(self, file_path: str):
        """Initializes the FileNotFoundError.

        Args:
            file_path: The path to the file that was not found.
        """
        super().__init__(
            f"File not found: {file_path}",
            ExitCode.FILE_NOT_FOUND,
            {"file_path": file_path},
        )


class NetworkError(CLIError):
    """An exception raised when a network operation fails."""

    def __init__(self, message: str, endpoint: Optional[str] = None):
        """Initializes the NetworkError.

        Args:
            message: The error message to display.
            endpoint: The network endpoint that was being accessed.
        """
        super().__init__(
            message, ExitCode.NETWORK_ERROR, {"endpoint": endpoint} if endpoint else {}
        )


class ConfigurationError(CLIError):
    """An exception raised when there is a configuration error."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        """Initializes the ConfigurationError.

        Args:
            message: The error message to display.
            config_key: The configuration key that caused the error.
        """
        super().__init__(
            message,
            ExitCode.CONFIGURATION_ERROR,
            {"config_key": config_key} if config_key else {},
        )


class HardwareError(CLIError):
    """An exception raised when a hardware-related operation fails."""

    def __init__(self, message: str, component: Optional[str] = None):
        """Initializes the HardwareError.

        Args:
            message: The error message to display.
            component: The hardware component that caused the error.
        """
        super().__init__(
            message,
            ExitCode.HARDWARE_ERROR,
            {"component": component} if component else {},
        )


class KernelError(CLIError):
    """An exception raised when a kernel-related operation fails."""

    def __init__(self, message: str, operation: Optional[str] = None):
        """Initializes the KernelError.

        Args:
            message: The error message to display.
            operation: The kernel operation that failed.
        """
        super().__init__(
            message,
            ExitCode.KERNEL_ERROR,
            {"operation": operation} if operation else {},
        )


class LogAnalysisError(CLIError):
    """An exception raised when log analysis fails."""

    def __init__(self, message: str, log_source: Optional[str] = None):
        """Initializes the LogAnalysisError.

        Args:
            message: The error message to display.
            log_source: The source of the log that was being analyzed.
        """
        super().__init__(
            message,
            ExitCode.LOG_ANALYSIS_ERROR,
            {"log_source": log_source} if log_source else {},
        )


class DiagnosticsError(CLIError):
    """An exception raised when a diagnostics operation fails."""

    def __init__(self, message: str, diagnostic_type: Optional[str] = None):
        """Initializes the DiagnosticsError.

        Args:
            message: The error message to display.
            diagnostic_type: The type of diagnostic that failed.
        """
        super().__init__(
            message,
            ExitCode.DIAGNOSTICS_ERROR,
            {"diagnostic_type": diagnostic_type} if diagnostic_type else {},
        )


class CLIErrorHandler:
    """A class for handling and reporting CLI errors.

    This class provides a centralized mechanism for managing exceptions and
    errors that occur during the execution of the CLI. It is responsible for
    formatting error messages, providing helpful suggestions, logging errors,
    and terminating the application with an appropriate exit code.

    Args:
        formatter: An `OutputFormatter` instance for printing formatted
                   messages.
    """

    def __init__(self, formatter: OutputFormatter):
        """Initializes the CLIErrorHandler.

        Args:
            formatter: An `OutputFormatter` instance to be used for displaying
                       error messages.
        """
        self.formatter = formatter
        self.error_suggestions = {
            ExitCode.COMMAND_NOT_FOUND: "Use 'tinel --help' to see available commands",
            ExitCode.INVALID_ARGUMENT: (
                "Check command syntax with 'tinel <command> --help'"
            ),
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
        """Handles a generic error, formats it, and terminates the application.

        This method is the core of the error handling process. It logs the
        error, prints a formatted message to the user, provides a helpful
        suggestion, and, in the case of unexpected errors, saves a detailed
        error report for debugging.

        Args:
            error: The error message to be displayed.
            exit_code: The exit code to be used for termination.
            details: An optional dictionary of additional details for debugging.
            suggestion: An optional suggestion to help the user resolve the
                        error.
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
        elif ExitCode(exit_code) in self.error_suggestions:
            print(
                f"Suggestion: {self.error_suggestions[ExitCode(exit_code)]}",
                file=sys.stderr,
            )

        # Save error report for debugging if this is an unexpected error
        if exit_code == ExitCode.GENERAL_ERROR and details:
            try:
                error_report_path = self.save_error_report(RuntimeError(error), details)
                if error_report_path:
                    print(
                        f"Error report saved to: {error_report_path}", file=sys.stderr
                    )
            except Exception as e:
                # Don't let error reporting itself cause issues
                logger.exception("An unexpected error occurred during error reporting: %s", e)

        # Exit with appropriate code
        sys.exit(exit_code)

    def handle_cli_error(self, error: CLIError) -> None:
        """Handles a `CLIError` instance by delegating to `handle_error`.

        This is a convenience method for handling instances of the `CLIError`
        base class and its subclasses.

        Args:
            error: The `CLIError` instance to be handled.
        """
        self.handle_error(error.message, error.exit_code, error.details)

    def handle_exception(
        self, exception: Exception, context: Optional[str] = None
    ) -> None:
        """Handles an unexpected exception.

        This method is designed to catch and process any exceptions that are
        not explicitly handled as `CLIError` instances. It logs the exception
        and provides a generic error message to the user.

        Args:
            exception: The unexpected exception that occurred.
            context: Optional context information about where the error
                     occurred.
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
        """Validates access to a file.

        This method checks for the existence of a file and whether the current
        user has the necessary permissions to perform the specified operation
        (read, write, or execute).

        Args:
            file_path: The path to the file to be validated.
            operation: The type of operation to be checked ('read', 'write',
                       or 'execute').

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the required permission is not granted.
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
        """Validates the availability of a system command.

        This method checks if a given command is present in the system's PATH
        and executable.

        Args:
            command: The name of the command to be checked.

        Raises:
            CommandNotFoundError: If the command is not found in the system's
                                  PATH.
        """
        # Import moved to top

        if not shutil.which(command):
            raise CommandNotFoundError(command)

    def validate_network_connectivity(
        self, host: str, port: int, timeout: int = 5
    ) -> None:
        """Validates network connectivity to a specified host and port.

        This method attempts to establish a TCP connection to the given host
        and port to verify network reachability.

        Args:
            host: The hostname or IP address to connect to.
            port: The port number to connect to.
            timeout: The connection timeout in seconds.

        Raises:
            NetworkError: If the connection cannot be established.
        """
        # Import moved to top

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result != 0:
                raise NetworkError(f"Cannot connect to {host}:{port}", f"{host}:{port}")

        except socket.gaierror as e:
            raise NetworkError(f"DNS resolution failed for {host}: {e}", host) from e
        except Exception as e:
            raise NetworkError(
                f"Network error connecting to {host}:{port}: {e}", f"{host}:{port}"
            ) from e

    def create_error_report(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Creates a detailed error report for debugging purposes.

        This method gathers comprehensive information about an error, including
        a timestamp, a traceback, system details, and any provided context,
        and compiles it into a structured dictionary.

        Args:
            error: The exception that occurred.
            context: An optional dictionary of additional context information.

        Returns:
            A dictionary containing the detailed error report.
        """
        # Imports moved to top

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
        """Saves a detailed error report to a file.

        This method generates an error report using `create_error_report` and
        saves it as a JSON file in the system's temporary directory. This is
        useful for persisting debugging information for unexpected errors.

        Args:
            error: The exception that occurred.
            context: An optional dictionary of additional context information.

        Returns:
            The path to the saved error report file, or an empty string if
            saving fails.
        """
        # Imports moved to top

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
        """Validates that the system meets the necessary requirements to run Tinel.

        This method checks for the correct Python version, operating system,
        and the availability of required system utilities.

        Raises:
            ConfigurationError: If any system requirement is not met.
        """
        # Imports moved to top

        # Check Python version
        if sys.version_info < (3, 11):
            raise ConfigurationError(
                f"Python 3.11+ required, found "
                f"{sys.version_info[0]}.{sys.version_info[1]}",
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
        """Handles operations that require permission escalation.

        This method raises a `PermissionError` with a user-friendly message
        that suggests re-running the command with `sudo`.

        Args:
            operation: The operation that requires elevated privileges.
            resource: The resource that requires access.

        Raises:
            PermissionError: Always, to indicate that permission was denied.
        """
        raise PermissionError(
            f"Permission denied for {operation} on {resource}. "
            f"This operation requires elevated privileges. "
            f"Try running with elevated privileges: sudo tinel {operation}",
            resource,
        )

    def validate_cli_arguments(self, args: Any) -> None:
        """Validates the parsed CLI arguments.

        This method checks for any conflicting or invalid arguments provided by
        the user, such as using `--quiet` and `--verbose` together or
        specifying an invalid output format.

        Args:
            args: The namespace object returned by `ArgumentParser.parse_args()`.

        Raises:
            InvalidArgumentError: If any argument is found to be invalid.
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
                f"Invalid output format '{args.format}'. "
                f"Valid formats: {', '.join(valid_formats)}",
                "format",
            )

    def get_error_context(self) -> Dict[str, Any]:
        """Gathers the current system context for error reporting.

        This method collects a snapshot of the system's state at the time of
        an error, including user, working directory, environment variables, and
        platform details. This information is invaluable for debugging.

        Returns:
            A dictionary containing the system context information.
        """
        # Imports moved to top

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
        """Formats an error message for user-friendly display.

        This method takes an exception and an optional context string and
        creates a simple, readable error message suitable for display to the
        end user.

        Args:
            error: The exception that occurred.
            context: An optional string providing context for the error.

        Returns:
            A formatted, user-friendly error message as a string.
        """
        error_type = type(error).__name__
        error_message = str(error)

        if context:
            return f"{context}: {error_type}: {error_message}"
        else:
            return f"{error_type}: {error_message}"
