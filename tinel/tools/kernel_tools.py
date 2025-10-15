#!/usr/bin/env python3
"""
Kernel-related tools for Tinel.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import logging
from typing import Dict, Optional

from tinel.kernel.config_analyzer import analyze_config
from tinel.kernel.config_parser import parse_kernel_config
from tinel.kernel.optimization import recommend_optimizations

logger = logging.getLogger(__name__)


def run_kernel_config_check(
    config_path: str, hardware_info: Optional[Dict] = None
) -> dict:
    """
    Run a complete kernel configuration check.

    :param config_path: Path to the kernel config file.
    :param hardware_info: A dictionary containing hardware information.
    :return: A dictionary with the analysis results.
    """
    try:
        config = parse_kernel_config(config_path)
        issues = analyze_config(config)
        recommendations = recommend_optimizations(config, hardware_info)
        return {
            "config": config,
            "issues": issues,
            "recommendations": recommendations,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Kernel config check failed: {e}", exc_info=True)
        return {
            "config": None,
            "issues": [],
            "recommendations": [],
            "error": f"Failed to process kernel config: {e}",
        }
