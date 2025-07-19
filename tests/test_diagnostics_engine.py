#!/usr/bin/env python3
"""Tests for Diagnostics Engine Module.

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
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from infenix.diagnostics.diagnostics_engine import DiagnosticsEngine
from infenix.interfaces import (
    HardwareInfo, KernelConfig, LogAnalysis, Diagnostic
)


class TestDiagnosticsEngine:
    """Test cases for DiagnosticsEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        # Mock system interface methods to return None for file reads
        self.mock_system.read_file.return_value = None
        self.mock_system.file_exists.return_value = False
        self.mock_system.run_command.return_value = Mock(success=False, stdout="", stderr="")
        
        self.engine = DiagnosticsEngine(self.mock_system)
        
        # Mock hardware info
        self.mock_hardware = HardwareInfo(
            cpu={
                "model": "Intel Core i7-9700K",
                "cores": 8,
                "threads": 8,
                "frequency_mhz": 3600,
                "features": ["sse", "avx", "avx2"],
                "temperature": 65.0
            },
            memory={
                "total_gb": 16.0,
                "available_gb": 8.0,
                "usage_percent": 50.0
            },
            storage={
                "devices": [
                    {
                        "device": "/dev/sda",
                        "model": "Samsung SSD 970",
                        "size_gb": 500.0,
                        "type": "SSD"
                    }
                ]
            },
            graphics={},
            network={},
            usb_devices={},
            pci_devices={}
        )
        
        # Mock kernel config
        from infenix.interfaces import KernelConfigOption
        self.mock_kernel_config = KernelConfig(
            version="5.15.0",
            options={
                "CONFIG_SMP": KernelConfigOption(
                    name="CONFIG_SMP",
                    value="y",
                    description="Symmetric Multi-Processing support"
                ),
                "CONFIG_PREEMPT": KernelConfigOption(
                    name="CONFIG_PREEMPT",
                    value="n",
                    description="Preemptible Kernel"
                )
            },
            analysis={},
            recommendations={}
        )
        
        # Mock log analysis
        from infenix.interfaces import LogEntry
        self.mock_log_analysis = LogAnalysis(
            entries=[
                LogEntry(
                    timestamp=datetime.now(),
                    facility="kernel",
                    severity="warning",
                    message="USB device disconnected unexpectedly",
                    source="/var/log/kern.log"
                )
            ],
            patterns={},
            issues={
                "usb_issues": [
                    {
                        "severity": "medium",
                        "type": "kernel",
                        "message": "USB device disconnected unexpectedly"
                    }
                ]
            },
            summary={"total_issues": 1, "critical_issues": 0}
        )
    
    def test_init(self):
        """Test DiagnosticsEngine initialization."""
        engine = DiagnosticsEngine()
        assert engine.system is not None
        assert engine.device_analyzer is not None
        assert engine.kernel_config_parser is not None
        assert engine.kernel_config_analyzer is not None
        assert engine.log_parser is not None
        assert engine.log_analyzer is not None
    
    def test_diagnose_system_with_provided_data(self):
        """Test system diagnosis with pre-provided data."""
        diagnostic = self.engine.diagnose_system(
            hardware=self.mock_hardware,
            kernel_config=self.mock_kernel_config,
            log_analysis=self.mock_log_analysis
        )
        
        assert isinstance(diagnostic, Diagnostic)
        assert diagnostic.hardware == self.mock_hardware
        assert diagnostic.kernel_config == self.mock_kernel_config
        assert diagnostic.log_analysis == self.mock_log_analysis
        assert isinstance(diagnostic.recommendations, dict)
        assert isinstance(diagnostic.explanation, str)
        assert len(diagnostic.explanation) > 0
    
    @patch('infenix.diagnostics.diagnostics_engine.DeviceAnalyzer')
    def test_diagnose_system_gather_data(self, mock_device_analyzer):
        """Test system diagnosis with data gathering."""
        # Mock device analyzer
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.get_all_hardware_info.return_value = self.mock_hardware
        mock_device_analyzer.return_value = mock_analyzer_instance
        
        # Mock kernel config parser and log analysis
        with patch.object(self.engine.kernel_config_parser, 'parse_config', return_value=self.mock_kernel_config), \
             patch.object(self.engine.log_parser, 'parse_logs', return_value=[]), \
             patch.object(self.engine.log_analyzer, 'analyze_logs', return_value=self.mock_log_analysis):
            
            diagnostic = self.engine.diagnose_system()
            
            assert isinstance(diagnostic, Diagnostic)
            assert diagnostic.hardware is not None
            assert diagnostic.kernel_config is not None
            assert diagnostic.log_analysis is not None
    
    def test_interpret_query_hardware(self):
        """Test natural language query interpretation for hardware queries."""
        query = "What is my CPU temperature?"
        result = self.engine.interpret_query(query)
        
        assert result["original_query"] == query
        assert result["query_type"] == "hardware"
        assert "component" in result["parameters"]
        assert result["parameters"]["component"] == "cpu"
        assert "response" in result
        assert "timestamp" in result
    
    def test_interpret_query_kernel(self):
        """Test natural language query interpretation for kernel queries."""
        query = "Check my kernel configuration"
        result = self.engine.interpret_query(query)
        
        assert result["query_type"] == "kernel"
        assert "kernel" in result["response"].lower()
    
    def test_interpret_query_logs(self):
        """Test natural language query interpretation for log queries."""
        query = "Show me recent errors in logs"
        result = self.engine.interpret_query(query)
        
        assert result["query_type"] == "logs"
        assert "timeframe" in result["parameters"]
        assert result["parameters"]["timeframe"] == "recent"
    
    def test_interpret_query_performance(self):
        """Test natural language query interpretation for performance queries."""
        query = "Why is my system slow?"
        result = self.engine.interpret_query(query)
        
        assert result["query_type"] == "performance"
        assert "performance" in result["response"].lower()
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        diagnostic = Diagnostic(
            hardware=self.mock_hardware,
            kernel_config=self.mock_kernel_config,
            log_analysis=self.mock_log_analysis,
            recommendations={},
            explanation="Test diagnostic"
        )
        
        result = self.engine.generate_recommendations(diagnostic)
        
        assert "recommendations" in result
        assert "prioritized" in result
        assert "summary" in result
        assert "timestamp" in result
        assert isinstance(result["recommendations"], dict)
        assert isinstance(result["prioritized"], list)
        assert isinstance(result["summary"], str)
    
    def test_run_hardware_diagnostics(self):
        """Test hardware diagnostics execution."""
        # Mock system calls for diagnostics
        self.mock_system.run_command.return_value = Mock(
            success=True,
            stdout="df output",
            stderr=""
        )
        
        with patch('os.listdir') as mock_listdir, \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data="50000\n")):
            
            mock_listdir.return_value = ['thermal_zone0']
            mock_exists.return_value = True
            
            result = self.engine.run_hardware_diagnostics()
            
            assert "status" in result
            assert "results" in result
            assert "issues" in result
            assert "recommendations" in result
            assert "timestamp" in result
            assert result["status"] in ["passed", "failed"]
    
    def test_classify_query(self):
        """Test query classification."""
        # Hardware queries
        assert self.engine._classify_query("cpu temperature") == "hardware"
        assert self.engine._classify_query("memory usage") == "hardware"
        assert self.engine._classify_query("disk space") == "hardware"
        
        # Kernel queries
        assert self.engine._classify_query("kernel version") == "kernel"
        assert self.engine._classify_query("module loaded") == "kernel"
        
        # Log queries
        assert self.engine._classify_query("show errors") == "logs"
        assert self.engine._classify_query("warning messages") == "logs"
        
        # Performance queries
        assert self.engine._classify_query("system slow") == "performance"
        assert self.engine._classify_query("optimize performance") == "performance"
        
        # Diagnostic queries
        assert self.engine._classify_query("check system health") == "diagnostic"
        assert self.engine._classify_query("diagnose issues") == "diagnostic"
        
        # General queries
        assert self.engine._classify_query("hello world") == "general"
    
    def test_extract_query_parameters(self):
        """Test parameter extraction from queries."""
        # Component parameters
        params = self.engine._extract_query_parameters("cpu temperature", "hardware")
        assert params["component"] == "cpu"
        
        params = self.engine._extract_query_parameters("memory usage", "hardware")
        assert params["component"] == "memory"
        
        # Timeframe parameters
        params = self.engine._extract_query_parameters("recent errors", "logs")
        assert params["timeframe"] == "recent"
        
        params = self.engine._extract_query_parameters("today's logs", "logs")
        assert params["timeframe"] == "recent"
        
        # Severity parameters
        params = self.engine._extract_query_parameters("critical issues", "logs")
        assert params["severity"] == "high"
        
        params = self.engine._extract_query_parameters("warning messages", "logs")
        assert params["severity"] == "medium"
    
    def test_generate_hardware_recommendations(self):
        """Test hardware-specific recommendation generation."""
        # Test high temperature CPU
        high_temp_hardware = HardwareInfo(
            cpu={
                "model": "Intel Core i7-9700K",
                "cores": 8,
                "threads": 8,
                "frequency_mhz": 3600,
                "features": ["sse", "avx", "avx2"],
                "temperature": 85.0  # High temperature
            },
            memory={
                "total_gb": 16.0,
                "available_gb": 8.0,
                "usage_percent": 50.0
            },
            storage={},
            graphics={},
            network={},
            usb_devices={},
            pci_devices={}
        )
        
        recommendations = self.engine._generate_hardware_recommendations(high_temp_hardware)
        
        assert len(recommendations) > 0
        cpu_rec = next((r for r in recommendations if r["component"] == "cpu"), None)
        assert cpu_rec is not None
        assert cpu_rec["priority"] == "high"
        assert "cooling" in cpu_rec["action"].lower()
    
    def test_check_cpu_temperature(self):
        """Test CPU temperature checking."""
        with patch('os.listdir') as mock_listdir, \
             patch('os.path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data="cpu\n")) as mock_file:
            
            mock_listdir.return_value = ['thermal_zone0']
            mock_exists.return_value = True
            
            # Mock temperature file reads
            mock_file.side_effect = [
                mock_open(read_data="cpu\n").return_value,  # type file
                mock_open(read_data="75000\n").return_value  # temp file (75°C)
            ]
            
            result = self.engine._check_cpu_temperature()
            
            assert result["temperature"] == 75.0
            assert result["status"] == "warning"  # 75°C should be warning
    
    def test_check_cpu_load(self):
        """Test CPU load checking."""
        with patch('builtins.open', mock_open(read_data="2.5 2.0 1.8 1/150 12345\n")), \
             patch('os.cpu_count', return_value=4):
            
            result = self.engine._check_cpu_load()
            
            assert result["load_avg_1min"] == 2.5
            assert result["status"] == "normal"  # 2.5/4 = 0.625, which is normal
    
    def test_check_memory_usage(self):
        """Test memory usage checking."""
        meminfo_data = """MemTotal:       16384000 kB
MemFree:         2048000 kB
Buffers:          512000 kB
Cached:          1024000 kB
"""
        
        with patch('builtins.open', mock_open(read_data=meminfo_data)):
            result = self.engine._check_memory_usage()
            
            # Used = Total - Free - Buffers - Cached
            # Used = 16384000 - 2048000 - 512000 - 1024000 = 12800000
            # Used% = 12800000 / 16384000 * 100 = 78.125%
            assert result["used_percent"] == 78.1
            assert result["status"] == "normal"  # 78% is normal
    
    def test_check_filesystem_usage(self):
        """Test filesystem usage checking."""
        df_output = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        20G   18G  1.2G  94%   /
/dev/sda2       100G   50G   46G  52%   /home
"""
        
        self.mock_system.run_command.return_value = Mock(
            success=True,
            stdout=df_output,
            stderr=""
        )
        
        result = self.engine._check_filesystem_usage()
        
        assert "/" in result
        assert "/home" in result
        assert result["/"]["used_percent"] == 94
        assert result["/"]["status"] == "warning"  # 94% is warning (critical is >95%)
        assert result["/home"]["used_percent"] == 52
        assert result["/home"]["status"] == "normal"  # 52% is normal
    
    def test_prioritize_recommendations(self):
        """Test recommendation prioritization."""
        recommendations = {
            "hardware": [
                {"priority": "low", "action": "Low priority action"},
                {"priority": "high", "action": "High priority action"}
            ],
            "kernel": [
                {"priority": "medium", "action": "Medium priority action"}
            ]
        }
        
        prioritized = self.engine._prioritize_recommendations(recommendations)
        
        assert len(prioritized) == 3
        assert prioritized[0]["priority"] == "high"  # High priority first
        assert prioritized[1]["priority"] == "medium"  # Medium priority second
        assert prioritized[2]["priority"] == "low"  # Low priority last
        
        # Check that categories are added
        for rec in prioritized:
            assert "category" in rec
    
    def test_generate_recommendation_summary(self):
        """Test recommendation summary generation."""
        # Test with no recommendations
        summary = self.engine._generate_recommendation_summary([])
        assert "no specific recommendations" in summary.lower()
        
        # Test with mixed priority recommendations
        recommendations = [
            {"priority": "high", "action": "High priority action"},
            {"priority": "high", "action": "Another high priority action"},
            {"priority": "medium", "action": "Medium priority action"},
            {"priority": "low", "action": "Low priority action"}
        ]
        
        summary = self.engine._generate_recommendation_summary(recommendations)
        assert "2 high-priority" in summary
        assert "1 medium-priority" in summary
        assert "1 low-priority" in summary


if __name__ == "__main__":
    pytest.main([__file__])