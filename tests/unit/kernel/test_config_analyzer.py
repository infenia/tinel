# -*- coding: utf-8 -*-
"""
Unit tests for the kernel configuration analyzer.
"""

import logging
from typing import List

import pytest

from tinel.kernel.config_analyzer import analyze_config
from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption


@pytest.fixture
def perfect_config() -> KernelConfig:
    """Provides a KernelConfig object with all options perfectly configured."""
    return KernelConfig(options=[
        KernelConfigOption(name='CONFIG_SECURITY_SELINUX', value='y'),
        KernelConfigOption(name='CONFIG_SECURITY_APPARMOR', value='y'),
        KernelConfigOption(name='CONFIG_STRICT_KERNEL_RWX', value='y'),
        KernelConfigOption(name='CONFIG_IKCONFIG', value='y'),
        KernelConfigOption(name='CONFIG_IKCONFIG_PROC', value='y'),
        KernelConfigOption(name='CONFIG_DEBUG_KERNEL', value='n'),
    ])


@pytest.fixture
def missing_options_config() -> KernelConfig:
    """Provides a KernelConfig with a missing security option."""
    return KernelConfig(options=[
        # CONFIG_SECURITY_SELINUX is missing
        KernelConfigOption(name='CONFIG_SECURITY_APPARMOR', value='y'),
        KernelConfigOption(name='CONFIG_STRICT_KERNEL_RWX', value='y'),
        KernelConfigOption(name='CONFIG_IKCONFIG', value='y'),
        KernelConfigOption(name='CONFIG_IKCONFIG_PROC', value='y'),
        KernelConfigOption(name='CONFIG_DEBUG_KERNEL', value='n'),
    ])


@pytest.fixture
def misconfigured_options_config() -> KernelConfig:
    """Provides a KernelConfig with a misconfigured security option."""
    return KernelConfig(options=[
        KernelConfigOption(name='CONFIG_SECURITY_SELINUX', value='n'), # Should be 'y'
        KernelConfigOption(name='CONFIG_SECURITY_APPARMOR', value='y'),
        KernelConfigOption(name='CONFIG_STRICT_KERNEL_RWX', value='y'),
        KernelConfigOption(name='CONFIG_IKCONFIG', value='y'),
        KernelConfigOption(name='CONFIG_IKCONFIG_PROC', value='y'),
        KernelConfigOption(name='CONFIG_DEBUG_KERNEL', value='y'), # Should be 'n'
    ])


@pytest.fixture
def empty_config() -> KernelConfig:
    """Provides an empty KernelConfig object."""
    return KernelConfig(options=[])


def test_analyze_config_perfect(perfect_config: KernelConfig, caplog: pytest.LogCaptureFixture) -> None:
    """Verify no issues are reported for a perfect configuration."""
    issues = analyze_config(perfect_config)
    assert not issues
    assert "Found 0 issues in kernel config" in caplog.text
    # Ensure no warnings were logged
    for record in caplog.records:
        assert record.levelno != logging.WARNING


def test_analyze_config_missing_option(
    missing_options_config: KernelConfig, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify issues are reported for missing options."""
    issues = analyze_config(missing_options_config)
    assert len(issues) == 1
    assert "Missing CONFIG_SECURITY_SELINUX" in issues[0]
    assert "enables mandatory access control" in issues[0].lower()

    assert "Missing option: CONFIG_SECURITY_SELINUX" in caplog.text
    assert "Found 1 issues in kernel config" in caplog.text


def test_analyze_config_misconfigured_option(
    misconfigured_options_config: KernelConfig, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify issues are reported for misconfigured options."""
    issues = analyze_config(misconfigured_options_config)
    assert len(issues) == 2

    # Check for the two specific misconfigurations
    expected_issue_1 = "CONFIG_SECURITY_SELINUX=n, recommended: y (Enables mandatory access control for enhanced security)"
    expected_issue_2 = "CONFIG_DEBUG_KERNEL=y, recommended: n (Disables debug symbols to reduce kernel size)"
    assert expected_issue_1 in issues
    assert expected_issue_2 in issues

    assert "Misconfigured option: CONFIG_SECURITY_SELINUX=n" in caplog.text
    assert "Misconfigured option: CONFIG_DEBUG_KERNEL=y" in caplog.text
    assert "Found 2 issues in kernel config" in caplog.text


def test_analyze_config_empty(empty_config: KernelConfig, caplog: pytest.LogCaptureFixture) -> None:
    """Verify all best-practice options are reported as missing for an empty config."""
    issues = analyze_config(empty_config)
    # Should be one issue for each item in BEST_PRACTICES
    assert len(issues) == 6
    assert "Missing CONFIG_SECURITY_SELINUX" in issues[0]
    assert "Found 6 issues in kernel config" in caplog.text
    assert caplog.text.count("Missing option:") == 6

def test_analyze_config_mixed_issues(caplog: pytest.LogCaptureFixture) -> None:
    """Verify correct reporting for a mix of missing and misconfigured options."""
    mixed_config = KernelConfig(options=[
        KernelConfigOption(name='CONFIG_SECURITY_SELINUX', value='n'), # Misconfigured
        # CONFIG_SECURITY_APPARMOR is missing
        KernelConfigOption(name='CONFIG_STRICT_KERNEL_RWX', value='y'),
        KernelConfigOption(name='CONFIG_IKCONFIG', value='n'), # Misconfigured
        # CONFIG_IKCONFIG_PROC is missing
        KernelConfigOption(name='CONFIG_DEBUG_KERNEL', value='n'),
    ])

    issues = analyze_config(mixed_config)
    assert len(issues) == 4

    # Check logs
    assert "Misconfigured option: CONFIG_SECURITY_SELINUX=n" in caplog.text
    assert "Missing option: CONFIG_SECURITY_APPARMOR" in caplog.text
    assert "Misconfigured option: CONFIG_IKCONFIG=n" in caplog.text
    assert "Missing option: CONFIG_IKCONFIG_PROC" in caplog.text
    assert "Found 4 issues in kernel config" in caplog.text