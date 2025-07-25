#!/usr/bin/env python3
"""
Unit tests for CPU analyzer implementation.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import time
from unittest.mock import Mock, patch

import pytest

from tinel.hardware.cpu_analyzer import CPUAnalyzer
from tinel.interfaces import CommandResult
from tests.utils import (
    unit_test,
    performance_test,
    AssertionHelpers,
    PerformanceTestHelpers,
    TestDataBuilder
)


class TestCPUAnalyzer:
    """Test cases for CPUAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.analyzer = CPUAnalyzer(self.mock_system)
        
    @unit_test
    def test_initialization(self):
        """Test CPU analyzer initialization."""
        # Test with mock system interface
        analyzer = CPUAnalyzer(self.mock_system)
        assert analyzer.system == self.mock_system
        assert analyzer._cache == {}
        assert analyzer._cache_ttl == 60
        
        # Test with default system interface
        analyzer_default = CPUAnalyzer()
        assert analyzer_default.system is not None
        
    @unit_test
    def test_cache_functionality(self, performance_monitor):
        """Test caching mechanism."""
        # Mock a slow computation
        def slow_computation():
            time.sleep(0.01)  # 10ms delay
            return {'result': 'computed'}
            
        # First call should compute and cache
        performance_monitor.start()
        result1 = self.analyzer._get_cached_or_compute('test_key', slow_computation)
        performance_monitor.stop()
        first_call_time = performance_monitor.elapsed
        
        # Second call should be cached and faster
        performance_monitor.start()
        result2 = self.analyzer._get_cached_or_compute('test_key', slow_computation)
        performance_monitor.stop()
        second_call_time = performance_monitor.elapsed
        
        # Verify results are identical
        assert result1 == result2
        assert result1 == {'result': 'computed'}
        
        # Verify second call was significantly faster
        assert second_call_time < first_call_time
        assert second_call_time < 0.005  # Should be under 5ms
        
    @unit_test
    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        # Set very short TTL for testing
        self.analyzer._cache_ttl = 0.01  # 10ms
        
        call_count = 0
        def counting_computation():
            nonlocal call_count
            call_count += 1
            return {'call': call_count}
            
        # First call
        result1 = self.analyzer._get_cached_or_compute('test_key', counting_computation)
        assert result1 == {'call': 1}
        
        # Second call immediately - should be cached
        result2 = self.analyzer._get_cached_or_compute('test_key', counting_computation)
        assert result2 == {'call': 1}  # Same result, from cache
        
        # Wait for cache to expire
        time.sleep(0.02)  # 20ms
        
        # Third call - should recompute
        result3 = self.analyzer._get_cached_or_compute('test_key', counting_computation)
        assert result3 == {'call': 2}  # New computation
        
    @unit_test
    def test_get_cpu_info_structure(self, sample_cpuinfo, sample_lscpu):
        """Test CPU info returns expected structure."""
        # Set up comprehensive file mock that includes cpuinfo and system files
        self._setup_comprehensive_mocks(sample_cpuinfo, sample_lscpu)
        
        cpu_info = self.analyzer.get_cpu_info()
        
        # Verify basic structure
        AssertionHelpers.assert_valid_cpu_info(cpu_info)
        
        # Verify key sections exist
        expected_sections = [
            'model_name', 'vendor_id', 'cpu_flags', 
            'security_features', 'performance_features',
            'virtualization_features', 'vulnerabilities'
        ]
        AssertionHelpers.assert_contains_keys(cpu_info, expected_sections)
        
    @unit_test
    def test_parse_cpuinfo(self, sample_cpuinfo):
        """Test /proc/cpuinfo parsing."""
        parsed = self.analyzer._parse_cpuinfo(sample_cpuinfo)
        
        expected_fields = ['model_name', 'vendor_id', 'cpu_family', 'model', 'stepping']
        AssertionHelpers.assert_contains_keys(parsed, expected_fields)
        
        assert parsed['model_name'] == 'Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz'
        assert parsed['vendor_id'] == 'GenuineIntel'
        assert parsed['cpu_family'] == '6'
        
    @unit_test
    def test_parse_lscpu(self, sample_lscpu):
        """Test lscpu output parsing."""
        parsed = self.analyzer._parse_lscpu(sample_lscpu)
        
        expected_fields = ['architecture', 'cpu_op_modes', 'byte_order']
        AssertionHelpers.assert_contains_keys(parsed, expected_fields)
        
        assert parsed['architecture'] == 'x86_64'
        assert parsed['cpu_op_modes'] == '32-bit, 64-bit'
        assert parsed['byte_order'] == 'Little Endian'
        
    @unit_test 
    def test_extract_cpu_flags(self, sample_cpuinfo):
        """Test CPU flags extraction."""
        flags = self.analyzer._extract_cpu_flags(sample_cpuinfo)
        
        assert isinstance(flags, list)
        assert len(flags) > 50  # Should have many flags
        
        # Check for common flags
        expected_flags = ['fpu', 'sse', 'sse2', 'sse4_1', 'sse4_2', 'avx', 'avx2']
        for flag in expected_flags:
            assert flag in flags, f"Expected flag '{flag}' not found"
            
    @unit_test
    def test_analyze_security_features(self, cpu_flags):
        """Test security features analysis."""
        security_features = self.analyzer._analyze_security_features(cpu_flags)
        
        expected_features = ['nx_bit', 'smep', 'smap', 'intel_pt']
        AssertionHelpers.assert_contains_keys(security_features, expected_features)
        
        # All values should be boolean
        for feature, enabled in security_features.items():
            assert isinstance(enabled, bool), f"Feature '{feature}' should be boolean"
            
    @unit_test
    def test_analyze_performance_features(self, cpu_flags):
        """Test performance features analysis."""
        performance_features = self.analyzer._analyze_performance_features(cpu_flags)
        
        expected_features = ['sse', 'sse2', 'avx', 'avx2', 'aes']
        AssertionHelpers.assert_contains_keys(performance_features, expected_features)
        
        # Check that SSE/AVX progression makes sense
        if performance_features.get('avx2'):
            assert performance_features.get('avx'), "AVX2 requires AVX"
        if performance_features.get('avx'):
            assert performance_features.get('sse2'), "AVX requires SSE2"
            
    @unit_test
    def test_analyze_virtualization_features(self, cpu_flags):
        """Test virtualization features analysis."""
        virt_features = self.analyzer._analyze_virtualization_features(cpu_flags)
        
        expected_features = ['vmx', 'svm', 'ept', 'vpid'] 
        AssertionHelpers.assert_contains_keys(virt_features, expected_features)
        
        # VMX and SVM are mutually exclusive (Intel vs AMD)
        assert not (virt_features.get('vmx') and virt_features.get('svm')), \
            "VMX and SVM should be mutually exclusive"
            
    @unit_test
    def test_frequency_info_parsing(self):
        """Test CPU frequency information parsing."""
        self._setup_frequency_mocks()
        
        freq_info = self.analyzer._get_frequency_info()
        
        expected_fields = [
            'current_frequency_khz', 'current_frequency_mhz',
            'min_frequency_khz', 'min_frequency_mhz', 
            'max_frequency_khz', 'max_frequency_mhz',
            'current_governor', 'available_governors'
        ]
        AssertionHelpers.assert_contains_keys(freq_info, expected_fields)
        
        # Verify frequency conversions
        assert freq_info['current_frequency_mhz'] == freq_info['current_frequency_khz'] / 1000
        assert freq_info['min_frequency_mhz'] == freq_info['min_frequency_khz'] / 1000
        assert freq_info['max_frequency_mhz'] == freq_info['max_frequency_khz'] / 1000
        
    @unit_test
    def test_topology_info_parsing(self):
        """Test CPU topology information parsing."""
        # Mock nproc command
        self.mock_system.run_command.return_value = CommandResult(
            success=True, stdout='8', stderr='', returncode=0
        )
        
        self._setup_topology_mocks()
        
        topology_info = self.analyzer._get_topology_info()
        
        expected_fields = ['logical_cpus', 'physical_cpus', 'cores_per_socket']
        AssertionHelpers.assert_contains_keys(topology_info, expected_fields)
        
        assert topology_info['logical_cpus'] == 8
        assert isinstance(topology_info['physical_cpus'], int)
        assert isinstance(topology_info['cores_per_socket'], int)
        
    @unit_test
    def test_cache_info_parsing(self):
        """Test CPU cache information parsing."""
        self._setup_cache_mocks()
        
        cache_info = self.analyzer._get_cache_info()
        
        if 'cache' in cache_info:
            cache_data = cache_info['cache']
            
            # Check cache levels
            for level in ['L1', 'L2', 'L3']:
                if level in cache_data:
                    assert 'size' in cache_data[level]
                    assert 'type' in cache_data[level]
                    
    @unit_test
    def test_optimization_analysis(self):
        """Test CPU optimization analysis."""
        # Set up files for suboptimal system (powersave governor + vulnerabilities)
        file_responses = {
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq': '2000000',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq': '400000', 
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq': '4600000',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor': 'powersave',  # Suboptimal
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors': 
                'conservative ondemand userspace powersave performance schedutil',
            '/sys/devices/system/cpu/vulnerabilities/meltdown': 'Vulnerable',  # Vulnerable
            '/sys/devices/system/cpu/vulnerabilities/spectre_v1': 'Vulnerable',  # Vulnerable
            '/sys/devices/system/cpu/vulnerabilities/spectre_v2': 'Mitigation: Enhanced IBRS',
        }
        
        self.mock_system.read_file.side_effect = lambda path: file_responses.get(path)
        
        optimization = self.analyzer._analyze_cpu_optimization()
        
        assert 'optimization_recommendations' in optimization
        recommendations = optimization['optimization_recommendations']
        
        assert isinstance(recommendations, list)
        
        # Should have recommendations for powersave governor and vulnerabilities
        rec_types = [rec['type'] for rec in recommendations]
        assert 'performance' in rec_types
        assert 'security' in rec_types
        
    @unit_test
    def test_error_handling_missing_files(self):
        """Test error handling when system files are missing."""
        # Mock system to return None for missing files
        self.mock_system.read_file.return_value = None
        self.mock_system.run_command.return_value = CommandResult(
            success=False, stdout='', stderr='command not found', returncode=127
        )
        
        cpu_info = self.analyzer.get_cpu_info()
        
        # Should handle errors gracefully
        assert 'proc_cpuinfo_error' in cpu_info
        assert 'lscpu_error' in cpu_info
        
    @performance_test 
    def test_performance_with_caching(self, performance_monitor):
        """Test performance improvement with caching."""
        self._setup_comprehensive_mocks()
        
        # First call - uncached
        performance_monitor.start()
        result1 = self.analyzer.get_cpu_info()
        performance_monitor.stop()
        uncached_time = performance_monitor.elapsed
        
        # Second call - cached
        performance_monitor.start()
        result2 = self.analyzer.get_cpu_info()
        performance_monitor.stop()
        cached_time = performance_monitor.elapsed
        
        # Results should be identical
        assert result1 == result2
        
        # Cached call should be significantly faster
        assert cached_time < uncached_time / 2  # At least 2x faster
        assert cached_time < 0.01  # Under 10ms
        
    def _setup_frequency_mocks(self, governor='powersave'):
        """Set up mocks for frequency information."""
        frequency_files = {
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq': '2000000',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq': '400000', 
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq': '4600000',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor': governor,
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors': 
                'conservative ondemand userspace powersave performance schedutil'
        }
        
        def mock_read_file(path):
            return frequency_files.get(path)
            
        self.mock_system.read_file.side_effect = mock_read_file
        
    def _setup_topology_mocks(self):
        """Set up mocks for topology information."""
        topology_files = {
            '/sys/devices/system/cpu/cpu0/topology/physical_package_id': '0',
            '/sys/devices/system/cpu/cpu1/topology/physical_package_id': '0', 
            '/sys/devices/system/cpu/cpu2/topology/physical_package_id': '0',
            '/sys/devices/system/cpu/cpu3/topology/physical_package_id': '0',
            '/sys/devices/system/cpu/cpu0/topology/core_id': '0',
            '/sys/devices/system/cpu/cpu1/topology/core_id': '1',
            '/sys/devices/system/cpu/cpu2/topology/core_id': '2', 
            '/sys/devices/system/cpu/cpu3/topology/core_id': '3',
        }
        
        def mock_read_file(path):
            return topology_files.get(path)
            
        self.mock_system.read_file.side_effect = mock_read_file
        
    def _setup_cache_mocks(self):
        """Set up mocks for cache information."""
        cache_files = {
            '/sys/devices/system/cpu/cpu0/cache/index0/size': '32K',
            '/sys/devices/system/cpu/cpu0/cache/index0/type': 'Data',
            '/sys/devices/system/cpu/cpu0/cache/index0/level': '1',
            '/sys/devices/system/cpu/cpu0/cache/index1/size': '32K',
            '/sys/devices/system/cpu/cpu0/cache/index1/type': 'Instruction', 
            '/sys/devices/system/cpu/cpu0/cache/index1/level': '1',
            '/sys/devices/system/cpu/cpu0/cache/index2/size': '256K',
            '/sys/devices/system/cpu/cpu0/cache/index2/type': 'Unified',
            '/sys/devices/system/cpu/cpu0/cache/index2/level': '2',
            '/sys/devices/system/cpu/cpu0/cache/index3/size': '8192K',
            '/sys/devices/system/cpu/cpu0/cache/index3/type': 'Unified',
            '/sys/devices/system/cpu/cpu0/cache/index3/level': '3',
        }
        
        # Mock file_exists for cache directories
        def mock_file_exists(path):
            return path in cache_files
            
        def mock_read_file(path):
            return cache_files.get(path)
            
        self.mock_system.file_exists.side_effect = mock_file_exists
        self.mock_system.read_file.side_effect = mock_read_file
        
    def _setup_vulnerability_mocks(self, vulnerable_count=1):
        """Set up mocks for vulnerability information."""
        vuln_files = {
            '/sys/devices/system/cpu/vulnerabilities/spectre_v1': 
                'Mitigation: usercopy/swapgs barriers',
            '/sys/devices/system/cpu/vulnerabilities/spectre_v2': 
                'Mitigation: Enhanced IBRS',
            '/sys/devices/system/cpu/vulnerabilities/meltdown': 
                'Mitigation: PTI',
            '/sys/devices/system/cpu/vulnerabilities/spec_store_bypass': 
                'Vulnerable' if vulnerable_count > 0 else 'Mitigation: SSB disabled',
            '/sys/devices/system/cpu/vulnerabilities/l1tf': 
                'Vulnerable' if vulnerable_count > 1 else 'Mitigation: PTE Inversion',
        }
        
        def mock_read_file(path):
            return vuln_files.get(path)
            
        self.mock_system.read_file.side_effect = mock_read_file
        
    def _setup_all_mocks(self, sample_cpuinfo=None, sample_lscpu=None):
        """Set up all mocks for comprehensive testing."""
        if not sample_cpuinfo:
            sample_cpuinfo = "model name : Test CPU\nflags : sse sse2 avx\n"
        if not sample_lscpu:
            sample_lscpu = "Architecture: x86_64\nCPU(s): 4\n"
            
        # Mock basic data sources
        self.mock_system.read_file.return_value = sample_cpuinfo
        
        # Mock different command responses
        def mock_run_command(cmd):
            if cmd[0] == 'nproc':
                return CommandResult(success=True, stdout='4', stderr='', returncode=0)
            else:  # lscpu and others
                return CommandResult(success=True, stdout=sample_lscpu, stderr='', returncode=0)
        
        self.mock_system.run_command.side_effect = mock_run_command
        
        # Set up all subsystem mocks
        self._setup_frequency_mocks()
        self._setup_topology_mocks() 
        self._setup_cache_mocks()
        self._setup_vulnerability_mocks()
        
    def _setup_comprehensive_mocks(self, sample_cpuinfo=None, sample_lscpu=None):
        """Set up comprehensive mocks including all file sources."""
        if not sample_cpuinfo:
            sample_cpuinfo = "model name : Test CPU\nflags : sse sse2 avx\n"
        if not sample_lscpu:
            sample_lscpu = "Architecture: x86_64\nCPU(s): 4\n"
            
        # Create comprehensive file mapping
        file_responses = {
            # Main CPU info sources
            '/proc/cpuinfo': sample_cpuinfo,
            
            # Frequency files
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq': '2000000',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq': '400000',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq': '4600000',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor': 'performance',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors': 
                'conservative ondemand userspace powersave performance schedutil',
                
            # Topology files
            '/sys/devices/system/cpu/cpu0/topology/physical_package_id': '0',
            '/sys/devices/system/cpu/cpu1/topology/physical_package_id': '0',
            '/sys/devices/system/cpu/cpu0/topology/core_id': '0',
            '/sys/devices/system/cpu/cpu1/topology/core_id': '1',
            '/sys/devices/system/cpu/cpu0/topology/thread_siblings_list': '0,1',
            
            # Cache files
            '/sys/devices/system/cpu/cpu0/cache/index0/size': '32K',
            '/sys/devices/system/cpu/cpu0/cache/index0/type': 'Data',
            '/sys/devices/system/cpu/cpu0/cache/index0/level': '1',
            '/sys/devices/system/cpu/cpu0/cache/index2/size': '256K',
            '/sys/devices/system/cpu/cpu0/cache/index2/type': 'Unified',
            '/sys/devices/system/cpu/cpu0/cache/index2/level': '2',
            
            # Vulnerability files
            '/sys/devices/system/cpu/vulnerabilities/meltdown': 'Mitigation: PTI',
            '/sys/devices/system/cpu/vulnerabilities/spectre_v1': 'Mitigation: barriers',
            '/sys/devices/system/cpu/vulnerabilities/spectre_v2': 'Mitigation: Enhanced IBRS',
        }
        
        def mock_read_file(path):
            return file_responses.get(path)
            
        self.mock_system.read_file.side_effect = mock_read_file
        
        # Mock command responses  
        def mock_run_command(cmd):
            if cmd[0] == 'nproc':
                return CommandResult(success=True, stdout='4', stderr='', returncode=0)
            else:  # lscpu and others
                return CommandResult(success=True, stdout=sample_lscpu, stderr='', returncode=0)
        
        self.mock_system.run_command.side_effect = mock_run_command
        
        # Mock file existence
        cache_files = {
            '/sys/devices/system/cpu/cpu0/cache/index0/size',
            '/sys/devices/system/cpu/cpu0/cache/index0/type',
            '/sys/devices/system/cpu/cpu0/cache/index0/level',
            '/sys/devices/system/cpu/cpu0/cache/index2/size',
            '/sys/devices/system/cpu/cpu0/cache/index2/type',
            '/sys/devices/system/cpu/cpu0/cache/index2/level',
        }
        self.mock_system.file_exists.side_effect = lambda path: path in cache_files or path in file_responses


@pytest.mark.parametrize("cache_ttl,expected_calls", [
    (0.01, 2),   # Very short TTL, should cause recomputation
    (60.0, 1),   # Long TTL, should stay cached
])
@unit_test 
def test_cache_ttl_behavior(cache_ttl, expected_calls):
    """Test cache TTL behavior with different timeout values."""
    mock_system = Mock()
    analyzer = CPUAnalyzer(mock_system)
    analyzer._cache_ttl = cache_ttl
    
    call_count = 0
    def counting_computation():
        nonlocal call_count
        call_count += 1
        return {'count': call_count}
        
    # First call
    result1 = analyzer._get_cached_or_compute('test', counting_computation)
    
    # Wait based on TTL
    if cache_ttl < 1.0:
        time.sleep(cache_ttl + 0.01)
        
    # Second call
    result2 = analyzer._get_cached_or_compute('test', counting_computation)
    
    assert call_count == expected_calls