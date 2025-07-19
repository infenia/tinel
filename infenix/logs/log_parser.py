#!/usr/bin/env python3
"""Log Parser Module.

This module provides system log parsing capabilities for kernel, system,
and application logs with support for various log formats including syslog
and journald.

Copyright 2024 Infenia Private Limited

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

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from ..interfaces import LogEntry, SystemInterface
from ..system import LinuxSystemInterface


class LogFormat(Enum):
    """Supported log formats."""
    RFC3164 = "rfc3164"
    RFC5424 = "rfc5424"
    KERNEL = "kernel"
    SIMPLE = "simple"


@dataclass
class LogPattern:
    """Log pattern configuration."""
    format_type: LogFormat
    regex: str
    description: str


class LogParser:
    """System log parser for various log formats."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize log parser.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        self.syslog_facilities = self._get_syslog_facilities()
        self.syslog_severities = self._get_syslog_severities()
        self.log_patterns = self._get_log_patterns()
        self.timestamp_formats = self._get_timestamp_formats()
    
    def _get_syslog_facilities(self) -> Dict[int, str]:
        """Get syslog facility mapping."""
        return {
            0: 'kernel', 1: 'user', 2: 'mail', 3: 'daemon', 4: 'auth',
            5: 'syslog', 6: 'lpr', 7: 'news', 8: 'uucp', 9: 'cron',
            10: 'authpriv', 11: 'ftp', 16: 'local0', 17: 'local1',
            18: 'local2', 19: 'local3', 20: 'local4', 21: 'local5',
            22: 'local6', 23: 'local7'
        }
    
    def _get_syslog_severities(self) -> Dict[int, str]:
        """Get syslog severity mapping."""
        return {
            0: 'emergency', 1: 'alert', 2: 'critical', 3: 'error',
            4: 'warning', 5: 'notice', 6: 'info', 7: 'debug'
        }
    
    def _get_log_patterns(self) -> List[LogPattern]:
        """Get log parsing patterns."""
        return [
            LogPattern(
                LogFormat.RFC3164,
                r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)',
                "RFC3164 format: MMM dd HH:MM:SS hostname tag: message"
            ),
            LogPattern(
                LogFormat.RFC5424,
                r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+(\S+)\s+([^:]+):\s*(.*)',
                "RFC5424 format: YYYY-MM-DDTHH:MM:SS.sssZ hostname tag - - message"
            ),
            LogPattern(
                LogFormat.KERNEL,
                r'^\[(\s*\d+\.\d+)\]\s*(.*)',
                "Kernel log format: [timestamp] message"
            ),
            LogPattern(
                LogFormat.SIMPLE,
                r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.*)',
                "Simple timestamp format: YYYY-MM-DD HH:MM:SS message"
            )
        ]
    
    def _get_timestamp_formats(self) -> List[str]:
        """Get supported timestamp formats."""
        return [
            '%b %d %H:%M:%S',  # MMM dd HH:MM:SS
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with microseconds
            '%Y-%m-%dT%H:%M:%SZ',  # ISO format
            '%Y-%m-%d %H:%M:%S',  # YYYY-MM-DD HH:MM:SS
            '%m/%d/%Y %H:%M:%S',  # MM/DD/YYYY HH:MM:SS
        ]
    
    def parse_logs(self, log_sources: List[str]) -> List[LogEntry]:
        """Parse system logs from various sources.
        
        Args:
            log_sources: List of log source paths or identifiers
            
        Returns:
            List of parsed log entries
        """
        entries = []
        
        for source in log_sources:
            # Determine log source type and parse accordingly
            if source == 'journald' or source.startswith('journalctl'):
                entries.extend(self._parse_journald_logs(source))
            elif source.startswith('/var/log/'):
                entries.extend(self._parse_file_logs(source))
            elif source == 'dmesg':
                entries.extend(self._parse_dmesg_logs())
            elif source == 'kern.log':
                entries.extend(self._parse_file_logs('/var/log/kern.log'))
            elif source == 'syslog':
                entries.extend(self._parse_file_logs('/var/log/syslog'))
            elif source == 'auth.log':
                entries.extend(self._parse_file_logs('/var/log/auth.log'))
            else:
                # Try to parse as a file path
                entries.extend(self._parse_file_logs(source))
        
        # Sort entries by timestamp
        entries.sort(key=lambda x: x.timestamp)
        
        return entries
    
    def _parse_journald_logs(self, source: str) -> List[LogEntry]:
        """Parse journald logs using journalctl.
        
        Args:
            source: Journald source identifier
            
        Returns:
            List of parsed log entries
        """
        entries = []
        
        # Build journalctl command
        cmd = ['journalctl', '--output=json', '--no-pager']
        
        # Add specific filters based on source
        if source == 'journald':
            # Get all logs from the last 24 hours
            cmd.extend(['--since', '24 hours ago'])
        elif source.startswith('journalctl:'):
            # Parse custom journalctl parameters
            params = source.split(':', 1)[1]
            cmd.extend(params.split())
        
        # Execute journalctl command
        result = self.system.run_command(cmd)
        if not result.success:
            return entries
        
        # Parse JSON output
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            try:
                log_data = json.loads(line)
                entry = self._parse_journald_entry(log_data)
                if entry:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
        
        return entries
    
    def _parse_journald_entry(self, log_data: Dict) -> Optional[LogEntry]:
        """Parse a single journald log entry.
        
        Args:
            log_data: Journald log entry data
            
        Returns:
            Parsed log entry or None if parsing fails
        """
        try:
            # Extract timestamp
            timestamp_str = log_data.get('__REALTIME_TIMESTAMP')
            if timestamp_str:
                # Convert microseconds to seconds
                timestamp = datetime.fromtimestamp(int(timestamp_str) / 1000000)
            else:
                timestamp = datetime.now()
            
            # Extract facility and severity
            priority = log_data.get('PRIORITY', '6')  # Default to info
            try:
                priority_int = int(priority)
                facility_code = priority_int >> 3
                severity_code = priority_int & 7
                facility = self.syslog_facilities.get(facility_code, 'unknown')
                severity = self.syslog_severities.get(severity_code, 'info')
            except ValueError:
                facility = 'unknown'
                severity = 'info'
            
            # Extract message
            message = log_data.get('MESSAGE', '')
            
            # Extract source
            source = log_data.get('_SYSTEMD_UNIT', log_data.get('SYSLOG_IDENTIFIER', 'unknown'))
            
            return LogEntry(
                timestamp=timestamp,
                facility=facility,
                severity=severity,
                message=message,
                source=source
            )
        
        except Exception:
            return None
    
    def _parse_file_logs(self, file_path: str) -> List[LogEntry]:
        """Parse log files in various formats.
        
        Args:
            file_path: Path to log file
            
        Returns:
            List of parsed log entries
        """
        entries = []
        
        # Check if file exists
        if not self.system.file_exists(file_path):
            return entries
        
        # Read file content
        content = self.system.read_file(file_path)
        if not content:
            return entries
        
        # Parse each line
        for line in content.split('\n'):
            if not line.strip():
                continue
            
            entry = self._parse_syslog_line(line, file_path)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_syslog_line(self, line: str, source_file: str) -> Optional[LogEntry]:
        """Parse a single syslog line.
        
        Args:
            line: Log line to parse
            source_file: Source file path
            
        Returns:
            Parsed log entry or None if parsing fails
        """
        # Common syslog patterns
        patterns = [
            # RFC3164 format: MMM dd HH:MM:SS hostname tag: message
            r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)$',
            # RFC5424 format: YYYY-MM-DDTHH:MM:SS.sssZ hostname tag - - message
            r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)\s+(\S+)\s+([^:]+):\s*(.*)$',
            # Kernel log format: [timestamp] message
            r'^\[(\s*\d+\.\d+)\]\s*(.*)$',
            # Simple timestamp format: YYYY-MM-DD HH:MM:SS message
            r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.*)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                return self._create_log_entry_from_match(match, source_file, pattern)
        
        # If no pattern matches, create a basic entry
        return LogEntry(
            timestamp=datetime.now(),
            facility='unknown',
            severity='info',
            message=line,
            source=source_file
        )
    
    def _create_log_entry_from_match(self, match: re.Match, source_file: str, pattern: str) -> LogEntry:
        """Create a log entry from a regex match.
        
        Args:
            match: Regex match object
            source_file: Source file path
            pattern: Pattern that matched
            
        Returns:
            Parsed log entry
        """
        groups = match.groups()
        
        # Parse timestamp
        timestamp_str = groups[0]
        timestamp = self._parse_timestamp(timestamp_str)
        
        # Determine facility and severity based on source file
        facility = self._determine_facility_from_file(source_file)
        severity = 'info'  # Default severity
        
        # Extract message and source
        if len(groups) == 4:
            # Full syslog format
            hostname = groups[1]
            tag = groups[2]
            message = groups[3]
            source = tag
        elif len(groups) == 2:
            # Kernel log or simple format
            message = groups[1]
            source = self._determine_source_from_file(source_file)
            
            # Extract severity from kernel messages
            if '[' in message and ']' in message:
                severity = self._extract_kernel_severity(message)
        else:
            message = ' '.join(groups[1:])
            source = self._determine_source_from_file(source_file)
        
        return LogEntry(
            timestamp=timestamp,
            facility=facility,
            severity=severity,
            message=message,
            source=source
        )
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string into datetime object.
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            Parsed datetime object
        """
        # Try various timestamp formats
        formats = [
            '%b %d %H:%M:%S',  # MMM dd HH:MM:SS
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with microseconds
            '%Y-%m-%dT%H:%M:%SZ',  # ISO format
            '%Y-%m-%d %H:%M:%S',  # YYYY-MM-DD HH:MM:SS
            '%m/%d/%Y %H:%M:%S',  # MM/DD/YYYY HH:MM:SS
        ]
        
        for fmt in formats:
            try:
                # Handle year for syslog format
                if fmt == '%b %d %H:%M:%S':
                    # Add current year
                    current_year = datetime.now().year
                    timestamp_with_year = f"{current_year} {timestamp_str}"
                    return datetime.strptime(timestamp_with_year, f'%Y {fmt}')
                else:
                    return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # Handle kernel timestamp (seconds since boot)
        try:
            if '.' in timestamp_str:
                seconds = float(timestamp_str.strip())
                # Approximate timestamp (not accurate but better than nothing)
                return datetime.now()
        except ValueError:
            pass
        
        # Default to current time if parsing fails
        return datetime.now()
    
    def _determine_facility_from_file(self, file_path: str) -> str:
        """Determine facility from file path.
        
        Args:
            file_path: Log file path
            
        Returns:
            Facility name
        """
        file_name = file_path.split('/')[-1]
        
        if 'kern' in file_name:
            return 'kernel'
        elif 'auth' in file_name:
            return 'auth'
        elif 'mail' in file_name:
            return 'mail'
        elif 'daemon' in file_name:
            return 'daemon'
        elif 'cron' in file_name:
            return 'cron'
        elif 'syslog' in file_name:
            return 'syslog'
        else:
            return 'user'
    
    def _determine_source_from_file(self, file_path: str) -> str:
        """Determine source from file path.
        
        Args:
            file_path: Log file path
            
        Returns:
            Source name
        """
        file_name = file_path.split('/')[-1]
        return file_name.split('.')[0]
    
    def _extract_kernel_severity(self, message: str) -> str:
        """Extract severity from kernel log message.
        
        Args:
            message: Kernel log message
            
        Returns:
            Severity level
        """
        # Kernel log levels
        if any(keyword in message.lower() for keyword in ['panic', 'oops', 'bug']):
            return 'emergency'
        elif any(keyword in message.lower() for keyword in ['error', 'failed', 'failure']):
            return 'error'
        elif any(keyword in message.lower() for keyword in ['warning', 'warn']):
            return 'warning'
        elif any(keyword in message.lower() for keyword in ['notice']):
            return 'notice'
        elif any(keyword in message.lower() for keyword in ['info']):
            return 'info'
        elif any(keyword in message.lower() for keyword in ['debug']):
            return 'debug'
        else:
            return 'info'
    
    def _parse_dmesg_logs(self) -> List[LogEntry]:
        """Parse dmesg logs.
        
        Returns:
            List of parsed log entries
        """
        entries = []
        
        # Execute dmesg command
        result = self.system.run_command(['dmesg', '-T'])
        if not result.success:
            # Try without -T flag
            result = self.system.run_command(['dmesg'])
            if not result.success:
                return entries
        
        # Parse dmesg output
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            
            entry = self._parse_dmesg_line(line)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_dmesg_line(self, line: str) -> Optional[LogEntry]:
        """Parse a single dmesg line.
        
        Args:
            line: Dmesg line to parse
            
        Returns:
            Parsed log entry or None if parsing fails
        """
        # Dmesg with timestamp: [Mon Dec  4 10:30:45 2023] message
        timestamp_match = re.match(r'^\[([^\]]+)\]\s*(.*)$', line)
        if timestamp_match:
            timestamp_str = timestamp_match.group(1)
            message = timestamp_match.group(2)
            
            # Try to parse timestamp
            try:
                timestamp = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Y')
            except ValueError:
                timestamp = datetime.now()
        else:
            # Dmesg without timestamp or with boot time: [12345.678] message
            boot_time_match = re.match(r'^\[\s*(\d+\.\d+)\]\s*(.*)$', line)
            if boot_time_match:
                message = boot_time_match.group(2)
                timestamp = datetime.now()  # Approximate
            else:
                message = line
                timestamp = datetime.now()
        
        # Determine severity from message content
        severity = self._extract_kernel_severity(message)
        
        return LogEntry(
            timestamp=timestamp,
            facility='kernel',
            severity=severity,
            message=message,
            source='dmesg'
        )