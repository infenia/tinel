import unittest
from datetime import datetime
from unittest.mock import patch

from tinel.logs.log_analyzer import (
    analyze_logs,
    correlate_with_hardware,
    detailed_analysis,
)
from tinel.logs.models import LogAnalysis, LogEntry


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
        kernel_analysis = next((a for a in analyses if a.issue_type == "kernel"), None)
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
        kernel_analysis = next((a for a in analyses if a.issue_type == "kernel"), None)
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
        self.assertIn("Level: error", analysis_str)
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
        self.assertIn("Timestamp: 2024-01-01T12:00:00", analysis_str)
        self.assertIn("Level: emerg", analysis_str)
        self.assertIn("Potential Cause(s):", analysis_str)
        self.assertIn("hardware", analysis_str)
        self.assertIn("kernel", analysis_str)

    def test_analyze_logs_no_patterns_detected(self):
        """Test analyze_logs when no patterns are detected in the entries."""
        entries = [
            LogEntry(
                timestamp=datetime(2023, 1, 1, 12, 0, 0),
                source="test",
                message="this is a completely normal log message",
                level="info",
                facility="test",
            )
        ]
        result = analyze_logs(entries)
        self.assertEqual(result, [])

    @patch("tinel.logs.log_analyzer.detect_patterns")
    def test_branch_coverage_with_mocking(self, mock_detect_patterns):
        """
        Test branch coverage for correlate_with_hardware and summary generation
        using mocked data.
        """
        mock_detect_patterns.return_value = [
            LogAnalysis(
                issue_type="hardware",
                summary="initial hw",
                count=1,
                entries=[
                    LogEntry(
                        timestamp=datetime(2024, 1, 1, 12, 0, 0),
                        source="s",
                        message="hw error",
                        level="s",
                        facility="s",
                    )
                ],
            ),
            LogAnalysis(
                issue_type="kernel",
                summary="initial kernel",
                count=1,
                entries=[
                    LogEntry(
                        timestamp=datetime(2024, 1, 1, 12, 5, 0),
                        source="s",
                        message="kernel error",
                        level="s",
                        facility="s",
                    )
                ],
            ),
        ]
        dummy_entries = [
            LogEntry(
                timestamp=datetime.now(),
                source="s",
                message="s",
                level="s",
                facility="s",
            )
        ]
        analyses = analyze_logs(dummy_entries)
        self.assertEqual(len(analyses), 2)
        hardware_analysis = next(a for a in analyses if a.issue_type == "hardware")
        kernel_analysis = next(a for a in analyses if a.issue_type == "kernel")
        self.assertNotEqual(hardware_analysis.summary, "initial hw")
        self.assertNotEqual(kernel_analysis.summary, "initial kernel")
        self.assertEqual(len(kernel_analysis.correlated_events), 1)

    def test_correlate_with_hardware_no_hardware_analysis(self):
        """Test correlation when no hardware analysis object exists."""
        analyses = {
            "kernel": LogAnalysis(
                issue_type="kernel",
                summary="s",
                count=1,
                entries=[
                    LogEntry(
                        timestamp=datetime.now(),
                        source="s",
                        message="s",
                        level="s",
                        facility="s",
                    )
                ],
            )
        }
        correlate_with_hardware(analyses)
        self.assertEqual(len(analyses["kernel"].correlated_events), 0)

    def test_correlate_with_hardware_only_hardware_events(self):
        """Test correlation with only hardware events present."""
        analyses = {
            "hardware": LogAnalysis(
                issue_type="hardware",
                summary="s",
                count=1,
                entries=[
                    LogEntry(
                        timestamp=datetime.now(),
                        source="s",
                        message="s",
                        level="s",
                        facility="s",
                    )
                ],
            )
        }
        correlate_with_hardware(analyses)
        self.assertEqual(len(analyses["hardware"].correlated_events), 0)

    @patch("tinel.logs.log_analyzer.detect_patterns")
    def test_analyze_logs_with_zero_count_analysis(self, mock_detect_patterns):
        """Test that summary is not generated for analysis with zero count."""
        mock_detect_patterns.return_value = [
            LogAnalysis(issue_type="test", summary="initial", count=0, entries=[])
        ]
        dummy_entries = [
            LogEntry(
                timestamp=datetime.now(),
                source="s",
                message="s",
                level="s",
                facility="s",
            )
        ]
        analyses = analyze_logs(dummy_entries)
        self.assertEqual(len(analyses), 1)
        self.assertEqual(analyses[0].summary, "initial")

    def test_correlation_already_exists(self):
        """Test that a correlation is not added twice."""
        entries = [
            LogEntry(
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                source="test",
                message="Critical hardware error",
                level="error",
                facility="kern",
            ),
            LogEntry(
                timestamp=datetime(2024, 1, 1, 12, 1, 0),
                source="test",
                message="Kernel panic",
                level="emerg",
                facility="kern",
            ),
            LogEntry(
                timestamp=datetime(2024, 1, 1, 12, 2, 0),
                source="test",
                message="Another Kernel panic",
                level="emerg",
                facility="kern",
            ),
        ]
        analyses = analyze_logs(entries)
        kernel_analysis = next((a for a in analyses if a.issue_type == "kernel"), None)
        self.assertIsNotNone(kernel_analysis)
        self.assertEqual(len(kernel_analysis.correlated_events), 1)
        self.assertEqual(kernel_analysis.count, 2)


if __name__ == "__main__":
    unittest.main()
