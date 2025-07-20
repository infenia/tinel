#!/usr/bin/env python3
"""Tests for log analysis tools in MCP server.

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

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from infenix.tools.log_tools import (
    SystemLogsToolProvider,
    LogAnalysisToolProvider,
    LogSummaryToolProvider,
    LogEntryAnalysisToolProvider,
    HardwareLogPatternToolProvider,
    KernelLogPatternToolProvider,
)
from infenix.interfaces import LogEntry, LogAnalysis
from infenix.system import LinuxSystemInterface


class TestSystemLogsToolProvider:
    """Test cases for SystemLogsToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = SystemLogsToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "get_system_logs"
    
    def test_tool_description(self):
        """Test tool description."""
        description = self.provider.get_tool_description()
        assert "system logs" in description.lower()
        assert "journald" in description.lower()
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert schema["type"] == "object"
        assert "sources" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "since" in schema["properties"]
    
    @patch('infenix.tools.log_tools.LogParser')
    def test_execute_success(self, mock_parser_class):
        """Test successful execution."""
        # Mock parser and entries
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        
        mock_entries = [
            LogEntry(
                timestamp=datetime.now(),
                facility="kernel",
                severity="error",
                message="Test error message",
                source="kernel"
            )
        ]
        mock_parser.parse_logs.return_value = mock_entries
        
        # Execute tool
        result = self.provider.execute({
            "sources": ["journald"],
            "limit": 100,
            "since": "1 hour ago"
        })
        
        # Verify result
        assert result["success"] is True
        assert result["total_entries"] == 1
        assert len(result["entries"]) == 1
        assert result["entries"][0]["facility"] == "kernel"
        assert result["entries"][0]["severity"] == "error"
    
    @patch('infenix.tools.log_tools.LogParser')
    def test_execute_with_defaults(self, mock_parser_class):
        """Test execution with default parameters."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_logs.return_value = []
        
        result = self.provider.execute({})
        
        assert result["success"] is True
        assert result["sources_parsed"] == ["journald", "syslog", "kern.log"]
    
    @patch('infenix.tools.log_tools.LogParser')
    def test_execute_error_handling(self, mock_parser_class):
        """Test error handling."""
        mock_parser_class.side_effect = Exception("Parser error")
        
        result = self.provider.execute({"sources": ["journald"]})
        
        assert result["success"] is False
        assert "error" in result
        assert result["entries"] == []
    
    def test_parse_time_filter(self):
        """Test time filter parsing."""
        # Test hours
        result = self.provider._parse_time_filter("2 hours ago")
        assert result is not None
        assert isinstance(result, datetime)
        
        # Test days
        result = self.provider._parse_time_filter("1 day ago")
        assert result is not None
        
        # Test invalid format
        result = self.provider._parse_time_filter("invalid")
        assert result is None


class TestLogAnalysisToolProvider:
    """Test cases for LogAnalysisToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = LogAnalysisToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "analyze_logs"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "analysis_type" in schema["properties"]
        assert "time_window" in schema["properties"]
        
        # Check enum values for analysis_type
        analysis_enum = schema["properties"]["analysis_type"]["enum"]
        assert "full" in analysis_enum
        assert "hardware" in analysis_enum
        assert "kernel" in analysis_enum
    
    @patch('infenix.tools.log_tools.LogAnalyzer')
    def test_execute_full_analysis(self, mock_analyzer_class):
        """Test full analysis execution."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock analysis result
        mock_analysis = Mock(spec=LogAnalysis)
        mock_analysis.entries = []
        mock_analysis.patterns = {"hardware": {}, "kernel": {}}
        mock_analysis.issues = {"critical": [], "high": []}
        mock_analysis.summary = {"total_issues": 0}
        mock_analyzer.analyze_logs.return_value = mock_analysis
        mock_analyzer.correlate_hardware_events.return_value = []
        
        result = self.provider.execute({
            "sources": ["journald"],
            "analysis_type": "full"
        })
        
        assert result["success"] is True
        assert result["analysis_type"] == "full"
        assert "correlations" in result
    
    @patch('infenix.tools.log_tools.LogAnalyzer')
    def test_execute_hardware_analysis(self, mock_analyzer_class):
        """Test hardware-specific analysis."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_analysis = Mock(spec=LogAnalysis)
        mock_analysis.entries = []
        mock_analysis.patterns = {
            "hardware": {"cpu_issues": []},
            "kernel": {"panics": []}
        }
        mock_analysis.issues = {}
        mock_analysis.summary = {}
        mock_analyzer.analyze_logs.return_value = mock_analysis
        
        result = self.provider.execute({
            "analysis_type": "hardware"
        })
        
        assert result["success"] is True
        assert "hardware" in result["patterns"]
        assert "kernel" not in result["patterns"]
    
    def test_serialize_patterns(self):
        """Test pattern serialization."""
        patterns = {
            "hardware": {
                "cpu_issues": [{
                    "type": "thermal_throttling",
                    "timestamp": datetime.now(),
                    "severity": "medium"
                }]
            }
        }
        
        result = self.provider._serialize_patterns(patterns)
        
        assert "hardware" in result
        assert "cpu_issues" in result["hardware"]
        assert len(result["hardware"]["cpu_issues"]) == 1
        # Check timestamp is serialized
        assert isinstance(result["hardware"]["cpu_issues"][0]["timestamp"], str)


