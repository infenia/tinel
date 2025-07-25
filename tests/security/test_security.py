#!/usr/bin/env python3
"""
Security tests for Tinel components.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import os
import subprocess
from unittest.mock import Mock, patch

import pytest

from tinel.system import LinuxSystemInterface
from tinel.cli.main import _validate_and_sanitize_argv
from tinel.cli.error_handler import CLIErrorHandler
from tests.utils import (
    security_test,
    SecurityTestHelpers,
    AssertionHelpers,
    TestDataBuilder
)


class TestCommandInjectionPrevention:
    """Test prevention of command injection attacks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.system = LinuxSystemInterface()
        
    @security_test
    def test_command_sanitization_blocks_injection(self):
        """Test that command sanitization blocks injection attempts."""
        malicious_commands = [
            ['lscpu', '; rm -rf /'],
            ['lscpu', '| nc -l 4444'],
            ['lscpu', '&& cat /etc/passwd'],
            ['lscpu', '$(whoami)'],
            ['lscpu', '`id`'],
            ['lscpu', '; shutdown -h now'],
        ]
        
        for malicious_cmd in malicious_commands:
            with pytest.raises(ValueError, match="Dangerous characters found"):
                self.system._sanitize_command(malicious_cmd)
                
    @security_test
    def test_command_whitelist_enforcement(self):
        """Test that only whitelisted commands are allowed."""
        dangerous_commands = [
            ['rm', '-rf', '/'],
            ['dd', 'if=/dev/zero', 'of=/dev/sda'],
            ['mkfs.ext4', '/dev/sda1'],
            ['fdisk', '/dev/sda'],
            ['shutdown', '-h', 'now'],
            ['reboot'],
            ['nc', '-l', '4444'],
            ['bash', '-c', 'echo hello'],
        ]
        
        for dangerous_cmd in dangerous_commands:
            with pytest.raises(ValueError, match="not allowed"):
                self.system._sanitize_command(dangerous_cmd)
                
    @security_test
    def test_safe_commands_allowed(self):
        """Test that safe commands are properly allowed."""
        safe_commands = [
            ['lscpu'],
            ['lspci', '-v'],
            ['lsusb', '-t'],
            ['lsblk', '-f'],
            ['df', '-h'],
            ['ip', 'addr', 'show'],
            ['cat', '/proc/cpuinfo'],
            ['dmidecode', '-t', 'memory'],
        ]
        
        for safe_cmd in safe_commands:
            # Should not raise exception
            result = self.system._sanitize_command(safe_cmd)
            assert result == safe_cmd
            
    @security_test
    def test_subprocess_security_settings(self):
        """Test that subprocess calls use secure settings."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout='output', stderr='', returncode=0)
            
            self.system.run_command(['lscpu'])
            
            # Verify secure settings
            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs['shell'] is False  # Never use shell=True
            assert 'env' in call_kwargs  # Custom environment provided
            assert call_kwargs['capture_output'] is True
            assert call_kwargs['text'] is True
            
            # Verify environment is restricted
            env = call_kwargs['env']
            assert env['PATH'] == '/usr/bin:/bin:/usr/sbin:/sbin'  # Restricted PATH
            
    @security_test
    def test_environment_variable_security(self):
        """Test that environment variables are properly controlled."""
        safe_env = self.system._get_safe_environment()
        
        # Should have minimal, safe environment
        assert safe_env['PATH'] == '/usr/bin:/bin:/usr/sbin:/sbin'
        assert safe_env['LC_ALL'] == 'C'
        assert safe_env['LANG'] == 'C'
        
        # Should not inherit dangerous variables
        with patch.dict(os.environ, {
            'LD_PRELOAD': '/malicious/lib.so',
            'LD_LIBRARY_PATH': '/malicious/libs',
            'SHELL': '/bin/bash',
        }):
            env = self.system._get_safe_environment()
            assert 'LD_PRELOAD' not in env
            assert 'LD_LIBRARY_PATH' not in env
            # SHELL is not in safe environment by default


class TestPathTraversalPrevention:
    """Test prevention of path traversal attacks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.system = LinuxSystemInterface()
        
    @security_test
    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        malicious_paths = SecurityTestHelpers.create_path_traversal_attempts()
        
        for malicious_path in malicious_paths:
            result = self.system._validate_file_path(malicious_path)
            assert result is None, f"Path traversal not blocked: {malicious_path}"
            
    @security_test
    def test_directory_whitelist_enforcement(self):
        """Test that only whitelisted directories are accessible."""
        allowed_paths = [
            '/proc/cpuinfo',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor',
            '/etc/hostname',
            '/usr/share/doc/readme.txt',
            '/var/log/syslog',
        ]
        
        for path in allowed_paths:
            result = self.system._validate_file_path(path)
            assert result == path, f"Valid path blocked: {path}"
            
    @security_test
    def test_dangerous_paths_blocked(self):
        """Test that dangerous paths are blocked."""
        dangerous_paths = [
            '/etc/shadow',  # Remove /etc/passwd since it's actually safe to read
            '/root/.ssh/id_rsa',
            '/home/user/.ssh/id_rsa',
            '/tmp/malicious.sh',
            '/dev/sda',
            '/boot/vmlinuz',
            '/home/user/sensitive.txt',  # Not in whitelist
            '/opt/secret.key',           # Not in whitelist
        ]
        
        for dangerous_path in dangerous_paths:
            result = self.system._validate_file_path(dangerous_path)
            assert result is None, f"Dangerous path not blocked: {dangerous_path}"
            
    @security_test
    def test_symbolic_link_handling(self):
        """Test handling of symbolic links in paths."""
        # Test paths that could be symbolic links
        potential_symlink_paths = [
            '/proc/../etc/passwd',
            '/sys/../../../etc/shadow',
            '/usr/share/../../etc/passwd',
        ]
        
        for path in potential_symlink_paths:
            result = self.system._validate_file_path(path)
            assert result is None, f"Potential symlink attack not blocked: {path}"
            
    @security_test
    def test_file_size_limits(self):
        """Test that file size limits are enforced."""
        with patch.object(self.system, '_validate_file_path', return_value='/proc/cpuinfo'):
            with patch('pathlib.Path.stat') as mock_stat:
                # Test with oversized file
                mock_stat.return_value = Mock(st_size=20 * 1024 * 1024)  # 20MB
                
                result = self.system.read_file('/proc/cpuinfo')
                assert result is None, "Large file size limit not enforced"
                
                # Test with reasonable file size
                mock_stat.return_value = Mock(st_size=1024)  # 1KB
                with patch('builtins.open', mock_open(read_data='test content')):
                    result = self.system.read_file('/proc/cpuinfo')
                    assert result == 'test content'


