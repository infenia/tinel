# -*- coding: utf-8 -*-
"""
Unit tests for the kernel configuration analyzer.
"""

import logging

import pytest

from tests.utils import create_mock_config_file
from tinel.kernel.config_analyzer import analyze_config
from tinel.kernel.config_parser import parse_kernel_config
from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption

# Constants for magic numbers
PERFECT_CONFIG_ISSUES = 0
MISSING_OPTIONS_ISSUES = 1
MISCONFIGURED_OPTIONS_ISSUES = 2
EMPTY_CONFIG_ISSUES = 6
MIXED_ISSUES = 4


@pytest.fixture
def perfect_config() -> KernelConfig:
    """Provides a KernelConfig object with all options perfectly configured."""
    return KernelConfig(
        options=[
            KernelConfigOption(name="CONFIG_SECURITY_SELINUX", value="y"),
            KernelConfigOption(name="CONFIG_SECURITY_APPARMOR", value="y"),
            KernelConfigOption(name="CONFIG_STRICT_KERNEL_RWX", value="y"),
            KernelConfigOption(name="CONFIG_IKCONFIG", value="y"),
            KernelConfigOption(name="CONFIG_IKCONFIG_PROC", value="y"),
            KernelConfigOption(name="CONFIG_DEBUG_KERNEL", value="n"),
        ]
    )


@pytest.fixture
def missing_options_config() -> KernelConfig:
    """Provides a KernelConfig with a missing security option."""
    return KernelConfig(
        options=[
            # CONFIG_SECURITY_SELINUX is missing
            KernelConfigOption(name="CONFIG_SECURITY_APPARMOR", value="y"),
            KernelConfigOption(name="CONFIG_STRICT_KERNEL_RWX", value="y"),
            KernelConfigOption(name="CONFIG_IKCONFIG", value="y"),
            KernelConfigOption(name="CONFIG_IKCONFIG_PROC", value="y"),
            KernelConfigOption(name="CONFIG_DEBUG_KERNEL", value="n"),
        ]
    )


@pytest.fixture
def misconfigured_options_config() -> KernelConfig:
    """Provides a KernelConfig with a misconfigured security option."""
    return KernelConfig(
        options=[
            KernelConfigOption(
                name="CONFIG_SECURITY_SELINUX", value="n"
            ),  # Should be 'y'
            KernelConfigOption(name="CONFIG_SECURITY_APPARMOR", value="y"),
            KernelConfigOption(name="CONFIG_STRICT_KERNEL_RWX", value="y"),
            KernelConfigOption(name="CONFIG_IKCONFIG", value="y"),
            KernelConfigOption(name="CONFIG_IKCONFIG_PROC", value="y"),
            KernelConfigOption(name="CONFIG_DEBUG_KERNEL", value="y"),  # Should be 'n'
        ]
    )


@pytest.fixture
def empty_config() -> KernelConfig:
    """Provides an empty KernelConfig object."""
    return KernelConfig(options=[])


def test_analyze_config_perfect(
    perfect_config: KernelConfig, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify no issues are reported for a perfect configuration."""
    issues = analyze_config(perfect_config)
    assert not issues
    assert f"Found {PERFECT_CONFIG_ISSUES} issues in kernel config" in caplog.text
    # Ensure no warnings were logged
    for record in caplog.records:
        assert record.levelno != logging.WARNING


def test_analyze_config_missing_option(
    missing_options_config: KernelConfig, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify issues are reported for missing options."""
    issues = analyze_config(missing_options_config)
    assert len(issues) == MISSING_OPTIONS_ISSUES
    assert "Missing CONFIG_SECURITY_SELINUX" in issues[0]
    assert "enables mandatory access control" in issues[0].lower()

    assert "Missing option: CONFIG_SECURITY_SELINUX" in caplog.text
    assert f"Found {MISSING_OPTIONS_ISSUES} issues in kernel config" in caplog.text


def test_analyze_config_misconfigured_option(
    misconfigured_options_config: KernelConfig, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify issues are reported for misconfigured options."""
    issues = analyze_config(misconfigured_options_config)
    assert len(issues) == MISCONFIGURED_OPTIONS_ISSUES

    # Check for the two specific misconfigurations
    expected_issue_1 = (
        "CONFIG_SECURITY_SELINUX=n, recommended: y "
        "(Enables mandatory access control for enhanced security)"
    )
    expected_issue_2 = (
        "CONFIG_DEBUG_KERNEL=y, recommended: n "
        "(Disables debug symbols to reduce kernel size)"
    )
    assert expected_issue_1 in issues
    assert expected_issue_2 in issues

    assert "Misconfigured option: CONFIG_SECURITY_SELINUX=n" in caplog.text
    assert "Misconfigured option: CONFIG_DEBUG_KERNEL=y" in caplog.text
    assert (
        f"Found {MISCONFIGURED_OPTIONS_ISSUES} issues in kernel config" in caplog.text
    )


def test_analyze_config_empty(
    empty_config: KernelConfig, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify all best-practice options are reported as missing for an empty config."""
    issues = analyze_config(empty_config)
    # Should be one issue for each item in BEST_PRACTICES
    assert len(issues) == EMPTY_CONFIG_ISSUES
    assert "Missing CONFIG_SECURITY_SELINUX" in issues[0]
    assert f"Found {EMPTY_CONFIG_ISSUES} issues in kernel config" in caplog.text
    assert caplog.text.count("Missing option:") == EMPTY_CONFIG_ISSUES


def test_analyze_config_mixed_issues(caplog: pytest.LogCaptureFixture) -> None:
    """Verify correct reporting for a mix of missing and misconfigured options."""
    mixed_config = KernelConfig(
        options=[
            KernelConfigOption(
                name="CONFIG_SECURITY_SELINUX", value="n"
            ),  # Misconfigured
            # CONFIG_SECURITY_APPARMOR is missing
            KernelConfigOption(name="CONFIG_STRICT_KERNEL_RWX", value="y"),
            KernelConfigOption(name="CONFIG_IKCONFIG", value="n"),  # Misconfigured
            # CONFIG_IKCONFIG_PROC is missing
            KernelConfigOption(name="CONFIG_DEBUG_KERNEL", value="n"),
        ]
    )

    issues = analyze_config(mixed_config)
    assert len(issues) == MIXED_ISSUES

    # Check logs
    assert "Misconfigured option: CONFIG_SECURITY_SELINUX=n" in caplog.text
    assert "Missing option: CONFIG_SECURITY_APPARMOR" in caplog.text
    assert "Misconfigured option: CONFIG_IKCONFIG=n" in caplog.text
    assert "Missing option: CONFIG_IKCONFIG_PROC" in caplog.text
    assert f"Found {MIXED_ISSUES} issues in kernel config" in caplog.text


def test_analyze_config_from_file():
    content = "CONFIG_SECURITY_SELINUX=n"
    path = create_mock_config_file(content)
    config = parse_kernel_config(path)
    issues = analyze_config(config)
    assert len(issues) > 0
    assert "CONFIG_SECURITY_SELINUX" in issues[0]
