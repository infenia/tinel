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

import argparse
import sys
from typing import List, Optional, Sequence

# Parser constants
MAX_VERBOSITY_LEVEL = 3


def _add_global_options(parser: argparse.ArgumentParser) -> None:
    """Add global options to a parser.

    Args:
        parser: ArgumentParser to add options to
    """
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (use -v, -vv, or -vvv)",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "yaml", "csv"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument(
        "--config", type=str, metavar="FILE", help="Configuration file path"
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="tinel",
        description="Tinel - AI-powered Linux system diagnostics and hardware analysis",
        epilog="For more information, visit: https://github.com/infenia/tinel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0 - Copyright 2025 Infenia Private Limited",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (use -v, -vv, or -vvv)",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "yaml", "csv"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument(
        "--config", type=str, metavar="FILE", help="Configuration file path"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest="command",
        title="Available Commands",
        description='Use "tinel <command> --help" for command-specific help',
        help="Command to execute",
    )

    # Hardware information commands
    _add_hardware_commands(subparsers)

    return parser


def _add_hardware_commands(subparsers: argparse._SubParsersAction) -> None:
    """Add hardware-related commands to the parser."""
    # Hardware parent parser for common options
    hardware_parent = argparse.ArgumentParser(add_help=False)
    hardware_parent.add_argument(
        "--detailed", action="store_true", help="Show detailed information"
    )

    # Add global options to hardware parent
    _add_global_options(hardware_parent)

    # Main hardware command
    hw_parser = subparsers.add_parser(
        "hardware",
        aliases=["hw"],
        parents=[hardware_parent],
        help="Hardware information and analysis",
        description="Get comprehensive hardware information and analysis",
    )

    hw_subparsers = hw_parser.add_subparsers(
        dest="hardware_command",
        title="Hardware Commands",
        help="Hardware command to execute",
    )

    # CPU information
    cpu_parser = hw_subparsers.add_parser(
        "cpu", parents=[hardware_parent], help="CPU information and analysis"
    )
    cpu_parser.add_argument(
        "--temperature", action="store_true", help="Include temperature information"
    )
    cpu_parser.add_argument(
        "--features", action="store_true", help="Show CPU features and capabilities"
    )

    # All hardware information
    all_parser = hw_subparsers.add_parser(
        "all", parents=[hardware_parent], help="All hardware information"
    )

    all_parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary instead of detailed information",
    )


def _validate_verbosity_options(args: argparse.Namespace) -> bool:
    """Validate verbosity-related arguments."""
    # Check for conflicting verbosity options
    if args.verbose > 0 and args.quiet:
        print("Error: Cannot use --verbose and --quiet together", file=sys.stderr)
        return False

    # Validate verbosity level
    if args.verbose > MAX_VERBOSITY_LEVEL:
        print(
            f"Error: Maximum verbosity level is {MAX_VERBOSITY_LEVEL} (-vvv)",
            file=sys.stderr,
        )
        return False

    return True


def _validate_basic_options(args: argparse.Namespace) -> bool:
    """Validate basic command arguments."""
    # Check if command is provided
    if not args.command:
        print(
            "Error: No command specified. Use --help for available commands.",
            file=sys.stderr,
        )
        return False

    return True


def _validate_subcommand(
    args: argparse.Namespace,
    command: str | Sequence[str],
    attr_name: str,
    help_cmd: str,
) -> bool:
    """Validate that a subcommand is provided when required."""
    if (
        (
            args.command == command
            or (isinstance(command, list) and args.command in command)
        )
        and hasattr(args, attr_name)
        and not getattr(args, attr_name)
    ):
        cmd_title = command.title() if isinstance(command, str) else command[0].title()
        print(
            f"Error: {cmd_title} command requires a subcommand. "
            f"Use '{help_cmd}' for options.",
            file=sys.stderr,
        )
        return False
    return True


def validate_arguments(args: argparse.Namespace) -> bool:
    """Validate parsed arguments for consistency.

    Args:
        args: Parsed arguments from ArgumentParser

    Returns:
        True if arguments are valid, False otherwise
    """
    # Validate verbosity options
    if not _validate_verbosity_options(args):
        return False

    # Validate basic options
    if not _validate_basic_options(args):
        return False

    # Command-specific validations
    validations = [
        (["hardware", "hw"], "hardware_command", "tinel hardware --help"),
        ("kernel", "kernel_command", "tinel kernel --help"),
        ("logs", "logs_command", "tinel logs --help"),
        (["diagnose", "diag"], "diag_command", "tinel diagnose --help"),
        ("server", "server_command", "tinel server --help"),
    ]

    for command, attr_name, help_cmd in validations:
        if not _validate_subcommand(args, command, attr_name, help_cmd):
            return False

    return True


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Parsed arguments namespace

    Raises:
        SystemExit: If arguments are invalid or help is requested
    """
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    if not validate_arguments(args):
        sys.exit(1)

    return args
