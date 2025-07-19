#!/usr/bin/env python3
"""Kernel Configuration Analyzer Module.

This module provides kernel configuration analysis capabilities including
security-related configuration options and performance optimization detection.

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

from typing import Any, Dict, List, Optional, Set

from ..interfaces import KernelConfig, KernelConfigOption, SystemInterface
from ..system import LinuxSystemInterface


class KernelConfigAnalyzer:
    """Kernel configuration analyzer for security and performance analysis."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize kernel configuration analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # Security-related configuration options
        self.security_options = self._get_security_options()
        
        # Performance-related configuration options
        self.performance_options = self._get_performance_options()
    
    def analyze_config(self, config: KernelConfig) -> Dict[str, Any]:
        """Analyze kernel configuration for security and performance issues.
        
        Args:
            config: Kernel configuration to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        analysis = {}
        
        # Analyze security-related configuration options
        security_analysis = self._analyze_security_options(config)
        analysis['security'] = security_analysis
        
        # Analyze performance-related configuration options
        performance_analysis = self._analyze_performance_options(config)
        analysis['performance'] = performance_analysis
        
        # Calculate overall scores
        analysis['security_score'] = self._calculate_security_score(security_analysis)
        analysis['performance_score'] = self._calculate_performance_score(performance_analysis)
        
        # Update kernel config with analysis results
        config.analysis = analysis
        
        return analysis
    
    def _analyze_security_options(self, config: KernelConfig) -> Dict[str, Any]:
        """Analyze security-related configuration options.
        
        Args:
            config: Kernel configuration to analyze
            
        Returns:
            Dictionary containing security analysis results
        """
        analysis = {
            'issues': [],
            'recommendations': [],
            'good_practices': []
        }
        
        # Check for missing security options
        for category, options in self.security_options.items():
            for option_name, option_data in options.items():
                recommended_value = option_data['recommended']
                description = option_data['description']
                impact = option_data['impact']
                
                # Check if option exists in config
                if option_name in config.options:
                    current_value = config.options[option_name].value
                    
                    # Update option with security impact
                    config.options[option_name].security_impact = impact
                    
                    # Check if option value matches recommended value
                    if self._is_value_compliant(current_value, recommended_value):
                        analysis['good_practices'].append({
                            'option': option_name,
                            'value': current_value,
                            'description': description,
                            'category': category
                        })
                    else:
                        analysis['issues'].append({
                            'option': option_name,
                            'current_value': current_value,
                            'recommended_value': recommended_value,
                            'description': description,
                            'impact': impact,
                            'category': category
                        })
                        
                        analysis['recommendations'].append({
                            'option': option_name,
                            'current_value': current_value,
                            'recommended_value': recommended_value,
                            'description': f"Set {option_name}={recommended_value} for better security: {description}",
                            'impact': impact,
                            'category': category
                        })
                else:
                    # Option is missing from config
                    analysis['issues'].append({
                        'option': option_name,
                        'current_value': 'missing',
                        'recommended_value': recommended_value,
                        'description': description,
                        'impact': impact,
                        'category': category
                    })
                    
                    analysis['recommendations'].append({
                        'option': option_name,
                        'current_value': 'missing',
                        'recommended_value': recommended_value,
                        'description': f"Add {option_name}={recommended_value} for better security: {description}",
                        'impact': impact,
                        'category': category
                    })
        
        return analysis
    
    def _analyze_performance_options(self, config: KernelConfig) -> Dict[str, Any]:
        """Analyze performance-related configuration options.
        
        Args:
            config: Kernel configuration to analyze
            
        Returns:
            Dictionary containing performance analysis results
        """
        analysis = {
            'issues': [],
            'recommendations': [],
            'good_practices': []
        }
        
        # Check for suboptimal performance options
        for category, options in self.performance_options.items():
            for option_name, option_data in options.items():
                recommended_value = option_data['recommended']
                description = option_data['description']
                impact = option_data['impact']
                
                # Check if option exists in config
                if option_name in config.options:
                    current_value = config.options[option_name].value
                    
                    # Update option with performance impact
                    config.options[option_name].performance_impact = impact
                    
                    # Check if option value matches recommended value
                    if self._is_value_compliant(current_value, recommended_value):
                        analysis['good_practices'].append({
                            'option': option_name,
                            'value': current_value,
                            'description': description,
                            'category': category
                        })
                    else:
                        analysis['issues'].append({
                            'option': option_name,
                            'current_value': current_value,
                            'recommended_value': recommended_value,
                            'description': description,
                            'impact': impact,
                            'category': category
                        })
                        
                        analysis['recommendations'].append({
                            'option': option_name,
                            'current_value': current_value,
                            'recommended_value': recommended_value,
                            'description': f"Set {option_name}={recommended_value} for better performance: {description}",
                            'impact': impact,
                            'category': category
                        })
                else:
                    # Option is missing from config
                    analysis['issues'].append({
                        'option': option_name,
                        'current_value': 'missing',
                        'recommended_value': recommended_value,
                        'description': description,
                        'impact': impact,
                        'category': category
                    })
                    
                    analysis['recommendations'].append({
                        'option': option_name,
                        'current_value': 'missing',
                        'recommended_value': recommended_value,
                        'description': f"Add {option_name}={recommended_value} for better performance: {description}",
                        'impact': impact,
                        'category': category
                    })
        
        return analysis
    
    def _calculate_security_score(self, security_analysis: Dict[str, Any]) -> int:
        """Calculate security score based on security analysis.
        
        Args:
            security_analysis: Security analysis results
            
        Returns:
            Security score (0-100)
        """
        # Count total security options
        total_options = len(security_analysis['issues']) + len(security_analysis['good_practices'])
        if total_options == 0:
            return 0
        
        # Calculate score based on good practices
        good_practices = len(security_analysis['good_practices'])
        score = int((good_practices / total_options) * 100)
        
        return score
    
    def _calculate_performance_score(self, performance_analysis: Dict[str, Any]) -> int:
        """Calculate performance score based on performance analysis.
        
        Args:
            performance_analysis: Performance analysis results
            
        Returns:
            Performance score (0-100)
        """
        # Count total performance options
        total_options = len(performance_analysis['issues']) + len(performance_analysis['good_practices'])
        if total_options == 0:
            return 0
        
        # Calculate score based on good practices
        good_practices = len(performance_analysis['good_practices'])
        score = int((good_practices / total_options) * 100)
        
        return score
    
    def _is_value_compliant(self, current_value: str, recommended_value: str) -> bool:
        """Check if current value is compliant with recommended value.
        
        Args:
            current_value: Current value
            recommended_value: Recommended value
            
        Returns:
            True if compliant, False otherwise
        """
        # Exact match
        if current_value == recommended_value:
            return True
        
        # Boolean values
        if recommended_value == 'y' and current_value in ['y', '1', 'yes', 'true']:
            return True
        if recommended_value == 'n' and current_value in ['n', '0', 'no', 'false']:
            return True
        
        # Numeric values with minimum requirement
        if recommended_value.startswith('>='):
            try:
                min_value = int(recommended_value[2:])
                current_int = int(current_value)
                return current_int >= min_value
            except ValueError:
                pass
        
        # Numeric values with maximum requirement
        if recommended_value.startswith('<='):
            try:
                max_value = int(recommended_value[2:])
                current_int = int(current_value)
                return current_int <= max_value
            except ValueError:
                pass
        
        return False
    
    def _get_security_options(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get security-related configuration options.
        
        Returns:
            Dictionary of security-related configuration options
        """
        return {
            'kernel_hardening': {
                'CONFIG_SECURITY': {
                    'recommended': 'y',
                    'description': 'Enable different security models',
                    'impact': 'high'
                },
                'CONFIG_SECURITY_SELINUX': {
                    'recommended': 'y',
                    'description': 'NSA SELinux Support',
                    'impact': 'high'
                },
                'CONFIG_SECURITY_SMACK': {
                    'recommended': 'y',
                    'description': 'Simplified Mandatory Access Control Kernel Support',
                    'impact': 'medium'
                },
                'CONFIG_SECURITY_APPARMOR': {
                    'recommended': 'y',
                    'description': 'AppArmor support',
                    'impact': 'high'
                },
                'CONFIG_SECURITY_YAMA': {
                    'recommended': 'y',
                    'description': 'Yama support',
                    'impact': 'medium'
                },
                'CONFIG_HARDENED_USERCOPY': {
                    'recommended': 'y',
                    'description': 'Hardened usercopy',
                    'impact': 'high'
                },
                'CONFIG_SLAB_FREELIST_RANDOM': {
                    'recommended': 'y',
                    'description': 'Randomize slab freelist',
                    'impact': 'medium'
                },
                'CONFIG_SLAB_FREELIST_HARDENED': {
                    'recommended': 'y',
                    'description': 'Harden slab freelist metadata',
                    'impact': 'medium'
                }
            },
            'memory_protection': {
                'CONFIG_PAGE_TABLE_ISOLATION': {
                    'recommended': 'y',
                    'description': 'Kernel page table isolation (KPTI)',
                    'impact': 'high'
                },
                'CONFIG_RANDOMIZE_BASE': {
                    'recommended': 'y',
                    'description': 'Randomize the address of the kernel image (KASLR)',
                    'impact': 'high'
                },
                'CONFIG_RANDOMIZE_MEMORY': {
                    'recommended': 'y',
                    'description': 'Randomize the memory layout',
                    'impact': 'medium'
                },
                'CONFIG_STRICT_KERNEL_RWX': {
                    'recommended': 'y',
                    'description': 'Make kernel text and rodata read-only',
                    'impact': 'high'
                },
                'CONFIG_STRICT_MODULE_RWX': {
                    'recommended': 'y',
                    'description': 'Set loadable kernel module data as NX and text as RO',
                    'impact': 'high'
                }
            },
            'exploit_mitigations': {
                'CONFIG_STACKPROTECTOR': {
                    'recommended': 'y',
                    'description': 'Stack Protector buffer overflow detection',
                    'impact': 'high'
                },
                'CONFIG_STACKPROTECTOR_STRONG': {
                    'recommended': 'y',
                    'description': 'Strong Stack Protector',
                    'impact': 'high'
                },
                'CONFIG_VMAP_STACK': {
                    'recommended': 'y',
                    'description': 'Use a virtually mapped stack',
                    'impact': 'medium'
                },
                'CONFIG_REFCOUNT_FULL': {
                    'recommended': 'y',
                    'description': 'Full reference count validation',
                    'impact': 'medium'
                },
                'CONFIG_FORTIFY_SOURCE': {
                    'recommended': 'y',
                    'description': 'Detect buffer overflows',
                    'impact': 'high'
                }
            },
            'network_security': {
                'CONFIG_SYN_COOKIES': {
                    'recommended': 'y',
                    'description': 'TCP SYN cookie protection',
                    'impact': 'high'
                },
                'CONFIG_INET_DIAG': {
                    'recommended': 'n',
                    'description': 'INET socket monitoring interface',
                    'impact': 'low'
                },
                'CONFIG_PACKET_DIAG': {
                    'recommended': 'n',
                    'description': 'Packet socket monitoring interface',
                    'impact': 'low'
                },
                'CONFIG_UNIX_DIAG': {
                    'recommended': 'n',
                    'description': 'UNIX socket monitoring interface',
                    'impact': 'low'
                }
            }
        }
    
    def _get_performance_options(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get performance-related configuration options.
        
        Returns:
            Dictionary of performance-related configuration options
        """
        return {
            'cpu_scheduling': {
                'CONFIG_PREEMPT': {
                    'recommended': 'y',
                    'description': 'Preemptible Kernel (Low-Latency Desktop)',
                    'impact': 'high'
                },
                'CONFIG_HZ': {
                    'recommended': '1000',
                    'description': 'Timer frequency',
                    'impact': 'medium'
                },
                'CONFIG_HZ_1000': {
                    'recommended': 'y',
                    'description': '1000 Hz tick rate',
                    'impact': 'medium'
                },
                'CONFIG_SCHED_AUTOGROUP': {
                    'recommended': 'y',
                    'description': 'Automatic process group scheduling',
                    'impact': 'medium'
                }
            },
            'memory_management': {
                'CONFIG_TRANSPARENT_HUGEPAGE': {
                    'recommended': 'y',
                    'description': 'Transparent Hugepage Support',
                    'impact': 'high'
                },
                'CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS': {
                    'recommended': 'n',
                    'description': 'Transparent Hugepage: always',
                    'impact': 'medium'
                },
                'CONFIG_TRANSPARENT_HUGEPAGE_MADVISE': {
                    'recommended': 'y',
                    'description': 'Transparent Hugepage: madvise',
                    'impact': 'medium'
                },
                'CONFIG_CLEANCACHE': {
                    'recommended': 'y',
                    'description': 'Enable cleancache driver to cache clean pages',
                    'impact': 'medium'
                },
                'CONFIG_FRONTSWAP': {
                    'recommended': 'y',
                    'description': 'Enable frontswap to cache swap pages',
                    'impact': 'medium'
                }
            },
            'io_performance': {
                'CONFIG_BLK_CGROUP': {
                    'recommended': 'y',
                    'description': 'Block IO controller',
                    'impact': 'medium'
                },
                'CONFIG_BFQ_GROUP_IOSCHED': {
                    'recommended': 'y',
                    'description': 'BFQ I/O scheduler',
                    'impact': 'medium'
                },
                'CONFIG_IOSCHED_BFQ': {
                    'recommended': 'y',
                    'description': 'BFQ I/O scheduler',
                    'impact': 'medium'
                },
                'CONFIG_MQ_IOSCHED_DEADLINE': {
                    'recommended': 'y',
                    'description': 'MQ deadline I/O scheduler',
                    'impact': 'medium'
                },
                'CONFIG_MQ_IOSCHED_KYBER': {
                    'recommended': 'y',
                    'description': 'Kyber I/O scheduler',
                    'impact': 'medium'
                }
            },
            'power_management': {
                'CONFIG_CPU_FREQ': {
                    'recommended': 'y',
                    'description': 'CPU frequency scaling',
                    'impact': 'high'
                },
                'CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE': {
                    'recommended': 'y',
                    'description': 'Performance governor as default',
                    'impact': 'high'
                },
                'CONFIG_CPU_FREQ_GOV_ONDEMAND': {
                    'recommended': 'y',
                    'description': 'Ondemand governor',
                    'impact': 'medium'
                },
                'CONFIG_CPU_FREQ_GOV_CONSERVATIVE': {
                    'recommended': 'y',
                    'description': 'Conservative governor',
                    'impact': 'low'
                },
                'CONFIG_CPU_FREQ_GOV_SCHEDUTIL': {
                    'recommended': 'y',
                    'description': 'Schedutil governor',
                    'impact': 'high'
                }
            }
        }