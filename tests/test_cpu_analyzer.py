#!/usr/bin/env python3
"""Tests for the CPU Analyzer module.

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
from unittest.mock import MagicMock, patch

from infenix.hardware.cpu_analyzer import CPUAnalyzer
from infenix.interfaces import CommandResult, SystemInterface


class MockSystemInterface(SystemInterface):
    """Mock system interface for testing."""
    
    def __init__(self):
        self.files = {}
        self.commands = {}
        self.file_exists_map = {}
    
    def run_command(self, cmd):
        cmd_str = ' '.join(cmd)
        if cmd_str in self.commands:
            return self.commands[cmd_str]
        return CommandResult(success=False, stdout="", stderr="", returncode=1, error="Command not found")
    
    def read_file(self, path):
        return self.files.get(path)
    
    def file_exists(self, path):
        return self.file_exists_map.get(path, False)


@pytest.fixture
def mock_system():
    """Create a mock system interface with sample data."""
    system = MockSystemInterface()
    
    # Mock /proc/cpuinfo content
    system.files['/proc/cpuinfo'] = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz
stepping	: 12
microcode	: 0xf0
cpu MHz		: 1800.000
cache size	: 8192 KB
physical id	: 0
siblings	: 8
core id		: 0
cpu cores	: 4
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 22
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp md_clear flush_l1d arch_capabilities
bugs		:
bogomips	: 3999.93
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:"""
    
    # Mock lscpu output
    system.commands['lscpu'] = CommandResult(
        success=True,
        stdout="""Architecture:                    x86_64
CPU op-mode(s):                  32-bit, 64-bit
Byte Order:                      Little Endian
Address sizes:                   39 bits physical, 48 bits virtual
CPU(s):                          8
On-line CPU(s) list:             0-7
Thread(s) per core:              2
Core(s) per socket:              4
Socket(s):                       1
NUMA node(s):                    1
Vendor ID:                       GenuineIntel
CPU family:                      6
Model:                           142
Model name:                      Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz
Stepping:                        12
CPU MHz:                         1800.000
CPU max MHz:                     4600.0000
CPU min MHz:                     400.0000
BogoMIPS:                        3999.93
Virtualization:                  VT-x
L1d cache:                       128 KiB
L1i cache:                       128 KiB
L2 cache:                        1 MiB
L3 cache:                        8 MiB
NUMA node0 CPU(s):               0-7""",
        stderr="",
        returncode=0
    )
    
    # Mock nproc output
    system.commands['nproc'] = CommandResult(
        success=True,
        stdout="8",
        stderr="",
        returncode=0
    )
    
    # Mock frequency files
    system.files['/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq'] = '1800000'
    system.files['/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq'] = '400000'
    system.files['/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq'] = '4600000'
    system.files['/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors'] = 'performance powersave'
    system.files['/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'] = 'powersave'
    
    # Mock topology files
    system.files['/sys/devices/system/cpu/cpu0/topology/physical_package_id'] = '0'
    system.files['/sys/devices/system/cpu/cpu0/topology/core_id'] = '0'
    
    # Mock cache files
    system.file_exists_map['/sys/devices/system/cpu/cpu0/cache/index0/size'] = True
    system.files['/sys/devices/system/cpu/cpu0/cache/index0/size'] = '32K'
    system.files['/sys/devices/system/cpu/cpu0/cache/index0/type'] = 'Data'
    system.files['/sys/devices/system/cpu/cpu0/cache/index0/level'] = '1'
    
    # Mock vulnerability files
    system.files['/sys/devices/system/cpu/vulnerabilities/spectre_v1'] = 'Mitigation: usercopy/swapgs barriers and __user pointer sanitization'
    system.files['/sys/devices/system/cpu/vulnerabilities/spectre_v2'] = 'Mitigation: Full generic retpoline, IBPB: conditional, IBRS_FW, STIBP: conditional, RSB filling'
    system.files['/sys/devices/system/cpu/vulnerabilities/meltdown'] = 'Mitigation: PTI'
    
    return system


def test_cpu_analyzer_initialization():
    """Test CPU analyzer initialization."""
    analyzer = CPUAnalyzer()
    assert analyzer is not None
    assert analyzer.system is not None


def test_cpu_analyzer_with_custom_system():
    """Test CPU analyzer with custom system interface."""
    mock_system = MockSystemInterface()
    analyzer = CPUAnalyzer(mock_system)
    assert analyzer.system is mock_system


def test_get_cpu_info_basic(mock_system):
    """Test basic CPU information gathering."""
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Check that basic info is present
    assert 'proc_cpuinfo' in result
    assert 'lscpu' in result
    assert 'model_name' in result
    assert 'vendor_id' in result
    assert 'architecture' in result
    
    # Check specific values
    assert result['model_name'] == 'Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz'
    assert result['vendor_id'] == 'GenuineIntel'
    assert result['architecture'] == 'x86_64'


def test_get_cpu_features(mock_system):
    """Test CPU features detection."""
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Check that features are detected
    assert 'cpu_flags' in result
    assert 'security_features' in result
    assert 'performance_features' in result
    assert 'virtualization_features' in result
    
    # Check specific features
    assert 'sse' in result['cpu_flags']
    assert 'avx' in result['cpu_flags']
    assert result['security_features']['nx_bit'] is True
    assert result['performance_features']['sse'] is True
    assert result['performance_features']['avx'] is True
    assert result['virtualization_features']['vmx'] is True


