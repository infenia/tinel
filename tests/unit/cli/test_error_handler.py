#!/usr/bin/env python3
"""
Unit tests for CLI error handler module.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import json
import os
import socket
import sys
import tempfile
from io import StringIO
from unittest.mock import Mock, patch, mock_open

import pytest

from tinel.cli.error_handler import (
    ExitCode,
    CLIError,
    CommandNotFoundError,
    InvalidArgumentError,
    PermissionError,
    FileNotFoundError,
    NetworkError,
    ConfigurationError,
    HardwareError,
    KernelError,
    LogAnalysisError,
    DiagnosticsError,
    CLIErrorHandler,
)
from tests.utils import unit_test


class TestExitCode:
    """Test exit code enum."""

    @unit_test
    def test_exit_code_values(self):
        """Test that exit codes have correct values."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.GENERAL_ERROR == 1
        assert ExitCode.COMMAND_NOT_FOUND == 127
        assert ExitCode.KEYBOARD_INTERRUPT == 130
        assert ExitCode.PERMISSION_DENIED == 10
        assert ExitCode.HARDWARE_ERROR == 14


class TestCLIError:
    """Test base CLI error class."""

    @unit_test
    def test_cli_error_default(self):
        """Test CLI error with default values."""
        error = CLIError("Test error")

        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.exit_code == ExitCode.GENERAL_ERROR
        assert error.details == {}

    @unit_test
    def test_cli_error_with_details(self):
        """Test CLI error with custom details."""
        details = {"key": "value", "number": 42}
        error = CLIError("Test error", ExitCode.CONFIGURATION_ERROR, details)

        assert error.message == "Test error"
        assert error.exit_code == ExitCode.CONFIGURATION_ERROR
        assert error.details == details


class TestSpecificErrors:
    """Test specific error classes."""

    @unit_test
    def test_command_not_found_error(self):
        """Test CommandNotFoundError."""
        error = CommandNotFoundError("lscpu")

        assert "lscpu" in error.message
        assert error.exit_code == ExitCode.COMMAND_NOT_FOUND
        assert error.details["command"] == "lscpu"

    @unit_test
    def test_invalid_argument_error(self):
        """Test InvalidArgumentError."""
        error = InvalidArgumentError("Invalid format", "format")

        assert error.message == "Invalid format"
        assert error.exit_code == ExitCode.INVALID_ARGUMENT
        assert error.details["argument"] == "format"

    @unit_test
    def test_invalid_argument_error_no_argument(self):
        """Test InvalidArgumentError without specific argument."""
        error = InvalidArgumentError("Invalid syntax")

        assert error.message == "Invalid syntax"
        assert error.details == {}

    @unit_test
    def test_permission_error(self):
        """Test PermissionError."""
        error = PermissionError("Access denied", "/etc/shadow")

        assert error.message == "Access denied"
        assert error.exit_code == ExitCode.PERMISSION_DENIED
        assert error.details["resource"] == "/etc/shadow"

    @unit_test
    def test_file_not_found_error(self):
        """Test FileNotFoundError."""
        error = FileNotFoundError("/path/to/missing/file")

        assert "/path/to/missing/file" in error.message
        assert error.exit_code == ExitCode.FILE_NOT_FOUND
        assert error.details["file_path"] == "/path/to/missing/file"

    @unit_test
    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection failed", "example.com:80")

        assert error.message == "Connection failed"
        assert error.exit_code == ExitCode.NETWORK_ERROR
        assert error.details["endpoint"] == "example.com:80"

    @unit_test
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid config", "api_key")

        assert error.message == "Invalid config"
        assert error.exit_code == ExitCode.CONFIGURATION_ERROR
        assert error.details["config_key"] == "api_key"

    @unit_test
    def test_hardware_error(self):
        """Test HardwareError."""
        error = HardwareError("CPU error", "cpu")

        assert error.message == "CPU error"
        assert error.exit_code == ExitCode.HARDWARE_ERROR
        assert error.details["component"] == "cpu"

    @unit_test
    def test_kernel_error(self):
        """Test KernelError."""
        error = KernelError("Kernel panic", "memory_allocation")

        assert error.message == "Kernel panic"
        assert error.exit_code == ExitCode.KERNEL_ERROR
        assert error.details["operation"] == "memory_allocation"

    @unit_test
    def test_log_analysis_error(self):
        """Test LogAnalysisError."""
        error = LogAnalysisError("Parse failed", "/var/log/syslog")

        assert error.message == "Parse failed"
        assert error.exit_code == ExitCode.LOG_ANALYSIS_ERROR
        assert error.details["log_source"] == "/var/log/syslog"

    @unit_test
    def test_diagnostics_error(self):
        """Test DiagnosticsError."""
        error = DiagnosticsError("Diagnosis failed", "system_check")

        assert error.message == "Diagnosis failed"
        assert error.exit_code == ExitCode.DIAGNOSTICS_ERROR
        assert error.details["diagnostic_type"] == "system_check"

    @unit_test
    def test_permission_error_no_resource(self):
        """Test PermissionError without a resource."""
        error = PermissionError("Access denied")
        assert error.message == "Access denied"
        assert error.exit_code == ExitCode.PERMISSION_DENIED
        assert error.details == {}

    @unit_test
    def test_network_error_no_endpoint(self):
        """Test NetworkError without an endpoint."""
        error = NetworkError("Connection failed")
        assert error.message == "Connection failed"
        assert error.exit_code == ExitCode.NETWORK_ERROR
        assert error.details == {}

    @unit_test
    def test_configuration_error_no_key(self):
        """Test ConfigurationError without a config_key."""
        error = ConfigurationError("Invalid config")
        assert error.message == "Invalid config"
        assert error.exit_code == ExitCode.CONFIGURATION_ERROR
        assert error.details == {}

    @unit_test
    def test_hardware_error_no_component(self):
        """Test HardwareError without a component."""
        error = HardwareError("CPU error")
        assert error.message == "CPU error"
        assert error.exit_code == ExitCode.HARDWARE_ERROR
        assert error.details == {}

    @unit_test
    def test_kernel_error_no_operation(self):
        """Test KernelError without an operation."""
        error = KernelError("Kernel panic")
        assert error.message == "Kernel panic"
        assert error.exit_code == ExitCode.KERNEL_ERROR
        assert error.details == {}

    @unit_test
    def test_log_analysis_error_no_source(self):
        """Test LogAnalysisError without a log_source."""
        error = LogAnalysisError("Parse failed")
        assert error.message == "Parse failed"
        assert error.exit_code == ExitCode.LOG_ANALYSIS_ERROR
        assert error.details == {}

    @unit_test
    def test_diagnostics_error_no_type(self):
        """Test DiagnosticsError without a diagnostic_type."""
        error = DiagnosticsError("Diagnosis failed")
        assert error.message == "Diagnosis failed"
        assert error.exit_code == ExitCode.DIAGNOSTICS_ERROR
        assert error.details == {}


