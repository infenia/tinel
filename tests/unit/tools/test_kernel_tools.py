#!/usr/bin/env python3
"""
Unit tests for the kernel tools module.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""
import unittest
from unittest.mock import MagicMock, patch

from tinel.tools.kernel_tools import run_kernel_config_check


class TestKernelTools(unittest.TestCase):
    @patch("tinel.tools.kernel_tools.recommend_optimizations")
    @patch("tinel.tools.kernel_tools.analyze_config")
    @patch("tinel.tools.kernel_tools.parse_kernel_config")
    def test_run_kernel_config_check_success(
        self,
        mock_parse_kernel_config: MagicMock,
        mock_analyze_config: MagicMock,
        mock_recommend_optimizations: MagicMock,
    ):
        """Test the run_kernel_config_check function for a successful run."""
        # Arrange
        mock_config = {"CONFIG_FOO": "y"}
        mock_issues = [{"id": "issue1", "description": "An issue"}]
        mock_recommendations = [{"id": "rec1", "description": "A recommendation"}]

        mock_parse_kernel_config.return_value = mock_config
        mock_analyze_config.return_value = mock_issues
        mock_recommend_optimizations.return_value = mock_recommendations

        # Act
        result = run_kernel_config_check("dummy_path")

        # Assert
        self.assertEqual(result["config"], mock_config)
        self.assertEqual(result["issues"], mock_issues)
        self.assertEqual(result["recommendations"], mock_recommendations)
        self.assertIsNone(result["error"])

        mock_parse_kernel_config.assert_called_once_with("dummy_path")
        mock_analyze_config.assert_called_once_with(mock_config)
        mock_recommend_optimizations.assert_called_once_with(mock_config, None)

    @patch("tinel.tools.kernel_tools.parse_kernel_config")
    def test_run_kernel_config_check_failure(
        self, mock_parse_kernel_config: MagicMock
    ):
        """Test the run_kernel_config_check function for a failure case."""
        # Arrange
        error_message = "File not found"
        mock_parse_kernel_config.side_effect = Exception(error_message)

        # Act
        result = run_kernel_config_check("dummy_path")

        # Assert
        self.assertIsNone(result["config"])
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["recommendations"], [])
        self.assertEqual(
            result["error"], f"Failed to process kernel config: {error_message}"
        )

        mock_parse_kernel_config.assert_called_once_with("dummy_path")