def test_get_frequency_info(mock_system):
    """Test CPU frequency information gathering."""
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Check frequency information
    assert 'current_frequency_khz' in result
    assert 'current_frequency_mhz' in result
    assert 'min_frequency_khz' in result
    assert 'max_frequency_khz' in result
    assert 'available_governors' in result
    assert 'current_governor' in result
    
    # Check specific values
    assert result['current_frequency_khz'] == 1800000
    assert result['current_frequency_mhz'] == 1800.0
    assert result['min_frequency_khz'] == 400000
    assert result['max_frequency_khz'] == 4600000
    assert 'performance' in result['available_governors']
    assert result['current_governor'] == 'powersave'


def test_get_topology_info(mock_system):
    """Test CPU topology information gathering."""
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Check topology information
    assert 'logical_cpus' in result
    assert result['logical_cpus'] == 8


def test_get_cache_info(mock_system):
    """Test CPU cache information gathering."""
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Check cache information
    assert 'cache' in result
    assert 'L1' in result['cache']
    assert result['cache']['L1']['size'] == '32K'
    assert result['cache']['L1']['type'] == 'Data'


def test_get_vulnerabilities(mock_system):
    """Test CPU vulnerabilities detection."""
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Check vulnerabilities
    assert 'vulnerabilities' in result
    assert 'spectre_v1' in result['vulnerabilities']
    assert 'spectre_v2' in result['vulnerabilities']
    assert 'meltdown' in result['vulnerabilities']
    
    # Check that mitigations are detected
    assert 'Mitigation' in result['vulnerabilities']['spectre_v1']
    assert 'Mitigation' in result['vulnerabilities']['spectre_v2']
    assert 'Mitigation' in result['vulnerabilities']['meltdown']


def test_optimization_recommendations(mock_system):
    """Test CPU optimization recommendations."""
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Check optimization recommendations
    assert 'optimization_recommendations' in result
    recommendations = result['optimization_recommendations']
    
    # Should recommend changing from powersave governor
    governor_rec = next((r for r in recommendations if r['type'] == 'performance'), None)
    assert governor_rec is not None
    assert 'powersave' in governor_rec['issue']


def test_parse_cpuinfo():
    """Test /proc/cpuinfo parsing."""
    analyzer = CPUAnalyzer()
    cpuinfo_content = """processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 142
model name	: Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz
stepping	: 12"""
    
    result = analyzer._parse_cpuinfo(cpuinfo_content)
    
    assert result['vendor_id'] == 'GenuineIntel'
    assert result['cpu_family'] == '6'
    assert result['model'] == '142'
    assert result['model_name'] == 'Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz'
    assert result['stepping'] == '12'


def test_parse_lscpu():
    """Test lscpu output parsing."""
    analyzer = CPUAnalyzer()
    lscpu_output = """Architecture:                    x86_64
CPU op-mode(s):                  32-bit, 64-bit
Byte Order:                      Little Endian"""
    
    result = analyzer._parse_lscpu(lscpu_output)
    
    assert result['architecture'] == 'x86_64'
    assert result['cpu_op_modes'] == '32-bit, 64-bit'
    assert result['byte_order'] == 'Little Endian'


def test_extract_cpu_flags():
    """Test CPU flags extraction."""
    analyzer = CPUAnalyzer()
    cpuinfo_content = "flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2"
    
    flags = analyzer._extract_cpu_flags(cpuinfo_content)
    
    assert 'fpu' in flags
    assert 'sse' in flags
    assert 'sse2' in flags
    assert len(flags) > 10


def test_analyze_security_features():
    """Test security features analysis."""
    analyzer = CPUAnalyzer()
    flags = ['nx', 'smep', 'smap', 'intel_pt']
    
    security_features = analyzer._analyze_security_features(flags)
    
    assert security_features['nx_bit'] is True
    assert security_features['smep'] is True
    assert security_features['smap'] is True
    assert security_features['intel_pt'] is True
    assert security_features['cet_ss'] is False


def test_analyze_performance_features():
    """Test performance features analysis."""
    analyzer = CPUAnalyzer()
    flags = ['sse', 'sse2', 'pni', 'ssse3', 'sse4_1', 'sse4_2', 'avx', 'avx2', 'aes']
    
    performance_features = analyzer._analyze_performance_features(flags)
    
    assert performance_features['sse'] is True
    assert performance_features['sse2'] is True
    assert performance_features['sse3'] is True  # pni = SSE3
    assert performance_features['ssse3'] is True
    assert performance_features['sse4_1'] is True
    assert performance_features['sse4_2'] is True
    assert performance_features['avx'] is True
    assert performance_features['avx2'] is True
    assert performance_features['aes'] is True


def test_analyze_virtualization_features():
    """Test virtualization features analysis."""
    analyzer = CPUAnalyzer()
    flags = ['vmx', 'ept', 'vpid']
    
    virt_features = analyzer._analyze_virtualization_features(flags)
    
    assert virt_features['vmx'] is True
    assert virt_features['ept'] is True
    assert virt_features['vpid'] is True
    assert virt_features['svm'] is False


def test_error_handling_missing_files(mock_system):
    """Test error handling when files are missing."""
    # Remove some files to test error handling
    del mock_system.files['/proc/cpuinfo']
    mock_system.commands['lscpu'] = CommandResult(
        success=False, stdout="", stderr="", returncode=1, error="Command failed"
    )
    
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Should handle missing files gracefully
    assert 'proc_cpuinfo_error' in result
    assert 'lscpu_error' in result
    assert result['proc_cpuinfo_error'] == 'Failed to read /proc/cpuinfo'


def test_error_handling_command_failure(mock_system):
    """Test error handling when commands fail."""
    mock_system.commands['nproc'] = CommandResult(
        success=False, stdout="", stderr="", returncode=1, error="Command not found"
    )
    
    analyzer = CPUAnalyzer(mock_system)
    result = analyzer.get_cpu_info()
    
    # Should handle command failures gracefully
    # The logical_cpus field should not be present if nproc fails
    assert 'logical_cpus' not in result or result.get('logical_cpus') is None