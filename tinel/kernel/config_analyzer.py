# -*- coding: utf-8 -*-
"""
This module provides functionality to analyze kernel configurations for security
and performance best practices.
"""
import logging
from types import MappingProxyType
from typing import List, Mapping, Tuple

from .dataclasses import KernelConfig

logger = logging.getLogger(__name__)

# An immutable dictionary of best practices for kernel configuration.
# Format: {CONFIG_OPTION: (recommended_value, explanation)}
BEST_PRACTICES: Mapping[str, Tuple[str, str]] = MappingProxyType({
    'CONFIG_SECURITY_SELINUX': ('y', 'Enables mandatory access control for enhanced security'),
    'CONFIG_SECURITY_APPARMOR': ('y', 'Enables application-level security controls'),
    'CONFIG_STRICT_KERNEL_RWX': ('y', 'Ensures kernel memory is non-writable and non-executable'),
    'CONFIG_IKCONFIG': ('y', 'Embeds kernel config in the kernel image'),
    'CONFIG_IKCONFIG_PROC': ('y', 'Exposes kernel config via /proc/config.gz'),
    'CONFIG_DEBUG_KERNEL': ('n', 'Disables debug symbols to reduce kernel size')
})


def analyze_config(config: KernelConfig) -> List[str]:
    """
    Analyze kernel config for security/performance issues against best practices.

    It checks a given KernelConfig object against a predefined set of best
    practices, identifying missing or misconfigured kernel options.

    Args:
        config: A KernelConfig object containing the kernel options to analyze.

    Returns:
        A list of strings, where each string is an issue found in the config.
        Returns an empty list if no issues are found.

    Example:
        >>> from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption
        >>> perfect_config = KernelConfig(options=[
        ...     KernelConfigOption(name='CONFIG_SECURITY_SELINUX', value='y'),
        ...     KernelConfigOption(name='CONFIG_SECURITY_APPARMOR', value='y'),
        ...     KernelConfigOption(name='CONFIG_STRICT_KERNEL_RWX', value='y'),
        ...     KernelConfigOption(name='CONFIG_IKCONFIG', value='y'),
        ...     KernelConfigOption(name='CONFIG_IKCONFIG_PROC', value='y'),
        ...     KernelConfigOption(name='CONFIG_DEBUG_KERNEL', value='n'),
        ... ])
        >>> analyze_config(perfect_config)
        []

        >>> bad_config = KernelConfig(options=[
        ...     KernelConfigOption(name='CONFIG_SECURITY_SELINUX', value='n'),
        ...     # CONFIG_SECURITY_APPARMOR is missing
        ... ])
        >>> issues = analyze_config(bad_config)
        >>> len(issues)
        5
    """
    issues = []
    config_dict = {opt.name: opt.value for opt in config.options}

    for opt, (recommended, explanation) in BEST_PRACTICES.items():
        if opt not in config_dict:
            issues.append(f"Missing {opt}, recommended: {recommended} ({explanation})")
            logger.warning(f"Missing option: {opt}")
        elif config_dict[opt] != recommended:
            issues.append(
                f"{opt}={config_dict[opt]}, recommended: {recommended} ({explanation})"
            )
            logger.warning(f"Misconfigured option: {opt}={config_dict[opt]}")

    logger.info(f"Found {len(issues)} issues in kernel config")
    return issues