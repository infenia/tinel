#!/usr/bin/env python3
"""
Testing utilities and helpers for Tinel tests.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import contextlib
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union
from unittest.mock import Mock, patch

import pytest


class TestDataBuilder:
    """Builder for creating test data structures."""
    
    @staticmethod
    def create_command_result(
        success: bool = True,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        error: Optional[str] = None
    ):
        """Create a CommandResult for testing."""
        from tinel.interfaces import CommandResult
        return CommandResult(
            success=success,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            error=error
        )
    
    @staticmethod
    def create_hardware_info(**kwargs):
        """Create a HardwareInfo object for testing."""
        from tinel.interfaces import HardwareInfo
        defaults = {
            'cpu': {'model': 'Test CPU', 'cores': 4}
        }
        defaults.update(kwargs)
        return HardwareInfo(**defaults)


class MockProcessManager:
    """Manager for mock processes and system commands."""
    
    def __init__(self):
        self.command_responses: Dict[str, Any] = {}
        self.command_call_count: Dict[str, int] = {}
        
    def add_command_response(self, command: Union[str, List[str]], response: Any):
        """Add a response for a specific command."""
        key = ' '.join(command) if isinstance(command, list) else command
        self.command_responses[key] = response
        
    def get_command_response(self, command: Union[str, List[str]]):
        """Get response for a command and increment call count."""
        key = ' '.join(command) if isinstance(command, list) else command
        self.command_call_count[key] = self.command_call_count.get(key, 0) + 1
        return self.command_responses.get(key, TestDataBuilder.create_command_result())
        
    def get_call_count(self, command: Union[str, List[str]]) -> int:
        """Get the number of times a command was called."""
        key = ' '.join(command) if isinstance(command, list) else command
        return self.command_call_count.get(key, 0)


class FileSystemMocker:
    """Mock file system operations for testing."""
    
    def __init__(self):
        self.files: Dict[str, str] = {}
        self.file_permissions: Dict[str, bool] = {}
        self.access_log: List[str] = []
        
    def add_file(self, path: str, content: str, readable: bool = True):
        """Add a file to the mock filesystem."""
        self.files[path] = content
        self.file_permissions[path] = readable
        
    def read_file(self, path: str) -> Optional[str]:
        """Mock file reading with permission checks."""
        self.access_log.append(f"read:{path}")
        
        if path not in self.files:
            return None
            
        if not self.file_permissions.get(path, True):
            raise PermissionError(f"Permission denied: {path}")
            
        return self.files[path]
        
    def file_exists(self, path: str) -> bool:
        """Mock file existence check."""
        self.access_log.append(f"exists:{path}")
        return path in self.files
        
    def was_accessed(self, path: str, operation: str = None) -> bool:
        """Check if a file was accessed."""
        if operation:
            return f"{operation}:{path}" in self.access_log
        return any(log.endswith(f":{path}") for log in self.access_log)


class TimeoutManager:
    """Manage timeouts for testing long-running operations."""
    
    def __init__(self, default_timeout: float = 5.0):
        self.default_timeout = default_timeout
        self._timers: List[threading.Timer] = []
        
    @contextlib.contextmanager
    def timeout(self, seconds: Optional[float] = None):
        """Context manager for operation timeouts."""
        timeout_seconds = seconds or self.default_timeout
        
        def timeout_handler():
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
            
        timer = threading.Timer(timeout_seconds, timeout_handler)
        self._timers.append(timer)
        timer.start()
        
        try:
            yield
        finally:
            timer.cancel()
            if timer in self._timers:
                self._timers.remove(timer)
                
    def cleanup(self):
        """Cancel all active timers."""
        for timer in self._timers:
            timer.cancel()
        self._timers.clear()


class AssertionHelpers:
    """Custom assertion helpers for testing."""
    
    @staticmethod
    def assert_contains_keys(data: Dict[str, Any], required_keys: List[str]):
        """Assert that dictionary contains all required keys."""
        missing_keys = set(required_keys) - set(data.keys())
        assert not missing_keys, f"Missing required keys: {missing_keys}"
        
    @staticmethod
    def assert_valid_cpu_info(cpu_info: Dict[str, Any]):
        """Assert that CPU info contains expected structure."""
        required_keys = ['model_name', 'vendor_id', 'cpu_flags']
        AssertionHelpers.assert_contains_keys(cpu_info, required_keys)
        
        # Check specific data types
        assert isinstance(cpu_info['cpu_flags'], list), "CPU flags should be a list"
        assert len(cpu_info['cpu_flags']) > 0, "CPU flags list should not be empty"
        
    @staticmethod
    def assert_performance_within_bounds(elapsed_time: float, max_time: float, min_time: float = 0):
        """Assert that performance is within acceptable bounds."""
        assert min_time <= elapsed_time <= max_time, \
            f"Performance out of bounds: {elapsed_time:.3f}s (expected {min_time:.3f}s - {max_time:.3f}s)"
            
    @staticmethod
    def assert_no_sensitive_data(data: Any, sensitive_patterns: Optional[List[str]] = None):
        """Assert that data doesn't contain sensitive information."""
        if sensitive_patterns is None:
            sensitive_patterns = ['password', 'token', 'key', 'secret']
            
        data_str = str(data).lower()
        found_patterns = [pattern for pattern in sensitive_patterns if pattern in data_str]
        assert not found_patterns, f"Found sensitive data patterns: {found_patterns}"


