#!/usr/bin/env python3
"""Core Interfaces for Infenix.

This module defines the core interfaces and abstract base classes that
establish system boundaries and contracts between different components.

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

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a system command execution."""
    
    success: bool
    stdout: str
    stderr: str
    returncode: int
    error: Optional[str] = None


@dataclass
class LogEntry:
    """Represents a single log entry."""
    
    timestamp: datetime
    facility: str
    severity: str
    message: str
    source: str


@dataclass
class KernelConfigOption:
    """Represents a kernel configuration option."""
    
    name: str
    value: str
    description: str
    recommended: Optional[str] = None
    security_impact: Optional[str] = None
    performance_impact: Optional[str] = None


@dataclass
class HardwareInfo:
    """Comprehensive hardware information."""
    
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    storage: Dict[str, Any]
    pci_devices: Dict[str, Any]
    usb_devices: Dict[str, Any]
    network: Dict[str, Any]
    graphics: Dict[str, Any]


@dataclass
class KernelConfig:
    """Kernel configuration information."""
    
    version: str
    options: Dict[str, KernelConfigOption]
    analysis: Dict[str, Any]
    recommendations: Dict[str, Any]


@dataclass
class LogAnalysis:
    """Log analysis results."""
    
    entries: List[LogEntry]
    patterns: Dict[str, Any]
    issues: Dict[str, Any]
    summary: Dict[str, Any]


@dataclass
class Diagnostic:
    """System diagnostic information."""
    
    hardware: HardwareInfo
    kernel_config: Optional[KernelConfig]
    log_analysis: Optional[LogAnalysis]
    recommendations: Dict[str, Any]
    explanation: str


class SystemInterface(ABC):
    """Abstract interface for system interactions."""
    
    @abstractmethod
    def run_command(self, cmd: List[str]) -> CommandResult:
        """Execute a system command and return the result."""
        pass
    
    @abstractmethod
    def read_file(self, path: str) -> Optional[str]:
        """Read a file from the filesystem."""
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        pass


class HardwareAnalyzer(ABC):
    """Abstract interface for hardware analysis."""
    
    @abstractmethod
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information."""
        pass
    
    @abstractmethod
    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information."""
        pass
    
    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """Get detailed storage information."""
        pass
    
    @abstractmethod
    def get_all_hardware_info(self) -> HardwareInfo:
        """Get comprehensive hardware information."""
        pass


class KernelAnalyzer(ABC):
    """Abstract interface for kernel configuration analysis."""
    
    @abstractmethod
    def get_kernel_config(self) -> Optional[KernelConfig]:
        """Get current kernel configuration."""
        pass
    
    @abstractmethod
    def analyze_config(self, config: KernelConfig) -> Dict[str, Any]:
        """Analyze kernel configuration for issues and optimizations."""
        pass
    
    @abstractmethod
    def get_recommendations(self, config: KernelConfig, hardware: HardwareInfo) -> Dict[str, Any]:
        """Get optimization recommendations based on hardware and configuration."""
        pass


class LogAnalyzer(ABC):
    """Abstract interface for log analysis."""
    
    @abstractmethod
    def parse_logs(self, log_sources: List[str]) -> List[LogEntry]:
        """Parse system logs from various sources."""
        pass
    
    @abstractmethod
    def detect_patterns(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Detect patterns in log entries."""
        pass
    
    @abstractmethod
    def analyze_logs(self, entries: List[LogEntry]) -> LogAnalysis:
        """Analyze logs for issues and patterns."""
        pass


class DiagnosticsProvider(ABC):
    """Abstract interface for AI-powered diagnostics."""
    
    @abstractmethod
    def diagnose_system(
        self,
        hardware: HardwareInfo,
        kernel_config: Optional[KernelConfig] = None,
        log_analysis: Optional[LogAnalysis] = None
    ) -> Diagnostic:
        """Provide comprehensive system diagnostics."""
        pass
    
    @abstractmethod
    def interpret_query(self, query: str) -> Dict[str, Any]:
        """Interpret natural language queries about the system."""
        pass
    
    @abstractmethod
    def generate_recommendations(self, diagnostic: Diagnostic) -> Dict[str, Any]:
        """Generate actionable recommendations based on diagnostics."""
        pass


class ToolProvider(ABC):
    """Abstract interface for MCP tool providers."""
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """Get the name of the tool."""
        pass
    
    @abstractmethod
    def get_tool_description(self) -> str:
        """Get the description of the tool."""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        pass
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass