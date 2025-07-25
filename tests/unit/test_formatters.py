#!/usr/bin/env python3
"""
Unit tests for output formatters.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import json
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from tinel.cli.formatters import (
    OutputFormatter, Color, FormatType, ColorUtility,
    JSONFormatter, TextFormatter, CSVFormatter, TableFormatter
)
from tests.utils import unit_test, AssertionHelpers


class TestColorUtility:
    """Test cases for ColorUtility."""
    
    @unit_test
    def test_colorize_with_color_enabled(self):
        """Test colorizing text with color enabled."""
        with patch.object(ColorUtility, '_supports_color', return_value=True):
            colorizer = ColorUtility(use_color=True)
            result = colorizer.colorize("test text", Color.RED)
            expected = f"{Color.RED}test text{Color.RESET}"
            assert result == expected
            
    @unit_test
    def test_colorize_with_color_disabled(self):
        """Test colorizing text with color disabled."""
        colorizer = ColorUtility(use_color=False)
        
        result = colorizer.colorize("test text", Color.RED)
        assert result == "test text"
        
    @unit_test
    def test_supports_color_no_color_env(self):
        """Test color support detection with NO_COLOR environment."""
        colorizer = ColorUtility(use_color=True)
        
        with patch.dict('os.environ', {'NO_COLOR': '1'}):
            assert colorizer._supports_color() is False
            
    @unit_test
    def test_supports_color_force_color_env(self):
        """Test color support detection with FORCE_COLOR environment."""
        colorizer = ColorUtility(use_color=False)
        
        with patch.dict('os.environ', {'FORCE_COLOR': '1'}):
            assert colorizer._supports_color() is True
            
    @unit_test
    def test_supports_color_tty_detection(self):
        """Test color support detection based on TTY."""
        colorizer = ColorUtility()
        
        with patch('sys.stdout.isatty', return_value=True):
            with patch('os.environ.get', return_value=None):  # No NO_COLOR or FORCE_COLOR
                # Should support color on TTY when stdout.isatty() returns True
                result = colorizer._supports_color()
                # Result depends on platform, just ensure it's boolean
                assert isinstance(result, bool)


class TestJSONFormatter:
    """Test cases for JSONFormatter."""
    
    @unit_test
    def test_format_simple_dict(self):
        """Test formatting simple dictionary as JSON."""
        formatter = JSONFormatter()
        data = {"key": "value", "number": 42}
        
        result = formatter.format(data)
        parsed = json.loads(result)
        
        assert parsed == data
        
    @unit_test
    def test_format_with_special_characters(self):
        """Test formatting data with special characters."""
        formatter = JSONFormatter()
        data = {"unicode": "测试", "newlines": "line1\nline2"}
        
        result = formatter.format(data)
        parsed = json.loads(result)
        
        assert parsed == data
        
    @unit_test
    def test_format_with_title_ignored(self):
        """Test that title parameter is ignored for JSON."""
        formatter = JSONFormatter()
        data = {"test": "data"}
        
        result = formatter.format(data, title="Test Title")
        parsed = json.loads(result)
        
        # Title should not appear in JSON output
        assert parsed == data
        assert "Test Title" not in result


class TestCSVFormatter:
    """Test cases for CSVFormatter."""
    
    @unit_test
    def test_format_simple_dict(self):
        """Test formatting simple dictionary as CSV."""
        formatter = CSVFormatter()
        data = {"name": "test", "value": 42}
        
        result = formatter.format(data)
        lines = result.strip().split('\n')
        
        # Handle CSV line endings (may have \r)
        lines = [line.rstrip('\r') for line in lines]
        
        assert lines[0] == "key,value"
        assert "name,test" in lines
        assert "value,42" in lines
        
    @unit_test
    def test_format_list_of_dicts(self):
        """Test formatting list of dictionaries as CSV."""
        formatter = CSVFormatter()
        data = [
            {"name": "item1", "value": 10},
            {"name": "item2", "value": 20}
        ]
        
        result = formatter.format(data)
        lines = result.strip().split('\n')
        
        # Handle CSV line endings (may have \r)
        lines = [line.rstrip('\r') for line in lines]
        
        assert lines[0] == "name,value"
        assert lines[1] == "item1,10" 
        assert lines[2] == "item2,20"
        
    @unit_test
    def test_format_nested_dict(self):
        """Test formatting nested dictionary as CSV."""
        formatter = CSVFormatter()
        data = {
            "system": {"cpu": "Intel", "ram": "16GB"},
            "status": "active"
        }
        
        result = formatter.format(data)
        lines = result.strip().split('\n')
        
        # Handle CSV line endings (may have \r)
        lines = [line.rstrip('\r') for line in lines]
        
        assert lines[0] == "key,value"
        # Should flatten nested structure
        assert any("system.cpu,Intel" in line for line in lines)
        assert any("system.ram,16GB" in line for line in lines)
        
    @unit_test
    def test_format_empty_list(self):
        """Test formatting empty list."""
        formatter = CSVFormatter()
        result = formatter.format([])
        assert result == ""


class TestTextFormatter:
    """Test cases for TextFormatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.colorizer = Mock()
        self.colorizer.colorize.side_effect = lambda text, color: text
        
    @unit_test
    def test_format_simple_dict(self):
        """Test formatting simple dictionary as text."""
        formatter = TextFormatter(self.colorizer, quiet=False, verbose=0)
        data = {"name": "test", "value": 42}
        
        result = formatter.format(data)
        
        assert "name:" in result
        assert "test" in result
        assert "value:" in result
        assert "42" in result
        
    @unit_test
    def test_format_with_title(self):
        """Test formatting with title."""
        formatter = TextFormatter(self.colorizer, quiet=False, verbose=0)
        data = {"test": "data"}
        
        result = formatter.format(data, title="Test Title")
        
        assert "Test Title" in result
        # Should have separator line
        assert "=" in result
        
    @unit_test
    def test_format_quiet_mode(self):
        """Test formatting in quiet mode."""
        formatter = TextFormatter(self.colorizer, quiet=True, verbose=0)
        data = {"name": "test", "value": 42}
        
        result = formatter.format(data)
        
        # Should be minimal format
        assert "name=test" in result
        assert "value=42" in result
        
    @unit_test
    def test_format_nested_dict(self):
        """Test formatting nested dictionary."""
        formatter = TextFormatter(self.colorizer, quiet=False, verbose=0)
        data = {
            "system": {
                "cpu": "Intel",
                "memory": "16GB"
            },
            "status": "running"
        }
        
        result = formatter.format(data)
        
        assert "system:" in result
        assert "cpu:" in result
        assert "Intel" in result
        assert "memory:" in result
        assert "16GB" in result
        assert "status:" in result
        assert "running" in result
        
    @unit_test
    def test_format_list(self):
        """Test formatting list data."""
        formatter = TextFormatter(self.colorizer, quiet=False, verbose=0)
        data = ["item1", "item2", "item3"]
        
        result = formatter.format(data)
        
        for item in data:
            assert item in result
            
    @unit_test
    def test_verbose_info(self):
        """Test verbose information inclusion."""
        formatter = TextFormatter(self.colorizer, quiet=False, verbose=2)
        data = {"test": "data"}
        
        result = formatter.format(data)
        
        assert "Verbose Information:" in result
        assert "Data type:" in result
        assert "Number of keys:" in result


