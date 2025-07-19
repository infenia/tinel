#!/usr/bin/env python3
"""Tests for the Log Parser module.

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

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from infenix.logs.log_parser import LogParser
from infenix.interfaces import CommandResult, LogEntry


class TestLogParser(unittest.TestCase):
    """Test cases for the LogParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_system = MagicMock()
        self.parser = LogParser(self.mock_system)
    
    def test_parse_logs(self):
        """Test parsing logs from various sources."""
        # Mock system interface responses
        self._setup_basic_mocks()
        
        # Call the method under test
        result = self.parser.parse_logs(['syslog', 'dmesg'])
        
        # Verify the result
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIsInstance(result[0], LogEntry)
    
    def test_parse_syslog_line(self):
        """Test parsing syslog lines."""
        # Test RFC3164 format
        line = "Dec  4 10:30:45 hostname sshd[1234]: Accepted password for user from 192.168.1.100"
        result = self.parser._parse_syslog_line(line, '/var/log/syslog')
        
        self.assertIsInstance(result, LogEntry)
        self.assertEqual(result.facility, 'syslog')
        self.assertEqual(result.severity, 'info')
        self.assertEqual(result.source, 'sshd[1234]')
        self.assertIn('Accepted password', result.message)
        
        # Test kernel log format
        line = "[12345.678] usb 1-1: new high-speed USB device number 2 using ehci-pci"
        result = self.parser._parse_syslog_line(line, '/var/log/kern.log')
        
        self.assertIsInstance(result, LogEntry)
        self.assertEqual(result.facility, 'kernel')
        self.assertEqual(result.severity, 'info')
        self.assertEqual(result.source, 'kern')
        self.assertIn('USB device', result.message)
    
    def test_parse_journald_entry(self):
        """Test parsing journald log entries."""
        log_data = {
            '__REALTIME_TIMESTAMP': '1701684645123456',
            'PRIORITY': '6',
            'MESSAGE': 'Test message',
            'SYSLOG_IDENTIFIER': 'test-service',
            '_SYSTEMD_UNIT': 'test.service'
        }
        
        result = self.parser._parse_journald_entry(log_data)
        
        self.assertIsInstance(result, LogEntry)
        self.assertEqual(result.facility, 'unknown')
        self.assertEqual(result.severity, 'info')
        self.assertEqual(result.message, 'Test message')
        self.assertEqual(result.source, 'test.service')
    
    def test_parse_timestamp(self):
        """Test parsing various timestamp formats."""
        # Test syslog format
        timestamp = self.parser._parse_timestamp('Dec  4 10:30:45')
        self.assertIsInstance(timestamp, datetime)
        self.assertEqual(timestamp.month, 12)
        self.assertEqual(timestamp.day, 4)
        self.assertEqual(timestamp.hour, 10)
        self.assertEqual(timestamp.minute, 30)
        self.assertEqual(timestamp.second, 45)
        
        # Test ISO format
        timestamp = self.parser._parse_timestamp('2023-12-04T10:30:45Z')
        self.assertIsInstance(timestamp, datetime)
        self.assertEqual(timestamp.year, 2023)
        self.assertEqual(timestamp.month, 12)
        self.assertEqual(timestamp.day, 4)
        
        # Test simple format
        timestamp = self.parser._parse_timestamp('2023-12-04 10:30:45')
        self.assertIsInstance(timestamp, datetime)
        self.assertEqual(timestamp.year, 2023)
        self.assertEqual(timestamp.month, 12)
        self.assertEqual(timestamp.day, 4)
    
    def test_determine_facility_from_file(self):
        """Test determining facility from file path."""
        self.assertEqual(self.parser._determine_facility_from_file('/var/log/kern.log'), 'kernel')
        self.assertEqual(self.parser._determine_facility_from_file('/var/log/auth.log'), 'auth')
        self.assertEqual(self.parser._determine_facility_from_file('/var/log/mail.log'), 'mail')
        self.assertEqual(self.parser._determine_facility_from_file('/var/log/daemon.log'), 'daemon')
        self.assertEqual(self.parser._determine_facility_from_file('/var/log/cron.log'), 'cron')
        self.assertEqual(self.parser._determine_facility_from_file('/var/log/syslog'), 'syslog')
        self.assertEqual(self.parser._determine_facility_from_file('/var/log/custom.log'), 'user')
    
    def test_extract_kernel_severity(self):
        """Test extracting severity from kernel messages."""
        self.assertEqual(self.parser._extract_kernel_severity('kernel panic: something bad happened'), 'emergency')
        self.assertEqual(self.parser._extract_kernel_severity('error: device not found'), 'error')
        self.assertEqual(self.parser._extract_kernel_severity('warning: deprecated function used'), 'warning')
        self.assertEqual(self.parser._extract_kernel_severity('notice: configuration changed'), 'notice')
        self.assertEqual(self.parser._extract_kernel_severity('info: device initialized'), 'info')
        self.assertEqual(self.parser._extract_kernel_severity('debug: entering function'), 'debug')
        self.assertEqual(self.parser._extract_kernel_severity('normal message'), 'info')
    
    def test_parse_dmesg_line(self):
        """Test parsing dmesg lines."""
        # Test with timestamp
        line = "[Mon Dec  4 10:30:45 2023] usb 1-1: new high-speed USB device"
        result = self.parser._parse_dmesg_line(line)
        
        self.assertIsInstance(result, LogEntry)
        self.assertEqual(result.facility, 'kernel')
        self.assertEqual(result.severity, 'info')
        self.assertEqual(result.source, 'dmesg')
        self.assertIn('USB device', result.message)
        
        # Test with boot time
        line = "[12345.678] error: device initialization failed"
        result = self.parser._parse_dmesg_line(line)
        
        self.assertIsInstance(result, LogEntry)
        self.assertEqual(result.facility, 'kernel')
        self.assertEqual(result.severity, 'error')
        self.assertEqual(result.source, 'dmesg')
        self.assertIn('initialization failed', result.message)
    
    def _setup_basic_mocks(self):
        """Set up basic mocks for system interface."""
        # Mock file existence
        self.mock_system.file_exists.side_effect = lambda path: {
            '/var/log/syslog': True,
            '/var/log/kern.log': True,
            '/var/log/auth.log': True,
        }.get(path, False)
        
        # Mock file content
        self.mock_system.read_file.side_effect = lambda path: {
            '/var/log/syslog': """Dec  4 10:30:45 hostname sshd[1234]: Accepted password for user from 192.168.1.100
Dec  4 10:31:00 hostname systemd[1]: Started Test Service.
Dec  4 10:31:15 hostname kernel: [12345.678] usb 1-1: new high-speed USB device""",
            '/var/log/kern.log': """Dec  4 10:30:00 hostname kernel: [12300.000] Linux version 5.15.0-58-generic
Dec  4 10:30:01 hostname kernel: [12301.000] Command line: BOOT_IMAGE=/boot/vmlinuz
Dec  4 10:30:02 hostname kernel: [12302.000] error: device initialization failed""",
        }.get(path, None)
        
        # Mock command execution
        journald_output = json.dumps({
            '__REALTIME_TIMESTAMP': '1701684645123456',
            'PRIORITY': '6',
            'MESSAGE': 'Test journald message',
            'SYSLOG_IDENTIFIER': 'test-service',
            '_SYSTEMD_UNIT': 'test.service'
        })
        
        dmesg_output = """[Mon Dec  4 10:30:45 2023] Linux version 5.15.0-58-generic
[Mon Dec  4 10:30:46 2023] Command line: BOOT_IMAGE=/boot/vmlinuz
[Mon Dec  4 10:30:47 2023] error: device initialization failed"""
        
        self.mock_system.run_command.side_effect = lambda cmd: {
            'journalctl --output=json --no-pager --since 24 hours ago': 
                CommandResult(True, journald_output, '', 0),
            'dmesg -T': 
                CommandResult(True, dmesg_output, '', 0),
            'dmesg': 
                CommandResult(True, dmesg_output, '', 0),
        }.get(' '.join(cmd), CommandResult(False, '', 'Command not found', 1))


if __name__ == '__main__':
    unittest.main()