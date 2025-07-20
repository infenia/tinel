#!/usr/bin/env python3
"""Log Analysis Tools for MCP Server.

This module provides MCP tools for log analysis including system log parsing,
pattern detection, and log summary generation.

Copyright 2025 Infenia Private Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseToolProvider
from ..interfaces import SystemInterface
from ..logs import LogAnalyzer, LogParser, PatternDetector
from ..system import LinuxSystemInterface


class SystemLogsToolProvider(BaseToolProvider):
    """Tool provider for system log retrieval and parsing."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize system logs tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "get_system_logs",
            "Retrieve and parse system logs from various sources including journald, syslog, kernel logs, and application logs"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.parser = LogParser(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of log sources to parse (e.g., 'journald', 'syslog', 'kern.log', 'dmesg', '/var/log/auth.log')",
                    "default": ["journald", "syslog", "kern.log"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of log entries to return",
                    "default": 1000,
                    "minimum": 1,
                    "maximum": 10000
                },
                "since": {
                    "type": "string",
                    "description": "Time period to retrieve logs from (e.g., '24 hours ago', '1 day ago', '2023-12-01')",
                    "default": "24 hours ago"
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system logs retrieval.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing parsed log entries
        """
        try:
            sources = parameters.get("sources", ["journald", "syslog", "kern.log"])
            limit = parameters.get("limit", 1000)
            since = parameters.get("since", "24 hours ago")
            
            # Parse logs from sources
            entries = self.parser.parse_logs(sources)
            
            # Filter by time if specified
            if since and since != "all":
                cutoff_time = self._parse_time_filter(since)
                if cutoff_time:
                    entries = [entry for entry in entries if entry.timestamp >= cutoff_time]
            
            # Limit results
            if limit and len(entries) > limit:
                entries = entries[-limit:]  # Get most recent entries
            
            # Convert entries to serializable format
            log_data = []
            for entry in entries:
                log_data.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "facility": entry.facility,
                    "severity": entry.severity,
                    "message": entry.message,
                    "source": entry.source
                })
            
            return {
                "success": True,
                "total_entries": len(log_data),
                "sources_parsed": sources,
                "time_filter": since,
                "entries": log_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve system logs: {str(e)}",
                "entries": []
            }
    
    def _parse_time_filter(self, time_str: str) -> Optional[datetime]:
        """Parse time filter string into datetime object.
        
        Args:
            time_str: Time filter string
            
        Returns:
            Datetime object or None if parsing fails
        """
        try:
            now = datetime.now()
            
            if "hour" in time_str:
                hours = int(time_str.split()[0])
                return now - timedelta(hours=hours)
            elif "day" in time_str:
                days = int(time_str.split()[0])
                return now - timedelta(days=days)
            elif "week" in time_str:
                weeks = int(time_str.split()[0])
                return now - timedelta(weeks=weeks)
            else:
                # Try to parse as date
                return datetime.fromisoformat(time_str)
        except (ValueError, IndexError):
            return None


class LogAnalysisToolProvider(BaseToolProvider):
    """Tool provider for comprehensive log analysis."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize log analysis tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "analyze_logs",
            "Perform comprehensive analysis of system logs including pattern detection, issue identification, and correlation analysis"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.analyzer = LogAnalyzer(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of log sources to analyze",
                    "default": ["journald", "syslog", "kern.log", "dmesg"]
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["full", "hardware", "kernel", "security", "performance"],
                    "description": "Type of analysis to perform",
                    "default": "full"
                },
                "time_window": {
                    "type": "integer",
                    "description": "Time window in seconds for event correlation",
                    "default": 300,
                    "minimum": 60,
                    "maximum": 3600
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute log analysis.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            sources = parameters.get("sources", ["journald", "syslog", "kern.log", "dmesg"])
            analysis_type = parameters.get("analysis_type", "full")
            time_window = parameters.get("time_window", 300)
            
            # Perform log analysis
            analysis = self.analyzer.analyze_logs(sources)
            
            # Filter results based on analysis type
            if analysis_type == "hardware":
                filtered_patterns = {"hardware": analysis.patterns.get("hardware", {})}
            elif analysis_type == "kernel":
                filtered_patterns = {"kernel": analysis.patterns.get("kernel", {})}
            else:
                filtered_patterns = analysis.patterns
            
            # Convert analysis to serializable format
            result = {
                "success": True,
                "analysis_type": analysis_type,
                "sources_analyzed": sources,
                "total_entries": len(analysis.entries),
                "patterns": self._serialize_patterns(filtered_patterns),
                "issues": self._serialize_issues(analysis.issues),
                "summary": analysis.summary
            }
            
            # Add correlation analysis if requested
            if analysis_type == "full":
                correlations = self.analyzer.correlate_hardware_events(analysis.entries, time_window)
                result["correlations"] = correlations
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze logs: {str(e)}",
                "patterns": {},
                "issues": {},
                "summary": {}
            }
    
    def _serialize_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize patterns for JSON output.
        
        Args:
            patterns: Patterns dictionary
            
        Returns:
            Serialized patterns
        """
        serialized = {}
        for category, category_patterns in patterns.items():
            serialized[category] = {}
            for subcategory, issues in category_patterns.items():
                serialized[category][subcategory] = []
                for issue in issues:
                    serialized_issue = dict(issue)
                    if "timestamp" in serialized_issue:
                        serialized_issue["timestamp"] = serialized_issue["timestamp"].isoformat()
                    serialized[category][subcategory].append(serialized_issue)
        return serialized
    
    def _serialize_issues(self, issues: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize issues for JSON output.
        
        Args:
            issues: Issues dictionary
            
        Returns:
            Serialized issues
        """
        serialized = {}
        for severity, issue_list in issues.items():
            serialized[severity] = []
            for issue in issue_list:
                serialized_issue = dict(issue)
                if "timestamp" in serialized_issue:
                    serialized_issue["timestamp"] = serialized_issue["timestamp"].isoformat()
                serialized[severity].append(serialized_issue)
        return serialized


class LogSummaryToolProvider(BaseToolProvider):
    """Tool provider for log summary generation."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize log summary tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "get_log_summary",
            "Generate a summary of critical issues found in system logs with prioritized recommendations"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.analyzer = LogAnalyzer(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of log sources to summarize",
                    "default": ["journald", "syslog", "kern.log", "dmesg"]
                },
                "severity_filter": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"]
                    },
                    "description": "Filter issues by severity levels",
                    "default": ["critical", "high"]
                },
                "max_issues": {
                    "type": "integer",
                    "description": "Maximum number of issues to include in summary",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute log summary generation.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing log summary
        """
        try:
            sources = parameters.get("sources", ["journald", "syslog", "kern.log", "dmesg"])
            severity_filter = parameters.get("severity_filter", ["critical", "high"])
            max_issues = parameters.get("max_issues", 20)
            
            # Parse logs
            entries = self.analyzer.parser.parse_logs(sources)
            
            # Generate critical issues summary
            summary = self.analyzer.generate_critical_issues_summary(entries)
            
            # Filter by severity
            if severity_filter:
                filtered_issues = []
                for issue in summary.get("issues", []):
                    if issue.get("severity") in severity_filter:
                        filtered_issues.append(issue)
                summary["issues"] = filtered_issues[:max_issues]
            
            # Serialize timestamps
            for issue in summary.get("issues", []):
                if "timestamp" in issue:
                    issue["timestamp"] = issue["timestamp"].isoformat()
            
            # Add metadata
            summary.update({
                "success": True,
                "sources_analyzed": sources,
                "severity_filter": severity_filter,
                "total_entries_analyzed": len(entries),
                "generated_at": datetime.now().isoformat()
            })
            
            return summary
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate log summary: {str(e)}",
                "total_critical_issues": 0,
                "issues": [],
                "statistics": {},
                "recommendations": []
            }


class LogEntryAnalysisToolProvider(BaseToolProvider):
    """Tool provider for detailed analysis of specific log entries."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize log entry analysis tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "analyze_log_entry",
            "Provide detailed analysis and context for a specific log entry including classification and recommendations"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.analyzer = LogAnalyzer(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "timestamp": {
                    "type": "string",
                    "description": "Timestamp of the log entry (ISO format)"
                },
                "facility": {
                    "type": "string",
                    "description": "Log facility (e.g., 'kernel', 'auth', 'daemon')"
                },
                "severity": {
                    "type": "string",
                    "description": "Log severity (e.g., 'error', 'warning', 'info')"
                },
                "message": {
                    "type": "string",
                    "description": "Log message content"
                },
                "source": {
                    "type": "string",
                    "description": "Log source (e.g., 'systemd', 'kernel', 'sshd')"
                }
            },
            "required": ["message"]
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute log entry analysis.
        
        Args:
            parameters: Tool parameters containing log entry details
            
        Returns:
            Dictionary containing detailed analysis
        """
        try:
            # Extract log entry parameters
            timestamp_str = parameters.get("timestamp")
            facility = parameters.get("facility", "unknown")
            severity = parameters.get("severity", "info")
            message = parameters.get("message", "")
            source = parameters.get("source", "unknown")
            
            # Parse timestamp
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
            
            # Create LogEntry object
            from ..interfaces import LogEntry
            entry = LogEntry(
                timestamp=timestamp,
                facility=facility,
                severity=severity,
                message=message,
                source=source
            )
            
            # Perform detailed analysis
            analysis = self.analyzer.analyze_specific_entry(entry)
            
            # Serialize timestamp in analysis
            if "entry" in analysis and "timestamp" in analysis["entry"]:
                analysis["entry"]["timestamp"] = analysis["entry"]["timestamp"].isoformat()
            
            analysis["success"] = True
            return analysis
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze log entry: {str(e)}",
                "entry": {},
                "classification": {},
                "context": {},
                "recommendations": []
            }


