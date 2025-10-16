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

import unittest
import json
import xml.etree.ElementTree as ET
from tinel.cli.lshw_formatters import (
    LSHWTextFormatter,
    LSHWJsonFormatter,
    LSHWXmlFormatter,
)

class TestLSHWFormatters(unittest.TestCase):
    def setUp(self):
        self.data = {
            "id": "system",
            "children": [
                {
                    "id": "core",
                    "vendor": "Intel",
                    "children": [
                        {"id": "cpu", "product": "Core i9"},
                        {"id": "memory", "size": "32GiB"},
                    ],
                }
            ],
        }

    def test_lshw_text_formatter(self):
        formatter = LSHWTextFormatter()
        output = formatter.format(self.data)
        self.assertIn("└─system", output)
        self.assertIn("└─core", output)
        self.assertIn("├─cpu", output)
        self.assertIn("└─memory", output)

    def test_lshw_text_formatter_last_attribute(self):
        formatter = LSHWTextFormatter()
        data = {"id": "node", "attr1": "value1", "attr2": "value2"}
        output = formatter.format(data)
        self.assertIn("└─attr2: value2", output)

    def test_lshw_json_formatter(self):
        formatter = LSHWJsonFormatter()
        output = formatter.format(self.data)
        parsed_output = json.loads(output)
        self.assertEqual(parsed_output["id"], "system")
        self.assertEqual(len(parsed_output["children"]), 1)

    def test_lshw_xml_formatter(self):
        formatter = LSHWXmlFormatter()
        output = formatter.format(self.data)
        root = ET.fromstring(output)
        self.assertEqual(root.tag, "node")
        self.assertEqual(root.get("id"), "system")
        self.assertEqual(len(list(root)), 1)

    def test_lshw_xml_formatter_with_none_value(self):
        formatter = LSHWXmlFormatter()
        data = {"id": "node", "attr": None}
        output = formatter.format(data)
        root = ET.fromstring(output)
        self.assertIsNone(root.get("attr"))

if __name__ == "__main__":
    unittest.main()