class TestTableFormatter:
    """Test cases for TableFormatter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.colorizer = Mock()
        self.colorizer.colorize.side_effect = lambda text, color: text
        self.formatter = TableFormatter(self.colorizer)
        
    @unit_test
    def test_format_table_with_dicts(self):
        """Test formatting table with dictionary rows."""
        data = [
            {"name": "item1", "value": 10, "status": "active"},
            {"name": "item2", "value": 20, "status": "inactive"}
        ]
        headers = ["name", "value", "status"]
        
        result = self.formatter.format_table(data, headers)
        
        # Check headers
        assert "name" in result
        assert "value" in result
        assert "status" in result
        
        # Check data
        assert "item1" in result
        assert "item2" in result
        assert "10" in result
        assert "20" in result
        
        # Check structure (should have separator)
        lines = result.split('\n')
        assert len(lines) >= 3  # Header + separator + at least 1 data row
        
    @unit_test
    def test_format_table_with_lists(self):
        """Test formatting table with list rows."""
        data = [
            ["item1", 10, "active"],
            ["item2", 20, "inactive"]
        ]
        headers = ["name", "value", "status"]
        
        result = self.formatter.format_table(data, headers)
        
        assert "item1" in result
        assert "item2" in result
        assert "10" in result
        assert "20" in result
        
    @unit_test
    def test_format_empty_table(self):
        """Test formatting empty table."""
        result = self.formatter.format_table([], ["name", "value"])
        assert result == "No data to display"
        
    @unit_test
    def test_column_width_calculation(self):
        """Test column width calculation."""
        data = [
            {"short": "a", "very_long_column": "very long content"},
            {"short": "bb", "very_long_column": "x"}
        ]
        headers = ["short", "very_long_column"]
        
        widths = self.formatter._calculate_column_widths(data, headers)
        
        # First column width should be max of header and data
        assert widths[0] == max(len("short"), len("bb"))  # "bb" is longest
        # Second column width should accommodate the header
        assert widths[1] >= len("very_long_column")


class TestOutputFormatter:
    """Test cases for OutputFormatter main class."""
    
    @unit_test
    def test_initialization_text_format(self):
        """Test initialization with text format."""
        formatter = OutputFormatter(format_type='text', use_color=False)
        
        assert formatter.format_type == FormatType.TEXT
        assert not formatter.colorizer.use_color
        
    @unit_test
    def test_initialization_json_format(self):
        """Test initialization with JSON format.""" 
        formatter = OutputFormatter(format_type='json', use_color=False)
        
        assert formatter.format_type == FormatType.JSON
        
    @unit_test
    def test_format_output_delegation(self):
        """Test that format_output delegates to the correct formatter."""
        formatter = OutputFormatter(format_type='json', use_color=False)
        data = {"test": "data"}
        
        result = formatter.format_output(data)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == data
        
    @unit_test
    def test_print_output(self):
        """Test print_output functionality."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            format_type='json', 
            use_color=False,
            output_file=output_buffer
        )
        data = {"test": "data"}
        
        formatter.print_output(data, title="Test")
        
        output = output_buffer.getvalue()
        assert output.strip()  # Should have content
        
        # Should be valid JSON
        parsed = json.loads(output.strip())
        assert parsed == data
        
    @unit_test
    def test_print_output_quiet_mode(self):
        """Test print_output in quiet mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            format_type='text',
            use_color=False,
            quiet=True,
            output_file=output_buffer
        )
        
        formatter.print_output({"test": "data"})
        
        # Should produce no output in quiet mode
        assert output_buffer.getvalue() == ""
        
    @unit_test
    def test_print_error(self):
        """Test error message printing."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            formatter = OutputFormatter(use_color=False)
            
            formatter.print_error("Test error message")
            
            error_output = mock_stderr.getvalue()
            assert "Error: Test error message" in error_output
            
    @unit_test
    def test_print_warning(self):
        """Test warning message printing."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            use_color=False,
            output_file=output_buffer
        )
        
        formatter.print_warning("Test warning")
        
        output = output_buffer.getvalue()
        assert "Warning: Test warning" in output
        
    @unit_test
    def test_print_warning_quiet_mode(self):
        """Test warning printing in quiet mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            use_color=False,
            quiet=True,
            output_file=output_buffer
        )
        
        formatter.print_warning("Test warning")
        
        # Should produce no output in quiet mode
        assert output_buffer.getvalue() == ""
        
    @unit_test
    def test_print_info_verbose_mode(self):
        """Test info message printing in verbose mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            use_color=False,
            verbose=1,
            output_file=output_buffer
        )
        
        formatter.print_info("Test info")
        
        output = output_buffer.getvalue()
        assert "Info: Test info" in output
        
    @unit_test
    def test_print_info_non_verbose(self):
        """Test info message printing in non-verbose mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            use_color=False,
            verbose=0,
            output_file=output_buffer
        )
        
        formatter.print_info("Test info")
        
        # Should produce no output in non-verbose mode
        assert output_buffer.getvalue() == ""
        
    @unit_test
    def test_print_debug_verbose_mode(self):
        """Test debug message printing in verbose mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            use_color=False,
            verbose=2,
            output_file=output_buffer
        )
        
        formatter.print_debug("Test debug")
        
        output = output_buffer.getvalue()
        assert "Debug: Test debug" in output
        
    @unit_test
    def test_print_success(self):
        """Test success message printing."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            use_color=False,
            output_file=output_buffer
        )
        
        formatter.print_success("Operation completed")
        
        output = output_buffer.getvalue()
        assert "Operation completed" in output
        
    @unit_test
    def test_colorize_method(self):
        """Test colorize method delegation."""
        formatter = OutputFormatter(use_color=False)
        
        result = formatter.colorize("test text", Color.RED)
        
        # With color disabled, should return plain text
        assert result == "test text"
        
    @unit_test
    def test_format_table_method(self):
        """Test format_table method delegation."""
        formatter = OutputFormatter(use_color=False)
        data = [{"name": "test", "value": 42}]
        headers = ["name", "value"]
        
        result = formatter.format_table(data, headers)
        
        assert "name" in result
        assert "value" in result
        assert "test" in result
        assert "42" in result


@pytest.mark.parametrize("format_type,expected_class", [
    ('text', TextFormatter),
    ('json', JSONFormatter), 
    ('csv', CSVFormatter),
])
@unit_test
def test_formatter_factory(format_type, expected_class):
    """Test formatter factory creates correct formatter types."""
    from tinel.cli.formatters import FormatterFactory, FormatType
    
    if format_type == 'text':
        colorizer = Mock()
        formatter = FormatterFactory.create_formatter(
            FormatType(format_type), colorizer=colorizer
        )
    else:
        formatter = FormatterFactory.create_formatter(FormatType(format_type))
    
    assert isinstance(formatter, expected_class)


@pytest.mark.parametrize("text,color_enabled,expected_contains", [
    ("test", True, ["\033[", "test", "\033[0m"]),  # Should have color codes
    ("test", False, ["test"]),  # Should only have text
])
@unit_test
def test_color_application(text, color_enabled, expected_contains):
    """Test color application in different modes."""
    with patch.object(ColorUtility, '_supports_color', return_value=color_enabled):
        colorizer = ColorUtility(use_color=color_enabled)
        result = colorizer.colorize(text, Color.RED)
        
        for expected in expected_contains:
            assert expected in result