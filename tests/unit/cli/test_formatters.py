#!/usr/bin/env python3
"""
Unit tests for output formatters.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import builtins
import importlib
import json
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

import tinel.cli.formatters as fmt
from tests.utils import unit_test
from tinel.cli.formatters import (
    Color,
    ColorUtility,
    CSVFormatter,
    FormatterFactory,
    FormatType,
    JSONFormatter,
    OutputFormatter,
    TableFormatter,
    TextFormatter,
    YAMLFormatter,
)


class TestColorUtility:
    """Test cases for ColorUtility."""

    @unit_test
    def test_colorize_with_color_enabled(self):
        """Test colorizing text with color enabled."""
        with patch.object(ColorUtility, "_supports_color", return_value=True):
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
        with patch.dict("os.environ", {"NO_COLOR": "1"}):
            colorizer = ColorUtility(use_color=True)
            assert colorizer._supports_color() is False

    @unit_test
    def test_supports_color_force_color_env(self):
        """Test color support detection with FORCE_COLOR environment."""
        with patch.dict("os.environ", {"FORCE_COLOR": "1"}):
            colorizer = ColorUtility(use_color=False)
            assert colorizer._supports_color() is True

    @unit_test
    def test_supports_color_tty_detection(self):
        """Test color support detection based on TTY."""
        with (
            patch("sys.stdout.isatty", return_value=True),
            patch("os.environ.get", return_value=None),
        ):
            colorizer = ColorUtility()
            result = colorizer._supports_color()
            assert isinstance(result, bool)

    @unit_test
    def test_supports_color_on_windows(self):
        """Test color support detection on Windows."""
        with (
            patch("sys.platform", "win32"),
            patch("sys.stdout.isatty", return_value=True),
        ):
            with patch.dict("os.environ", {"WT_SESSION": "1"}):
                assert ColorUtility()._supports_color() is True
            with patch.dict("os.environ", {"ANSICON": "1"}):
                assert ColorUtility()._supports_color() is True
            with patch.dict("os.environ", clear=True):
                assert ColorUtility()._supports_color() is False


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
        assert parsed == data
        assert "Test Title" not in result


class TestYAMLFormatter:
    """Test cases for YAMLFormatter."""

    @unit_test
    def test_format_simple_dict(self):
        """Test formatting simple dictionary as YAML."""
        with (
            patch("tinel.cli.formatters.YAML_AVAILABLE", True),
            patch("yaml.dump") as mock_yaml_dump,
        ):
            formatter = YAMLFormatter()
            data = {"key": "value", "number": 42}
            formatter.format(data)
            mock_yaml_dump.assert_called_once_with(
                data, default_flow_style=False, allow_unicode=True, sort_keys=False
            )

    @unit_test
    def test_format_yaml_not_available(self):
        """Test YAML formatting raises RuntimeError if PyYAML is not available."""
        with patch("tinel.cli.formatters.YAML_AVAILABLE", False):
            formatter = YAMLFormatter()
            with pytest.raises(RuntimeError, match="YAML formatting requires PyYAML"):
                formatter.format({"test": "data"})


class TestCSVFormatter:
    """Test cases for CSVFormatter."""

    @unit_test
    def test_format_simple_dict(self):
        """Test formatting simple dictionary as CSV."""
        formatter = CSVFormatter()
        data = {"name": "test", "value": 42}
        result = formatter.format(data)
        lines = [line.rstrip("\r") for line in result.strip().split("\n")]
        assert lines[0] == "key,value"
        assert "name,test" in lines
        assert "value,42" in lines

    @unit_test
    def test_format_list_of_dicts(self):
        """Test formatting list of dictionaries as CSV."""
        formatter = CSVFormatter()
        data = [{"name": "item1", "value": 10}, {"name": "item2", "value": 20}]
        result = formatter.format(data)
        lines = [line.rstrip("\r") for line in result.strip().split("\n")]
        assert lines[0] == "name,value"
        assert lines[1] == "item1,10"
        assert lines[2] == "item2,20"

    @unit_test
    def test_format_list_mixed_types(self):
        """Test formatting list with mixed types as CSV."""
        formatter = CSVFormatter()
        data = [{"name": "item1", "value": 10}, "simple_string", 123, ["nested"]]
        result = formatter.format(data)
        lines = [line.rstrip("\r") for line in result.strip().split("\n")]
        assert lines[0] == "index,value"
        assert "0,name=item1; value=10" in lines
        assert "1,simple_string" in lines
        assert "2,123" in lines
        assert "3,['nested']" in lines

    @unit_test
    def test_format_nested_dict(self):
        """Test formatting nested dictionary as CSV."""
        formatter = CSVFormatter()
        data = {"system": {"cpu": "Intel", "ram": "16GB"}, "status": "active"}
        result = formatter.format(data)
        lines = [line.rstrip("\r") for line in result.strip().split("\n")]
        assert lines[0] == "key,value"
        assert "system.cpu,Intel" in lines
        assert "system.ram,16GB" in lines
        assert "status,active" in lines

    @unit_test
    def test_format_empty_list(self):
        """Test formatting empty list."""
        formatter = CSVFormatter()
        assert formatter.format([]) == ""

    @unit_test
    def test_format_single_value(self):
        """Test formatting a single value as CSV."""
        formatter = CSVFormatter()
        result = formatter.format("hello")
        lines = [line.rstrip("\r") for line in result.strip().split("\n")]
        assert lines[0] == "value"
        assert lines[1] == "hello"

    @unit_test
    def test_format_list_of_lists_in_csv(self):
        """Test formatting list of lists as CSV."""
        formatter = CSVFormatter()
        data = [["a", "b"], ["c", "d"]]
        result = formatter.format(data)
        lines = result.strip().splitlines()
        assert lines[0] == "index,value"
        assert lines[1] == "0,\"['a', 'b']\""
        assert lines[2] == "1,\"['c', 'd']\""

    @unit_test
    def test_csv_formatter_with_nested_list_in_dict(self):
        """Test formatting a dict with a nested list containing a dict."""
        formatter = CSVFormatter()
        data = {"key": "value", "list": [1, "two", {"a": "b"}]}
        result = formatter.format(data)
        assert "key,value" in result
        assert "list[0],1" in result
        assert "list[1],two" in result
        assert "list[2].a,b" in result

    @unit_test
    def test_csvformatter_invalid_data(self):
        # Import moved to top

        fmt = CSVFormatter()
        # Not a list or dict: should return a single-value CSV
        out = fmt.format("string")
        assert out.strip() == "value\nstring" or out.strip() == "value\r\nstring"
        # Empty dict: should return just the header
        assert fmt.format({}).strip() == "key,value"
        # Nested dict edge case
        nested = {"a": {"b": {"c": 1}}}
        out = fmt.format(nested)
        assert "a.b.c" in out


class TestTextFormatter:
    """Test cases for TextFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.colorizer = Mock()
        self.colorizer.colorize.side_effect = lambda text, color: text

    @unit_test
    def test_format_simple_dict(self):
        """Test formatting simple dictionary as text."""
        formatter = TextFormatter(self.colorizer)
        data = {"name": "test", "value": 42}
        result = formatter.format(data)
        assert "name: test" in result
        assert "value: 42" in result

    @unit_test
    def test_format_with_title(self):
        """Test formatting with title."""
        formatter = TextFormatter(self.colorizer)
        data = {"test": "data"}
        result = formatter.format(data, title="Test Title")
        assert "Test Title" in result
        assert "==========" in result

    @unit_test
    def test_format_quiet_mode(self):
        """Test formatting in quiet mode."""
        formatter = TextFormatter(self.colorizer, quiet=True)
        data = {"name": "test", "value": 42}
        result = formatter.format(data)
        assert "name=test" in result
        assert "value=42" in result

    @unit_test
    def test_format_nested_dict(self):
        """Test formatting nested dictionary."""
        formatter = TextFormatter(self.colorizer)
        data = {"system": {"cpu": "Intel", "memory": "16GB"}, "status": "running"}
        result = formatter.format(data)
        assert "system:" in result
        assert "  cpu: Intel" in result
        assert "  memory: 16GB" in result
        assert "status: running" in result

    @unit_test
    def test_format_list(self):
        """Test formatting list data."""
        formatter = TextFormatter(self.colorizer)
        data = ["item1", "item2", {"key": "value"}, ["nested"]]
        result = formatter.format(data)
        assert "- item1" in result
        assert "- item2" in result
        assert "  key: value" in result
        assert "  - nested" in result

    @unit_test
    def test_verbose_info(self):
        """Test verbose information inclusion."""
        formatter = TextFormatter(self.colorizer, verbose=2)
        data = {"test": "data"}
        result = formatter.format(data)
        assert "Verbose Information:" in result
        assert "Data type: dict" in result
        assert "Number of keys: 1" in result
        assert "Keys: test" in result

    @unit_test
    def test_format_minimal_list(self):
        """Test minimal list formatting."""
        formatter = TextFormatter(self.colorizer, quiet=True)
        data = ["item1", {"key": "val"}, ["nested"]]
        result = formatter.format(data)
        expected_output = "[0]=item1\n[1].key=val\n[0]=nested"
        assert result == expected_output

    @unit_test
    def test_format_value_coloring(self):
        """Test value formatting and coloring."""
        colorizer = ColorUtility(use_color=True)
        with patch.object(colorizer, "_supports_color", return_value=True):
            formatter = TextFormatter(colorizer)
            assert colorizer.colorize("True", Color.GREEN) in formatter._format_value(
                True
            )
            assert colorizer.colorize("False", Color.RED) in formatter._format_value(
                False
            )
            assert colorizer.colorize("123", Color.CYAN) in formatter._format_value(123)
            assert colorizer.colorize("ok", Color.GREEN) in formatter._format_value(
                "ok"
            )
            assert colorizer.colorize("error", Color.RED) in formatter._format_value(
                "error"
            )
            assert colorizer.colorize(
                "warning", Color.YELLOW
            ) in formatter._format_value("warning")
            assert "plain" in formatter._format_value("plain")
            assert "None" in formatter._format_value(None)

    @unit_test
    def test_textformatter_format_with_primitive(self):
        # Import moved to top

        tf = TextFormatter(ColorUtility(False))
        # Should hit the else branch for both format and _format_minimal_text
        assert tf.format(123) == "123"
        assert tf._format_minimal_text(456) == "456"

    @unit_test
    def test_textformatter_add_verbose_info_dict_and_dictlike(self):
        # Import moved to top

        tf = TextFormatter(ColorUtility(False))
        # Standard dict (has keys)
        d = {"a": 1, "b": 2}
        out = tf._add_verbose_info(d)
        assert any("Keys: a, b" in line for line in out)

        # Dict-like with __len__ but no keys
        class NoKeysDict:
            def __len__(self):
                return 2

        n = NoKeysDict()
        out2 = tf._add_verbose_info(n)
        assert any("Number of keys: 2" in line for line in out2)
        assert not any("Keys:" in line for line in out2)

    @unit_test
    def test_textformatter_format_dict_with_list(self):
        # Import moved to top

        tf = TextFormatter(ColorUtility(False))
        d = {"a": [1, 2]}
        out = tf._format_dict(d)
        assert any("a:" in line for line in out)
        assert any("1" in line for line in out)
        assert any("2" in line for line in out)

    @unit_test
    def test_textformatter_add_verbose_info_keys(self):
        # Import moved to top

        tf = TextFormatter(ColorUtility(False))

        class Dummy:
            def keys(self):
                return ["x", "y"]

            def __iter__(self):
                return iter(["x", "y"])

            def __len__(self):
                return 2

        lines = tf._add_verbose_info(Dummy())
        assert any("Keys:" in line for line in lines)

    @unit_test
    def test_textformatter_format_quiet_and_none(self):
        # Import moved to top

        tf = TextFormatter(ColorUtility(False), quiet=True)
        # Quiet mode path
        assert tf.format({"a": 1}) == "a=1"
        # None data
        assert tf.format(None) == "None"
        # Empty dict
        assert tf.format({}) == ""
        # Empty list
        assert tf.format([]) == ""
        # With title
        assert tf.format({}, title="Title") == ""
        assert tf.format([], title="Title") == ""


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
        data = [{"name": "item1", "value": 10}, {"name": "item2", "value": 20}]
        headers = ["name", "value"]
        result = self.formatter.format_table(data, headers)
        assert "name  | value" in result
        assert "item1 | 10" in result
        assert "item2 | 20" in result

    @unit_test
    def test_format_table_with_lists(self):
        """Test formatting table with list rows."""
        data = [["item1", 10], ["item2", 20]]
        headers = ["name", "value"]
        result = self.formatter.format_table(data, headers)
        assert "item1 | 10" in result
        assert "item2 | 20" in result

    @unit_test
    def test_format_empty_table(self):
        """Test formatting empty table."""
        result = self.formatter.format_table([], ["name", "value"])
        assert result == "No data to display"

    @unit_test
    def test_column_width_calculation(self):
        """Test column width calculation."""
        data = [{"h1": "a", "h2": "long content"}, {"h1": "bb", "h2": "x"}]
        headers = ["h1", "h2"]
        widths = self.formatter._calculate_column_widths(data, headers)
        expected_h1_width = 2  # max(len("h1"), len("a"), len("bb"))
        expected_h2_width = 12  # max(len("h2"), len("long content"), len("x"))
        assert widths[0] == expected_h1_width
        assert widths[1] == expected_h2_width

    @unit_test
    def test_table_formatter_with_non_list_tuple_rows(self):
        """Test formatting table with rows that are not lists or tuples."""
        data = ["string_row", 123]
        headers = ["Column1"]
        result = self.formatter.format_table(data, headers)
        assert "string_row" in result
        assert "123" in result

    @unit_test
    def test_cell_value_coloring(self):
        """Test cell value formatting and coloring."""
        colorizer = ColorUtility(use_color=True)
        with patch.object(colorizer, "_supports_color", return_value=True):
            formatter = TableFormatter(colorizer)
            assert colorizer.colorize(
                "ok", Color.GREEN
            ) in formatter._format_cell_value("ok")
            assert colorizer.colorize(
                "error", Color.RED
            ) in formatter._format_cell_value("error")
            assert colorizer.colorize(
                "warning", Color.YELLOW
            ) in formatter._format_cell_value("warning")
            assert "plain" in formatter._format_cell_value("plain")

    @unit_test
    def test_tableformatter_extra_missing_columns(self):
        # Import moved to top

        tf = TableFormatter(ColorUtility(False))
        # Row with extra columns: only as many columns as headers are shown
        data = [[1, 2, 3]]
        headers = ["A", "B"]
        out = tf.format_table(data, headers)
        assert "1" in out and "2" in out and "A" in out and "B" in out
        # Empty headers: output should be blank lines
        out2 = tf.format_table([[1, 2]], [])
        assert out2 == "\n\n"
        # Non-string headers: should raise TypeError
        # Import moved to top

        with pytest.raises(TypeError):
            tf.format_table([[1]], [1])

    @unit_test
    def test_tableformatter_row_shorter_than_headers(self):
        # Import moved to top

        tf = TableFormatter(ColorUtility(False))
        data = [["a"]]  # fewer columns than headers
        headers = ["col1", "col2"]
        out = tf.format_table(data, headers)
        assert "a" in out and "col2" in out

    @unit_test
    def test_outputformatter_explanation_included(self):
        # Import moved to top

        out = OutputFormatter(verbose=1)
        s = out.format_with_explanation({"a": 1}, "this is an explanation")
        assert "explanation" in s.lower()

    @unit_test
    def test_outputformatter_wrap_text_line(self):
        # Import moved to top

        of = OutputFormatter()
        # Long line with spaces
        s = of._wrap_text_line("a " * 40, max_width=20)
        assert all(isinstance(part, str) for part in s)
        assert "".join(s).replace(" ", "") == "a" * 40
        # Line with no spaces
        expected_total_length = 50
        s2 = of._wrap_text_line("x" * 50, max_width=20)
        assert all(isinstance(part, str) for part in s2)
        assert sum(len(part) for part in s2) == expected_total_length

    @unit_test
    def test_outputformatter_print_output_quiet(self, capsys):
        # Import moved to top

        out = OutputFormatter(quiet=True)
        out.print_output({"a": 1})  # Should not print anything
        captured = capsys.readouterr()
        assert captured.out == ""

    @unit_test
    def test_outputformatter_format_table(self):
        # Import moved to top

        out = OutputFormatter()
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        s = out.format_table(data, ["a", "b"])
        assert "a" in s and "b" in s and "1" in s and "4" in s


