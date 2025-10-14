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

import csv
import json
import os
import sys
from abc import ABC, abstractmethod
from enum import Enum
from io import StringIO
from typing import Any, Dict, List, Optional, TextIO

"""This module provides a flexible and extensible output formatting system.

It includes a variety of formatters (Text, JSON, YAML, CSV) and a color
utility for creating user-friendly and machine-readable output. The module is
designed to be easily extensible with new formatters and provides a
centralized `OutputFormatter` class to manage the formatting process.
"""

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Verbosity constants
DEBUG_VERBOSITY_LEVEL = 2


# Constants for commonly used strings
class StatusValues:
    """A collection of common status values for consistent color-coding.

    This class defines lists of positive, negative, and warning strings that
    can be used to apply consistent coloring to status-related output.
    """

    POSITIVE = ["ok", "good", "healthy", "normal", "active", "enabled"]
    NEGATIVE = ["error", "failed", "critical", "bad", "unhealthy", "disabled"]
    WARNING = ["warning", "caution", "degraded", "inactive"]


class LogSources:
    """A collection of common log source names.

    This class provides a centralized place to define the names of common log
    sources, ensuring consistency throughout the application.
    """

    JOURNALD = "journald"
    SYSLOG = "syslog"
    KERN_LOG = "kern.log"
    DMESG = "dmesg"
    AUTH_LOG = "auth.log"


class Color:
    """A collection of ANSI color codes for terminal output.

    This class provides a set of constants for standard, bold, and background
    colors, making it easy to apply consistent and readable color-coding to
    terminal output.
    """

    # Reset
    RESET = "\033[0m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bold colors
    BOLD_BLACK = "\033[1;30m"
    BOLD_RED = "\033[1;31m"
    BOLD_GREEN = "\033[1;32m"
    BOLD_YELLOW = "\033[1;33m"
    BOLD_BLUE = "\033[1;34m"
    BOLD_MAGENTA = "\033[1;35m"
    BOLD_CYAN = "\033[1;36m"
    BOLD_WHITE = "\033[1;37m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class FormatType(Enum):
    """An enumeration of the supported output format types.

    This enum provides a typesafe way to specify the desired output format
    for the CLI.
    """

    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"


class BaseFormatter(ABC):
    """An abstract base class for all data formatters.

    This class defines the common interface that all formatters must implement,
    ensuring that they can be used interchangeably by the `FormatterFactory` and
    `OutputFormatter`.
    """

    @abstractmethod
    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Formats the given data into a string representation.

        Args:
            data: The data to be formatted.
            title: An optional title for the output.

        Returns:
            A string containing the formatted data.
        """
        pass


class JSONFormatter(BaseFormatter):
    """A formatter for converting data into JSON format."""

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Formats the given data as a JSON string.

        Args:
            data: The data to be formatted.
            title: An optional title (ignored by this formatter).

        Returns:
            A string containing the data in JSON format.
        """
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)


