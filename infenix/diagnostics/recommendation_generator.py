#!/usr/bin/env python3
"""Recommendation Generation Module.

This module provides comprehensive recommendation generation capabilities
for system optimization, security, and performance improvements.

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

import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from functools import lru_cache
from dataclasses import dataclass

from ..interfaces import Diagnostic, HardwareInfo, KernelConfig, LogAnalysis, SystemInterface
from ..system import LinuxSystemInterface
from abc import ABC, abstractmethod


class RecommendationCategory:
    """Recommendation category constants."""
    SECURITY = 'security'
    PERFORMANCE = 'performance'
    STABILITY = 'stability'
    OPTIMIZATION = 'optimization'
    MAINTENANCE = 'maintenance'


class RecommendationPriority:
    """Recommendation priority constants."""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


@dataclass
class Recommendation:
    """Data class for structured recommendations."""
    component: str
    category: str
    priority: str
    action: str
    details: str
    impact: str
    urgency: str = 'when_convenient'
    explanation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary."""
        return {
            'component': self.component,
            'category': self.category,
            'priority': self.priority,
            'action': self.action,
            'details': self.details,
            'impact': self.impact,
            'urgency': self.urgency,
            'explanation': self.explanation
        }


class RecommendationConfig:
    """Configuration class for recommendation thresholds and rules."""
    
    # Temperature thresholds (Celsius)
    CPU_TEMP_CRITICAL = 85
    CPU_TEMP_HIGH = 75
    CPU_TEMP_NORMAL = 65
    
    # Usage thresholds (percentage)
    MEMORY_USAGE_CRITICAL = 95
    MEMORY_USAGE_HIGH = 85
    DISK_USAGE_CRITICAL = 95
    DISK_USAGE_HIGH = 85
    SWAP_USAGE_HIGH = 50
    
    # Load thresholds
    CPU_LOAD_HIGH_MULTIPLIER = 2.0
    
    # Log pattern thresholds
    ERROR_FREQUENCY_THRESHOLD = 10
    
    # Security patterns
    SECURITY_PATTERNS = [
        'authentication failed',
        'security violation', 
        'unauthorized access',
        'failed login'
    ]
    
    # Performance patterns
    PERFORMANCE_PATTERNS = [
        'high load',
        'slow response',
        'timeout',
        'performance degradation'
    ]


class BaseAnalyzer(ABC):
    """Base class for component-specific analyzers."""
    
    def __init__(self, rules: Dict[str, Any]):
        """Initialize analyzer with rules.
        
        Args:
            rules: Configuration rules for analysis
        """
        self.rules = rules
    
    @abstractmethod
    def analyze(self, data: Any) -> List[Dict[str, Any]]:
        """Analyze component data and generate recommendations.
        
        Args:
            data: Component-specific data to analyze
            
        Returns:
            List of recommendations
        """
        pass
    
    def _create_recommendation(
        self,
        component: str,
        category: str,
        priority: str,
        action: str,
        details: str,
        impact: str,
        urgency: str = 'when_convenient'
    ) -> Dict[str, Any]:
        """Create a standardized recommendation dictionary."""
        return {
            'component': component,
            'category': category,
            'priority': priority,
            'action': action,
            'details': details,
            'impact': impact,
            'urgency': urgency
        }


