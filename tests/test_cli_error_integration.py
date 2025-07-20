#!/usr/bin/env python3
"""Integration Tests for CLI Error Handling.

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

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add the parent directory to the path to import infenix modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from infenix.cli.main import main
from infenix.cli.commands.router import CommandRouter
from infenix.cli.commands.base import BaseCommand
from infenix.cli.error_handler import (
    ExitCode,
    CLIError,
    CommandNotFoundError,
    HardwareError,
    KernelError,
    LogAnalysisError,
    DiagnosticsError
)
from infenix.cli.formatters import OutputFormatter


class TestCLIMainErrorHandling(unittest.TestCase):
    """Test error handling in the main CLI entry point."""
    
    @patch('infenix.cli.main.parse_arguments')
    @patch('infenix.cli.main.setup_logging')
    @patch('infenix.cli.main.OutputFormatter')
    @patch('infenix.cli.main.CLIErrorHandler')
    @patch('infenix.cli.main.CommandRouter')
    def test_main_success(self, mock_router_class, mock_error_handler_class, 
                         mock_formatter_class, mock_setup_logging, mock_parse_args):
        """Test successful main execution."""
        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = 0
        mock_args.quiet = False
        mock_args.format = 'text'
        mock_args.no_color = False
        mock_parse_args.return_value = mock_args
        
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler
        
        mock_router = Mock()
        mock_router.execute_command.return_value = 0
        mock_router_class.return_value = mock_router
        
        # Execute
        result = main(['hardware'])
        
        # Verify
        self.assertEqual(result, 0)
        mock_parse_args.assert_called_once_with(['hardware'])
        mock_setup_logging.assert_called_once_with(0, False)
        mock_router.execute_command.assert_called_once_with(mock_args)
    
    @patch('infenix.cli.main.parse_arguments')
    def test_main_keyboard_interrupt_no_error_handler(self, mock_parse_args):
        """Test keyboard interrupt handling when error handler is not yet created."""
        mock_parse_args.side_effect = KeyboardInterrupt()
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = main(['hardware'])
        
        self.assertEqual(result, 130)
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Operation cancelled by user", stderr_output)
    
    @patch('infenix.cli.main.parse_arguments')
    @patch('infenix.cli.main.setup_logging')
    @patch('infenix.cli.main.OutputFormatter')
    @patch('infenix.cli.main.CLIErrorHandler')
    def test_main_keyboard_interrupt_with_error_handler(self, mock_error_handler_class,
                                                       mock_formatter_class, mock_setup_logging,
                                                       mock_parse_args):
        """Test keyboard interrupt handling when error handler exists."""
        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = 0
        mock_args.quiet = False
        mock_args.format = 'text'
        mock_args.no_color = False
        mock_parse_args.return_value = mock_args
        
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        mock_error_handler = Mock()
        mock_error_handler.handle_error.side_effect = SystemExit(130)
        mock_error_handler_class.return_value = mock_error_handler
        
        with patch('infenix.cli.main.CommandRouter') as mock_router_class:
            mock_router = Mock()
            mock_router.execute_command.side_effect = KeyboardInterrupt()
            mock_router_class.return_value = mock_router
            
            result = main(['hardware'])
        
        self.assertEqual(result, 130)
        mock_error_handler.handle_error.assert_called_once_with(
            "Operation cancelled by user", 
            130, 
            suggestion="Use Ctrl+C to cancel operations"
        )
    
    @patch('infenix.cli.main.parse_arguments')
    def test_main_system_exit(self, mock_parse_args):
        """Test SystemExit handling."""
        mock_parse_args.side_effect = SystemExit(42)
        
        result = main(['hardware'])
        
        self.assertEqual(result, 42)
    
    @patch('infenix.cli.main.parse_arguments')
    def test_main_unexpected_exception_no_error_handler(self, mock_parse_args):
        """Test unexpected exception handling when error handler is not yet created."""
        mock_parse_args.side_effect = ValueError("Test error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = main(['hardware'])
        
        self.assertEqual(result, 1)
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Fatal error: Test error", stderr_output)
    
    @patch('infenix.cli.main.parse_arguments')
    @patch('infenix.cli.main.setup_logging')
    @patch('infenix.cli.main.OutputFormatter')
    @patch('infenix.cli.main.CLIErrorHandler')
    def test_main_unexpected_exception_with_error_handler(self, mock_error_handler_class,
                                                         mock_formatter_class, mock_setup_logging,
                                                         mock_parse_args):
        """Test unexpected exception handling when error handler exists."""
        # Setup mocks
        mock_args = Mock()
        mock_args.verbose = 0
        mock_args.quiet = False
        mock_args.format = 'text'
        mock_args.no_color = False
        mock_parse_args.return_value = mock_args
        
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        
        mock_error_handler = Mock()
        mock_error_handler.handle_exception.side_effect = SystemExit(1)
        mock_error_handler_class.return_value = mock_error_handler
        
        with patch('infenix.cli.main.CommandRouter') as mock_router_class:
            mock_router = Mock()
            mock_router.execute_command.side_effect = ValueError("Test error")
            mock_router_class.return_value = mock_router
            
            result = main(['hardware'])
        
        self.assertEqual(result, 1)
        # Check that handle_exception was called with the correct arguments
        args, kwargs = mock_error_handler.handle_exception.call_args
        self.assertIsInstance(args[0], ValueError)
        self.assertEqual(str(args[0]), "Test error")
        self.assertEqual(args[1], "main execution")


class TestCommandRouterErrorHandling(unittest.TestCase):
    """Test error handling in the command router."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = Mock(spec=OutputFormatter)
        self.error_handler = Mock()
        
        # Mock all command handlers to avoid initialization issues
        with patch('infenix.cli.commands.router.HardwareCommands'), \
             patch('infenix.cli.commands.router.KernelCommands'), \
             patch('infenix.cli.commands.router.LogsCommands'), \
             patch('infenix.cli.commands.router.DiagnosticsCommands'), \
             patch('infenix.cli.commands.router.ServerCommands'):
            self.router = CommandRouter(self.formatter, self.error_handler)
    
    def test_execute_command_no_command(self):
        """Test execution with no command specified."""
        args = Mock()
        args.command = None
        
        self.error_handler.handle_cli_error.side_effect = SystemExit(1)
        
        with self.assertRaises(SystemExit):
            self.router.execute_command(args)
        
        # Verify that InvalidArgumentError was raised
        from infenix.cli.error_handler import InvalidArgumentError
        call_args = self.error_handler.handle_cli_error.call_args[0][0]
        self.assertIsInstance(call_args, InvalidArgumentError)
        self.assertEqual(call_args.message, "No command specified")
    
    def test_execute_command_unknown_command(self):
        """Test execution with unknown command."""
        args = Mock()
        args.command = 'unknown-command'
        
        self.error_handler.handle_cli_error.side_effect = SystemExit(127)
        
        with self.assertRaises(SystemExit):
            self.router.execute_command(args)
        
        # Verify that CommandNotFoundError was raised
        self.error_handler.handle_cli_error.assert_called_once()
    
    def test_execute_command_cli_error(self):
        """Test execution when command raises CLIError."""
        args = Mock()
        args.command = 'hardware'
        
        # Mock the hardware command to raise a CLIError
        cli_error = HardwareError("Hardware detection failed", "cpu")
        mock_hardware_handler = Mock()
        mock_hardware_handler.side_effect = cli_error
        self.router.command_handlers['hardware'] = mock_hardware_handler
        
        result = self.router.execute_command(args)
        
        self.assertEqual(result, cli_error.exit_code)
        self.error_handler.handle_cli_error.assert_called_once_with(cli_error)
    
    def test_execute_command_keyboard_interrupt(self):
        """Test execution when command raises KeyboardInterrupt."""
        args = Mock()
        args.command = 'hardware'
        
        mock_hardware_handler = Mock()
        mock_hardware_handler.side_effect = KeyboardInterrupt()
        self.router.command_handlers['hardware'] = mock_hardware_handler
        
        with self.assertRaises(KeyboardInterrupt):
            self.router.execute_command(args)
    
    def test_execute_command_unexpected_exception(self):
        """Test execution when command raises unexpected exception."""
        args = Mock()
        args.command = 'hardware'
        
        exception = ValueError("Unexpected error")
        mock_hardware_handler = Mock()
        mock_hardware_handler.side_effect = exception
        self.router.command_handlers['hardware'] = mock_hardware_handler
        
        result = self.router.execute_command(args)
        
        self.assertEqual(result, 1)
        self.error_handler.handle_exception.assert_called_once_with(exception, "command 'hardware'")


