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

import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


class LSHWTextFormatter:
    """Formats hardware information in a text format similar to lshw."""

    def format(self, data: Dict[str, Any]) -> str:
        """Formats the data into a tree-like text structure."""
        output = []
        self._format_node(data, output, "", True)
        return "\n".join(output)

    def _format_node(
        self, node: Dict[str, Any], output: List[str], prefix: str, is_last: bool
    ):
        """Recursively formats a node in the hardware tree."""
        connector = "└─" if is_last else "├─"
        node_id = node.get("id", "node")
        output.append(f"{prefix}{connector}{node_id}")

        child_prefix = prefix + ("    " if is_last else "│   ")

        # Format attributes
        attributes = {
            k: v
            for k, v in node.items()
            if k not in ["id", "children"] and v is not None
        }
        attr_items = list(attributes.items())
        for i, (key, value) in enumerate(attr_items):
            is_last_attr = i == (len(attr_items) - 1) and not node.get("children")
            attr_connector = "└─" if is_last_attr else "├─"
            output.append(f"{child_prefix}{attr_connector}{key}: {value}")

        # Format children
        if "children" in node and node["children"]:
            for i, child in enumerate(node["children"]):
                is_last_child = i == (len(node["children"]) - 1)
                self._format_node(child, output, child_prefix, is_last_child)


class LSHWJsonFormatter:
    """Formats hardware information in a JSON format similar to lshw."""

    def format(self, data: Dict[str, Any]) -> str:
        """Formats the data into a JSON string."""
        return json.dumps(data, indent=2)


class LSHWXmlFormatter:
    """Formats hardware information in an XML format similar to lshw."""

    def format(self, data: Dict[str, Any]) -> str:
        """Formats the data into an XML string."""
        root = self._build_xml_node("node", data)
        return ET.tostring(root, encoding="unicode")

    def _build_xml_node(self, tag_name: str, node_data: Dict[str, Any]) -> ET.Element:
        """Recursively builds an XML node from a dictionary."""
        # Use "node" as the tag for all elements, and store the original class in an attribute
        elem = ET.Element("node")
        for key, value in node_data.items():
            if key == "children":
                continue
            if value is not None:
                elem.set(key, str(value))

        if "children" in node_data:
            for child_data in node_data["children"]:
                elem.append(self._build_xml_node("node", child_data))

        return elem