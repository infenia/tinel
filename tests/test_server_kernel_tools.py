#!/usr/bin/env python3
"""Tests for MCP Server Kernel Configuration Tools.

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

import pytest
import json
from unittest.mock import Mock, patch, mock_open

from mcp.types import CallToolRequest

# Import server functions
from infenix.server import (
    get_kernel_info,
    get_kernel_config,
    analyze_kernel_config,
    get_kernel_modules,
    get_kernel_parameters,
    handle_call_tool,
    handle_list_tools
)


class TestKernelConfigurationTools:
    """Test cases for kernel configuration MCP tools."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_uname_output = "Linux testhost 5.15.0-generic #123-Ubuntu SMP x86_64 GNU/Linux"
        self.mock_proc_version = "Linux version 5.15.0-generic (buildd@ubuntu) (gcc version 11.2.0)"
        self.mock_cmdline = "BOOT_IMAGE=/boot/vmlinuz root=UUID=12345 ro quiet splash"
        self.mock_lsmod_output = """Module                  Size  Used by
ext4                  786432  2
crc16                  16384  1 ext4
jbd2                  131072  1 ext4"""
    
    @patch('infenix.server.run_command')
    @patch('builtins.open', new_callable=mock_open)
    def test_get_kernel_info(self, mock_file, mock_run_command):
        """Test getting basic kernel information."""
        # Mock command outputs
        mock_run_command.side_effect = [
            {'success': True, 'stdout': self.mock_uname_output},  # uname -a
            {'success': True, 'stdout': self.mock_lsmod_output}   # lsmod
        ]
        
        # Mock file reads
        mock_file.side_effect = [
            mock_open(read_data=self.mock_proc_version).return_value,  # /proc/version
            mock_open(read_data=self.mock_cmdline).return_value        # /proc/cmdline
        ]
        
        result = get_kernel_info()
        
        assert 'uname' in result
        assert 'proc_version' in result
        assert 'cmdline' in result
        assert 'loaded_modules' in result
        
        assert result['uname'] == self.mock_uname_output
        assert result['proc_version'] == self.mock_proc_version
        assert result['cmdline'] == self.mock_cmdline
        assert result['loaded_modules'] == self.mock_lsmod_output
    
    @patch('infenix.server.run_command')
    @patch('builtins.open', side_effect=OSError("File not found"))
    def test_get_kernel_info_file_errors(self, mock_file, mock_run_command):
        """Test kernel info with file read errors."""
        mock_run_command.side_effect = [
            {'success': True, 'stdout': self.mock_uname_output},
            {'success': True, 'stdout': self.mock_lsmod_output}
        ]
        
        result = get_kernel_info()
        
        assert 'uname' in result
        assert 'loaded_modules' in result
        assert 'proc_version_error' in result
        assert 'cmdline_error' in result
    
    @patch('infenix.server.LinuxSystemInterface')
    @patch('infenix.server.KernelConfigParser')
    def test_get_kernel_config_success(self, mock_parser_class, mock_system_class):
        """Test successful kernel configuration retrieval."""
        # Mock system interface
        mock_system = Mock()
        mock_system_class.return_value = mock_system
        
        # Mock parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        
        # Mock kernel config
        from infenix.interfaces import KernelConfig, KernelConfigOption
        mock_config = KernelConfig(
            version="5.15.0",
            options={
                "CONFIG_SMP": KernelConfigOption(
                    name="CONFIG_SMP",
                    value="y",
                    description="Symmetric Multi-Processing support"
                )
            },
            analysis={},
            recommendations={}
        )
        mock_parser.parse_config.return_value = mock_config
        
        result = get_kernel_config()
        
        assert 'config' in result
        assert 'error' not in result
        
        config = result['config']
        assert config['version'] == "5.15.0"
        assert 'CONFIG_SMP' in config['options']
        assert config['options']['CONFIG_SMP']['value'] == "y"
    
    @patch('infenix.server.LinuxSystemInterface')
    @patch('infenix.server.KernelConfigParser')
    def test_get_kernel_config_parse_failure(self, mock_parser_class, mock_system_class):
        """Test kernel configuration retrieval with parse failure."""
        mock_system = Mock()
        mock_system_class.return_value = mock_system
        
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_config.return_value = None
        
        result = get_kernel_config()
        
        assert 'error' in result
        assert result['error'] == 'Could not parse kernel configuration'
    
    @patch('infenix.server.LinuxSystemInterface')
    @patch('infenix.server.KernelConfigParser')
    def test_get_kernel_config_exception(self, mock_parser_class, mock_system_class):
        """Test kernel configuration retrieval with exception."""
        mock_parser_class.side_effect = Exception("Test exception")
        
        result = get_kernel_config()
        
        assert 'error' in result
        assert 'Test exception' in result['error']
    
    @patch('infenix.server.LinuxSystemInterface')
    @patch('infenix.server.KernelConfigParser')
    @patch('infenix.server.KernelConfigAnalyzer')
    def test_analyze_kernel_config_success(self, mock_analyzer_class, mock_parser_class, mock_system_class):
        """Test successful kernel configuration analysis."""
        # Mock system interface
        mock_system = Mock()
        mock_system_class.return_value = mock_system
        
        # Mock parser
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock kernel config
        from infenix.interfaces import KernelConfig, KernelConfigOption
        mock_config = KernelConfig(
            version="5.15.0",
            options={
                "CONFIG_SECURITY": KernelConfigOption(
                    name="CONFIG_SECURITY",
                    value="n",
                    description="Security framework"
                )
            },
            analysis={},
            recommendations={}
        )
        mock_parser.parse_config.return_value = mock_config
        
        # Mock analysis result
        mock_analysis = {
            'security_score': 75.0,
            'performance_score': 85.0,
            'security': {
                'issues': [
                    {
                        'severity': 'high',
                        'option': 'CONFIG_SECURITY',
                        'description': 'Security framework is disabled',
                        'recommendation': 'Enable CONFIG_SECURITY=y'
                    }
                ],
                'recommendations': [
                    {
                        'category': 'security',
                        'priority': 'high',
                        'option': 'CONFIG_SECURITY',
                        'current_value': 'n',
                        'recommended_value': 'y',
                        'description': 'Enable security framework',
                        'impact': 'Enhanced system security'
                    }
                ]
            },
            'performance': {
                'issues': [],
                'recommendations': []
            }
        }
        mock_analyzer.analyze_config.return_value = mock_analysis
        
        result = analyze_kernel_config()
        
        assert 'analysis' in result
        assert 'error' not in result
        
        analysis = result['analysis']
        assert analysis['security_score'] == 75.0
        assert analysis['performance_score'] == 85.0
        assert len(analysis['security']['recommendations']) == 1
        assert len(analysis['security']['issues']) == 1
        assert analysis['security']['recommendations'][0]['option'] == "CONFIG_SECURITY"
    
    @patch('infenix.server.run_command')
    def test_get_kernel_modules_success(self, mock_run_command):
        """Test successful kernel module information retrieval."""
        mock_run_command.side_effect = [
            {'success': True, 'stdout': self.mock_lsmod_output},  # lsmod
            {'success': True, 'stdout': 'filename: /lib/modules/5.15.0/kernel/fs/ext4/ext4.ko'},  # modinfo ext4
            {'success': True, 'stdout': 'filename: /lib/modules/5.15.0/kernel/lib/crc16.ko'},     # modinfo crc16
            {'success': True, 'stdout': 'filename: /lib/modules/5.15.0/kernel/fs/jbd2/jbd2.ko'},  # modinfo jbd2
            {'success': True, 'stdout': '/lib/modules/5.15.0/kernel/fs/ext4/ext4.ko\n/lib/modules/5.15.0/kernel/lib/crc16.ko'}  # find modules
        ]
        
        result = get_kernel_modules()
        
        assert 'loaded_modules' in result
        assert 'module_details' in result
        assert 'available_modules' in result
        
        assert result['loaded_modules'] == self.mock_lsmod_output
        assert 'ext4' in result['module_details']
        assert 'crc16' in result['module_details']
        assert 'jbd2' in result['module_details']
        assert len(result['available_modules']) == 2
    
    @patch('infenix.server.run_command')
    def test_get_kernel_parameters_success(self, mock_run_command):
        """Test successful kernel parameter retrieval."""
        mock_sysctl_all = """kernel.version = #123-Ubuntu SMP
kernel.ostype = Linux
vm.swappiness = 60"""
        
        mock_run_command.side_effect = [
            {'success': True, 'stdout': mock_sysctl_all},  # sysctl -a
            {'success': True, 'stdout': 'kernel.version = #123-Ubuntu SMP'},  # sysctl kernel.version
            {'success': True, 'stdout': 'kernel.ostype = Linux'},             # sysctl kernel.ostype
            {'success': True, 'stdout': 'kernel.osrelease = 5.15.0-generic'}, # sysctl kernel.osrelease
            {'success': True, 'stdout': 'vm.swappiness = 60'},                 # sysctl vm.swappiness
            {'success': True, 'stdout': 'vm.dirty_ratio = 20'},                # sysctl vm.dirty_ratio
            {'success': True, 'stdout': 'net.core.rmem_max = 212992'},         # sysctl net.core.rmem_max
            {'success': True, 'stdout': 'net.core.wmem_max = 212992'},         # sysctl net.core.wmem_max
            {'success': True, 'stdout': 'fs.file-max = 9223372036854775807'},  # sysctl fs.file-max
        ]
        
        result = get_kernel_parameters()
        
        assert 'sysctl_all' in result
        assert 'important_parameters' in result
        
        assert result['sysctl_all'] == mock_sysctl_all
        assert 'kernel.version' in result['important_parameters']
        assert 'vm.swappiness' in result['important_parameters']
    
    @pytest.mark.asyncio
    async def test_handle_list_tools_includes_kernel_tools(self):
        """Test that kernel tools are included in the tool list."""
        result = await handle_list_tools()
        
        tool_names = [tool.name for tool in result.tools]
        
        assert 'get_kernel_info' in tool_names
        assert 'get_kernel_config' in tool_names
        assert 'analyze_kernel_config' in tool_names
        assert 'get_kernel_modules' in tool_names
        assert 'get_kernel_parameters' in tool_names
        
        # Check tool descriptions
        kernel_info_tool = next(tool for tool in result.tools if tool.name == 'get_kernel_info')
        assert 'kernel information' in kernel_info_tool.description.lower()
        
        analyze_tool = next(tool for tool in result.tools if tool.name == 'analyze_kernel_config')
        assert 'analyze' in analyze_tool.description.lower()
        assert 'security' in analyze_tool.description.lower()
    
    @pytest.mark.asyncio
    @patch('infenix.server.get_kernel_info')
    async def test_handle_call_tool_kernel_info(self, mock_get_kernel_info):
        """Test calling kernel info tool through MCP handler."""
        mock_get_kernel_info.return_value = {
            'uname': self.mock_uname_output,
            'proc_version': self.mock_proc_version
        }
        
        request = CallToolRequest(
            method="tools/call",
            params={"name": "get_kernel_info", "arguments": {}},
            name="get_kernel_info",
            arguments={}
        )
        result = await handle_call_tool(request)
        
        assert result.isError is None or result.isError is False
        assert len(result.content) == 1
        
        # Parse the JSON content
        content_text = result.content[0].text
        data = json.loads(content_text)
        
        assert 'uname' in data
        assert 'proc_version' in data
        assert data['uname'] == self.mock_uname_output
    
    @pytest.mark.asyncio
    @patch('infenix.server.analyze_kernel_config')
    async def test_handle_call_tool_analyze_kernel_config(self, mock_analyze):
        """Test calling kernel config analysis tool through MCP handler."""
        mock_analyze.return_value = {
            'analysis': {
                'security_score': 80.0,
                'performance_score': 90.0,
                'recommendations': []
            }
        }
        
        request = CallToolRequest(
            method="tools/call",
            params={"name": "analyze_kernel_config", "arguments": {}},
            name="analyze_kernel_config",
            arguments={}
        )
        result = await handle_call_tool(request)
        
        assert result.isError is None or result.isError is False
        assert len(result.content) == 1
        
        # Parse the JSON content
        content_text = result.content[0].text
        data = json.loads(content_text)
        
        assert 'analysis' in data
        assert data['analysis']['security_score'] == 80.0
    
    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown_kernel_tool(self):
        """Test calling unknown kernel tool."""
        request = CallToolRequest(
            method="tools/call",
            params={"name": "unknown_kernel_tool", "arguments": {}},
            name="unknown_kernel_tool",
            arguments={}
        )
        result = await handle_call_tool(request)
        
        assert result.isError is True
        assert len(result.content) == 1
        assert 'Unknown tool' in result.content[0].text
    
    @pytest.mark.asyncio
    @patch('infenix.server.get_kernel_config')
    async def test_handle_call_tool_with_exception(self, mock_get_kernel_config):
        """Test calling kernel tool that raises an exception."""
        mock_get_kernel_config.side_effect = Exception("Test exception")
        
        request = CallToolRequest(
            method="tools/call",
            params={"name": "get_kernel_config", "arguments": {}},
            name="get_kernel_config",
            arguments={}
        )
        result = await handle_call_tool(request)
        
        assert result.isError is True
        assert len(result.content) == 1
        assert 'Error getting get_kernel_config information' in result.content[0].text
        assert 'Test exception' in result.content[0].text


if __name__ == "__main__":
    pytest.main([__file__])