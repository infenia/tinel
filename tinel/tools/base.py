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

"""Base tool provider implementation."""

from abc import abstractmethod
from typing import Any, Dict

from ..interfaces import ToolProvider


class BaseToolProvider(ToolProvider):
    """Base implementation for tool providers."""

    def __init__(self, name: str, description: str, feature_name: str = None):
        """Initialize base tool provider.

        Args:
            name: Tool name
            description: Tool description
            feature_name: Name of the feature flag that controls access to this tool
        """
        self._name = name
        self._description = description
        self.feature_name = feature_name

    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return self._name

    def get_tool_description(self) -> str:
        """Get the description of the tool."""
        return self._description

    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
