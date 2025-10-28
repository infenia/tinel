#!/usr/bin/env python3
"""
Copyright 2025 Infenia Private Limited

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
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import psutil

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface
from .models import CPUInfo

"""Provides a detailed analysis of the host system's CPU.

This module contains the `CPUAnalyzer` class, which is responsible for
gathering a comprehensive set of information about the CPU. This includes,
but is not limited to:

- Basic identification (model, vendor, architecture).
- Core and thread topology (physical cores, logical processors).
- CPU features and instruction set extensions (e.g., AVX, SSE, AES).
- Security feature analysis and vulnerability status (e.g., Spectre, Meltdown).
- Real-time performance metrics (frequency, governor).
- Cache hierarchy details (L1, L2, L3 cache sizes).
- Actionable optimization recommendations.

The analyzer employs a caching mechanism to minimize performance impact from
repeated queries to system files and commands like `lscpu` and `nproc`.
It primarily sources information from the `/proc/cpuinfo` file and the sysfs
filesystem (`/sys`), with `psutil` used as a robust fallback and for
cross-verification.
"""


class CPUAnalyzer:
    """Analyzes and retrieves detailed information about the system's CPU.

    This class orchestrates the collection of CPU data from various system
    sources. It uses a caching mechanism with a configurable time-to-live (TTL)
    to avoid redundant, expensive system calls for data that changes
    infrequently.

    The primary public method is `get_cpu_info()`, which returns a
    comprehensive dictionary of CPU attributes.

    Attributes:
        system: An instance of a `SystemInterface` for interacting with the
                underlying operating system. Defaults to `LinuxSystemInterface`.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the CPUAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions. If not provided, a default
                              `LinuxSystemInterface` is instantiated.
        """
        self.system = system_interface or LinuxSystemInterface()
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    def _get_cached_or_compute(self, key: str, compute_func: Callable[[], Any]) -> Any:
        """Retrieves a result from the cache or computes it if not present.

        This method implements a time-to-live (TTL) caching strategy to avoid
        re-computing data that changes infrequently. It checks for a valid
        cached result and, if not found, executes the `compute_func` to
        generate and cache a new result.

        Args:
            key: The unique key for the cached item.
            compute_func: A callable that computes the result if it's not in
                          the cache.

        Returns:
            The cached or newly computed result.
        """
        current_time = time.time()

        # Check if we have a valid cached result
        if key in self._cache:
            cached_result, timestamp = self._cache[key]
            if current_time - timestamp < self._cache_ttl:
                return cached_result

        # Compute new result and cache it
        result = compute_func()
        self._cache[key] = (result, current_time)
        return result

    def get_cpu_info(self) -> CPUInfo:
        """Retrieves comprehensive information about the CPU.

        This is the main public method of the class. It orchestrates the
        gathering of all CPU-related data, including basic information,
        features, topology, and cache details. The result is cached to
        optimize subsequent calls.

        Returns:
            A CPUInfo dataclass containing a detailed breakdown of CPU information.
        """
        return cast(
            CPUInfo,
            self._get_cached_or_compute("cpu_info_full", self._compute_cpu_info),
        )

    def _compute_cpu_info(self) -> CPUInfo:
        """Gathers and computes all CPU information.

        This internal method is responsible for collecting data from various
        sources, such as `/proc/cpuinfo` and the `lscpu` command, and
        organizing it into a structured dataclass. It also triggers
        analyses for CPU features, topology, and optimization.

        Returns:
            A CPUInfo dataclass containing detailed CPU information.
        """
        info = CPUInfo()

        # Get all data sources once to avoid repeated system calls
        cpuinfo_content = self._get_cached_or_compute(
            "cpuinfo", lambda: self.system.read_file("/proc/cpuinfo")
        )
        lscpu_result = self._get_cached_or_compute(
            "lscpu", lambda: self.system.run_command(["lscpu"])
        )

        # Process basic CPU info
        self._process_basic_cpu_info(info, cpuinfo_content, lscpu_result)

        # Process CPU features (reuse cpuinfo_content)
        if cpuinfo_content:
            self._process_cpu_features(info, cpuinfo_content)

        # Get dynamic information (frequency, governor)
        self._get_frequency_info(info)

        # Get topology information
        self._get_topology_info(info)

        # Get cache information
        self._get_cache_info(info)

        # Get optimization analysis
        self._analyze_cpu_optimization(info)

        return info

    def _process_basic_cpu_info(
        self,
        info: CPUInfo,
        cpuinfo_content: Optional[str],
        lscpu_result: Any,
    ) -> None:
        """Processes basic CPU information from `/proc/cpuinfo` and `lscpu`.

        This method extracts fundamental CPU details, such as model name,
        vendor ID, and architecture, from the provided data sources and
        populates the `info` dataclass.

        Args:
            info: The CPUInfo dataclass to populate.
            cpuinfo_content: The content of `/proc/cpuinfo`.
            lscpu_result: The result of the `lscpu` command.
        """
        # Process /proc/cpuinfo data
        if cpuinfo_content:
            cpuinfo_data = self._parse_cpuinfo(cpuinfo_content)
            info.product = cpuinfo_data.get("model_name")
            info.vendor = cpuinfo_data.get("vendor_id")
        else:
            # Handle error case if needed
            pass

        # Process lscpu data
        if lscpu_result and lscpu_result.success:
            lscpu_info = self._parse_lscpu(lscpu_result.stdout)
            info.architecture = lscpu_info.get("architecture")
            info.cpu_op_modes = lscpu_info.get("cpu_op_modes")
            info.byte_order = lscpu_info.get("byte_order")
            info.lscpu_flags = lscpu_info.get("lscpu_flags", [])

            # Extract width and version from lscpu output
            width_match = re.search(r"CPU max MHz:\s*(\d+)", lscpu_result.stdout)
            if width_match:
                info.width = 64  # Assuming 64-bit if lscpu is present

            version_match = re.search(r"Model name:\s*(.*)", lscpu_result.stdout)
            if version_match:
                version_str = version_match.group(1)
                version_num_match = re.search(r"(\d+\.\d+\.\d+)", version_str)
                if version_num_match:
                    info.version = version_num_match.group(1)
                else:
                    info.version = version_str

            # Get performance analysis (feature detection and frequency)
            info.performance_analysis = self._analyze_cpu_performance(lscpu_info)
        else:
            # Handle error case if needed
            pass

    def _process_cpu_features(self, info: CPUInfo, cpuinfo_content: str) -> None:
        """Processes CPU features and vulnerabilities.

        This method analyzes the CPU flags from `/proc/cpuinfo` to identify
        supported security, performance, and virtualization features. It also
        checks for known CPU vulnerabilities by inspecting the relevant sysfs
        files.

        Args:
            info: The CPUInfo dataclass to populate.
            cpuinfo_content: The content of `/proc/cpuinfo`.
        """
        # Extract and analyze CPU flags
        flags = self._extract_cpu_flags(cpuinfo_content)
        info.cpu_flags = flags
        info.security_features = self._analyze_security_features(flags)
        info.performance_features = self._analyze_performance_features(flags)
        info.virtualization_features = self._analyze_virtualization_features(flags)

        # Get CPU vulnerabilities
        info.vulnerabilities = self._get_cached_or_compute(
            "vulnerabilities", self._get_cpu_vulnerabilities
        )

    def _get_frequency_info(self, info: CPUInfo) -> None:
        """Retrieves detailed CPU frequency and governor information."""
        # This data is not cached as it's dynamic
        freq_info: Dict[str, Any] = {}
        current_freq = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
        )
        if current_freq:
            freq_info["current_frequency_khz"] = int(current_freq)
            freq_info["current_frequency_mhz"] = round(int(current_freq) / 1000, 2)
        info.performance_analysis.update(freq_info)

    def _get_topology_info(self, info: CPUInfo) -> None:
        """Retrieves CPU topology information."""
        topology = self._get_cached_or_compute(
            "topology", self._compute_topology_info
        )
        info.topology = topology

    def _compute_topology_info(self) -> Dict[str, Any]:
        """Computes CPU topology information."""
        topology: Dict[str, Any] = {}
        nproc_result = self.system.run_command(["nproc"])
        if nproc_result.success:
            topology["logical_cpus"] = int(nproc_result.stdout)
        return topology

    def _get_cache_info(self, info: CPUInfo) -> None:
        """Retrieves information about the CPU cache hierarchy."""
        cache = self._get_cached_or_compute("cache", self._compute_cache_info)
        info.cache = cache

    def _compute_cache_info(self) -> Dict[str, Any]:
        """Computes CPU cache information."""
        cache_info: Dict[str, Any] = {}
        for cache_level in ["index0", "index1", "index2", "index3"]:
            cache_path = f"/sys/devices/system/cpu/cpu0/cache/{cache_level}"
            try:
                if self.system.file_exists(f"{cache_path}/size"):
                    size = self.system.read_file(f"{cache_path}/size")
                    ctype = self.system.read_file(f"{cache_path}/type")
                    level = self.system.read_file(f"{cache_path}/level")
                    if size and ctype and level:
                        level_val = level.strip()
                        ctype_val = ctype.strip()

                        level_key = f"L{level_val}"
                        if level_val == "1":
                            if ctype_val == "Data":
                                level_key = "L1d"
                            elif ctype_val == "Instruction":
                                level_key = "L1i"

                        cache_info[level_key] = {
                            "size": size.strip(),
                            "type": ctype_val,
                            "level": level_val,
                            "coherency_line_size": self.system.read_file(f"{cache_path}/coherency_line_size"),
                            "number_of_sets": self.system.read_file(f"{cache_path}/number_of_sets"),
                            "physical_line_partition": self.system.read_file(f"{cache_path}/physical_line_partition"),
                        }
            except (IOError, OSError, FileNotFoundError) as e:
                # Log the error, but continue to the next cache level
                print(f"Could not read cache info for {cache_path}: {e}")
                continue
        return cache_info

    def _analyze_cpu_optimization(self, info: CPUInfo) -> None:
        """Analyzes the CPU configuration for optimization opportunities."""
        recommendations = []
        current_governor = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        )
        if current_governor == "powersave":
            recommendations.append(
                {
                    "type": "performance",
                    "issue": "CPU governor set to powersave",
                    "recommendation": "Consider using performance or ondemand governor for better performance",
                    "command": "echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor",
                }
            )

        # Check for CPU vulnerabilities
        vulnerabilities = self._get_cpu_vulnerabilities()
        vulnerable_count = sum(
            1 for vuln in vulnerabilities.values() if "Vulnerable" in str(vuln)
        )
        if vulnerable_count > 0:
            recommendations.append(
                {
                    "type": "security",
                    "issue": f"{vulnerable_count} CPU vulnerabilities detected",
                    "recommendation": (
                        "Update kernel and microcode to mitigate CPU vulnerabilities"
                    ),
                    "command": (
                        "sudo apt update && sudo apt upgrade linux-generic "
                        "intel-microcode"
                    ),
                }
            )
        info.optimization_recommendations = recommendations

    def _analyze_cpu_performance(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes CPU performance, including feature support and frequency.

        This method checks for advanced CPU features like AVX2 and gathers
        real-time frequency data using `psutil`. It is designed to be
        extensible for future performance-related metrics.

        Args:
            info: A dictionary containing previously gathered CPU information,
                  including `lscpu_flags`.

        Returns:
            A dictionary with performance-related analysis, including
            supported optimizations and current CPU frequency.
        """
        performance_info: Dict[str, Any] = {}
        lscpu_flags = info.get("lscpu_flags", [])

        # Check for specific optimization flags
        optimizations = {
            "avx_supported": "avx" in lscpu_flags,
            "avx2_supported": "avx2" in lscpu_flags,
            "avx512f_supported": "avx512f" in lscpu_flags,
            "sse4_1_supported": "sse4_1" in lscpu_flags,
            "sse4_2_supported": "sse4_2" in lscpu_flags,
        }
        performance_info["optimizations"] = optimizations

        # Get CPU frequency using psutil as a fallback or primary source
        try:
            freq = psutil.cpu_freq()
            if freq:
                performance_info["psutil_cpu_frequency"] = {
                    "current": freq.current,
                    "min": freq.min,
                    "max": freq.max,
                }
        except (AttributeError, NotImplementedError, PermissionError) as e:
            performance_info["psutil_cpu_frequency_error"] = str(e)
        except Exception as e:
            # Catch any other unexpected errors from psutil
            performance_info["psutil_cpu_frequency_error"] = (
                f"An unexpected error occurred: {e}"
            )

        # Get CPU stats using psutil
        try:
            stats = psutil.cpu_stats()
            if stats:
                performance_info["psutil_cpu_stats"] = {
                    "context_switches": stats.ctx_switches,
                    "interrupts": stats.interrupts,
                    "soft_interrupts": stats.soft_interrupts,
                    "syscalls": stats.syscalls,
                }
        except (AttributeError, NotImplementedError, PermissionError) as e:
            performance_info["psutil_cpu_stats_error"] = str(e)
        except Exception as e:
            # Catch any other unexpected errors from psutil
            performance_info["psutil_cpu_stats_error"] = (
                f"An unexpected error occurred: {e}"
            )

        return {"performance_analysis": performance_info}

    def _parse_cpuinfo(self, cpuinfo_content: str) -> Dict[str, Any]:
        """Parses the content of `/proc/cpuinfo`.

        This method uses regular expressions to extract key-value information
        from the `/proc/cpuinfo` file, such as the model name, vendor ID,
        and CPU family.

        Args:
            cpuinfo_content: The string content of `/proc/cpuinfo`.

        Returns:
            A dictionary containing the parsed information.
        """
        info: Dict[str, Any] = {}

        # Extract model name
        model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo_content)
        if model_match:
            info["model_name"] = model_match.group(1).strip()

        # Extract vendor ID
        vendor_match = re.search(r"vendor_id\s*:\s*(.+)", cpuinfo_content)
        if vendor_match:
            info["vendor_id"] = vendor_match.group(1).strip()

        # Extract CPU family
        family_match = re.search(r"cpu family\s*:\s*(.+)", cpuinfo_content)
        if family_match:
            info["cpu_family"] = family_match.group(1).strip()

        # Extract model
        model_match = re.search(r"^model\s*:\s*(.+)", cpuinfo_content, re.MULTILINE)
        if model_match:
            info["model"] = model_match.group(1).strip()

        # Extract stepping
        stepping_match = re.search(r"stepping\s*:\s*(.+)", cpuinfo_content)
        if stepping_match:
            info["stepping"] = stepping_match.group(1).strip()

        return info

    def _parse_lscpu(self, lscpu_output: str) -> Dict[str, Any]:
        """Parses the output of the `lscpu` command.

        This method extracts information from the `lscpu` command's output,
        such as the CPU architecture, op-modes, and byte order.

        Args:
            lscpu_output: The string output of the `lscpu` command.

        Returns:
            A dictionary containing the parsed information.
        """
        info: Dict[str, Any] = {}

        # Extract architecture
        arch_match = re.search(r"Architecture:\s*(.+)", lscpu_output)
        if arch_match:
            info["architecture"] = arch_match.group(1).strip()

        # Extract CPU op-modes
        opmode_match = re.search(r"CPU op-mode\(s\):\s*(.+)", lscpu_output)
        if opmode_match:
            info["cpu_op_modes"] = opmode_match.group(1).strip()

        # Extract byte order
        byte_order_match = re.search(r"Byte Order:\s*(.+)", lscpu_output)
        if byte_order_match:
            info["byte_order"] = byte_order_match.group(1).strip()

        # Extract flags
        flags_match = re.search(r"Flags:\s*(.+)", lscpu_output)
        if flags_match:
            info["lscpu_flags"] = flags_match.group(1).strip().split()

        return info

    def _extract_cpu_flags(self, cpuinfo_content: str) -> List[str]:
        """Extracts the CPU flags from the `/proc/cpuinfo` content.

        Args:
            cpuinfo_content: The string content of `/proc/cpuinfo`.

        Returns:
            A list of strings, where each string is a CPU flag.
        """
        flags_match = re.search(r"flags\s*:\s*(.+)", cpuinfo_content)
        if flags_match:
            return flags_match.group(1).strip().split()
        return []

    def _analyze_security_features(self, flags: List[str]) -> Dict[str, bool]:
        """Analyzes the security-related CPU features from a list of flags.

        Args:
            flags: A list of CPU flags.

        Returns:
            A dictionary indicating the presence of various security features.
        """
        security_features = {
            "nx_bit": "nx" in flags,  # No-execute bit
            "smep": "smep" in flags,  # Supervisor Mode Execution Prevention
            "smap": "smap" in flags,  # Supervisor Mode Access Prevention
            "intel_pt": "intel_pt" in flags,  # Intel Processor Trace
            "cet_ss": "cet_ss"
            in flags,  # Control-flow Enforcement Technology Shadow Stack
            "cet_ibt": "cet_ibt"
            in flags,  # Control-flow Enforcement Technology Indirect Branch Tracking
        }
        return security_features

    def _analyze_performance_features(self, flags: List[str]) -> Dict[str, bool]:
        """Analyzes the performance-related CPU features from a list of flags.

        Args:
            flags: A list of CPU flags.

        Returns:
            A dictionary indicating the presence of various performance features.
        """
        performance_features = {
            "sse": "sse" in flags,
            "sse2": "sse2" in flags,
            "sse3": "pni" in flags,  # pni = Prescott New Instructions (SSE3)
            "ssse3": "ssse3" in flags,
            "sse4_1": "sse4_1" in flags,
            "sse4_2": "sse4_2" in flags,
            "avx": "avx" in flags,
            "avx2": "avx2" in flags,
            "avx512f": "avx512f" in flags,
            "aes": "aes" in flags,  # AES acceleration
            "rdrand": "rdrand" in flags,  # Hardware random number generator
            "rdseed": "rdseed" in flags,  # Hardware random seed generator
        }
        return performance_features

    def _analyze_virtualization_features(self, flags: List[str]) -> Dict[str, bool]:
        """Analyzes the virtualization-related CPU features from a list of flags.

        Args:
            flags: A list of CPU flags.

        Returns:
            A dictionary indicating the presence of various virtualization
            features.
        """
        virt_features = {
            "vmx": "vmx" in flags,  # Intel VT-x
            "svm": "svm" in flags,  # AMD-V
            "ept": "ept" in flags,  # Extended Page Tables
            "vpid": "vpid" in flags,  # Virtual Processor ID
        }
        return virt_features

    def _get_cpu_vulnerabilities(self) -> Dict[str, str]:
        """Retrieves information about CPU vulnerabilities from sysfs.

        This method checks for the status of common CPU vulnerabilities by
        reading the corresponding files in `/sys/devices/system/cpu/vulnerabilities/`.

        Returns:
            A dictionary where keys are vulnerability names and values are their
            reported statuses.
        """
        vulnerabilities = {}

        # Common CPU vulnerabilities to check
        vuln_files = [
            "spectre_v1",
            "spectre_v2",
            "meltdown",
            "spec_store_bypass",
            "l1tf",
            "mds",
            "tsx_async_abort",
            "itlb_multihit",
            "srbds",
        ]

        for vuln in vuln_files:
            vuln_path = f"/sys/devices/system/cpu/vulnerabilities/{vuln}"
            vuln_status = self.system.read_file(vuln_path)
            if vuln_status:
                vulnerabilities[vuln] = vuln_status

        return vulnerabilities
