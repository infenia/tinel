#!/usr/bin/env python3
"""Base tool provider implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from ..interfaces import ToolProvider


class BaseToolProvider(ToolProvider):
    """Base implementation for tool providers."""
    
    def __init__(self, name: str, description: str):
        """Initialize base tool provider.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self._name = name
        self._description = description
    
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        return self._name
    
    def get_tool_description(self) -> str:
        """Get the description of the tool."""
        return self._description
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass