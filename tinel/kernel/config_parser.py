# -*- coding: utf-8 -*-
"""
This module provides functionality to parse kernel configuration files.
"""

import gzip
import logging
from pathlib import Path
from typing import Optional

from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption

logger = logging.getLogger(__name__)


def parse_kernel_config(path: str) -> KernelConfig:
    """Parse a kernel config file (gzipped or plain) into a KernelConfig object.

    This function supports both gzipped (.gz) and plain text files. It reads
    the file line by line, parsing valid configuration options and skipping
    comments or malformed lines.

    Args:
        path: The full path to the kernel configuration file.

    Returns:
        A KernelConfig object containing the parsed options.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        PermissionError: If there is a permission error accessing the file.
        gzip.BadGzipFile: If the file is a .gz file but is not a valid gzip file.
    """
    options = []
    file_path = Path(path)
    logger.info(f"Parsing kernel config from {path}")

    try:
        if file_path.suffix == '.gz':
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                for line in f:
                    option = _parse_line(line)
                    if option:
                        options.append(option)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    option = _parse_line(line)
                    if option:
                        options.append(option)
    except FileNotFoundError:
        logger.error(f"Kernel config file not found: {path}")
        raise
    except PermissionError:
        logger.error(f"Permission denied accessing {path}")
        raise
    except gzip.BadGzipFile:
        logger.error(f"Invalid gzip file: {path}")
        raise

    logger.info(f"Parsed {len(options)} valid options from {path}")
    return KernelConfig(options=options)


def _parse_line(line: str) -> Optional[KernelConfigOption]:
    """Parse a single line into a KernelConfigOption, skipping comments or invalid lines.

    A valid line is in the format `CONFIG_NAME=value` where value is one of
    'y', 'm', or 'n'. Lines starting with '#' (comments) and malformed lines
    are skipped.

    Args:
        line: The line to parse.

    Returns:
        A KernelConfigOption if the line is valid, otherwise None.
    """
    line = line.strip()

    if not line or line.startswith('#') or '=' not in line:
        return None

    name, value = line.split('=', 1)
    name, value = name.strip(), value.strip()

    try:
        # The KernelConfigOption dataclass validates that value is 'y', 'n', or 'm'.
        # A ValueError will be raised for any other value.
        return KernelConfigOption(name=name, value=value)
    except ValueError:
        logger.warning(f"Skipping invalid option (value not in y/n/m): {line}")
        return None