#!/usr/bin/env python3
"""Tests for the Memory Analyzer module.

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
from unittest.mock import MagicMock

from infenix.hardware.memory_analyzer import MemoryAnalyzer
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
    
    # Mock /proc/meminfo content
    system.files['/proc/meminfo'] = """MemTotal:       16384000 kB
MemFree:         8192000 kB
MemAvailable:   12288000 kB
Buffers:          512000 kB
Cached:          2048000 kB
SwapCached:            0 kB
Active:          4096000 kB
Inactive:        2048000 kB
Active(anon):    2048000 kB
Inactive(anon):   512000 kB
Active(file):    2048000 kB
Inactive(file):  1536000 kB
Unevictable:           0 kB
Mlocked:               0 kB
SwapTotal:       2097152 kB
SwapFree:        2097152 kB
Dirty:             64000 kB
Writeback:             0 kB
AnonPages:       2048000 kB
Mapped:           512000 kB
Shmem:            256000 kB
KReclaimable:     512000 kB
Slab:             256000 kB
SReclaimable:     128000 kB
SUnreclaim:       128000 kB
KernelStack:       16000 kB
PageTables:        32000 kB
NFS_Unstable:          0 kB
Bounce:                0 kB
WritebackTmp:          0 kB
CommitLimit:    10289152 kB
Committed_AS:    4096000 kB
VmallocTotal:   34359738367 kB
VmallocUsed:       32000 kB
VmallocChunk:          0 kB
Percpu:             8000 kB
HardwareCorrupted:     0 kB
AnonHugePages:         0 kB
ShmemHugePages:        0 kB
ShmemPmdMapped:        0 kB
FileHugePages:         0 kB
FilePmdMapped:         0 kB
HugePages_Total:       0
HugePages_Free:        0
HugePages_Rsvd:        0
HugePages_Surp:        0
Hugepagesize:       2048 kB
Hugetlb:               0 kB
DirectMap4k:      262144 kB
DirectMap2M:    16515072 kB
DirectMap1G:           0 kB"""
    
    # Mock free command output
    system.commands['free -h'] = CommandResult(
        success=True,
        stdout="""              total        used        free      shared  buff/cache   available
Mem:            16Gi        4.0Gi        8.0Gi        256Mi        4.0Gi         12Gi
Swap:          2.0Gi          0B        2.0Gi""",
        stderr="",
        returncode=0
    )
    
    # Mock dmidecode memory output
    system.commands['sudo dmidecode -t memory'] = CommandResult(
        success=True,
        stdout="""# dmidecode 3.3
Getting SMBIOS data from sysfs.
SMBIOS 3.2.0 present.

Handle 0x0010, DMI type 17, 84 bytes
Memory Device
	Array Handle: 0x000F
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 8192 MB
	Form Factor: SODIMM
	Set: None
	Locator: DIMM A
	Bank Locator: BANK 0
	Type: DDR4
	Type Detail: Synchronous
	Speed: 3200 MT/s
	Manufacturer: Samsung
	Serial Number: 12345678
	Asset Tag: 9876543210
	Part Number: M471A1K43DB1-CWE
	Rank: 1
	Configured Memory Speed: 3200 MT/s
	Minimum Voltage: 1.2 V
	Maximum Voltage: 1.2 V
	Configured Voltage: 1.2 V

Handle 0x0011, DMI type 17, 84 bytes
Memory Device
	Array Handle: 0x000F
	Error Information Handle: Not Provided
	Total Width: 64 bits
	Data Width: 64 bits
	Size: 8192 MB
	Form Factor: SODIMM
	Set: None
	Locator: DIMM B
	Bank Locator: BANK 1
	Type: DDR4
	Type Detail: Synchronous
	Speed: 3200 MT/s
	Manufacturer: Samsung
	Serial Number: 87654321
	Asset Tag: 0123456789
	Part Number: M471A1K43DB1-CWE
	Rank: 1
	Configured Memory Speed: 3200 MT/s
	Minimum Voltage: 1.2 V
	Maximum Voltage: 1.2 V
	Configured Voltage: 1.2 V""",
        stderr="",
        returncode=0
    )
    
    # Mock dmidecode memory controller output
    system.commands['sudo dmidecode -t 16'] = CommandResult(
        success=True,
        stdout="""# dmidecode 3.3
