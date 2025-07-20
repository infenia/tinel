#!/usr/bin/env python3
"""Tests for AI diagnostics tools in MCP server.

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
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from infenix.tools.diagnostics_tools import (
    SystemDiagnosticsToolProvider,
    QueryProcessorToolProvider,
    RecommendationGeneratorToolProvider,
    HardwareDiagnosticsToolProvider,
)
from infenix.interfaces import Diagnostic, HardwareInfo, KernelConfig, LogAnalysis
from infenix.system import LinuxSystemInterface


class TestSystemDiagnosticsToolProvider:
    """Test cases for SystemDiagnosticsToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = SystemDiagnosticsToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "diagnose_system"
    
    def test_tool_description(self):
        """Test tool description."""
        description = self.provider.get_tool_description()
        assert "comprehensive" in description.lower()
        assert "diagnostics" in description.lower()
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert schema["type"] == "object"
        assert "include_hardware" in schema["properties"]
        assert "include_kernel" in schema["properties"]
        assert "include_logs" in schema["properties"]
        assert "generate_recommendations" in schema["properties"]
    
    @patch('infenix.tools.diagnostics_tools.DiagnosticsEngine')
    def test_execute_success(self, mock_engine_class):
        """Test successful execution."""
        # Mock diagnostics engine
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        # Mock diagnostic result
        mock_diagnostic = Mock(spec=Diagnostic)
        mock_diagnostic.explanation = "System is running well"
        mock_diagnostic.hardware = Mock()
        mock_diagnostic.kernel_config = Mock()
        mock_diagnostic.log_analysis = Mock()
        mock_diagnostic.recommendations = {"hardware": []}
        
        mock_engine._gather_hardware_info.return_value = mock_diagnostic.hardware
        mock_engine._parse_kernel_config.return_value = mock_diagnostic.kernel_config
        mock_engine._analyze_logs.return_value = mock_diagnostic.log_analysis
        mock_engine.diagnose_system.return_value = mock_diagnostic
        
        result = self.provider.execute({
            "include_hardware": True,
            "include_kernel": True,
            "include_logs": True
        })
        
        assert result["success"] is True
        assert "diagnostic_summary" in result
        assert "hardware_analysis" in result
        assert "kernel_analysis" in result
        assert "log_analysis" in result
        assert "recommendations" in result
    
    @patch('infenix.tools.diagnostics_tools.DiagnosticsEngine')
    def test_execute_with_defaults(self, mock_engine_class):
        """Test execution with default parameters."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        
        mock_diagnostic = Mock(spec=Diagnostic)
        mock_diagnostic.explanation = "System analysis complete"
        mock_diagnostic.hardware = None
        mock_diagnostic.kernel_config = None
        mock_diagnostic.log_analysis = None
        mock_diagnostic.recommendations = {}
        
        mock_engine.diagnose_system.return_value = mock_diagnostic
        
        result = self.provider.execute({})
        
        assert result["success"] is True
        assert result["analysis_metadata"]["included_hardware"] is True
        assert result["analysis_metadata"]["included_kernel"] is True
        assert result["analysis_metadata"]["included_logs"] is True
    
    @patch('infenix.tools.diagnostics_tools.DiagnosticsEngine')
    def test_execute_error_handling(self, mock_engine_class):
        """Test error handling."""
        mock_engine_class.side_effect = Exception("Engine error")
        
        result = self.provider.execute({"include_hardware": True})
        
        assert result["success"] is False
        assert "error" in result
        assert result["hardware_analysis"] is None
    
    def test_serialize_hardware_info(self):
        """Test hardware info serialization."""
        mock_hardware = Mock()
        mock_hardware.cpu = {"model": "Test CPU"}
        mock_hardware.memory = {"total": "8GB"}
        
        result = self.provider._serialize_hardware_info(mock_hardware)
        
        assert "cpu" in result
        assert "memory" in result
        assert result["cpu"] == {"model": "Test CPU"}
    
    def test_serialize_kernel_config(self):
        """Test kernel config serialization."""
        mock_kernel = Mock()
        mock_kernel.version = "5.15.0"
        mock_kernel.options = {"CONFIG_SMP": Mock()}
        mock_kernel.analysis = {"security": "good"}
        
        result = self.provider._serialize_kernel_config(mock_kernel)
        
        assert result["version"] == "5.15.0"
        assert result["options_count"] == 1
        assert result["analysis"] == {"security": "good"}


class TestQueryProcessorToolProvider:
    """Test cases for QueryProcessorToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = QueryProcessorToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "process_natural_language_query"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "query" in schema["required"]
        assert "include_tool_routing" in schema["properties"]
        assert "execute_tools" in schema["properties"]
    
    @patch('infenix.tools.diagnostics_tools.QueryProcessor')
    def test_execute_success(self, mock_processor_class):
        """Test successful query processing."""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock interpretation result
        mock_interpretation = {
            "original_query": "What is my CPU temperature?",
            "normalized_query": "what is my cpu temperature",
            "intent": "hardware_info",
            "confidence": 0.9,
            "entities": {"component": "cpu"},
            "parameters": {"component": "cpu"},
            "response_template": "Checking CPU temperature...",
            "timestamp": datetime.now().isoformat()
        }
        
        mock_processor.interpret_query.return_value = mock_interpretation
        mock_processor.route_to_tools.return_value = [
            {"tool": "get_cpu_info", "priority": 1}
        ]
        
        result = self.provider.execute({
            "query": "What is my CPU temperature?",
            "include_tool_routing": True
        })
        
        assert result["success"] is True
        assert result["interpretation"]["intent"] == "hardware_info"
        assert result["confidence"] == 0.9
        assert len(result["tool_routing"]) == 1
    
    @patch('infenix.tools.diagnostics_tools.QueryProcessor')
    def test_execute_empty_query(self, mock_processor_class):
        """Test execution with empty query."""
        result = self.provider.execute({"query": ""})
        
        assert result["success"] is False
        assert "empty" in result["error"].lower()
    
    @patch('infenix.tools.diagnostics_tools.QueryProcessor')
    def test_execute_with_tool_execution(self, mock_processor_class):
        """Test execution with tool execution enabled."""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        mock_interpretation = {
            "intent": "hardware_info",
            "confidence": 0.8,
            "response_template": "Analyzing hardware..."
        }
        
        mock_processor.interpret_query.return_value = mock_interpretation
        mock_processor.route_to_tools.return_value = [
            {"tool": "get_cpu_info", "parameters": {}}
        ]
        
        result = self.provider.execute({
            "query": "Show me CPU info",
            "execute_tools": True
        })
        
        assert result["success"] is True
        assert len(result["execution_results"]) > 0
        assert result["execution_results"][0]["tool"] == "get_cpu_info"
    
    def test_execute_recommended_tools(self):
        """Test tool execution simulation."""
        tool_routing = [
            {"tool": "get_cpu_info", "parameters": {"component": "cpu"}},
            {"tool": "get_memory_info", "parameters": {}}
        ]
        
        results = self.provider._execute_recommended_tools(tool_routing)
        
        assert len(results) == 2
        assert results[0]["tool"] == "get_cpu_info"
        assert results[0]["status"] == "simulated"


