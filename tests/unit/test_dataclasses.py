# -*- coding: utf-8 -*-
"""
Unit tests for the dataclasses defined in the tinel.kernel module.
"""

import pytest

from tinel.kernel.dataclasses import KernelConfig, KernelConfigOption

# --- Tests for KernelConfigOption ---


def test_kernel_config_option_valid_instantiation():
    """
    Tests that KernelConfigOption can be successfully instantiated with all valid
    inputs.
    """
    option = KernelConfigOption(
        name="CONFIG_SECURITY_SELINUX", value="y", recommended="n"
    )
    assert option.name == "CONFIG_SECURITY_SELINUX"
    assert option.value == "y"
    assert option.recommended == "n"


def test_kernel_config_option_valid_instantiation_null_recommended():
    """
    Tests that KernelConfigOption handles null (None) for the recommended value.
    """
    option = KernelConfigOption(name="CONFIG_HUGETLBFS", value="m")
    assert option.name == "CONFIG_HUGETLBFS"
    assert option.value == "m"
    assert option.recommended is None


def test_kernel_config_option_raises_error_for_empty_name():
    """
    Tests that instantiating KernelConfigOption with an empty name raises a
    ValueError.
    """
    with pytest.raises(ValueError, match="KernelConfigOption name cannot be empty"):
        KernelConfigOption(name="", value="y")


def test_kernel_config_option_raises_error_for_invalid_value():
    """
    Tests that instantiating KernelConfigOption with an invalid value raises a
    ValueError.
    """
    with pytest.raises(ValueError, match=r"Invalid value for CONFIG_TEST: invalid"):
        KernelConfigOption(name="CONFIG_TEST", value="invalid")


# --- Tests for KernelConfig ---


def test_kernel_config_instantiation_with_empty_list():
    """
    Tests that KernelConfig can be successfully instantiated with an empty list of
    options.
    """
    config = KernelConfig(options=[])
    assert config.options == []


def test_kernel_config_instantiation_with_valid_options():
    """
    Tests that KernelConfig correctly stores a list of valid KernelConfigOption
    instances.
    """
    options = [
        KernelConfigOption(name="CONFIG_SECURITY_SELINUX", value="y"),
        KernelConfigOption(name="CONFIG_CPU_FREQ_GOV_PERFORMANCE", value="n"),
        KernelConfigOption(name="CONFIG_HUGETLBFS", value="m"),
    ]
    config = KernelConfig(options=options)

    assert config.options == options


def test_kernel_config_get_option_not_found():
    """
    Tests that KernelConfig.get_option returns None when the option is not found.
    """
    config = KernelConfig(options=[])
    assert config.get_option("CONFIG_NON_EXISTENT") is None


def test_kernel_config_get_option_found():
    """
    Tests that KernelConfig.get_option returns the correct option when it is found.
    """
    option = KernelConfigOption(name="CONFIG_TEST", value="y")
    config = KernelConfig(options=[option])
    assert config.get_option("CONFIG_TEST") == option


def test_kernel_config_get_option_found_in_middle():
    """
    Tests that KernelConfig.get_option returns the correct option when it is
    in the middle of the list.
    """
    option1 = KernelConfigOption(name="CONFIG_TEST1", value="y")
    option2 = KernelConfigOption(name="CONFIG_TEST2", value="y")
    option3 = KernelConfigOption(name="CONFIG_TEST3", value="y")
    config = KernelConfig(options=[option1, option2, option3])
    assert config.get_option("CONFIG_TEST2") == option2


def test_kernel_config_option_validation():
    with pytest.raises(ValueError):
        KernelConfigOption(name="CONFIG_TEST", value="invalid")
