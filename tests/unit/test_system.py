#!/usr/bin/env python3
"""
Unit tests for system interface implementations.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from tinel.system import LinuxSystemInterface
from tinel.interfaces import CommandResult
from tests.utils import (
    unit_test,
    SecurityTestHelpers,
    AssertionHelpers,
    TestDataBuilder,
)


class TestLinuxSystemInterface:
    """Test cases for LinuxSystemInterface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.system = LinuxSystemInterface()

    @unit_test
    def test_run_command_success(self):
        """Test successful command execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="test output", stderr="", returncode=0)

            result = self.system.run_command(["echo", "test"])

            assert result.success is True
            assert result.stdout == "test output"
            assert result.stderr == ""
            assert result.returncode == 0
            assert result.error is None

    @unit_test
    def test_run_command_failure(self):
        """Test command execution failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="", stderr="command not found", returncode=127
            )

            result = self.system.run_command(["lscpu", "--invalid-flag"])

            assert result.success is False
            assert result.returncode == 127
            assert result.stderr == "command not found"

    @unit_test
    def test_run_command_timeout(self):
        """Test command timeout handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(["sleep", "10"], 5)

            result = self.system.run_command(["sleep", "10"], timeout=5)

            assert result.success is False
            assert result.returncode == -1
            assert "timed out after 5 seconds" in result.error

    @unit_test
    def test_run_command_with_safe_environment(self):
        """Test that commands run with safe environment."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

            self.system.run_command(["lscpu"])

            # Verify subprocess.run was called with safe environment
            call_args = mock_run.call_args
            env = call_args.kwargs.get("env", {})

            assert "PATH" in env
            assert env["PATH"] == "/usr/bin:/bin:/usr/sbin:/sbin"
            assert env["LC_ALL"] == "C"
            assert env["LANG"] == "C"

    @unit_test
    def test_sanitize_command_allowed_commands(self):
        """Test command sanitization allows safe commands."""
        safe_commands = ["lscpu", "lspci", "lsusb", "lsblk", "df", "ip"]

        for cmd in safe_commands:
            result = self.system._sanitize_command([cmd])
            assert result == [cmd]

    @unit_test
    def test_sanitize_command_disallowed_commands(self):
        """Test command sanitization blocks dangerous commands."""
        dangerous_commands = ["rm", "dd", "mkfs", "shutdown"]

        for cmd in dangerous_commands:
            with pytest.raises(ValueError, match=f"Command '{cmd}' not allowed"):
                self.system._sanitize_command([cmd])

    @unit_test
    def test_sanitize_command_dangerous_characters(self):
        """Test command sanitization blocks dangerous characters."""
        dangerous_args = [
            "arg;rm",
            "arg&echo",
            "arg|cat",
            "arg`whoami`",
            "arg$(id)",
            "arg{test}",
            "arg[0]",
            "arg<file",
            "arg>file",
        ]

        for dangerous_arg in dangerous_args:
            with pytest.raises(ValueError, match="Dangerous characters found"):
                self.system._sanitize_command(["lscpu", dangerous_arg])

    @unit_test
    def test_sanitize_command_empty_command(self):
        """Test command sanitization handles empty command."""
        with pytest.raises(ValueError, match="Empty command"):
            self.system._sanitize_command([])

    @unit_test
    def test_read_file_success(self):
        """Test successful file reading."""
        mock_content = "test file content"

        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(
                self.system, "_validate_file_path", return_value="/proc/cpuinfo"
            ):
                with patch("pathlib.Path.stat") as mock_stat:
                    mock_stat.return_value = Mock(st_size=100)

                    result = self.system.read_file("/proc/cpuinfo")

                    assert result == mock_content.strip()

    @unit_test
    def test_read_file_invalid_path(self):
        """Test file reading with invalid path."""
        with patch.object(self.system, "_validate_file_path", return_value=None):
            result = self.system.read_file("../../../etc/passwd")
            assert result is None

    @unit_test
    def test_read_file_too_large(self):
        """Test file reading with file too large."""
        with patch.object(
            self.system, "_validate_file_path", return_value="/proc/cpuinfo"
        ):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value = Mock(st_size=20 * 1024 * 1024)  # 20MB

                result = self.system.read_file("/proc/cpuinfo")
                assert result is None

    @unit_test
    def test_read_file_permission_error(self):
        """Test file reading with permission error."""
        with patch.object(
            self.system, "_validate_file_path", return_value="/proc/cpuinfo"
        ):
            with patch("pathlib.Path.stat") as mock_stat:
                mock_stat.return_value = Mock(st_size=100)
                with patch("builtins.open", side_effect=PermissionError()):
                    result = self.system.read_file("/proc/cpuinfo")
                    assert result is None

    @unit_test
    def test_validate_file_path_safe_paths(self):
        """Test path validation allows safe paths."""
        safe_paths = [
            "/proc/cpuinfo",
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor",
            "/etc/hostname",
            "/usr/share/doc/readme.txt",
        ]

        for safe_path in safe_paths:
            result = self.system._validate_file_path(safe_path)
            assert result == safe_path

    @unit_test
    def test_validate_file_path_dangerous_paths(self):
        """Test path validation blocks dangerous paths."""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/home/../../../etc/passwd",  # tries to traverse from /home
            "....//....//....//home/user",
            "/home/user/file",  # not in whitelist
            "/tmp/file",  # not in whitelist
            "relative/path",  # not absolute
        ]

        for dangerous_path in dangerous_paths:
            result = self.system._validate_file_path(dangerous_path)
            assert result is None

    @unit_test
    def test_validate_file_path_non_whitelisted(self):
        """Test path validation blocks non-whitelisted directories."""
        non_whitelisted_paths = [
            "/home/user/secret.txt",
            "/root/.ssh/id_rsa",
            "/tmp/malicious.sh",
        ]

        for path in non_whitelisted_paths:
            result = self.system._validate_file_path(path)
            assert result is None

    @unit_test
    def test_get_safe_environment(self):
        """Test safe environment generation."""
        with patch.dict(os.environ, {"HOME": "/home/test", "USER": "test"}):
            env = self.system._get_safe_environment()

            # Check required safe variables
            assert env["PATH"] == "/usr/bin:/bin:/usr/sbin:/sbin"
            assert env["LC_ALL"] == "C"
            assert env["LANG"] == "C"

            # Check preserved variables
            assert env["HOME"] == "/home/test"
            assert env["USER"] == "test"

    @unit_test
    def test_file_exists(self):
        """Test file existence checking."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            result = self.system.file_exists("/proc/cpuinfo")
            assert result is True

            mock_exists.return_value = False
            result = self.system.file_exists("/nonexistent/file")
            assert result is False

    @unit_test
    def test_run_command_input_validation(self):
        """Test command input validation."""
        # Test empty command list
        result = self.system.run_command(None)
        assert result.success is False
        assert "Invalid command arguments" in result.error

        # Test non-string arguments
        result = self.system.run_command(["lscpu", 123])
        assert result.success is False
        assert "Invalid command arguments" in result.error

    @unit_test
    def test_run_command_security_measures(self):
        """Test that security measures are properly applied."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="output", stderr="", returncode=0)

            self.system.run_command(["lscpu"])

            # Verify security settings
            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs["shell"] is False  # Never use shell=True
            assert "env" in call_kwargs  # Custom environment provided
            assert call_kwargs["capture_output"] is True
            assert call_kwargs["text"] is True


