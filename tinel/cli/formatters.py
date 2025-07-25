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
import sys
from abc import ABC, abstractmethod
from enum import Enum
from io import StringIO
from typing import Any, Dict, List, Optional, TextIO

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Constants for commonly used strings
class StatusValues:
    """Common status values for color coding."""

    POSITIVE = ["ok", "good", "healthy", "normal", "active", "enabled"]
    NEGATIVE = ["error", "failed", "critical", "bad", "unhealthy", "disabled"]
    WARNING = ["warning", "caution", "degraded", "inactive"]


class LogSources:
    """Common log source names."""

    JOURNALD = "journald"
    SYSLOG = "syslog"
    KERN_LOG = "kern.log"
    DMESG = "dmesg"
    AUTH_LOG = "auth.log"


class Color:
    """ANSI color codes for terminal output."""

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
    """Output format types."""

    TEXT = "text"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"


class BaseFormatter(ABC):
    """Abstract base class for data formatters."""

    @abstractmethod
    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Format data according to the specific format type.

        Args:
            data: Data to format
            title: Optional title for the output

        Returns:
            Formatted string
        """
        pass


class JSONFormatter(BaseFormatter):
    """JSON formatter implementation."""

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)


class YAMLFormatter(BaseFormatter):
    """YAML formatter implementation."""

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Format data as YAML."""
        if not YAML_AVAILABLE:
            raise RuntimeError(
                "YAML formatting requires PyYAML. Install with: pip install PyYAML"
            )

        result = yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        return str(result)