class TestOutputFormatter:
    """Test cases for OutputFormatter main class."""

    @unit_test
    def test_initialization(self):
        """Test initialization with different formats."""
        formatter_text = OutputFormatter(format_type="text", use_color=False)
        assert formatter_text.format_type == FormatType.TEXT
        formatter_json = OutputFormatter(format_type="json")
        assert formatter_json.format_type == FormatType.JSON

    @unit_test
    def test_format_output_delegation(self):
        """Test that format_output delegates to the correct formatter."""
        formatter = OutputFormatter(format_type="json")
        data = {"test": "data"}
        result = formatter.format_output(data)
        assert json.loads(result) == data

    @unit_test
    def test_print_output(self):
        """Test print_output functionality."""
        output_buffer = StringIO()
        formatter = OutputFormatter(format_type="json", output_file=output_buffer)
        data = {"test": "data"}
        formatter.print_output(data, title="Test")
        assert json.loads(output_buffer.getvalue().strip()) == data

    @unit_test
    def test_print_output_quiet_mode(self):
        """Test print_output in quiet mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(quiet=True, output_file=output_buffer)
        formatter.print_output({"test": "data"})
        assert output_buffer.getvalue() == ""

    @unit_test
    def test_print_error(self):
        """Test error message printing."""
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            formatter = OutputFormatter(use_color=False)
            formatter.print_error("Test error")
            assert "Error: Test error" in mock_stderr.getvalue()

    @unit_test
    def test_print_warning(self):
        """Test warning message printing."""
        output_buffer = StringIO()
        formatter = OutputFormatter(use_color=False, output_file=output_buffer)
        formatter.print_warning("Test warning")
        assert "Warning: Test warning" in output_buffer.getvalue()

    @unit_test
    def test_print_warning_quiet_mode(self):
        """Test warning printing in quiet mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(quiet=True, output_file=output_buffer)
        formatter.print_warning("Test warning")
        assert output_buffer.getvalue() == ""

    @unit_test
    def test_print_info(self):
        """Test info message printing."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            verbose=1, use_color=False, output_file=output_buffer
        )
        formatter.print_info("Test info")
        assert "Info: Test info" in output_buffer.getvalue()
        output_buffer.truncate(0)
        output_buffer.seek(0)
        formatter = OutputFormatter(verbose=0, output_file=output_buffer)
        formatter.print_info("Test info")
        assert output_buffer.getvalue() == ""

    @unit_test
    def test_print_debug(self):
        """Test debug message printing."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            verbose=2, use_color=False, output_file=output_buffer
        )
        formatter.print_debug("Test debug")
        assert "Debug: Test debug" in output_buffer.getvalue()
        output_buffer.truncate(0)
        output_buffer.seek(0)
        formatter = OutputFormatter(verbose=1, output_file=output_buffer)
        formatter.print_debug("Test debug")
        assert output_buffer.getvalue() == ""

    @unit_test
    def test_print_success(self):
        """Test success message printing."""
        output_buffer = StringIO()
        formatter = OutputFormatter(use_color=False, output_file=output_buffer)
        formatter.print_success("OK")
        assert "✓ OK" in output_buffer.getvalue()

    @unit_test
    def test_format_with_explanation(self):
        """Test formatting with an explanation."""
        output_buffer = StringIO()
        formatter = OutputFormatter(
            verbose=1, use_color=False, output_file=output_buffer
        )
        data = {"key": "val"}
        explanation = "This is why."
        formatter.print_output_with_explanation(data, explanation, title="Title")
        output = output_buffer.getvalue()
        assert "Title" in output
        assert "key: val" in output
        assert "Explanation:" in output
        assert "This is why." in output

    @unit_test
    def test_format_with_explanation_quiet(self):
        """Test that explanations are suppressed in quiet mode."""
        output_buffer = StringIO()
        formatter = OutputFormatter(verbose=1, quiet=True, output_file=output_buffer)
        formatter.print_output_with_explanation({}, "exp")
        assert output_buffer.getvalue() == ""

    @unit_test
    def test_wrap_text_line(self):
        # Import moved to top

        of = OutputFormatter()
        # Long line with spaces
        s = of._wrap_text_line("a " * 40, max_width=20)
        assert all(isinstance(part, str) for part in s)
        assert "".join(s).replace(" ", "") == "a" * 40
        # Line with no spaces (single long word)
        expected_total_length = 50
        s2 = of._wrap_text_line("x" * 50, max_width=20)
        assert all(isinstance(part, str) for part in s2)
        assert sum(len(part) for part in s2) == expected_total_length

    @unit_test
    def test_outputformatter_should_include_explanation_none(self):
        # Import moved to top

        of = OutputFormatter(verbose=1, quiet=False)
        assert not of._should_include_explanation(None)

    @unit_test
    def test_outputformatter_format_explanation_section_empty_and_newline(self):
        # Import moved to top

        of = OutputFormatter()
        # Empty string
        out = of._format_explanation_section("")
        assert isinstance(out, list)
        # Only newline
        out2 = of._format_explanation_section("\n")
        assert isinstance(out2, list)
        assert any(isinstance(line, str) for line in out2)

    @unit_test
    def test_outputformatter_format_with_explanation_no_explanation_branch(self):
        # Import moved to top

        # verbose=0 disables explanation
        of = OutputFormatter(verbose=0)
        result = of.format_with_explanation(
            {"a": 1}, explanation="Should not show", title=None
        )
        assert "Explanation:" not in result
        # Also test with explanation empty
        of2 = OutputFormatter(verbose=1)
        result2 = of2.format_with_explanation({"a": 1}, explanation="", title=None)
        assert "Explanation:" not in result2

    @unit_test
    def test_outputformatter_wrap_text_line_empty_final_line(self):
        # Import moved to top

        of = OutputFormatter()
        # This will result in current_line being only spaces at the end
        s = of._wrap_text_line("word1 word2    ", max_width=6)
        # The last current_line is only spaces, so nothing should be appended
        assert all(part.strip() for part in s)  # No empty lines
        # Pure whitespace input
        s2 = of._wrap_text_line("    ", max_width=2)
        assert s2 == [] or all(part.strip() == "" for part in s2)