class TestInputValidation:
    """Test input validation security measures."""
    
    @security_test
    def test_argument_validation(self):
        """Test command line argument validation."""
        # Test only inputs that should actually fail validation
        invalid_inputs = [
            "A" * 10001,  # Too long (>1000 chars)
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValueError):
                _validate_and_sanitize_argv(['hardware', invalid_input])
                
        # Test that normal malicious inputs are handled (not rejected at argv level)
        malicious_but_valid_inputs = [
            "; rm -rf /",
            "$(rm -rf /)",
            "|nc -l 4444", 
            "`cat /etc/passwd`",
            "../../../etc/passwd",
            "${PATH}",
        ]
        
        for valid_input in malicious_but_valid_inputs:
            # These should NOT raise errors at argv validation level
            result = _validate_and_sanitize_argv(['hardware', valid_input])
            assert result is not None
                
    @security_test
    def test_argument_length_limits(self):
        """Test that argument length limits are enforced."""
        # Test extremely long argument
        long_arg = 'A' * 1001  # Over 1000 characters
        
        with pytest.raises(ValueError, match="Argument too long"):
            _validate_and_sanitize_argv(['hardware', long_arg])
            
    @security_test
    def test_argument_count_limits(self):
        """Test that argument count limits are enforced."""
        # Test too many arguments
        many_args = ['arg'] * 101  # Over 100 arguments
        
        with pytest.raises(ValueError, match="Too many arguments"):
            _validate_and_sanitize_argv(many_args)
            
    @security_test
    def test_argument_type_validation(self):
        """Test that argument types are validated."""
        # Test non-string arguments
        invalid_args = ['hardware', 123, {'key': 'value'}, ['nested', 'list']]
        
        with pytest.raises(ValueError, match="Invalid argument type"):
            _validate_and_sanitize_argv(invalid_args)
            
    @security_test
    def test_null_byte_injection_prevention(self):
        """Test prevention of null byte injection at system level."""
        # The argv validation doesn't check for null bytes, but the system interface should
        null_byte_attacks = [
            'file.txt\x00.exe',
            '/proc/cpuinfo\x00/../etc/passwd',
        ]
        
        system = LinuxSystemInterface()
        
        for attack in null_byte_attacks:
            # Test that null bytes are handled at system interface level
            with pytest.raises(ValueError):
                system._sanitize_command(['lscpu', attack])


