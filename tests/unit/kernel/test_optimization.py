#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the kernel optimization module.

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

import unittest
from typing import Dict
from unittest.mock import patch

from tests.utils import create_mock_config_file
from tinel.kernel.config_parser import parse_kernel_config
from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption
from tinel.kernel.optimization import recommend_optimizations

# Constants for magic numbers
HIGH_MEMORY_GB = 16


class TestRecommendOptimizations(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.base_config_options = [
            KernelConfigOption(name="CONFIG_CPU_FREQ_GOV_PERFORMANCE", value="n"),
            KernelConfigOption(name="CONFIG_HUGETLBFS", value="n"),
            KernelConfigOption(name="CONFIG_MCORE2", value="n"),
            KernelConfigOption(name="CONFIG_ARM64_64K_PAGES", value="n"),
            KernelConfigOption(name="CONFIG_64BIT", value="n"),
        ]

    def _get_hardware_info(self, cores=1, arch="x86_64", memory_gb=4) -> Dict:
        """Helper to generate hardware_info dictionary."""
        return {
            "cpu": {
                "topology": {"logical_cpus": cores},
                "architecture": arch,
            },
            "memory": {
                "total_memory_bytes": memory_gb * (1024**3),
            },
        }

    def test_multicore_high_memory_x86_64(self):
        """Test recommendations for a powerful x86_64 machine."""
        config = KernelConfig(options=self.base_config_options)
        hardware_info = self._get_hardware_info(
            cores=8, memory_gb=HIGH_MEMORY_GB, arch="x86_64"
        )

        recommendations = recommend_optimizations(config, hardware_info)
        rec_names = {rec.name for rec in recommendations}

        self.assertIn("CONFIG_CPU_FREQ_GOV_PERFORMANCE", rec_names)
        self.assertIn("CONFIG_HUGETLBFS", rec_names)
        self.assertIn("CONFIG_MCORE2", rec_names)
        self.assertIn("CONFIG_64BIT", rec_names)
        self.assertNotIn("CONFIG_ARM64_64K_PAGES", rec_names)

    def test_single_core_low_memory(self):
        """Test with a single-core, low-memory machine."""
        config = KernelConfig(options=self.base_config_options)
        hardware_info = self._get_hardware_info(cores=1, memory_gb=4)

        recommendations = recommend_optimizations(config, hardware_info)
        rec_names = {rec.name for rec in recommendations}

        self.assertNotIn("CONFIG_CPU_FREQ_GOV_PERFORMANCE", rec_names)
        self.assertNotIn("CONFIG_HUGETLBFS", rec_names)

    def test_aarch64_architecture(self):
        """Test recommendations for an aarch64 machine."""
        config = KernelConfig(options=self.base_config_options)
        hardware_info = self._get_hardware_info(
            cores=8, memory_gb=HIGH_MEMORY_GB, arch="aarch64"
        )

        recommendations = recommend_optimizations(config, hardware_info)
        rec_names = {rec.name for rec in recommendations}

        self.assertIn("CONFIG_CPU_FREQ_GOV_PERFORMANCE", rec_names)
        self.assertIn("CONFIG_HUGETLBFS", rec_names)
        self.assertIn("CONFIG_ARM64_64K_PAGES", rec_names)
        self.assertNotIn("CONFIG_MCORE2", rec_names)
        self.assertNotIn("CONFIG_64BIT", rec_names)

    def test_no_recommendations_for_optimized_config(self):
        """Test that no recommendations are made for a fully optimized config."""
        optimized_options = [
            KernelConfigOption(name="CONFIG_CPU_FREQ_GOV_PERFORMANCE", value="y"),
            KernelConfigOption(name="CONFIG_HUGETLBFS", value="y"),
            KernelConfigOption(name="CONFIG_MCORE2", value="y"),
            KernelConfigOption(name="CONFIG_64BIT", value="y"),
        ]
        config = KernelConfig(options=optimized_options)
        hardware_info = self._get_hardware_info(
            cores=8, memory_gb=HIGH_MEMORY_GB, arch="x86_64"
        )

        recommendations = recommend_optimizations(config, hardware_info)
        self.assertEqual(len(recommendations), 0)

    def test_missing_hardware_info(self):
        """Test fallback behavior when hardware_info is missing or empty."""
        config = KernelConfig(options=self.base_config_options)

        # Test with None
        recommendations_none = recommend_optimizations(config, None)
        self.assertEqual(len(recommendations_none), 2)
        rec_names_none = {rec.name for rec in recommendations_none}
        self.assertIn("CONFIG_MCORE2", rec_names_none)
        self.assertIn("CONFIG_64BIT", rec_names_none)

        # Test with empty dict
        recommendations_empty = recommend_optimizations(config, {})
        self.assertEqual(len(recommendations_empty), 2)
        rec_names_empty = {rec.name for rec in recommendations_empty}
        self.assertIn("CONFIG_MCORE2", rec_names_empty)
        self.assertIn("CONFIG_64BIT", rec_names_empty)

    def test_partially_missing_hardware_info(self):
        """Test fallback with partially missing hardware info."""
        config = KernelConfig(options=self.base_config_options)
        hardware_info = {"cpu": {}}  # Missing topology and memory
        recommendations = recommend_optimizations(config, hardware_info)
        rec_names = {rec.name for rec in recommendations}
        self.assertNotIn("CONFIG_CPU_FREQ_GOV_PERFORMANCE", rec_names)
        self.assertNotIn("CONFIG_HUGETLBFS", rec_names)
        self.assertIn("CONFIG_MCORE2", rec_names)
        self.assertIn("CONFIG_64BIT", rec_names)

    def test_aarch64_already_optimized(self):
        """Test no page size recommendation for an optimized aarch64 config."""
        config = KernelConfig(
            options=[
                KernelConfigOption(name="CONFIG_ARM64_64K_PAGES", value="y"),
            ]
        )
        hardware_info = self._get_hardware_info(arch="aarch64")
        recommendations = recommend_optimizations(config, hardware_info)
        rec_names = {rec.name for rec in recommendations}
        self.assertNotIn("CONFIG_ARM64_64K_PAGES", rec_names)

    def test_other_architecture(self):
        """
        Test that no arch-specific recommendations are made for other architectures.
        """
        config = KernelConfig(options=self.base_config_options)
        hardware_info = self._get_hardware_info(arch="riscv64")
        recommendations = recommend_optimizations(config, hardware_info)
        rec_names = {rec.name for rec in recommendations}
        self.assertNotIn("CONFIG_MCORE2", rec_names)
        self.assertNotIn("CONFIG_64BIT", rec_names)
        self.assertNotIn("CONFIG_ARM64_64K_PAGES", rec_names)

    @patch("tinel.kernel.optimization.logger")
    def test_logging(self, mock_logger):
        """Test that recommendations are logged."""
        config = KernelConfig(options=self.base_config_options)
        hardware_info = self._get_hardware_info(
            cores=2, memory_gb=HIGH_MEMORY_GB, arch="x86_64"
        )

        recommend_optimizations(config, hardware_info)

        self.assertTrue(mock_logger.info.called)
        # Check that we have 3 calls: performance, hugepages, mcore2, 64bit
        self.assertEqual(mock_logger.info.call_count, 4)

        # Check the content of one of the calls
        mock_logger.info.assert_any_call(
            "Recommended CONFIG_CPU_FREQ_GOV_PERFORMANCE=y for multi-core CPU"
        )


def test_get_recommendations_from_file():
    content = "CONFIG_HUGETLBFS=n"
    path = create_mock_config_file(content)
    config = parse_kernel_config(path)
    hardware_info = {"memory": {"total_memory_bytes": 32 * 1024**3}}
    recommendations = recommend_optimizations(config, hardware_info)
    assert len(recommendations) > 0
    assert "CONFIG_HUGETLBFS" in recommendations[0].name