class TestFormatterFactoryAndMisc:
    """Tests for FormatterFactory and other miscellaneous cases."""

    @unit_test
    @pytest.mark.parametrize(
        "format_type,expected_class",
        [
            ("json", JSONFormatter),
            ("csv", CSVFormatter),
        ],
    )
    def test_formatter_factory(self, format_type, expected_class):
        """Test formatter factory creates correct formatter types."""
        formatter = FormatterFactory.create_formatter(FormatType(format_type))
        assert isinstance(formatter, expected_class)

    @unit_test
    def test_formatter_factory_text(self):
        """Test formatter factory for text formatter."""
        colorizer = Mock()
        formatter = FormatterFactory.create_formatter(
            FormatType.TEXT, colorizer=colorizer
        )
        assert isinstance(formatter, TextFormatter)

    @unit_test
    def test_formatter_factory_yaml(self):
        """Test formatter factory for yaml formatter."""
        with patch("tinel.cli.formatters.YAML_AVAILABLE", True):
            formatter = FormatterFactory.create_formatter(FormatType.YAML)
            assert isinstance(formatter, YAMLFormatter)

    @unit_test
    def test_formatter_factory_unsupported(self):
        """Test factory raises error for unsupported type."""
        with pytest.raises(ValueError, match="Unsupported format type: non_existent"):
            FormatterFactory.create_formatter("non_existent")

    @unit_test
    def test_formatter_factory_requires_colorizer_for_text(self):
        """Test factory raises error if colorizer is missing for text."""
        with pytest.raises(
            ValueError, match="Text formatter requires a colorizer instance"
        ):
            FormatterFactory.create_formatter(FormatType.TEXT)


