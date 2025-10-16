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

"""Detects issue patterns in log entries using regular expressions."""

import re
from typing import Dict, List

from .models import LogAnalysis, LogEntry

# A dictionary of regex patterns to detect common issues.
PATTERNS: Dict[str, re.Pattern] = {
    "hardware": re.compile(r"hardware error", re.IGNORECASE),
    "kernel": re.compile(r"kernel panic", re.IGNORECASE),
    "oom": re.compile(r"out of memory", re.IGNORECASE),
    "segfault": re.compile(r"segmentation fault", re.IGNORECASE),
}


def detect_patterns(entries: List[LogEntry]) -> List[LogAnalysis]:
    """
    Analyzes a list of log entries to detect predefined issue patterns.

    This function iterates through a list of LogEntry objects and matches their
    messages against a dictionary of compiled regular expression patterns.
    When a match is found, the entry is added to a corresponding LogAnalysis
    object, which aggregates all entries for a given issue type.

    Args:
        entries: A list of LogEntry objects to be analyzed.

    Returns:
        A list of LogAnalysis objects, each representing a detected
        issue type and containing the corresponding log entries. If no
        patterns are matched, an empty list is returned.
    """
    analyses: Dict[str, LogAnalysis] = {}
    for entry in entries:
        for issue_type, pattern in PATTERNS.items():
            if pattern.search(entry.message):
                if issue_type not in analyses:
                    analyses[issue_type] = LogAnalysis(
                        issue_type=issue_type,
                        summary=f"Detected {issue_type} issues.",
                    )
                analyses[issue_type].add_entry(entry)
                # An entry can match multiple patterns, so we don't break here.
                # If we wanted to assign an entry to only the first pattern it
                # matches, we would add a `break`.
    return list(analyses.values())
