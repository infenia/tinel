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

"""Data models for the Log Analysis Module."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """
    Represents a single log entry.

    Attributes:
        timestamp: The timestamp of the log entry.
        source: The source of the log (e.g., "syslog", "journald").
        message: The raw log message.
        level: The log level (e.g., "ERROR", "WARNING").
        facility: The syslog facility (e.g., "kernel").
        host: The hostname where the log was generated.
        process: The process that generated the log.
    """

    timestamp: datetime
    source: str
    message: str
    level: str
    facility: str
    host: Optional[str] = None
    process: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"LogEntry(timestamp={self.timestamp}, source='{self.source}', "
            f"level='{self.level}', message='{self.message[:50]}...')"
        )


class LogAnalysis(BaseModel):
    """
    Represents an analysis of a set of log entries.

    Attributes:
        issue_type: The type of issue detected (e.g., "hardware", "kernel").
        count: The number of occurrences of the issue.
        entries: A list of log entries related to the issue.
        summary: An aggregated description of the issue.
        correlated_events: A list of timestamps or IDs of correlated hardware events.
    """

    issue_type: str
    summary: str
    count: int = 0
    entries: List[LogEntry] = Field(default_factory=list)
    correlated_events: List[str] = Field(default_factory=list)

    def add_entry(self, entry: LogEntry) -> None:
        """
        Adds a log entry to the analysis.

        Args:
            entry: The LogEntry to add.
        """
        self.entries.append(entry)
        self.count = len(self.entries)

    def __repr__(self) -> str:
        return (
            f"LogAnalysis(issue_type='{self.issue_type}', count={self.count}, "
            f"summary='{self.summary}')"
        )
