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

"""This module defines the base class for all tool providers.

It includes the `BaseToolProvider` abstract base class, which provides a
common framework and shared functionality for all tool providers. This
ensures a consistent structure and simplifies the implementation of new tools.
"""

from abc import abstractmethod
from typing import Any, Dict, Optional

from ..interfaces import ToolProvider


class BaseToolProvider(ToolProvider):
    """A base implementation for tool providers.

    This abstract base class provides a common foundation for all tool
    providers, including a name, description, and an optional feature flag.

    Args:
        name: The name of the tool.
        description: A brief description of what the tool does.
        feature_name: An optional name of the feature flag that controls
                      access to this tool.
    """

    def __init__(self, name: str, description: str, feature_name: Optional[str] = None):
        """Initializes the BaseToolProvider.

        Args:
            name: The name of the tool.
            description: The description of the tool.
            feature_name: The name of the feature flag.
        """
        self._name = name
        self._description = description
        self.feature_name = feature_name

    def get_tool_name(self) -> str:
        """Gets the name of the tool.

        Returns:
            The name of the tool as a string.
        """
        return self._name

    def get_tool_description(self) -> str:
        """Gets the description of the tool.

        Returns:
            The description of the tool as a string.
        """
        return self._description

    def get_input_schema(self) -> Dict[str, Any]:
        """Gets the input schema for the tool.

        By default, this returns a schema for a tool that takes no parameters.
        Subclasses should override this method to define their own input schemas.

        Returns:
            A dictionary representing the JSON schema for the tool's input.
        """
        return {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the tool with the given parameters.

        This is an abstract method that must be implemented by all subclasses.
        It contains the core logic for the tool.

        Args:
            parameters: A dictionary of parameters for the tool.

        Returns:
            A dictionary containing the result of the tool's execution.
        """
        pass