class TestCLIErrorHandler:
    """Test CLI error handler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_initialization(self):
        """Test error handler initialization."""
        assert self.handler.formatter == self.formatter
        assert isinstance(self.handler.error_suggestions, dict)
        assert ExitCode.COMMAND_NOT_FOUND in self.handler.error_suggestions

    @unit_test
    def test_handle_error_basic(self):
        """Test basic error handling."""
        with patch("sys.exit") as mock_exit:
            # The logger is already created at module level
            self.handler.handle_error("Test error")

            self.formatter.print_error.assert_called_once_with("Test error")
            mock_exit.assert_called_once_with(ExitCode.GENERAL_ERROR)

    @unit_test
    def test_handle_error_with_details(self):
        """Test error handling with details."""
        self.formatter.verbose = 1
        details = {"key": "value"}

        with patch("sys.exit"):
            self.handler.handle_error("Test error", details=details)

            self.formatter.print_debug.assert_called_once()

    @unit_test
    def test_handle_error_with_suggestion(self):
        """Test error handling with custom suggestion."""
        with patch("sys.exit"):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                self.handler.handle_error("Test error", suggestion="Try this fix")

                stderr_output = mock_stderr.getvalue()
                assert "Suggestion: Try this fix" in stderr_output

    @unit_test
    def test_handle_error_default_suggestion(self):
        """Test error handling with default suggestion."""
        with patch("sys.exit"):
            with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                self.handler.handle_error(
                    "Command not found", ExitCode.COMMAND_NOT_FOUND
                )

                stderr_output = mock_stderr.getvalue()
                assert "tinel --help" in stderr_output

    @unit_test
    def test_handle_error_save_report(self):
        """Test error report saving for general errors."""
        details = {"context": "test"}
        self.formatter.verbose = 0  # Set verbose to an integer, not a Mock

        with patch("sys.exit"):
            with patch.object(
                self.handler, "save_error_report", return_value="/tmp/report.json"
            ):
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    self.handler.handle_error(
                        "General error", ExitCode.GENERAL_ERROR, details
                    )

                    stderr_output = mock_stderr.getvalue()
                    assert "Error report saved to" in stderr_output

    @unit_test
    def test_handle_error_save_report_failure_in_handle_error(self):
        """Test error report saving failure within handle_error."""
        details = {"context": "test"}
        self.formatter.verbose = 0

        with patch("sys.exit"):
            with patch.object(
                self.handler, "save_error_report", side_effect=Exception("Save failed")
            ):
                with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
                    with patch.object(
                        self.formatter, "print_error"
                    ) as mock_print_error:
                        self.handler.handle_error(
                            "General error", ExitCode.GENERAL_ERROR, details
                        )

                        mock_print_error.assert_called_once_with("General error")
                        stderr_output = mock_stderr.getvalue()
                        # Assert that no message about saving report is printed
                        assert "Error report saved to" not in stderr_output

    @unit_test
    def test_handle_cli_error(self):
        """Test handling CLIError instances."""
        cli_error = CLIError(
            "Test CLI error", ExitCode.HARDWARE_ERROR, {"component": "cpu"}
        )

        with patch.object(self.handler, "handle_error") as mock_handle:
            self.handler.handle_cli_error(cli_error)

            mock_handle.assert_called_once_with(
                cli_error.message, cli_error.exit_code, cli_error.details
            )

    @unit_test
    def test_handle_exception(self):
        """Test handling unexpected exceptions."""
        exception = RuntimeError("Unexpected error")

        with patch.object(self.handler, "handle_error") as mock_handle:
            self.handler.handle_exception(exception, "test context")

            mock_handle.assert_called_once()
            args = mock_handle.call_args[0]
            assert "test context" in args[0]
            assert "Unexpected error" in args[0]


class TestFileValidation:
    """Test file validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_validate_file_access_file_not_found(self):
        """Test file validation when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                self.handler.validate_file_access("/nonexistent/file")

    @unit_test
    def test_validate_file_access_read_permission_denied(self):
        """Test file validation when read permission is denied."""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=False):
                with pytest.raises(PermissionError):
                    self.handler.validate_file_access("/restricted/file", "read")

    @unit_test
    def test_validate_file_access_write_permission_denied(self):
        """Test file validation when write permission is denied."""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=False):
                with pytest.raises(PermissionError):
                    self.handler.validate_file_access("/restricted/file", "write")

    @unit_test
    def test_validate_file_access_execute_permission_denied(self):
        """Test file validation when execute permission is denied."""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=False):
                with pytest.raises(PermissionError):
                    self.handler.validate_file_access("/restricted/file", "execute")

    @unit_test
    def test_validate_file_access_success(self):
        """Test successful file validation."""
        with patch("os.path.exists", return_value=True):
            with patch("os.access", return_value=True):
                # Should not raise any exception
                self.handler.validate_file_access("/accessible/file", "read")


class TestCommandValidation:
    """Test command validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_validate_command_availability_found(self):
        """Test command validation when command is found."""
        with patch("shutil.which", return_value="/usr/bin/lscpu"):
            # Should not raise any exception
            self.handler.validate_command_availability("lscpu")

    @unit_test
    def test_validate_command_availability_not_found(self):
        """Test command validation when command is not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(CommandNotFoundError):
                self.handler.validate_command_availability("nonexistent_command")


class TestNetworkValidation:
    """Test network validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_validate_network_connectivity_success(self):
        """Test successful network connectivity validation."""
        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 0

        with patch("socket.socket", return_value=mock_socket):
            # Should not raise any exception
            self.handler.validate_network_connectivity("example.com", 80)

    @unit_test
    def test_validate_network_connectivity_connection_failed(self):
        """Test network validation when connection fails."""
        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 1  # Connection failed

        with patch("socket.socket", return_value=mock_socket):
            with pytest.raises(NetworkError):
                self.handler.validate_network_connectivity("example.com", 80)

    @unit_test
    def test_validate_network_connectivity_dns_failure(self):
        """Test network validation when DNS resolution fails."""
        with patch("socket.socket", side_effect=socket.gaierror("DNS failed")):
            with pytest.raises(NetworkError):
                self.handler.validate_network_connectivity("invalid.example", 80)

    @unit_test
    def test_validate_network_connectivity_general_exception(self):
        """Test network validation with general exception."""
        with patch("socket.socket", side_effect=OSError("General error")):
            with pytest.raises(NetworkError):
                self.handler.validate_network_connectivity("example.com", 80)


