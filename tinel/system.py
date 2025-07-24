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


import subprocess
from pathlib import Path
from typing import List, Optional

from .interfaces import CommandResult, SystemInterface


class LinuxSystemInterface(SystemInterface):
    """Linux system interface implementation."""
    
    def run_command(self, cmd: List[str]) -> CommandResult:
        """Execute a system command and return the result.
        
        Args:
            cmd: Command to execute as a list of strings
            
        Returns:
            CommandResult containing execution results
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return CommandResult(
                success=True,
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
                error="Command timed out",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr="",
                returncode=-1,
                error=str(e),
            )
    
    def read_file(self, path: str) -> Optional[str]:
        """Read a file from the filesystem.
        
        Args:
            path: Path to the file to read
            
        Returns:
            File contents as string or None if file couldn't be read
        """
        try:
            with open(path, 'r') as f:
                return f.read().strip()
        except Exception:
            return None
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists.
        
        Args:
            path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        return Path(path).exists()