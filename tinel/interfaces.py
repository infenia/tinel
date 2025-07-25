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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CommandResult:
    """Result of a system command execution."""

    success: bool
    stdout: str
    stderr: str
    returncode: int
    error: Optional[str] = None




@dataclass
class HardwareInfo:
    """Comprehensive hardware information."""

    cpu: Dict[str, Any]




class SystemInterface(ABC):
    """Abstract interface for system interactions."""

    @abstractmethod
    def run_command(self, cmd: List[str]) -> CommandResult:
        """Execute a system command and return the result."""
        pass

    @abstractmethod
    def read_file(self, path: str) -> Optional[str]:
        """Read a file from the filesystem."""
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass




class ToolProvider(ABC):
    """Abstract interface for MCP tool providers."""

    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        pass

    @abstractmethod
    def get_tool_description(self) -> str:
        """Get the description of the tool."""
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        pass

    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