class TestRecommendationGeneratorToolProvider:
    """Test cases for RecommendationGeneratorToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = RecommendationGeneratorToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "generate_recommendations"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "focus_areas" in schema["properties"]
        assert "priority_filter" in schema["properties"]
        assert "max_recommendations" in schema["properties"]
        
        # Check enum values
        focus_enum = schema["properties"]["focus_areas"]["items"]["enum"]
        assert "hardware" in focus_enum
        assert "security" in focus_enum
        assert "all" in focus_enum
    
    @patch('infenix.tools.diagnostics_tools.RecommendationGenerator')
    @patch('infenix.tools.diagnostics_tools.DiagnosticsEngine')
    def test_execute_success(self, mock_engine_class, mock_generator_class):
        """Test successful recommendation generation."""
        # Mock diagnostics engine
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_diagnostic = Mock(spec=Diagnostic)
        mock_engine.diagnose_system.return_value = mock_diagnostic
        
        # Mock recommendation generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        mock_recommendations = {
            "recommendations": {
                "hardware": [{"priority": "high", "action": "Check CPU temperature"}],
                "security": [{"priority": "medium", "action": "Update kernel"}]
            },
            "prioritized": [
                {"priority": "high", "component": "cpu", "action": "Check temperature"},
                {"priority": "medium", "component": "kernel", "action": "Update"}
            ],
            "summary": "2 recommendations generated",
            "statistics": {"total": 2, "high": 1, "medium": 1}
        }
        
        mock_generator.generate_recommendations.return_value = mock_recommendations
        
        result = self.provider.execute({
            "focus_areas": ["hardware", "security"],
            "priority_filter": ["high", "medium"],
            "max_recommendations": 10
        })
        
        assert result["success"] is True
        assert "recommendations" in result
        assert len(result["recommendations"]["prioritized"]) == 2
    
    @patch('infenix.tools.diagnostics_tools.RecommendationGenerator')
    @patch('infenix.tools.diagnostics_tools.DiagnosticsEngine')
    def test_execute_with_filtering(self, mock_engine_class, mock_generator_class):
        """Test execution with recommendation filtering."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.diagnose_system.return_value = Mock()
        
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        mock_recommendations = {
            "recommendations": {
                "hardware": [{"priority": "critical"}],
                "security": [{"priority": "high"}],
                "performance": [{"priority": "low"}]
            },
            "prioritized": [
                {"priority": "critical", "component": "cpu"},
                {"priority": "high", "component": "kernel"},
                {"priority": "low", "component": "disk"}
            ]
        }
        
        mock_generator.generate_recommendations.return_value = mock_recommendations
        
        result = self.provider.execute({
            "focus_areas": ["hardware"],
            "priority_filter": ["critical", "high"],
            "max_recommendations": 5
        })
        
        assert result["success"] is True
        # Should only include hardware recommendations
        assert "hardware" in result["recommendations"]["recommendations"]
        assert "performance" not in result["recommendations"]["recommendations"]
    
    def test_filter_recommendations(self):
        """Test recommendation filtering logic."""
        recommendations_result = {
            "recommendations": {
                "hardware": [{"priority": "high"}],
                "security": [{"priority": "medium"}],
                "performance": [{"priority": "low"}]
            },
            "prioritized": [
                {"priority": "high", "component": "cpu"},
                {"priority": "medium", "component": "kernel"},
                {"priority": "low", "component": "disk"}
            ]
        }
        
        filtered = self.provider._filter_recommendations(
            recommendations_result,
            ["hardware"],
            ["high", "medium"],
            2
        )
        
        # Should only include hardware recommendations
        assert "hardware" in filtered["recommendations"]
        assert "performance" not in filtered["recommendations"]
        
        # Should filter by priority and limit count
        assert len(filtered["prioritized"]) == 2
        priorities = [rec["priority"] for rec in filtered["prioritized"]]
        assert "low" not in priorities
    
    def test_generate_implementation_guides(self):
        """Test implementation guide generation."""
        recommendations = [
            {"component": "cpu", "action": "Check CPU temperature"},
            {"component": "memory", "action": "Reduce memory usage"}
        ]
        
        guides = self.provider._generate_implementation_guides(recommendations)
        
        assert len(guides) == 2
        assert guides[0]["component"] == "cpu"
        assert "steps" in guides[0]
        assert "estimated_time" in guides[0]
        assert "difficulty" in guides[0]
    
    def test_get_implementation_steps(self):
        """Test implementation steps generation."""
        steps = self.provider._get_implementation_steps("cpu", "Check CPU temperature")
        
        assert len(steps) > 0
        assert any("temperature" in step.lower() for step in steps)
        assert any("sensors" in step.lower() for step in steps)


