#!/usr/bin/env python3
"""
Unit tests for CLI main module.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import logging
import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock

import pytest

from tinel.cli.main import (
    setup_logging,
    _validate_and_sanitize_argv,
    display_banner,
    main,
    _execute_main_logic,
    _handle_keyboard_interrupt,
    _handle_unexpected_error,
    _get_command_router
)
from tests.utils import unit_test


class TestSetupLogging:
    """Test logging setup functionality."""
    
    @unit_test
    def test_setup_logging_quiet_mode(self):
        """Test logging setup in quiet mode."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=0, quiet=True)
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args.kwargs
            assert call_kwargs['level'] == logging.ERROR
            
    @unit_test
    def test_setup_logging_default_verbosity(self):
        """Test logging setup with default verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=0, quiet=False)
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args.kwargs
            assert call_kwargs['level'] == logging.WARNING
            
    @unit_test
    def test_setup_logging_info_level(self):
        """Test logging setup with info verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=1, quiet=False)
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args.kwargs
            assert call_kwargs['level'] == logging.INFO
            
    @unit_test
    def test_setup_logging_debug_level(self):
        """Test logging setup with debug verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=2, quiet=False)
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args.kwargs
            assert call_kwargs['level'] == logging.DEBUG
            
    @unit_test
    def test_setup_logging_max_verbosity(self):
        """Test logging setup with maximum verbosity."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=3, quiet=False)
            
            mock_config.assert_called_once()
            call_kwargs = mock_config.call_args.kwargs
            assert call_kwargs['level'] == logging.DEBUG
            
    @unit_test
    def test_setup_logging_format_debug(self):
        """Test logging format for debug level."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=2, quiet=False)
            
            call_kwargs = mock_config.call_args.kwargs
            assert 'filename' in call_kwargs['format']
            assert 'lineno' in call_kwargs['format']
            
    @unit_test
    def test_setup_logging_format_info(self):
        """Test logging format for info level."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=1, quiet=False)
            
            call_kwargs = mock_config.call_args.kwargs
            assert 'asctime' in call_kwargs['format']
            assert 'filename' not in call_kwargs['format']
            
    @unit_test
    def test_setup_logging_format_basic(self):
        """Test logging format for basic level."""
        with patch('logging.basicConfig') as mock_config:
            setup_logging(verbosity=0, quiet=False)
            
            call_kwargs = mock_config.call_args.kwargs
            assert 'asctime' not in call_kwargs['format']
            assert 'levelname' in call_kwargs['format']
            
    @unit_test
    def test_setup_logging_suppress_noisy_loggers(self):
        """Test that noisy loggers are suppressed in non-debug mode."""
        with patch('logging.basicConfig'):
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                setup_logging(verbosity=1, quiet=False)
                
                # Should suppress urllib3 and requests loggers
                calls = mock_get_logger.call_args_list
                logger_names = [call[0][0] for call in calls if call[0]]
                assert 'urllib3' in logger_names
                assert 'requests' in logger_names


class TestValidateAndSanitizeArgv:
    """Test argument validation and sanitization."""
    
    @unit_test
    def test_validate_none_argv(self):
        """Test validation with None argv."""
        result = _validate_and_sanitize_argv(None)
        assert result is None
        
    @unit_test
    def test_validate_empty_argv(self):
        """Test validation with empty argv."""
        result = _validate_and_sanitize_argv([])
        assert result == []
        
    @unit_test
    def test_validate_normal_argv(self):
        """Test validation with normal arguments."""
        argv = ['hardware', 'cpu', '--verbose']
        result = _validate_and_sanitize_argv(argv)
        assert result == argv
        
    @unit_test
    def test_validate_strips_whitespace(self):
        """Test that arguments are stripped of whitespace."""
        argv = [' hardware ', '  cpu  ', '--verbose ']
        result = _validate_and_sanitize_argv(argv)
        assert result == ['hardware', 'cpu', '--verbose']
        
    @unit_test
    def test_validate_removes_empty_strings(self):
        """Test that empty strings are removed."""
        argv = ['hardware', '', 'cpu', '   ', '--verbose']
        result = _validate_and_sanitize_argv(argv)
        assert result == ['hardware', 'cpu', '--verbose']
        
    @unit_test
    def test_validate_too_many_arguments(self):
        """Test validation fails with too many arguments."""
        argv = ['arg'] * 101  # Over 100 arguments
        
        with pytest.raises(ValueError, match="Too many arguments"):
            _validate_and_sanitize_argv(argv)
            
    @unit_test
    def test_validate_invalid_argument_type(self):
        """Test validation fails with non-string arguments."""
        argv = ['hardware', 123, 'cpu']
        
        with pytest.raises(ValueError, match="Invalid argument type"):
            _validate_and_sanitize_argv(argv)
            
    @unit_test
    def test_validate_argument_too_long(self):
        """Test validation fails with too long arguments."""
        long_arg = 'A' * 1001  # Over 1000 characters
        argv = ['hardware', long_arg]
        
        with pytest.raises(ValueError, match="Argument too long"):
            _validate_and_sanitize_argv(argv)