Getting SMBIOS data from sysfs.
SMBIOS 3.2.0 present.

Handle 0x000F, DMI type 16, 23 bytes
Physical Memory Array
	Location: System Board Or Motherboard
	Use: System Memory
	Error Correction Type: None
	Maximum Capacity: 32 GB
	Error Information Handle: Not Provided
	Number Of Devices: 2""",
        stderr="",
        returncode=0
    )
    
    # Mock /proc/vmstat content
    system.files['/proc/vmstat'] = """nr_free_pages 2097152
nr_zone_inactive_anon 131072
nr_zone_active_anon 524288
nr_zone_inactive_file 393216
nr_zone_active_file 524288
nr_zone_unevictable 0
nr_zone_write_pending 16384
nr_mlock 0
nr_bounce 0
nr_zspages 0
nr_free_cma 0
numa_hit 1000000
numa_miss 0
numa_foreign 0
numa_interleave 50000
numa_local 1000000
numa_other 0
pgpgin 500000
pgpgout 300000
pswpin 0
pswpout 0
pgalloc_dma 0
pgalloc_dma32 100000
pgalloc_normal 900000
pgalloc_movable 0
allocstall_dma 0
allocstall_dma32 0
allocstall_normal 0
allocstall_movable 0
pgskip_dma 0
pgskip_dma32 0
pgskip_normal 0
pgskip_movable 0
pgfree 1000000
pgactivate 200000
pgdeactivate 100000
pglazyfree 0
pgfault 5000000
pgmajfault 10000
pglazyfreed 0
pgrefill 100000
pgsteal_kswapd 50000
pgsteal_direct 0
pgscan_kswapd 100000
pgscan_direct 0
pgscan_direct_throttle 0
zone_reclaim_failed 0
pginodesteal 0
slabs_scanned 0
kswapd_inodesteal 0
kswapd_low_wmark_hit_quickly 0
kswapd_high_wmark_hit_quickly 0
pageoutrun 0
pgrotated 0
drop_pagecache 0
drop_slab 0
oom_kill 0
numa_pte_updates 0
numa_huge_pte_updates 0
numa_hint_faults 0
numa_hint_faults_local 0
numa_pages_migrated 0
pgmigrate_success 0
pgmigrate_fail 0
compact_migrate_scanned 0
compact_free_scanned 0
compact_isolated 0
compact_stall 0
compact_fail 0
compact_success 0
compact_daemon_wake 0
compact_daemon_migrate_scanned 0
compact_daemon_free_scanned 0
htlb_buddy_alloc_success 0
htlb_buddy_alloc_fail 0
unevictable_pgs_culled 0
unevictable_pgs_scanned 0
unevictable_pgs_rescued 0
unevictable_pgs_mlocked 0
unevictable_pgs_munlocked 0
unevictable_pgs_cleared 0
unevictable_pgs_stranded 0
thp_fault_alloc 0
thp_fault_fallback 0
thp_fault_fallback_charge 0
thp_collapse_alloc 0
thp_collapse_alloc_failed 0
thp_file_alloc 0
thp_file_fallback 0
thp_file_fallback_charge 0
thp_file_mapped 0
thp_split_page 0
thp_split_page_failed 0
thp_deferred_split_page 0
thp_split_pmd 0
thp_split_pud 0
thp_zero_page_alloc 0
thp_zero_page_alloc_failed 0
thp_swpout 0
thp_swpout_fallback 0
balloon_inflate 0
balloon_deflate 0
balloon_migrate 0
swap_ra 0
swap_ra_hit 0
direct_map_level2_splits 0
direct_map_level3_splits 0"""
    
    # Mock /proc/buddyinfo content
    system.files['/proc/buddyinfo'] = """Node 0, zone      DMA      0      0      0      0      2      1      1      0      1      1      3
