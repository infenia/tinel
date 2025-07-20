#!/usr/bin/env python3
"""Unit tests for CLI output formatters.

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
import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch, MagicMock

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from infenix.cli.formatters import OutputFormatter, FormatType, Color


class TestOutputFormatter(unittest.TestCase):
    """Test cases for OutputFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = {
            'cpu': {
                'model': 'Intel Core i7-9700K',
                'cores': 8,
                'frequency': 3.6,
                'features': ['sse', 'avx', 'avx2']
            },
            'memory': {
                'total': '16GB',
                'available': '8GB',
                'type': 'DDR4'
            },
            'status': 'healthy'
        }
        
        self.test_list = [
            {'name': 'device1', 'status': 'ok'},
            {'name': 'device2', 'status': 'error'},
            {'name': 'device3', 'status': 'warning'}
        ]
    
    def test_init_default_values(self):
        """Test formatter initialization with default values."""
        formatter = OutputFormatter()
        
        self.assertEqual(formatter.format_type, FormatType.TEXT)
        self.assertEqual(formatter.verbose, 0)
        self.assertFalse(formatter.quiet)
        self.assertEqual(formatter.output_file, sys.stdout)
    
    def test_init_custom_values(self):
        """Test formatter initialization with custom values."""
        output_file = StringIO()
        formatter = OutputFormatter(
            format_type='json',
            use_color=False,
            verbose=2,
            quiet=True,
            output_file=output_file
        )
        
        self.assertEqual(formatter.format_type, FormatType.JSON)
        self.assertFalse(formatter.use_color)
        self.assertEqual(formatter.verbose, 2)
        self.assertTrue(formatter.quiet)
        self.assertEqual(formatter.output_file, output_file)
    
    def test_format_type_validation(self):
        """Test format type validation."""
        # Valid format types
        for format_type in ['text', 'json', 'yaml']:
            formatter = OutputFormatter(format_type=format_type)
            self.assertEqual(formatter.format_type.value, format_type)
        
        # Invalid format type should raise ValueError
        with self.assertRaises(ValueError):
            OutputFormatter(format_type='invalid')
    
    @patch('sys.stdout.isatty')
    def test_supports_color_tty(self, mock_isatty):
        """Test color support detection for TTY."""
        mock_isatty.return_value = True
        
        formatter = OutputFormatter()
        self.assertTrue(formatter._supports_color())
    
    @patch('sys.stdout.isatty')
    def test_supports_color_no_tty(self, mock_isatty):
        """Test color support detection for non-TTY."""
        mock_isatty.return_value = False
        
        formatter = OutputFormatter()
        self.assertFalse(formatter._supports_color())
    
    @patch.dict(os.environ, {'NO_COLOR': '1'})
    @patch('sys.stdout.isatty')
    def test_supports_color_no_color_env(self, mock_isatty):
        """Test color support with NO_COLOR environment variable."""
        mock_isatty.return_value = True
        
        formatter = OutputFormatter()
        self.assertFalse(formatter._supports_color())
    
    @patch.dict(os.environ, {'FORCE_COLOR': '1'})
    @patch('sys.stdout.isatty')
    def test_supports_color_force_color_env(self, mock_isatty):
        """Test color support with FORCE_COLOR environment variable."""
        mock_isatty.return_value = False
        
        formatter = OutputFormatter()
        self.assertTrue(formatter._supports_color())
    
    @patch('sys.stdout.isatty')
    def test_colorize_with_color(self, mock_isatty):
        """Test colorize method with color enabled."""
        mock_isatty.return_value = True
        formatter = OutputFormatter(use_color=True)
        
        result = formatter.colorize("test", Color.RED)
        expected = f"{Color.RED}test{Color.RESET}"
        self.assertEqual(result, expected)
    
    def test_colorize_without_color(self):
        """Test colorize method with color disabled."""
        formatter = OutputFormatter(use_color=False)
        
        result = formatter.colorize("test", Color.RED)
        self.assertEqual(result, "test")
    
    def test_format_json(self):
        """Test JSON formatting."""
        formatter = OutputFormatter(format_type='json')
        
        result = formatter.format_output(self.test_data)
        
        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed, self.test_data)
        
        # Should be pretty-printed (indented)
        self.assertIn('\n', result)
        self.assertIn('  ', result)
    
    @unittest.skipUnless(YAML_AVAILABLE, "PyYAML not available")
    def test_format_yaml(self):
        """Test YAML formatting."""
        formatter = OutputFormatter(format_type='yaml')
        
        result = formatter.format_output(self.test_data)
        
        # Should be valid YAML
        parsed = yaml.safe_load(result)
        self.assertEqual(parsed, self.test_data)
    
    @unittest.skipIf(YAML_AVAILABLE, "PyYAML is available")
    def test_format_yaml_not_available(self):
        """Test YAML formatting when PyYAML is not available."""
        formatter = OutputFormatter(format_type='yaml')
        
        with self.assertRaises(RuntimeError) as cm:
            formatter.format_output(self.test_data)
        
        self.assertIn("PyYAML", str(cm.exception))
    
    def test_format_text_with_title(self):
        """Test text formatting with title."""
        formatter = OutputFormatter(format_type='text', use_color=False)
        
        result = formatter.format_output(self.test_data, "Test Title")
        
        self.assertIn("Test Title", result)
        self.assertIn("=", result)  # Title underline
        self.assertIn("cpu:", result)
        self.assertIn("Intel Core i7-9700K", result)
    
    def test_format_text_without_title(self):
        """Test text formatting without title."""
        formatter = OutputFormatter(format_type='text', use_color=False)
        
        result = formatter.format_output(self.test_data)
        
        self.assertIn("cpu:", result)
        self.assertIn("Intel Core i7-9700K", result)
        self.assertNotIn("=", result)  # No title underline
    
    def test_format_text_quiet_mode(self):
        """Test text formatting in quiet mode."""
        formatter = OutputFormatter(format_type='text', quiet=True, use_color=False)
        
        result = formatter.format_output(self.test_data, "Test Title")
        
        # Should not include title in quiet mode
        self.assertNotIn("Test Title", result)
        # Should not include title underline (multiple equals signs)
        self.assertNotIn("====", result)
        
        # Should use minimal format
        self.assertIn("cpu.model=Intel Core i7-9700K", result)
        self.assertIn("cpu.cores=8", result)
    
    def test_format_text_verbose_mode(self):
        """Test text formatting in verbose mode."""
        formatter = OutputFormatter(format_type='text', verbose=2, use_color=False)
        
        result = formatter.format_output(self.test_data, "Test Title")
        
        self.assertIn("Verbose Information:", result)
        self.assertIn("Data type: dict", result)
        self.assertIn("Number of keys:", result)
        self.assertIn("Keys:", result)
    
    def test_format_minimal_dict(self):
        """Test minimal dictionary formatting."""
        formatter = OutputFormatter(format_type='text', quiet=True, use_color=False)
        
        result = formatter._format_minimal_dict(self.test_data)
        
        expected_lines = [
            "cpu.model=Intel Core i7-9700K",
            "cpu.cores=8",
            "cpu.frequency=3.6",
            "cpu.features[0]=sse",
            "cpu.features[1]=avx",
            "cpu.features[2]=avx2",
            "memory.total=16GB",
            "memory.available=8GB",
            "memory.type=DDR4",
            "status=healthy"
        ]
        
        for line in expected_lines:
            self.assertIn(line, result)
    
    def test_format_minimal_list(self):
        """Test minimal list formatting."""
        formatter = OutputFormatter(format_type='text', quiet=True, use_color=False)
        
        result = formatter._format_minimal_list(self.test_list)
        
        expected_lines = [
            "[0].name=device1",
            "[0].status=ok",
            "[1].name=device2",
            "[1].status=error",
            "[2].name=device3",
            "[2].status=warning"
        ]
        
        for line in expected_lines:
            self.assertIn(line, result)
    
    @patch('sys.stdout.isatty')
    def test_format_value_colors(self, mock_isatty):
        """Test value formatting with colors."""
        mock_isatty.return_value = True
        formatter = OutputFormatter(use_color=True)
        
        # Test boolean values
        self.assertIn(Color.GREEN, formatter._format_value(True))
        self.assertIn(Color.RED, formatter._format_value(False))
        
        # Test numeric values
        self.assertIn(Color.CYAN, formatter._format_value(42))
        self.assertIn(Color.CYAN, formatter._format_value(3.14))
        
        # Test status values
        self.assertIn(Color.GREEN, formatter._format_value("ok"))
        self.assertIn(Color.GREEN, formatter._format_value("healthy"))
        self.assertIn(Color.RED, formatter._format_value("error"))
        self.assertIn(Color.RED, formatter._format_value("failed"))
        self.assertIn(Color.YELLOW, formatter._format_value("warning"))
    
    def test_format_with_explanation(self):
        """Test formatting with explanation."""
        formatter = OutputFormatter(verbose=1, use_color=False)
        explanation = "This is a test explanation that provides context."
        
        result = formatter.format_with_explanation(self.test_data, explanation, "Test")
        
        self.assertIn("Test", result)
        self.assertIn("cpu:", result)
        self.assertIn("Explanation:", result)
        self.assertIn(explanation, result)
    
    def test_format_with_explanation_quiet(self):
        """Test formatting with explanation in quiet mode."""
        formatter = OutputFormatter(verbose=1, quiet=True, use_color=False)
        explanation = "This explanation should not appear."
        
        result = formatter.format_with_explanation(self.test_data, explanation, "Test")
        
        self.assertNotIn("Explanation:", result)
        self.assertNotIn(explanation, result)
    
    def test_format_with_explanation_not_verbose(self):
        """Test formatting with explanation when not verbose."""
        formatter = OutputFormatter(verbose=0, use_color=False)
        explanation = "This explanation should not appear."
        
        result = formatter.format_with_explanation(self.test_data, explanation, "Test")
        
        self.assertNotIn("Explanation:", result)
        self.assertNotIn(explanation, result)
    
    def test_format_with_long_explanation(self):
        """Test formatting with long explanation that needs wrapping."""
        formatter = OutputFormatter(verbose=1, use_color=False)
        explanation = "This is a very long explanation that should be wrapped because it exceeds the 80 character limit and should be broken into multiple lines for better readability."
        
        result = formatter.format_with_explanation(self.test_data, explanation, "Test")
        
        self.assertIn("Explanation:", result)
        # Check that the explanation is wrapped
        lines = result.split('\n')
        explanation_lines = [line for line in lines if line and not line.startswith(('Test', '=', 'cpu:', 'memory:', 'status:', 'Explanation:', '-'))]
        
        # Should have multiple lines due to wrapping
        self.assertGreater(len(explanation_lines), 1)
        
        # Each line should be reasonably short
        for line in explanation_lines:
            self.assertLessEqual(len(line), 85)  # Allow some margin
    
    def test_print_output(self):
        """Test print_output method."""
        output_file = StringIO()
        formatter = OutputFormatter(format_type='json', output_file=output_file)
        
        formatter.print_output(self.test_data, "Test")
        
        output = output_file.getvalue()
        self.assertIn('"cpu"', output)
        self.assertIn('"Intel Core i7-9700K"', output)
    
    def test_print_output_quiet(self):
        """Test print_output method in quiet mode."""
        output_file = StringIO()
        formatter = OutputFormatter(quiet=True, output_file=output_file)
        
        formatter.print_output(self.test_data, "Test")
        
        output = output_file.getvalue()
        self.assertEqual(output, "")
    
    def test_print_output_with_explanation(self):
        """Test print_output_with_explanation method."""
        output_file = StringIO()
        formatter = OutputFormatter(verbose=1, use_color=False, output_file=output_file)
        
        formatter.print_output_with_explanation(self.test_data, "Test explanation", "Test")
        
        output = output_file.getvalue()
        self.assertIn("cpu:", output)
        self.assertIn("Explanation:", output)
        self.assertIn("Test explanation", output)
    
    def test_print_error(self):
        """Test print_error method."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            formatter = OutputFormatter(use_color=False)
            
            formatter.print_error("Test error message")
            
            output = mock_stderr.getvalue()
            self.assertIn("Error: Test error message", output)
    
    def test_print_warning(self):
        """Test print_warning method."""
        output_file = StringIO()
        formatter = OutputFormatter(use_color=False, output_file=output_file)
        
        formatter.print_warning("Test warning message")
        
        output = output_file.getvalue()
        self.assertIn("Warning: Test warning message", output)
    
    def test_print_warning_quiet(self):
        """Test print_warning method in quiet mode."""
        output_file = StringIO()
        formatter = OutputFormatter(quiet=True, output_file=output_file)
        
        formatter.print_warning("Test warning message")
        
        output = output_file.getvalue()
        self.assertEqual(output, "")
    
    def test_print_info(self):
        """Test print_info method."""
        output_file = StringIO()
        formatter = OutputFormatter(verbose=1, use_color=False, output_file=output_file)
        
        formatter.print_info("Test info message")
        
        output = output_file.getvalue()
        self.assertIn("Info: Test info message", output)
    
    def test_print_info_not_verbose(self):
        """Test print_info method when not verbose."""
        output_file = StringIO()
        formatter = OutputFormatter(verbose=0, output_file=output_file)
        
        formatter.print_info("Test info message")
        
        output = output_file.getvalue()
        self.assertEqual(output, "")
    
    def test_print_debug(self):
        """Test print_debug method."""
        output_file = StringIO()
        formatter = OutputFormatter(verbose=2, use_color=False, output_file=output_file)
        
        formatter.print_debug("Test debug message")
        
        output = output_file.getvalue()
        self.assertIn("Debug: Test debug message", output)
    
    def test_print_debug_not_verbose_enough(self):
        """Test print_debug method when not verbose enough."""
        output_file = StringIO()
        formatter = OutputFormatter(verbose=1, output_file=output_file)
        
        formatter.print_debug("Test debug message")
        
        output = output_file.getvalue()
        self.assertEqual(output, "")
    
    def test_print_success(self):
        """Test print_success method."""
        output_file = StringIO()
        formatter = OutputFormatter(use_color=False, output_file=output_file)
        
        formatter.print_success("Test success message")
        
        output = output_file.getvalue()
        self.assertIn("✓ Test success message", output)
    
    def test_print_success_quiet(self):
        """Test print_success method in quiet mode."""
        output_file = StringIO()
        formatter = OutputFormatter(quiet=True, output_file=output_file)
        
        formatter.print_success("Test success message")
        
        output = output_file.getvalue()
        self.assertEqual(output, "")
    
    def test_format_table(self):
        """Test format_table method."""
        formatter = OutputFormatter(use_color=False)
        
        data = [
            {'name': 'device1', 'status': 'ok', 'type': 'cpu'},
            {'name': 'device2', 'status': 'error', 'type': 'memory'},
            {'name': 'device3', 'status': 'warning', 'type': 'storage'}
        ]
        headers = ['name', 'status', 'type']
        
        result = formatter.format_table(data, headers)
        
        # Check headers
        self.assertIn('name', result)
        self.assertIn('status', result)
        self.assertIn('type', result)
        
        # Check data
        self.assertIn('device1', result)
        self.assertIn('device2', result)
        self.assertIn('device3', result)
        self.assertIn('ok', result)
        self.assertIn('error', result)
        self.assertIn('warning', result)
        
        # Check table structure
        self.assertIn('|', result)  # Column separators
        self.assertIn('-', result)  # Header separator
    
    def test_format_table_list_data(self):
        """Test format_table method with list data."""
        formatter = OutputFormatter(use_color=False)
        
        data = [
            ['device1', 'ok', 'cpu'],
            ['device2', 'error', 'memory'],
            ['device3', 'warning', 'storage']
        ]
        headers = ['name', 'status', 'type']
        
        result = formatter.format_table(data, headers)
        
        self.assertIn('device1', result)
        self.assertIn('ok', result)
        self.assertIn('cpu', result)
    
    def test_format_table_empty_data(self):
        """Test format_table method with empty data."""
        formatter = OutputFormatter()
        
        result = formatter.format_table([], ['name', 'status'])
        
        self.assertEqual(result, "No data to display")
    
    def test_format_table_column_width_calculation(self):
        """Test format_table column width calculation."""
        formatter = OutputFormatter(use_color=False)
        
        data = [
            {'name': 'very_long_device_name', 'status': 'ok'},
            {'name': 'short', 'status': 'error_with_long_status'}
        ]
        headers = ['name', 'status']
        
        result = formatter.format_table(data, headers)
        
        # Should handle different column widths properly
        lines = result.split('\n')
        header_line = lines[0]
        separator_line = lines[1]
        
        # All lines should have consistent column alignment
        self.assertGreater(len(header_line), 20)  # Should be wide enough
        self.assertGreater(len(separator_line), 20)


class TestFormatType(unittest.TestCase):
    """Test cases for FormatType enum."""
    
    def test_format_type_values(self):
        """Test FormatType enum values."""
        self.assertEqual(FormatType.TEXT.value, 'text')
        self.assertEqual(FormatType.JSON.value, 'json')
        self.assertEqual(FormatType.YAML.value, 'yaml')
    
    def test_format_type_from_string(self):
        """Test creating FormatType from string."""
        self.assertEqual(FormatType('text'), FormatType.TEXT)
        self.assertEqual(FormatType('json'), FormatType.JSON)
        self.assertEqual(FormatType('yaml'), FormatType.YAML)


class TestColor(unittest.TestCase):
    """Test cases for Color class."""
    
    def test_color_constants(self):
        """Test Color constants are defined."""
        self.assertTrue(hasattr(Color, 'RESET'))
        self.assertTrue(hasattr(Color, 'RED'))
        self.assertTrue(hasattr(Color, 'GREEN'))
        self.assertTrue(hasattr(Color, 'YELLOW'))
        self.assertTrue(hasattr(Color, 'BLUE'))
        self.assertTrue(hasattr(Color, 'MAGENTA'))
        self.assertTrue(hasattr(Color, 'CYAN'))
        self.assertTrue(hasattr(Color, 'WHITE'))
        
        # Test that they are strings
        self.assertIsInstance(Color.RESET, str)
        self.assertIsInstance(Color.RED, str)
        self.assertIsInstance(Color.GREEN, str)
    
    def test_color_ansi_codes(self):
        """Test Color ANSI codes are correct."""
        self.assertEqual(Color.RESET, '\033[0m')
        self.assertEqual(Color.RED, '\033[31m')
        self.assertEqual(Color.GREEN, '\033[32m')
        self.assertEqual(Color.YELLOW, '\033[33m')
        self.assertEqual(Color.BLUE, '\033[34m')


if __name__ == '__main__':
    unittest.main()