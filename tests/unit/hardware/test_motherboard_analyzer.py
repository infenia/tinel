#!/usr/bin/env python3
"""
Unit tests for motherboard analyzer implementation.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from unittest.mock import Mock

from tests.utils import unit_test
from tinel.hardware.motherboard_analyzer import MotherboardAnalyzer
from tinel.interfaces import CommandResult


class TestMotherboardAnalyzer:
    """Test cases for MotherboardAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.analyzer = MotherboardAnalyzer(self.mock_system)

    @unit_test
    def test_get_motherboard_info_success(self):
        """Test successful retrieval of motherboard information."""
        # Arrange
        dmi_output = """
Base Board Information
	Manufacturer: ASUSTeK COMPUTER INC.
	Product Name: ROG STRIX Z390-E GAMING
	Version: Rev 1.xx
	Serial Number: 123456789
"""
        self.mock_system.run_command.return_value = CommandResult(
            success=True, stdout=dmi_output, stderr="", returncode=0
        )

        # Act
        info = self.analyzer.get_motherboard_info()

        # Assert
        assert info["manufacturer"] == "ASUSTeK COMPUTER INC."
        assert info["product_name"] == "ROG STRIX Z390-E GAMING"
        assert info["version"] == "Rev 1.xx"
        assert info["serial_number"] == "123456789"

    @unit_test
    def test_get_motherboard_info_failure(self):
        """Test failure to retrieve motherboard information."""
        # Arrange
        self.mock_system.run_command.return_value = CommandResult(
            success=False, stdout="", stderr="command not found", returncode=127
        )

        # Act
        info = self.analyzer.get_motherboard_info()

        # Assert
        assert "error" in info
        assert "command not found" in info["error"]

    @unit_test
    def test_parse_dmi_output(self):
        """Test parsing of dmidecode output."""
        # Arrange
        dmi_output = """
	Manufacturer: Test-Manu
	Product Name: Test-Prod
	Version: 1.0
"""

        # Act & Assert
        assert (
            self.analyzer._parse_dmi_output(dmi_output, "Manufacturer") == "Test-Manu"
        )
        assert (
            self.analyzer._parse_dmi_output(dmi_output, "Product Name") == "Test-Prod"
        )
        assert self.analyzer._parse_dmi_output(dmi_output, "Version") == "1.0"
        assert self.analyzer._parse_dmi_output(dmi_output, "Serial Number") is None

    @unit_test
    def test_parse_dmi_output_malformed_line(self):
        """Test parsing when a line contains the field but has no colon."""
        # Arrange - line contains "Manufacturer" but no colon separator
        dmi_output = """
	Manufacturer Without Colon
	Manufacturer: Test-Manu
"""

        # Act
        result = self.analyzer._parse_dmi_output(dmi_output, "Manufacturer")

        # Assert - should skip the malformed line and find the correct one
        assert result == "Test-Manu"
