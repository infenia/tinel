#!/usr/bin/env python3
"""Kernel Optimization Module.

This module provides kernel optimization recommendations based on hardware
profile and best practices comparison.

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

from typing import Any, Dict, List, Optional, Set, Tuple

from ..interfaces import HardwareInfo, KernelConfig, SystemInterface
from ..system import LinuxSystemInterface


class KernelOptimizer:
    """Kernel optimization recommendation engine."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize kernel optimizer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # Best practices for different hardware profiles
        self.best_practices = self._get_best_practices()
    
    def get_recommendations(self, config: KernelConfig, hardware: HardwareInfo) -> Dict[str, Any]:
        """Get optimization recommendations based on hardware profile.
        
        Args:
            config: Kernel configuration to analyze
            hardware: Hardware information
            
        Returns:
            Dictionary containing optimization recommendations
        """
        recommendations = {
            'general': [],
            'cpu': [],
            'memory': [],
            'storage': [],
            'network': [],
            'graphics': []
        }
        
        # Get hardware profile
        profile = self._determine_hardware_profile(hardware)
        
        # Get best practices for the hardware profile
        best_practices = self._get_profile_best_practices(profile)
        
        # Compare current configuration with best practices
        for category, options in best_practices.items():
            for option_name, option_data in options.items():
                recommended_value = option_data['value']
                description = option_data['description']
                reason = option_data['reason']
                
                # Check if option exists in config
                if option_name in config.options:
                    current_value = config.options[option_name].value
                    
                    # Check if option value matches recommended value
                    if not self._is_value_compliant(current_value, recommended_value):
                        recommendations[category].append({
                            'option': option_name,
                            'current_value': current_value,
                            'recommended_value': recommended_value,
                            'description': description,
                            'reason': reason,
                            'command': self._get_change_command(option_name, recommended_value)
                        })
                else:
                    # Option is missing from config
                    recommendations[category].append({
                        'option': option_name,
                        'current_value': 'missing',
                        'recommended_value': recommended_value,
                        'description': description,
                        'reason': reason,
                        'command': self._get_add_command(option_name, recommended_value)
                    })
        
        # Add sysctl recommendations
        sysctl_recommendations = self._get_sysctl_recommendations(hardware)
        for category, recs in sysctl_recommendations.items():
            recommendations[category].extend(recs)
        
        # Update kernel config with recommendations
        config.recommendations = recommendations
        
        return recommendations
    
    def _determine_hardware_profile(self, hardware: HardwareInfo) -> Dict[str, str]:
        """Determine hardware profile based on hardware information.
        
        Args:
            hardware: Hardware information
            
        Returns:
            Dictionary containing hardware profile
        """
        profile = {
            'system_type': 'desktop',  # Default to desktop
            'cpu_cores': 'multi',      # Default to multi-core
            'memory_size': 'medium',   # Default to medium memory
            'storage_type': 'hdd',     # Default to HDD
            'network_type': 'ethernet',  # Default to ethernet
            'graphics_type': 'integrated'  # Default to integrated graphics
        }
        
        # Determine system type
        if 'server' in hardware.cpu.get('model_name', '').lower():
            profile['system_type'] = 'server'
        elif 'mobile' in hardware.cpu.get('model_name', '').lower():
            profile['system_type'] = 'laptop'
        
        # Determine CPU cores
        cpu_cores = hardware.cpu.get('logical_cpus', 1)
        if cpu_cores == 1:
            profile['cpu_cores'] = 'single'
        elif cpu_cores <= 4:
            profile['cpu_cores'] = 'few'
        elif cpu_cores <= 16:
            profile['cpu_cores'] = 'multi'
        else:
            profile['cpu_cores'] = 'many'
        
        # Determine memory size
        memory_gb = hardware.memory.get('memory_total_gb', 4)
        if memory_gb < 4:
            profile['memory_size'] = 'small'
        elif memory_gb <= 16:
            profile['memory_size'] = 'medium'
        elif memory_gb <= 64:
            profile['memory_size'] = 'large'
        else:
            profile['memory_size'] = 'very_large'
        
        # Determine storage type
        for disk in hardware.storage.get('disks', []):
            if disk.get('is_ssd', False):
                profile['storage_type'] = 'ssd'
                break
            if 'nvme' in disk.get('name', '').lower():
                profile['storage_type'] = 'nvme'
                break
        
        # Determine network type
        for interface in hardware.network.get('interfaces', []):
            if interface.get('type', '') == 'wireless':
                profile['network_type'] = 'wireless'
                break
        
        # Determine graphics type
        for gpu in hardware.graphics.get('gpus', []):
            if gpu.get('vendor', '') in ['NVIDIA', 'AMD']:
                profile['graphics_type'] = 'dedicated'
                break
        
        return profile
    
    def _get_profile_best_practices(self, profile: Dict[str, str]) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get best practices for a specific hardware profile.
        
        Args:
            profile: Hardware profile
            
        Returns:
            Dictionary containing best practices for the hardware profile
        """
        best_practices = {
            'general': {},
            'cpu': {},
            'memory': {},
            'storage': {},
            'network': {},
            'graphics': {}
        }
        
        # Add general best practices
        best_practices['general'].update(self.best_practices['general'])
        
        # Add CPU best practices based on profile
        if profile['cpu_cores'] == 'single':
            best_practices['cpu'].update(self.best_practices['cpu_single'])
        elif profile['cpu_cores'] == 'few':
            best_practices['cpu'].update(self.best_practices['cpu_few'])
        elif profile['cpu_cores'] == 'multi':
            best_practices['cpu'].update(self.best_practices['cpu_multi'])
        else:  # many
            best_practices['cpu'].update(self.best_practices['cpu_many'])
        
        # Add memory best practices based on profile
        if profile['memory_size'] == 'small':
            best_practices['memory'].update(self.best_practices['memory_small'])
        elif profile['memory_size'] == 'medium':
            best_practices['memory'].update(self.best_practices['memory_medium'])
        elif profile['memory_size'] == 'large':
            best_practices['memory'].update(self.best_practices['memory_large'])
        else:  # very_large
            best_practices['memory'].update(self.best_practices['memory_very_large'])
        
        # Add storage best practices based on profile
        if profile['storage_type'] == 'hdd':
            best_practices['storage'].update(self.best_practices['storage_hdd'])
        elif profile['storage_type'] == 'ssd':
            best_practices['storage'].update(self.best_practices['storage_ssd'])
        else:  # nvme
            best_practices['storage'].update(self.best_practices['storage_nvme'])
        
        # Add network best practices based on profile
        if profile['network_type'] == 'ethernet':
            best_practices['network'].update(self.best_practices['network_ethernet'])
        else:  # wireless
            best_practices['network'].update(self.best_practices['network_wireless'])
        
        # Add graphics best practices based on profile
        if profile['graphics_type'] == 'integrated':
            best_practices['graphics'].update(self.best_practices['graphics_integrated'])
        else:  # dedicated
            best_practices['graphics'].update(self.best_practices['graphics_dedicated'])
        
        # Add system type best practices
        if profile['system_type'] == 'server':
            best_practices['general'].update(self.best_practices['system_server'])
            best_practices['cpu'].update(self.best_practices['cpu_server'])
            best_practices['memory'].update(self.best_practices['memory_server'])
            best_practices['storage'].update(self.best_practices['storage_server'])
            best_practices['network'].update(self.best_practices['network_server'])
        elif profile['system_type'] == 'laptop':
            best_practices['general'].update(self.best_practices['system_laptop'])
            best_practices['cpu'].update(self.best_practices['cpu_laptop'])
            best_practices['memory'].update(self.best_practices['memory_laptop'])
            best_practices['storage'].update(self.best_practices['storage_laptop'])
            best_practices['network'].update(self.best_practices['network_laptop'])
        else:  # desktop
            best_practices['general'].update(self.best_practices['system_desktop'])
            best_practices['cpu'].update(self.best_practices['cpu_desktop'])
            best_practices['memory'].update(self.best_practices['memory_desktop'])
            best_practices['storage'].update(self.best_practices['storage_desktop'])
            best_practices['network'].update(self.best_practices['network_desktop'])
        
        return best_practices
    
    def _get_sysctl_recommendations(self, hardware: HardwareInfo) -> Dict[str, List[Dict[str, str]]]:
        """Get sysctl recommendations based on hardware profile.
        
        Args:
            hardware: Hardware information
            
        Returns:
            Dictionary containing sysctl recommendations
        """
        recommendations = {
            'general': [],
            'cpu': [],
            'memory': [],
            'storage': [],
            'network': []
        }
        
        # Memory recommendations
        memory_gb = hardware.memory.get('memory_total_gb', 4)
        
        # VM swappiness
        if memory_gb < 4:
            recommendations['memory'].append({
                'option': 'vm.swappiness',
                'current_value': '60',  # Default value
                'recommended_value': '10',
                'description': 'Reduce swappiness for systems with limited memory',
                'reason': 'Reduces swap usage to improve performance on low-memory systems',
                'command': 'echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
            })
        elif memory_gb > 16:
            recommendations['memory'].append({
                'option': 'vm.swappiness',
                'current_value': '60',  # Default value
                'recommended_value': '10',
                'description': 'Reduce swappiness for systems with ample memory',
                'reason': 'Reduces swap usage to improve performance on high-memory systems',
                'command': 'echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
            })
        
        # VM dirty ratio
        if memory_gb > 16:
            recommendations['memory'].append({
                'option': 'vm.dirty_ratio',
                'current_value': '20',  # Default value
                'recommended_value': '10',
                'description': 'Reduce dirty ratio for systems with ample memory',
                'reason': 'Reduces the amount of dirty memory before forced writeback',
                'command': 'echo "vm.dirty_ratio=10" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
            })
            
            recommendations['memory'].append({
                'option': 'vm.dirty_background_ratio',
                'current_value': '10',  # Default value
                'recommended_value': '5',
                'description': 'Reduce dirty background ratio for systems with ample memory',
                'reason': 'Reduces the amount of dirty memory before background writeback',
                'command': 'echo "vm.dirty_background_ratio=5" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
            })
        
        # Network recommendations
        recommendations['network'].append({
            'option': 'net.core.rmem_max',
            'current_value': '212992',  # Default value
            'recommended_value': '16777216',
            'description': 'Increase maximum receive socket buffer size',
            'reason': 'Improves network performance for high-bandwidth connections',
            'command': 'echo "net.core.rmem_max=16777216" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
        })
        
        recommendations['network'].append({
            'option': 'net.core.wmem_max',
            'current_value': '212992',  # Default value
            'recommended_value': '16777216',
            'description': 'Increase maximum send socket buffer size',
            'reason': 'Improves network performance for high-bandwidth connections',
            'command': 'echo "net.core.wmem_max=16777216" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
        })
        
        # Storage recommendations
        if hardware.storage.get('storage_type', 'hdd') == 'ssd':
            recommendations['storage'].append({
                'option': 'vm.vfs_cache_pressure',
                'current_value': '100',  # Default value
                'recommended_value': '50',
                'description': 'Reduce VFS cache pressure for SSD systems',
                'reason': 'Keeps more VFS caches in memory to reduce disk I/O',
                'command': 'echo "vm.vfs_cache_pressure=50" | sudo tee -a /etc/sysctl.conf && sudo sysctl -p'
            })
        
        return recommendations
    
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
    
    def _get_change_command(self, option_name: str, recommended_value: str) -> str:
        """Get command to change kernel configuration option.
        
        Args:
            option_name: Option name
            recommended_value: Recommended value
            
        Returns:
            Command to change kernel configuration option
        """
        return f"echo '{option_name}={recommended_value}' | sudo tee -a /etc/modprobe.d/local.conf && sudo update-initramfs -u"
    
    def _get_add_command(self, option_name: str, recommended_value: str) -> str:
        """Get command to add kernel configuration option.
        
        Args:
            option_name: Option name
            recommended_value: Recommended value
            
        Returns:
            Command to add kernel configuration option
        """
        return f"echo '{option_name}={recommended_value}' | sudo tee -a /etc/modprobe.d/local.conf && sudo update-initramfs -u"
    
    def _get_best_practices(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Get best practices for different hardware profiles.
        
        Returns:
            Dictionary containing best practices for different hardware profiles
        """
        return {
            'general': {
                'CONFIG_PREEMPT': {
                    'value': 'y',
                    'description': 'Preemptible Kernel (Low-Latency Desktop)',
                    'reason': 'Improves system responsiveness for desktop and interactive workloads'
                },
                'CONFIG_HZ_1000': {
                    'value': 'y',
                    'description': '1000 Hz tick rate',
                    'reason': 'Provides better timer resolution for desktop systems'
                },
                'CONFIG_HZ': {
                    'value': '1000',
                    'description': 'Timer frequency',
                    'reason': 'Higher timer frequency improves responsiveness'
                }
            },
            'system_desktop': {
                'CONFIG_PREEMPT': {
                    'value': 'y',
                    'description': 'Preemptible Kernel (Low-Latency Desktop)',
                    'reason': 'Improves system responsiveness for desktop workloads'
                },
                'CONFIG_SCHED_AUTOGROUP': {
                    'value': 'y',
                    'description': 'Automatic process group scheduling',
                    'reason': 'Improves desktop interactivity'
                }
            },
            'system_laptop': {
                'CONFIG_PREEMPT': {
                    'value': 'y',
                    'description': 'Preemptible Kernel (Low-Latency Desktop)',
                    'reason': 'Improves system responsiveness for laptop workloads'
                },
                'CONFIG_PM_AUTOSLEEP': {
                    'value': 'y',
                    'description': 'Opportunistic sleep',
                    'reason': 'Improves power management for laptops'
                },
                'CONFIG_SUSPEND': {
                    'value': 'y',
                    'description': 'Suspend to RAM and standby',
                    'reason': 'Enables suspend functionality for laptops'
                },
                'CONFIG_HIBERNATE': {
                    'value': 'y',
                    'description': 'Hibernation (aka suspend to disk)',
                    'reason': 'Enables hibernation functionality for laptops'
                }
            },
            'system_server': {
                'CONFIG_PREEMPT': {
                    'value': 'n',
                    'description': 'No Forced Preemption (Server)',
                    'reason': 'Optimizes throughput for server workloads'
                },
                'CONFIG_HZ_300': {
                    'value': 'y',
                    'description': '300 Hz tick rate',
                    'reason': 'Lower timer frequency reduces overhead for server systems'
                },
                'CONFIG_HZ': {
                    'value': '300',
                    'description': 'Timer frequency',
                    'reason': 'Lower timer frequency reduces overhead for server systems'
                },
                'CONFIG_NO_HZ_FULL': {
                    'value': 'y',
                    'description': 'Full dynticks system (tickless)',
                    'reason': 'Reduces timer interrupts for better performance on server systems'
                }
            },
            'cpu_single': {
                'CONFIG_SMP': {
                    'value': 'n',
                    'description': 'Symmetric multi-processing support',
                    'reason': 'Disables unnecessary SMP support for single-core systems'
                },
                'CONFIG_NR_CPUS': {
                    'value': '1',
                    'description': 'Maximum number of CPUs',
                    'reason': 'Optimizes for single-core systems'
                }
            },
            'cpu_few': {
                'CONFIG_SMP': {
                    'value': 'y',
                    'description': 'Symmetric multi-processing support',
                    'reason': 'Enables SMP support for multi-core systems'
                },
                'CONFIG_NR_CPUS': {
                    'value': '4',
                    'description': 'Maximum number of CPUs',
                    'reason': 'Optimizes for systems with few cores'
                }
            },
            'cpu_multi': {
                'CONFIG_SMP': {
                    'value': 'y',
                    'description': 'Symmetric multi-processing support',
                    'reason': 'Enables SMP support for multi-core systems'
                },
                'CONFIG_NR_CPUS': {
                    'value': '16',
                    'description': 'Maximum number of CPUs',
                    'reason': 'Optimizes for systems with multiple cores'
                }
            },
            'cpu_many': {
                'CONFIG_SMP': {
                    'value': 'y',
                    'description': 'Symmetric multi-processing support',
                    'reason': 'Enables SMP support for multi-core systems'
                },
                'CONFIG_NR_CPUS': {
                    'value': '64',
                    'description': 'Maximum number of CPUs',
                    'reason': 'Optimizes for systems with many cores'
                },
                'CONFIG_NUMA': {
                    'value': 'y',
                    'description': 'NUMA support',
                    'reason': 'Enables NUMA support for systems with many cores'
                }
            },
            'cpu_desktop': {
                'CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE': {
                    'value': 'y',
                    'description': 'Performance governor as default',
                    'reason': 'Optimizes for desktop performance'
                },
                'CONFIG_CPU_FREQ_GOV_SCHEDUTIL': {
                    'value': 'y',
                    'description': 'Schedutil governor',
                    'reason': 'Provides good balance between performance and power efficiency'
                }
            },
            'cpu_laptop': {
                'CONFIG_CPU_FREQ_DEFAULT_GOV_ONDEMAND': {
                    'value': 'y',
                    'description': 'Ondemand governor as default',
                    'reason': 'Optimizes for laptop power efficiency'
                },
                'CONFIG_CPU_FREQ_GOV_POWERSAVE': {
                    'value': 'y',
                    'description': 'Powersave governor',
                    'reason': 'Enables power saving for laptops'
                }
            },
            'cpu_server': {
                'CONFIG_CPU_FREQ_DEFAULT_GOV_PERFORMANCE': {
                    'value': 'y',
                    'description': 'Performance governor as default',
                    'reason': 'Optimizes for server performance'
                }
            },
            'memory_small': {
                'CONFIG_CLEANCACHE': {
                    'value': 'y',
                    'description': 'Enable cleancache driver to cache clean pages',
                    'reason': 'Improves memory efficiency for systems with limited memory'
                },
                'CONFIG_FRONTSWAP': {
                    'value': 'y',
                    'description': 'Enable frontswap to cache swap pages',
                    'reason': 'Improves swap performance for systems with limited memory'
                },
                'CONFIG_ZSWAP': {
                    'value': 'y',
                    'description': 'Compressed cache for swap pages',
                    'reason': 'Improves swap performance for systems with limited memory'
                }
            },
            'memory_medium': {
                'CONFIG_TRANSPARENT_HUGEPAGE': {
                    'value': 'y',
                    'description': 'Transparent Hugepage Support',
                    'reason': 'Improves memory performance for systems with moderate memory'
                },
                'CONFIG_TRANSPARENT_HUGEPAGE_MADVISE': {
                    'value': 'y',
                    'description': 'Transparent Hugepage: madvise',
                    'reason': 'Enables application control of Transparent Hugepages'
                }
            },
            'memory_large': {
                'CONFIG_TRANSPARENT_HUGEPAGE': {
                    'value': 'y',
                    'description': 'Transparent Hugepage Support',
                    'reason': 'Improves memory performance for systems with large memory'
                },
                'CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS': {
                    'value': 'y',
                    'description': 'Transparent Hugepage: always',
                    'reason': 'Enables Transparent Hugepages for all allocations'
                },
                'CONFIG_HUGETLBFS': {
                    'value': 'y',
                    'description': 'HugeTLB file system support',
                    'reason': 'Enables explicit huge page support for applications'
                }
            },
            'memory_very_large': {
                'CONFIG_TRANSPARENT_HUGEPAGE': {
                    'value': 'y',
                    'description': 'Transparent Hugepage Support',
                    'reason': 'Improves memory performance for systems with very large memory'
                },
                'CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS': {
                    'value': 'y',
                    'description': 'Transparent Hugepage: always',
                    'reason': 'Enables Transparent Hugepages for all allocations'
                },
                'CONFIG_HUGETLBFS': {
                    'value': 'y',
                    'description': 'HugeTLB file system support',
                    'reason': 'Enables explicit huge page support for applications'
                },
                'CONFIG_NUMA': {
                    'value': 'y',
                    'description': 'NUMA support',
                    'reason': 'Enables NUMA support for systems with very large memory'
                }
            },
            'memory_desktop': {
                'CONFIG_COMPACTION': {
                    'value': 'y',
                    'description': 'Memory compaction',
                    'reason': 'Improves memory fragmentation for desktop systems'
                }
            },
            'memory_laptop': {
                'CONFIG_COMPACTION': {
                    'value': 'y',
                    'description': 'Memory compaction',
                    'reason': 'Improves memory fragmentation for laptop systems'
                },
                'CONFIG_KSM': {
                    'value': 'y',
                    'description': 'Kernel Samepage Merging',
                    'reason': 'Reduces memory usage by merging identical pages'
                }
            },
            'memory_server': {
                'CONFIG_COMPACTION': {
                    'value': 'y',
                    'description': 'Memory compaction',
                    'reason': 'Improves memory fragmentation for server systems'
                },
                'CONFIG_KSM': {
                    'value': 'y',
                    'description': 'Kernel Samepage Merging',
                    'reason': 'Reduces memory usage by merging identical pages'
                },
                'CONFIG_MEMORY_FAILURE': {
                    'value': 'y',
                    'description': 'Memory failure recovery',
                    'reason': 'Enables recovery from memory failures for server systems'
                }
            },
            'storage_hdd': {
                'CONFIG_BLK_DEV_IO_TRACE': {
                    'value': 'y',
                    'description': 'Block layer I/O tracing',
                    'reason': 'Enables I/O tracing for performance analysis'
                },
                'CONFIG_IOSCHED_BFQ': {
                    'value': 'y',
                    'description': 'BFQ I/O scheduler',
                    'reason': 'Provides good I/O scheduling for HDDs'
                },
                'CONFIG_DEFAULT_BFQ': {
                    'value': 'y',
                    'description': 'BFQ as default I/O scheduler',
                    'reason': 'Sets BFQ as default I/O scheduler for HDDs'
                }
            },
            'storage_ssd': {
                'CONFIG_BLK_DEV_IO_TRACE': {
                    'value': 'y',
                    'description': 'Block layer I/O tracing',
                    'reason': 'Enables I/O tracing for performance analysis'
                },
                'CONFIG_IOSCHED_DEADLINE': {
                    'value': 'y',
                    'description': 'Deadline I/O scheduler',
                    'reason': 'Provides good I/O scheduling for SSDs'
                },
                'CONFIG_DEFAULT_DEADLINE': {
                    'value': 'y',
                    'description': 'Deadline as default I/O scheduler',
                    'reason': 'Sets Deadline as default I/O scheduler for SSDs'
                }
            },
            'storage_nvme': {
                'CONFIG_BLK_DEV_IO_TRACE': {
                    'value': 'y',
                    'description': 'Block layer I/O tracing',
                    'reason': 'Enables I/O tracing for performance analysis'
                },
                'CONFIG_IOSCHED_DEADLINE': {
                    'value': 'y',
                    'description': 'Deadline I/O scheduler',
                    'reason': 'Provides good I/O scheduling for NVMe drives'
                },
                'CONFIG_DEFAULT_DEADLINE': {
                    'value': 'y',
                    'description': 'Deadline as default I/O scheduler',
                    'reason': 'Sets Deadline as default I/O scheduler for NVMe drives'
                },
                'CONFIG_NVME_MULTIPATH': {
                    'value': 'y',
                    'description': 'NVMe multipath support',
                    'reason': 'Enables multipath support for NVMe drives'
                }
            },
            'storage_desktop': {
                'CONFIG_BLK_CGROUP': {
                    'value': 'y',
                    'description': 'Block IO controller',
                    'reason': 'Enables I/O control for desktop systems'
                }
            },
            'storage_laptop': {
                'CONFIG_BLK_CGROUP': {
                    'value': 'y',
                    'description': 'Block IO controller',
                    'reason': 'Enables I/O control for laptop systems'
                },
                'CONFIG_BLK_DEV_THROTTLING': {
                    'value': 'y',
                    'description': 'Block device I/O throttling',
                    'reason': 'Enables I/O throttling for power efficiency'
                }
            },
            'storage_server': {
                'CONFIG_BLK_CGROUP': {
                    'value': 'y',
                    'description': 'Block IO controller',
                    'reason': 'Enables I/O control for server systems'
                },
                'CONFIG_BLK_DEV_INTEGRITY': {
                    'value': 'y',
                    'description': 'Block layer data integrity support',
                    'reason': 'Enables data integrity for server storage'
                }
            },
            'network_ethernet': {
                'CONFIG_NET_SCHED': {
                    'value': 'y',
                    'description': 'QoS and/or fair queueing',
                    'reason': 'Enables network traffic control for Ethernet'
                },
                'CONFIG_NET_SCH_FQ_CODEL': {
                    'value': 'y',
                    'description': 'Fair Queue CoDel packet scheduler',
                    'reason': 'Provides fair queuing and reduces bufferbloat'
                },
                'CONFIG_TCP_CONG_BBR': {
                    'value': 'y',
                    'description': 'BBR TCP congestion control',
                    'reason': 'Improves TCP performance for high-bandwidth connections'
                }
            },
            'network_wireless': {
                'CONFIG_NET_SCHED': {
                    'value': 'y',
                    'description': 'QoS and/or fair queueing',
                    'reason': 'Enables network traffic control for wireless'
                },
                'CONFIG_NET_SCH_FQ_CODEL': {
                    'value': 'y',
                    'description': 'Fair Queue CoDel packet scheduler',
                    'reason': 'Provides fair queuing and reduces bufferbloat'
                },
                'CONFIG_MAC80211_RC_MINSTREL': {
                    'value': 'y',
                    'description': 'Minstrel rate control algorithm',
                    'reason': 'Provides good rate control for wireless connections'
                },
                'CONFIG_CFG80211_WEXT': {
                    'value': 'y',
                    'description': 'cfg80211 wireless extensions compatibility',
                    'reason': 'Enables compatibility with wireless tools'
                }
            },
            'network_desktop': {
                'CONFIG_PACKET': {
                    'value': 'y',
                    'description': 'Packet socket',
                    'reason': 'Enables packet socket support for desktop networking'
                },
                'CONFIG_NETFILTER': {
                    'value': 'y',
                    'description': 'Network packet filtering framework',
                    'reason': 'Enables firewall support for desktop systems'
                }
            },
            'network_laptop': {
                'CONFIG_PACKET': {
                    'value': 'y',
                    'description': 'Packet socket',
                    'reason': 'Enables packet socket support for laptop networking'
                },
                'CONFIG_NETFILTER': {
                    'value': 'y',
                    'description': 'Network packet filtering framework',
                    'reason': 'Enables firewall support for laptop systems'
                },
                'CONFIG_PM_RUNTIME': {
                    'value': 'y',
                    'description': 'Run-time PM core functionality',
                    'reason': 'Enables power management for network devices'
                }
            },
            'network_server': {
                'CONFIG_PACKET': {
                    'value': 'y',
                    'description': 'Packet socket',
                    'reason': 'Enables packet socket support for server networking'
                },
                'CONFIG_NETFILTER': {
                    'value': 'y',
                    'description': 'Network packet filtering framework',
                    'reason': 'Enables firewall support for server systems'
                },
                'CONFIG_NET_RX_BUSY_POLL': {
                    'value': 'y',
                    'description': 'Busy poll for sockets',
                    'reason': 'Reduces latency for server networking'
                },
                'CONFIG_RPS': {
                    'value': 'y',
                    'description': 'Receive Packet Steering',
                    'reason': 'Distributes network processing across CPUs'
                },
                'CONFIG_XPS': {
                    'value': 'y',
                    'description': 'Transmit Packet Steering',
                    'reason': 'Distributes network transmit across CPUs'
                }
            },
            'graphics_integrated': {
                'CONFIG_DRM': {
                    'value': 'y',
                    'description': 'Direct Rendering Manager',
                    'reason': 'Enables graphics support for integrated GPUs'
                },
                'CONFIG_DRM_I915': {
                    'value': 'y',
                    'description': 'Intel 8xx/9xx/G3x/G4x/HD Graphics',
                    'reason': 'Enables support for Intel integrated graphics'
                },
                'CONFIG_DRM_AMD_DC': {
                    'value': 'y',
                    'description': 'AMD DC - Display Core',
                    'reason': 'Enables support for AMD integrated graphics'
                }
            },
            'graphics_dedicated': {
                'CONFIG_DRM': {
                    'value': 'y',
                    'description': 'Direct Rendering Manager',
                    'reason': 'Enables graphics support for dedicated GPUs'
                },
                'CONFIG_DRM_NOUVEAU': {
                    'value': 'y',
                    'description': 'Nouveau (NVIDIA) cards',
                    'reason': 'Enables open-source support for NVIDIA GPUs'
                },
                'CONFIG_DRM_AMDGPU': {
                    'value': 'y',
                    'description': 'AMD GPU',
                    'reason': 'Enables support for AMD GPUs'
                },
                'CONFIG_DRM_AMDGPU_SI': {
                    'value': 'y',
                    'description': 'Enable amdgpu support for SI parts',
                    'reason': 'Enables support for older AMD GPUs'
                },
                'CONFIG_DRM_AMDGPU_CIK': {
                    'value': 'y',
                    'description': 'Enable amdgpu support for CIK parts',
                    'reason': 'Enables support for older AMD GPUs'
                }
            }
        }