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

from datetime import datetime

import pytest

from tinel.logs.models import LogEntry
from tinel.logs.pattern_detector import detect_patterns

# A common timestamp for all mock log entries
TIMESTAMP = datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def mock_log_entries():
    """Provides a list of mock LogEntry objects for testing."""
    return [
        LogEntry(
            timestamp=TIMESTAMP,
            source="syslog",
            level="error",
            facility="kernel",
            message="A critical hardware error occurred.",
        ),
        LogEntry(
            timestamp=TIMESTAMP,
            source="journald",
            level="emerg",
            facility="kernel",
            message="System encountered a KERNEL PANIC.",
        ),
        LogEntry(
            timestamp=TIMESTAMP,
            source="syslog",
            level="error",
            facility="kernel",
            message="Another HARDWARE error message.",
        ),
        LogEntry(
            timestamp=TIMESTAMP,
            source="syslog",
            level="info",
            facility="system",
            message="Normal system operation.",
        ),
        LogEntry(
            timestamp=TIMESTAMP,
            source="journald",
            level="crit",
            facility="system",
            message="Process[123]: segmentation fault at 0",
        ),
        LogEntry(
            timestamp=TIMESTAMP,
            source="syslog",
            level="warning",
            facility="memory",
            message="System is running out of memory.",
        ),
    ]


def test_detect_patterns_empty_list():
    """Test that an empty list of log entries results in an empty analysis list."""
    assert detect_patterns([]) == []


def test_detect_patterns_no_matches():
    """
    Test that log entries with no matching patterns result in an empty analysis
    list.
    """
    entries = [
        LogEntry(
            timestamp=TIMESTAMP,
            source="syslog",
            level="info",
            facility="auth",
            message="User login successful.",
        ),
        LogEntry(
            timestamp=TIMESTAMP,
            source="journald",
            level="debug",
            facility="system",
            message="A regular message.",
        ),
    ]
    assert detect_patterns(entries) == []


def test_detect_patterns_and_aggregation(mock_log_entries):
    """Test detection of multiple patterns and correct aggregation of counts."""
    analyses = detect_patterns(mock_log_entries)

    # We expect 4 types of issues to be detected
    expected_issue_types = 4
    assert len(analyses) == expected_issue_types

    analysis_map = {a.issue_type: a for a in analyses}

    # Check hardware errors
    assert "hardware" in analysis_map
    # Check hardware errors
    assert "hardware" in analysis_map
    expected_hardware_count = 2
    assert analysis_map["hardware"].count == expected_hardware_count
    assert len(analysis_map["hardware"].entries) == expected_hardware_count
    assert (
        analysis_map["hardware"].entries[0].message
        == "A critical hardware error occurred."
    )
    assert (
        analysis_map["hardware"].entries[1].message == "Another HARDWARE error message."
    )

    # Check kernel panics
    assert "kernel" in analysis_map
    assert analysis_map["kernel"].count == 1
    assert len(analysis_map["kernel"].entries) == 1
    assert (
        analysis_map["kernel"].entries[0].message
        == "System encountered a KERNEL PANIC."
    )

    # Check segmentation faults
    assert "segfault" in analysis_map
    assert analysis_map["segfault"].count == 1
    assert (
        analysis_map["segfault"].entries[0].message
        == "Process[123]: segmentation fault at 0"
    )

    # Check out of memory
    assert "oom" in analysis_map
    assert analysis_map["oom"].count == 1
    assert analysis_map["oom"].entries[0].message == "System is running out of memory."


def test_case_insensitivity():
    """Test that pattern matching is case-insensitive."""
    entries = [
        LogEntry(
            timestamp=TIMESTAMP,
            source="syslog",
            level="error",
            facility="kernel",
            message="HARDWARE ERROR detected.",
        ),
        LogEntry(
            timestamp=TIMESTAMP,
            source="journald",
            level="emerg",
            facility="kernel",
            message="kernel panic happened.",
        ),
    ]
    analyses = detect_patterns(entries)
    expected_case_insensitive_count = 2
    assert len(analyses) == expected_case_insensitive_count

    analysis_map = {a.issue_type: a for a in analyses}
    assert "hardware" in analysis_map
    assert analysis_map["hardware"].count == 1
    assert "kernel" in analysis_map
    assert analysis_map["kernel"].count == 1