class YAMLFormatter(BaseFormatter):
    """A formatter for converting data into YAML format."""

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Formats the given data as a YAML string.

        Args:
            data: The data to be formatted.
            title: An optional title (ignored by this formatter).

        Returns:
            A string containing the data in YAML format.

        Raises:
            RuntimeError: If the `PyYAML` library is not installed.
        """
        if not YAML_AVAILABLE:
            raise RuntimeError(
                "YAML formatting requires PyYAML. Install with: pip install PyYAML"
            )

        result = yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        return str(result)


class CSVFormatter(BaseFormatter):
    """A formatter for converting data into CSV format."""

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Formats the given data as a CSV string.

        This method can handle dictionaries, lists of dictionaries, and other
        data types, converting them into an appropriate CSV representation.

        Args:
            data: The data to be formatted.
            title: An optional title (ignored by this formatter).

        Returns:
            A string containing the data in CSV format.
        """
        if isinstance(data, dict):
            return self._format_dict_as_csv(data)
        elif isinstance(data, list):
            return self._format_list_as_csv(data)
        else:
            # Single value - create a simple CSV with one column
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["value"])
            writer.writerow([str(data)])
            return output.getvalue().strip()

    def _format_dict_as_csv(self, data: Dict[str, Any]) -> str:
        """Formats a dictionary as a key-value CSV.

        Args:
            data: The dictionary to be formatted.

        Returns:
            A string containing the dictionary in key-value CSV format.
        """
        output = StringIO()
        writer = csv.writer(output)

        # Flatten the dictionary for CSV output
        flattened = self._flatten_dict(data)

        # Write header and data
        writer.writerow(["key", "value"])
        for key, value in flattened.items():
            writer.writerow([key, str(value)])

        return output.getvalue().strip()

    def _format_list_as_csv(self, data: List[Any]) -> str:
        """Formats a list as a CSV.

        This method intelligently handles lists of dictionaries by using the
        dictionary keys as headers. For other list types, it creates an
        indexed CSV.

        Args:
            data: The list to be formatted.

        Returns:
            A string containing the list in CSV format.
        """
        if not data:
            return ""

        output = StringIO()
        writer = csv.writer(output)

        # Check if all items are dictionaries with the same keys
        if all(isinstance(item, dict) for item in data):
            # Get all unique keys from all dictionaries
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())

            headers = sorted(all_keys)
            writer.writerow(headers)

            for item in data:
                row = [str(item.get(key, "")) for key in headers]
                writer.writerow(row)
        else:
            # Mixed types or simple values - create indexed CSV
            writer.writerow(["index", "value"])
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    # Convert dict to string representation
                    value = "; ".join(f"{k}={v}" for k, v in item.items())
                else:
                    value = str(item)
                writer.writerow([i, value])

        return output.getvalue().strip()

    def _flatten_dict(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Recursively flattens a nested dictionary.

        This helper method is used to convert a nested dictionary into a
        single-level dictionary with dot-separated keys, which is suitable for
        CSV output.

        Args:
            data: The dictionary to be flattened.
            prefix: The prefix to be used for the keys in the flattened
                    dictionary.

        Returns:
            A new, flattened dictionary.
        """
        flattened = {}

        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flattened.update(self._flatten_dict(item, f"{full_key}[{i}]"))
                    else:
                        flattened[f"{full_key}[{i}]"] = item
            else:
                flattened[full_key] = value

        return flattened


class TextFormatter(BaseFormatter):
    """A formatter for converting data into human-readable text.

    This class provides a rich, colorized text representation of data, with
    support for nested structures, titles, and different verbosity levels.

    Args:
        colorizer: A `ColorUtility` instance for applying color to the text.
        quiet: A boolean indicating whether to suppress non-essential output.
        verbose: An integer representing the verbosity level.
    """

    def __init__(self, colorizer: Any, quiet: bool = False, verbose: int = 0):
        """Initializes the TextFormatter.

        Args:
            colorizer: A `ColorUtility` instance.
            quiet: A boolean indicating whether to operate in quiet mode.
            verbose: An integer representing the verbosity level.
        """
        self.colorizer = colorizer
        self.quiet = quiet
        self.verbose = verbose

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Formats the given data as a human-readable text string.

        This method produces either a rich, colorized output or a minimal,
        script-friendly output, depending on the `quiet` setting.

        Args:
            data: The data to be formatted.
            title: An optional title for the output.

        Returns:
            A string containing the formatted data.
        """
        if self.quiet:
            return self._format_minimal_text(data)

        lines = []

        if title and not self.quiet:
            lines.append(self.colorizer.colorize(title, Color.BOLD_CYAN))
            lines.append(self.colorizer.colorize("=" * len(title), Color.CYAN))
            lines.append("")

        if isinstance(data, dict):
            lines.extend(self._format_dict(data))
        elif isinstance(data, list):
            lines.extend(self._format_list(data))
        else:
            lines.append(str(data))

        # Add verbose information if enabled
        if self.verbose >= DEBUG_VERBOSITY_LEVEL and isinstance(data, dict):
            lines.extend(self._add_verbose_info(data))

        return "\n".join(lines)

    def _format_minimal_text(self, data: Any) -> str:
        """Formats data as minimal text suitable for scripting.

        Args:
            data: The data to be formatted.

        Returns:
            A string containing the data in a minimal, script-friendly format.
        """
        if isinstance(data, dict):
            return self._format_minimal_dict(data)
        elif isinstance(data, list):
            return self._format_minimal_list(data)
        else:
            return str(data)

    def _format_minimal_dict(self, data: Dict[str, Any], prefix: str = "") -> str:
        """Formats a dictionary as minimal, dot-separated key-value pairs.

        Args:
            data: The dictionary to be formatted.
            prefix: The prefix for the keys.

        Returns:
            A string containing the formatted dictionary.
        """
        lines = []

        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key

            if isinstance(value, dict):
                lines.extend(
                    self._format_minimal_dict(value, f"{full_key}.").split("\n")
                )
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        lines.extend(
                            self._format_minimal_dict(item, f"{full_key}[{i}].").split(
                                "\n"
                            )
                        )
                    else:
                        lines.append(f"{full_key}[{i}]={item}")
            else:
                lines.append(f"{full_key}={value}")

        return "\n".join(lines)

    def _format_minimal_list(self, data: list) -> str:
        """Formats a list as minimal, indexed key-value pairs.

        Args:
            data: The list to be formatted.

        Returns:
            A string containing the formatted list.
        """
        lines = []

        for i, item in enumerate(data):
            if isinstance(item, dict):
                lines.extend(self._format_minimal_dict(item, f"[{i}].").split("\n"))
            elif isinstance(item, list):
                lines.extend(self._format_minimal_list(item).split("\n"))
            else:
                lines.append(f"[{i}]={item}")

        return "\n".join(lines)

    def _format_dict(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """Formats a dictionary as a rich, colorized text block.

        Args:
            data: The dictionary to be formatted.
            indent: The indentation level.

        Returns:
            A list of strings representing the formatted dictionary.
        """
        lines = []
        indent_str = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                colored_key = self.colorizer.colorize(key + ":", Color.BOLD_WHITE)
                lines.append(f"{indent_str}{colored_key}")
                lines.extend(self._format_dict(value, indent + 1))
            elif isinstance(value, list):
                colored_key = self.colorizer.colorize(key + ":", Color.BOLD_WHITE)
                lines.append(f"{indent_str}{colored_key}")
                lines.extend(self._format_list(value, indent + 1))
            else:
                formatted_value = self._format_value(value)
                colored_key = self.colorizer.colorize(key + ":", Color.BOLD_WHITE)
                lines.append(f"{indent_str}{colored_key} {formatted_value}")

        return lines

    def _format_list(self, data: list, indent: int = 0) -> List[str]:
        """Formats a list as a rich, colorized text block.

        Args:
            data: The list to be formatted.
            indent: The indentation level.

        Returns:
            A list of strings representing the formatted list.
        """
        lines = []
        indent_str = "  " * indent

        for i, item in enumerate(data):
            if isinstance(item, dict):
                lines.append(
                    f"{indent_str}{self.colorizer.colorize(f'[{i}]:', Color.YELLOW)}"
                )
                lines.extend(self._format_dict(item, indent + 1))
            elif isinstance(item, list):
                lines.append(
                    f"{indent_str}{self.colorizer.colorize(f'[{i}]:', Color.YELLOW)}"
                )
                lines.extend(self._format_list(item, indent + 1))
            else:
                formatted_value = self._format_value(item)
                colored_dash = self.colorizer.colorize("-", Color.YELLOW)
                lines.append(f"{indent_str}{colored_dash} {formatted_value}")

        return lines

    def _format_value(self, value: Any) -> str:  # noqa: PLR0911
        """Formats and colorizes an individual value based on its type and content.

        Args:
            value: The value to be formatted.

        Returns:
            A string containing the formatted and colorized value.
        """
        if isinstance(value, bool):
            color = Color.GREEN if value else Color.RED
            return self.colorizer.colorize(str(value), color)  # type: ignore[no-any-return]
        elif isinstance(value, (int, float)):
            return self.colorizer.colorize(str(value), Color.CYAN)  # type: ignore[no-any-return]
        elif isinstance(value, str):
            # Color-code common status values
            if value.lower() in StatusValues.POSITIVE:
                return self.colorizer.colorize(value, Color.GREEN)  # type: ignore[no-any-return]
            elif value.lower() in StatusValues.NEGATIVE:
                return self.colorizer.colorize(value, Color.RED)  # type: ignore[no-any-return]
            elif value.lower() in StatusValues.WARNING:
                return self.colorizer.colorize(value, Color.YELLOW)  # type: ignore[no-any-return]
            else:
                return value
        else:
            return str(value)

    def _add_verbose_info(self, data: Dict[str, Any]) -> List[str]:
        """Adds verbose information about the data to the output.

        Args:
            data: The data for which to add verbose information.

        Returns:
            A list of strings containing the verbose information.
        """
        lines = [""]
        lines.append(
            self.colorizer.colorize("Verbose Information:", Color.BOLD_MAGENTA)
        )
        lines.append(self.colorizer.colorize("-" * 20, Color.MAGENTA))
        lines.append(f"Data type: {type(data).__name__}")
        lines.append(f"Number of keys: {len(data)}")
        if hasattr(data, "keys"):
            lines.append(f"Keys: {', '.join(str(k) for k in data)}")
        return lines


class FormatterFactory:
    """A factory class for creating formatter instances.

    This class provides a centralized way to create instances of the different
    formatter classes based on a `FormatType` enum.
    """

    @staticmethod
    def create_formatter(
        format_type: FormatType,
        colorizer: Any = None,
        quiet: bool = False,
        verbose: int = 0,
    ) -> BaseFormatter:
        """Creates a formatter instance based on the specified format type.

        Args:
            format_type: The type of formatter to create.
            colorizer: A `ColorUtility` instance (required for the text
                       formatter).
            quiet: A boolean indicating whether to operate in quiet mode.
            verbose: An integer representing the verbosity level.

        Returns:
            An instance of a `BaseFormatter` subclass.

        Raises:
            ValueError: If the specified format type is not supported or if a
                        required dependency is missing.
        """
        if format_type == FormatType.JSON:
            return JSONFormatter()
        elif format_type == FormatType.YAML:
            return YAMLFormatter()
        elif format_type == FormatType.CSV:
            return CSVFormatter()
        elif format_type == FormatType.TEXT:
            if colorizer is None:
                raise ValueError("Text formatter requires a colorizer instance")
            return TextFormatter(colorizer, quiet, verbose)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")


class ColorUtility:
    """A utility class for applying ANSI color codes to text.

    This class provides a simple way to colorize text for terminal output,
    with built-in support for disabling color when not supported or desired.

    Args:
        use_color: A boolean indicating whether to enable colorized output.
    """

    def __init__(self, use_color: bool = True):
        """Initializes the ColorUtility.

        Args:
            use_color: A boolean indicating whether to enable color.
        """
        self.use_color = use_color and self._supports_color()

    def colorize(self, text: str, color: str) -> str:
        """Applies a color to the given text if color is enabled.

        Args:
            text: The text to be colorized.
            color: The ANSI color code to be applied.

        Returns:
            The colorized text, or the original text if color is disabled.
        """
        if not self.use_color:
            return text
        return f"{color}{text}{Color.RESET}"

    def _supports_color(self) -> bool:
        """Checks if the terminal supports color output.

        This method considers environment variables like `NO_COLOR` and
        `FORCE_COLOR`, and also checks if `stdout` is a TTY.

        Returns:
            True if color is supported, False otherwise.
        """
        # Import moved to top

        # Check for NO_COLOR environment variable (https://no-color.org/)
        if os.environ.get("NO_COLOR"):
            return False

        # Check for FORCE_COLOR environment variable
        if os.environ.get("FORCE_COLOR"):
            return True

        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False

        # Check for common terminals that support color
        term = sys.platform
        if term == "win32":
            # Windows 10 and later support ANSI colors
            return "ANSICON" in os.environ or "WT_SESSION" in os.environ

        return True


class TableFormatter:
    """A specialized formatter for creating text-based tables.

    This class provides methods for creating well-formatted, colorized tables
    from lists of dictionaries or lists of lists.

    Args:
        colorizer: A `ColorUtility` instance for applying color to the table.
    """

    def __init__(self, colorizer: ColorUtility):
        """Initializes the TableFormatter.

        Args:
            colorizer: A `ColorUtility` instance.
        """
        self.colorizer = colorizer

    def format_table(self, data: list, headers: list) -> str:
        """Formats the given data as a text-based table.

        Args:
            data: A list of dictionaries or lists representing the table rows.
            headers: A list of strings for the table headers.

        Returns:
            A string containing the formatted table.
        """
        if not data:
            return "No data to display"

        # Calculate column widths
        col_widths = self._calculate_column_widths(data, headers)

        # Format table components
        header_line = self._format_header_line(headers, col_widths)
        separator_line = self._format_separator_line(col_widths)
        data_lines = self._format_data_lines(data, headers, col_widths)

        return "\n".join([header_line, separator_line] + data_lines)

    def _calculate_column_widths(self, data: list, headers: list) -> List[int]:
        """Calculates the optimal width for each column in a table.

        Args:
            data: The table data.
            headers: The table headers.

        Returns:
            A list of integers representing the calculated width for each
            column.
        """
        col_widths = [len(header) for header in headers]

        for row in data:
            if isinstance(row, dict):
                for i, header in enumerate(headers):
                    value = str(row.get(header, ""))
                    col_widths[i] = max(col_widths[i], len(value))
            elif isinstance(row, (list, tuple)):
                for i, value in enumerate(row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], len(str(value)))

        return col_widths

    def _format_header_line(self, headers: list, col_widths: List[int]) -> str:
        """Formats the header line of a table.

        Args:
            headers: The table headers.
            col_widths: The calculated column widths.

        Returns:
            A string representing the formatted header line.
        """
        return " | ".join(
            self.colorizer.colorize(header.ljust(width), Color.BOLD_WHITE)
            for header, width in zip(headers, col_widths, strict=False)
        )

    def _format_separator_line(self, col_widths: List[int]) -> str:
        """Formats the separator line of a table.

        Args:
            col_widths: The calculated column widths.

        Returns:
            A string representing the formatted separator line.
        """
        separator = "-+-".join("-" * width for width in col_widths)
        return self.colorizer.colorize(separator, Color.CYAN)

    def _format_data_lines(
        self, data: list, headers: list, col_widths: List[int]
    ) -> List[str]:
        """Formats the data lines of a table.

        Args:
            data: The table data.
            headers: The table headers.
            col_widths: The calculated column widths.

        Returns:
            A list of strings, where each string is a formatted data line.
        """
        lines = []

        for row in data:
            if isinstance(row, dict):
                row_values = [str(row.get(header, "")) for header in headers]
            elif isinstance(row, (list, tuple)):
                row_values = [str(value) for value in row]
                # Pad with empty strings if row is shorter than headers
                while len(row_values) < len(headers):
                    row_values.append("")
            else:
                row_values = [str(row)]

            formatted_values = []
            for value, width in zip(row_values, col_widths, strict=False):
                formatted_value = self._format_cell_value(value).ljust(width)
                formatted_values.append(formatted_value)

            lines.append(" | ".join(formatted_values))

        return lines

    def _format_cell_value(self, value: str) -> str:
        """Formats and colorizes an individual cell value.

        Args:
            value: The cell value to be formatted.

        Returns:
            A string containing the formatted and colorized cell value.
        """
        if value.lower() in StatusValues.POSITIVE:
            return self.colorizer.colorize(value, Color.GREEN)
        elif value.lower() in StatusValues.NEGATIVE:
            return self.colorizer.colorize(value, Color.RED)
        elif value.lower() in StatusValues.WARNING:
            return self.colorizer.colorize(value, Color.YELLOW)
        else:
            return value


class OutputFormatter:
    """A high-level class for managing output formatting.

    This class acts as a facade for the various formatter classes, providing a
    simple and consistent interface for formatting and printing data in
    different styles and formats. It also includes methods for printing
    standardized messages, such as errors, warnings, and success notifications.

    Args:
        format_type: The desired output format ('text', 'json', 'yaml', 'csv').
        use_color: A boolean indicating whether to use color in the output.
        verbose: The verbosity level (0-3).
        quiet: A boolean indicating whether to suppress non-error output.
        output_file: The file to which output should be written (defaults to
                     `sys.stdout`).
    """

    def __init__(
        self,
        format_type: str = "text",
        use_color: bool = True,
        verbose: int = 0,
        quiet: bool = False,
        output_file: Optional[TextIO] = None,
    ):
        """Initializes the OutputFormatter.

        Args:
            format_type: The output format.
            use_color: Whether to use color.
            verbose: The verbosity level.
            quiet: Whether to suppress non-error output.
            output_file: The output file.
        """
        self.format_type = FormatType(format_type)
        self.verbose = verbose
        self.quiet = quiet
        self.output_file = output_file or sys.stdout

        # Initialize utilities
        self.colorizer = ColorUtility(use_color)
        self.table_formatter = TableFormatter(self.colorizer)

        # Initialize formatter strategy
        self.formatter = FormatterFactory.create_formatter(
            self.format_type, self.colorizer, quiet, verbose
        )

    def colorize(self, text: str, color: str) -> str:
        """Applies color to the given text.

        Args:
            text: The text to be colorized.
            color: The ANSI color code to be applied.

        Returns:
            The colorized text, or the original text if color is disabled.
        """
        return self.colorizer.colorize(text, color)

    def format_output(self, data: Any, title: Optional[str] = None) -> str:
        """Formats the given data using the configured formatter.

        Args:
            data: The data to be formatted.
            title: An optional title for the output.

        Returns:
            A string containing the formatted data.
        """
        return self.formatter.format(data, title)

    def format_with_explanation(
        self, data: Any, explanation: str, title: Optional[str] = None
    ) -> str:
        """Formats data and includes an explanation in verbose mode.

        Args:
            data: The data to be formatted.
            explanation: The explanation text to be included.
            title: An optional title for the output.

        Returns:
            A string containing the formatted data and, if applicable, the
            explanation.
        """
        lines = [self.format_output(data, title)]

        if self._should_include_explanation(explanation):
            lines.extend(self._format_explanation_section(explanation))

        return "\n".join(lines)

    def _should_include_explanation(self, explanation: str) -> bool:
        """Determines if the explanation should be included in the output.

        Args:
            explanation: The explanation text.

        Returns:
            True if the explanation should be included, False otherwise.
        """
        return bool(self.verbose >= 1 and explanation and not self.quiet)

    def _format_explanation_section(self, explanation: str) -> List[str]:
        """Formats the explanation section with proper wrapping and color.

        Args:
            explanation: The explanation text.

        Returns:
            A list of strings representing the formatted explanation section.
        """
        lines = [""]
        lines.append(self.colorize("Explanation:", Color.BOLD_YELLOW))
        lines.append(self.colorize("-" * 12, Color.YELLOW))

        for line in explanation.split("\n"):
            lines.extend(self._wrap_text_line(line))

        return lines

    def _wrap_text_line(self, line: str, max_width: int = 80) -> List[str]:
        """Wraps a single line of text to a specified width.

        Args:
            line: The line of text to be wrapped.
            max_width: The maximum width of a line.

        Returns:
            A list of strings representing the wrapped lines.
        """
        if len(line) <= max_width:
            return [line]

        words = line.split()
        wrapped_lines = []
        current_line = ""

        for word in words:
            if len(current_line + word) > max_width:
                if current_line.strip():
                    wrapped_lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line += word + " "

        if current_line.strip():
            wrapped_lines.append(current_line.strip())

        return wrapped_lines

    def print_output(self, data: Any, title: Optional[str] = None) -> None:
        """Prints formatted output to the configured output file.

        Args:
            data: The data to be printed.
            title: An optional title for the output.
        """
        if self.quiet:
            return

        formatted = self.format_output(data, title)
        print(formatted, file=self.output_file)

    def print_output_with_explanation(
        self, data: Any, explanation: str, title: Optional[str] = None
    ) -> None:
        """Prints formatted output with an explanation.

        Args:
            data: The data to be printed.
            explanation: The explanation text to be included.
            title: An optional title for the output.
        """
        if self.quiet:
            return

        formatted = self.format_with_explanation(data, explanation, title)
        print(formatted, file=self.output_file)

    def print_error(self, message: str) -> None:
        """Prints an error message to stderr.

        Args:
            message: The error message to be printed.
        """
        colored_message = self.colorize(f"Error: {message}", Color.BOLD_RED)
        print(colored_message, file=sys.stderr)

    def print_warning(self, message: str) -> None:
        """Prints a warning message.

        Args:
            message: The warning message to be printed.
        """
        if self.quiet:
            return

        colored_message = self.colorize(f"Warning: {message}", Color.BOLD_YELLOW)
        print(colored_message, file=self.output_file)

    def print_info(self, message: str) -> None:
        """Prints an informational message (only in verbose mode).

        Args:
            message: The informational message to be printed.
        """
        if self.quiet or self.verbose < 1:
            return

        colored_message = self.colorize(f"Info: {message}", Color.BOLD_BLUE)
        print(colored_message, file=self.output_file)

    def print_debug(self, message: str) -> None:
        """Prints a debug message (only in high verbosity mode).

        Args:
            message: The debug message to be printed.
        """
        if self.quiet or self.verbose < DEBUG_VERBOSITY_LEVEL:
            return

        colored_message = self.colorize(f"Debug: {message}", Color.MAGENTA)
        print(colored_message, file=self.output_file)

    def print_success(self, message: str) -> None:
        """Prints a success message.

        Args:
            message: The success message to be printed.
        """
        if self.quiet:
            return

        colored_message = self.colorize(f"✓ {message}", Color.BOLD_GREEN)
        print(colored_message, file=self.output_file)

    def format_table(self, data: list, headers: list) -> str:
        """Formats the given data as a text-based table.

        Args:
            data: A list of dictionaries or lists representing the table rows.
            headers: A list of strings for the table headers.

        Returns:
            A string containing the formatted table.
        """
        return self.table_formatter.format_table(data, headers)
