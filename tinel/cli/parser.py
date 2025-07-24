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
from typing import List, Optional


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
        choices=["text", "json", "yaml"],
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
        choices=["text", "json", "yaml"],
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

    # # Kernel information commands
    # _add_kernel_commands(subparsers)

    # # Log analysis commands
    # _add_log_commands(subparsers)

    # # Diagnostics commands
    # _add_diagnostics_commands(subparsers)

    # # Server commands
    # _add_server_commands(subparsers)

    return parser


def _add_hardware_commands(subparsers) -> None:
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

    # # Memory information
    # mem_parser = hw_subparsers.add_parser(
    #     'memory',
    #     aliases=['mem'],
    #     parents=[hardware_parent],
    #     help='Memory information and analysis'
    # )
    # mem_parser.add_argument(
    #     '--usage',
    #     action='store_true',
    #     help='Show memory usage statistics'
    # )
    # mem_parser.add_argument(
    #     '--timing',
    #     action='store_true',
    #     help='Show memory timing information'
    # )

    # # Storage information
    # storage_parser = hw_subparsers.add_parser(
    #     'storage',
    #     aliases=['disk'],
    #     parents=[hardware_parent],
    #     help='Storage information and analysis'
    # )
    # storage_parser.add_argument(
    #     '--health',
    #     action='store_true',
    #     help='Show storage health information'
    # )
    # storage_parser.add_argument(
    #     '--performance',
    #     action='store_true',
    #     help='Show storage performance metrics'
    # )

    # # Network information
    # net_parser = hw_subparsers.add_parser(
    #     'network',
    #     aliases=['net'],
    #     parents=[hardware_parent],
    #     help='Network hardware information'
    # )
    # net_parser.add_argument(
    #     '--interfaces',
    #     action='store_true',
    #     help='Show network interface details'
    # )

    # # Graphics information
    # gpu_parser = hw_subparsers.add_parser(
    #     'graphics',
    #     aliases=['gpu'],
    #     parents=[hardware_parent],
    #     help='Graphics hardware information'
    # )
    # gpu_parser.add_argument(
    #     '--drivers',
    #     action='store_true',
    #     help='Show graphics driver information'
    # )

    # # PCI devices
    # pci_parser = hw_subparsers.add_parser(
    #     'pci',
    #     parents=[hardware_parent],
    #     help='PCI devices information'
    # )
    # pci_parser.add_argument(
    #     '--tree',
    #     action='store_true',
    #     help='Show PCI device tree'
    # )

    # # USB devices
    # usb_parser = hw_subparsers.add_parser(
    #     'usb',
    #     parents=[hardware_parent],
    #     help='USB devices information'
    # )
    # usb_parser.add_argument(
    #     '--tree',
    #     action='store_true',
    #     help='Show USB device tree'
    # )

    # All hardware information
    all_parser = hw_subparsers.add_parser(
        "all", parents=[hardware_parent], help="All hardware information"
    )

    all_parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary instead of detailed information",
    )


# def _add_kernel_commands(subparsers) -> None:
#     """Add kernel-related commands to the parser."""
#     # Kernel parent parser for common options
#     kernel_parent = argparse.ArgumentParser(add_help=False)
#     kernel_parent.add_argument(
#         '--detailed',
#         action='store_true',
#         help='Show detailed information'
#     )

#     # Add global options to kernel parent
#     _add_global_options(kernel_parent)

#     # Main kernel command
#     kernel_parser = subparsers.add_parser(
#         'kernel',
#         parents=[kernel_parent],
#         help='Kernel information and configuration',
#         description='Get kernel information and analyze configuration'
#     )

#     kernel_subparsers = kernel_parser.add_subparsers(
#         dest='kernel_command',
#         title='Kernel Commands',
#         help='Kernel command to execute'
#     )

#     # Kernel information
#     info_parser = kernel_subparsers.add_parser(
#         'info',
#         parents=[kernel_parent],
#         help='Kernel version and basic information'
#     )