class CPUAnalyzer(BaseAnalyzer):
    """Analyzer for CPU-related recommendations."""
    
    def analyze(self, cpu_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze CPU information and generate recommendations."""
        recommendations = []
        
        # Temperature analysis
        temp = cpu_info.get('temperature')
        if temp:
            recommendations.extend(self._analyze_temperature(temp))
        
        # Frequency scaling analysis
        governor = cpu_info.get('governor')
        if governor:
            recommendations.extend(self._analyze_governor(governor))
        
        # Load analysis
        load_avg = cpu_info.get('load_avg_1min')
        cores = cpu_info.get('cores', 1)
        if load_avg and cores:
            recommendations.extend(self._analyze_load(load_avg, cores))
        
        return recommendations
    
    def _analyze_temperature(self, temp: float) -> List[Dict[str, Any]]:
        """Analyze CPU temperature."""
        recommendations = []
        
        if temp >= RecommendationConfig.CPU_TEMP_CRITICAL:
            recommendations.append(self._create_recommendation(
                'cpu', RecommendationCategory.STABILITY, RecommendationPriority.CRITICAL,
                'Immediate CPU cooling required',
                f'CPU temperature is critically high at {temp}°C. System may throttle or shutdown.',
                'System stability at risk', 'immediate'
            ))
        elif temp > RecommendationConfig.CPU_TEMP_HIGH:
            recommendations.append(self._create_recommendation(
                'cpu', RecommendationCategory.PERFORMANCE, RecommendationPriority.HIGH,
                'Improve CPU cooling',
                f'CPU temperature is high at {temp}°C. Consider cleaning fans or improving airflow.',
                'Performance degradation possible', 'soon'
            ))
        
        return recommendations
    
    def _analyze_governor(self, governor: str) -> List[Dict[str, Any]]:
        """Analyze CPU frequency governor."""
        if governor not in ['performance', 'schedutil']:
            return [self._create_recommendation(
                'cpu', RecommendationCategory.PERFORMANCE, RecommendationPriority.MEDIUM,
                'Optimize CPU frequency scaling',
                f'Current governor "{governor}" may not provide optimal performance. Consider "performance" or "schedutil".',
                'CPU performance optimization'
            )]
        return []
    
    def _analyze_load(self, load_avg: float, cores: int) -> List[Dict[str, Any]]:
        """Analyze CPU load."""
        load_per_core = load_avg / cores
        
        if load_per_core > RecommendationConfig.CPU_LOAD_HIGH_MULTIPLIER:
            return [self._create_recommendation(
                'cpu', RecommendationCategory.PERFORMANCE, RecommendationPriority.HIGH,
                'Investigate high CPU load',
                f'CPU load is very high ({load_avg:.2f} on {cores} cores). Check for resource-intensive processes.',
                'System responsiveness affected', 'soon'
            )]
        return []


class MemoryAnalyzer(BaseAnalyzer):
    """Analyzer for memory-related recommendations."""
    
    def analyze(self, memory_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze memory information and generate recommendations."""
        recommendations = []
        
        # Memory usage analysis
        usage_percent = memory_info.get('usage_percent')
        if usage_percent:
            if usage_percent >= RecommendationConfig.MEMORY_USAGE_CRITICAL:
                recommendations.append(self._create_recommendation(
                    'memory', RecommendationCategory.STABILITY, RecommendationPriority.CRITICAL,
                    'Address critical memory shortage',
                    f'Memory usage is critically high at {usage_percent}%. System may become unstable.',
                    'System stability at risk', 'immediate'
                ))
            elif usage_percent > RecommendationConfig.MEMORY_USAGE_HIGH:
                recommendations.append(self._create_recommendation(
                    'memory', RecommendationCategory.PERFORMANCE, RecommendationPriority.HIGH,
                    'Address high memory usage',
                    f'Memory usage is high at {usage_percent}%. Consider adding more RAM or closing applications.',
                    'Performance degradation likely', 'soon'
                ))
        
        # Swap usage analysis
        swap_usage = memory_info.get('swap_usage_percent')
        if swap_usage and swap_usage > RecommendationConfig.SWAP_USAGE_HIGH:
            recommendations.append(self._create_recommendation(
                'memory', RecommendationCategory.PERFORMANCE, RecommendationPriority.MEDIUM,
                'Reduce swap usage',
                f'Swap usage is high at {swap_usage}%. This can significantly slow down the system.',
                'System performance degradation'
            ))
        
        return recommendations


class RecommendationGenerator:
    """Advanced recommendation generator for system optimization and diagnostics."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize recommendation generator.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        self.priority_weights = {
            RecommendationPriority.CRITICAL: 4,
            RecommendationPriority.HIGH: 3,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 1
        }
        self.category_weights = {
            RecommendationCategory.SECURITY: 4,
            RecommendationCategory.STABILITY: 3,
            RecommendationCategory.PERFORMANCE: 2,
            RecommendationCategory.OPTIMIZATION: 2,
            RecommendationCategory.MAINTENANCE: 1
        }
        self.recommendation_rules = self._load_recommendation_rules()
        self._analyzers = self._initialize_analyzers()
        self.logger = logging.getLogger(__name__)
    
    def _initialize_analyzers(self) -> Dict[str, BaseAnalyzer]:
        """Initialize component-specific analyzers."""
        return {
            'cpu': CPUAnalyzer(self.recommendation_rules),
            'memory': MemoryAnalyzer(self.recommendation_rules),
            # Add more analyzers as needed
        }
    
    def generate_recommendations(self, diagnostic: Diagnostic) -> Dict[str, Any]:
        """Generate comprehensive actionable recommendations based on diagnostics.
        
        Args:
            diagnostic: System diagnostic information
            
        Returns:
            Comprehensive recommendations with priorities, explanations, and actions
            
        Raises:
            ValueError: If diagnostic is None or invalid
        """
        if not diagnostic:
            raise ValueError("Diagnostic information is required")
        
        try:
            # Generate category-specific recommendations
            recommendations = {
                "hardware": self._safe_generate_hardware_recommendations(diagnostic.hardware),
                "kernel": self._safe_generate_kernel_recommendations(diagnostic.kernel_config),
                "logs": self._safe_generate_log_recommendations(diagnostic.log_analysis),
                "system": self._safe_generate_system_recommendations(diagnostic),
                "security": self._safe_generate_security_recommendations(diagnostic),
                "performance": self._safe_generate_performance_recommendations(diagnostic),
                "maintenance": self._safe_generate_maintenance_recommendations(diagnostic)
            }
            
            # Remove empty recommendation categories
            recommendations = {k: v for k, v in recommendations.items() if v}
            
            # Prioritize and deduplicate recommendations
            prioritized = self._prioritize_recommendations(recommendations)
            deduplicated = self._deduplicate_recommendations(prioritized)
            
            # Generate explanations for top recommendations
            explained = self._add_explanations(deduplicated)
            
            # Generate implementation guides
            implementation_guides = self._generate_implementation_guides(explained[:5])  # Top 5
            
            return {
                "recommendations": recommendations,
                "prioritized": explained,
                "summary": self._generate_recommendation_summary(explained),
                "implementation_guides": implementation_guides,
                "statistics": self._generate_recommendation_statistics(explained),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # Log the error and return a minimal response
            return {
                "error": f"Failed to generate recommendations: {str(e)}",
                "recommendations": {},
                "prioritized": [],
                "summary": "Unable to generate recommendations due to an error",
                "implementation_guides": [],
                "statistics": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _safe_generate_hardware_recommendations(self, hardware: Optional[HardwareInfo]) -> List[Dict[str, Any]]:
        """Safely generate hardware recommendations with error handling."""
        try:
            return self._generate_hardware_recommendations(hardware)
        except Exception:
            return []
    
    def _safe_generate_kernel_recommendations(self, kernel_config: Optional[KernelConfig]) -> List[Dict[str, Any]]:
        """Safely generate kernel recommendations with error handling."""
        try:
            return self._generate_kernel_recommendations(kernel_config)
        except Exception:
            return []
    
    def _safe_generate_log_recommendations(self, log_analysis: Optional[LogAnalysis]) -> List[Dict[str, Any]]:
        """Safely generate log recommendations with error handling."""
        try:
            return self._generate_log_recommendations(log_analysis)
        except Exception:
            return []
    
    def _safe_generate_system_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Safely generate system recommendations with error handling."""
        try:
            return self._generate_system_recommendations(diagnostic)
        except Exception:
            return []
    
    def _safe_generate_security_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Safely generate security recommendations with error handling."""
        try:
            return self._generate_security_recommendations(diagnostic)
        except Exception:
            return []
    
    def _safe_generate_performance_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Safely generate performance recommendations with error handling."""
        try:
            return self._generate_performance_recommendations(diagnostic)
        except Exception:
            return []
    
    def _safe_generate_maintenance_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Safely generate maintenance recommendations with error handling."""
        try:
            return self._generate_maintenance_recommendations(diagnostic)
        except Exception:
            return []
    
    def _generate_hardware_recommendations(self, hardware: Optional[HardwareInfo]) -> List[Dict[str, Any]]:
        """Generate comprehensive hardware-specific recommendations."""
        if not hardware:
            return []
        
        recommendations = []
        
        # CPU recommendations
        if hardware.cpu and isinstance(hardware.cpu, dict):
            recommendations.extend(self._analyze_cpu_recommendations(hardware.cpu))
        
        # Memory recommendations
        if hardware.memory and isinstance(hardware.memory, dict):
            recommendations.extend(self._analyze_memory_recommendations(hardware.memory))
        
        # Storage recommendations
        if hardware.storage and isinstance(hardware.storage, dict):
            recommendations.extend(self._analyze_storage_recommendations(hardware.storage))
        
        # Network recommendations
        if hardware.network and isinstance(hardware.network, dict):
            recommendations.extend(self._analyze_network_recommendations(hardware.network))
        
        # Graphics recommendations
        if hardware.graphics and isinstance(hardware.graphics, dict):
            recommendations.extend(self._analyze_graphics_recommendations(hardware.graphics))
        
        return recommendations
    
    def _analyze_cpu_recommendations(self, cpu_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze CPU and generate recommendations."""
        return self._analyzers['cpu'].analyze(cpu_info)
    
    def _analyze_memory_recommendations(self, memory_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze memory and generate recommendations."""
        return self._analyzers['memory'].analyze(memory_info)
    
    def _analyze_storage_recommendations(self, storage_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze storage and generate recommendations."""
        recommendations = []
        
        # Disk usage analysis
        devices = storage_info.get('devices', [])
        for device in devices:
            usage_percent = device.get('usage_percent')
            mount_point = device.get('mount_point', device.get('device', 'Unknown'))
            
            if usage_percent:
                if usage_percent > 95:
                    recommendations.append({
                        'component': 'storage',
                        'category': RecommendationCategory.STABILITY,
                        'priority': RecommendationPriority.CRITICAL,
                        'action': f'Free up space on {mount_point}',
                        'details': f'Disk usage is critically high at {usage_percent}%. System may become unstable.',
                        'impact': 'System stability at risk',
                        'urgency': 'immediate'
                    })
                elif usage_percent > 85:
                    recommendations.append({
                        'component': 'storage',
                        'category': RecommendationCategory.MAINTENANCE,
                        'priority': RecommendationPriority.HIGH,
                        'action': f'Clean up disk space on {mount_point}',
                        'details': f'Disk usage is high at {usage_percent}%. Consider removing unnecessary files.',
                        'impact': 'Prevent future storage issues',
                        'urgency': 'soon'
                    })
        
        # SMART status analysis
        smart_issues = storage_info.get('smart_issues', [])
        for issue in smart_issues:
            device = issue.get('device', 'Unknown device')
            severity = issue.get('severity', 'medium')
            
            priority = RecommendationPriority.CRITICAL if severity == 'critical' else RecommendationPriority.HIGH
            recommendations.append({
                'component': 'storage',
                'category': RecommendationCategory.STABILITY,
                'priority': priority,
                'action': f'Address SMART warnings on {device}',
                'details': f'SMART monitoring detected potential issues with {device}. Backup data and consider replacement.',
                'impact': 'Data loss risk',
                'urgency': 'immediate' if severity == 'critical' else 'soon'
            })
        
        return recommendations
    
    def _analyze_network_recommendations(self, network_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze network and generate recommendations."""
        recommendations = []
        
        # Interface status analysis
        interfaces = network_info.get('interfaces', [])
        for interface in interfaces:
            if interface.get('status') == 'down' and interface.get('type') != 'loopback':
                recommendations.append({
                    'component': 'network',
                    'category': RecommendationCategory.STABILITY,
                    'priority': RecommendationPriority.MEDIUM,
                    'action': f'Check network interface {interface.get("name", "unknown")}',
                    'details': f'Network interface is down. Check cable connections and configuration.',
                    'impact': 'Network connectivity issues',
                    'urgency': 'when_convenient'
                })
        
        return recommendations
    
    def _analyze_graphics_recommendations(self, graphics_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze graphics and generate recommendations."""
        recommendations = []
        
        # Driver recommendations
        vendor = graphics_info.get('vendor', '').lower()
        driver = graphics_info.get('driver', '').lower()
        
        if 'nvidia' in vendor and 'nouveau' in driver:
            recommendations.append({
                'component': 'graphics',
                'category': RecommendationCategory.PERFORMANCE,
                'priority': RecommendationPriority.MEDIUM,
                'action': 'Consider proprietary NVIDIA drivers',
                'details': 'Using open-source Nouveau driver. Proprietary NVIDIA drivers may provide better performance.',
                'impact': 'Graphics performance improvement',
                'urgency': 'when_convenient'
            })
        
        return recommendations
    
    def _generate_kernel_recommendations(self, kernel_config: Optional[KernelConfig]) -> List[Dict[str, Any]]:
        """Generate comprehensive kernel configuration recommendations."""
        if not kernel_config:
            return []
        
        recommendations = []
        
        # Security recommendations
        recommendations.extend(self._analyze_kernel_security(kernel_config))
        
        # Performance recommendations
        recommendations.extend(self._analyze_kernel_performance(kernel_config))
        
        # Stability recommendations
        recommendations.extend(self._analyze_kernel_stability(kernel_config))
        
        return recommendations
    
    def _analyze_kernel_security(self, kernel_config: KernelConfig) -> List[Dict[str, Any]]:
        """Analyze kernel security configuration."""
        recommendations = []
        
        # Critical security options
        critical_security_options = {
            'CONFIG_SECURITY': ('y', 'Enable kernel security framework'),
            'CONFIG_SECURITY_DMESG_RESTRICT': ('y', 'Restrict dmesg access to privileged users'),
            'CONFIG_SECURITY_YAMA': ('y', 'Enable Yama security module'),
            'CONFIG_HARDENED_USERCOPY': ('y', 'Enable hardened usercopy'),
            'CONFIG_FORTIFY_SOURCE': ('y', 'Enable FORTIFY_SOURCE'),
        }
        
        for option, (recommended_value, description) in critical_security_options.items():
            if option in kernel_config.options:
                current_value = kernel_config.options[option].value
                if current_value != recommended_value:
                    recommendations.append({
                        'component': 'kernel',
                        'category': RecommendationCategory.SECURITY,
                        'priority': RecommendationPriority.HIGH,
                        'action': f'Enable {option}',
                        'details': f'{description}. Current: {current_value}, Recommended: {recommended_value}',
                        'impact': 'Enhanced system security',
                        'urgency': 'soon'
                    })
        
        # Optional security enhancements
        optional_security_options = {
            'CONFIG_SECURITY_SELINUX': ('y', 'Enable SELinux mandatory access control'),
            'CONFIG_SECURITY_APPARMOR': ('y', 'Enable AppArmor application security'),
            'CONFIG_SECURITY_TOMOYO': ('y', 'Enable TOMOYO security module'),
        }
        
        for option, (recommended_value, description) in optional_security_options.items():
            if option in kernel_config.options:
                current_value = kernel_config.options[option].value
                if current_value != recommended_value:
                    recommendations.append({
                        'component': 'kernel',
                        'category': RecommendationCategory.SECURITY,
                        'priority': RecommendationPriority.MEDIUM,
                        'action': f'Consider enabling {option}',
                        'details': f'{description}. Current: {current_value}, Recommended: {recommended_value}',
                        'impact': 'Additional security layer',
                        'urgency': 'when_convenient'
                    })
        
        return recommendations
    
    def _analyze_kernel_performance(self, kernel_config: KernelConfig) -> List[Dict[str, Any]]:
        """Analyze kernel performance configuration."""
        recommendations = []
        
        # Performance-critical options
        performance_options = {
            'CONFIG_PREEMPT': ('y', 'Enable preemptible kernel for better responsiveness'),
            'CONFIG_NO_HZ': ('y', 'Enable tickless system for power efficiency'),
            'CONFIG_HIGH_RES_TIMERS': ('y', 'Enable high resolution timers'),
            'CONFIG_SMP': ('y', 'Enable symmetric multiprocessing'),
        }
        
        for option, (recommended_value, description) in performance_options.items():
            if option in kernel_config.options:
                current_value = kernel_config.options[option].value
                if current_value != recommended_value:
                    recommendations.append({
                        'component': 'kernel',
                        'category': RecommendationCategory.PERFORMANCE,
                        'priority': RecommendationPriority.MEDIUM,
                        'action': f'Optimize {option}',
                        'details': f'{description}. Current: {current_value}, Recommended: {recommended_value}',
                        'impact': 'System performance improvement',
                        'urgency': 'when_convenient'
                    })
        
        return recommendations
    
    def _analyze_kernel_stability(self, kernel_config: KernelConfig) -> List[Dict[str, Any]]:
        """Analyze kernel stability configuration."""
        recommendations = []
        
        # Stability options
        stability_options = {
            'CONFIG_PANIC_ON_OOPS': ('n', 'Disable panic on oops for better debugging'),
            'CONFIG_DEBUG_KERNEL': ('n', 'Disable debug kernel for production systems'),
            'CONFIG_KASAN': ('n', 'Disable KASAN for production (performance impact)'),
        }
        
        for option, (recommended_value, description) in stability_options.items():
            if option in kernel_config.options:
                current_value = kernel_config.options[option].value
                if current_value != recommended_value:
                    recommendations.append({
                        'component': 'kernel',
                        'category': RecommendationCategory.STABILITY,
                        'priority': RecommendationPriority.LOW,
                        'action': f'Adjust {option}',
                        'details': f'{description}. Current: {current_value}, Recommended: {recommended_value}',
                        'impact': 'System stability optimization',
                        'urgency': 'when_convenient'
                    })
        
        return recommendations
    
    def _generate_log_recommendations(self, log_analysis: Optional[LogAnalysis]) -> List[Dict[str, Any]]:
        """Generate comprehensive log-based recommendations."""
        if not log_analysis:
            return []
        
        recommendations = []
        
        # Analyze log issues
        if log_analysis.issues and isinstance(log_analysis.issues, dict):
            for issue_category, issues in log_analysis.issues.items():
                if isinstance(issues, list):
                    for issue in issues:
                        recommendations.extend(self._analyze_log_issue(issue, issue_category))
        
        # Analyze log patterns
        if hasattr(log_analysis, 'patterns') and log_analysis.patterns:
            recommendations.extend(self._analyze_log_patterns(log_analysis.patterns))
        
        return recommendations
    
    def _analyze_log_issue(self, issue: Dict[str, Any], category: str) -> List[Dict[str, Any]]:
        """Analyze individual log issue and generate recommendations."""
        recommendations = []
        
        severity = issue.get('severity', 'medium')
        message = issue.get('message', 'Unknown issue')
        issue_type = issue.get('type', 'system')
        
        # Map severity to priority
        priority_map = {
            'critical': RecommendationPriority.CRITICAL,
            'high': RecommendationPriority.HIGH,
            'medium': RecommendationPriority.MEDIUM,
            'low': RecommendationPriority.LOW
        }
        
        priority = priority_map.get(severity, RecommendationPriority.MEDIUM)
        
        # Generate specific recommendations based on issue type
        if 'memory' in message.lower() or 'oom' in message.lower():
            recommendations.append({
                'component': 'system',
                'category': RecommendationCategory.STABILITY,
                'priority': priority,
                'action': 'Address memory issues',
                'details': f'Memory-related error detected: {message}',
                'impact': 'System stability at risk',
                'urgency': 'soon' if priority in [RecommendationPriority.CRITICAL, RecommendationPriority.HIGH] else 'when_convenient'
            })
        elif 'disk' in message.lower() or 'i/o' in message.lower():
            recommendations.append({
                'component': 'system',
                'category': RecommendationCategory.STABILITY,
                'priority': priority,
                'action': 'Investigate storage issues',
                'details': f'Storage-related error detected: {message}',
                'impact': 'Data integrity at risk',
                'urgency': 'soon' if priority in [RecommendationPriority.CRITICAL, RecommendationPriority.HIGH] else 'when_convenient'
            })
        elif 'network' in message.lower() or 'connection' in message.lower():
            recommendations.append({
                'component': 'system',
                'category': RecommendationCategory.STABILITY,
                'priority': priority,
                'action': 'Check network connectivity',
                'details': f'Network-related error detected: {message}',
                'impact': 'Network functionality affected',
                'urgency': 'when_convenient'
            })
        else:
            recommendations.append({
                'component': 'system',
                'category': RecommendationCategory.STABILITY,
                'priority': priority,
                'action': f'Address {issue_type} issue',
                'details': message,
                'impact': 'System stability may be affected',
                'urgency': 'when_convenient'
            })
        
        return recommendations
    
    def _analyze_log_patterns(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze log patterns and generate recommendations."""
        recommendations = []
        
        # Analyze error frequency patterns
        error_patterns = patterns.get('error_frequency', {})
        recommendations.extend(self._analyze_error_frequency(error_patterns))
        
        return recommendations
    
    def _analyze_error_frequency(self, error_patterns: Dict[str, int]) -> List[Dict[str, Any]]:
        """Analyze error frequency patterns."""
        recommendations = []
        
        for error_type, frequency in error_patterns.items():
            if frequency > RecommendationConfig.ERROR_FREQUENCY_THRESHOLD:
                recommendations.append({
                    'component': 'system',
                    'category': RecommendationCategory.STABILITY,
                    'priority': RecommendationPriority.MEDIUM,
                    'action': f'Investigate recurring {error_type} errors',
                    'details': f'Detected {frequency} occurrences of {error_type} errors. This may indicate a systemic issue.',
                    'impact': 'System reliability concern',
                    'urgency': 'soon'
                })
        
        return recommendations
    
    def _generate_system_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Generate system-wide recommendations."""
        recommendations = []
        
        # Cross-module analysis
        if diagnostic.hardware and diagnostic.kernel_config:
            recommendations.extend(self._check_hardware_kernel_compatibility(
                diagnostic.hardware, diagnostic.kernel_config
            ))
        
        return recommendations
    
    def _check_hardware_kernel_compatibility(
        self, 
        hardware: HardwareInfo, 
        kernel_config: KernelConfig
    ) -> List[Dict[str, Any]]:
        """Check compatibility between hardware and kernel configuration."""
        recommendations = []
        
        # Graphics driver recommendations
        if hasattr(hardware, 'graphics') and hardware.graphics:
            vendor = getattr(hardware.graphics, 'vendor', '').lower()
            if 'nvidia' in vendor:
                recommendations.append({
                    'component': 'kernel',
                    'priority': 'medium',
                    'action': 'Verify NVIDIA driver configuration',
                    'details': 'Ensure appropriate NVIDIA drivers are configured for optimal performance',
                    'impact': 'performance'
                })
            elif 'amd' in vendor:
                recommendations.append({
                    'component': 'kernel',
                    'priority': 'medium',
                    'action': 'Verify AMD driver configuration',
                    'details': 'Ensure appropriate AMD drivers are configured for optimal performance',
                    'impact': 'performance'
                })
        
        return recommendations
    
    def _prioritize_recommendations(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize recommendations by severity and impact."""
        all_recommendations = []
        
        for category, recs in recommendations.items():
            if isinstance(recs, list):
                for rec in recs:
                    rec['category'] = category
                    all_recommendations.append(rec)
        
        # Sort by priority weight and impact
        def sort_key(rec):
            priority_weight = self.priority_weights.get(rec.get('priority', 'medium'), 2)
            impact_weight = {'security': 3, 'stability': 2, 'performance': 1}.get(
                rec.get('impact', 'performance'), 1
            )
            return (priority_weight, impact_weight)
        
        all_recommendations.sort(key=sort_key, reverse=True)
        return all_recommendations
    
    def _generate_recommendation_summary(self, prioritized_recommendations: List[Dict[str, Any]]) -> str:
        """Generate a summary of recommendations."""
        if not prioritized_recommendations:
            return "No specific recommendations at this time. System appears to be running well."
        
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for rec in prioritized_recommendations:
            priority = rec.get('priority', 'medium')
            counts[priority] = counts.get(priority, 0) + 1
        
        summary_parts = []
        if counts['critical']:
            summary_parts.append(f"{counts['critical']} critical-priority issues require immediate attention")
        if counts['high']:
            summary_parts.append(f"{counts['high']} high-priority issues require immediate attention")
        if counts['medium']:
            summary_parts.append(f"{counts['medium']} medium-priority optimizations available")
        if counts['low']:
            summary_parts.append(f"{counts['low']} low-priority improvements suggested")
        
        return "; ".join(summary_parts)
    
    def _generate_security_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Generate security-focused recommendations."""
        recommendations = []
        
        # Check for security-related log entries
        if diagnostic.log_analysis and diagnostic.log_analysis.issues:
            for issue_category, issues in diagnostic.log_analysis.issues.items():
                if isinstance(issues, list):
                    for issue in issues:
                        message = issue.get('message', '').lower()
                        if any(sec_term in message for sec_term in ['authentication', 'failed login', 'security', 'breach']):
                            recommendations.append({
                                'component': 'security',
                                'category': RecommendationCategory.SECURITY,
                                'priority': RecommendationPriority.HIGH,
                                'action': 'Review security logs',
                                'details': f'Security-related event detected: {issue.get("message", "Unknown")}',
                                'impact': 'Security posture assessment needed',
                                'urgency': 'soon'
                            })
        
        # General security recommendations
        recommendations.append({
            'component': 'security',
            'category': RecommendationCategory.SECURITY,
            'priority': RecommendationPriority.MEDIUM,
            'action': 'Regular security updates',
            'details': 'Ensure system packages are regularly updated to patch security vulnerabilities.',
            'impact': 'Maintain security posture',
            'urgency': 'ongoing'
        })
        
        return recommendations
    
    def _generate_performance_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Generate performance-focused recommendations."""
        recommendations = []
        
        # CPU performance recommendations
        if diagnostic.hardware and diagnostic.hardware.cpu:
            cpu_info = diagnostic.hardware.cpu
            if isinstance(cpu_info, dict):
                load_avg = cpu_info.get('load_avg_1min')
                cores = cpu_info.get('cores', 1)
                if load_avg and cores and (load_avg / cores) > 1.5:
                    recommendations.append({
                        'component': 'performance',
                        'category': RecommendationCategory.PERFORMANCE,
                        'priority': RecommendationPriority.MEDIUM,
                        'action': 'Optimize CPU usage',
                        'details': f'High CPU load detected ({load_avg:.2f} on {cores} cores). Consider process optimization.',
                        'impact': 'System responsiveness improvement',
                        'urgency': 'when_convenient'
                    })
        
        # Memory performance recommendations
        if diagnostic.hardware and diagnostic.hardware.memory:
            memory_info = diagnostic.hardware.memory
            if isinstance(memory_info, dict):
                usage_percent = memory_info.get('usage_percent')
                if usage_percent and usage_percent > 70:
                    recommendations.append({
                        'component': 'performance',
                        'category': RecommendationCategory.PERFORMANCE,
                        'priority': RecommendationPriority.MEDIUM,
                        'action': 'Optimize memory usage',
                        'details': f'Memory usage is {usage_percent}%. Consider memory optimization or upgrade.',
                        'impact': 'System performance improvement',
                        'urgency': 'when_convenient'
                    })
        
        return recommendations
    
    def _generate_maintenance_recommendations(self, diagnostic: Diagnostic) -> List[Dict[str, Any]]:
        """Generate maintenance-focused recommendations."""
        recommendations = []
        
        # Regular maintenance tasks
        recommendations.extend([
            {
                'component': 'maintenance',
                'category': RecommendationCategory.MAINTENANCE,
                'priority': RecommendationPriority.LOW,
                'action': 'Schedule regular system cleanup',
                'details': 'Regularly clean temporary files, logs, and package cache to maintain system health.',
                'impact': 'Prevent storage issues and maintain performance',
                'urgency': 'ongoing'
            },
            {
                'component': 'maintenance',
                'category': RecommendationCategory.MAINTENANCE,
                'priority': RecommendationPriority.LOW,
                'action': 'Monitor system logs regularly',
                'details': 'Regular log monitoring helps identify issues before they become critical.',
                'impact': 'Proactive issue detection',
                'urgency': 'ongoing'
            },
            {
                'component': 'maintenance',
                'category': RecommendationCategory.MAINTENANCE,
                'priority': RecommendationPriority.LOW,
                'action': 'Backup important data',
                'details': 'Regular backups protect against data loss from hardware failures or security incidents.',
                'impact': 'Data protection',
                'urgency': 'ongoing'
            }
        ])
        
        return recommendations
    
    def _deduplicate_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate recommendations based on action and component."""
        seen_keys = set()
        deduplicated = []
        
        for rec in recommendations:
            # Create a more comprehensive key for deduplication
            key = (
                rec.get('component', ''),
                rec.get('action', ''),
                rec.get('category', ''),
                rec.get('priority', '')
            )
            
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(rec)
            else:
                # If we have a duplicate, keep the one with higher priority
                existing_rec = next((r for r in deduplicated 
                                   if (r.get('component', ''), r.get('action', ''), 
                                       r.get('category', ''), r.get('priority', '')) == key), None)
                if existing_rec:
                    current_priority_weight = self.priority_weights.get(rec.get('priority', 'medium'), 2)
                    existing_priority_weight = self.priority_weights.get(existing_rec.get('priority', 'medium'), 2)
                    
                    if current_priority_weight > existing_priority_weight:
                        deduplicated.remove(existing_rec)
                        deduplicated.append(rec)
        
        return deduplicated
    
    def _add_explanations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add detailed explanations to recommendations."""
        for rec in recommendations:
            if 'explanation' not in rec:
                rec['explanation'] = self._generate_explanation(rec)
        
        return recommendations
    
    def _generate_explanation(self, recommendation: Dict[str, Any]) -> str:
        """Generate detailed explanation for a recommendation."""
        component = recommendation.get('component', 'system')
        action = recommendation.get('action', 'unknown action')
        details = recommendation.get('details', '')
        impact = recommendation.get('impact', '')
        
        explanation_parts = []
        
        # Why this recommendation is important
        explanation_parts.append(f"This recommendation addresses {component} optimization.")
        
        if details:
            explanation_parts.append(f"Issue: {details}")
        
        if impact:
            explanation_parts.append(f"Impact: {impact}")
        
        # Add urgency context
        urgency = recommendation.get('urgency', 'when_convenient')
        urgency_text = {
            'immediate': 'This should be addressed immediately to prevent system issues.',
            'soon': 'This should be addressed in the near future to maintain system health.',
            'when_convenient': 'This can be addressed when convenient as part of regular maintenance.',
            'ongoing': 'This is an ongoing maintenance task that should be performed regularly.'
        }
        
        if urgency in urgency_text:
            explanation_parts.append(urgency_text[urgency])
        
        return ' '.join(explanation_parts)
    
    def _generate_implementation_guides(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate implementation guides for top recommendations."""
        guides = []
        
        for rec in recommendations:
            guide = {
                'recommendation_id': f"{rec.get('component')}_{rec.get('action', '').replace(' ', '_').lower()}",
                'title': rec.get('action', 'Unknown Action'),
                'steps': self._generate_implementation_steps(rec),
                'estimated_time': self._estimate_implementation_time(rec),
                'difficulty': self._assess_implementation_difficulty(rec),
                'prerequisites': self._identify_prerequisites(rec),
                'risks': self._identify_risks(rec)
            }
            guides.append(guide)
        
        return guides
    
    def _generate_implementation_steps(self, recommendation: Dict[str, Any]) -> List[str]:
        """Generate step-by-step implementation guide."""
        component = recommendation.get('component', 'system')
        action = recommendation.get('action', '').lower()
        
        # Generate context-specific steps
        if 'cpu' in component and 'cooling' in action:
            return [
                "1. Monitor CPU temperature using sensors or system monitoring tools",
                "2. Check CPU fan operation and clean if necessary",
                "3. Verify thermal paste application on CPU",
                "4. Ensure proper case airflow and ventilation",
                "5. Consider upgrading CPU cooler if temperatures remain high"
            ]
        elif 'memory' in component and 'usage' in action:
            return [
                "1. Identify memory-intensive processes using top or htop",
                "2. Close unnecessary applications and services",
                "3. Check for memory leaks in running applications",
                "4. Consider adding more RAM if usage consistently high",
                "5. Optimize system services and startup programs"
            ]
        elif 'storage' in component and 'space' in action:
            return [
                "1. Identify large files and directories using du command",
                "2. Clean temporary files and system cache",
                "3. Remove old log files and rotate logs properly",
                "4. Uninstall unused packages and clean package cache",
                "5. Consider moving large files to external storage"
            ]
        else:
            return [
                "1. Review the specific issue details",
                "2. Research appropriate solutions for your system",
                "3. Test changes in a safe environment if possible",
                "4. Implement the recommended changes",
                "5. Monitor system behavior after changes"
            ]
    
    def _estimate_implementation_time(self, recommendation: Dict[str, Any]) -> str:
        """Estimate time required to implement recommendation."""
        priority = recommendation.get('priority', RecommendationPriority.MEDIUM)
        component = recommendation.get('component', 'system')
        
        if priority == RecommendationPriority.CRITICAL:
            return "15-30 minutes"
        elif priority == RecommendationPriority.HIGH:
            return "30-60 minutes"
        elif component in ['kernel', 'security']:
            return "1-2 hours"
        else:
            return "15-45 minutes"
    
    def _assess_implementation_difficulty(self, recommendation: Dict[str, Any]) -> str:
        """Assess difficulty level of implementing recommendation."""
        component = recommendation.get('component', 'system')
        action = recommendation.get('action', '').lower()
        
        if component == 'kernel' or 'configuration' in action:
            return "Advanced"
        elif component in ['security', 'performance']:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _identify_prerequisites(self, recommendation: Dict[str, Any]) -> List[str]:
        """Identify prerequisites for implementing recommendation."""
        component = recommendation.get('component', 'system')
        action = recommendation.get('action', '').lower()
        
        prerequisites = ["Administrative/root access to the system"]
        
        if component == 'kernel':
            prerequisites.extend([
                "Understanding of kernel configuration",
                "Ability to recompile kernel (if needed)",
                "System backup before making changes"
            ])
        elif 'hardware' in component:
            prerequisites.extend([
                "Physical access to the system",
                "Basic hardware troubleshooting knowledge"
            ])
        elif component == 'security':
            prerequisites.extend([
                "Understanding of security implications",
                "Knowledge of system security policies"
            ])
        
        return prerequisites
    
    def _identify_risks(self, recommendation: Dict[str, Any]) -> List[str]:
        """Identify potential risks of implementing recommendation."""
        component = recommendation.get('component', 'system')
        priority = recommendation.get('priority', RecommendationPriority.MEDIUM)
        
        risks = []
        
        if component == 'kernel':
            risks.extend([
                "System may fail to boot if kernel configuration is incorrect",
                "Some hardware may not function properly with new configuration",
                "Performance impact during kernel recompilation"
            ])
        elif component == 'security':
            risks.extend([
                "Some applications may be blocked by enhanced security",
                "User workflow may be affected by security changes",
                "System access may be restricted"
            ])
        elif priority == RecommendationPriority.CRITICAL:
            risks.append("Delaying implementation may lead to system instability")
        else:
            risks.append("Minimal risk - changes can typically be reverted if needed")
        
        return risks
    
    def _generate_recommendation_statistics(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about recommendations."""
        if not recommendations:
            return {}
        
        # Count by priority
        priority_counts = {}
        for rec in recommendations:
            priority = rec.get('priority', RecommendationPriority.MEDIUM)
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Count by category
        category_counts = {}
        for rec in recommendations:
            category = rec.get('category', 'unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count by component
        component_counts = {}
        for rec in recommendations:
            component = rec.get('component', 'unknown')
            component_counts[component] = component_counts.get(component, 0) + 1
        
        # Count by urgency
        urgency_counts = {}
        for rec in recommendations:
            urgency = rec.get('urgency', 'when_convenient')
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        
        return {
            'total_recommendations': len(recommendations),
            'by_priority': priority_counts,
            'by_category': category_counts,
            'by_component': component_counts,
            'by_urgency': urgency_counts,
            'critical_count': priority_counts.get(RecommendationPriority.CRITICAL, 0),
            'high_priority_count': priority_counts.get(RecommendationPriority.HIGH, 0)
        }
    
    def _load_recommendation_rules(self) -> Dict[str, Any]:
        """Load recommendation rules and patterns."""
        return {
            'temperature_thresholds': {
                'cpu_critical': 85,
                'cpu_high': 75,
                'cpu_normal': 65
            },
            'usage_thresholds': {
                'memory_critical': 95,
                'memory_high': 85,
                'disk_critical': 95,
                'disk_high': 85,
                'cpu_load_high': 2.0
            },
            'security_patterns': [
                'authentication failed',
                'security violation',
                'unauthorized access',
                'failed login'
            ],
            'performance_patterns': [
                'high load',
                'slow response',
                'timeout',
                'performance degradation'
            ]
        }