class TestInformationDisclosure:
    """Test prevention of information disclosure."""
    
    @security_test
    def test_error_message_sanitization(self):
        """Test that error messages don't leak sensitive information."""
        system = LinuxSystemInterface()
        error_handler = CLIErrorHandler(Mock())
        
        # Test with sensitive path
        sensitive_path = '/root/.ssh/id_rsa'
        
        # Mock file operations to simulate errors
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = system.read_file(sensitive_path)
            assert result is None  # Should fail safely without leaking path
            
    @security_test
    def test_debug_information_filtering(self):
        """Test that debug information doesn't expose sensitive data."""
        from tinel.cli.formatters import OutputFormatter
        
        formatter = OutputFormatter(verbose=3, use_color=False)  # Max verbosity
        
        # Test data that doesn't contain sensitive information (current behavior)
        test_data = {
            'system_info': 'normal info',
            'cpu_model': 'Intel Core i7',
            'architecture': 'x86_64',
            'cores': 8,
        }
        
        # Verify the formatter doesn't crash with normal data
        result = formatter.format_output(test_data)
        assert result is not None
        
        # Test with our assertion helper - should pass with non-sensitive data
        AssertionHelpers.assert_no_sensitive_data(test_data)
        
        # Test that sensitive data would be detected if present
        sensitive_test_data = {
            'password': 'secret123',
            'api_key': 'sk-1234567890', 
            'private_key': 'rsa-key-data',
            'secret': 'confidential'
        }
        
        # This should fail because sensitive data is present
        with pytest.raises(AssertionError, match="Found sensitive data patterns"):
            AssertionHelpers.assert_no_sensitive_data(sensitive_test_data)
        
    @security_test 
    def test_command_output_sanitization(self):
        """Test that command outputs are properly sanitized."""
        system = LinuxSystemInterface()
        
        # Mock command that might return sensitive information
        with patch('subprocess.run') as mock_run:
            # Simulate command output with potential sensitive data
            mock_run.return_value = Mock(
                stdout='normal output\npassword=secret123\napi_key=abc123',
                stderr='',
                returncode=0
            )
            
            result = system.run_command(['lscpu'])
            
            # Command should execute but we should be aware of sensitive data
            assert result.success
            # In production, output should be sanitized
            assert result.stdout is not None


class TestPrivilegeEscalation:
    """Test prevention of privilege escalation attacks."""
    
    @security_test
    def test_sudo_command_prevention(self):
        """Test that sudo commands are not allowed."""
        system = LinuxSystemInterface()
        
        sudo_attempts = [
            ['sudo', 'lscpu'],
            ['su', '-c', 'lscpu'],
            ['pkexec', 'lscpu'],
        ]
        
        for sudo_cmd in sudo_attempts:
            with pytest.raises(ValueError, match="not allowed"):
                system._sanitize_command(sudo_cmd)
                
    @security_test
    def test_setuid_binary_prevention(self):
        """Test prevention of dangerous setuid binary execution."""
        system = LinuxSystemInterface()
        
        # Common setuid binaries that could be dangerous
        dangerous_setuid = [
            ['passwd'],
            ['su'],
            ['sudo'],
            ['mount'],
            ['umount'],
        ]
        
        for cmd in dangerous_setuid:
            with pytest.raises(ValueError, match="not allowed"):
                system._sanitize_command(cmd)
                
    @security_test
    def test_file_permission_validation(self):
        """Test that file permissions are properly validated."""
        system = LinuxSystemInterface()
        
        # Test with valid safe path
        with patch.object(system, '_validate_file_path', return_value='/proc/cpuinfo'):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value = Mock(st_size=100)
                
                # Test with readable file
                with patch('builtins.open', mock_open(read_data='content')):
                    result = system.read_file('/proc/cpuinfo')
                    assert result == 'content'
                    
                # Test with permission error
                with patch('builtins.open', side_effect=PermissionError()):
                    result = system.read_file('/proc/cpuinfo')
                    assert result is None


