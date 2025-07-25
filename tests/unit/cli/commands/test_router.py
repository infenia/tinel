#!/usr/bin/env python3
"""
Unit tests for CLI command router module.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import argparse
from unittest.mock import Mock, patch

import pytest

from tests.utils import unit_test
from tinel.cli.commands.router import CommandRouter
from tinel.cli.error_handler import CLIError, CommandNotFoundError, InvalidArgumentError


class TestCommandRouter:
    """Test CLI command router."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = Mock()
        self.error_handler = Mock()

        # Mock HardwareCommands during router creation
        with patch("tinel.cli.commands.router.HardwareCommands") as mock_hw_class:
            self.mock_hardware_commands = Mock()
            mock_hw_class.return_value = self.mock_hardware_commands
            self.router = CommandRouter(self.formatter, self.error_handler)

    @unit_test
    def test_initialization(self):
        """Test command router initialization."""
        assert self.router.formatter == self.formatter
        assert self.router.error_handler == self.error_handler
        assert hasattr(self.router, "hardware_commands")
        assert "hardware" in self.router.command_handlers
        assert "hw" in self.router.command_handlers

    @unit_test
    def test_command_handlers_mapping(self):
        """Test that command handlers are properly mapped."""
        # Both 'hardware' and 'hw' should map to the same handler
        hardware_handler = self.router.command_handlers["hardware"]
        hw_handler = self.router.command_handlers["hw"]

        assert hardware_handler == hw_handler
        assert hardware_handler == self.router.hardware_commands.execute

    @unit_test
    def test_execute_command_no_command(self):
        """Test executing with no command specified."""
        args = argparse.Namespace(command=None)

        # Mock handle_cli_error to prevent actual error handling
        self.error_handler.handle_cli_error = Mock()

        result = self.router.execute_command(args)

        assert result == 1
        self.error_handler.handle_cli_error.assert_called_once()
        error_arg = self.error_handler.handle_cli_error.call_args[0][0]
        assert isinstance(error_arg, InvalidArgumentError)
        assert "No command specified" in str(error_arg)

    @unit_test
    def test_execute_command_empty_command(self):
        """Test executing with empty command."""
        args = argparse.Namespace(command="")

        self.error_handler.handle_cli_error = Mock()

        result = self.router.execute_command(args)

        assert result == 1
        self.error_handler.handle_cli_error.assert_called_once()

    @unit_test
    def test_execute_command_unknown_command(self):
        """Test executing unknown command."""
        args = argparse.Namespace(command="unknown")

        self.error_handler.handle_cli_error = Mock()

        result = self.router.execute_command(args)

        assert result == 1
        self.error_handler.handle_cli_error.assert_called_once()
        error_arg = self.error_handler.handle_cli_error.call_args[0][0]
        assert isinstance(error_arg, CommandNotFoundError)

    @unit_test
    def test_execute_command_hardware_success(self):
        """Test successful hardware command execution."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        # Mock the hardware command handler to return success
        self.mock_hardware_commands.execute.return_value = 0

        result = self.router.execute_command(args)

        assert result == 0
        self.mock_hardware_commands.execute.assert_called_once_with(args)

    @unit_test
    def test_execute_command_hw_alias_success(self):
        """Test successful hardware command execution using 'hw' alias."""
        args = argparse.Namespace(command="hw", hardware_command="cpu")

        self.mock_hardware_commands.execute.return_value = 0

        result = self.router.execute_command(args)

        assert result == 0
        self.mock_hardware_commands.execute.assert_called_once_with(args)

    @unit_test
    def test_execute_command_hardware_failure(self):
        """Test hardware command execution failure."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        # Mock the hardware command handler to return failure
        self.mock_hardware_commands.execute.return_value = 1

        result = self.router.execute_command(args)

        assert result == 1
        self.mock_hardware_commands.execute.assert_called_once_with(args)

    @unit_test
    def test_execute_command_cli_error_handling(self):
        """Test handling of CLIError exceptions."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        cli_error = CLIError("Test CLI error", exit_code=10)
        self.mock_hardware_commands.execute.side_effect = cli_error
        self.error_handler.handle_cli_error = Mock()

        result = self.router.execute_command(args)

        assert result == 10  # Should return the CLI error's exit code
        self.error_handler.handle_cli_error.assert_called_once_with(cli_error)

    @unit_test
    def test_execute_command_keyboard_interrupt(self):
        """Test handling of KeyboardInterrupt."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        self.mock_hardware_commands.execute.side_effect = KeyboardInterrupt()

        # KeyboardInterrupt should be re-raised
        with pytest.raises(KeyboardInterrupt):
            self.router.execute_command(args)

    @unit_test
    def test_execute_command_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        unexpected_error = RuntimeError("Unexpected error")
        self.mock_hardware_commands.execute.side_effect = unexpected_error
        self.error_handler.handle_exception = Mock()

        result = self.router.execute_command(args)

        assert result == 1
        self.error_handler.handle_exception.assert_called_once_with(
            unexpected_error, "command 'hardware'"
        )

    @unit_test
    def test_execute_command_logging(self):
        """Test that command execution is logged."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        self.mock_hardware_commands.execute.return_value = 0

        with patch("tinel.cli.commands.router.logger") as mock_logger:
            result = self.router.execute_command(args)

            assert result == 0
            # Debug logging should occur
            mock_logger.debug.assert_called_with("Executing command: hardware")

    @unit_test
    def test_execute_command_cli_error_logging(self):
        """Test that CLI errors are logged."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        cli_error = CLIError("Test error")
        self.mock_hardware_commands.execute.side_effect = cli_error
        self.error_handler.handle_cli_error = Mock()

        with patch("tinel.cli.commands.router.logger") as mock_logger:
            self.router.execute_command(args)

            mock_logger.debug.assert_called_with(
                "CLI error in command hardware: Test error"
            )

    @unit_test
    def test_execute_command_unexpected_error_logging(self):
        """Test that unexpected errors are logged."""
        args = argparse.Namespace(command="hardware", hardware_command="cpu")

        unexpected_error = RuntimeError("Unexpected")
        self.mock_hardware_commands.execute.side_effect = unexpected_error
        self.error_handler.handle_exception = Mock()

        with patch("tinel.cli.commands.router.logger") as mock_logger:
            self.router.execute_command(args)

            mock_logger.exception.assert_called_with(
                "Unexpected error executing command hardware"
            )


