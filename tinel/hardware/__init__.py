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
# -*- coding: utf-8 -*-
"""Hardware information module for Tinel."""
import dataclasses
from typing import Any, Dict

from .cpu_analyzer import CPUAnalyzer


@dataclasses.dataclass
class HardwareInfo:
    """A dataclass to store hardware information."""

    cpu: Dict[str, Any] = dataclasses.field(default_factory=dict)
    memory: Dict[str, Any] = dataclasses.field(default_factory=dict)
    disks: Dict[str, Any] = dataclasses.field(default_factory=dict)
    gpu: Dict[str, Any] = dataclasses.field(default_factory=dict)
    network: Dict[str, Any] = dataclasses.field(default_factory=dict)
    motherboard: Dict[str, Any] = dataclasses.field(default_factory=dict)


__all__ = ["HardwareInfo", "CPUAnalyzer"]