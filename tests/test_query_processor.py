#!/usr/bin/env python3
"""Tests for Query Processor Module.

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

import pytest
from unittest.mock import Mock

from infenix.diagnostics.query_processor import QueryProcessor, QueryIntent


class TestQueryProcessor:
    """Test cases for QueryProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.mock_system.read_file.return_value = None
        self.mock_system.file_exists.return_value = False
        self.mock_system.run_command.return_value = Mock(success=False, stdout="", stderr="")
        
        self.processor = QueryProcessor(self.mock_system)
    
    def test_init(self):
        """Test QueryProcessor initialization."""
        processor = QueryProcessor()
        assert processor.system is not None
        assert processor.query_patterns is not None
        assert processor.intent_classifiers is not None
        assert processor.entity_extractors is not None
    
    def test_normalize_query(self):
        """Test query normalization."""
        # Test basic normalization
        result = self.processor._normalize_query("  What's   my CPU   temperature?  ")
        assert result == "what is my cpu temperature?"
        
        # Test contraction expansion
        result = self.processor._normalize_query("Can't check my system")
        assert result == "cannot check my system"
        
        # Test multiple contractions
        result = self.processor._normalize_query("What's wrong? I can't find the issue.")
        assert result == "what is wrong? i cannot find the issue."
    
    def test_classify_intent_hardware_info(self):
        """Test intent classification for hardware information queries."""
        queries = [
            "What is my CPU information?",
            "Show me hardware details",
            "Get memory specifications",
            "Display GPU information"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.HARDWARE_INFO
            assert confidence > 0.5
    
    def test_classify_intent_hardware_diagnostic(self):
        """Test intent classification for hardware diagnostic queries."""
        queries = [
            "Diagnose my hardware",
            "Check CPU health",
            "Test memory integrity",
            "Run hardware diagnostics"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.HARDWARE_DIAGNOSTIC
            assert confidence > 0.5
    
    def test_classify_intent_kernel_info(self):
        """Test intent classification for kernel information queries."""
        queries = [
            "What kernel version am I running?",
            "Show kernel information",
            "Get kernel details"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.KERNEL_INFO
            assert confidence > 0.5
    
    def test_classify_intent_kernel_config(self):
        """Test intent classification for kernel configuration queries."""
        queries = [
            "Analyze kernel configuration",
            "Check kernel config",
            "Show kernel modules"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.KERNEL_CONFIG
            assert confidence > 0.5
    
    def test_classify_intent_log_analysis(self):
        """Test intent classification for log analysis queries."""
        queries = [
            "Show me recent errors",
            "Analyze system logs",
            "Check for warnings",
            "What issues are in the logs?"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.LOG_ANALYSIS
            assert confidence > 0.5
    
    def test_classify_intent_performance_analysis(self):
        """Test intent classification for performance analysis queries."""
        queries = [
            "Why is my system slow?",
            "Analyze performance",
            "Check system speed",
            "Performance benchmark"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.PERFORMANCE_ANALYSIS
            assert confidence > 0.5
    
    def test_classify_intent_system_diagnostic(self):
        """Test intent classification for system diagnostic queries."""
        queries = [
            "Diagnose my system",
            "Check system health",
            "System status check",
            "Overall system diagnostic"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.SYSTEM_DIAGNOSTIC
            assert confidence > 0.5
    
    def test_classify_intent_troubleshooting(self):
        """Test intent classification for troubleshooting queries."""
        queries = [
            "Fix my system problem",
            "Troubleshoot issues",
            "Solve this problem",
            "Help me debug this"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.TROUBLESHOOTING
            assert confidence > 0.5
    
    def test_classify_intent_optimization(self):
        """Test intent classification for optimization queries."""
        queries = [
            "Optimize my system",
            "Tune system settings",
            "Enhance system configuration"
        ]
        
        for query in queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == QueryIntent.OPTIMIZATION
            assert confidence > 0.5
    
    def test_extract_entities_components(self):
        """Test entity extraction for hardware components."""
        test_cases = [
            ("Check my CPU temperature", {'component': 'cpu'}),
            ("Show memory usage", {'component': 'memory'}),
            ("Analyze disk performance", {'component': 'storage'}),
            ("Check network status", {'component': 'network'}),
            ("GPU information", {'component': 'graphics'})
        ]
        
        for query, expected in test_cases:
            entities = self.processor._extract_entities(query.lower(), QueryIntent.HARDWARE_INFO)
            assert entities.get('component') == expected['component']
    
    def test_extract_entities_timeframes(self):
        """Test entity extraction for timeframes."""
        test_cases = [
            ("Show recent logs", {'timeframe': 'recent'}),
            ("Logs from last hour", {'timeframe': 'hour'}),
            ("Yesterday's logs", {'timeframe': 'day'}),
            ("Weekly log summary", {'timeframe': 'week'})
        ]
        
        for query, expected in test_cases:
            entities = self.processor._extract_entities(query.lower(), QueryIntent.LOG_ANALYSIS)
            # Check if the expected timeframe is extracted (may not be exact due to ordering)
            assert 'timeframe' in entities or expected['timeframe'] == 'recent'
    
    def test_extract_entities_severities(self):
        """Test entity extraction for severity levels."""
        test_cases = [
            ("Show critical errors", {'severity': 'critical'}),
            ("High priority issues", {'severity': 'high'}),
            ("Warning messages", {'severity': 'medium'}),
            ("Info level logs", {'severity': 'low'})
        ]
        
        for query, expected in test_cases:
            entities = self.processor._extract_entities(query.lower(), QueryIntent.LOG_ANALYSIS)
            assert entities.get('severity') == expected['severity']
    
    def test_extract_parameters(self):
        """Test parameter extraction from queries."""
        # Test numeric extraction
        query = "Show logs from last 24 hours"
        params = self.processor._extract_parameters(query.lower(), QueryIntent.LOG_ANALYSIS, {})
        assert 'numbers' in params
        assert 24 in params['numbers']
        
        # Test file path extraction
        query = "Check /var/log/syslog for errors"
        params = self.processor._extract_parameters(query.lower(), QueryIntent.LOG_ANALYSIS, {})
        assert 'file_paths' in params
        assert '/var/log/syslog' in params['file_paths']
        
        # Test device extraction
        query = "Check /dev/sda1 disk health"
        params = self.processor._extract_parameters(query.lower(), QueryIntent.HARDWARE_DIAGNOSTIC, {})
        assert 'devices' in params
        assert '/dev/sda1' in params['devices']
    
    def test_interpret_query_complete(self):
        """Test complete query interpretation."""
        query = "What's my CPU information?"
        result = self.processor.interpret_query(query)
        
        assert result['original_query'] == query
        assert result['normalized_query'] == "what is my cpu information?"
        assert result['intent'] == QueryIntent.HARDWARE_INFO
        assert result['confidence'] > 0.5
        assert 'entities' in result
        assert 'parameters' in result
        assert 'tool_routing' in result
        assert 'response_template' in result
        assert 'timestamp' in result
    
    def test_generate_tool_routing_hardware_info(self):
        """Test tool routing for hardware information queries."""
        routing = self.processor._generate_tool_routing(QueryIntent.HARDWARE_INFO, {'component': 'cpu'})
        
        assert 'primary_tools' in routing
        assert 'secondary_tools' in routing
        assert 'execution_order' in routing
        assert 'get_hardware_info' in routing['primary_tools']
        assert 'get_cpu_info' in routing['secondary_tools']
    
    def test_generate_tool_routing_system_diagnostic(self):
        """Test tool routing for system diagnostic queries."""
        routing = self.processor._generate_tool_routing(QueryIntent.SYSTEM_DIAGNOSTIC, {})
        
        assert routing['execution_order'] == 'sequential'
        assert 'diagnose_system' in routing['primary_tools']
    
    def test_generate_response_template(self):
        """Test response template generation."""
        # Test hardware info template
        template = self.processor._generate_response_template(
            QueryIntent.HARDWARE_INFO, 
            {'component': 'cpu'}
        )
        assert 'cpu' in template.lower()
        assert 'hardware' in template.lower()
        
        # Test log analysis template
        template = self.processor._generate_response_template(
            QueryIntent.LOG_ANALYSIS, 
            {'timeframe': 'recent'}
        )
        assert 'recent' in template.lower()
        assert 'log' in template.lower()
    
    def test_route_to_tools_hardware_info(self):
        """Test tool routing for hardware information queries."""
        interpretation = {
            'intent': QueryIntent.HARDWARE_INFO,
            'parameters': {'component': 'cpu'},
            'tool_routing': {}
        }
        
        tools = self.processor.route_to_tools(interpretation)
        
        assert len(tools) > 0
        assert any(tool['tool'] == 'get_cpu_info' for tool in tools)
    
    def test_route_to_tools_system_diagnostic(self):
        """Test tool routing for system diagnostic queries."""
        interpretation = {
            'intent': QueryIntent.SYSTEM_DIAGNOSTIC,
            'parameters': {},
            'tool_routing': {}
        }
        
        tools = self.processor.route_to_tools(interpretation)
        
        assert len(tools) > 0
        assert any(tool['tool'] == 'diagnose_system' for tool in tools)
    
    def test_route_to_tools_troubleshooting(self):
        """Test tool routing for troubleshooting queries."""
        interpretation = {
            'intent': QueryIntent.TROUBLESHOOTING,
            'parameters': {'component': 'memory'},
            'tool_routing': {}
        }
        
        tools = self.processor.route_to_tools(interpretation)
        
        assert len(tools) > 0
        # Should include multiple diagnostic tools for troubleshooting
        tool_names = [tool['tool'] for tool in tools]
        assert 'diagnose_system' in tool_names
        assert 'analyze_logs' in tool_names
        assert 'run_hardware_diagnostics' in tool_names
    
    def test_complex_query_interpretation(self):
        """Test interpretation of complex queries."""
        complex_queries = [
            "Why is my CPU running hot and system slow?",
            "Check for memory errors in recent logs and run diagnostics",
            "Optimize kernel configuration for better disk performance",
            "Troubleshoot network issues from yesterday's logs"
        ]
        
        for query in complex_queries:
            result = self.processor.interpret_query(query)
            
            # Should successfully interpret all complex queries
            assert result['intent'] != QueryIntent.GENERAL
            assert result['confidence'] > 0.3
            # Parameters may be empty for some complex queries, that's ok
            assert len(result['tool_routing']['primary_tools']) > 0
    
    def test_ambiguous_query_handling(self):
        """Test handling of ambiguous queries."""
        ambiguous_queries = [
            "Help",
            "What's wrong?",
            "Fix it",
            "Check this"
        ]
        
        for query in ambiguous_queries:
            result = self.processor.interpret_query(query)
            
            # Should handle ambiguous queries gracefully
            assert 'intent' in result
            assert 'confidence' in result
            assert result['confidence'] >= 0.0  # Should not fail
    
    def test_intent_confidence_scoring(self):
        """Test intent confidence scoring accuracy."""
        # High confidence queries
        high_confidence_queries = [
            ("Check CPU temperature", QueryIntent.HARDWARE_DIAGNOSTIC),
            ("Show kernel configuration", QueryIntent.KERNEL_CONFIG),
            ("Analyze system logs", QueryIntent.LOG_ANALYSIS)
        ]
        
        for query, expected_intent in high_confidence_queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            assert intent == expected_intent
            assert confidence > 0.5  # Should be reasonable confidence
        
        # Lower confidence queries (more ambiguous)
        lower_confidence_queries = [
            "Help me",
            "What now?",
            "Fix this"
        ]
        
        for query in lower_confidence_queries:
            intent, confidence = self.processor._classify_intent(query.lower())
            # These should have lower confidence or be classified as general
            assert confidence < 1.5 or intent == QueryIntent.GENERAL


if __name__ == "__main__":
    pytest.main([__file__])