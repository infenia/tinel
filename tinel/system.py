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

"""This module provides a Linux-specific implementation of the SystemInterface.

It offers a secure and robust way to execute system commands and read files,
with a strong emphasis on security. The LinuxSystemInterface class includes
mechanisms to prevent command injection, path traversal, and other common
vulnerabilities. It is the primary means by which Tinel interacts with the
underlying operating system.
"""


class LinuxSystemInterface(SystemInterface):
    """Provides a concrete implementation of the SystemInterface for Linux systems.

    This class is responsible for all interactions with the Linux operating
    system, including executing commands and reading files. It is designed
    with security as a primary concern, incorporating features such as command
    sanitization, allow-listed commands, and restricted file access to
    minimize the risk of vulnerabilities.
    """

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

        try:
            # Security: Sanitize command arguments
            sanitized_cmd = self._sanitize_command(cmd)
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
        """Reads a file from the filesystem with enhanced security checks.

        This method validates the file path against a list of safe locations,
        checks the file size to prevent denial-of-service attacks, and handles
        potential exceptions gracefully. It is the recommended way to read
        files from the system.

        Args:
            path: The absolute path to the file to be read.
            max_size: The maximum allowed file size in bytes. Defaults to 10MB.

        Returns:
            The content of the file as a string if successful, otherwise None.
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
        """Checks if a file exists at the specified path.

        This method provides a simple and safe way to check for the existence
        of a file. It uses `pathlib.Path` for robust path handling.

        Args:
            path: The path to the file to check.

        Returns:
            True if the file exists, False otherwise.
        """
        return Path(path).exists()

    def list_dir(self, path: str) -> List[str]:
        """Lists the contents of a directory.

        Args:
            path: The path to the directory.

        Returns:
            A list of names of the entries in the directory.

        Raises:
            FileNotFoundError: If the path does not exist.
            PermissionError: If the user does not have permission to read the
                             directory.
        """
        safe_path = self._validate_file_path(path)
        if not safe_path:
            return []
        return os.listdir(safe_path)

    def readlink(self, path: str) -> str:
        """Reads the value of a symbolic link.

        Args:
            path: The path to the symbolic link.

        Returns:
            A string representing the path to which the symbolic link points.

        Raises:
            FileNotFoundError: If the link does not exist.
            OSError: If the path is not a symbolic link.
        """
        safe_path = self._validate_file_path(path)
        if not safe_path:
            return ""
        return os.readlink(safe_path)

    def _sanitize_command(self, cmd: List[str]) -> List[str]:
        """Sanitizes and validates a command and its arguments for security.

        This method enforces a strict security policy by checking the command
        against an allow-list and scanning all arguments for potentially
        dangerous characters. It is a critical component of the application's
        defense against command injection attacks.

        Args:
            cmd: A list of strings representing the command and its arguments.

        Returns:
            The sanitized list of command arguments.

        Raises:
            ValueError: If the command is not in the allow-list or if any
                        argument contains dangerous characters.
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
            "smartctl",
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
        """Creates a safe environment for executing system commands.

        This method constructs a minimal set of environment variables to reduce
        the potential attack surface. It includes only essential variables like
        `PATH` and `LC_ALL`, while discarding others that could be exploited.

        Returns:
            A dictionary representing a safe environment for command execution.
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
        """Validates and normalizes a file path for secure access.

        This method ensures that file access is restricted to a predefined list
        of safe directories and files. It also prevents path traversal attacks
        by rejecting paths containing '..' and normalizing the path before
        validation.

        Args:
            path: The file path to validate.

        Returns:
            The normalized, safe path if it is valid, otherwise None.
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
                # Exact file match
                elif normalized == safe_path:
                    allowed = True
                    break

            if not allowed:
                return None

            return normalized
        except (ValueError, OSError):
            return None
