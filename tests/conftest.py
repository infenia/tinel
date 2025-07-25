#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Tinel testing.

Copyright 2025 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from unittest.mock import Mock, MagicMock

import pytest

# Add the parent directory to the path to import tinel modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from tinel.interfaces import CommandResult
from tinel.system import LinuxSystemInterface
from tinel.cli.formatters import OutputFormatter
from tinel.cli.error_handler import CLIErrorHandler


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_system_interface():
    """Create a mock system interface for testing."""
    mock = Mock(spec=LinuxSystemInterface)
    
    # Default successful command result
    mock.run_command.return_value = CommandResult(
        success=True,
        stdout="mock output",
        stderr="",
        returncode=0
    )
    
    # Default file read result
    mock.read_file.return_value = "mock file content"
    mock.file_exists.return_value = True
    
    return mock


@pytest.fixture
def sample_cpuinfo():
    """Sample /proc/cpuinfo content for testing."""
    return """processor	: 0
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
vmx flags	: vnmi preemption_timer posted_intr invvpid ept_x_only ept_ad ept_1gb flexpriority apicv tsc_offset vtpr mtf vapic ept vpid unrestricted_guest vapic_reg vid ple shadow_vmcs ept_mode_based_exec tsc_scaling
bugs		: spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs taa itlb_multihit srbds mmio_stale_data retbleed
bogomips	: 3999.93
clflush size	: 64
cache_alignment	: 64
address sizes	: 39 bits physical, 48 bits virtual
power management:
"""


@pytest.fixture
def sample_lscpu():
    """Sample lscpu output for testing."""
    return """Architecture:                    x86_64
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
NUMA node0 CPU(s):               0-7
Vulnerability Itlb multihit:     KVM: Mitigation: VMX disabled
Vulnerability L1tf:              Mitigation; PTE Inversion; VMX conditional cache flushes, SMT vulnerable
Vulnerability Mds:               Mitigation; Clear CPU buffers; SMT vulnerable
Vulnerability Meltdown:          Mitigation; PTI
Vulnerability Mmio stale data:   Mitigation; Clear CPU buffers; SMT vulnerable
Vulnerability Retbleed:          Mitigation; Enhanced IBRS
Vulnerability Spec store bypass: Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:        Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:        Mitigation; Enhanced IBRS, IBPB conditional, RSB filling, PBRSB-eIBRS SW sequence
Vulnerability Srbds:             Mitigation; Microcode
Vulnerability Tsx async abort:   Not affected
Flags:                           fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb invpcid_single pti ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp md_clear flush_l1d arch_capabilities
"""


@pytest.fixture
def sample_vulnerabilities():
    """Sample CPU vulnerability information for testing."""
    return {
        'spectre_v1': 'Mitigation: usercopy/swapgs barriers and __user pointer sanitization',
        'spectre_v2': 'Mitigation: Enhanced IBRS, IBPB conditional, RSB filling',
        'meltdown': 'Mitigation: PTI',
        'spec_store_bypass': 'Mitigation: Speculative Store Bypass disabled via prctl',
        'l1tf': 'Mitigation: PTE Inversion; VMX conditional cache flushes, SMT vulnerable',
        'mds': 'Mitigation: Clear CPU buffers; SMT vulnerable',
        'tsx_async_abort': 'Not affected',
        'itlb_multihit': 'KVM: Mitigation: VMX disabled',
        'srbds': 'Mitigation: Microcode'
    }


@pytest.fixture
def mock_output_formatter():
    """Create a mock output formatter for testing."""
    mock = Mock(spec=OutputFormatter)
    mock.format_output.return_value = "formatted output"
    mock.print_output.return_value = None
    mock.print_error.return_value = None
    mock.colorize.side_effect = lambda text, color: text  # No coloring in tests
    return mock


@pytest.fixture
def mock_error_handler():
    """Create a mock error handler for testing."""
    mock = Mock(spec=CLIErrorHandler)
    return mock


@pytest.fixture
def safe_environment():
    """Create a safe environment dictionary for testing."""
    return {
        'PATH': '/usr/bin:/bin:/usr/sbin:/sbin',
        'LC_ALL': 'C',
        'LANG': 'C',
        'HOME': '/home/test',
        'USER': 'test'
    }


@pytest.fixture
def cpu_flags():
    """Sample CPU flags for testing."""
    return [
        'fpu', 'vme', 'de', 'pse', 'tsc', 'msr', 'pae', 'mce', 'cx8', 'apic',
        'sep', 'mtrr', 'pge', 'mca', 'cmov', 'pat', 'pse36', 'clflush', 'dts',
        'acpi', 'mmx', 'fxsr', 'sse', 'sse2', 'ss', 'ht', 'tm', 'pbe', 'syscall',
        'nx', 'pdpe1gb', 'rdtscp', 'lm', 'constant_tsc', 'art', 'arch_perfmon',
        'pebs', 'bts', 'rep_good', 'nopl', 'xtopology', 'nonstop_tsc', 'cpuid',
        'aperfmperf', 'pni', 'pclmulqdq', 'dtes64', 'monitor', 'ds_cpl', 'vmx',
        'est', 'tm2', 'ssse3', 'sdbg', 'fma', 'cx16', 'xtpr', 'pdcm', 'pcid',
        'sse4_1', 'sse4_2', 'x2apic', 'movbe', 'popcnt', 'tsc_deadline_timer',
        'aes', 'xsave', 'avx', 'f16c', 'rdrand', 'lahf_lm', 'abm', '3dnowprefetch',
        'cpuid_fault', 'epb', 'invpcid_single', 'pti', 'ssbd', 'ibrs', 'ibpb',
        'stibp', 'tpr_shadow', 'vnmi', 'flexpriority', 'ept', 'vpid', 'ept_ad',
        'fsgsbase', 'tsc_adjust', 'bmi1', 'avx2', 'smep', 'bmi2', 'erms',
        'invpcid', 'mpx', 'rdseed', 'adx', 'smap', 'clflushopt', 'intel_pt',
        'xsaveopt', 'xsavec', 'xgetbv1', 'xsaves', 'dtherm', 'ida', 'arat',
        'pln', 'pts', 'hwp', 'hwp_notify', 'hwp_act_window', 'hwp_epp',
        'md_clear', 'flush_l1d', 'arch_capabilities'
    ]