class TestErrorReporting:
    """Test error reporting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_create_error_report(self):
        """Test error report creation."""
        error = RuntimeError("Test error")
        context = {"test": "context"}

        with patch("platform.platform", return_value="Linux"):
            with patch("sys.version", "3.11.0"):
                report = self.handler.create_error_report(error, context)

                assert "timestamp" in report
                assert report["error"]["type"] == "RuntimeError"
                assert report["error"]["message"] == "Test error"
                assert "traceback" in report["error"]
                assert report["system"]["platform"] == "Linux"
                assert report["context"] == context

    @unit_test
    def test_save_error_report_success(self):
        """Test successful error report saving."""
        error = RuntimeError("Test error")

        with patch("tempfile.gettempdir", return_value="/tmp"):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("json.dump") as mock_json_dump:
                    filepath = self.handler.save_error_report(error)

                    assert filepath.startswith("/tmp/tinel_error_")
                    assert filepath.endswith(".json")
                    mock_file.assert_called_once()
                    mock_json_dump.assert_called_once()

    @unit_test
    def test_save_error_report_failure(self):
        """Test error report saving failure."""
        error = RuntimeError("Test error")

        with patch("tempfile.gettempdir", return_value="/tmp"):
            with patch("builtins.open", side_effect=OSError("Write failed")):
                with patch("tinel.cli.error_handler.logger") as mock_logger:
                    filepath = self.handler.save_error_report(error)

                    assert filepath == ""
                    mock_logger.warning.assert_called_once()


class TestSystemValidation:
    """Test system validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_validate_system_requirements_python_version_too_old(self):
        """Test system validation with old Python version."""
        with patch("sys.version_info", (3, 10, 0)):
            with pytest.raises(ConfigurationError, match="Python 3.11\\+ required"):
                self.handler.validate_system_requirements()

    @unit_test
    def test_validate_system_requirements_not_linux(self):
        """Test system validation on non-Linux system."""
        with patch("platform.system", return_value="Windows"):
            with pytest.raises(ConfigurationError, match="Tinel requires Linux"):
                self.handler.validate_system_requirements()

    @unit_test
    def test_validate_system_requirements_missing_commands(self):
        """Test system validation with missing commands."""
        with patch("platform.system", return_value="Linux"):
            with patch("sys.version_info", (3, 11, 0)):
                with patch.object(
                    self.handler,
                    "validate_command_availability",
                    side_effect=CommandNotFoundError("lscpu"),
                ):
                    with pytest.raises(
                        ConfigurationError, match="Required system utilities not found"
                    ):
                        self.handler.validate_system_requirements()

    @unit_test
    def test_validate_system_requirements_success(self):
        """Test successful system validation."""
        with patch("platform.system", return_value="Linux"):
            with patch("sys.version_info", (3, 11, 0)):
                with patch.object(self.handler, "validate_command_availability"):
                    # Should not raise any exception
                    self.handler.validate_system_requirements()


