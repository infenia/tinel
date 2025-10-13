#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware information module for Tinel.

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

from .cpu_analyzer import CPUAnalyzer
from .graphics_analyzer import GraphicsAnalyzer
from .memory_analyzer import MemoryAnalyzer
from .models import HardwareInfo, PCIInfo, USBInfo
from .network_analyzer import NetworkAnalyzer
from .storage_analyzer import StorageAnalyzer

__all__ = [
    "HardwareInfo",
    "CPUAnalyzer",
    "NetworkAnalyzer",
    "GraphicsAnalyzer",
    "MemoryAnalyzer",
    "StorageAnalyzer",
    "PCIInfo",
    "USBInfo",
]
