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
from tinel.cli.lshw_formatters import (
    LSHWJsonFormatter,
    LSHWTextFormatter,
    LSHWXmlFormatter,
)


def test_lshw_text_formatter():
    """Test the LSHWTextFormatter."""
    formatter = LSHWTextFormatter()
    data = {
        "id": "core",
        "class": "system",
        "description": "Test System",
        "children": [
            {
                "id": "cpu",
                "class": "processor",
                "description": "Test CPU",
                "product": "Test CPU Product",
            }
        ],
    }
    output = formatter.format(data)
    expected_output = """
└─core
    ├─class: system
    ├─description: Test System
    └─cpu
        ├─class: processor
        ├─description: Test CPU
        └─product: Test CPU Product
""".strip()
    assert expected_output in output


def test_lshw_json_formatter():
    """Test the LSHWJsonFormatter."""
    formatter = LSHWJsonFormatter()
    data = {
        "id": "core",
        "class": "system",
        "children": [{"id": "cpu", "class": "processor"}],
    }
    output = formatter.format(data)
    parsed_output = json.loads(output)
    assert parsed_output["id"] == "core"
    assert parsed_output["children"][0]["id"] == "cpu"


def test_lshw_xml_formatter():
    """Test the LSHWXmlFormatter."""
    formatter = LSHWXmlFormatter()
    data = {
        "id": "core",
        "class": "system",
        "description": "Test System",
        "children": [
            {
                "id": "cpu",
                "class": "processor",
                "product": "Test CPU",
            }
        ],
    }
    output = formatter.format(data)
    root = ET.fromstring(output)
    assert root.tag == "node"
    assert root.attrib["id"] == "core"
    assert root.attrib["description"] == "Test System"
    cpu_node = root.find("node")
    assert cpu_node is not None
    assert cpu_node.attrib["id"] == "cpu"
    assert cpu_node.attrib["product"] == "Test CPU"