class TestPermissionHandling:
    """Test permission handling methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_handle_permission_escalation(self):
        """Test permission escalation handling."""
        with pytest.raises(PermissionError) as exc_info:
            self.handler.handle_permission_escalation("read", "/etc/shadow")

        error = exc_info.value
        assert "Permission denied" in error.message
        assert "sudo tinel read" in error.message
        assert error.details["resource"] == "/etc/shadow"


class TestArgumentValidation:
    """Test CLI argument validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_validate_cli_arguments_conflicting_quiet_verbose(self):
        """Test validation of conflicting quiet and verbose options."""
        args = Mock(quiet=True, verbose=1)

        with pytest.raises(
            InvalidArgumentError, match="Cannot use both --quiet and --verbose"
        ):
            self.handler.validate_cli_arguments(args)

    @unit_test
    def test_validate_cli_arguments_negative_verbosity(self):
        """Test validation of negative verbosity."""
        args = Mock(quiet=False, verbose=-1)

        with pytest.raises(
            InvalidArgumentError, match="Verbosity level cannot be negative"
        ):
            self.handler.validate_cli_arguments(args)

    @unit_test
    def test_validate_cli_arguments_invalid_format(self):
        """Test validation of invalid output format."""
        args = Mock(quiet=False, verbose=0, format="invalid")

        with pytest.raises(InvalidArgumentError, match="Invalid output format"):
            self.handler.validate_cli_arguments(args)

    @unit_test
    def test_validate_cli_arguments_valid(self):
        """Test validation of valid arguments."""
        args = Mock(quiet=False, verbose=1, format="json")

        # Should not raise any exception
        self.handler.validate_cli_arguments(args)

    @unit_test
    def test_validate_cli_arguments_missing_attributes(self):
        """Test validation when args don't have expected attributes."""
        args = Mock(spec=[])  # Empty spec means no attributes

        # Should not raise any exception when attributes are missing
        self.handler.validate_cli_arguments(args)


