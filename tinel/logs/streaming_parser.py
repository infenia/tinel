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

"""Streaming log parsing functionality for handling large files."""

import logging
import re
from datetime import datetime
from typing import Generator

from .models import LogEntry

LOG = logging.getLogger(__name__)

# Regex for standard syslog format (e.g., "Oct 16 10:00:00 host kernel: message")
# It captures: timestamp, host, process, optional PID, and message.
# This is intentionally duplicated from log_parser.py to keep streaming independent.
SYSLOG_REGEX = re.compile(
    r"^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?:\s+"
    r"(?P<message>.*)$"
)


def _infer_log_level(message: str) -> str:
    """
    Infers the log level from the message content.
    This is intentionally duplicated from log_parser.py to keep streaming independent.
    """
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


def parse_logs_stream(
    file_path: str, log_format: str = "syslog"
) -> Generator[LogEntry, None, None]:
    """
    Parses a log file line-by-line without loading the entire file into memory.

    This function is designed for handling very large log files efficiently.
    It yields LogEntry objects as they are parsed.

    Args:
        file_path: The path to the log file.
        log_format: The format of the logs (currently only "syslog" is supported).

    Yields:
        LogEntry objects for each successfully parsed line.
    """
    if log_format != "syslog":
        LOG.error("Unsupported log format for streaming: %s", log_format)
        return

    current_year = datetime.now().year
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                match = SYSLOG_REGEX.match(line.strip())
                if not match:
                    LOG.debug(
                        "Skipping malformed syslog line %d: %s", i + 1, line.strip()
                    )
                    continue

                data = match.groupdict()
                try:
                    # Syslog timestamps don't have a year, so we assume the current one.
                    timestamp_str = f"{data['timestamp']} {current_year}"
                    timestamp = datetime.strptime(timestamp_str, "%b %d %H:%M:%S %Y")
                except (ValueError, TypeError):
                    LOG.warning(
                        "Could not parse timestamp on line %d: %s", i + 1, line.strip()
                    )
                    continue

                yield LogEntry(
                    timestamp=timestamp,
                    source="syslog_stream",
                    message=data["message"].strip(),
                    level=_infer_log_level(data["message"]),
                    facility=data["process"],
                    host=data["host"],
                    process=f"{data['process']}"
                    + (f"[{data['pid']}]" if data.get("pid") else ""),
                )
    except FileNotFoundError:
        LOG.error("Log file not found: %s", file_path)
    except IOError as e:
        LOG.error("Error reading log file %s: %s", file_path, e)
