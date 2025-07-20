#!/usr/bin/env python3
"""Tests for CLI argument parser.

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

import pytest
import sys
from unittest.mock import patch

from infenix.cli.parser import (
    create_argument_parser,
    parse_arguments,
    validate_arguments,
)


class TestArgumentParser:
    """Test cases for the argument parser."""
    
    def test_create_argument_parser(self):
        """Test parser creation."""
        parser = create_argument_parser()
        assert parser.prog == 'infenix'
        assert 'Infenix' in parser.description
    
    def test_global_options(self):
        """Test global command line options."""
        parser = create_argument_parser()
        
        # Test version option
        with pytest.raises(SystemExit):
            parser.parse_args(['--version'])
    
    def test_verbose_option(self):
        """Test verbose option parsing."""
        args = parse_arguments(['hardware', 'cpu', '-v'])
        assert args.verbose == 1
        
        args = parse_arguments(['hardware', 'cpu', '-vv'])
        assert args.verbose == 2
        
        args = parse_arguments(['hardware', 'cpu', '-vvv'])
        assert args.verbose == 3
    
    def test_quiet_option(self):
        """Test quiet option parsing."""
        args = parse_arguments(['hardware', 'cpu', '--quiet'])
        assert args.quiet is True
    
    def test_format_option(self):
        """Test format option parsing."""
        args = parse_arguments(['hardware', 'cpu', '--format', 'json'])
        assert args.format == 'json'
        
        args = parse_arguments(['hardware', 'cpu', '--format', 'yaml'])
        assert args.format == 'yaml'
        
        args = parse_arguments(['hardware', 'cpu', '--format', 'text'])
        assert args.format == 'text'
    
    def test_no_color_option(self):
        """Test no-color option parsing."""
        args = parse_arguments(['hardware', 'cpu', '--no-color'])
        assert args.no_color is True
    
    def test_config_option(self):
        """Test config option parsing."""
        args = parse_arguments(['hardware', 'cpu', '--config', '/path/to/config'])
        assert args.config == '/path/to/config'


class TestHardwareCommands:
    """Test cases for hardware command parsing."""
    
    def test_hardware_command(self):
        """Test basic hardware command parsing."""
        args = parse_arguments(['hardware', 'cpu'])
        assert args.command == 'hardware'
        assert args.hardware_command == 'cpu'
    
    def test_hardware_aliases(self):
        """Test hardware command aliases."""
        args = parse_arguments(['hw', 'cpu'])
        assert args.command == 'hw'
        assert args.hardware_command == 'cpu'
    
    def test_cpu_options(self):
        """Test CPU command options."""
        args = parse_arguments(['hardware', 'cpu', '--temperature', '--features'])
        assert args.temperature is True
        assert args.features is True
    
    def test_memory_options(self):
        """Test memory command options."""
        args = parse_arguments(['hardware', 'memory', '--usage', '--timing'])
        assert args.usage is True
        assert args.timing is True
        
        # Test alias
        args = parse_arguments(['hardware', 'mem', '--usage'])
        assert args.hardware_command == 'mem'
        assert args.usage is True
    
    def test_storage_options(self):
        """Test storage command options."""
        args = parse_arguments(['hardware', 'storage', '--health', '--performance'])
        assert args.health is True
        assert args.performance is True
        
        # Test alias
        args = parse_arguments(['hardware', 'disk', '--health'])
        assert args.hardware_command == 'disk'
        assert args.health is True
    
    def test_network_options(self):
        """Test network command options."""
        args = parse_arguments(['hardware', 'network', '--interfaces'])
        assert args.interfaces is True
        
        # Test alias
        args = parse_arguments(['hardware', 'net', '--interfaces'])
        assert args.hardware_command == 'net'
        assert args.interfaces is True
    
    def test_graphics_options(self):
        """Test graphics command options."""
        args = parse_arguments(['hardware', 'graphics', '--drivers'])
        assert args.drivers is True
        
        # Test alias
        args = parse_arguments(['hardware', 'gpu', '--drivers'])
        assert args.hardware_command == 'gpu'
        assert args.drivers is True
    
    def test_pci_options(self):
        """Test PCI command options."""
        args = parse_arguments(['hardware', 'pci', '--tree'])
        assert args.tree is True
    
    def test_usb_options(self):
        """Test USB command options."""
        args = parse_arguments(['hardware', 'usb', '--tree'])
        assert args.tree is True
    
    def test_all_hardware_options(self):
        """Test all hardware command options."""
        args = parse_arguments(['hardware', 'all', '--summary'])
        assert args.hardware_command == 'all'
        assert args.summary is True


class TestKernelCommands:
    """Test cases for kernel command parsing."""
    
    def test_kernel_command(self):
        """Test basic kernel command parsing."""
        args = parse_arguments(['kernel', 'info'])
        assert args.command == 'kernel'
        assert args.kernel_command == 'info'
    
    def test_kernel_config_options(self):
        """Test kernel config command options."""
        args = parse_arguments(['kernel', 'config', '--analyze', '--recommendations'])
        assert args.analyze is True
        assert args.recommendations is True
        
        args = parse_arguments(['kernel', 'config', '--option', 'CONFIG_SMP'])
        assert args.option == 'CONFIG_SMP'
    
    def test_kernel_modules_options(self):
        """Test kernel modules command options."""
        args = parse_arguments(['kernel', 'modules', '--loaded'])
        assert args.loaded is True
        
        args = parse_arguments(['kernel', 'modules', '--available'])
        assert args.available is True
    
    def test_kernel_parameters_options(self):
        """Test kernel parameters command options."""
        args = parse_arguments(['kernel', 'parameters', '--parameter', 'vm.swappiness'])
        assert args.parameter == 'vm.swappiness'
        
        # Test alias
        args = parse_arguments(['kernel', 'params', '--parameter', 'vm.swappiness'])
        assert args.kernel_command == 'params'
        assert args.parameter == 'vm.swappiness'


class TestLogCommands:
    """Test cases for log command parsing."""
    
    def test_logs_command(self):
        """Test basic logs command parsing."""
        args = parse_arguments(['logs', 'system'])
        assert args.command == 'logs'
        assert args.logs_command == 'system'
    
    def test_logs_common_options(self):
        """Test common log options."""
        args = parse_arguments(['logs', 'system', '--lines', '200', '--since', '1 hour ago'])
        assert args.lines == 200
        assert args.since == '1 hour ago'
        
        args = parse_arguments(['logs', 'system', '--until', '2023-01-01'])
        assert args.until == '2023-01-01'
    
    def test_system_logs_options(self):
        """Test system logs command options."""
        args = parse_arguments(['logs', 'system', '--source', 'syslog'])
        assert args.source == 'syslog'
    
    def test_hardware_logs_options(self):
        """Test hardware logs command options."""
        args = parse_arguments(['logs', 'hardware', '--component', 'cpu'])
        assert args.component == 'cpu'
    
    def test_kernel_logs_options(self):
        """Test kernel logs command options."""
        args = parse_arguments(['logs', 'kernel', '--errors-only'])
        assert args.errors_only is True
    
    def test_log_summary_options(self):
        """Test log summary command options."""
        args = parse_arguments(['logs', 'summary', '--critical-only'])
        assert args.critical_only is True
    
    def test_analyze_log_file(self):
        """Test analyze log file command."""
        args = parse_arguments(['logs', 'analyze', '/var/log/syslog', '--patterns'])
        assert args.logs_command == 'analyze'
        assert args.file == '/var/log/syslog'
        assert args.patterns is True


class TestDiagnosticsCommands:
    """Test cases for diagnostics command parsing."""
    
    def test_diagnostics_command(self):
        """Test basic diagnostics command parsing."""
        args = parse_arguments(['diagnose', 'system'])
        assert args.command == 'diagnose'
        assert args.diag_command == 'system'
        
        # Test alias
        args = parse_arguments(['diag', 'system'])
        assert args.command == 'diag'
        assert args.diag_command == 'system'
    
    def test_system_diagnostics_options(self):
        """Test system diagnostics command options."""
        args = parse_arguments(['diagnose', 'system', '--recommendations'])
        assert args.recommendations is True
    
    def test_hardware_diagnostics_options(self):
        """Test hardware diagnostics command options."""
        args = parse_arguments(['diagnose', 'hardware', '--components', 'cpu', 'memory'])
        assert args.components == ['cpu', 'memory']
        
        args = parse_arguments(['diagnose', 'hardware', '--temperature', '--performance', '--health'])
        assert args.temperature is True
        assert args.performance is True
        assert args.health is True
    
    def test_query_command(self):
        """Test query command parsing."""
        args = parse_arguments(['diagnose', 'query', 'What is my CPU temperature?', '--execute'])
        assert args.diag_command == 'query'
        assert args.query == 'What is my CPU temperature?'
        assert args.execute is True
    
    def test_recommendations_options(self):
        """Test recommendations command options."""
        args = parse_arguments(['diagnose', 'recommendations', '--focus', 'hardware', 'security'])
        assert args.focus == ['hardware', 'security']
        
        args = parse_arguments(['diagnose', 'rec', '--priority', 'critical', 'high'])
        assert args.diag_command == 'rec'
        assert args.priority == ['critical', 'high']
        
        args = parse_arguments(['diagnose', 'recommendations', '--max-recommendations', '10'])
        assert args.max_recommendations == 10
        
        args = parse_arguments(['diagnose', 'recommendations', '--implementation-guides'])
        assert args.implementation_guides is True


class TestServerCommands:
    """Test cases for server command parsing."""
    
    def test_server_start_command(self):
        """Test server start command parsing."""
        args = parse_arguments(['server', 'start'])
        assert args.command == 'server'
        assert args.server_command == 'start'
    
    def test_server_start_options(self):
        """Test server start command options."""
        args = parse_arguments(['server', 'start', '--host', '0.0.0.0', '--port', '9000', '--debug'])
        assert args.host == '0.0.0.0'
        assert args.port == 9000
        assert args.debug is True
    
    def test_list_tools_command(self):
        """Test list tools command parsing."""
        args = parse_arguments(['server', 'list-tools'])
        assert args.server_command == 'list-tools'
        
        args = parse_arguments(['server', 'list-tools', '--category', 'hardware'])
        assert args.category == 'hardware'


class TestArgumentValidation:
    """Test cases for argument validation."""
    
    def test_validate_conflicting_options(self):
        """Test validation of conflicting options."""
        # Create a mock args object
        class MockArgs:
            def __init__(self):
                self.verbose = 1
                self.quiet = True
                self.command = 'hardware'
        
        args = MockArgs()
        assert validate_arguments(args) is False
    
    def test_validate_verbosity_level(self):
        """Test validation of verbosity level."""
        class MockArgs:
            def __init__(self):
                self.verbose = 5  # Too high
                self.quiet = False
                self.command = 'hardware'
        
        args = MockArgs()
        assert validate_arguments(args) is False
    
    def test_validate_missing_command(self):
        """Test validation of missing command."""
        class MockArgs:
            def __init__(self):
                self.verbose = 0
                self.quiet = False
                self.command = None
        
        args = MockArgs()
        assert validate_arguments(args) is False
    
    def test_validate_valid_arguments(self):
        """Test validation of valid arguments."""
        class MockArgs:
            def __init__(self):
                self.verbose = 2
                self.quiet = False
                self.command = 'hardware'
                self.format = 'json'
                self.no_color = False
        
        args = MockArgs()
        assert validate_arguments(args) is True


class TestErrorHandling:
    """Test cases for error handling in argument parsing."""
    
    def test_invalid_format_option(self):
        """Test handling of invalid format option."""
        with pytest.raises(SystemExit):
            parse_arguments(['hardware', 'cpu', '--format', 'invalid'])
    
    def test_invalid_verbosity_combination(self):
        """Test handling of invalid verbosity combination."""
        with patch('sys.stderr'):
            with pytest.raises(SystemExit):
                parse_arguments(['hardware', 'cpu', '-v', '--quiet'])
    
    def test_missing_required_argument(self):
        """Test handling of missing required arguments."""
        with pytest.raises(SystemExit):
            parse_arguments(['logs', 'analyze'])  # Missing file argument
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        with patch('sys.stderr'):
            with pytest.raises(SystemExit):
                parse_arguments(['invalid-command'])


if __name__ == "__main__":
    pytest.main([__file__])