class SecurityTestHelpers:
    """Helpers for security-related testing."""
    
    @staticmethod
    def create_malicious_inputs() -> List[str]:
        """Create list of potentially malicious inputs for testing."""
        return [
            "; rm -rf /",
            "$(rm -rf /)",
            "|nc -l 4444",
            "`cat /etc/passwd`",
            "../../../etc/passwd",
            "file://etc/passwd",
            "\x00\x01\x02",  # null bytes
            "A" * 10000,      # very long input
            "${PATH}",
            "$IFS",
        ]
        
    @staticmethod
    def create_path_traversal_attempts() -> List[str]:
        """Create list of path traversal attempts."""
        return [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/proc/../../../etc/passwd",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
        ]
        
    @staticmethod  
    def assert_safe_command(command: List[str]):
        """Assert that a command is safe to execute."""
        dangerous_commands = ['rm', 'dd', 'mkfs', 'fdisk', 'shutdown', 'reboot']
        dangerous_chars = [';', '|', '&', '`', '$', '(', ')', '>', '<']
        
        # Check for dangerous commands
        if command:
            base_cmd = command[0].split('/')[-1]  # Get just the command name
            assert base_cmd not in dangerous_commands, f"Dangerous command detected: {base_cmd}"
            
        # Check for dangerous characters in arguments
        for arg in command:
            for char in dangerous_chars:
                assert char not in arg, f"Dangerous character '{char}' found in argument: {arg}"


class PerformanceTestHelpers:
    """Helpers for performance testing."""
    
    @staticmethod
    @contextlib.contextmanager
    def measure_time() -> Generator[Dict[str, Any], None, None]:
        """Context manager to measure execution time."""
        result = {'start': None, 'end': None, 'elapsed': None}
        
        result['start'] = time.perf_counter()
        try:
            yield result
        finally:
            result['end'] = time.perf_counter()
            result['elapsed'] = result['end'] - result['start']
            
    @staticmethod
    def assert_cached_performance(cached_call, uncached_call, min_improvement: float = 2.0):
        """Assert that cached calls are significantly faster than uncached."""
        # Time uncached call
        with PerformanceTestHelpers.measure_time() as uncached_result:
            uncached_call()
            
        # Time cached call
        with PerformanceTestHelpers.measure_time() as cached_result:
            cached_call()
            
        improvement_ratio = uncached_result['elapsed'] / cached_result['elapsed']
        assert improvement_ratio >= min_improvement, \
            f"Cached call not fast enough: {improvement_ratio:.2f}x improvement (expected >= {min_improvement}x)"


class IntegrationTestHelpers:
    """Helpers for integration testing."""
    
    @staticmethod
    @contextlib.contextmanager
    def temporary_config_file(config_content: str) -> Generator[Path, None, None]:
        """Create a temporary configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
            
        try:
            yield config_path
        finally:
            config_path.unlink(missing_ok=True)
            
    @staticmethod
    @contextlib.contextmanager
    def mock_system_environment(**env_vars) -> Generator[None, None, None]:
        """Context manager to mock environment variables."""
        original_values = {}
        
        # Set new values and store originals
        for key, value in env_vars.items():
            original_values[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
                
        try:
            yield
        finally:
            # Restore original values
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


def create_test_categories():
    """Create test categories for organizing tests."""
    return {
        'unit': {
            'description': 'Fast, isolated tests of individual components',
            'max_duration': 0.1,  # 100ms
            'requires_system': False
        },
        'integration': {
            'description': 'Tests of component interactions',
            'max_duration': 1.0,  # 1 second
            'requires_system': True
        },
        'performance': {
            'description': 'Tests verifying performance characteristics',
            'max_duration': 5.0,  # 5 seconds
            'requires_system': True
        },
        'security': {
            'description': 'Tests verifying security measures',
            'max_duration': 2.0,  # 2 seconds
            'requires_system': False
        },
        'e2e': {
            'description': 'End-to-end tests of complete workflows',
            'max_duration': 10.0,  # 10 seconds
            'requires_system': True
        }
    }


# Test decorators for different test types
def unit_test(func):
    """Decorator for unit tests."""
    return pytest.mark.unit(func)


def integration_test(func):
    """Decorator for integration tests."""
    return pytest.mark.integration(func)


def performance_test(func):
    """Decorator for performance tests."""
    return pytest.mark.performance(func)


def security_test(func):
    """Decorator for security tests."""
    return pytest.mark.security(func)


def slow_test(func):
    """Decorator for slow tests."""
    return pytest.mark.slow(func)


# Export commonly used test utilities
__all__ = [
    'TestDataBuilder',
    'MockProcessManager', 
    'FileSystemMocker',
    'TimeoutManager',
    'AssertionHelpers',
    'SecurityTestHelpers',
    'PerformanceTestHelpers',
    'IntegrationTestHelpers',
    'unit_test',
    'integration_test',
    'performance_test',
    'security_test',
    'slow_test',
    'create_test_categories'
]