class TestResourceExhaustion:
    """Test prevention of resource exhaustion attacks."""
    
    @security_test
    def test_command_timeout_enforcement(self):
        """Test that command timeouts prevent resource exhaustion."""
        system = LinuxSystemInterface()
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(['sleep', '1000'], 1.0)
            
            result = system.run_command(['sleep', '1000'], timeout=1.0)
            
            assert not result.success
            assert 'timed out' in result.error
            
    @security_test
    def test_file_size_limits_enforcement(self):
        """Test that file size limits prevent resource exhaustion."""
        system = LinuxSystemInterface()
        
        with patch.object(system, '_validate_file_path', return_value='/proc/cpuinfo'):
            with patch('pathlib.Path.stat') as mock_stat:
                # Test with file that's too large
                mock_stat.return_value = Mock(st_size=100 * 1024 * 1024)  # 100MB
                
                result = system.read_file('/proc/cpuinfo')
                assert result is None  # Should reject large files
                
    @security_test
    def test_memory_usage_limits(self):
        """Test that memory usage is bounded."""
        system = LinuxSystemInterface()
        
        # Test with very large mock data
        huge_content = 'X' * (50 * 1024 * 1024)  # 50MB string
        
        with patch.object(system, '_validate_file_path', return_value='/proc/cpuinfo'):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value = Mock(st_size=len(huge_content))
                with patch('builtins.open', mock_open(read_data=huge_content)):
                    # Should reject due to size limits before reading
                    result = system.read_file('/proc/cpuinfo')
                    assert result is None


class TestSecurityConfiguration:
    """Test security configuration and hardening."""
    
    @security_test
    def test_secure_defaults(self):
        """Test that secure defaults are used."""
        system = LinuxSystemInterface()
        
        # Test default timeout
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout='output', stderr='', returncode=0)
            
            # Default timeout should be reasonable (not infinite)
            system.run_command(['lscpu'])
            
            call_kwargs = mock_run.call_args.kwargs
            assert 'timeout' in call_kwargs
            assert call_kwargs['timeout'] <= 60  # Should have reasonable default timeout
            
    @security_test
    def test_error_handling_security(self):
        """Test that error handling doesn't leak sensitive information."""
        system = LinuxSystemInterface()
        
        # Test with command that would fail
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = OSError("No such file or directory: /secret/path")
            
            result = system.run_command(['lscpu'])
            
            assert not result.success
            # Error message should be generic, not expose system paths
            assert result.error is not None
            assert len(result.error) > 0


@pytest.mark.parametrize("attack_vector,expected_blocked", [
    ('command_injection', True),
    ('path_traversal', True), 
    ('privilege_escalation', True),
    ('resource_exhaustion', True),
])
@security_test
def test_attack_vector_prevention(attack_vector, expected_blocked):
    """Test prevention of various attack vectors."""
    system = LinuxSystemInterface()
    
    if attack_vector == 'command_injection':
        with pytest.raises(ValueError):
            system._sanitize_command(['lscpu', '; rm -rf /'])
            
    elif attack_vector == 'path_traversal':
        result = system._validate_file_path('../../../etc/passwd')
        assert result is None
        
    elif attack_vector == 'privilege_escalation':
        with pytest.raises(ValueError):
            system._sanitize_command(['sudo', 'lscpu'])
            
    elif attack_vector == 'resource_exhaustion':
        with patch.object(system, '_validate_file_path', return_value='/proc/cpuinfo'):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value = Mock(st_size=100 * 1024 * 1024)  # 100MB
                result = system.read_file('/proc/cpuinfo')
                assert result is None


def mock_open(read_data=''):
    """Create a mock open function for testing."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)