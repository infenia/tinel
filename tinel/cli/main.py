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
import time
from typing import Any, List, Optional

from .commands import CommandRouter
from .config import CLIConfig
from .error_handler import CLIErrorHandler
from .formatters import OutputFormatter
from .parser import parse_arguments

"""This module serves as the main entry point for the Tinel command-line tool.

It is responsible for orchestrating the entire CLI workflow, including parsing
arguments, setting up logging, handling errors, and routing commands to their
respective handlers. The `main` function is the primary function that is
executed when the tool is run.
"""

# CLI constants
DEBUG_VERBOSITY_THRESHOLD = 2
MAX_ARGUMENTS_COUNT = 100
MAX_ARGUMENT_LENGTH = 1000


# Command router initialization
def _get_command_router(formatter: Any, error_handler: Any) -> Any:
    """Initializes and returns the command router.

    Args:
        formatter: The output formatter to be used by the commands.
        error_handler: The error handler to be used by the commands.

    Returns:
        An instance of the `CommandRouter`.
    """
    # Import moved to top

    return CommandRouter(formatter, error_handler)


def setup_logging(verbosity: int, quiet: bool) -> None:
    """Configures the logging for the application.

    This function sets up the logging level and format based on the user-
    specified verbosity and quiet settings.

    Args:
        verbosity: The verbosity level (0-3).
        quiet: A boolean indicating whether to suppress all output except
               errors.
    """
    if quiet:
        level = logging.ERROR
    elif verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity == DEBUG_VERBOSITY_THRESHOLD:
        level = logging.DEBUG
    else:  # verbosity >= 3
        level = logging.DEBUG

    # Configure logging format with more context for debugging
    if verbosity >= DEBUG_VERBOSITY_THRESHOLD:
        format_str = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
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
    if verbosity < DEBUG_VERBOSITY_THRESHOLD:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    # Log the initialization
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging initialized with verbosity={verbosity}, quiet={quiet}")


def _validate_and_sanitize_argv(argv: Optional[List[str]]) -> Optional[List[str]]:
    """Validates and sanitizes the raw command-line arguments.

    This function performs basic security and sanity checks on the command-
    line arguments, such as checking for a reasonable number of arguments and
    argument length.

    Args:
        argv: The raw list of command-line arguments.

    Returns:
        A sanitized list of arguments, or None if the input is None.

    Raises:
        ValueError: If the arguments are found to be invalid.
    """
    if argv is None:
        return None

    # Reasonable limits to prevent abuse
    if len(argv) > MAX_ARGUMENTS_COUNT:
        raise ValueError(
            f"Too many arguments provided (maximum: {MAX_ARGUMENTS_COUNT})"
        )

    # Sanitize arguments - remove empty strings and strip whitespace
    sanitized = []
    for arg in argv:
        if not isinstance(arg, str):
            raise ValueError(f"Invalid argument type: {type(arg).__name__}")

        stripped = arg.strip()
        if stripped:  # Only keep non-empty arguments
            # Basic security check - prevent extremely long arguments
            if len(stripped) > MAX_ARGUMENT_LENGTH:
                raise ValueError(
                    f"Argument too long (maximum: {MAX_ARGUMENT_LENGTH} characters): "
                    f"{stripped[:50]}..."
                )
            sanitized.append(stripped)

    return sanitized


def display_banner() -> None:
    """Displays the Tinel ASCII art banner.

    This function prints a banner with the Tinel logo and a brief description
    of the tool. It is displayed at the start of the application unless the
    `--quiet` flag is used.
    """
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


def main(argv: Optional[List[str]] = None) -> int:  # noqa: PLR0911
    """The main entry point for the Tinel CLI.

    This function orchestrates the entire lifecycle of a CLI command, from
    parsing arguments to executing the command and handling any errors that
    occur.

    Args:
        argv: A list of command-line arguments. If not provided, `sys.argv`
              is used.

    Returns:
        An integer exit code (0 for success, non-zero for errors).
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
        if e.code is None:
            return 0
        elif isinstance(e.code, int):
            return e.code
        else:
            return 1  # Convert string codes to 1
    except Exception as e:
        return _handle_unexpected_error(e)


def _execute_main_logic(argv: Optional[List[str]]) -> int:
    """Executes the core logic of the application.

    This function is responsible for parsing arguments, setting up the
    configuration and logging, and executing the requested command.

    Args:
        argv: The sanitized list of command-line arguments.

    Returns:
        The exit code from the command execution.
    """

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

        return result  # type: ignore[no-any-return]

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"CLI execution failed after {execution_time:.3f}s: {e}")
        raise


def _handle_keyboard_interrupt() -> int:
    """Handles a `KeyboardInterrupt` (Ctrl+C) gracefully.

    Returns:
        The standard exit code for a `SIGINT` signal (130).
    """
    print("\nOperation cancelled by user.", file=sys.stderr)
    return 130  # Standard SIGINT exit code


def _handle_unexpected_error(error: Exception) -> int:
    """Handles an unexpected error that occurs during initialization.

    This function is a fallback for when the main error handler has not yet
    been initialized.

    Args:
        error: The unexpected exception that occurred.

    Returns:
        A general error exit code (1).
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
