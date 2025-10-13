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

"""This module defines the configuration for the Tinel CLI.

It includes the `CLIConfig` dataclass, which holds all the configuration
settings for a CLI session, such as output format, color usage, and
verbosity. The module also provides methods for creating, validating, and
interpreting the configuration.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Optional

# Verbosity constants
MAX_VERBOSITY_LEVEL = 3


@dataclass
class CLIConfig:
    """A dataclass that holds the configuration for a CLI session.

    This class encapsulates all the settings that control the behavior of the
    CLI, such as the output format, verbosity level, and color usage. It
    provides a single, structured object for passing configuration around the
    application.

    Attributes:
        format_type: The desired output format (e.g., 'text', 'json').
        use_color: A boolean indicating whether to use color in the output.
        verbose: The verbosity level for logging.
        quiet: A boolean indicating whether to suppress all output except errors.
        config_file: An optional path to a configuration file.
    """

    format_type: str = "text"
    use_color: bool = True
    verbose: int = 0
    quiet: bool = False
    config_file: Optional[str] = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "CLIConfig":
        """Creates a `CLIConfig` instance from parsed command-line arguments.

        This class method provides a convenient way to translate the arguments
        captured by `argparse` into a structured `CLIConfig` object.

        Args:
            args: The namespace object returned by `ArgumentParser.parse_args()`.

        Returns:
            A new `CLIConfig` instance populated with the values from `args`.
        """
        return cls(
            format_type=args.format,
            use_color=not args.no_color,
            verbose=args.verbose,
            quiet=args.quiet,
            config_file=getattr(args, "config", None),
        )

    def validate(self) -> None:
        """Validates the consistency and correctness of the configuration.

        This method checks for any conflicting or invalid settings, such as
        using `verbose` and `quiet` modes simultaneously or specifying an
        unsupported output format.

        Raises:
            ValueError: If any configuration setting is found to be invalid.
        """
        if self.verbose > 0 and self.quiet:
            raise ValueError("Cannot use both verbose and quiet modes together")

        if self.verbose < 0:
            raise ValueError("Verbosity level cannot be negative")

        if self.verbose > MAX_VERBOSITY_LEVEL:
            raise ValueError(f"Maximum verbosity level is {MAX_VERBOSITY_LEVEL}")

        valid_formats = ["text", "json", "yaml", "csv"]
        if self.format_type not in valid_formats:
            raise ValueError(
                f"Invalid format '{self.format_type}'. "
                f"Valid formats: {', '.join(valid_formats)}"
            )

    @property
    def should_use_color(self) -> bool:
        """Determines whether to use color in the output.

        This property checks the `use_color` setting, environment variables
        like `NO_COLOR` and `FORCE_COLOR`, and whether `stdout` is a TTY to
        make a final decision on using color.

        Returns:
            True if color should be used, False otherwise.
        """
        # Imports moved to top

        # Respect NO_COLOR environment variable (https://no-color.org/)
        if os.environ.get("NO_COLOR"):
            return False

        # Force color if FORCE_COLOR is set
        if os.environ.get("FORCE_COLOR"):
            return True

        # Use color if explicitly enabled and stdout is a TTY
        return self.use_color and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    @property
    def log_level(self) -> str:
        """Determines the appropriate log level based on the verbosity settings.

        This property translates the `quiet` and `verbose` settings into a
        standard log level string (e.g., 'ERROR', 'WARNING', 'INFO', 'DEBUG').

        Returns:
            A string representing the calculated log level.
        """
        if self.quiet:
            return "ERROR"
        elif self.verbose == 0:
            return "WARNING"
        elif self.verbose == 1:
            return "INFO"
        else:  # verbose >= 2
            return "DEBUG"
