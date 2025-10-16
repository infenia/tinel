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
        "Oct 15 14:35:11 my-host sshd: a warning message\n"
        "Oct 15 14:35:12 my-host cron[111]: job failed\n"
        "Oct 15 14:35:13 my-host app: this is a warn message\n"
        "Oct 15 14:35:14 my-host app: this is a notice\n"
        "Oct 15 14:35:15 my-host app: this is some info"
    )
    mock_file = io.StringIO(log_data)

    with patch("builtins.open", return_value=mock_file):
        log_generator = parse_logs_stream("dummy/path.log")
        entries = list(log_generator)

    assert len(entries) == 6
    assert entries[0].level == "ERROR"
    assert entries[1].level == "WARNING"
    assert entries[2].level == "ERROR"
    assert entries[3].level == "WARNING"
    assert entries[4].level == "NOTICE"
    assert entries[5].level == "INFO"


def test_parse_logs_stream_malformed_lines(caplog):
    """Tests that the stream parser skips malformed lines and logs them."""
    log_data = (
        "this is not a valid syslog line\n"
        "Oct 15 14:35:10 my-host kernel: a valid line\n"
        "another invalid line"
    )
    mock_file = io.StringIO(log_data)

    with patch("builtins.open", return_value=mock_file), caplog.at_level(logging.DEBUG):
        entries = list(parse_logs_stream("dummy/path.log"))

    assert len(entries) == 1
    assert entries[0].message == "a valid line"
    assert "Skipping malformed syslog line 1" in caplog.text
    assert "Skipping malformed syslog line 3" in caplog.text


def test_parse_logs_stream_invalid_timestamp(caplog):
    """Tests that a line with an invalid timestamp is skipped."""
    # Feb 30 is not a valid date
    log_data = "Feb 30 10:00:00 my-host kernel: message"
    mock_file = io.StringIO(log_data)

    with patch("builtins.open", return_value=mock_file), caplog.at_level(logging.WARNING):
        entries = list(parse_logs_stream("dummy/path.log"))

    assert len(entries) == 0
    assert "Could not parse timestamp on line 1" in caplog.text


def test_parse_logs_stream_io_error(caplog):
    """Tests graceful handling of an IOError while reading the file."""

    class MockFailingFile:
        """A mock file-like object that raises IOError during iteration."""

        def __init__(self):
            self.lines_read = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self.lines_read == 0:
                self.lines_read += 1
                return "Oct 15 14:35:10 my-host kernel: a valid line\n"
            # After the first line, simulate a read error
            raise IOError("Disk read error")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            # No special exception handling
            pass

    mock_file_instance = MockFailingFile()

    with patch("builtins.open", return_value=mock_file_instance):
        with caplog.at_level(logging.ERROR):
            # Consume the generator to trigger the iteration and the error
            entries = list(parse_logs_stream("dummy/path.log"))

    # The generator should yield one entry before the error is raised
    assert len(entries) == 1
    # The error should be caught and logged
    assert "Error reading log file dummy/path.log: Disk read error" in caplog.text


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