class TestContextGathering:
    """Test system context gathering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_get_error_context_success(self):
        """Test successful context gathering."""
        mock_pwd_struct = Mock()
        mock_pwd_struct.pw_name = "testuser"

        with patch("pwd.getpwuid", return_value=mock_pwd_struct):
            with patch("os.getuid", return_value=1000):
                with patch("os.getcwd", return_value="/home/testuser"):
                    with patch("platform.platform", return_value="Linux"):
                        context = self.handler.get_error_context()

                        assert "timestamp" in context
                        assert context["user"] == "testuser"
                        assert context["working_directory"] == "/home/testuser"
                        assert "environment" in context
                        assert "system" in context

    @unit_test
    def test_get_error_context_exception(self):
        """Test context gathering with exception."""
        with patch("pwd.getpwuid", side_effect=KeyError("User not found")):
            context = self.handler.get_error_context()

            assert "timestamp" in context
            assert "error" in context
            assert context["error"] == "Could not gather full system context"


class TestErrorFormatting:
    """Test error message formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.handler = CLIErrorHandler(self.formatter)

    @unit_test
    def test_format_error_for_user_with_context(self):
        """Test error formatting with context."""
        error = RuntimeError("Something went wrong")

        result = self.handler.format_error_for_user(error, "hardware analysis")

        assert "hardware analysis" in result
        assert "RuntimeError" in result
        assert "Something went wrong" in result

    @unit_test
    def test_format_error_for_user_without_context(self):
        """Test error formatting without context."""
        error = ValueError("Invalid value")

        result = self.handler.format_error_for_user(error)

        assert "ValueError" in result
        assert "Invalid value" in result
        assert result.startswith("ValueError:")


@pytest.mark.parametrize(
    "exit_code,has_suggestion",
    [
        (ExitCode.COMMAND_NOT_FOUND, True),
        (ExitCode.INVALID_ARGUMENT, True),
        (ExitCode.PERMISSION_DENIED, True),
        (ExitCode.FILE_NOT_FOUND, True),
        (ExitCode.NETWORK_ERROR, True),
        (ExitCode.CONFIGURATION_ERROR, True),
        (ExitCode.HARDWARE_ERROR, True),
        (ExitCode.KERNEL_ERROR, True),
        (ExitCode.LOG_ANALYSIS_ERROR, True),
        (ExitCode.DIAGNOSTICS_ERROR, True),
        (ExitCode.SUCCESS, False),  # Success doesn't need suggestion
    ],
)
@unit_test
def test_error_suggestions_coverage(exit_code, has_suggestion):
    """Test that error suggestions are available for appropriate exit codes."""
    formatter = Mock()
    handler = CLIErrorHandler(formatter)

    if has_suggestion:
        assert exit_code in handler.error_suggestions
        assert isinstance(handler.error_suggestions[exit_code], str)
        assert len(handler.error_suggestions[exit_code]) > 0
    else:
        # Success and other codes might not have suggestions
        pass


@pytest.mark.parametrize(
    "error_class,expected_exit_code",
    [
        (CommandNotFoundError, ExitCode.COMMAND_NOT_FOUND),
        (InvalidArgumentError, ExitCode.INVALID_ARGUMENT),
        (FileNotFoundError, ExitCode.FILE_NOT_FOUND),
        (NetworkError, ExitCode.NETWORK_ERROR),
        (ConfigurationError, ExitCode.CONFIGURATION_ERROR),
        (HardwareError, ExitCode.HARDWARE_ERROR),
        (KernelError, ExitCode.KERNEL_ERROR),
        (LogAnalysisError, ExitCode.LOG_ANALYSIS_ERROR),
        (DiagnosticsError, ExitCode.DIAGNOSTICS_ERROR),
    ],
)
@unit_test
def test_error_exit_codes(error_class, expected_exit_code):
    """Test that error classes use correct exit codes."""
    if error_class == CommandNotFoundError:
        error = error_class("test_command")
    elif error_class == FileNotFoundError:
        error = error_class("/test/path")
    elif error_class in [
        InvalidArgumentError,
        NetworkError,
        ConfigurationError,
        HardwareError,
        KernelError,
        LogAnalysisError,
        DiagnosticsError,
    ]:
        error = error_class("Test message")
    else:
        error = error_class("Test message")

    assert error.exit_code == expected_exit_code
