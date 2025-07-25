#!/usr/bin/env python3
"""
Unit tests for CLI config module.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import argparse
import os
import sys
from unittest.mock import Mock, patch

import pytest

from tinel.cli.config import CLIConfig
from tests.utils import unit_test


class TestCLIConfig:
    """Test CLI configuration class."""
    
    @unit_test
    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = CLIConfig()
        
        assert config.format_type == 'text'
        assert config.use_color is True
        assert config.verbose == 0
        assert config.quiet is False
        assert config.config_file is None
        
    @unit_test
    def test_custom_initialization(self):
        """Test custom configuration initialization."""
        config = CLIConfig(
            format_type='json',
            use_color=False,
            verbose=2,
            quiet=True,
            config_file='/path/to/config.yaml'
        )
        
        assert config.format_type == 'json'
        assert config.use_color is False
        assert config.verbose == 2
        assert config.quiet is True
        assert config.config_file == '/path/to/config.yaml'


class TestFromArgs:
    """Test creating configuration from command line arguments."""
    
    @unit_test
    def test_from_args_basic(self):
        """Test creating config from basic arguments."""
        args = argparse.Namespace(
            format='text',
            no_color=False,
            verbose=0,
            quiet=False,
            config=None
        )
        
        config = CLIConfig.from_args(args)
        
        assert config.format_type == 'text'
        assert config.use_color is True  # not no_color
        assert config.verbose == 0
        assert config.quiet is False
        assert config.config_file is None
        
    @unit_test
    def test_from_args_with_options(self):
        """Test creating config with various options."""
        args = argparse.Namespace(
            format='json',
            no_color=True,
            verbose=2,
            quiet=False,
            config='/home/user/.tinel.yaml'
        )
        
        config = CLIConfig.from_args(args)
        
        assert config.format_type == 'json'
        assert config.use_color is False  # no_color is True
        assert config.verbose == 2
        assert config.quiet is False
        assert config.config_file == '/home/user/.tinel.yaml'
        
    @unit_test
    def test_from_args_quiet_mode(self):
        """Test creating config in quiet mode."""
        args = argparse.Namespace(
            format='yaml',
            no_color=False,
            verbose=0,
            quiet=True,
            config=None
        )
        
        config = CLIConfig.from_args(args)
        
        assert config.format_type == 'yaml'
        assert config.use_color is True
        assert config.verbose == 0
        assert config.quiet is True
        assert config.config_file is None
        
    @unit_test
    def test_from_args_missing_config_attribute(self):
        """Test creating config when config attribute is missing."""
        args = argparse.Namespace(
            format='text',
            no_color=False,
            verbose=1,
            quiet=False
            # No config attribute
        )
        
        config = CLIConfig.from_args(args)
        
        assert config.format_type == 'text'
        assert config.use_color is True
        assert config.verbose == 1
        assert config.quiet is False
        assert config.config_file is None  # Should default to None when missing


class TestValidation:
    """Test configuration validation."""
    
    @unit_test
    def test_validate_success(self):
        """Test successful validation."""
        config = CLIConfig(
            format_type='json',
            use_color=True,
            verbose=1,
            quiet=False
        )
        
        # Should not raise any exception
        config.validate()
        
    @unit_test
    def test_validate_conflicting_verbose_quiet(self):
        """Test validation with conflicting verbose and quiet options."""
        config = CLIConfig(verbose=1, quiet=True)
        
        with pytest.raises(ValueError, match="Cannot use both verbose and quiet modes together"):
            config.validate()
            
    @unit_test
    def test_validate_negative_verbosity(self):
        """Test validation with negative verbosity."""
        config = CLIConfig(verbose=-1)
        
        with pytest.raises(ValueError, match="Verbosity level cannot be negative"):
            config.validate()
            
    @unit_test
    def test_validate_excessive_verbosity(self):
        """Test validation with excessive verbosity."""
        config = CLIConfig(verbose=4)
        
        with pytest.raises(ValueError, match="Maximum verbosity level is 3"):
            config.validate()
            
    @unit_test
    def test_validate_invalid_format(self):
        """Test validation with invalid format."""
        config = CLIConfig(format_type='invalid')
        
        with pytest.raises(ValueError, match="Invalid format 'invalid'"):
            config.validate()
            
    @unit_test
    def test_validate_valid_formats(self):
        """Test validation with all valid formats."""
        valid_formats = ['text', 'json', 'yaml', 'csv']
        
        for format_type in valid_formats:
            config = CLIConfig(format_type=format_type)
            # Should not raise any exception
            config.validate()


class TestShouldUseColor:
    """Test color usage determination."""
    
    @unit_test
    def test_should_use_color_no_color_env(self):
        """Test color disabled by NO_COLOR environment variable."""
        config = CLIConfig(use_color=True)
        
        with patch.dict(os.environ, {'NO_COLOR': '1'}):
            assert config.should_use_color is False
            
    @unit_test
    def test_should_use_color_force_color_env(self):
        """Test color enabled by FORCE_COLOR environment variable."""
        config = CLIConfig(use_color=False)
        
        with patch.dict(os.environ, {'FORCE_COLOR': '1'}):
            assert config.should_use_color is True
            
    @unit_test
    def test_should_use_color_tty_detection(self):
        """Test color based on TTY detection."""
        config = CLIConfig(use_color=True)
        
        # Clear environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stdout.isatty', return_value=True):
                assert config.should_use_color is True
                
            with patch('sys.stdout.isatty', return_value=False):
                assert config.should_use_color is False
                
    @unit_test
    def test_should_use_color_use_color_disabled(self):
        """Test color when use_color is disabled."""
        config = CLIConfig(use_color=False)
        
        # Even with TTY, should not use color if disabled
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stdout.isatty', return_value=True):
                assert config.should_use_color is False
                
    @unit_test
    def test_should_use_color_no_isatty_method(self):
        """Test color when stdout has no isatty method."""
        config = CLIConfig(use_color=True)
        
        # Mock stdout without isatty method
        mock_stdout = Mock(spec=[])  # Empty spec means no methods
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stdout', mock_stdout):
                assert config.should_use_color is False
                
    @unit_test
    def test_should_use_color_environment_precedence(self):
        """Test environment variable precedence."""
        config = CLIConfig(use_color=True)
        
        # NO_COLOR takes precedence over FORCE_COLOR
        with patch.dict(os.environ, {'NO_COLOR': '1', 'FORCE_COLOR': '1'}):
            assert config.should_use_color is False
            
        # FORCE_COLOR works when NO_COLOR is not set
        with patch.dict(os.environ, {'FORCE_COLOR': '1'}):
            # Remove NO_COLOR if it exists
            with patch.dict(os.environ, {'NO_COLOR': ''}, clear=False):
                os.environ.pop('NO_COLOR', None)
                assert config.should_use_color is True


class TestLogLevel:
    """Test log level determination."""
    
    @unit_test
    def test_log_level_quiet(self):
        """Test log level in quiet mode."""
        config = CLIConfig(quiet=True, verbose=0)
        
        assert config.log_level == 'ERROR'
        
    @unit_test
    def test_log_level_default(self):
        """Test log level with default verbosity."""
        config = CLIConfig(quiet=False, verbose=0)
        
        assert config.log_level == 'WARNING'
        
    @unit_test
    def test_log_level_info(self):
        """Test log level with info verbosity."""
        config = CLIConfig(quiet=False, verbose=1)
        
        assert config.log_level == 'INFO'
        
    @unit_test
    def test_log_level_debug(self):
        """Test log level with debug verbosity."""
        config = CLIConfig(quiet=False, verbose=2)
        
        assert config.log_level == 'DEBUG'
        
    @unit_test
    def test_log_level_max_debug(self):
        """Test log level with maximum verbosity."""
        config = CLIConfig(quiet=False, verbose=3)
        
        assert config.log_level == 'DEBUG'
        
    @unit_test
    def test_log_level_quiet_overrides_verbose(self):
        """Test that quiet mode overrides verbose setting."""
        config = CLIConfig(quiet=True, verbose=3)
        
        # Even with high verbosity, quiet should force ERROR level
        assert config.log_level == 'ERROR'


class TestIntegration:
    """Integration tests for CLIConfig."""
    
    @unit_test
    def test_end_to_end_configuration(self):
        """Test end-to-end configuration creation and validation."""
        # Simulate parsed arguments
        args = argparse.Namespace(
            format='json',
            no_color=False,
            verbose=1,
            quiet=False,
            config='/etc/tinel/config.yaml'
        )
        
        # Create configuration
        config = CLIConfig.from_args(args)
        
        # Validate configuration
        config.validate()  # Should not raise
        
        # Test properties
        assert config.format_type == 'json'
        assert config.verbose == 1
        assert config.log_level == 'INFO'
        assert config.config_file == '/etc/tinel/config.yaml'
        
        # Test color determination (depends on environment and TTY)
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stdout.isatty', return_value=True):
                assert config.should_use_color is True
                
    @unit_test
    def test_configuration_with_validation_errors(self):
        """Test configuration that fails validation."""
        args = argparse.Namespace(
            format='invalid_format',
            no_color=False,
            verbose=5,  # Too high
            quiet=False,
            config=None
        )
        
        config = CLIConfig.from_args(args)
        
        # Should fail validation
        with pytest.raises(ValueError):
            config.validate()


@pytest.mark.parametrize("verbose,expected_log_level", [
    (0, 'WARNING'),
    (1, 'INFO'),
    (2, 'DEBUG'),
    (3, 'DEBUG'),
])
@unit_test
def test_log_level_mapping(verbose, expected_log_level):
    """Test log level mapping for different verbosity levels."""
    config = CLIConfig(quiet=False, verbose=verbose)
    assert config.log_level == expected_log_level


@pytest.mark.parametrize("format_type", ['text', 'json', 'yaml', 'csv'])
@unit_test
def test_valid_format_types(format_type):
    """Test all valid format types."""
    config = CLIConfig(format_type=format_type)
    config.validate()  # Should not raise


@pytest.mark.parametrize("invalid_format", ['xml', 'html', 'binary', ''])
@unit_test
def test_invalid_format_types(invalid_format):
    """Test invalid format types."""
    config = CLIConfig(format_type=invalid_format)
    with pytest.raises(ValueError, match="Invalid format"):
        config.validate()


@pytest.mark.parametrize("env_vars,use_color,expected", [
    ({}, True, True),  # Default case with TTY
    ({}, False, False),  # use_color disabled
    ({'NO_COLOR': '1'}, True, False),  # NO_COLOR overrides
    ({'FORCE_COLOR': '1'}, False, True),  # FORCE_COLOR overrides
    ({'NO_COLOR': '1', 'FORCE_COLOR': '1'}, True, False),  # NO_COLOR takes precedence
])
@unit_test 
def test_color_environment_combinations(env_vars, use_color, expected):
    """Test various environment variable combinations for color."""
    config = CLIConfig(use_color=use_color)
    
    with patch.dict(os.environ, env_vars, clear=True):
        with patch('sys.stdout.isatty', return_value=True):
            assert config.should_use_color == expected


@pytest.mark.parametrize("verbosity,is_valid", [
    (-1, False),  # Negative
    (0, True),    # Valid
    (1, True),    # Valid  
    (2, True),    # Valid
    (3, True),    # Valid (max)
    (4, False),   # Too high
    (10, False),  # Way too high
])
@unit_test
def test_verbosity_validation(verbosity, is_valid):
    """Test verbosity level validation."""
    config = CLIConfig(verbose=verbosity)
    
    if is_valid:
        config.validate()  # Should not raise
    else:
        with pytest.raises(ValueError):
            config.validate()


@pytest.mark.parametrize("quiet,verbose,is_valid", [
    (False, 0, True),   # Normal case
    (False, 1, True),   # Verbose but not quiet
    (True, 0, True),    # Quiet with no verbose
    (True, 1, False),   # Conflicting
    (True, 2, False),   # Conflicting
])
@unit_test
def test_quiet_verbose_combinations(quiet, verbose, is_valid):
    """Test quiet and verbose combination validation."""
    config = CLIConfig(quiet=quiet, verbose=verbose)
    
    if is_valid:
        config.validate()  # Should not raise
    else:
        with pytest.raises(ValueError, match="Cannot use both verbose and quiet"):
            config.validate()