class TestCommandRouterIntegration:
    """Integration tests for command router."""

    @unit_test
    def test_router_with_real_hardware_commands(self):
        """Test router with actual hardware commands instance."""
        formatter = Mock()
        error_handler = Mock()

        # Don't mock the hardware commands - let it be created normally
        router = CommandRouter(formatter, error_handler)

        # Verify the hardware commands were created
        assert router.hardware_commands is not None
        assert hasattr(router.hardware_commands, "execute")

        # Verify command handlers are set up correctly
        assert "hardware" in router.command_handlers
        assert "hw" in router.command_handlers
        assert router.command_handlers["hardware"] == router.hardware_commands.execute
        assert router.command_handlers["hw"] == router.hardware_commands.execute

    @unit_test
    def test_router_command_handler_consistency(self):
        """Test that all command aliases point to the same handler."""
        formatter = Mock()
        error_handler = Mock()
        router = CommandRouter(formatter, error_handler)

        # Both hardware and hw should point to the same handler
        hardware_handler = router.command_handlers.get("hardware")
        hw_handler = router.command_handlers.get("hw")

        assert hardware_handler is not None
        assert hw_handler is not None
        assert hardware_handler == hw_handler


@pytest.mark.parametrize(
    "command,should_exist",
    [
        ("hardware", True),
        ("hw", True),
        ("unknown", False),
        ("", False),
        (None, False),
    ],
)
@unit_test
def test_command_handler_existence(command, should_exist):
    """Test command handler existence for various commands."""
    formatter = Mock()
    error_handler = Mock()
    router = CommandRouter(formatter, error_handler)

    if should_exist:
        assert command in router.command_handlers
        handler = router.command_handlers.get(command)
        assert handler is not None
        assert callable(handler)
    else:
        assert (
            command not in router.command_handlers
            or router.command_handlers.get(command) is None
        )


@pytest.mark.parametrize("command_name", ["hardware", "hw"])
@unit_test
def test_command_aliases(command_name):
    """Test that command aliases work correctly."""
    formatter = Mock()
    error_handler = Mock()

    with patch("tinel.cli.commands.router.HardwareCommands") as mock_hw_class:
        mock_hardware_commands = Mock()
        mock_hw_class.return_value = mock_hardware_commands
        router = CommandRouter(formatter, error_handler)

        args = argparse.Namespace(command=command_name, hardware_command="cpu")

        # Mock the hardware command execution
        mock_hardware_commands.execute.return_value = 0

        result = router.execute_command(args)

        assert result == 0
        mock_hardware_commands.execute.assert_called_once_with(args)


@pytest.mark.parametrize(
    "exception_type,expected_result",
    [
        (RuntimeError("Runtime error"), 1),
        (ValueError("Value error"), 1),
        (OSError("OS error"), 1),
        (Exception("Generic error"), 1),
    ],
)
@unit_test
def test_exception_handling_types(exception_type, expected_result):
    """Test handling of different exception types."""
    formatter = Mock()
    error_handler = Mock()

    with patch("tinel.cli.commands.router.HardwareCommands") as mock_hw_class:
        mock_hardware_commands = Mock()
        mock_hw_class.return_value = mock_hardware_commands
        router = CommandRouter(formatter, error_handler)

        args = argparse.Namespace(command="hardware")
        mock_hardware_commands.execute.side_effect = exception_type
        error_handler.handle_exception = Mock()

        result = router.execute_command(args)

        assert result == expected_result
        error_handler.handle_exception.assert_called_once_with(
            exception_type, "command 'hardware'"
        )


@pytest.mark.parametrize("exit_code", [0, 1, 2, 10, 127])
@unit_test
def test_cli_error_exit_codes(exit_code):
    """Test that CLI error exit codes are properly returned."""
    formatter = Mock()
    error_handler = Mock()

    with patch("tinel.cli.commands.router.HardwareCommands") as mock_hw_class:
        mock_hardware_commands = Mock()
        mock_hw_class.return_value = mock_hardware_commands
        router = CommandRouter(formatter, error_handler)

        args = argparse.Namespace(command="hardware")
        cli_error = CLIError("Test error", exit_code=exit_code)
        mock_hardware_commands.execute.side_effect = cli_error
        error_handler.handle_cli_error = Mock()

        result = router.execute_command(args)

        assert result == exit_code
        error_handler.handle_cli_error.assert_called_once_with(cli_error)
