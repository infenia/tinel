import unittest
from unittest.mock import Mock

from tinel.cli.commands.base import BaseCommand
from tinel.cli.error_handler import (
    CLIError,
    DiagnosticsError,
    HardwareError,
    KernelError,
    LogAnalysisError,
)


class TestBaseCommand(unittest.TestCase):
    def setUp(self):
        class ConcreteCommand(BaseCommand):
            def execute(self, args):  # type: ignore
                pass

        self.mock_formatter = Mock()
        self.mock_error_handler = Mock()
        self.base_command = ConcreteCommand(
            self.mock_formatter, self.mock_error_handler
        )

    def test_handle_tool_error_cli_error_re_raise(self):
        # Test when the error is already a CLIError, ensuring it's re-raised
        cli_error = CLIError("Test CLI Error")
        with self.assertRaises(CLIError) as cm:
            self.base_command._handle_tool_error(cli_error, "test_tool")
        self.assertEqual(str(cm.exception), "Test CLI Error")

    def test_handle_tool_error_generic_exception_default_cli_error(self):
        # Test when a generic exception is raised, and it falls through to
        # the default CLIError
        generic_error = ValueError("Some unexpected error")
        with self.assertRaises(CLIError) as cm:
            self.base_command._handle_tool_error(generic_error, "unmapped_tool")
        self.assertEqual(
            str(cm.exception),
            "Tool 'unmapped_tool' execution failed: Some unexpected error",
        )

    def test_handle_tool_error_hardware_error(self):
        # Test mapping to HardwareError
        generic_error = Exception("Hardware issue")
        for tool_name in [
            "cpu_tool",
            "memory_tool",
            "storage_tool",
            "pci_tool",
            "usb_tool",
            "network_tool",
            "graphics_tool",
            "hardware_tool",
        ]:
            with self.assertRaises(HardwareError) as cm:
                self.base_command._handle_tool_error(generic_error, tool_name)
            self.assertIn("Hardware analysis failed", str(cm.exception))
            self.assertIn("Hardware issue", str(cm.exception))

    def test_handle_tool_error_kernel_error(self):
        # Test mapping to KernelError
        generic_error = Exception("Kernel panic")
        for tool_name in ["kernel_tool", "config_tool"]:
            with self.assertRaises(KernelError) as cm:
                self.base_command._handle_tool_error(generic_error, tool_name)
            self.assertIn("Kernel analysis failed", str(cm.exception))
            self.assertIn("Kernel panic", str(cm.exception))

    def test_handle_tool_error_log_analysis_error(self):
        # Test mapping to LogAnalysisError and the specific error message for logs
        generic_error = Exception("Log parsing failed")
        tool_name = "log_tool"
        with self.assertRaises(LogAnalysisError) as cm:
            self.base_command._handle_tool_error(generic_error, tool_name)
        self.assertEqual(str(cm.exception), "Log analysis failed: Log parsing failed")

    def test_handle_tool_error_diagnostics_error(self):
        # Test mapping to DiagnosticsError
        generic_error = Exception("Diagnostic failed")
        for tool_name in ["diagnose_tool", "diagnostic_tool"]:
            with self.assertRaises(DiagnosticsError) as cm:
                self.base_command._handle_tool_error(generic_error, tool_name)
            self.assertIn("Diagnostics analysis failed", str(cm.exception))
            self.assertIn("Diagnostic failed", str(cm.exception))

    def test_handle_tool_error_unknown_tool(self):
        # Test when tool name does not match any specific error type
        generic_error = Exception("Unknown error occurred")
        with self.assertRaises(CLIError) as cm:
            self.base_command._handle_tool_error(generic_error, "unknown_tool")
        self.assertEqual(
            str(cm.exception),
            "Tool 'unknown_tool' execution failed: Unknown error occurred",
        )

    def test_execute_tool_success(self):
        mock_tool_provider = Mock()
        mock_tool_provider.get_tool_name.return_value = "test_tool"
        mock_tool_provider.execute.return_value = {"success": True, "data": "some_data"}

        result = self.base_command._execute_tool(mock_tool_provider, {"param": "value"})
        self.assertEqual(result, {"success": True, "data": "some_data"})
        self.mock_formatter.print_debug.assert_called_with("Executing tool: test_tool")
        mock_tool_provider.execute.assert_called_with({"param": "value"})

    def test_execute_tool_failure_from_tool_provider_with_error_message(self):
        mock_tool_provider = Mock()
        mock_tool_provider.get_tool_name.return_value = "failing_tool"
        mock_tool_provider.execute.return_value = {
            "success": False,
            "error": "Tool internal error",
        }

        with self.assertRaises(CLIError) as cm:
            self.base_command._execute_tool(mock_tool_provider, {})
        self.assertEqual(
            str(cm.exception),
            "Tool 'failing_tool' execution failed: Tool internal error",
        )

    def test_execute_tool_failure_from_tool_provider_without_error_message(self):
        mock_tool_provider = Mock()
        mock_tool_provider.get_tool_name.return_value = "failing_tool_no_msg"
        mock_tool_provider.execute.return_value = {"success": False}

        with self.assertRaises(CLIError) as cm:
            self.base_command._execute_tool(mock_tool_provider, {})
        self.assertEqual(
            str(cm.exception),
            "Tool 'failing_tool_no_msg' execution failed: Unknown error",
        )

    def test_execute_tool_exception_during_execution(self):
        mock_tool_provider = Mock()
        mock_tool_provider.get_tool_name.return_value = "exception_tool"
        mock_tool_provider.execute.side_effect = ValueError(
            "Execution failed unexpectedly"
        )

        with self.assertRaises(CLIError) as cm:
            self.base_command._execute_tool(mock_tool_provider, {})
        self.assertEqual(
            str(cm.exception),
            "Tool 'exception_tool' execution failed: Execution failed unexpectedly",
        )

    def test_execute_tool_exception_handle_tool_error_no_raise(self):
        """Test _execute_tool when _handle_tool_error doesn't raise."""
        mock_tool_provider = Mock()
        mock_tool_provider.get_tool_name.return_value = "exception_tool"
        mock_tool_provider.execute.side_effect = ValueError("Test error")

        # Mock _handle_tool_error to not raise exception
        self.base_command._handle_tool_error = Mock()

        result = self.base_command._execute_tool(mock_tool_provider, {})
        assert result == {}
        self.base_command._handle_tool_error.assert_called_once()


if __name__ == "__main__":
    unittest.main()
