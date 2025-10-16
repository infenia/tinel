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

import io
import json
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

from tinel.logs.log_parser import (
    _infer_log_level,
    parse_journald,
    parse_logs,
    parse_syslog,
)

# Sample syslog content with various formats
MOCK_SYSLOG_CONTENT = """
Oct 16 10:00:00 my-host kernel: [12345.67890] hardware error - high temperature
Oct 16 10:01:00 my-host systemd[1]: Starting service...
Oct 16 10:02:00 my-host CRON[12348]: (root) CMD (command)
This is a malformed line.
Oct 16 10:03:00 my-host sshd[12349]: Failed password for invalid user from 10.0.0.1
Oct 16 10:04:00 my-host kernel: a warning message
"""

# Sample journald content (as a list of JSON strings)
MOCK_JOURNALD_JSON = [
    {
        "__REALTIME_TIMESTAMP": "1665932400000000",
        "_HOSTNAME": "my-host",
        "SYSLOG_IDENTIFIER": "kernel",
        "MESSAGE": "hardware error - high temperature",
        "PRIORITY": "3",
        "_COMM": "kernel",
    },
    {
        "__REALTIME_TIMESTAMP": "1665932460000000",
        "_HOSTNAME": "my-host",
        "SYSLOG_IDENTIFIER": "systemd",
        "MESSAGE": "Starting service...",
        "PRIORITY": "6",
        "_COMM": "systemd",
    },
]


def test_parse_syslog_valid_and_malformed(tmp_path):
    """Tests syslog parsing with a mix of valid and malformed lines."""
    log_file = tmp_path / "syslog"
    log_file.write_text(MOCK_SYSLOG_CONTENT)

    expected_syslog_entries = 5
    entries = parse_syslog(str(log_file))
    assert len(entries) == expected_syslog_entries
    assert entries[0].message == "[12345.67890] hardware error - high temperature"
    assert entries[0].level == "ERROR"
    assert entries[0].facility == "kernel"
    assert entries[0].host == "my-host"
    assert entries[1].process == "systemd[1]"
    assert entries[2].level == "UNKNOWN"  # No keyword
    assert entries[3].level == "ERROR"  # "Failed" keyword
    assert entries[4].level == "WARNING"  # "warning" keyword


def test_parse_syslog_file_not_found():
    """Tests that parse_syslog handles a non-existent file gracefully."""
    entries = parse_syslog("non_existent_file.log")
    assert len(entries) == 0


@patch("subprocess.run")
def test_parse_journald_valid(mock_run):
    """Tests journald parsing with valid JSON output."""
    mock_stdout = "\n".join(json.dumps(entry) for entry in MOCK_JOURNALD_JSON)
    mock_run.return_value = MagicMock(stdout=mock_stdout, stderr="", returncode=0)

    expected_journald_entries = 2
    entries = parse_journald()
    assert len(entries) == expected_journald_entries
    assert entries[0].message == "hardware error - high temperature"
    assert entries[0].level == "ERR"
    assert entries[0].facility == "kernel"
    assert entries[0].host == "my-host"
    assert entries[0].process == "kernel"
    ts = datetime.fromtimestamp(1665932400000000 / 1_000_000)
    assert entries[0].timestamp == ts


@patch("subprocess.run")
def test_parse_journald_command_fails(mock_run):
    """Tests that journald parsing handles a command failure."""
    mock_run.return_value = MagicMock(
        stdout="", stderr="command not found", returncode=127
    )
    entries = parse_journald()
    assert len(entries) == 0


@patch("subprocess.run")
def test_parse_journald_malformed_json(mock_run):
    """Tests that journald parsing handles malformed JSON."""
    mock_stdout = '{"__REALTIME_TIMESTAMP": "123"}\nthis is not json'
    mock_run.return_value = MagicMock(stdout=mock_stdout, stderr="", returncode=0)
    entries = parse_journald()
    assert len(entries) == 1  # Should parse the first valid line and skip the second


def test_parse_logs_dispatcher(tmp_path):
    """Tests the main dispatcher function."""
    log_file = tmp_path / "syslog"
    log_file.write_text("Oct 16 10:00:00 h k: m")

    # Test syslog dispatch
    entries = parse_logs(str(log_file), "syslog")
    assert len(entries) == 1
    assert entries[0].source == "syslog"

    # Test journald dispatch (mocking subprocess)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        entries = parse_logs(None, "journald")
        assert len(entries) == 0
        assert mock_run.called

    # Test invalid format
    entries = parse_logs(None, "invalid_format")
    assert len(entries) == 0


def test_syslog_parsing_performance():
    """Tests the performance of parsing a large number of syslog lines."""
    num_lines = 1000
    content = (MOCK_SYSLOG_CONTENT.strip() + "\n") * (num_lines // 5)
    log_file = io.StringIO(content)

    # Create a temporary file-like object in memory
    with patch("builtins.open", return_value=log_file):
        start_time = time.time()
        parse_syslog("dummy_path")
        end_time = time.time()

    duration = end_time - start_time
    print(f"Parsed {num_lines} syslog lines in {duration:.4f} seconds.")
    assert duration < 1.0


def test_parse_syslog_timestamp_value_error(tmp_path, caplog):
    """Tests that a ValueError during timestamp parsing is handled."""
    log_file = tmp_path / "syslog"
    # This timestamp is invalid because it's not a real date
    log_file.write_text("Feb 30 10:00:00 h k: m")

    entries = parse_syslog(str(log_file))
    assert len(entries) == 0
    assert "Could not parse timestamp" in caplog.text


@patch("subprocess.run", side_effect=FileNotFoundError("journalctl not found"))
def test_parse_journald_command_not_found(mock_run, caplog):
    """Tests that a FileNotFoundError for journalctl is handled."""
    entries = parse_journald()
    assert len(entries) == 0
    assert "journalctl command not found" in caplog.text


def test_parse_logs_syslog_no_path(caplog):
    """Tests calling parse_logs for syslog with no file_path."""
    entries = parse_logs(None, "syslog")
    assert len(entries) == 0
    assert "File path is required for syslog format" in caplog.text


def test_infer_log_level_coverage():
    """Ensures all branches of _infer_log_level are covered."""

    assert _infer_log_level("this is a notice") == "NOTICE"
    assert _infer_log_level("this is some info") == "INFO"


@patch("builtins.open", side_effect=Exception("Unexpected error"))
def test_parse_syslog_generic_exception(mock_open, caplog):
    """Tests handling of a generic exception during file processing."""
    entries = parse_syslog("any/path")
    assert len(entries) == 0
    assert "An unexpected error occurred" in caplog.text


@patch("subprocess.run")
@patch("json.loads", side_effect=Exception("Unexpected JSON error"))
def test_parse_journald_generic_exception(mock_loads, mock_run, caplog):
    """Tests handling of a generic exception during journald log processing."""
    mock_run.return_value = MagicMock(
        stdout='{"__REALTIME_TIMESTAMP": "123"}', stderr="", returncode=0
    )
    entries = parse_journald()
    assert len(entries) == 0
    assert "An unexpected error occurred while parsing journald logs" in caplog.text