#     # Kernel configuration
#     config_parser = kernel_subparsers.add_parser(
#         'config',
#         parents=[kernel_parent],
#         help='Kernel configuration analysis'
#     )
#     config_parser.add_argument(
#         '--analyze',
#         action='store_true',
#         help='Analyze configuration for security and performance'
#     )
#     config_parser.add_argument(
#         '--recommendations',
#         action='store_true',
#         help='Show configuration recommendations'
#     )
#     config_parser.add_argument(
#         '--option',
#         type=str,
#         metavar='OPTION',
#         help='Show specific configuration option'
#     )

#     # Kernel modules
#     modules_parser = kernel_subparsers.add_parser(
#         'modules',
#         parents=[kernel_parent],
#         help='Kernel modules information'
#     )
#     modules_parser.add_argument(
#         '--loaded',
#         action='store_true',
#         help='Show only loaded modules'
#     )
#     modules_parser.add_argument(
#         '--available',
#         action='store_true',
#         help='Show available modules'
#     )

#     # Kernel parameters
#     params_parser = kernel_subparsers.add_parser(
#         'parameters',
#         aliases=['params'],
#         parents=[kernel_parent],
#         help='Kernel parameters information'
#     )
#     params_parser.add_argument(
#         '--parameter',
#         type=str,
#         metavar='PARAM',
#         help='Show specific parameter value'
#     )


# def _add_log_commands(subparsers) -> None:
#     """Add log analysis commands to the parser."""
#     # Log parent parser for common options
#     log_parent = argparse.ArgumentParser(add_help=False)
#     log_parent.add_argument(
#         '--lines',
#         type=int,
#         default=100,
#         metavar='N',
#         help='Number of lines to analyze (default: 100)'
#     )
#     log_parent.add_argument(
#         '--since',
#         type=str,
#         metavar='TIME',
#         help='Analyze logs since specified time (e.g., "1 hour ago", "2023-01-01")'
#     )
#     log_parent.add_argument(
#         '--until',
#         type=str,
#         metavar='TIME',
#         help='Analyze logs until specified time'
#     )

#     # Add global options to log parent
#     _add_global_options(log_parent)

#     # Main logs command
#     logs_parser = subparsers.add_parser(
#         'logs',
#         parents=[log_parent],
#         help='Log analysis and monitoring',
#         description='Analyze system logs for issues and patterns'
#     )

#     logs_subparsers = logs_parser.add_subparsers(
#         dest='logs_command',
#         title='Log Commands',
#         help='Log command to execute'
#     )

#     # System logs
#     system_parser = logs_subparsers.add_parser(
#         'system',
#         parents=[log_parent],
#         help='System log analysis'
#     )
#     system_parser.add_argument(
#         '--source',
#         choices=['journald', 'syslog', 'kern.log', 'auth.log'],
#         default='journald',
#         help='Log source to analyze (default: journald)'
#     )

#     # Hardware logs
#     hardware_parser = logs_subparsers.add_parser(
#         'hardware',
#         parents=[log_parent],
#         help='Hardware-related log analysis'
#     )
#     hardware_parser.add_argument(
#         '--component',
#         choices=['cpu', 'memory', 'storage', 'network', 'graphics'],
#         help='Focus on specific hardware component'
#     )

#     # Kernel logs
#     kernel_parser = logs_subparsers.add_parser(
#         'kernel',
#         parents=[log_parent],
#         help='Kernel log analysis'
#     )
#     kernel_parser.add_argument(
#         '--errors-only',
#         action='store_true',
#         help='Show only kernel errors'
#     )

#     # Log summary
#     summary_parser = logs_subparsers.add_parser(
#         'summary',
#         parents=[log_parent],
#         help='Log summary and statistics'
#     )
#     summary_parser.add_argument(
#         '--critical-only',
#         action='store_true',
#         help='Show only critical issues'
#     )

