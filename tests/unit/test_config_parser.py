# -*- coding: utf-8 -*-
"""
Unit tests for the kernel configuration parser.
"""

import gzip
import logging
import pytest
from pathlib import Path

from tinel.kernel.config_parser import parse_kernel_config
from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption


def test_parse_plain_text_config(tmp_path: Path):
    """Test parsing a valid plain text config file."""
    config_content = (
        "# This is a comment\n"
        "CONFIG_FIRST_OPTION=y\n"
        "CONFIG_SECOND_OPTION=m\n"
        "# CONFIG_THIRD_OPTION is not set\n"
        "CONFIG_FOURTH_OPTION=y\n"
        "CONFIG_INVALID_VALUE=invalid\n"
        "CONFIG_EMPTY_VALUE=\n"
        "MALFORMED_LINE\n"
    )
    config_file = tmp_path / "config"
    config_file.write_text(config_content)

    result = parse_kernel_config(str(config_file))

    assert isinstance(result, KernelConfig)
    # The parser should correctly identify 3 valid options and skip the others.
    assert len(result.options) == 3
    expected_options = [
        KernelConfigOption(name='CONFIG_FIRST_OPTION', value='y'),
        KernelConfigOption(name='CONFIG_SECOND_OPTION', value='m'),
        KernelConfigOption(name='CONFIG_FOURTH_OPTION', value='y')
    ]
    for option in expected_options:
        assert option in result.options


def test_parse_gzipped_config(tmp_path: Path):
    """Test parsing a valid gzipped config file."""
    config_content = (
        "CONFIG_SECURITY_SELINUX=y\n"
        "MALFORMED_LINE\n"
        "CONFIG_CPU_FREQ_GOV_PERFORMANCE=n\n"
        "# CONFIG_DEBUG_KERNEL is not set\n"
        "CONFIG_HUGETLBFS=m\n"
    ).encode('utf-8')

    config_file = tmp_path / "config.gz"
    with gzip.open(config_file, 'wb') as f:
        f.write(config_content)

    result = parse_kernel_config(str(config_file))

    assert isinstance(result, KernelConfig)
    assert len(result.options) == 3
    expected_options = [
        KernelConfigOption(name='CONFIG_SECURITY_SELINUX', value='y'),
        KernelConfigOption(name='CONFIG_CPU_FREQ_GOV_PERFORMANCE', value='n'),
        KernelConfigOption(name='CONFIG_HUGETLBFS', value='m')
    ]
    for option in expected_options:
        assert option in result.options


def test_parse_empty_file(tmp_path: Path):
    """Test parsing an empty config file."""
    config_file = tmp_path / "empty_config"
    config_file.touch()

    result = parse_kernel_config(str(config_file))
    assert isinstance(result, KernelConfig)
    assert len(result.options) == 0


def test_file_not_found():
    """Test that FileNotFoundError is raised for a non-existent file."""
    with pytest.raises(FileNotFoundError):
        parse_kernel_config("/non/existent/path/config")


def test_bad_gzip_file(tmp_path: Path):
    """Test that gzip.BadGzipFile is raised for a corrupted gzip file."""
    config_file = tmp_path / "bad.gz"
    config_file.write_text("this is not gzipped")

    with pytest.raises(gzip.BadGzipFile):
        parse_kernel_config(str(config_file))


def test_permission_error(tmp_path: Path, caplog):
    """Test that PermissionError is raised when file access is denied."""
    config_file = tmp_path / "no_access_config"
    config_file.touch()
    config_file.chmod(0o000)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(PermissionError):
            parse_kernel_config(str(config_file))
        assert f"Permission denied accessing {config_file}" in caplog.text

    # Restore permissions to allow cleanup
    config_file.chmod(0o600)


def test_logging_output(tmp_path: Path, caplog):
    """Test that logging output is generated correctly."""
    config_content = "CONFIG_VALID=y\nCONFIG_INVALID=123"
    config_file = tmp_path / "logging_config"
    config_file.write_text(config_content)

    with caplog.at_level(logging.INFO):
        parse_kernel_config(str(config_file))
        assert f"Parsing kernel config from {config_file}" in caplog.text
        assert "Parsed 1 valid options" in caplog.text
        assert "Skipping invalid option" in caplog.text


def test_malformed_lines(tmp_path: Path):
    """Test that malformed lines are skipped correctly."""
    config_content = (
        "\n"  # Empty line
        "   \n"  # Whitespace line
        "MALFORMED_LINE_NO_EQUALS\n"
        "# REGULAR COMMENT\n"
    )
    config_file = tmp_path / "malformed_config"
    config_file.write_text(config_content)

    result = parse_kernel_config(str(config_file))
    assert len(result.options) == 0