Node 0, zone    DMA32   1234   5678   2345   1234    567    234    123     56     23     12      5
Node 0, zone   Normal  12345  23456  12345   6789   3456   1234    567    234    123     56     23"""
    
    # Mock transparent huge pages setting
    system.files['/sys/kernel/mm/transparent_hugepage/enabled'] = 'always [madvise] never'
    
    # Mock PSI memory pressure
    system.files['/proc/pressure/memory'] = """some avg10=0.00 avg60=0.00 avg300=0.00 total=0
full avg10=0.00 avg60=0.00 avg300=0.00 total=0"""
    
    # Mock NUMA information
    system.file_exists_map['/sys/devices/system/node'] = True
    system.commands['numactl --hardware'] = CommandResult(
        success=True,
        stdout="""available: 1 nodes (0)
node 0 cpus: 0 1 2 3 4 5 6 7
node 0 size: 16384 MB
node 0 free: 8192 MB
node distances:
node   0 
  0:  10""",
        stderr="",
        returncode=0
    )
    
    # Mock EDAC information
    system.file_exists_map['/sys/devices/system/edac'] = True
    system.file_exists_map['/sys/devices/system/edac/mc/mc0'] = True
    system.files['/sys/devices/system/edac/mc/mc0/size_mb'] = '16384'
    system.files['/sys/devices/system/edac/mc/mc0/mc_name'] = 'Intel_iMC'
    
    return system


def test_memory_analyzer_initialization():
    """Test memory analyzer initialization."""
    analyzer = MemoryAnalyzer()
    assert analyzer is not None
    assert analyzer.system is not None


def test_memory_analyzer_with_custom_system():
    """Test memory analyzer with custom system interface."""
    mock_system = MockSystemInterface()
    analyzer = MemoryAnalyzer(mock_system)
    assert analyzer.system is mock_system


def test_get_memory_info_basic(mock_system):
    """Test basic memory information gathering."""
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Check that basic info is present
    assert 'proc_meminfo' in result
    assert 'free_output' in result
    assert 'memory_total_kb' in result
    assert 'memory_total_gb' in result
    assert 'memory_free_kb' in result
    assert 'memory_available_kb' in result
    
    # Check specific values
    assert result['memory_total_kb'] == 16384000
    assert result['memory_total_gb'] == 15.62  # 16384000 / 1024 / 1024 = 15.625, rounded to 15.62
    assert result['memory_free_kb'] == 8192000
    assert result['memory_available_kb'] == 12288000


def test_get_memory_hardware_info(mock_system):
    """Test memory hardware information gathering."""
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Check hardware info
    assert 'dmidecode_memory' in result
    assert 'memory_devices' in result
    assert 'memory_device_count' in result
    assert 'total_installed_memory_mb' in result
    assert 'total_installed_memory_gb' in result
    assert 'max_capacity' in result
    assert 'max_memory_devices' in result
    
    # Check specific values
    assert result['memory_device_count'] == 2
    assert result['total_installed_memory_mb'] == 16384
    assert result['total_installed_memory_gb'] == 16.0
    assert result['max_capacity'] == '32 GB'
    assert result['max_memory_devices'] == 2
    
    # Check individual memory devices
    devices = result['memory_devices']
    assert len(devices) == 2
    assert devices[0]['size'] == '8192 MB'
    assert devices[0]['type'] == 'DDR4'
    assert devices[0]['speed'] == '3200 MT/s'
    assert devices[0]['manufacturer'] == 'Samsung'
    assert devices[0]['locator'] == 'DIMM A'


def test_get_memory_performance_info(mock_system):
    """Test memory performance information gathering."""
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Check performance info
    assert 'vmstat' in result
    assert 'page_faults' in result
    assert 'major_page_faults' in result
    assert 'swap_in_pages' in result
    assert 'swap_out_pages' in result
    assert 'memory_pressure' in result
    assert 'numa_info' in result
    
    # Check specific values
    assert result['page_faults'] == 5000000
    assert result['major_page_faults'] == 10000
    assert result['swap_in_pages'] == 0
    assert result['swap_out_pages'] == 0


def test_get_numa_info(mock_system):
    """Test NUMA information gathering."""
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Check NUMA info
    assert 'numa_info' in result
    numa_info = result['numa_info']
    assert 'numactl_hardware' in numa_info
    assert 'numa_nodes' in numa_info
    assert 'node_distances' in numa_info
    
    # Check specific values
    assert numa_info['numa_nodes'] == 1


def test_get_edac_info(mock_system):
    """Test EDAC information gathering."""
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Check EDAC info
    assert 'edac_info' in result
    edac_info = result['edac_info']
    assert 'memory_controllers' in edac_info
    
    # Check memory controller info
    controllers = edac_info['memory_controllers']
    assert len(controllers) == 1
    assert controllers[0]['size_mb'] == 16384
    assert controllers[0]['name'] == 'Intel_iMC'


def test_memory_optimization_analysis(mock_system):
    """Test memory optimization analysis."""
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Check optimization recommendations
    assert 'optimization_recommendations' in result
    recommendations = result['optimization_recommendations']
    
    # Should not have high swap usage recommendation (swap is not being used)
    swap_recs = [r for r in recommendations if 'swap usage' in r.get('issue', '')]
    assert len(swap_recs) == 0


def test_memory_optimization_high_swap(mock_system):
    """Test memory optimization with high swap usage."""
    # Modify mock to show high swap usage
    mock_system.files['/proc/meminfo'] = mock_system.files['/proc/meminfo'].replace(
        'SwapFree:        2097152 kB',
        'SwapFree:         524288 kB'  # 75% swap usage
    )
    
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Check optimization recommendations
    recommendations = result['optimization_recommendations']
    swap_recs = [r for r in recommendations if 'swap usage' in r.get('issue', '')]
    assert len(swap_recs) == 1
    assert swap_recs[0]['severity'] == 'medium'  # 75% swap usage should be medium severity


def test_parse_meminfo():
    """Test /proc/meminfo parsing."""
    analyzer = MemoryAnalyzer()
    meminfo_content = """MemTotal:       16384000 kB
