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

"""Unit tests for the streaming log parser."""

import io
import logging
from datetime import datetime
from unittest.mock import patch

from tinel.logs.models import LogEntry
from tinel.logs.streaming_parser import parse_logs_stream


def test_parse_logs_stream_syslog_valid():
    """Tests that the stream parser correctly parses valid syslog lines."""
    log_data = (
        "Oct 15 14:35:10 my-host kernel[12345]: a kernel error message\n"
        "Oct 15 14:35:11 my-host sshd: a warning message"
    )
    mock_file = io.StringIO(log_data)
    current_year = datetime.now().year

    with patch("builtins.open", return_value=mock_file):
        log_generator = parse_logs_stream("dummy/path.log")
        entries = list(log_generator)

    assert len(entries) == 2
    # First entry
    assert isinstance(entries[0], LogEntry)
    assert entries[0].timestamp == datetime(current_year, 10, 15, 14, 35, 10)
    assert entries[0].source == "syslog_stream"
    assert entries[0].host == "my-host"
    assert entries[0].process == "kernel[12345]"
    assert entries[0].facility == "kernel"
    assert entries[0].level == "ERROR"
    assert entries[0].message == "a kernel error message"
    # Second entry
    assert isinstance(entries[1], LogEntry)
    assert entries[1].timestamp == datetime(current_year, 10, 15, 14, 35, 11)
    assert entries[1].host == "my-host"
    assert entries[1].process == "sshd"
    assert entries[1].facility == "sshd"
    assert entries[1].level == "WARNING"
    assert entries[1].message == "a warning message"


def test_parse_logs_stream_malformed_lines():
    """Tests that the stream parser skips malformed lines."""
    log_data = (
        "this is not a valid syslog line\n"
        "Oct 15 14:35:10 my-host kernel: a valid line\n"
        "another invalid line"
    )
    mock_file = io.StringIO(log_data)

    with patch("builtins.open", return_value=mock_file):
        entries = list(parse_logs_stream("dummy/path.log"))

    assert len(entries) == 1
    assert entries[0].message == "a valid line"


def test_parse_logs_stream_file_not_found(caplog):
    """Tests graceful handling of FileNotFoundError."""
    with caplog.at_level(logging.ERROR):
        entries = list(parse_logs_stream("non_existent_file.log"))

    assert len(entries) == 0
    assert "Log file not found: non_existent_file.log" in caplog.text


def test_parse_logs_stream_unsupported_format(caplog):
    """Tests that an unsupported log format is handled correctly."""
    with caplog.at_level(logging.ERROR):
        entries = list(parse_logs_stream("dummy.log", log_format="not_syslog"))

    assert len(entries) == 0
    assert "Unsupported log format for streaming: not_syslog" in caplog.text


def test_parse_logs_stream_large_file_performance():
    """
    Indirectly tests memory efficiency by streaming a large number of log
    entries and ensuring it completes without excessive resource usage.
    """
    num_lines = 100_000  # Simulate a large file
    line = "Oct 15 14:35:10 h kernel: message\n"
    large_log_data = io.StringIO(line * num_lines)

    with patch("builtins.open", return_value=large_log_data):
        # The test is that this can be iterated over without memory errors
        # and that the count is correct.
        count = sum(1 for _ in parse_logs_stream("large_dummy.log"))

    assert count == num_lines