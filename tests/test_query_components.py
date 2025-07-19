#!/usr/bin/env python3
"""Tests for query processing components.

Copyright 2024 Infenia Private Limited

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
from unittest.mock import patch

from infenix.diagnostics.query_components import (
    QueryNormalizer,
    IntentClassifier,
    EntityExtractor,
    DefaultToolRouter
)


class TestQueryNormalizer(unittest.TestCase):
    """Test cases for QueryNormalizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = QueryNormalizer()
    
    def test_normalize_basic(self):
        """Test basic normalization."""
        result = self.normalizer.normalize("  HELLO WORLD  ")
        self.assertEqual(result, "hello world")
    
    def test_normalize_contractions(self):
        """Test contraction expansion."""
        result = self.normalizer.normalize("What's the CPU info?")
        self.assertEqual(result, "what is the cpu info?")
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        result = self.normalizer.normalize("show   me    the    hardware")
        self.assertEqual(result, "show me the hardware")


class TestIntentClassifier(unittest.TestCase):
    """Test cases for IntentClassifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = IntentClassifier()
    
    def test_classify_hardware_info(self):
        """Test hardware info intent classification."""
        intent, confidence = self.classifier.classify("show me cpu information")
        self.assertEqual(intent, "hardware_info")
        self.assertGreater(confidence, 0.5)
    
    def test_classify_diagnostic(self):
        """Test diagnostic intent classification."""
        intent, confidence = self.classifier.classify("diagnose hardware issues")
        self.assertEqual(intent, "hardware_diagnostic")
        self.assertGreater(confidence, 0.5)
    
    def test_classify_unknown(self):
        """Test unknown query classification."""
        intent, confidence = self.classifier.classify("random unrelated text")
        self.assertEqual(intent, "general")
        self.assertEqual(confidence, 0.5)
    
    def test_caching(self):
        """Test that classification results are cached."""
        query = "show me cpu information"
        
        # First call
        result1 = self.classifier.classify(query)
        
        # Second call should use cache
        result2 = self.classifier.classify(query)
        
        self.assertEqual(result1, result2)


class TestEntityExtractor(unittest.TestCase):
    """Test cases for EntityExtractor."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = EntityExtractor()
    
    def test_extract_hardware_components(self):
        """Test hardware component extraction."""
        entities = self.extractor.extract("show me cpu information", "hardware_info")
        self.assertEqual(entities.get('component'), 'cpu')
    
    def test_extract_timeframes(self):
        """Test timeframe extraction."""
        entities = self.extractor.extract("show recent logs", "log_analysis")
        self.assertEqual(entities.get('timeframe'), 'recent')
    
    def test_extract_severities(self):
        """Test severity extraction."""
        entities = self.extractor.extract("show critical errors", "log_analysis")
        self.assertEqual(entities.get('severity'), 'critical')
    
    def test_extract_no_entities(self):
        """Test extraction with no matching entities."""
        entities = self.extractor.extract("general query", "general")
        self.assertEqual(entities, {})


class TestDefaultToolRouter(unittest.TestCase):
    """Test cases for DefaultToolRouter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.router = DefaultToolRouter()
    
    def test_route_hardware_info(self):
        """Test routing for hardware info intent."""
        tools = self.router.route("hardware_info", {})
        self.assertGreater(len(tools), 0)
        self.assertIn('get_hardware_info', [tool['tool'] for tool in tools])
    
    def test_route_with_component(self):
        """Test routing with specific component."""
        tools = self.router.route("hardware_info", {"component": "cpu"})
        tool_names = [tool['tool'] for tool in tools]
        self.assertIn('get_cpu_info', tool_names)
    
    def test_route_unknown_intent(self):
        """Test routing for unknown intent."""
        tools = self.router.route("unknown_intent", {})
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]['tool'], 'diagnose_system')
    
    def test_tool_priorities(self):
        """Test that tools have proper priorities."""
        tools = self.router.route("hardware_info", {})
        for tool in tools:
            self.assertIn('priority', tool)
            self.assertIsInstance(tool['priority'], int)
            self.assertGreater(tool['priority'], 0)


if __name__ == '__main__':
    unittest.main()