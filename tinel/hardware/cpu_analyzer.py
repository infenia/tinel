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

"""This module provides a detailed analysis of the CPU.

It includes the `CPUAnalyzer` class, which gathers comprehensive information
about the CPU, such as model, vendor, features, topology, and vulnerabilities.
The analyzer uses a combination of system files, commands, and the `psutil`
library to provide a complete picture of the CPU's capabilities and status.
"""


class CPUAnalyzer:
    """Analyzes and retrieves detailed information about the system's CPU.

    This class provides a comprehensive analysis of the CPU, including its
    model, features, performance characteristics, and security vulnerabilities.
    It uses a caching mechanism to improve performance for repeated queries.

    Args:
        system_interface: An optional `SystemInterface` implementation for
                          executing commands and reading files. If not provided,
                          a `LinuxSystemInterface` instance is created.
    """

    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initializes the CPUAnalyzer.

        Args:
            system_interface: An optional `SystemInterface` for system
                              interactions.
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

    def get_cpu_info(self) -> Dict[str, Any]:
        """Retrieves comprehensive information about the CPU.

        This is the main public method of the class. It orchestrates the
        gathering of all CPU-related data, including basic information,
        features, topology, and cache details. The result is cached to
        optimize subsequent calls.

        Returns:
            A dictionary containing a detailed breakdown of CPU information.
        """
        return cast(
            Dict[str, Any],
            self._get_cached_or_compute("cpu_info_full", self._compute_cpu_info),
        )

    def _compute_cpu_info(self) -> Dict[str, Any]:
        """Gathers and computes all CPU information.

        This internal method is responsible for collecting data from various
        sources, such as `/proc/cpuinfo` and the `lscpu` command, and
        organizing it into a structured dictionary. It also triggers
        analyses for CPU features, topology, and optimization.

        Returns:
            A dictionary containing detailed CPU information.
        """
        info: Dict[str, Any] = {}

        # Get all data sources once to avoid repeated system calls
        cpuinfo_content = self._get_cached_or_compute(
            "cpuinfo", lambda: self.system.read_file("/proc/cpuinfo")
        )
        lscpu_output = self._get_cached_or_compute(
            "lscpu", lambda: self.system.run_command(["lscpu"])
        )

        # Process basic CPU info
        info.update(self._process_basic_cpu_info(cpuinfo_content, lscpu_output))

        # Process CPU features (reuse cpuinfo_content)
        if cpuinfo_content:
            info.update(self._process_cpu_features(cpuinfo_content))

        # Get dynamic information (frequency, governor) - don't cache this
        info.update(self._get_frequency_info())

        # Get topology information - cache this
        info.update(self._get_cached_or_compute("topology", self._get_topology_info))

        # Get cache information - cache this
        info.update(self._get_cached_or_compute("cache", self._get_cache_info))

        # Get optimization analysis
        info.update(self._analyze_cpu_optimization())

        return info

    def _process_basic_cpu_info(
        self, cpuinfo_content: Optional[str], lscpu_result: Any
    ) -> Dict[str, Any]:
        """Processes basic CPU information from `/proc/cpuinfo` and `lscpu`.

        This method extracts fundamental CPU details, such as model name,
        vendor ID, and architecture, from the provided data sources. It is
        called by `_compute_cpu_info` to populate the initial information.

        Args:
            cpuinfo_content: The content of `/proc/cpuinfo`.
            lscpu_result: The result of the `lscpu` command.

        Returns:
            A dictionary containing the processed basic CPU information.
        """
        info: Dict[str, Any] = {}

        # Process /proc/cpuinfo data
        if cpuinfo_content:
            info["proc_cpuinfo"] = cpuinfo_content
            info.update(self._parse_cpuinfo(cpuinfo_content))
        else:
            info["proc_cpuinfo_error"] = "Failed to read /proc/cpuinfo"

        # Process lscpu data
        if lscpu_result and lscpu_result.success:
            info["lscpu"] = lscpu_result.stdout
            lscpu_info = self._parse_lscpu(lscpu_result.stdout)
            info.update(lscpu_info)
            # Get performance analysis (feature detection and frequency)
            info.update(self._analyze_cpu_performance(lscpu_info))
        else:
            error_msg = lscpu_result.error if lscpu_result else "Failed to run lscpu"
            info["lscpu_error"] = error_msg

        return info

    def _process_cpu_features(self, cpuinfo_content: str) -> Dict[str, Any]:
        """Processes CPU features and vulnerabilities.

        This method analyzes the CPU flags from `/proc/cpuinfo` to identify
        supported security, performance, and virtualization features. It also
        checks for known CPU vulnerabilities by inspecting the relevant sysfs
        files.

        Args:
            cpuinfo_content: The content of `/proc/cpuinfo`.

        Returns:
            A dictionary containing detailed information about CPU features
            and vulnerabilities.
        """
        info: Dict[str, Any] = {}

        # Extract and analyze CPU flags
        flags = self._extract_cpu_flags(cpuinfo_content)
        info["cpu_flags"] = flags
        info["security_features"] = self._analyze_security_features(flags)
        info["performance_features"] = self._analyze_performance_features(flags)
        info["virtualization_features"] = self._analyze_virtualization_features(flags)

        # Get CPU vulnerabilities (cache this separately as it's file system intensive)
        info["vulnerabilities"] = self._get_cached_or_compute(
            "vulnerabilities", self._get_cpu_vulnerabilities
        )

        return info

    def _get_frequency_info(self) -> Dict[str, Any]:
        """Retrieves detailed CPU frequency and governor information.

        This method reads data from the `cpufreq` sysfs interface to determine
        the current, minimum, and maximum CPU frequencies, as well as the
        available and current CPU governors.

        Returns:
            A dictionary containing CPU frequency and governor details.
        """
        info: Dict[str, Any] = {}

        # Get current frequency
        current_freq = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
        )
        if current_freq:
            info["current_frequency_khz"] = int(current_freq)
            info["current_frequency_mhz"] = round(int(current_freq) / 1000, 2)

        # Get min/max frequencies
        min_freq = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq"
        )
        if min_freq:
            info["min_frequency_khz"] = int(min_freq)
            info["min_frequency_mhz"] = round(int(min_freq) / 1000, 2)

        max_freq = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq"
        )
        if max_freq:
            info["max_frequency_khz"] = int(max_freq)
            info["max_frequency_mhz"] = round(int(max_freq) / 1000, 2)

        # Get available governors
        governors = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
        )
        if governors:
            info["available_governors"] = governors.split()

        # Get current governor
        current_governor = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        )
        if current_governor:
            info["current_governor"] = current_governor

        return info

    def _get_topology_info(self) -> Dict[str, Any]:
        """Retrieves CPU topology information, such as core and thread counts.

        This method determines the number of logical and physical CPUs, as well
        as the number of cores per socket. It uses a combination of system
        commands and sysfs files, and cross-verifies the results with `psutil`.

        Returns:
            A dictionary containing CPU topology details.
        """
        info: Dict[str, Any] = {}

        # Get number of CPUs
        nproc_result = self.system.run_command(["nproc"])
        if nproc_result.success:
            info["logical_cpus"] = int(nproc_result.stdout)

        # Get physical CPU count
        physical_cpus = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/topology/physical_package_id"
        )
        if physical_cpus is not None:
            # Count unique physical package IDs
            package_ids = set()
            cpu_num = 0
            while True:
                package_id = self.system.read_file(
                    f"/sys/devices/system/cpu/cpu{cpu_num}/topology/physical_package_id"
                )
                if package_id is None:
                    break
                package_ids.add(package_id)
                cpu_num += 1
            info["physical_cpus"] = len(package_ids)

        # Get cores per socket
        core_id = self.system.read_file("/sys/devices/system/cpu/cpu0/topology/core_id")
        if core_id is not None:
            core_ids = set()
            cpu_num = 0
            while True:
                core_id = self.system.read_file(
                    f"/sys/devices/system/cpu/cpu{cpu_num}/topology/core_id"
                )
                if core_id is None:
                    break
                core_ids.add(core_id)
                cpu_num += 1
            info["cores_per_socket"] = len(core_ids)

        # Cross-verify with psutil
        try:
            info["logical_cpus_psutil"] = psutil.cpu_count(logical=True)
            info["physical_cores_psutil"] = psutil.cpu_count(logical=False)
        except Exception as e:
            info["psutil_error"] = str(e)

        return info

    def _get_cache_info(self) -> Dict[str, Any]:
        """Retrieves information about the CPU cache hierarchy.

        This method inspects the sysfs filesystem to discover the different
        levels of CPU cache (L1, L2, L3), their sizes, and their types (e.g.,
        Data, Instruction, Unified).

        Returns:
            A dictionary containing details about the CPU cache.
        """
        info: Dict[str, Any] = {}
        cache_info = {}

        # Check for cache information in /sys/devices/system/cpu/cpu0/cache/
        for cache_level in ["index0", "index1", "index2", "index3"]:
            cache_path = f"/sys/devices/system/cpu/cpu0/cache/{cache_level}"
            if self.system.file_exists(f"{cache_path}/size"):
                cache_size = self.system.read_file(f"{cache_path}/size")
                cache_type = self.system.read_file(f"{cache_path}/type")
                cache_level_num = self.system.read_file(f"{cache_path}/level")

                if cache_size and cache_type and cache_level_num:
                    cache_info[f"L{cache_level_num}"] = {
                        "size": cache_size,
                        "type": cache_type,
                    }

        if cache_info:
            info["cache"] = cache_info

        return info

    def _analyze_cpu_optimization(self) -> Dict[str, Any]:
        """Analyzes the CPU configuration for optimization opportunities.

        This method checks for potential performance and security improvements,
        such as suboptimal governor settings or unmitigated CPU
        vulnerabilities. It provides actionable recommendations for addressing
        any identified issues.

        Returns:
            A dictionary containing a list of optimization recommendations.
        """
        info: Dict[str, Any] = {}
        recommendations = []

        # Check governor settings
        current_governor = self.system.read_file(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        )
        if current_governor == "powersave":
            recommendations.append(
                {
                    "type": "performance",
                    "issue": "CPU governor set to powersave",
                    "recommendation": (
                        "Consider using performance or ondemand governor "
                        "for better performance"
                    ),
                    "command": (
                        "echo performance | sudo tee "
                        "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
                    ),
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

        info["optimization_recommendations"] = recommendations
        return info

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
        performance_info["avx2_supported"] = "avx2" in lscpu_flags

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
            performance_info["psutil_cpu_frequency_error"] = f"An unexpected error occurred: {e}"

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