#     # Analyze specific log file
#     analyze_parser = logs_subparsers.add_parser(
#         'analyze',
#         help='Analyze specific log file'
#     )
#     analyze_parser.add_argument(
#         'file',
#         type=str,
#         help='Log file path to analyze'
#     )
#     analyze_parser.add_argument(
#         '--patterns',
#         action='store_true',
#         help='Show detected patterns'
#     )


# def _add_diagnostics_commands(subparsers) -> None:
#     """Add diagnostics commands to the parser."""
#     # Diagnostics parent parser for common options
#     diag_parent = argparse.ArgumentParser(add_help=False)
#     diag_parent.add_argument(
#         '--comprehensive',
#         action='store_true',
#         help='Run comprehensive diagnostics'
#     )

#     # Add global options to diagnostics parent
#     _add_global_options(diag_parent)

#     # Main diagnostics command
#     diag_parser = subparsers.add_parser(
#         'diagnose',
#         aliases=['diag'],
#         parents=[diag_parent],
#         help='System diagnostics and analysis',
#         description='Run AI-powered system diagnostics'
#     )

#     diag_subparsers = diag_parser.add_subparsers(
#         dest='diag_command',
#         title='Diagnostics Commands',
#         help='Diagnostics command to execute'
#     )

#     # System diagnostics
#     system_parser = diag_subparsers.add_parser(
#         'system',
#         parents=[diag_parent],
#         help='Comprehensive system diagnostics'
#     )
#     system_parser.add_argument(
#         '--include-hardware',
#         action='store_true',
#         default=True,
#         help='Include hardware analysis (default: enabled)'
#     )
#     system_parser.add_argument(
#         '--include-kernel',
#         action='store_true',
#         default=True,
#         help='Include kernel analysis (default: enabled)'
#     )
#     system_parser.add_argument(
#         '--include-logs',
#         action='store_true',
#         default=True,
#         help='Include log analysis (default: enabled)'
#     )
#     system_parser.add_argument(
#         '--recommendations',
#         action='store_true',
#         help='Generate recommendations'
#     )

#     # Hardware diagnostics
#     hw_diag_parser = diag_subparsers.add_parser(
#         'hardware',
#         parents=[diag_parent],
#         help='Hardware-specific diagnostics'
#     )
#     hw_diag_parser.add_argument(
#         '--components',
#         nargs='+',
#         choices=['cpu', 'memory', 'storage', 'network', 'graphics'],
#         default=['all'],
#         help='Components to diagnose (default: all)'
#     )
#     hw_diag_parser.add_argument(
#         '--temperature',
#         action='store_true',
#         help='Include temperature monitoring'
#     )
#     hw_diag_parser.add_argument(
#         '--performance',
#         action='store_true',
#         help='Include performance analysis'
#     )
#     hw_diag_parser.add_argument(
#         '--health',
#         action='store_true',
#         help='Include health checks'
#     )

#     # Query processor
#     query_parser = diag_subparsers.add_parser(
#         'query',
#         help='Natural language query processing'
#     )
#     query_parser.add_argument(
#         'query',
#         type=str,
#         help='Natural language query about the system'
#     )
#     query_parser.add_argument(
#         '--execute',
#         action='store_true',
#         help='Execute recommended tools automatically'
#     )

#     # Recommendations
#     rec_parser = diag_subparsers.add_parser(
#         'recommendations',
#         aliases=['rec'],
#         help='Generate system recommendations'
#     )
#     rec_parser.add_argument(
#         '--focus',
#         nargs='+',
#         choices=['hardware', 'kernel', 'security', 'performance', 'maintenance'],
#         default=['all'],
#         help='Focus areas for recommendations (default: all)'
#     )
#     rec_parser.add_argument(
#         '--priority',
#         nargs='+',
#         choices=['critical', 'high', 'medium', 'low'],
#         default=['critical', 'high', 'medium', 'low'],
#         help='Priority levels to include (default: all)'
#     )
#     rec_parser.add_argument(
#         '--max-recommendations',
#         type=int,
#         default=20,
#         metavar='N',
#         help='Maximum number of recommendations (default: 20)'
#     )
#     rec_parser.add_argument(
#         '--implementation-guides',
#         action='store_true',
#         help='Include implementation guides'
#     )


