#!/usr/bin/env python3
"""
Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from .interfaces import CommandResult, SystemInterface


class LinuxSystemInterface(SystemInterface):
    """Linux system interface implementation."""

    def run_command(self, cmd: List[str], timeout: int = 30) -> CommandResult:
        """Execute a system command and return the result.

        Args:
            cmd: Command to execute as a list of strings
            timeout: Command timeout in seconds

        Returns:
            CommandResult containing execution results

        Raises:
            ValueError: If command contains unsafe characters
        """
        # Security: Validate command arguments
        if not cmd or not all(isinstance(arg, str) for arg in cmd):
            return CommandResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error="Invalid command arguments",
            )

        # Security: Sanitize command arguments
        sanitized_cmd = self._sanitize_command(cmd)

        try:
            result = subprocess.run(
                sanitized_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,  # Security: Never use shell=True
                env=self._get_safe_environment(),  # Security: Controlled environment
            )
            return CommandResult(
                success=result.returncode == 0,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                returncode=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=f"Command timed out after {timeout} seconds",
            )
        except (OSError, ValueError) as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=f"Command execution failed: {e}",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=f"Unexpected error: {e}",
            )

    def read_file(self, path: str, max_size: int = 10 * 1024 * 1024) -> Optional[str]:
        """Read a file from the filesystem with security checks.

        Args:
            path: Path to the file to read
            max_size: Maximum file size to read (default 10MB)

        Returns:
            File contents as string or None if file couldn't be read
        """
        try:
            # Security: Validate and normalize path
            safe_path = self._validate_file_path(path)
            if not safe_path:
                return None

            # Security: Check file size before reading
            file_path = Path(safe_path)
            if file_path.stat().st_size > max_size:
                return None

            with open(safe_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except (OSError, UnicodeDecodeError, PermissionError):
            return None

    def file_exists(self, path: str) -> bool:
        """Check if a file exists.

        Args:
            path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        return Path(path).exists()

    def _sanitize_command(self, cmd: List[str]) -> List[str]:
        """Sanitize command arguments for security.

        Args:
            cmd: Command arguments to sanitize

        Returns:
            Sanitized command arguments

        Raises:
            ValueError: If command contains unsafe characters
        """
        # Allow list of safe commands for hardware analysis
        safe_commands = {
            "lscpu",
            "lspci",
            "lsusb",
            "lsblk",
            "df",
            "ip",
            "cat",
            "head",
            "tail",
            "dmidecode",
            "lshw",
            "nvidia-smi",
            "nproc",
            "uname",
            "echo",
            "sleep",  # echo and sleep for testing
        }

        if not cmd:
            raise ValueError("Empty command")

        base_command = cmd[0].split("/")[-1]  # Get just the command name
        if base_command not in safe_commands:
            raise ValueError(f"Command '{base_command}' not allowed")

        # Sanitize arguments - remove potentially dangerous characters
        sanitized = []
        dangerous_chars = re.compile(r"[;&|`$(){}[\]<>\x00]")  # Include null bytes

        for arg in cmd:
            if dangerous_chars.search(arg):
                raise ValueError(f"Dangerous characters found in argument: {arg}")
            sanitized.append(arg)

        return sanitized

    def _get_safe_environment(self) -> Dict[str, str]:
        """Get a safe environment for command execution.

        Returns:
            Dictionary containing safe environment variables
        """
        # Minimal environment to reduce attack surface
        safe_env = {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "LC_ALL": "C",  # Consistent locale for parsing
            "LANG": "C",
        }

        # Preserve essential variables if they exist
        for var in ["HOME", "USER", "LOGNAME"]:
            if var in os.environ:
                safe_env[var] = os.environ[var]

        return safe_env

    def _validate_file_path(self, path: str) -> Optional[str]:
        """Validate and normalize file path for security.

        Args:
            path: File path to validate

        Returns:
            Safe normalized path or None if invalid
        """
        try:
            # Security: Only allow reading from safe system paths and specific files
            safe_paths = [
                # Directories (with trailing slash to match prefixes)
                "/proc/",
                "/sys/",
                "/usr/share/",
                "/var/log/",
                # Specific safe files in /etc/
                "/etc/os-release",
                "/etc/hostname",
                "/etc/machine-id",
                "/etc/lsb-release",
            ]

            # Security: Prevent path traversal attempts before normalization
            if ".." in path or not path.startswith("/"):
                return None

            # Normalize path to prevent directory traversal
            normalized = os.path.normpath(path)

            # Security: Check if path is allowed
            allowed = False
            for safe_path in safe_paths:
                if safe_path.endswith("/"):
                    # Directory prefix check
                    if normalized.startswith(safe_path):
                        allowed = True
                        break
                else:
                    # Exact file match
                    if normalized == safe_path:
                        allowed = True
                        break

            if not allowed:
                return None

            return normalized
        except (ValueError, OSError):
            return None
