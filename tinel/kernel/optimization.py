#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kernel configuration optimization module for Tinel.

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
from typing import Dict, List

from .dataclasses import KernelConfig, KernelConfigOption

logger = logging.getLogger(__name__)


def recommend_optimizations(
    config: KernelConfig, hardware_info: Dict
) -> List[KernelConfigOption]:
    """Recommend kernel config optimizations based on hardware and current config.

    Examples:
        >>> from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption
        >>> config = KernelConfig(options=[
        ...     KernelConfigOption(name='CONFIG_CPU_FREQ_GOV_PERFORMANCE', value='n'),
        ...     KernelConfigOption(name='CONFIG_HUGETLBFS', value='n'),
        ...     KernelConfigOption(name='CONFIG_64BIT', value='y'),
        ... ])
        >>> hardware = {'cpu': {'topology': {'logical_cpus': 4}, 'architecture': 'x86_64'}, 'memory': {'total_memory_bytes': 32 * 1024**3}}
        >>> recommendations = recommend_optimizations(config, hardware)
        >>> for rec in recommendations:
        ...     print(f'{rec.name}={rec.recommended}')
        CONFIG_CPU_FREQ_GOV_PERFORMANCE=y
        CONFIG_HUGETLBFS=y

    Args:
        config: The current kernel configuration.
        hardware_info: A dictionary containing hardware information.

    Returns:
        A list of recommended kernel configuration options.
    """
    recommendations = []
    config_dict = {opt.name: opt.value for opt in config.options}

    # Default hardware info if unavailable
    hardware_info = hardware_info or {}

    # Extract hardware details with fallbacks
    cpu_info = hardware_info.get("cpu", {})
    cpu_topology = cpu_info.get("topology", {})
    cpu_cores = cpu_topology.get("logical_cpus", 1)
    architecture = cpu_info.get("architecture", "x86_64")

    memory_info = hardware_info.get("memory", {})
    total_memory_bytes = memory_info.get("total_memory_bytes", 4 * 1024**3)
    memory_gb = total_memory_bytes / (1024**3)

    # Multi-core CPU: Enable performance governor
    if cpu_cores > 1:
        if config_dict.get("CONFIG_CPU_FREQ_GOV_PERFORMANCE", "n") != "y":
            recommendations.append(
                KernelConfigOption(
                    name="CONFIG_CPU_FREQ_GOV_PERFORMANCE",
                    value=config_dict.get("CONFIG_CPU_FREQ_GOV_PERFORMANCE", "n"),
                    recommended="y",
                )
            )
            logger.info(
                "Recommended CONFIG_CPU_FREQ_GOV_PERFORMANCE=y for multi-core CPU"
            )

    # High memory: Enable huge pages
    if memory_gb >= 16:
        if config_dict.get("CONFIG_HUGETLBFS", "n") != "y":
            recommendations.append(
                KernelConfigOption(
                    name="CONFIG_HUGETLBFS",
                    value=config_dict.get("CONFIG_HUGETLBFS", "n"),
                    recommended="y",
                )
            )
            logger.info("Recommended CONFIG_HUGETLBFS=y for high memory")

    # Architecture-specific recommendations
    if architecture == "x86_64":
        if config_dict.get("CONFIG_MCORE2", "n") != "y":
            recommendations.append(
                KernelConfigOption(
                    name="CONFIG_MCORE2",
                    value=config_dict.get("CONFIG_MCORE2", "n"),
                    recommended="y",
                )
            )
            logger.info("Recommended CONFIG_MCORE2=y for x86_64 architecture")
        # Also recommend 64BIT if not set, as a baseline
        if config_dict.get("CONFIG_64BIT", "n") != "y":
            recommendations.append(
                KernelConfigOption(
                    name="CONFIG_64BIT",
                    value=config_dict.get("CONFIG_64BIT", "n"),
                    recommended="y",
                )
            )
            logger.info("Recommended CONFIG_64BIT=y for x86_64 architecture")
    elif architecture == "aarch64":
        if config_dict.get("CONFIG_ARM64_64K_PAGES", "n") != "y":
            recommendations.append(
                KernelConfigOption(
                    name="CONFIG_ARM64_64K_PAGES",
                    value=config_dict.get("CONFIG_ARM64_64K_PAGES", "n"),
                    recommended="y",
                )
            )
            logger.info(
                "Recommended CONFIG_ARM64_64K_PAGES=y for aarch64 architecture"
            )

    return recommendations