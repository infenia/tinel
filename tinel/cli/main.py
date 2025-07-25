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

import logging
import sys
from typing import List, Optional

from .config import CLIConfig
from .error_handler import CLIErrorHandler
from .formatters import OutputFormatter
from .parser import parse_arguments


# Lazy import for CommandRouter to improve startup time
def _get_command_router(formatter, error_handler):
    """Lazy load command router to improve startup performance."""
    from .commands import CommandRouter

    return CommandRouter(formatter, error_handler)


def setup_logging(verbosity: int, quiet: bool) -> None:
    """Set up logging based on verbosity level.

    Args:
        verbosity: Verbosity level (0-3)
        quiet: Whether to suppress output
    """
    if quiet:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity == 2:
        level = logging.DEBUG
    else:  # verbosity >= 3
        level = logging.DEBUG

    # Configure logging format with more context for debugging
    if verbosity >= 2:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    elif verbosity >= 1:
        format_str = "%(asctime)s - %(levelname)s - %(message)s"
    else:
        format_str = "%(levelname)s: %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,  # Override any existing configuration
    )

    # Suppress some noisy loggers unless in debug mode
    if verbosity < 2:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    # Log the initialization
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging initialized with verbosity={verbosity}, quiet={quiet}")


def _validate_and_sanitize_argv(argv: Optional[List[str]]) -> Optional[List[str]]:
    """Validate and sanitize command line arguments.

    Args:
        argv: Raw command line arguments

    Returns:
        Sanitized arguments or None if invalid

    Raises:
        ValueError: If arguments are invalid
    """
    if argv is None:
        return None

    # Reasonable limits to prevent abuse
    if len(argv) > 100:
        raise ValueError("Too many arguments provided (maximum: 100)")

    # Sanitize arguments - remove empty strings and strip whitespace
    sanitized = []
    for arg in argv:
        if not isinstance(arg, str):
            raise ValueError(f"Invalid argument type: {type(arg).__name__}")

        stripped = arg.strip()
        if stripped:  # Only keep non-empty arguments
            # Basic security check - prevent extremely long arguments
            if len(stripped) > 1000:
                raise ValueError(
                    f"Argument too long (maximum: 1000 characters): {stripped[:50]}..."
                )
            sanitized.append(stripped)

    return sanitized


def display_banner():
    """Display Tinel banner with Infenia attribution."""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║  ████████╗██╗███╗   ██╗███████╗██╗                       ║
    ║  ╚══██╔══╝██║████╗  ██║██╔════╝██║                       ║
    ║     ██║   ██║██╔██╗ ██║█████╗  ██║                       ║
    ║     ██║   ██║██║╚██╗██║██╔══╝  ██║                       ║
    ║     ██║   ██║██║ ╚████║███████╗███████╗                  ║
    ║     ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝                  ║
    ║                                                          ║
    ║  Terminal Intelligence for Linux Systems                 ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Display banner unless running in quiet mode
        if argv is None or not any(arg in ["-q", "--quiet"] for arg in argv):
            display_banner()

        # Validate and sanitize input arguments
        sanitized_argv = _validate_and_sanitize_argv(argv)
        return _execute_main_logic(sanitized_argv)
    except ValueError as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return _handle_keyboard_interrupt()
    except SystemExit as e:
        # SystemExit with None code should return 0 (success)
        # SystemExit with no arguments defaults to code=None
        return e.code if e.code is not None else 0
        raise
    except Exception as e:
        return _handle_unexpected_error(e)


def _execute_main_logic(argv: Optional[List[str]]) -> int:
    """Execute the main application logic.

    Args:
        argv: Command line arguments

    Returns:
        Exit code from command execution
    """
    import time

    start_time = time.time()
    logger = logging.getLogger(__name__)

    try:
        # Parse command line arguments
        args = parse_arguments(argv)

        # Create and validate configuration
        config = CLIConfig.from_args(args)
        config.validate()

        # Set up logging using configuration
        setup_logging(config.verbose, config.quiet)

        # Log execution start
        logger.info(
            f"CLI execution started with command: {getattr(args, 'command', 'none')}"
        )

        # Create output formatter using configuration
        formatter = OutputFormatter(
            format_type=config.format_type,
            use_color=config.should_use_color,
            verbose=config.verbose,
            quiet=config.quiet,
        )

        # Create error handler
        error_handler = CLIErrorHandler(formatter)

        # Create command router (lazy loaded)
        router = _get_command_router(formatter, error_handler)

        # Execute the command
        result = router.execute_command(args)

        # Log successful completion
        execution_time = time.time() - start_time
        logger.info(f"CLI execution completed successfully in {execution_time:.3f}s")

        return result

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"CLI execution failed after {execution_time:.3f}s: {e}")
        raise


def _handle_keyboard_interrupt() -> int:
    """Handle keyboard interrupt (Ctrl+C) gracefully.

    Returns:
        Standard exit code for SIGINT (130)
    """
    print("\nOperation cancelled by user.", file=sys.stderr)
    return 130  # Standard SIGINT exit code


def _handle_unexpected_error(error: Exception) -> int:
    """Handle unexpected errors when error handler is not available.

    Args:
        error: The unexpected exception

    Returns:
        Error exit code (1)
    """
    logging.exception("Unexpected error occurred during CLI initialization")
    print(f"Fatal error: {error}", file=sys.stderr)
    print(
        "This appears to be an internal error. Please report this issue.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