class HardwareLogPatternToolProvider(BaseToolProvider):
    """Tool provider for hardware-specific log pattern detection."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize hardware log pattern tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "detect_hardware_patterns",
            "Detect patterns in logs that indicate hardware issues including CPU, memory, storage, and network problems"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.detector = PatternDetector(self.system)
        self.parser = LogParser(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of log sources to analyze for hardware patterns",
                    "default": ["journald", "kern.log", "dmesg"]
                },
                "hardware_type": {
                    "type": "string",
                    "enum": ["all", "cpu", "memory", "storage", "network", "graphics", "usb", "pci"],
                    "description": "Specific hardware type to focus on",
                    "default": "all"
                },
                "time_window": {
                    "type": "integer",
                    "description": "Time window in seconds for event correlation",
                    "default": 300
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hardware pattern detection.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing detected hardware patterns
        """
        try:
            sources = parameters.get("sources", ["journald", "kern.log", "dmesg"])
            hardware_type = parameters.get("hardware_type", "all")
            time_window = parameters.get("time_window", 300)
            
            # Parse logs
            entries = self.parser.parse_logs(sources)
            
            # Detect hardware patterns
            patterns = self.detector.detect_hardware_patterns(entries)
            
            # Filter by hardware type if specified
            if hardware_type != "all":
                hardware_key = f"{hardware_type}_issues"
                if hardware_key in patterns:
                    patterns = {hardware_key: patterns[hardware_key]}
                else:
                    patterns = {}
            
            # Correlate hardware events
            correlations = self.detector.correlate_hardware_events(entries, time_window)
            
            # Serialize results
            serialized_patterns = {}
            for category, issues in patterns.items():
                serialized_patterns[category] = []
                for issue in issues:
                    serialized_issue = dict(issue)
                    if "timestamp" in serialized_issue:
                        serialized_issue["timestamp"] = serialized_issue["timestamp"].isoformat()
                    serialized_patterns[category].append(serialized_issue)
            
            # Serialize correlations
            serialized_correlations = []
            for correlation in correlations:
                serialized_correlation = dict(correlation)
                # Handle any datetime objects in correlations
                for key, value in serialized_correlation.items():
                    if isinstance(value, datetime):
                        serialized_correlation[key] = value.isoformat()
                serialized_correlations.append(serialized_correlation)
            
            return {
                "success": True,
                "hardware_type": hardware_type,
                "sources_analyzed": sources,
                "total_entries": len(entries),
                "patterns": serialized_patterns,
                "correlations": serialized_correlations,
                "analysis_metadata": {
                    "time_window_seconds": time_window,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to detect hardware patterns: {str(e)}",
                "patterns": {},
                "correlations": []
            }


class KernelLogPatternToolProvider(BaseToolProvider):
    """Tool provider for kernel-specific log pattern detection."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize kernel log pattern tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "detect_kernel_patterns",
            "Detect patterns in kernel logs including panics, oops, warnings, errors, and driver issues"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.detector = PatternDetector(self.system)
        self.parser = LogParser(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of log sources to analyze for kernel patterns",
                    "default": ["kern.log", "dmesg", "journald"]
                },
                "pattern_type": {
                    "type": "string",
                    "enum": ["all", "panics", "oops", "warnings", "errors", "deadlocks", "driver_issues"],
                    "description": "Specific kernel pattern type to focus on",
                    "default": "all"
                },
                "severity_threshold": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Minimum severity level to include",
                    "default": "medium"
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute kernel pattern detection.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing detected kernel patterns
        """
        try:
            sources = parameters.get("sources", ["kern.log", "dmesg", "journald"])
            pattern_type = parameters.get("pattern_type", "all")
            severity_threshold = parameters.get("severity_threshold", "medium")
            
            # Parse logs
            entries = self.parser.parse_logs(sources)
            
            # Detect kernel patterns
            patterns = self.detector.detect_kernel_patterns(entries)
            
            # Filter by pattern type if specified
            if pattern_type != "all":
                if pattern_type in patterns:
                    patterns = {pattern_type: patterns[pattern_type]}
                else:
                    patterns = {}
            
            # Filter by severity threshold
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            threshold_level = severity_order.get(severity_threshold, 1)
            
            filtered_patterns = {}
            for category, issues in patterns.items():
                filtered_issues = []
                for issue in issues:
                    issue_severity = issue.get("severity", "low")
                    if severity_order.get(issue_severity, 0) >= threshold_level:
                        filtered_issues.append(issue)
                if filtered_issues:
                    filtered_patterns[category] = filtered_issues
            
            # Serialize results
            serialized_patterns = {}
            for category, issues in filtered_patterns.items():
                serialized_patterns[category] = []
                for issue in issues:
                    serialized_issue = dict(issue)
                    if "timestamp" in serialized_issue:
                        serialized_issue["timestamp"] = serialized_issue["timestamp"].isoformat()
                    serialized_patterns[category].append(serialized_issue)
            
            return {
                "success": True,
                "pattern_type": pattern_type,
                "severity_threshold": severity_threshold,
                "sources_analyzed": sources,
                "total_entries": len(entries),
                "patterns": serialized_patterns,
                "analysis_metadata": {
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to detect kernel patterns: {str(e)}",
                "patterns": {}
            }