MemFree:         8192000 kB
MemAvailable:   12288000 kB
Buffers:          512000 kB
Cached:          2048000 kB
SwapTotal:       2097152 kB
SwapFree:        2097152 kB"""
    
    result = analyzer._parse_meminfo(meminfo_content)
    
    assert result['memory_total_kb'] == 16384000
    assert result['memory_total_gb'] == 15.62  # 16384000 / 1024 / 1024 = 15.625, rounded to 15.62
    assert result['memory_free_kb'] == 8192000
    assert result['memory_available_kb'] == 12288000
    assert result['buffers_kb'] == 512000
    assert result['cached_kb'] == 2048000
    assert result['swap_total_kb'] == 2097152
    assert result['swap_free_kb'] == 2097152
    assert result['swap_used_kb'] == 0
    assert result['memory_usage_percent'] == 25.0  # (16384000 - 12288000) / 16384000 * 100


def test_parse_free_output():
    """Test free command output parsing."""
    analyzer = MemoryAnalyzer()
    free_output = """              total        used        free      shared  buff/cache   available
Mem:            16Gi        4.0Gi        8.0Gi        256Mi        4.0Gi         12Gi
Swap:          2.0Gi          0B        2.0Gi"""
    
    result = analyzer._parse_free_output(free_output)
    
    assert result['free_memory_total'] == '16Gi'
    assert result['free_memory_used'] == '4.0Gi'
    assert result['free_memory_free'] == '8.0Gi'
    assert result['free_memory_shared'] == '256Mi'
    assert result['free_memory_buff_cache'] == '4.0Gi'
    assert result['free_memory_available'] == '12Gi'


def test_parse_dmidecode_memory():
    """Test dmidecode memory output parsing."""
    analyzer = MemoryAnalyzer()
    dmidecode_output = """Handle 0x0010, DMI type 17, 84 bytes