class TestLogSummaryToolProvider:
    """Test cases for LogSummaryToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = LogSummaryToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "get_log_summary"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "severity_filter" in schema["properties"]
        assert "max_issues" in schema["properties"]
        
        # Check severity filter enum
        severity_enum = schema["properties"]["severity_filter"]["items"]["enum"]
        assert "critical" in severity_enum
        assert "high" in severity_enum
    
    @patch('infenix.tools.log_tools.LogAnalyzer')
    def test_execute_success(self, mock_analyzer_class):
        """Test successful summary generation."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock parser
        mock_parser = Mock()
        mock_analyzer.parser = mock_parser
        mock_parser.parse_logs.return_value = []
        
        # Mock summary
        mock_summary = {
            "total_critical_issues": 2,
            "issues": [
                {
                    "type": "kernel_panic",
                    "severity": "critical",
                    "timestamp": datetime.now(),
                    "description": "Test panic"
                }
            ],
            "statistics": {},
            "recommendations": []
        }
        mock_analyzer.generate_critical_issues_summary.return_value = mock_summary
        
        result = self.provider.execute({
            "severity_filter": ["critical"],
            "max_issues": 10
        })
        
        assert result["success"] is True
        assert result["total_critical_issues"] == 2
        assert len(result["issues"]) == 1
        # Check timestamp serialization
        assert isinstance(result["issues"][0]["timestamp"], str)
    
    @patch('infenix.tools.log_tools.LogAnalyzer')
    def test_execute_with_filtering(self, mock_analyzer_class):
        """Test execution with severity filtering."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_parser = Mock()
        mock_analyzer.parser = mock_parser
        mock_parser.parse_logs.return_value = []
        
        # Mock summary with mixed severity issues
        mock_summary = {
            "issues": [
                {"severity": "critical", "timestamp": datetime.now()},
                {"severity": "high", "timestamp": datetime.now()},
                {"severity": "medium", "timestamp": datetime.now()}
            ]
        }
        mock_analyzer.generate_critical_issues_summary.return_value = mock_summary
        
        result = self.provider.execute({
            "severity_filter": ["critical"],
            "max_issues": 10
        })
        
        # Should only include critical issues
        assert len(result["issues"]) == 1
        assert result["issues"][0]["severity"] == "critical"


class TestLogEntryAnalysisToolProvider:
    """Test cases for LogEntryAnalysisToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = LogEntryAnalysisToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "analyze_log_entry"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "message" in schema["required"]
        assert "timestamp" in schema["properties"]
        assert "facility" in schema["properties"]
    
    @patch('infenix.tools.log_tools.LogAnalyzer')
    def test_execute_success(self, mock_analyzer_class):
        """Test successful log entry analysis."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock analysis result
        mock_analysis = {
            "entry": {
                "timestamp": datetime.now(),
                "facility": "kernel",
                "message": "Test message"
            },
            "classification": {"category": "kernel"},
            "context": {"age_hours": 1},
            "recommendations": ["Check kernel logs"]
        }
        mock_analyzer.analyze_specific_entry.return_value = mock_analysis
        
        result = self.provider.execute({
            "message": "Test kernel error",
            "facility": "kernel",
            "severity": "error"
        })
        
        assert result["success"] is True
        assert "classification" in result
        assert "recommendations" in result
        # Check timestamp serialization
        assert isinstance(result["entry"]["timestamp"], str)
    
    @patch('infenix.tools.log_tools.LogAnalyzer')
    def test_execute_minimal_parameters(self, mock_analyzer_class):
        """Test execution with minimal parameters."""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_specific_entry.return_value = {
            "entry": {"timestamp": datetime.now()},
            "classification": {},
            "context": {},
            "recommendations": []
        }
        
        result = self.provider.execute({
            "message": "Test message"
        })
        
        assert result["success"] is True


class TestHardwareLogPatternToolProvider:
    """Test cases for HardwareLogPatternToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = HardwareLogPatternToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "detect_hardware_patterns"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "hardware_type" in schema["properties"]
        
        # Check hardware type enum
        hardware_enum = schema["properties"]["hardware_type"]["enum"]
        assert "all" in hardware_enum
        assert "cpu" in hardware_enum
        assert "memory" in hardware_enum
    
    @patch('infenix.tools.log_tools.PatternDetector')
    @patch('infenix.tools.log_tools.LogParser')
    def test_execute_all_hardware(self, mock_parser_class, mock_detector_class):
        """Test hardware pattern detection for all hardware types."""
        # Mock parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_logs.return_value = []
        
        # Mock detector
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.detect_hardware_patterns.return_value = {
            "cpu_issues": [{
                "type": "thermal_throttling",
                "timestamp": datetime.now(),
                "severity": "medium"
            }]
        }
        mock_detector.correlate_hardware_events.return_value = []
        
        result = self.provider.execute({
            "hardware_type": "all"
        })
        
        assert result["success"] is True
        assert "patterns" in result
        assert "correlations" in result
        assert result["hardware_type"] == "all"
    
    @patch('infenix.tools.log_tools.PatternDetector')
    @patch('infenix.tools.log_tools.LogParser')
    def test_execute_specific_hardware(self, mock_parser_class, mock_detector_class):
        """Test hardware pattern detection for specific hardware type."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_logs.return_value = []
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.detect_hardware_patterns.return_value = {
            "cpu_issues": [{"type": "test", "timestamp": datetime.now()}],
            "memory_issues": [{"type": "test", "timestamp": datetime.now()}]
        }
        mock_detector.correlate_hardware_events.return_value = []
        
        result = self.provider.execute({
            "hardware_type": "cpu"
        })
        
        assert result["success"] is True
        assert "cpu_issues" in result["patterns"]
        assert "memory_issues" not in result["patterns"]


class TestKernelLogPatternToolProvider:
    """Test cases for KernelLogPatternToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = KernelLogPatternToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "detect_kernel_patterns"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "pattern_type" in schema["properties"]
        assert "severity_threshold" in schema["properties"]
        
        # Check pattern type enum
        pattern_enum = schema["properties"]["pattern_type"]["enum"]
        assert "all" in pattern_enum
        assert "panics" in pattern_enum
        assert "oops" in pattern_enum
    
    @patch('infenix.tools.log_tools.PatternDetector')
    @patch('infenix.tools.log_tools.LogParser')
    def test_execute_all_patterns(self, mock_parser_class, mock_detector_class):
        """Test kernel pattern detection for all pattern types."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_logs.return_value = []
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.detect_kernel_patterns.return_value = {
            "kernel_panics": [{
                "type": "kernel_panic",
                "timestamp": datetime.now(),
                "severity": "critical"
            }],
            "warnings": [{
                "type": "kernel_warning",
                "timestamp": datetime.now(),
                "severity": "low"
            }]
        }
        
        result = self.provider.execute({
            "pattern_type": "all",
            "severity_threshold": "medium"
        })
        
        assert result["success"] is True
        # Should include critical panic but exclude low severity warning
        assert "kernel_panics" in result["patterns"]
        assert len(result["patterns"]["kernel_panics"]) == 1
        assert "warnings" not in result["patterns"]  # Filtered out by severity
    
    @patch('infenix.tools.log_tools.PatternDetector')
    @patch('infenix.tools.log_tools.LogParser')
    def test_execute_specific_pattern(self, mock_parser_class, mock_detector_class):
        """Test kernel pattern detection for specific pattern type."""
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_logs.return_value = []
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.detect_kernel_patterns.return_value = {
            "kernel_panics": [{"type": "panic", "timestamp": datetime.now(), "severity": "critical"}],
            "oops": [{"type": "oops", "timestamp": datetime.now(), "severity": "high"}]
        }
        
        result = self.provider.execute({
            "pattern_type": "kernel_panics"
        })
        
        assert result["success"] is True
        assert "kernel_panics" in result["patterns"]
        assert "oops" not in result["patterns"]


if __name__ == "__main__":
    pytest.main([__file__])