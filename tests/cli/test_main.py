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


import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add the parent directory to the path to import tinel modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tinel.cli.main import main, _validate_and_sanitize_argv, _execute_main_logic
from tinel.cli.config import CLIConfig


class TestArgumentValidation(unittest.TestCase):
    """Test argument validation and sanitization."""

    def test_validate_none_argv(self):
        """Test validation with None argv."""
        result = _validate_and_sanitize_argv(None)
        self.assertIsNone(result)

    def test_validate_empty_argv(self):
        """Test validation with empty argv."""
        result = _validate_and_sanitize_argv([])
        self.assertEqual(result, [])

    def test_validate_normal_argv(self):
        """Test validation with normal arguments."""
        argv = ["hardware", "cpu", "--verbose"]
        result = _validate_and_sanitize_argv(argv)
        self.assertEqual(result, ["hardware", "cpu", "--verbose"])

    def test_validate_argv_with_whitespace(self):
        """Test validation removes whitespace and empty strings."""
        argv = ["  hardware  ", "", "  cpu  ", "   ", "--verbose"]
        result = _validate_and_sanitize_argv(argv)
        self.assertEqual(result, ["hardware", "cpu", "--verbose"])

    def test_validate_too_many_arguments(self):
        """Test validation fails with too many arguments."""
        argv = ["arg"] * 101  # More than 100 arguments

        with self.assertRaises(ValueError) as cm:
            _validate_and_sanitize_argv(argv)

        self.assertIn("Too many arguments", str(cm.exception))

    def test_validate_non_string_argument(self):
        """Test validation fails with non-string arguments."""
        argv = ["hardware", 123, "cpu"]

        with self.assertRaises(ValueError) as cm:
            _validate_and_sanitize_argv(argv)

        self.assertIn("Invalid argument type", str(cm.exception))

    def test_validate_extremely_long_argument(self):
        """Test validation fails with extremely long arguments."""
        long_arg = "x" * 1001  # More than 1000 characters
        argv = ["hardware", long_arg]

        with self.assertRaises(ValueError) as cm:
            _validate_and_sanitize_argv(argv)

        self.assertIn("Argument too long", str(cm.exception))


class TestCLIConfig(unittest.TestCase):
    """Test CLI configuration management."""

    def test_config_from_args(self):
        """Test creating config from arguments."""
        args = Mock()
        args.format = "json"
        args.no_color = False
        args.verbose = 2
        args.quiet = False
        args.config = "/path/to/config"

        config = CLIConfig.from_args(args)

        self.assertEqual(config.format_type, "json")
        self.assertTrue(config.use_color)
        self.assertEqual(config.verbose, 2)
        self.assertFalse(config.quiet)
        self.assertEqual(config.config_file, "/path/to/config")

    def test_config_validation_success(self):
        """Test successful config validation."""
        config = CLIConfig(format_type="text", verbose=1, quiet=False)

        # Should not raise any exception
        config.validate()

    def test_config_validation_verbose_and_quiet(self):
        """Test config validation fails with both verbose and quiet."""
        config = CLIConfig(verbose=1, quiet=True)

        with self.assertRaises(ValueError) as cm:
            config.validate()

        self.assertIn("Cannot use both verbose and quiet", str(cm.exception))

    def test_config_validation_negative_verbosity(self):
        """Test config validation fails with negative verbosity."""
        config = CLIConfig(verbose=-1)

        with self.assertRaises(ValueError) as cm:
            config.validate()

        self.assertIn("Verbosity level cannot be negative", str(cm.exception))

    def test_config_validation_excessive_verbosity(self):
        """Test config validation fails with excessive verbosity."""
        config = CLIConfig(verbose=4)

        with self.assertRaises(ValueError) as cm:
            config.validate()

        self.assertIn("Maximum verbosity level is 3", str(cm.exception))

    def test_config_validation_invalid_format(self):
        """Test config validation fails with invalid format."""
        config = CLIConfig(format_type="invalid")

        with self.assertRaises(ValueError) as cm:
            config.validate()

        self.assertIn("Invalid format 'invalid'", str(cm.exception))

    def test_should_use_color_with_no_color_env(self):
        """Test color detection with NO_COLOR environment variable."""
        config = CLIConfig(use_color=True)

        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(config.should_use_color)

    def test_should_use_color_with_force_color_env(self):
        """Test color detection with FORCE_COLOR environment variable."""
        config = CLIConfig(use_color=False)

        with patch.dict(os.environ, {"FORCE_COLOR": "1"}):
            self.assertTrue(config.should_use_color)

    def test_log_level_mapping(self):
        """Test log level mapping based on verbosity."""
        test_cases = [
            (CLIConfig(quiet=True), "ERROR"),
            (CLIConfig(verbose=0), "WARNING"),
            (CLIConfig(verbose=1), "INFO"),
            (CLIConfig(verbose=2), "DEBUG"),
            (CLIConfig(verbose=3), "DEBUG"),
        ]

        for config, expected_level in test_cases:
            with self.subTest(config=config):
                self.assertEqual(config.log_level, expected_level)