Memory Device
	Size: 8192 MB
	Type: DDR4
	Speed: 3200 MT/s
	Manufacturer: Samsung
	Part Number: M471A1K43DB1-CWE
	Locator: DIMM A

Handle 0x0011, DMI type 17, 84 bytes
Memory Device
	Size: 8192 MB
	Type: DDR4
	Speed: 3200 MT/s
	Manufacturer: Samsung
	Part Number: M471A1K43DB1-CWE
	Locator: DIMM B"""
    
    result = analyzer._parse_dmidecode_memory(dmidecode_output)
    
    assert 'memory_devices' in result
    assert result['memory_device_count'] == 2
    assert result['total_installed_memory_mb'] == 16384
    assert result['total_installed_memory_gb'] == 16.0
    
    devices = result['memory_devices']
    assert devices[0]['size'] == '8192 MB'
    assert devices[0]['type'] == 'DDR4'
    assert devices[0]['speed'] == '3200 MT/s'
    assert devices[0]['manufacturer'] == 'Samsung'
    assert devices[0]['locator'] == 'DIMM A'


def test_parse_vmstat():
    """Test /proc/vmstat parsing."""
    analyzer = MemoryAnalyzer()
    vmstat_content = """pgfault 5000000
pgmajfault 10000
pswpin 0
pswpout 0
numa_hit 1000000"""
    
    result = analyzer._parse_vmstat(vmstat_content)
    
    assert result['page_faults'] == 5000000
    assert result['major_page_faults'] == 10000
    assert result['swap_in_pages'] == 0
    assert result['swap_out_pages'] == 0


def test_analyze_memory_fragmentation():
    """Test memory fragmentation analysis."""
    analyzer = MemoryAnalyzer()
    buddyinfo_content = """Node 0, zone      DMA      0      0      0      0      2      1      1      0      1      1      3
Node 0, zone    DMA32      0      0      0      0      0      0      0      0      0      0      0
Node 0, zone   Normal  12345  23456  12345   6789   3456   1234    567    234    123     56     23"""
    
    result = analyzer._analyze_memory_fragmentation(buddyinfo_content)
    
    assert 'fragmented' in result
    assert 'analysis' in result
    
    # DMA32 zone should be flagged as fragmented (all higher order pages are 0)
    fragmented_zones = [a for a in result['analysis'] if a['higher_order_pages'] < 100]
    assert len(fragmented_zones) >= 1


def test_extract_meminfo_value():
    """Test meminfo value extraction."""
    analyzer = MemoryAnalyzer()
    meminfo_content = """MemTotal:       16384000 kB
MemFree:         8192000 kB
MemAvailable:   12288000 kB"""
    
    assert analyzer._extract_meminfo_value(meminfo_content, 'MemTotal') == 16384000
    assert analyzer._extract_meminfo_value(meminfo_content, 'MemFree') == 8192000
    assert analyzer._extract_meminfo_value(meminfo_content, 'MemAvailable') == 12288000
    assert analyzer._extract_meminfo_value(meminfo_content, 'NonExistent') is None


def test_error_handling_missing_files(mock_system):
    """Test error handling when files are missing."""
    # Remove some files to test error handling
    del mock_system.files['/proc/meminfo']
    mock_system.commands['free -h'] = CommandResult(
        success=False, stdout="", stderr="", returncode=1, error="Command failed"
    )
    
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Should handle missing files gracefully
    assert 'proc_meminfo_error' in result
    assert 'free_error' in result
    assert result['proc_meminfo_error'] == 'Failed to read /proc/meminfo'


def test_error_handling_command_failure(mock_system):
    """Test error handling when commands fail."""
    mock_system.commands['sudo dmidecode -t memory'] = CommandResult(
        success=False, stdout="", stderr="", returncode=1, error="Permission denied"
    )
    
    analyzer = MemoryAnalyzer(mock_system)
    result = analyzer.get_memory_info()
    
    # Should handle command failures gracefully
    assert 'dmidecode_memory_error' in result
    assert 'Permission denied' in result['dmidecode_memory_error']