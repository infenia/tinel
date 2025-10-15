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

"""Log parsing functionality for syslog and journald."""

import json
import logging
import re
import subprocess
from datetime import datetime
from typing import Any, List, Optional

from tinel.logs.models import LogEntry

LOG = logging.getLogger(__name__)

# Regex for standard syslog format (e.g., "Oct 16 10:00:00 host kernel: message")
# It captures: timestamp, host, process, optional PID, and message.
SYSLOG_REGEX = re.compile(
    r"^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+"
    r"(?P<message>.*)$"
)

def _infer_log_level(message: str) -> str:
    """Infers the log level from the message content."""
    message_lower = message.lower()
    if "error" in message_lower or "failed" in message_lower:
        return "ERROR"
    if "warning" in message_lower or "warn" in message_lower:
        return "WARNING"
    if "notice" in message_lower:
        return "NOTICE"
    if "info" in message_lower:
        return "INFO"
    return "UNKNOWN"

def parse_syslog(file_path: str) -> List[LogEntry]:
    """
    Parses a syslog file line by line.

    Args:
        file_path: The path to the syslog file.

    Returns:
        A list of parsed LogEntry objects.
    """
    entries = []
    current_year = datetime.now().year
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                match = SYSLOG_REGEX.match(line.strip())
                if not match:
                    LOG.warning("Skipping malformed syslog line %d: %s", i + 1, line.strip())
                    continue

                data = match.groupdict()
                try:
                    # Syslog timestamps don't have a year, so we assume the current one.
                    # This could be inaccurate for logs spanning new year's eve.
                    timestamp_str = f"{data['timestamp']} {current_year}"
                    timestamp = datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")
                except (ValueError, TypeError):
                    LOG.warning("Could not parse timestamp on line %d: %s", i + 1, line.strip())
                    continue

                entries.append(
                    LogEntry(
                        timestamp=timestamp,
                        source="syslog",
                        message=data["message"].strip(),
                        level=_infer_log_level(data["message"]),
                        facility=data["process"],
                        host=data["host"],
                        process=f"{data['process']}" + (f"[{data['pid']}]" if data.get("pid") else ""),
                    )
                )
    except FileNotFoundError:
        LOG.error("Log file not found: %s", file_path)
    except Exception as e:
        LOG.error("An unexpected error occurred while parsing syslog: %s", e)

    return entries


# Mapping from journald priority to a standard log level string.
# See https://en.wikipedia.org/wiki/Syslog#Severity_level
JOURNALD_PRIORITY_MAP = {
    "0": "EMERG",
    "1": "ALERT",
    "2": "CRIT",
    "3": "ERR",
    "4": "WARNING",
    "5": "NOTICE",
    "6": "INFO",
    "7": "DEBUG",
}


def parse_journald() -> List[LogEntry]:
    """
    Fetches and parses journald logs.

    Returns:
        A list of parsed LogEntry objects.
    """
    entries = []
    try:
        # Execute journalctl to get logs in JSON format
        result = subprocess.run(
            ["journalctl", "-o", "json"],
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit code
            encoding="utf-8",
        )

        if result.returncode != 0:
            LOG.error(
                "journalctl command failed with exit code %d: %s",
                result.returncode,
                result.stderr,
            )
            return entries

        # Each line of the output is a separate JSON object
        for i, line in enumerate(result.stdout.strip().split("\n")):
            if not line:
                continue
            try:
                log = json.loads(line)

                # Convert timestamp from microseconds to a datetime object
                ts_usec = int(log.get("__REALTIME_TIMESTAMP", 0))
                timestamp = datetime.fromtimestamp(ts_usec / 1_000_000)

                # Map journald fields to LogEntry fields
                entries.append(
                    LogEntry(
                        timestamp=timestamp,
                        source="journald",
                        message=log.get("MESSAGE", ""),
                        level=JOURNALD_PRIORITY_MAP.get(log.get("PRIORITY"), "UNKNOWN"),
                        facility=log.get("SYSLOG_IDENTIFIER", "unknown"),
                        host=log.get("_HOSTNAME", "unknown"),
                        process=log.get("_COMM", "unknown"),
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                LOG.warning(
                    "Skipping malformed journald JSON on line %d: %s (error: %s)",
                    i + 1,
                    line,
                    e,
                )
                continue

    except FileNotFoundError:
        LOG.error("journalctl command not found. Is systemd installed and in PATH?")
    except Exception as e:
        LOG.error("An unexpected error occurred while parsing journald logs: %s", e)

    return entries


def parse_logs(file_path: Optional[str], log_format: str) -> List[LogEntry]:
    """
    Dispatches to the correct log parser based on the specified format.

    Args:
        file_path: The path to the log file (used by syslog).
        log_format: The format of the logs ("syslog" or "journald").

    Returns:
        A list of parsed LogEntry objects.
    """
    if log_format == "syslog":
        if not file_path:
            LOG.error("File path is required for syslog format.")
            return []
        return parse_syslog(file_path)
    elif log_format == "journald":
        return parse_journald()
    else:
        LOG.error("Unsupported log format: %s", log_format)
        return []