class TestCommandResultCreation:
    """Test CommandResult creation and validation."""

    @unit_test
    def test_command_result_creation(self):
        """Test creating CommandResult objects."""
        result = TestDataBuilder.create_command_result(
            success=True, stdout="test output", stderr="", returncode=0
        )

        assert result.success is True
        assert result.stdout == "test output"
        assert result.stderr == ""
        assert result.returncode == 0
        assert result.error is None

    @unit_test
    def test_command_result_with_error(self):
        """Test creating CommandResult with error."""
        result = TestDataBuilder.create_command_result(
            success=False,
            stdout="",
            stderr="error message",
            returncode=1,
            error="Command failed",
        )

        assert result.success is False
        assert result.error == "Command failed"
        assert result.returncode == 1


@pytest.mark.parametrize("timeout_value", [1.0, 5.0, 30.0, 60.0])
@unit_test
def test_custom_timeout_values(timeout_value):
    """Test different timeout values are properly handled."""
    system = LinuxSystemInterface()

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["sleep"], timeout_value)

        result = system.run_command(["sleep", "1"], timeout=timeout_value)

        assert result.success is False
        assert f"timed out after {timeout_value} seconds" in result.error

        # Verify timeout was passed to subprocess.run
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["timeout"] == timeout_value


@pytest.mark.parametrize(
    "command,expected_allowed",
    [
        (["lscpu"], True),
        (["lspci"], True),
        (["lsusb"], True),
        (["lsblk"], True),
        (["df"], True),
        (["ip"], True),
        (["cat", "/proc/cpuinfo"], True),
        (["dmidecode"], True),
        (["lshw"], True),
        (["rm", "-rf", "/"], False),
        (["dd", "if=/dev/zero"], False),
        (["shutdown", "-h", "now"], False),
        (["mkfs.ext4", "/dev/sda1"], False),
    ],
)
@unit_test
def test_command_whitelist(command, expected_allowed):
    """Test command whitelist validation."""
    system = LinuxSystemInterface()

    if expected_allowed:
        result = system._sanitize_command(command)
        assert result == command
    else:
        with pytest.raises(ValueError):
            system._sanitize_command(command)
