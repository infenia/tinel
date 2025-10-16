# --- T-NEL LINUX SYSTEM ANALYZER ---
#
# Copyright (c) 2024 Battelle Memorial Institute
#
# Battelle Memorial Institute (hereinafter Battelle) hereby grants permission
# to any person or entity obtaining a copy of this software and associated
# documentation files (hereinafter "the Software") to deal in the Software
# without restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# 1. The above copyright notice and this permission notice shall be included
#    in all copies or substantial portions of the Software.
#
# 2. The Software is licensed under the MIT License, which can be found in the
#    LICENSE file accompanying the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Advanced log analysis, including correlation and summarization."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Dict, List

from .models import LogAnalysis, LogEntry
from .pattern_detector import PATTERNS, detect_patterns


def correlate_with_hardware(
    analyses: Dict[str, LogAnalysis], time_window: timedelta = timedelta(minutes=10)
) -> None:
    """
    Correlates log entries with hardware events within a given time window.

    This function identifies hardware error events and searches for other
    log entries (e.g., kernel panics, OOM errors) that occurred within the
    specified time window around the hardware event.

    Args:
        analyses: A dictionary of LogAnalysis objects, keyed by issue type.
        time_window: The time delta for the correlation window.
    """
    if "hardware" not in analyses:
        return

    hardware_events = analyses["hardware"].entries
    for hw_event in hardware_events:
        start_window = hw_event.timestamp - time_window
        end_window = hw_event.timestamp + time_window
        for issue_type, analysis in analyses.items():
            if issue_type == "hardware":
                continue
            for entry in analysis.entries:
                if start_window <= entry.timestamp <= end_window:
                    correlation_id = (
                        f"Correlated with hardware event at "
                        f"{hw_event.timestamp.isoformat()}"
                    )
                    if correlation_id not in analysis.correlated_events:
                        analysis.correlated_events.append(correlation_id)


def detailed_analysis(entry: LogEntry) -> str:
    """
    Provides a detailed analysis of a single log entry.

    This function extracts and formats key information from a log entry and
    identifies potential causes by matching it against predefined patterns.

    Args:
        entry: The LogEntry to analyze.

    Returns:
        A formatted string containing the detailed analysis.
    """
    potential_causes = [
        issue_type
        for issue_type, pattern in PATTERNS.items()
        if pattern.search(entry.message)
    ]

    causes_str = (
        ", ".join(potential_causes)
        if potential_causes
        else "No specific pattern detected."
    )

    return (
        f"Timestamp: {entry.timestamp.isoformat()}\n"
        f"Source: {entry.source}\n"
        f"Facility: {entry.facility}\n"
        f"Level: {entry.level}\n"
        f"Host: {entry.host or 'N/A'}\n"
        f"Process: {entry.process or 'N/A'}\n"
        f"Message: {entry.message}\n"
        f"Potential Cause(s): {causes_str}"
    )


def analyze_logs(
    entries: List[LogEntry], patterns: Dict[str, re.Pattern] = PATTERNS
) -> List[LogAnalysis]:
    """
    Performs advanced analysis on a list of log entries.

    This function orchestrates the entire analysis pipeline:
    1. Detects patterns in the log entries.
    2. Correlates events with hardware issues.
    3. Generates enhanced, descriptive summaries for each issue type.

    Args:
        entries: A list of LogEntry objects to be analyzed.
        patterns: A dictionary of regex patterns to detect issues.

    Returns:
        A list of LogAnalysis objects with correlated events and
        enhanced summaries.
    """
    if not entries:
        return []

    # 1. Detect patterns
    detected_analyses_list = detect_patterns(entries)
    analyses: Dict[str, LogAnalysis] = {
        analysis.issue_type: analysis for analysis in detected_analyses_list
    }

    # 2. Correlate with hardware events
    correlate_with_hardware(analyses)

    # 3. Enhance summaries
    for issue_type, analysis in analyses.items():
        if analysis.count > 0:
            min_ts = min(entry.timestamp for entry in analysis.entries)
            max_ts = max(entry.timestamp for entry in analysis.entries)
            analysis.summary = (
                f"{analysis.count} {issue_type} issue(s) detected "
                f"between {min_ts.isoformat()} and {max_ts.isoformat()}."
            )

    return list(analyses.values())