class TestHardwareDiagnosticsToolProvider:
    """Test cases for HardwareDiagnosticsToolProvider."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock(spec=LinuxSystemInterface)
        self.provider = HardwareDiagnosticsToolProvider(self.mock_system)
    
    def test_tool_name(self):
        """Test tool name."""
        assert self.provider.get_tool_name() == "run_hardware_diagnostics"
    
    def test_input_schema(self):
        """Test input schema structure."""
        schema = self.provider.get_input_schema()
        assert "components" in schema["properties"]
        assert "include_temperature" in schema["properties"]
        assert "include_performance" in schema["properties"]
        assert "include_health" in schema["properties"]
        
        # Check component enum values
        component_enum = schema["properties"]["components"]["items"]["enum"]
        assert "all" in component_enum
        assert "cpu" in component_enum
        assert "memory" in component_enum
    
    @patch('infenix.tools.diagnostics_tools.HardwareDiagnostics')
    def test_execute_success(self, mock_diagnostics_class):
        """Test successful hardware diagnostics execution."""
        mock_diagnostics = Mock()
        mock_diagnostics_class.return_value = mock_diagnostics
        
        mock_results = {
            "cpu": {
                "temperature": 45.0,
                "performance_metrics": {"load": 0.3},
                "health_status": "good"
            },
            "memory": {
                "usage_percent": 60,
                "performance_metrics": {"speed": "DDR4-3200"},
                "health_status": "good"
            }
        }
        
        mock_diagnostics.run_comprehensive_diagnostics.return_value = mock_results
        
        result = self.provider.execute({
            "components": ["cpu", "memory"],
            "include_temperature": True,
            "include_performance": True,
            "include_health": True
        })
        
        assert result["success"] is True
        assert "cpu" in result["hardware_diagnostics"]
        assert "memory" in result["hardware_diagnostics"]
        assert result["hardware_diagnostics"]["cpu"]["temperature"] == 45.0
    
    @patch('infenix.tools.diagnostics_tools.HardwareDiagnostics')
    def test_execute_with_filtering(self, mock_diagnostics_class):
        """Test execution with component filtering."""
        mock_diagnostics = Mock()
        mock_diagnostics_class.return_value = mock_diagnostics
        
        mock_results = {
            "cpu": {"temperature": 45.0, "performance_metrics": {}},
            "memory": {"usage_percent": 60, "performance_metrics": {}},
            "storage": {"health_status": "good"}
        }
        
        mock_diagnostics.run_comprehensive_diagnostics.return_value = mock_results
        
        result = self.provider.execute({
            "components": ["cpu"],
            "include_temperature": False,
            "include_performance": False
        })
        
        assert result["success"] is True
        assert "cpu" in result["hardware_diagnostics"]
        assert "memory" not in result["hardware_diagnostics"]
        assert "storage" not in result["hardware_diagnostics"]
    
    def test_remove_temperature_data(self):
        """Test temperature data removal."""
        results = {
            "cpu": {
                "temperature": 45.0,
                "thermal_status": "normal",
                "other_data": "keep"
            }
        }
        
        self.provider._remove_temperature_data(results)
        
        assert "temperature" not in results["cpu"]
        assert "thermal_status" not in results["cpu"]
        assert "other_data" in results["cpu"]
    
    def test_remove_performance_data(self):
        """Test performance data removal."""
        results = {
            "cpu": {
                "performance_metrics": {"load": 0.3},
                "benchmarks": {"score": 1000},
                "other_data": "keep"
            }
        }
        
        self.provider._remove_performance_data(results)
        
        assert "performance_metrics" not in results["cpu"]
        assert "benchmarks" not in results["cpu"]
        assert "other_data" in results["cpu"]
    
    def test_remove_health_data(self):
        """Test health data removal."""
        results = {
            "storage": {
                "health_status": "good",
                "smart_data": {"temperature": 35},
                "other_data": "keep"
            }
        }
        
        self.provider._remove_health_data(results)
        
        assert "health_status" not in results["storage"]
        assert "smart_data" not in results["storage"]
        assert "other_data" in results["storage"]


if __name__ == "__main__":
    pytest.main([__file__])