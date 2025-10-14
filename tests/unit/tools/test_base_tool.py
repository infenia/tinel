#!/usr/bin/env python3
"""
Unit tests for the BaseToolProvider.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from tinel.tools.base import BaseToolProvider


class ConcreteToolProvider(BaseToolProvider):
    def execute(self, parameters):
        return {"status": "success"}


class TestBaseToolProvider:
    def test_base_tool_provider_methods(self):
        """Test the methods of the BaseToolProvider."""
        tool_name = "test_tool"
        tool_description = "A test tool."
        tool = ConcreteToolProvider(name=tool_name, description=tool_description)

        assert tool.get_tool_name() == tool_name
        assert tool.get_tool_description() == tool_description
        assert tool.get_input_schema() == {
            "type": "object",
            "properties": {},
            "required": [],
        }
