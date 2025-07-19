#!/usr/bin/env python3
"""Tests for Recommendation Generator Module.

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
from datetime import datetime

from infenix.diagnostics.recommendation_generator import (
    RecommendationGenerator, RecommendationCategory, RecommendationPriority
)
from infenix.interfaces import (
    Diagnostic, HardwareInfo, KernelConfig, LogAnalysis, LogEntry, KernelConfigOption
)


class TestRecommendationGenerator:
    """Test cases for RecommendationGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.mock_system.read_file.return_value = None
        self.mock_system.file_exists.return_value = False
        self.mock_system.run_command.return_value = Mock(success=False, stdout="", stderr="")
        
        self.generator = RecommendationGenerator(self.mock_system)
        
        # Mock hardware info with high CPU temperature
        self.mock_hardware_high_temp = HardwareInfo(
            cpu={
                "model": "Intel Core i7-9700K",
                "cores": 8,
                "threads": 8,
                "frequency_mhz": 3600,
                "features": ["sse", "avx", "avx2"],
                "temperature": 85.0,  # High temperature
                "load_avg_1min": 16.0,  # High load: 16.0 / 8 = 2.0 per core > 1.5 threshold
                "governor": "powersave"  # Non-optimal governor
            },
            memory={
                "total_gb": 16.0,
                "available_gb": 1.0,
                "usage_percent": 95.0,  # Critical usage
                "swap_usage_percent": 60.0  # High swap usage
            },
            storage={
                "devices": [
                    {
                        "device": "/dev/sda",
                        "model": "Samsung SSD 970",
                        "size_gb": 500.0,
                        "type": "SSD",
                        "mount_point": "/",
                        "usage_percent": 96.0  # Critical usage
                    }
                ],
                "smart_issues": [
                    {
                        "device": "/dev/sda",
                        "severity": "critical",
                        "message": "Reallocated sector count high"
                    }
                ]
            },
            graphics={
                "vendor": "NVIDIA Corporation",
                "driver": "nouveau"
            },
            network={
                "interfaces": [
                    {
                        "name": "eth0",
                        "status": "down",
                        "type": "ethernet"
                    }
                ]
            },
            usb_devices={},
            pci_devices={}
        )
        
        # Mock kernel config with security issues
        self.mock_kernel_config = KernelConfig(
            version="5.15.0",
            options={
                "CONFIG_SECURITY": KernelConfigOption(
                    name="CONFIG_SECURITY",
                    value="n",  # Should be "y"
                    description="Kernel security framework"
                ),
                "CONFIG_PREEMPT": KernelConfigOption(
                    name="CONFIG_PREEMPT",
                    value="n",  # Could be "y" for better performance
                    description="Preemptible kernel"
                )
            },
            analysis={},
            recommendations={}
        )
        
        # Mock log analysis with issues
        self.mock_log_analysis = LogAnalysis(
            entries=[
                LogEntry(
                    timestamp=datetime.now(),
                    facility="kernel",
                    severity="error",
                    message="Out of memory: Kill process",
                    source="/var/log/kern.log"
                )
            ],
            patterns={
                "error_frequency": {
                    "memory_error": 15,
                    "disk_error": 5
                }
            },
            issues={
                "memory_issues": [
                    {
                        "severity": "critical",
                        "type": "memory",
                        "message": "Out of memory condition detected"
                    }
                ],
                "security_issues": [
                    {
                        "severity": "high",
                        "type": "security",
                        "message": "Authentication failed for user"
                    }
                ]
            },
            summary={"total_issues": 2, "critical_issues": 1}
        )
        
        # Mock diagnostic
        self.mock_diagnostic = Diagnostic(
            hardware=self.mock_hardware_high_temp,
            kernel_config=self.mock_kernel_config,
            log_analysis=self.mock_log_analysis,
            recommendations={},
            explanation="Test diagnostic"
        )
    
    def test_init(self):
        """Test RecommendationGenerator initialization."""
        generator = RecommendationGenerator()
        assert generator.system is not None
        assert generator.priority_weights is not None
        assert generator.category_weights is not None
        assert generator.recommendation_rules is not None
    
    def test_generate_recommendations_complete(self):
        """Test complete recommendation generation."""
        result = self.generator.generate_recommendations(self.mock_diagnostic)
        
        assert "recommendations" in result
        assert "prioritized" in result
        assert "summary" in result
        assert "implementation_guides" in result
        assert "statistics" in result
        assert "timestamp" in result
        
        # Should have recommendations from multiple categories
        assert len(result["recommendations"]) > 0
        assert len(result["prioritized"]) > 0
        assert isinstance(result["summary"], str)
        assert len(result["implementation_guides"]) > 0
        assert isinstance(result["statistics"], dict)
    
    def test_analyze_cpu_recommendations(self):
        """Test CPU-specific recommendation analysis."""
        cpu_info = {
            "temperature": 85.0,
            "load_avg_1min": 10.0,  # High load: 10.0 / 4 = 2.5 per core > 2.0 threshold
            "cores": 4,
            "governor": "powersave"
        }
        
        recommendations = self.generator._analyze_cpu_recommendations(cpu_info)
        
        assert len(recommendations) > 0
        
        # Should have critical temperature recommendation
        temp_rec = next((r for r in recommendations if 'cooling' in r['action'].lower()), None)
        assert temp_rec is not None
        assert temp_rec['priority'] == RecommendationPriority.CRITICAL
        assert temp_rec['category'] == RecommendationCategory.STABILITY
        
        # Should have high load recommendation
        load_rec = next((r for r in recommendations if 'load' in r['action'].lower()), None)
        assert load_rec is not None
        assert load_rec['priority'] == RecommendationPriority.HIGH
        
        # Should have governor recommendation
        gov_rec = next((r for r in recommendations if 'frequency' in r['action'].lower()), None)
        assert gov_rec is not None
        assert gov_rec['category'] == RecommendationCategory.PERFORMANCE
    
    def test_analyze_memory_recommendations(self):
        """Test memory-specific recommendation analysis."""
        memory_info = {
            "usage_percent": 95.0,
            "swap_usage_percent": 60.0
        }
        
        recommendations = self.generator._analyze_memory_recommendations(memory_info)
        
        assert len(recommendations) > 0
        
        # Should have critical memory usage recommendation
        mem_rec = next((r for r in recommendations if 'memory' in r['action'].lower()), None)
        assert mem_rec is not None
        assert mem_rec['priority'] == RecommendationPriority.CRITICAL
        assert mem_rec['category'] == RecommendationCategory.STABILITY
        
        # Should have swap usage recommendation
        swap_rec = next((r for r in recommendations if 'swap' in r['action'].lower()), None)
        assert swap_rec is not None
        assert swap_rec['category'] == RecommendationCategory.PERFORMANCE
    
    def test_analyze_storage_recommendations(self):
        """Test storage-specific recommendation analysis."""
        storage_info = {
            "devices": [
                {
                    "device": "/dev/sda",
                    "mount_point": "/",
                    "usage_percent": 96.0
                }
            ],
            "smart_issues": [
                {
                    "device": "/dev/sda",
                    "severity": "critical",
                    "message": "Reallocated sector count high"
                }
            ]
        }
        
        recommendations = self.generator._analyze_storage_recommendations(storage_info)
        
        assert len(recommendations) > 0
        
        # Should have critical disk usage recommendation
        disk_rec = next((r for r in recommendations if 'space' in r['action'].lower()), None)
        assert disk_rec is not None
        assert disk_rec['priority'] == RecommendationPriority.CRITICAL
        
        # Should have SMART issue recommendation
        smart_rec = next((r for r in recommendations if 'smart' in r['action'].lower()), None)
        assert smart_rec is not None
        assert smart_rec['priority'] == RecommendationPriority.CRITICAL
        assert smart_rec['category'] == RecommendationCategory.STABILITY
    
    def test_analyze_kernel_security(self):
        """Test kernel security analysis."""
        recommendations = self.generator._analyze_kernel_security(self.mock_kernel_config)
        
        assert len(recommendations) > 0
        
        # Should have security framework recommendation
        sec_rec = next((r for r in recommendations if 'CONFIG_SECURITY' in r['action']), None)
        assert sec_rec is not None
        assert sec_rec['category'] == RecommendationCategory.SECURITY
        assert sec_rec['priority'] == RecommendationPriority.HIGH
    
    def test_analyze_kernel_performance(self):
        """Test kernel performance analysis."""
        recommendations = self.generator._analyze_kernel_performance(self.mock_kernel_config)
        
        assert len(recommendations) > 0
        
        # Should have preemption recommendation
        preempt_rec = next((r for r in recommendations if 'CONFIG_PREEMPT' in r['action']), None)
        assert preempt_rec is not None
        assert preempt_rec['category'] == RecommendationCategory.PERFORMANCE
    
    def test_analyze_log_issue(self):
        """Test individual log issue analysis."""
        issue = {
            "severity": "critical",
            "type": "memory",
            "message": "Out of memory: Kill process 1234"
        }
        
        recommendations = self.generator._analyze_log_issue(issue, "memory_issues")
        
        assert len(recommendations) > 0
        
        rec = recommendations[0]
        assert rec['priority'] == RecommendationPriority.CRITICAL
        assert rec['category'] == RecommendationCategory.STABILITY
        assert 'memory' in rec['action'].lower()
        assert rec['urgency'] == 'soon'
    
    def test_analyze_log_patterns(self):
        """Test log pattern analysis."""
        patterns = {
            "error_frequency": {
                "memory_error": 15,
                "disk_error": 5
            }
        }
        
        recommendations = self.generator._analyze_log_patterns(patterns)
        
        assert len(recommendations) > 0
        
        # Should have recommendation for high-frequency memory errors
        mem_rec = next((r for r in recommendations if 'memory_error' in r['action']), None)
        assert mem_rec is not None
        assert mem_rec['priority'] == RecommendationPriority.MEDIUM
    
    def test_generate_security_recommendations(self):
        """Test security recommendation generation."""
        recommendations = self.generator._generate_security_recommendations(self.mock_diagnostic)
        
        assert len(recommendations) > 0
        
        # Should have security log review recommendation
        sec_rec = next((r for r in recommendations if 'security' in r['action'].lower()), None)
        assert sec_rec is not None
        assert sec_rec['category'] == RecommendationCategory.SECURITY
        
        # Should have general security update recommendation
        update_rec = next((r for r in recommendations if 'update' in r['action'].lower()), None)
        assert update_rec is not None
    
    def test_generate_performance_recommendations(self):
        """Test performance recommendation generation."""
        recommendations = self.generator._generate_performance_recommendations(self.mock_diagnostic)
        
        assert len(recommendations) > 0
        
        # Should have CPU optimization recommendation
        cpu_rec = next((r for r in recommendations if 'cpu' in r['action'].lower()), None)
        assert cpu_rec is not None
        assert cpu_rec['category'] == RecommendationCategory.PERFORMANCE
        
        # Should have memory optimization recommendation
        mem_rec = next((r for r in recommendations if 'memory' in r['action'].lower()), None)
        assert mem_rec is not None
    
    def test_generate_maintenance_recommendations(self):
        """Test maintenance recommendation generation."""
        recommendations = self.generator._generate_maintenance_recommendations(self.mock_diagnostic)
        
        assert len(recommendations) >= 3  # Should have at least 3 maintenance recommendations
        
        # Should have cleanup recommendation
        cleanup_rec = next((r for r in recommendations if 'cleanup' in r['action'].lower()), None)
        assert cleanup_rec is not None
        assert cleanup_rec['category'] == RecommendationCategory.MAINTENANCE
        
        # Should have backup recommendation
        backup_rec = next((r for r in recommendations if 'backup' in r['action'].lower()), None)
        assert backup_rec is not None
    
    def test_prioritize_recommendations(self):
        """Test recommendation prioritization."""
        recommendations = {
            "hardware": [
                {
                    'component': 'cpu',
                    'priority': RecommendationPriority.LOW,
                    'category': RecommendationCategory.PERFORMANCE,
                    'action': 'Low priority action'
                },
                {
                    'component': 'cpu',
                    'priority': RecommendationPriority.CRITICAL,
                    'category': RecommendationCategory.SECURITY,
                    'action': 'Critical action'
                }
            ],
            "kernel": [
                {
                    'component': 'kernel',
                    'priority': RecommendationPriority.MEDIUM,
                    'category': RecommendationCategory.STABILITY,
                    'action': 'Medium priority action'
                }
            ]
        }
        
        prioritized = self.generator._prioritize_recommendations(recommendations)
        
        assert len(prioritized) == 3
        
        # Critical priority should be first
        assert prioritized[0]['priority'] == RecommendationPriority.CRITICAL
        
        # Should have category added
        for rec in prioritized:
            assert 'category' in rec
    
    def test_deduplicate_recommendations(self):
        """Test recommendation deduplication."""
        recommendations = [
            {
                'component': 'cpu',
                'action': 'Check CPU cooling',
                'priority': RecommendationPriority.HIGH
            },
            {
                'component': 'cpu',
                'action': 'Check CPU cooling',  # Duplicate
                'priority': RecommendationPriority.MEDIUM
            },
            {
                'component': 'memory',
                'action': 'Check memory usage',
                'priority': RecommendationPriority.LOW
            }
        ]
        
        deduplicated = self.generator._deduplicate_recommendations(recommendations)
        
        assert len(deduplicated) == 2  # Should remove one duplicate
        
        # Should keep the first occurrence
        cpu_rec = next((r for r in deduplicated if r['component'] == 'cpu'), None)
        assert cpu_rec is not None
        assert cpu_rec['priority'] == RecommendationPriority.HIGH
    
    def test_add_explanations(self):
        """Test adding explanations to recommendations."""
        recommendations = [
            {
                'component': 'cpu',
                'action': 'Check CPU cooling',
                'details': 'CPU temperature is high',
                'impact': 'Performance degradation',
                'urgency': 'soon'
            }
        ]
        
        explained = self.generator._add_explanations(recommendations)
        
        assert len(explained) == 1
        assert 'explanation' in explained[0]
        assert isinstance(explained[0]['explanation'], str)
        assert len(explained[0]['explanation']) > 0
    
    def test_generate_implementation_guides(self):
        """Test implementation guide generation."""
        recommendations = [
            {
                'component': 'cpu',
                'action': 'Check CPU cooling',
                'priority': RecommendationPriority.HIGH
            },
            {
                'component': 'memory',
                'action': 'Optimize memory usage',
                'priority': RecommendationPriority.MEDIUM
            }
        ]
        
        guides = self.generator._generate_implementation_guides(recommendations)
        
        assert len(guides) == 2
        
        for guide in guides:
            assert 'recommendation_id' in guide
            assert 'title' in guide
            assert 'steps' in guide
            assert 'estimated_time' in guide
            assert 'difficulty' in guide
            assert 'prerequisites' in guide
            assert 'risks' in guide
            
            assert isinstance(guide['steps'], list)
            assert len(guide['steps']) > 0
    
    def test_generate_implementation_steps(self):
        """Test implementation step generation."""
        # CPU cooling recommendation
        cpu_rec = {
            'component': 'cpu',
            'action': 'Check CPU cooling'
        }
        
        steps = self.generator._generate_implementation_steps(cpu_rec)
        
        assert isinstance(steps, list)
        assert len(steps) >= 3
        assert any('temperature' in step.lower() for step in steps)
        assert any('fan' in step.lower() for step in steps)
        
        # Memory usage recommendation
        mem_rec = {
            'component': 'memory',
            'action': 'Optimize memory usage'
        }
        
        steps = self.generator._generate_implementation_steps(mem_rec)
        
        assert isinstance(steps, list)
        assert len(steps) >= 3
        assert any('memory' in step.lower() for step in steps)
    
    def test_estimate_implementation_time(self):
        """Test implementation time estimation."""
        # Critical priority should be quick
        critical_rec = {'priority': RecommendationPriority.CRITICAL}
        time_est = self.generator._estimate_implementation_time(critical_rec)
        assert '15-30' in time_est
        
        # Kernel changes should take longer
        kernel_rec = {'component': 'kernel', 'priority': RecommendationPriority.MEDIUM}
        time_est = self.generator._estimate_implementation_time(kernel_rec)
        assert '1-2 hours' in time_est
    
    def test_assess_implementation_difficulty(self):
        """Test implementation difficulty assessment."""
        # Kernel changes should be advanced
        kernel_rec = {'component': 'kernel'}
        difficulty = self.generator._assess_implementation_difficulty(kernel_rec)
        assert difficulty == "Advanced"
        
        # Security changes should be intermediate
        security_rec = {'component': 'security'}
        difficulty = self.generator._assess_implementation_difficulty(security_rec)
        assert difficulty == "Intermediate"
        
        # Hardware changes should be beginner
        hardware_rec = {'component': 'hardware'}
        difficulty = self.generator._assess_implementation_difficulty(hardware_rec)
        assert difficulty == "Beginner"
    
    def test_generate_recommendation_statistics(self):
        """Test recommendation statistics generation."""
        recommendations = [
            {
                'priority': RecommendationPriority.CRITICAL,
                'category': RecommendationCategory.SECURITY,
                'component': 'cpu',
                'urgency': 'immediate'
            },
            {
                'priority': RecommendationPriority.HIGH,
                'category': RecommendationCategory.PERFORMANCE,
                'component': 'memory',
                'urgency': 'soon'
            },
            {
                'priority': RecommendationPriority.MEDIUM,
                'category': RecommendationCategory.MAINTENANCE,
                'component': 'storage',
                'urgency': 'when_convenient'
            }
        ]
        
        stats = self.generator._generate_recommendation_statistics(recommendations)
        
        assert stats['total_recommendations'] == 3
        assert stats['critical_count'] == 1
        assert stats['high_priority_count'] == 1
        
        assert 'by_priority' in stats
        assert 'by_category' in stats
        assert 'by_component' in stats
        assert 'by_urgency' in stats
        
        assert stats['by_priority'][RecommendationPriority.CRITICAL] == 1
        assert stats['by_category'][RecommendationCategory.SECURITY] == 1
        assert stats['by_component']['cpu'] == 1
        assert stats['by_urgency']['immediate'] == 1
    
    def test_generate_recommendation_summary(self):
        """Test recommendation summary generation."""
        # Test with no recommendations
        summary = self.generator._generate_recommendation_summary([])
        assert "no specific recommendations" in summary.lower()
        
        # Test with mixed priority recommendations
        recommendations = [
            {'priority': RecommendationPriority.CRITICAL},
            {'priority': RecommendationPriority.CRITICAL},
            {'priority': RecommendationPriority.HIGH},
            {'priority': RecommendationPriority.MEDIUM},
            {'priority': RecommendationPriority.LOW}
        ]
        
        summary = self.generator._generate_recommendation_summary(recommendations)
        assert "2 critical-priority" in summary
        assert "1 high-priority" in summary
        assert "1 medium-priority" in summary
        assert "1 low-priority" in summary


if __name__ == "__main__":
    pytest.main([__file__])