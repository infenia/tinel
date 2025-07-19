"""Infenix - Linux Hardware and Kernel Intelligence Tool.

A next-generation open-source platform designed to control, optimize, and
analyze Linux-based systems using AI and LLMs. Developed by Infenia Private
Limited, Infenix interfaces with the Linux kernel through various system
utilities and filesystem interfaces to gather detailed hardware data.

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

from . import diagnostics, kernel, logs
from .interfaces import (
    CommandResult,
    Diagnostic,
    DiagnosticsProvider,
    HardwareAnalyzer,
    HardwareInfo,
    KernelAnalyzer,
    KernelConfig,
    KernelConfigOption,
    LogAnalyzer,
    LogAnalysis,
    LogEntry,
    SystemInterface,
    ToolProvider,
)

__version__ = "0.1.0"
__author__ = "Infenia Private Limited"
__license__ = "Apache-2.0"

__all__ = [
    "diagnostics",
    "kernel", 
    "logs",
    "CommandResult",
    "Diagnostic",
    "DiagnosticsProvider",
    "HardwareAnalyzer",
    "HardwareInfo",
    "KernelAnalyzer",
    "KernelConfig",
    "KernelConfigOption",
    "LogAnalyzer",
    "LogAnalysis",
    "LogEntry",
    "SystemInterface",
    "ToolProvider",
]