class MockFileSystem:
    """Mock file system for testing file operations."""
    
    def __init__(self):
        self.files: Dict[str, str] = {}
        self.file_sizes: Dict[str, int] = {}
        
    def add_file(self, path: str, content: str, size: Optional[int] = None):
        """Add a file to the mock filesystem."""
        self.files[path] = content
        self.file_sizes[path] = size or len(content)
        
    def read_file(self, path: str) -> Optional[str]:
        """Mock file reading."""
        return self.files.get(path)
        
    def file_exists(self, path: str) -> bool:
        """Mock file existence check."""
        return path in self.files
        
    def get_file_size(self, path: str) -> int:
        """Mock file size check."""
        return self.file_sizes.get(path, 0)


@pytest.fixture
def mock_filesystem():
    """Create a mock filesystem for testing."""
    fs = MockFileSystem()
    
    # Add common system files
    fs.add_file('/proc/cpuinfo', pytest.lazy_fixture('sample_cpuinfo'))
    fs.add_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', '2000000')
    fs.add_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq', '400000')
    fs.add_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', '4600000')
    fs.add_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'powersave')
    fs.add_file('/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors', 
                'conservative ondemand userspace powersave performance schedutil')
    
    # Add vulnerability files
    vuln_base = '/sys/devices/system/cpu/vulnerabilities'
    fs.add_file(f'{vuln_base}/spectre_v1', 'Mitigation: usercopy/swapgs barriers')
    fs.add_file(f'{vuln_base}/spectre_v2', 'Mitigation: Enhanced IBRS')
    fs.add_file(f'{vuln_base}/meltdown', 'Mitigation: PTI')
    fs.add_file(f'{vuln_base}/spec_store_bypass', 'Mitigation: Speculative Store Bypass disabled')
    
    # Add cache information
    cache_base = '/sys/devices/system/cpu/cpu0/cache'
    fs.add_file(f'{cache_base}/index0/size', '32K')
    fs.add_file(f'{cache_base}/index0/type', 'Data')
    fs.add_file(f'{cache_base}/index0/level', '1')
    fs.add_file(f'{cache_base}/index1/size', '32K')
    fs.add_file(f'{cache_base}/index1/type', 'Instruction')
    fs.add_file(f'{cache_base}/index1/level', '1')
    fs.add_file(f'{cache_base}/index2/size', '256K')
    fs.add_file(f'{cache_base}/index2/type', 'Unified')
    fs.add_file(f'{cache_base}/index2/level', '2')
    fs.add_file(f'{cache_base}/index3/size', '8192K')
    fs.add_file(f'{cache_base}/index3/type', 'Unified')
    fs.add_file(f'{cache_base}/index3/level', '3')
    
    return fs


@pytest.fixture
def command_results():
    """Create sample command results for testing."""
    return {
        'lscpu': CommandResult(
            success=True,
            stdout=pytest.lazy_fixture('sample_lscpu'),
            stderr='',
            returncode=0
        ),
        'nproc': CommandResult(
            success=True,
            stdout='8',
            stderr='',
            returncode=0
        ),
        'lscpu_fail': CommandResult(
            success=False,
            stdout='',
            stderr='lscpu: command not found',
            returncode=127,
            error='Command not found'
        )
    }


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables for consistent testing."""
    env_vars_to_remove = ['NO_COLOR', 'FORCE_COLOR', 'TINEL_CONFIG']
    original_values = {}
    
    # Store original values and remove them
    for var in env_vars_to_remove:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_values.items():
        os.environ[var] = value


@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture for tests."""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.perf_counter()
            
        def stop(self):
            self.end_time = time.perf_counter()
            
        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time
            
        def assert_max_time(self, max_seconds: float):
            """Assert that elapsed time is under the maximum."""
            assert self.elapsed is not None, "Timer not started/stopped"
            assert self.elapsed <= max_seconds, f"Operation took {self.elapsed:.3f}s, expected <= {max_seconds}s"
    
    return PerformanceMonitor()


# Test markers for different types of tests
pytest_markers = {
    'unit': 'Unit tests',
    'integration': 'Integration tests',
    'performance': 'Performance tests',
    'security': 'Security tests',
    'slow': 'Slow tests that may take longer to run',
    'network': 'Tests that require network access',
    'sudo': 'Tests that require sudo privileges'
}

# Register custom markers
for marker, description in pytest_markers.items():
    pytest.mark.__dict__.setdefault(marker, pytest.mark.mark(marker))