class TestBaseCommandErrorHandling(unittest.TestCase):
    """Test error handling in the base command class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.formatter = Mock(spec=OutputFormatter)
        self.error_handler = Mock()
        
        # Create a concrete implementation of BaseCommand for testing
        class TestCommand(BaseCommand):
            def execute(self, args):
                return 0
        
        self.command = TestCommand(self.formatter, self.error_handler)
    
    def test_handle_tool_error_cli_error(self):
        """Test handling tool error when it's already a CLIError."""
        cli_error = HardwareError("Hardware failed", "cpu")
        
        with self.assertRaises(HardwareError):
            self.command._handle_tool_error(cli_error, "hardware")
    
    def test_handle_tool_error_hardware_tool(self):
        """Test handling tool error for hardware tools."""
        exception = ValueError("Hardware detection failed")
        
        with self.assertRaises(HardwareError) as cm:
            self.command._handle_tool_error(exception, "cpu_info")
        
        self.assertIn("Hardware analysis failed", cm.exception.message)
        self.assertEqual(cm.exception.details["component"], "cpu_info")
    
    def test_handle_tool_error_kernel_tool(self):
        """Test handling tool error for kernel tools."""
        exception = ValueError("Kernel config failed")
        
        with self.assertRaises(KernelError) as cm:
            self.command._handle_tool_error(exception, "kernel_config")
        
        self.assertIn("Kernel analysis failed", cm.exception.message)
        self.assertEqual(cm.exception.details["operation"], "kernel_config")
    
    def test_handle_tool_error_log_tool(self):
        """Test handling tool error for log analysis tools."""
        exception = ValueError("Log parsing failed")
        
        with self.assertRaises(LogAnalysisError) as cm:
            self.command._handle_tool_error(exception, "log_analysis")
        
        self.assertIn("Log analysis failed", cm.exception.message)
        self.assertEqual(cm.exception.details["log_source"], "log_analysis")
    
    def test_handle_tool_error_diagnostics_tool(self):
        """Test handling tool error for diagnostics tools."""
        exception = ValueError("Diagnostics failed")
        
        with self.assertRaises(DiagnosticsError) as cm:
            self.command._handle_tool_error(exception, "diagnose")
        
        self.assertIn("Diagnostics failed", cm.exception.message)
        self.assertEqual(cm.exception.details["diagnostic_type"], "diagnose")
    
    def test_handle_tool_error_unknown_tool(self):
        """Test handling tool error for unknown tools."""
        exception = ValueError("Unknown tool failed")
        
        with self.assertRaises(CLIError) as cm:
            self.command._handle_tool_error(exception, "unknown_tool")
        
        self.assertIn("Tool 'unknown_tool' execution failed", cm.exception.message)
    
    def test_execute_tool_success(self):
        """Test successful tool execution."""
        mock_tool = Mock()
        mock_tool.get_tool_name.return_value = "test_tool"
        mock_tool.execute.return_value = {"success": True, "data": "test_data"}
        
        parameters = {"param": "value"}
        result = self.command._execute_tool(mock_tool, parameters)
        
        self.assertEqual(result, {"success": True, "data": "test_data"})
        mock_tool.execute.assert_called_once_with(parameters)
        self.formatter.print_debug.assert_called_once_with("Executing tool: test_tool")
    
    def test_execute_tool_failure_in_result(self):
        """Test tool execution when result indicates failure."""
        mock_tool = Mock()
        mock_tool.get_tool_name.return_value = "test_tool"
        mock_tool.execute.return_value = {"success": False, "error": "Tool failed"}
        
        parameters = {"param": "value"}
        
        with self.assertRaises(CLIError) as cm:
            self.command._execute_tool(mock_tool, parameters)
        
        self.assertIn("Tool 'test_tool' execution failed: Tool failed", str(cm.exception))
    
    def test_execute_tool_exception(self):
        """Test tool execution when tool raises exception."""
        mock_tool = Mock()
        mock_tool.get_tool_name.return_value = "test_tool"
        mock_tool.execute.side_effect = ValueError("Tool exception")
        
        parameters = {"param": "value"}
        
        with self.assertRaises(CLIError) as cm:
            self.command._execute_tool(mock_tool, parameters)
        
        self.assertIn("Tool 'test_tool' execution failed: Tool exception", str(cm.exception))


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test end-to-end error handling integration."""
    
    @patch('infenix.cli.main.main')
    def test_cli_error_propagation(self, mock_main):
        """Test that CLI errors propagate correctly through the system."""
        # This test would be more comprehensive in a real integration test
        # For now, we'll test that the main function can be called
        mock_main.return_value = 0
        
        from infenix.__main__ import main as module_main
        
        with patch('sys.argv', ['infenix', 'hardware']):
            # This should not raise an exception
            pass
    
    def test_exit_code_consistency(self):
        """Test that exit codes are consistent across error types."""
        error_exit_code_map = {
            CommandNotFoundError("test"): ExitCode.COMMAND_NOT_FOUND,
            HardwareError("test", "cpu"): ExitCode.HARDWARE_ERROR,
            KernelError("test", "config"): ExitCode.KERNEL_ERROR,
            LogAnalysisError("test", "syslog"): ExitCode.LOG_ANALYSIS_ERROR,
            DiagnosticsError("test", "system"): ExitCode.DIAGNOSTICS_ERROR,
        }
        
        for error, expected_code in error_exit_code_map.items():
            self.assertEqual(error.exit_code, expected_code)

    def test_error_handler_argument_validation_integration(self):
        """Test that argument validation is properly integrated."""
        from infenix.cli.error_handler import CLIErrorHandler, InvalidArgumentError
        from infenix.cli.formatters import OutputFormatter
        
        formatter = Mock(spec=OutputFormatter)
        error_handler = CLIErrorHandler(formatter)
        
        # Test invalid format
        args = Mock()
        args.format = 'invalid'
        
        with self.assertRaises(InvalidArgumentError):
            error_handler.validate_cli_arguments(args)

    def test_error_context_gathering(self):
        """Test that error context can be gathered successfully."""
        from infenix.cli.error_handler import CLIErrorHandler
        from infenix.cli.formatters import OutputFormatter
        
        formatter = Mock(spec=OutputFormatter)
        error_handler = CLIErrorHandler(formatter)
        
        context = error_handler.get_error_context()
        
        # Should always have a timestamp
        self.assertIn("timestamp", context)
        
        # Should have system info if gathering was successful
        if "error" not in context:
            self.assertIn("system", context)

    def test_user_friendly_error_formatting(self):
        """Test that errors are formatted in a user-friendly way."""
        from infenix.cli.error_handler import CLIErrorHandler
        from infenix.cli.formatters import OutputFormatter
        
        formatter = Mock(spec=OutputFormatter)
        error_handler = CLIErrorHandler(formatter)
        
        error = ValueError("Test error")
        formatted = error_handler.format_error_for_user(error, "test operation")
        
        self.assertIn("ValueError", formatted)
        self.assertIn("Test error", formatted)
        self.assertIn("test operation", formatted)


if __name__ == '__main__':
    unittest.main()