#!/usr/bin/env python3
"""
Performance tests for Tinel components.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest

from tinel.hardware.cpu_analyzer import CPUAnalyzer
from tinel.system import LinuxSystemInterface
from tinel.cli.formatters import OutputFormatter
from tests.utils import (
    performance_test,
    PerformanceTestHelpers,
    AssertionHelpers,
    TestDataBuilder
)


class TestCPUAnalyzerPerformance:
    """Performance tests for CPU analyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system = Mock()
        self.analyzer = CPUAnalyzer(self.mock_system)
        
    def _setup_realistic_mocks(self, slow_mode=False):
        """Set up realistic system mocks that don't cause infinite loops."""
        def mock_read_file(path):
            if slow_mode:
                time.sleep(0.01)  # 10ms delay per file read
                
            if 'cpuinfo' in path:
                return "model name : Test CPU\nflags : sse sse2 avx\n"
            elif 'scaling_cur_freq' in path:
                return '2000000'
            elif 'scaling_min_freq' in path:
                return '400000'
            elif 'scaling_max_freq' in path:
                return '4600000'
            elif 'scaling_governor' in path:
                return 'performance'
            elif 'scaling_available_governors' in path:
                return 'conservative ondemand userspace powersave performance schedutil'
            elif 'vulnerabilities' in path:
                return 'Mitigation: Enhanced IBRS'
            elif 'cache' in path and 'size' in path:
                return '256K'
            elif 'cache' in path and 'type' in path:
                return 'Unified'
            elif 'cache' in path and 'level' in path:
                return '2'
            elif 'topology' in path:
                # Simulate 4 CPUs (cpu0-cpu3), then return None to break loops
                if 'cpu0' in path or 'cpu1' in path or 'cpu2' in path or 'cpu3' in path:
                    if 'physical_package_id' in path:
                        return '0'  # All CPUs in same package
                    elif 'core_id' in path:
                        # Extract CPU number and return core_id
                        if 'cpu0' in path or 'cpu1' in path:
                            return '0'
                        else:
                            return '1'
                    return '0'
                else:
                    return None  # Break infinite loops for cpu4+
            else:
                return "mock content"
                
        def mock_run_command(cmd):
            if slow_mode:
                time.sleep(0.02)  # 20ms delay per command
                
            if cmd[0] == 'nproc':
                return TestDataBuilder.create_command_result(stdout="4")
            else:
                return TestDataBuilder.create_command_result(stdout="Architecture: x86_64\nCPU(s): 4\n")
        
        self.mock_system.read_file.side_effect = mock_read_file
        self.mock_system.run_command.side_effect = mock_run_command
        
        # Mock file existence for common files
        def mock_file_exists(path):
            common_files = [
                '/proc/cpuinfo',
                '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq',
                '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor',
                '/sys/devices/system/cpu/cpu0/topology/physical_package_id',
                '/sys/devices/system/cpu/vulnerabilities/meltdown'
            ]
            return path in common_files or 'cache' in path
            
        self.mock_system.file_exists.side_effect = mock_file_exists
        
    @performance_test
    def test_cpu_info_caching_performance(self, performance_monitor):
        """Test performance improvement from caching."""
        self._setup_realistic_mocks(slow_mode=True)
        
        # First call - should be slow (uncached)
        performance_monitor.start()
        result1 = self.analyzer.get_cpu_info()
        performance_monitor.stop()
        uncached_time = performance_monitor.elapsed
        
        # Second call - should be fast (cached)  
        performance_monitor.start()
        result2 = self.analyzer.get_cpu_info()
        performance_monitor.stop()
        cached_time = performance_monitor.elapsed
        
        # Verify results are identical
        assert result1 == result2
        
        # Verify significant performance improvement
        PerformanceTestHelpers.assert_cached_performance(
            lambda: self.analyzer.get_cpu_info(),  # cached call
            lambda: self._fresh_cpu_info(),        # uncached call
            min_improvement=3.0  # At least 3x faster
        )
        
        # Verify absolute performance bounds
        AssertionHelpers.assert_performance_within_bounds(cached_time, 0.01, 0.0)  # Under 10ms
        
    @performance_test
    def test_concurrent_cpu_analysis(self):
        """Test performance under concurrent access."""
        self._setup_realistic_mocks(slow_mode=False)
        
        # Run concurrent analyses
        def analyze_cpu():
            return self.analyzer.get_cpu_info()
            
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze_cpu) for _ in range(10)]
            results = [future.result() for future in futures]
            
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        # All results should be identical (cached)
        for result in results[1:]:
            assert result == results[0]
            
        # Should complete quickly due to caching
        AssertionHelpers.assert_performance_within_bounds(elapsed, 0.5, 0.0)  # Under 500ms
        
    @performance_test
    def test_memory_usage_bounds(self):
        """Test memory usage stays within reasonable bounds."""
        import psutil
        import os
        
        # Measure initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Set up realistic mocks with large data
        self._setup_realistic_mocks(slow_mode=False)
        
        # Override with large data where needed
        large_cpuinfo = "processor : 0\nmodel name : Test CPU\n" + "flags : " + " ".join([f"flag{i}" for i in range(1000)]) + "\n"
        large_lscpu = "Architecture: x86_64\nCPU(s): 4\n" + "\n".join([f"Field{i}: Value{i}" for i in range(100)])
        
        # Override specific files with large data
        original_read_file = self.mock_system.read_file.side_effect
        def large_data_read_file(path):
            if 'cpuinfo' in path:
                return large_cpuinfo
            else:
                return original_read_file(path)
        
        self.mock_system.read_file.side_effect = large_data_read_file
        
        # Override command responses with large data
        def large_data_run_command(cmd):
            if cmd[0] == 'nproc':
                return TestDataBuilder.create_command_result(stdout="4")
            else:
                return TestDataBuilder.create_command_result(stdout=large_lscpu)
        
        self.mock_system.run_command.side_effect = large_data_run_command
        
        # Run multiple analyses
        for _ in range(10):
            self.analyzer.get_cpu_info()
            
        # Measure final memory
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (under 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory usage increased by {memory_increase / 1024 / 1024:.2f}MB"
        
    @performance_test
    def test_cache_eviction_performance(self):
        """Test performance when cache entries are evicted."""
        # Set very short cache TTL
        self.analyzer._cache_ttl = 0.01  # 10ms
        
        self._setup_realistic_mocks(slow_mode=False)
        
        # First call
        result1 = self.analyzer.get_cpu_info()
        
        # Wait for cache expiration
        time.sleep(0.02)
        
        # Second call should recompute but still be reasonably fast
        with PerformanceTestHelpers.measure_time() as timing:
            result2 = self.analyzer.get_cpu_info()
            
        # Should complete within reasonable time even after cache expiration
        AssertionHelpers.assert_performance_within_bounds(timing['elapsed'], 0.1, 0.0)  # Under 100ms
        
    def _fresh_cpu_info(self):
        """Get fresh CPU info without cache."""
        fresh_analyzer = CPUAnalyzer(self.mock_system)
        return fresh_analyzer.get_cpu_info()


class TestSystemInterfacePerformance:
    """Performance tests for system interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.system = LinuxSystemInterface()
        
    @performance_test
    def test_command_execution_timeout(self):
        """Test command execution respects timeout limits."""
        # Test with mock that simulates slow command
        with patch('subprocess.run') as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired(['sleep', '10'], 0.1)
            
            start_time = time.perf_counter()
            result = self.system.run_command(['sleep', '10'], timeout=0.1)
            end_time = time.perf_counter()
            
            # Should timeout quickly
            elapsed = end_time - start_time
            assert elapsed < 0.2  # Should timeout within 200ms
            assert not result.success
            assert 'timed out' in result.error
            
    @performance_test 
    def test_file_reading_performance(self):
        """Test file reading performance with size limits."""
        with patch('builtins.open') as mock_open:
            with patch.object(self.system, '_validate_file_path', return_value='/proc/cpuinfo'):
                with patch('pathlib.Path.stat') as mock_stat:
                    # Test with various file sizes
                    file_sizes = [1024, 10*1024, 100*1024, 1024*1024]  # 1KB to 1MB
                    
                    for size in file_sizes:
                        mock_stat.return_value = Mock(st_size=size)
                        mock_content = "x" * size
                        mock_open.return_value.__enter__.return_value.read.return_value = mock_content
                        
                        with PerformanceTestHelpers.measure_time() as timing:
                            result = self.system.read_file('/proc/cpuinfo')
                            
                        # Should read successfully and within reasonable time
                        assert result is not None
                        # Reading should be fast (under 10ms per 100KB)
                        max_time = max(0.01 * (size / (100 * 1024)), 0.001)  # At least 1ms minimum
                        # Just assert it's under the max time, don't enforce minimum
                        assert timing['elapsed'] <= max_time, f"File reading took {timing['elapsed']:.4f}s, expected ≤ {max_time:.4f}s"
                        
    @performance_test
    def test_command_sanitization_performance(self):
        """Test command sanitization performance."""
        # Test with various command sizes
        commands = [
            ['lscpu'],
            ['lscpu', '-p'],
            ['lscpu'] + [f'arg{i}' for i in range(10)],
            ['lscpu'] + [f'arg{i}' for i in range(100)],
        ]
        
        for cmd in commands:
            with PerformanceTestHelpers.measure_time() as timing:
                result = self.system._sanitize_command(cmd)
                
            # Sanitization should be very fast
            AssertionHelpers.assert_performance_within_bounds(timing['elapsed'], 0.001, 0.0)  # Under 1ms
            assert result == cmd
            
    @performance_test
    def test_path_validation_performance(self):
        """Test path validation performance."""
        # Test with various path lengths and types
        paths = [
            '/proc/cpuinfo',
            '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor',
            '/proc/' + 'deep/' * 10 + 'file',
            '../' * 20 + 'etc/passwd',  # Path traversal attempt
        ]
        
        for path in paths:
            with PerformanceTestHelpers.measure_time() as timing:
                result = self.system._validate_file_path(path)
                
            # Path validation should be very fast
            AssertionHelpers.assert_performance_within_bounds(timing['elapsed'], 0.001, 0.0)  # Under 1ms


class TestFormatterPerformance:
    """Performance tests for output formatters."""
    
    @performance_test
    def test_large_data_formatting_performance(self):
        """Test formatting performance with large datasets."""
        # Create large test dataset
        large_data = {
            'cpu_info': {
                'model_name': 'Test CPU Model Name',
                'vendor_id': 'TestVendor',
                'cpu_flags': [f'flag{i}' for i in range(200)],  # 200 flags
                'features': {f'feature{i}': i % 2 == 0 for i in range(100)},  # 100 features
            },
            'detailed_info': {f'key{i}': f'value{i}' * 10 for i in range(50)},  # 50 detailed entries
        }
        
        formatters = [
            ('text', OutputFormatter(format_type='text', use_color=False)),
            ('json', OutputFormatter(format_type='json', use_color=False)),
            ('csv', OutputFormatter(format_type='csv', use_color=False)),
        ]
        
        for format_name, formatter in formatters:
            with PerformanceTestHelpers.measure_time() as timing:
                result = formatter.format_output(large_data)
                
            # Formatting should complete within reasonable time
            max_time = 0.1  # 100ms for large data
            AssertionHelpers.assert_performance_within_bounds(
                timing['elapsed'], max_time, 0.0
            )
            
            # Result should not be empty
            assert len(result) > 1000  # Should be substantial output
            
    @performance_test
    def test_concurrent_formatting(self):
        """Test formatter performance under concurrent load."""
        formatter = OutputFormatter(format_type='json', use_color=False)
        test_data = {'test': 'data', 'number': 42, 'list': [1, 2, 3, 4, 5]}
        
        def format_data():
            return formatter.format_output(test_data)
            
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(format_data) for _ in range(50)]
            results = [future.result() for future in futures]
            
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        # All results should be identical
        for result in results[1:]:
            assert result == results[0]
            
        # Should handle concurrent load efficiently
        AssertionHelpers.assert_performance_within_bounds(elapsed, 1.0, 0.0)  # Under 1 second
        
    @performance_test
    def test_table_formatting_performance(self):
        """Test table formatting performance with large datasets."""
        formatter = OutputFormatter(format_type='text', use_color=False)
        
        # Create large table data
        headers = ['name', 'value', 'status', 'description', 'timestamp']
        data = [
            {
                'name': f'item{i}',
                'value': i * 10,
                'status': 'active' if i % 2 == 0 else 'inactive',
                'description': f'Description for item {i} with more details',
                'timestamp': f'2025-01-{i%30 + 1:02d}'
            }
            for i in range(100)  # 100 rows
        ]
        
        with PerformanceTestHelpers.measure_time() as timing:
            result = formatter.format_table(data, headers)
            
        # Table formatting should be reasonably fast
        AssertionHelpers.assert_performance_within_bounds(timing['elapsed'], 0.05, 0.0)  # Under 50ms
        
        # Verify table structure
        lines = result.split('\n')
        assert len(lines) >= 102  # Header + separator + 100 data rows


class TestOverallSystemPerformance:
    """Overall system performance tests."""
    
    @performance_test
    def test_cold_start_performance(self):
        """Test cold start performance of the system."""
        # Simulate cold start by creating fresh instances
        with PerformanceTestHelpers.measure_time() as timing:
            mock_system = Mock()
            
            # Set up realistic mocks for cold start
            def mock_read_file(path):
                if 'cpuinfo' in path:
                    return "model name : Test CPU\nflags : sse sse2 avx\n"
                elif 'scaling_cur_freq' in path:
                    return '2000000'
                elif 'scaling_min_freq' in path:
                    return '400000'
                elif 'scaling_max_freq' in path:
                    return '4600000'
                elif 'scaling_governor' in path:
                    return 'performance'
                elif 'scaling_available_governors' in path:
                    return 'conservative ondemand userspace powersave performance schedutil'
                elif 'vulnerabilities' in path:
                    return 'Mitigation: Enhanced IBRS'
                elif 'cache' in path and 'size' in path:
                    return '256K'
                elif 'cache' in path and 'type' in path:
                    return 'Unified'
                elif 'cache' in path and 'level' in path:
                    return '2'
                elif 'topology' in path:
                    if 'cpu0' in path:
                        return '0'
                    else:
                        return None
                else:
                    return "mock content"
                    
            def mock_run_command(cmd):
                if cmd[0] == 'nproc':
                    return TestDataBuilder.create_command_result(stdout="4")
                else:
                    return TestDataBuilder.create_command_result(stdout="Architecture: x86_64\nCPU(s): 4\n")
            
            mock_system.read_file.side_effect = mock_read_file
            mock_system.run_command.side_effect = mock_run_command
            mock_system.file_exists.return_value = True
            
            analyzer = CPUAnalyzer(mock_system)
            result = analyzer.get_cpu_info()
            
        # Cold start should complete within reasonable time
        AssertionHelpers.assert_performance_within_bounds(timing['elapsed'], 0.1, 0.0)  # Under 100ms
        assert result is not None
        
    @performance_test
    def test_memory_efficiency_under_load(self):
        """Test memory efficiency under sustained load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create multiple analyzers and run analyses
        analyzers = []
        for i in range(10):
            mock_system = Mock()
            
            # Set up realistic mocks for each analyzer
            cpu_id = i  # Capture the current value
            def mock_read_file(path):
                if 'cpuinfo' in path:
                    return f"model name : Test CPU {cpu_id}\nflags : sse sse2 avx\n"
                elif 'scaling_cur_freq' in path:
                    return '2000000'
                elif 'scaling_min_freq' in path:
                    return '400000'
                elif 'scaling_max_freq' in path:
                    return '4600000'
                elif 'scaling_governor' in path:
                    return 'performance'
                elif 'scaling_available_governors' in path:
                    return 'conservative ondemand userspace powersave performance schedutil'
                elif 'vulnerabilities' in path:
                    return 'Mitigation: Enhanced IBRS'
                elif 'cache' in path and 'size' in path:
                    return '256K'
                elif 'cache' in path and 'type' in path:
                    return 'Unified'
                elif 'cache' in path and 'level' in path:
                    return '2'
                elif 'topology' in path:
                    if 'cpu0' in path:
                        return '0'
                    else:
                        return None
                else:
                    return "mock content"
                    
            def mock_run_command(cmd):
                if cmd[0] == 'nproc':
                    return TestDataBuilder.create_command_result(stdout="4")
                else:
                    return TestDataBuilder.create_command_result(stdout="Architecture: x86_64\nCPU(s): 4\n")
            
            mock_system.read_file.side_effect = mock_read_file
            mock_system.run_command.side_effect = mock_run_command
            mock_system.file_exists.return_value = True
            
            analyzer = CPUAnalyzer(mock_system)
            analyzers.append(analyzer)
            
            # Run analysis
            analyzer.get_cpu_info()
            
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable per analyzer
        memory_per_analyzer = memory_increase / len(analyzers)
        assert memory_per_analyzer < 5 * 1024 * 1024, \
            f"Memory per analyzer: {memory_per_analyzer / 1024 / 1024:.2f}MB (should be < 5MB)"


@pytest.mark.parametrize("data_size,max_time", [
    (100, 0.01),    # Small data: 10ms
    (1000, 0.05),   # Medium data: 50ms  
    (10000, 0.2),   # Large data: 200ms
])
@performance_test
def test_scaling_performance(data_size, max_time):
    """Test performance scaling with different data sizes."""
    formatter = OutputFormatter(format_type='json', use_color=False)
    
    # Create data of specified size
    data = {f'key{i}': f'value{i}' for i in range(data_size)}
    
    with PerformanceTestHelpers.measure_time() as timing:
        result = formatter.format_output(data)
        
    # Should scale reasonably with data size
    AssertionHelpers.assert_performance_within_bounds(timing['elapsed'], max_time, 0.0)
    assert result is not None