# def _add_server_commands(subparsers) -> None:
#     """Add server-related commands to the parser."""
#     # Server parent parser for global options
#     server_parent = argparse.ArgumentParser(add_help=False)
#     _add_global_options(server_parent)

#     # Server command
#     server_parser = subparsers.add_parser(
#         'server',
#         parents=[server_parent],
#         help='MCP server operations',
#         description='Start and manage the MCP server'
#     )

#     server_subparsers = server_parser.add_subparsers(
#         dest='server_command',
#         title='Server Commands',
#         help='Server command to execute'
#     )

#     # Start server
#     start_parser = server_subparsers.add_parser(
#         'start',
#         parents=[server_parent],
#         help='Start the MCP server'
#     )
#     start_parser.add_argument(
#         '--host',
#         type=str,
#         default='localhost',
#         help='Server host (default: localhost)'
#     )
#     start_parser.add_argument(
#         '--port',
#         type=int,
#         default=8000,
#         help='Server port (default: 8000)'
#     )
#     start_parser.add_argument(
#         '--debug',
#         action='store_true',
#         help='Enable debug mode'
#     )

#     # List tools
#     list_parser = server_subparsers.add_parser(
#         'list-tools',
#         parents=[server_parent],
#         help='List available MCP tools'
#     )
#     list_parser.add_argument(
#         '--category',
#         choices=['hardware', 'kernel', 'logs', 'diagnostics'],
#         help='Filter tools by category'
#     )


def validate_arguments(args) -> bool:
    """Validate parsed arguments for consistency.

    Args:
        args: Parsed arguments from ArgumentParser

    Returns:
        True if arguments are valid, False otherwise
    """
    # Check for conflicting verbosity options
    if args.verbose > 0 and args.quiet:
        print("Error: Cannot use --verbose and --quiet together", file=sys.stderr)
        return False

    # Validate verbosity level
    if args.verbose > 3:
        print("Error: Maximum verbosity level is 3 (-vvv)", file=sys.stderr)
        return False

    # Check if command is provided
    if not args.command:
        print(
            "Error: No command specified. Use --help for available commands.",
            file=sys.stderr,
        )
        return False

    # Validate format-specific options
    if args.format == "json" and args.no_color:
        # JSON output doesn't use colors anyway, so this is fine
        pass

    # Command-specific validations
    if args.command in ["hardware", "hw"]:
        if hasattr(args, "hardware_command") and not args.hardware_command:
            print(
                "Error: Hardware command requires a subcommand. Use 'tinel hardware --help' for options.",
                file=sys.stderr,
            )
            return False

    if args.command == "kernel":
        if hasattr(args, "kernel_command") and not args.kernel_command:
            print(
                "Error: Kernel command requires a subcommand. Use 'tinel kernel --help' for options.",
                file=sys.stderr,
            )
            return False

    if args.command == "logs":
        if hasattr(args, "logs_command") and not args.logs_command:
            print(
                "Error: Logs command requires a subcommand. Use 'tinel logs --help' for options.",
                file=sys.stderr,
            )
            return False

    if args.command in ["diagnose", "diag"]:
        if hasattr(args, "diag_command") and not args.diag_command:
            print(
                "Error: Diagnose command requires a subcommand. Use 'tinel diagnose --help' for options.",
                file=sys.stderr,
            )
            return False

    if args.command == "server":
        if hasattr(args, "server_command") and not args.server_command:
            print(
                "Error: Server command requires a subcommand. Use 'tinel server --help' for options.",
                file=sys.stderr,
            )
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
