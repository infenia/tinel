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

"""This module defines the core interfaces and data structures for Tinel.

It includes abstract base classes (ABCs) for system interactions and tool
providers, as well as dataclasses for representing command results and
hardware information. These interfaces ensure a consistent and extensible
architecture for the entire application.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CommandResult:
    """Represents the result of a system command execution.

    This dataclass encapsulates the standard output, standard error, return code,
    and success status of a command, providing a structured way to handle
    command results throughout the application.

    Attributes:
        success: A boolean indicating whether the command executed successfully.
        stdout: The standard output of the command as a string.
        stderr: The standard error of the command as a string.
        returncode: The integer return code of the command.
        error: An optional string containing any error message if the command
               failed to execute.
    """

    success: bool
    stdout: str
    stderr: str
    returncode: int
    error: Optional[str] = None


@dataclass
class HardwareInfo:
    """Represents a comprehensive collection of hardware information.

    This dataclass aggregates information from all hardware analyzers, providing
    a single, structured object that contains details about the CPU, memory,
    storage, and other hardware components of the system.

    Attributes:
        cpu: A dictionary containing CPU information.
        memory: A dictionary containing memory information.
        storage: A dictionary containing storage information.
        pci: A dictionary containing PCI device information.
        usb: A dictionary containing USB device information.
        network: A dictionary containing network interface information.
        graphics: A dictionary containing graphics card information.
    """

    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    storage: Dict[str, Any]
    pci: Dict[str, Any]
    usb: Dict[str, Any]
    network: Dict[str, Any]
    graphics: Dict[str, Any]


class SystemInterface(ABC):
    """Defines an abstract interface for system interactions.

    This abstract base class (ABC) specifies a contract for classes that
    provide system-level functionalities, such as running commands and
    accessing the filesystem. By depending on this interface, the application
    can be easily tested and adapted to different environments.
    """

    @abstractmethod
    def run_command(self, cmd: List[str]) -> CommandResult:
        """Executes a system command and returns the result.

        Args:
            cmd: A list of strings representing the command and its arguments.

        Returns:
            A CommandResult object containing the outcome of the command execution.
        """
        pass

    @abstractmethod
    def read_file(self, path: str) -> Optional[str]:
        """Reads a file from the filesystem.

        Args:
            path: The absolute or relative path to the file.

        Returns:
            The content of the file as a string, or None if the file cannot be read.
        """
        pass

    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Checks if a file exists at the given path.

        Args:
            path: The path to the file.

        Returns:
            True if the file exists, False otherwise.
        """
        pass


class ToolProvider(ABC):
    """Defines an abstract interface for tool providers.

    This abstract base class (ABC) outlines the contract for creating tool
    providers that can be integrated into the Tinel framework. Each tool
_provider
    is responsible for defining its name, description, input schema, and
    execution logic.
    """

    @abstractmethod
    def get_tool_name(self) -> str:
        """Gets the name of the tool.

        Returns:
            A string representing the unique name of the tool.
        """
        pass

    @abstractmethod
    def get_tool_description(self) -> str:
        """Gets the description of the tool.

        Returns:
            A string providing a brief description of what the tool does.
        """
        pass

    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Gets the input schema for the tool.

        Returns:
            A dictionary representing the JSON schema for the tool's input
            parameters.
        """
        pass

    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the tool with the given parameters.

        Args:
            parameters: A dictionary of parameters that conform to the tool's
                        input schema.

        Returns:
            A dictionary containing the result of the tool's execution.
        """
        pass
