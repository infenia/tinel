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

"""Unit tests for the log analysis data models."""

from datetime import datetime

import pytest
from tinel.logs.models import LogAnalysis, LogEntry


@pytest.mark.unit
def test_log_entry_instantiation():
    """Test that a LogEntry can be instantiated with valid data."""
    now = datetime.now()
    entry = LogEntry(
        timestamp=now,
        source="syslog",
        message="Test message",
        level="ERROR",
        facility="kernel",
        host="localhost",
        process="test_process",
    )
    assert entry.timestamp == now
    assert entry.source == "syslog"
    assert entry.message == "Test message"
    assert entry.level == "ERROR"
    assert entry.facility == "kernel"
    assert entry.host == "localhost"
    assert entry.process == "test_process"


@pytest.mark.unit
def test_log_entry_repr():
    """Test the __repr__ method of the LogEntry model."""
    now = datetime.now()
    entry = LogEntry(
        timestamp=now,
        source="syslog",
        level="INFO",
        message="This is a test log message that is longer than 50 characters to test truncation.",
        facility="auth",
    )
    expected_repr = (
        f"LogEntry(timestamp={now}, source='syslog', level='INFO', "
        f"message='This is a test log message that is longer than 50 ...')"
    )
    assert repr(entry) == expected_repr


@pytest.mark.unit
def test_log_analysis_instantiation():
    """Test that a LogAnalysis object can be instantiated."""
    analysis = LogAnalysis(
        issue_type="hardware",
        summary="Test hardware issue",
    )
    assert analysis.issue_type == "hardware"
    assert analysis.summary == "Test hardware issue"
    assert analysis.count == 0
    assert analysis.entries == []
    assert analysis.correlated_events == []


@pytest.mark.unit
def test_log_analysis_add_entry():
    """Test the add_entry method of the LogAnalysis model."""
    analysis = LogAnalysis(
        issue_type="kernel",
        summary="Kernel panic detected",
    )
    entry1 = LogEntry(
        timestamp=datetime.now(),
        source="journald",
        message="Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block(0,0)",
        level="CRITICAL",
        facility="kernel",
    )
    entry2 = LogEntry(
        timestamp=datetime.now(),
        source="journald",
        message="CPU: 1 PID: 1 Comm: swapper/0 Not tainted 5.15.0-101-generic #111-Ubuntu",
        level="INFO",
        facility="kernel",
    )

    analysis.add_entry(entry1)
    assert analysis.count == 1
    assert len(analysis.entries) == 1
    assert analysis.entries[0] == entry1

    analysis.add_entry(entry2)
    assert analysis.count == 2
    assert len(analysis.entries) == 2
    assert analysis.entries[1] == entry2


@pytest.mark.unit
def test_log_analysis_repr():
    """Test the __repr__ method of the LogAnalysis model."""
    analysis = LogAnalysis(
        issue_type="security",
        summary="Multiple failed login attempts",
    )
    entry = LogEntry(
        timestamp=datetime.now(),
        source="auth.log",
        message="Failed password for invalid user admin",
        level="WARNING",
        facility="auth",
    )
    analysis.add_entry(entry)

    expected_repr = "LogAnalysis(issue_type='security', count=1, summary='Multiple failed login attempts')"
    assert repr(analysis) == expected_repr