class CSVFormatter(BaseFormatter):
    """CSV formatter implementation."""

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Format data as CSV."""
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
        """Format dictionary as CSV with key-value pairs."""
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
        """Format list as CSV."""
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
        """Flatten nested dictionary for CSV output."""
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
    """Text formatter implementation."""

    def __init__(self, colorizer: Any, quiet: bool = False, verbose: int = 0):
        """Initialize text formatter.

        Args:
            colorizer: Color utility instance
            quiet: Whether to suppress non-essential output
            verbose: Verbosity level
        """
        self.colorizer = colorizer
        self.quiet = quiet
        self.verbose = verbose

    def format(self, data: Any, title: Optional[str] = None) -> str:
        """Format data as human-readable text."""
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
        if self.verbose >= 2 and isinstance(data, dict):
            lines.extend(self._add_verbose_info(data))

        return "\n".join(lines)

    def _format_minimal_text(self, data: Any) -> str:
        """Format data as minimal text suitable for scripting."""
        if isinstance(data, dict):
            return self._format_minimal_dict(data)
        elif isinstance(data, list):
            return self._format_minimal_list(data)
        else:
            return str(data)

    def _format_minimal_dict(self, data: Dict[str, Any], prefix: str = "") -> str:
        """Format dictionary as minimal text lines."""
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
        """Format list as minimal text lines."""
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
        """Format dictionary as text lines."""
        lines = []
        indent_str = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(
                    f"{indent_str}{self.colorizer.colorize(key + ':', Color.BOLD_WHITE)}"
                )
                lines.extend(self._format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(
                    f"{indent_str}{self.colorizer.colorize(key + ':', Color.BOLD_WHITE)}"
                )
                lines.extend(self._format_list(value, indent + 1))
            else:
                formatted_value = self._format_value(value)
                lines.append(
                    f"{indent_str}{self.colorizer.colorize(key + ':', Color.BOLD_WHITE)} {formatted_value}"
                )

        return lines

    def _format_list(self, data: list, indent: int = 0) -> List[str]:
        """Format list as text lines."""
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
                lines.append(
                    f"{indent_str}{self.colorizer.colorize('-', Color.YELLOW)} {formatted_value}"
                )

        return lines

    def _format_value(self, value: Any) -> str:
        """Format individual values with appropriate colors."""
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
        """Add verbose information about the data."""
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
    """Factory for creating formatter instances."""

    @staticmethod
    def create_formatter(
        format_type: FormatType, colorizer: Any = None, quiet: bool = False, verbose: int = 0
    ) -> BaseFormatter:
        """Create a formatter instance based on format type.

        Args:
            format_type: Type of formatter to create
            colorizer: Color utility instance (for text formatter)
            quiet: Whether to suppress non-essential output
            verbose: Verbosity level

        Returns:
            Formatter instance

        Raises:
            ValueError: If format type is not supported
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
    """Utility class for color operations."""

    def __init__(self, use_color: bool = True):
        """Initialize color utility.

        Args:
            use_color: Whether to use colored output
        """
        self.use_color = use_color and self._supports_color()

    def colorize(self, text: str, color: str) -> str:
        """Apply color to text if color is enabled.

        Args:
            text: Text to colorize
            color: Color code from Color class

        Returns:
            Colorized text or original text if color is disabled
        """
        if not self.use_color:
            return text
        return f"{color}{text}{Color.RESET}"

    def _supports_color(self) -> bool:
        """Check if the terminal supports color output."""
        import os

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
    """Specialized formatter for table data."""

    def __init__(self, colorizer: ColorUtility):
        """Initialize table formatter.

        Args:
            colorizer: Color utility instance
        """
        self.colorizer = colorizer

    def format_table(self, data: list, headers: list) -> str:
        """Format data as a table.

        Args:
            data: List of dictionaries or lists representing table rows
            headers: List of column headers

        Returns:
            Formatted table string
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
        """Calculate optimal column widths."""
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
        """Format table header line."""
        return " | ".join(
            self.colorizer.colorize(header.ljust(width), Color.BOLD_WHITE)
            for header, width in zip(headers, col_widths, strict=False)
        )

    def _format_separator_line(self, col_widths: List[int]) -> str:
        """Format table separator line."""
        separator = "-+-".join("-" * width for width in col_widths)
        return self.colorizer.colorize(separator, Color.CYAN)

    def _format_data_lines(
        self, data: list, headers: list, col_widths: List[int]
    ) -> List[str]:
        """Format table data lines."""
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
        """Format individual cell values with appropriate colors."""
        if value.lower() in StatusValues.POSITIVE:
            return self.colorizer.colorize(value, Color.GREEN)
        elif value.lower() in StatusValues.NEGATIVE:
            return self.colorizer.colorize(value, Color.RED)
        elif value.lower() in StatusValues.WARNING:
            return self.colorizer.colorize(value, Color.YELLOW)
        else:
            return value


class OutputFormatter:
    """Handles output formatting for different formats and styles."""

    def __init__(
        self,
        format_type: str = "text",
        use_color: bool = True,
        verbose: int = 0,
        quiet: bool = False,
        output_file: Optional[TextIO] = None,
    ):
        """Initialize the output formatter.

        Args:
            format_type: Output format ('text', 'json', 'yaml', 'csv')
            use_color: Whether to use colored output
            verbose: Verbosity level (0-3)
            quiet: Whether to suppress non-error output
            output_file: Output file (defaults to stdout)
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
        """Apply color to text if color is enabled.

        Args:
            text: Text to colorize
            color: Color code from Color class

        Returns:
            Colorized text or original text if color is disabled
        """
        return self.colorizer.colorize(text, color)

    def format_output(self, data: Any, title: Optional[str] = None) -> str:
        """Format data according to the specified format type.

        Args:
            data: Data to format
            title: Optional title for the output

        Returns:
            Formatted string
        """
        return self.formatter.format(data, title)

    def format_with_explanation(
        self, data: Any, explanation: str, title: Optional[str] = None
    ) -> str:
        """Format data with explanation for verbose mode.

        Args:
            data: Data to format
            explanation: Explanation text
            title: Optional title for the output

        Returns:
            Formatted string with explanation
        """
        lines = [self.format_output(data, title)]

        if self._should_include_explanation(explanation):
            lines.extend(self._format_explanation_section(explanation))

        return "\n".join(lines)

    def _should_include_explanation(self, explanation: str) -> bool:
        """Check if explanation should be included in output."""
        return bool(self.verbose >= 1 and explanation and not self.quiet)

    def _format_explanation_section(self, explanation: str) -> List[str]:
        """Format the explanation section with proper wrapping."""
        lines = [""]
        lines.append(self.colorize("Explanation:", Color.BOLD_YELLOW))
        lines.append(self.colorize("-" * 12, Color.YELLOW))

        for line in explanation.split("\n"):
            lines.extend(self._wrap_text_line(line))

        return lines

    def _wrap_text_line(self, line: str, max_width: int = 80) -> List[str]:
        """Wrap a single line of text to specified width."""
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
        """Print formatted output to the output file.

        Args:
            data: Data to print
            title: Optional title for the output
        """
        if self.quiet:
            return

        formatted = self.format_output(data, title)
        print(formatted, file=self.output_file)

    def print_output_with_explanation(
        self, data: Any, explanation: str, title: Optional[str] = None
    ) -> None:
        """Print formatted output with explanation to the output file.

        Args:
            data: Data to print
            explanation: Explanation text
            title: Optional title for the output
        """
        if self.quiet:
            return

        formatted = self.format_with_explanation(data, explanation, title)
        print(formatted, file=self.output_file)

    def print_error(self, message: str) -> None:
        """Print error message to stderr.

        Args:
            message: Error message to print
        """
        colored_message = self.colorize(f"Error: {message}", Color.BOLD_RED)
        print(colored_message, file=sys.stderr)

    def print_warning(self, message: str) -> None:
        """Print warning message.

        Args:
            message: Warning message to print
        """
        if self.quiet:
            return

        colored_message = self.colorize(f"Warning: {message}", Color.BOLD_YELLOW)
        print(colored_message, file=self.output_file)

    def print_info(self, message: str) -> None:
        """Print info message (only if verbose).

        Args:
            message: Info message to print
        """
        if self.quiet or self.verbose < 1:
            return

        colored_message = self.colorize(f"Info: {message}", Color.BOLD_BLUE)
        print(colored_message, file=self.output_file)

    def print_debug(self, message: str) -> None:
        """Print debug message (only if very verbose).

        Args:
            message: Debug message to print
        """
        if self.quiet or self.verbose < 2:
            return

        colored_message = self.colorize(f"Debug: {message}", Color.MAGENTA)
        print(colored_message, file=self.output_file)

    def print_success(self, message: str) -> None:
        """Print success message.

        Args:
            message: Success message to print
        """
        if self.quiet:
            return

        colored_message = self.colorize(f"✓ {message}", Color.BOLD_GREEN)
        print(colored_message, file=self.output_file)

    def format_table(self, data: list, headers: list) -> str:
        """Format data as a table.

        Args:
            data: List of dictionaries or lists representing table rows
            headers: List of column headers

        Returns:
            Formatted table string
        """
        return self.table_formatter.format_table(data, headers)
