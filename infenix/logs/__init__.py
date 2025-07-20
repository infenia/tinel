#!/usr/bin/env python3
"""Log Analysis Module.

This module provides tools to parse and analyze system logs for patterns
and issues. It identifies patterns indicating hardware and kernel issues,
correlates log entries with hardware events, and provides summaries.

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

from .log_parser import LogParser
from .pattern_detector import PatternDetector
from .log_analyzer import LogAnalyzer
from .streaming_parser import StreamingLogParser, StreamingConfig, IncrementalLogAnalyzer

__all__ = [
    "LogParser",
    "PatternDetector",
    "LogAnalyzer",
    "StreamingLogParser",
    "StreamingConfig",
    "IncrementalLogAnalyzer",
]