class TestMainFunctionImprovements(unittest.TestCase):
    """Test improvements to the main function."""

    @patch("tinel.cli.main._execute_main_logic")
    def test_main_with_valid_arguments(self, mock_execute):
        """Test main function with valid arguments."""
        mock_execute.return_value = 0

        result = main(["hardware", "cpu"])

        self.assertEqual(result, 0)
        mock_execute.assert_called_once_with(["hardware", "cpu"])

    def test_main_with_invalid_arguments(self):
        """Test main function with invalid arguments."""
        # Test with too many arguments
        long_argv = ["arg"] * 101

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = main(long_argv)

        self.assertEqual(result, 1)
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Too many arguments", stderr_output)

    @patch("tinel.cli.main._execute_main_logic")
    def test_main_keyboard_interrupt(self, mock_execute):
        """Test main function handles KeyboardInterrupt."""
        mock_execute.side_effect = KeyboardInterrupt()

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = main(["hardware"])

        self.assertEqual(result, 130)
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Operation cancelled by user", stderr_output)

    @patch("tinel.cli.main._execute_main_logic")
    def test_main_system_exit_with_code(self, mock_execute):
        """Test main function handles SystemExit with code."""
        mock_execute.side_effect = SystemExit(42)

        result = main(["hardware"])

        self.assertEqual(result, 42)

    @patch("tinel.cli.main._execute_main_logic")
    def test_main_system_exit_with_none_code(self, mock_execute):
        """Test main function handles SystemExit with None code."""
        mock_execute.side_effect = SystemExit(None)

        result = main(["hardware"])

        self.assertEqual(result, 0)

    @patch("tinel.cli.main._execute_main_logic")
    def test_main_unexpected_exception(self, mock_execute):
        """Test main function handles unexpected exceptions."""
        mock_execute.side_effect = ValueError("Test error")

        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            result = main(["hardware"])

        self.assertEqual(result, 1)
        stderr_output = mock_stderr.getvalue()
        self.assertIn("Fatal error: Test error", stderr_output)
        self.assertIn("internal error", stderr_output)


class TestPerformanceMonitoring(unittest.TestCase):
    """Test performance monitoring features."""

    @patch("tinel.cli.main.parse_arguments")
    @patch("tinel.cli.main.CLIConfig")
    @patch("tinel.cli.main.setup_logging")
    @patch("tinel.cli.main.OutputFormatter")
    @patch("tinel.cli.main.CLIErrorHandler")
    @patch("tinel.cli.main._get_command_router")
    @patch("time.time")
    def test_execution_time_logging(
        self,
        mock_time,
        mock_get_router,
        mock_error_handler_class,
        mock_formatter_class,
        mock_setup_logging,
        mock_config_class,
        mock_parse_args,
    ):
        """Test that execution time is logged."""
        # Setup mocks
        mock_time.side_effect = [1000.0, 1001.5]  # Start and end times

        mock_args = Mock()
        mock_args.command = "hardware"
        mock_parse_args.return_value = mock_args

        mock_config = Mock()
        mock_config.validate.return_value = None
        mock_config_class.from_args.return_value = mock_config

        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter

        mock_error_handler = Mock()
        mock_error_handler_class.return_value = mock_error_handler

        mock_router = Mock()
        mock_router.execute_command.return_value = 0
        mock_get_router.return_value = mock_router

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = _execute_main_logic(["hardware"])

        self.assertEqual(result, 0)

        # Check that timing was logged
        mock_logger.info.assert_any_call("CLI execution started with command: hardware")
        mock_logger.info.assert_any_call(
            "CLI execution completed successfully in 1.500s"
        )


class TestLazyLoading(unittest.TestCase):
    """Test lazy loading functionality."""

    @patch("tinel.cli.main.CommandRouter")
    def test_lazy_command_router_loading(self, mock_router_class):
        """Test that CommandRouter is loaded lazily."""
        from tinel.cli.main import _get_command_router

        formatter = Mock()
        error_handler = Mock()
        mock_router = Mock()
        mock_router_class.return_value = mock_router

        result = _get_command_router(formatter, error_handler)

        self.assertEqual(result, mock_router)
        mock_router_class.assert_called_once_with(formatter, error_handler)


class TestSecurityImprovements(unittest.TestCase):
    """Test security-related improvements."""

    def test_argument_length_validation(self):
        """Test that extremely long arguments are rejected."""
        long_arg = "x" * 1001
        argv = ["hardware", long_arg]

        with self.assertRaises(ValueError) as cm:
            _validate_and_sanitize_argv(argv)

        self.assertIn("Argument too long", str(cm.exception))
        # Should include truncated preview
        self.assertIn("xxx...", str(cm.exception))

    def test_argument_type_validation(self):
        """Test that non-string arguments are rejected."""
        argv = ["hardware", {"malicious": "dict"}, "cpu"]

        with self.assertRaises(ValueError) as cm:
            _validate_and_sanitize_argv(argv)

        self.assertIn("Invalid argument type: dict", str(cm.exception))

    def test_argument_count_validation(self):
        """Test that excessive argument counts are rejected."""
        argv = ["arg"] * 101

        with self.assertRaises(ValueError) as cm:
            _validate_and_sanitize_argv(argv)

        self.assertIn("Too many arguments provided (maximum: 100)", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