class TestDisplayBanner:
    """Test banner display functionality."""
    
    @unit_test
    def test_display_banner(self):
        """Test that banner is displayed correctly."""
        with patch('builtins.print') as mock_print:
            display_banner()
            
            mock_print.assert_called_once()
            banner_text = mock_print.call_args[0][0]
            # The banner contains ASCII art for TINEL, not the word TINEL
            assert 'Terminal Intelligence for Linux Systems' in banner_text
            assert '█' in banner_text  # Check for ASCII art characters


class TestGetCommandRouter:
    """Test command router lazy loading."""
    
    @unit_test
    def test_get_command_router(self):
        """Test command router creation."""
        formatter = Mock()
        error_handler = Mock()
        
        # CommandRouter is imported inside the function, so patch the import path
        with patch('tinel.cli.commands.CommandRouter') as mock_router_class:
            mock_router = Mock()
            mock_router_class.return_value = mock_router
            
            result = _get_command_router(formatter, error_handler)
            
            mock_router_class.assert_called_once_with(formatter, error_handler)
            assert result == mock_router


class TestMain:
    """Test the main entry point function."""
    
    @unit_test
    def test_main_displays_banner_by_default(self):
        """Test that main displays banner by default."""
        with patch('tinel.cli.main.display_banner') as mock_banner:
            with patch('tinel.cli.main._execute_main_logic', return_value=0):
                result = main(['hardware', 'cpu'])
                
                mock_banner.assert_called_once()
                assert result == 0
                
    @unit_test
    def test_main_suppresses_banner_quiet_short(self):
        """Test that main suppresses banner with -q flag."""
        with patch('tinel.cli.main.display_banner') as mock_banner:
            with patch('tinel.cli.main._execute_main_logic', return_value=0):
                result = main(['-q', 'hardware', 'cpu'])
                
                mock_banner.assert_not_called()
                assert result == 0
                
    @unit_test
    def test_main_suppresses_banner_quiet_long(self):
        """Test that main suppresses banner with --quiet flag."""
        with patch('tinel.cli.main.display_banner') as mock_banner:
            with patch('tinel.cli.main._execute_main_logic', return_value=0):
                result = main(['--quiet', 'hardware', 'cpu'])
                
                mock_banner.assert_not_called()
                assert result == 0
                
    @unit_test
    def test_main_validation_error(self):
        """Test main handles validation errors."""
        with patch('tinel.cli.main._validate_and_sanitize_argv', side_effect=ValueError("Invalid args")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                result = main(['invalid'])
                
                assert result == 1
                assert "Fatal error: Invalid args" in mock_stderr.getvalue()
                
    @unit_test
    def test_main_keyboard_interrupt(self):
        """Test main handles keyboard interrupt."""
        with patch('tinel.cli.main._execute_main_logic', side_effect=KeyboardInterrupt()):
            with patch('tinel.cli.main._handle_keyboard_interrupt', return_value=130) as mock_handler:
                result = main(['hardware', 'cpu'])
                
                mock_handler.assert_called_once()
                assert result == 130
                
    @unit_test
    def test_main_system_exit_with_code(self):
        """Test main handles SystemExit with code."""
        with patch('tinel.cli.main._execute_main_logic', side_effect=SystemExit(2)):
            result = main(['hardware', 'cpu'])
            
            assert result == 2
            
    @unit_test
    def test_main_system_exit_without_code(self):
        """Test main handles SystemExit without code."""
        with patch('tinel.cli.main._execute_main_logic', side_effect=SystemExit()):
            result = main(['hardware', 'cpu'])
            
            assert result == 0
            
    @unit_test
    def test_main_unexpected_error(self):
        """Test main handles unexpected errors."""
        with patch('tinel.cli.main._execute_main_logic', side_effect=RuntimeError("Unexpected")):
            with patch('tinel.cli.main._handle_unexpected_error', return_value=1) as mock_handler:
                result = main(['hardware', 'cpu'])
                
                mock_handler.assert_called_once()
                assert result == 1


class TestExecuteMainLogic:
    """Test the main execution logic."""
    
    @unit_test
    def test_execute_main_logic_success(self):
        """Test successful execution of main logic."""
        mock_args = Mock(command='hardware')
        mock_config = Mock(
            verbose=0,
            quiet=False,
            format_type='text',
            should_use_color=False
        )
        mock_formatter = Mock()
        mock_error_handler = Mock()
        mock_router = Mock()
        mock_router.execute_command.return_value = 0
        
        with patch('tinel.cli.main.parse_arguments', return_value=mock_args):
            with patch('tinel.cli.main.CLIConfig.from_args', return_value=mock_config):
                with patch('tinel.cli.main.setup_logging'):
                    with patch('tinel.cli.main.OutputFormatter', return_value=mock_formatter):
                        with patch('tinel.cli.main.CLIErrorHandler', return_value=mock_error_handler):
                            with patch('tinel.cli.main._get_command_router', return_value=mock_router):
                                result = _execute_main_logic(['hardware', 'cpu'])
                                
                                assert result == 0
                                mock_router.execute_command.assert_called_once_with(mock_args)
                                
    @unit_test
    def test_execute_main_logic_with_timing(self):
        """Test that execution timing is logged properly."""
        mock_args = Mock(command='hardware')
        mock_config = Mock(
            verbose=1,
            quiet=False,
            format_type='text',
            should_use_color=False
        )
        
        with patch('tinel.cli.main.parse_arguments', return_value=mock_args):
            with patch('tinel.cli.main.CLIConfig.from_args', return_value=mock_config):
                with patch('tinel.cli.main.setup_logging'):
                    with patch('tinel.cli.main.OutputFormatter'):
                        with patch('tinel.cli.main.CLIErrorHandler'):
                            with patch('tinel.cli.main._get_command_router') as mock_get_router:
                                mock_router = Mock()
                                mock_router.execute_command.return_value = 0
                                mock_get_router.return_value = mock_router
                                
                                with patch('logging.getLogger') as mock_get_logger:
                                    mock_logger = Mock()
                                    mock_get_logger.return_value = mock_logger
                                    
                                    result = _execute_main_logic(['hardware', 'cpu'])
                                    
                                    assert result == 0
                                    # Check that info logging was called for start and completion
                                    assert mock_logger.info.call_count >= 2
                                    
    @unit_test
    def test_execute_main_logic_exception_handling(self):
        """Test exception handling in main logic."""
        with patch('tinel.cli.main.parse_arguments', side_effect=RuntimeError("Parse error")):
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                with pytest.raises(RuntimeError, match="Parse error"):
                    _execute_main_logic(['invalid'])
                    
                # Should log the error
                mock_logger.error.assert_called_once()


class TestErrorHandlers:
    """Test error handling functions."""
    
    @unit_test
    def test_handle_keyboard_interrupt(self):
        """Test keyboard interrupt handler."""
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = _handle_keyboard_interrupt()
            
            assert result == 130
            assert "Operation cancelled by user" in mock_stderr.getvalue()
            
    @unit_test
    def test_handle_unexpected_error(self):
        """Test unexpected error handler."""
        error = RuntimeError("Something went wrong")
        
        with patch('logging.exception') as mock_log_exception:
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                result = _handle_unexpected_error(error)
                
                assert result == 1
                mock_log_exception.assert_called_once()
                stderr_output = mock_stderr.getvalue()
                assert "Fatal error: Something went wrong" in stderr_output
                assert "internal error" in stderr_output


class TestMainIntegration:
    """Integration tests for main function."""
    
    @unit_test
    def test_main_none_argv(self):
        """Test main with None argv (uses sys.argv)."""
        with patch('tinel.cli.main.display_banner'):
            with patch('tinel.cli.main._execute_main_logic', return_value=0):
                result = main(None)
                
                assert result == 0
                
    @unit_test
    def test_main_end_to_end_success(self):
        """Test successful end-to-end execution."""
        mock_args = Mock(command='hardware', hardware_command='cpu')
        mock_config = Mock(
            verbose=0,
            quiet=False,
            format_type='text',
            should_use_color=False
        )
        
        with patch('tinel.cli.main.display_banner'):
            with patch('tinel.cli.main.parse_arguments', return_value=mock_args):
                with patch('tinel.cli.main.CLIConfig.from_args', return_value=mock_config):
                    with patch('tinel.cli.main.setup_logging'):
                        with patch('tinel.cli.main.OutputFormatter'):
                            with patch('tinel.cli.main.CLIErrorHandler'):
                                with patch('tinel.cli.main._get_command_router') as mock_get_router:
                                    mock_router = Mock()
                                    mock_router.execute_command.return_value = 0
                                    mock_get_router.return_value = mock_router
                                    
                                    result = main(['hardware', 'cpu'])
                                    
                                    assert result == 0


@pytest.mark.parametrize("verbosity,expected_level", [
    (0, logging.WARNING),
    (1, logging.INFO),
    (2, logging.DEBUG),
    (3, logging.DEBUG),
    (10, logging.DEBUG),  # High verbosity should still use DEBUG
])
@unit_test
def test_setup_logging_verbosity_levels(verbosity, expected_level):
    """Test different verbosity levels map to correct logging levels."""
    with patch('logging.basicConfig') as mock_config:
        setup_logging(verbosity, quiet=False)
        
        call_kwargs = mock_config.call_args.kwargs
        assert call_kwargs['level'] == expected_level


@pytest.mark.parametrize("argv,should_show_banner", [
    (['hardware', 'cpu'], True),
    (['-q', 'hardware', 'cpu'], False),
    (['--quiet', 'hardware', 'cpu'], False),
    (['-v', 'hardware', 'cpu'], True),
    (['hardware', '--quiet', 'cpu'], False),  # quiet anywhere should suppress
])
@unit_test
def test_main_banner_display_conditions(argv, should_show_banner):
    """Test banner display under different conditions."""
    with patch('tinel.cli.main.display_banner') as mock_banner:
        with patch('tinel.cli.main._execute_main_logic', return_value=0):
            main(argv)
            
            if should_show_banner:
                mock_banner.assert_called_once()
            else:
                mock_banner.assert_not_called()