class TestEdgeCoverage:
    def test_yaml_available_importerror(self, monkeypatch):
        # Simulate ImportError for yaml and actually use YAMLFormatter
        # Imports moved to top

        orig_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "yaml":
                raise ImportError
            return orig_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        # Import moved to top

        sys.modules.pop("yaml", None)
        # Import is at top - using direct reference

        importlib.reload(fmt)
        assert fmt.YAML_AVAILABLE is False
        # Actually try to use YAMLFormatter to hit the RuntimeError path
        # Import moved to top

        with pytest.raises(RuntimeError):
            fmt.YAMLFormatter().format({"a": 1})

    def test_format_minimal_dict_nested(self):
        # Import moved to top

        tf = TextFormatter(ColorUtility(False))
        # Nested dict
        d = {"a": {"b": 1}}
        out = tf.format(d)
        assert "a:" in out and "b: 1" in out
        # Dict with list of dicts
        d2 = {"a": [{"b": 2}, 3]}
        out2 = tf.format(d2)
        assert "a:" in out2 and "b: 2" in out2 and "- 3" in out2
        # Dict with list of primitives
        d3 = {"a": [1, 2]}
        out3 = tf.format(d3)
        assert "a:" in out3 and "- 1" in out3 and "- 2" in out3


class TestAdditional:
    """Additional tests from test_formatters_additional.py."""

    def _create_plain_colorizer(self):
        """Return a ColorUtility instance that leaves strings unchanged."""
        return ColorUtility(use_color=False)

    @unit_test
    def test_table_formatter_basic(self):
        """Test basic table formatting."""
        headers = ["name", "status", "value"]
        data = [
            {"name": "row1", "status": "ok", "value": 10},
            {"name": "r2", "status": "warning", "value": 200},
        ]
        formatter = TableFormatter(self._create_plain_colorizer())
        table = formatter.format_table(data, headers)
        lines = table.splitlines()
        expected_line_count = 4
        assert len(lines) == expected_line_count
        header, separator, first_row, second_row = lines
        assert "name" in header and "status" in header and "value" in header
        assert len(separator) > 0
        assert "row1" in first_row and "ok" in first_row and "10" in first_row
        assert "r2" in second_row and "warning" in second_row and "200" in second_row

    @unit_test
    def test_table_formatter_non_dict_rows(self):
        """Test table formatting with non-dict rows."""
        headers = ["col1", "col2"]
        data = [["a", "b"], ["c", "d"]]
        formatter = TableFormatter(self._create_plain_colorizer())
        table = formatter.format_table(data, headers).splitlines()
        assert table[2].startswith("a")
        assert table[3].startswith("c")

    @unit_test
    def test_output_formatter_wrap_text_line_wrapping(self):
        """Test wrapping text lines."""
        long_line = "word " * 30
        out_fmt = OutputFormatter("text", use_color=False)
        wrapped = out_fmt._wrap_text_line(long_line)
        max_line_length = 80
        assert all(len(line) <= max_line_length for line in wrapped)
        assert " ".join(wrapped).replace("  ", " ").startswith("word")

    @unit_test
    def test_output_formatter_explanation_included_and_suppressed(self):
        """Test explanation inclusion and suppression."""
        data = {"k": "v"}
        explanation = "some explanation text"
        out_verbose = OutputFormatter("text", verbose=1, use_color=False)
        formatted = out_verbose.format_with_explanation(data, explanation)
        assert "Explanation:" in formatted and "some explanation text" in formatted
        out_quiet = OutputFormatter("text", verbose=0, use_color=False)
        formatted_no_exp = out_quiet.format_with_explanation(data, explanation)
        assert "Explanation:" not in formatted_no_exp
        out_super_quiet = OutputFormatter(
            "text", verbose=3, quiet=True, use_color=False
        )
        formatted_quiet = out_super_quiet.format_with_explanation(data, explanation)
        assert "Explanation:" not in formatted_quiet and "k=v" in formatted_quiet

    @unit_test
    def test_formatter_factory_requires_colorizer_for_text(self):
        """Test formatter factory requires colorizer for text."""
        with pytest.raises(ValueError):
            FormatterFactory.create_formatter(FormatType.TEXT, colorizer=None)

    @unit_test
    def test_formatter_factory_unsupported_format(self):
        """Test formatter factory raises error for unsupported format."""

        class FakeFormat(str):
            pass

        fake = FakeFormat("fake")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            FormatterFactory.create_formatter(
                fake, colorizer=self._create_plain_colorizer()
            )

    @unit_test
    def test_output_formatter_print_methods_do_not_throw(self):
        """Test output formatter print methods do not throw."""
        buffer = StringIO()
        out_fmt = OutputFormatter(
            "text", use_color=False, verbose=2, output_file=buffer
        )
        out_fmt.print_output({"a": 1})
        out_fmt.print_output_with_explanation({"a": 1}, "explain")
        out_fmt.print_warning("warn")
        out_fmt.print_info("info")
        out_fmt.print_debug("debug")
        out_fmt.print_success("done")
        with patch("sys.stderr", new=StringIO()):
            out_fmt.print_error("err")
        combined = buffer.getvalue()
        assert "warn" in combined and "info" in combined and "✓" in combined

    @unit_test
    def test_output_formatter_wrap_text_line_no_wrap(self):
        """Test wrapping text lines with no wrapping."""
        out_fmt = OutputFormatter(use_color=False)
        short = "short line"
        assert out_fmt._wrap_text_line(short) == [short]

    @unit_test
    def test_textformatter_format_minimal_dict_with_nested_list(self):
        """Test formatting minimal dict with nested list."""
        # Import moved to top

        tf = TextFormatter(ColorUtility(False), quiet=True)
        data = {"outer": [1, {"inner": "val"}, 3]}
        result = tf.format(data)
        assert "outer[0]=1" in result
        assert "outer[1].inner=val" in result
        assert "outer[2]=3" in result

    @unit_test
    def test_textformatter_format_minimal_dict_with_nested_dict(self):
        """Test formatting minimal dict with nested dict."""
        # Import moved to top

        tf = TextFormatter(ColorUtility(False), quiet=True)
        data = {"first": {"second": {"third": 3}}}
        result = tf.format(data)
        assert "first.second.third=3" in result

    @unit_test
    def test_outputformatter_quiet_print_success_no_output(self):
        """Test quiet output formatter print success with no output."""
        # Import moved to top

        buffer = StringIO()
        out_fmt = OutputFormatter(
            "text", use_color=False, quiet=True, output_file=buffer
        )
        out_fmt.print_success("done quietly")
        assert buffer.getvalue() == ""
