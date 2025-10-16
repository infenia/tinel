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

import unittest
from datetime import datetime, timedelta

from tinel.logs.log_analyzer import analyze_logs, detailed_analysis
from tinel.logs.models import LogEntry


class TestLogAnalyzer(unittest.TestCase):
    def test_analyze_logs_empty_input(self):
        """Test that analyze_logs handles empty lists gracefully."""
        self.assertEqual(analyze_logs([]), [])

    def test_correlation(self):
        """Test correlation of a kernel panic with a hardware error."""
        entries = [
            LogEntry(
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                source="test",
                message="Critical hardware error on device xyz",
                level="error",
                facility="kern",
            ),
            LogEntry(
                timestamp=datetime(2024, 1, 1, 12, 5, 0),
                source="test",
                message="Kernel panic - not syncing: Fatal exception",
                level="emerg",
                facility="kern",
            ),
        ]
        analyses = analyze_logs(entries)
        kernel_analysis = next(
            (a for a in analyses if a.issue_type == "kernel"), None
        )
        self.assertIsNotNone(kernel_analysis)
        self.assertEqual(len(kernel_analysis.correlated_events), 1)
        self.assertIn(
            "Correlated with hardware event at 2024-01-01T12:00:00",
            kernel_analysis.correlated_events[0],
        )

    def test_no_correlation_outside_window(self):
        """Test that events outside the time window are not correlated."""
        entries = [
            LogEntry(
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                source="test",
                message="Critical hardware error on device xyz",
                level="error",
                facility="kern",
            ),
            LogEntry(
                timestamp=datetime(2024, 1, 1, 12, 15, 0),
                source="test",
                message="Kernel panic - not syncing",
                level="emerg",
                facility="kern",
            ),
        ]
        analyses = analyze_logs(entries)
        kernel_analysis = next(
            (a for a in analyses if a.issue_type == "kernel"), None
        )
        self.assertIsNotNone(kernel_analysis)
        self.assertEqual(len(kernel_analysis.correlated_events), 0)

    def test_summary_generation(self):
        """Test the generation of enhanced summaries."""
        entries = [
            LogEntry(
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                source="test",
                message="Segmentation fault at 0x0",
                level="error",
                facility="system",
            ),
            LogEntry(
                timestamp=datetime(2024, 1, 1, 11, 0, 0),
                source="test",
                message="Another segmentation fault",
                level="error",
                facility="system",
            ),
        ]
        analyses = analyze_logs(entries)
        segfault_analysis = next(
            (a for a in analyses if a.issue_type == "segfault"), None
        )
        self.assertIsNotNone(segfault_analysis)
        self.assertEqual(segfault_analysis.count, 2)
        expected_summary = (
            "2 segfault issue(s) detected between "
            "2024-01-01T10:00:00 and 2024-01-01T11:00:00."
        )
        self.assertEqual(segfault_analysis.summary, expected_summary)

    def test_detailed_analysis_single_cause(self):
        """Test detailed analysis for an entry with a single potential cause."""
        entry = LogEntry(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            source="syslog",
            message="systemd[1]: Out of memory: Killed process 1234 (test)",
            level="error",
            facility="kern",
            host="testhost",
            process="systemd",
        )
        analysis_str = detailed_analysis(entry)
        self.assertIn("Timestamp: 2024-01-01T12:00:00", analysis_str)
        self.assertIn("Potential Cause(s): oom", analysis_str)

    def test_detailed_analysis_multiple_causes(self):
        """Test detailed analysis for an entry with multiple potential causes."""
        entry = LogEntry(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            source="syslog",
            message="Kernel panic due to hardware error!",
            level="emerg",
            facility="kern",
            host="testhost",
            process="kernel",
        )
        analysis_str = detailed_analysis(entry)
        # The order of causes is not guaranteed, so check for both
        self.assertIn("Potential Cause(s):", analysis_str)
        self.assertIn("hardware", analysis_str)
        self.assertIn("kernel", analysis_str)


if __name__ == "__main__":
    unittest.main()