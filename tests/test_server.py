"""Tests for the Infenix server module.

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
import pytest
import subprocess
import asyncio
from unittest.mock import patch, MagicMock, mock_open

from mcp.types import CallToolRequest

from infenix.server import (
    run_command,
    read_sys_file,
    get_cpu_info,
    get_memory_info,
    get_storage_info,
    get_pci_devices,
    get_usb_devices,
    get_network_info,
    get_graphics_info,
    get_all_hardware_info,
    create_tool_result,
    handle_list_tools,
    handle_call_tool,
    main,
    server,
)


def test_run_command_success():
    """Test successful command execution."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = run_command(["test", "command"])
        
        assert result["success"] is True
        assert result["stdout"] == "test output"
        assert result["returncode"] == 0
        mock_run.assert_called_once_with(
            ["test", "command"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )


def test_run_command_timeout():
    """Test command timeout handling."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=30)
        
        result = run_command(["test", "command"])
        
        assert result["success"] is False
        assert "Command timed out" in result["error"]


def test_run_command_exception():
    """Test general exception handling in command execution."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("Test error")
        
        result = run_command(["test", "command"])
        
        assert result["success"] is False
        assert "Test error" in result["error"]


def test_read_sys_file_success():
    """Test successful file reading."""
    with patch("builtins.open", mock_open(read_data="test content\n")) as m:
        result = read_sys_file("/test/path")
        
        assert result == "test content"
        m.assert_called_once_with("/test/path", "r")


def test_read_sys_file_exception():
    """Test exception handling in file reading."""
    with patch("builtins.open") as mock_open:
        mock_open.side_effect = Exception("Test error")
        
        result = read_sys_file("/test/path")
        
        assert result is None


def test_get_cpu_info():
    """Test CPU information gathering."""
    # Mock file reading
    mock_cpuinfo = "processor : 0\nvendor_id : GenuineIntel\n"
    mock_freq = "3700000"
    
    # Set up mocks
    with patch("builtins.open", mock_open(read_data=mock_cpuinfo)), \
         patch("infenix.server.run_command") as mock_run, \
         patch("infenix.server.read_sys_file") as mock_read_sys:
        
        # Configure mocks
        mock_run.return_value = {
            "success": True,
            "stdout": "Architecture: x86_64\nCPU(s): 8",
            "stderr": "",
            "returncode": 0
        }
        mock_read_sys.return_value = mock_freq
        
        # Call the function
        result = get_cpu_info()
        
        # Verify results
        assert "proc_cpuinfo" in result
        assert result["proc_cpuinfo"] == mock_cpuinfo
        assert "lscpu" in result
        assert result["lscpu"] == "Architecture: x86_64\nCPU(s): 8"
        assert "current_frequency_khz" in result
        assert result["current_frequency_khz"] == mock_freq


def test_get_cpu_info_with_errors():
    """Test CPU information gathering with errors."""
    # Set up mocks
    with patch("builtins.open") as mock_open, \
         patch("infenix.server.run_command") as mock_run, \
         patch("infenix.server.read_sys_file") as mock_read_sys:
        
        # Configure mocks for errors
        mock_open.side_effect = Exception("File error")
        mock_run.return_value = {
            "success": False,
            "error": "Command failed",
            "stdout": "",
            "stderr": "Error",
            "returncode": 1
        }
        mock_read_sys.return_value = None
        
        # Call the function
        result = get_cpu_info()
        
        # Verify results
        assert "proc_cpuinfo_error" in result
        assert "File error" in result["proc_cpuinfo_error"]
        assert "lscpu_error" in result
        assert "current_frequency_khz" not in result


def test_get_memory_info():
    """Test memory information gathering."""
    # Mock file reading
    mock_meminfo = "MemTotal: 16384000 kB\nMemFree: 8192000 kB\n"
    
    # Set up mocks
    with patch("builtins.open", mock_open(read_data=mock_meminfo)), \
         patch("infenix.server.run_command") as mock_run:
        
        # Configure mocks
        mock_run.return_value = {
            "success": True,
            "stdout": "Memory Device\nSize: 8 GB\nType: DDR4",
            "stderr": "",
            "returncode": 0
        }
        
        # Call the function
        result = get_memory_info()
        
        # Verify results
        assert "proc_meminfo" in result
        assert result["proc_meminfo"] == mock_meminfo
        assert "dmidecode_memory" in result
        assert result["dmidecode_memory"] == "Memory Device\nSize: 8 GB\nType: DDR4"


def test_get_memory_info_with_errors():
    """Test memory information gathering with errors."""
    # Set up mocks
    with patch("builtins.open") as mock_open, \
         patch("infenix.server.run_command") as mock_run:
        
        # Configure mocks for errors
        mock_open.side_effect = Exception("File error")
        mock_run.return_value = {
            "success": False,
            "error": "Command failed",
            "stdout": "",
            "stderr": "Error",
            "returncode": 1
        }
        
        # Call the function
        result = get_memory_info()
        
        # Verify results
        assert "proc_meminfo_error" in result
        assert "File error" in result["proc_meminfo_error"]
        assert "dmidecode_memory_error" in result


def test_get_storage_info():
    """Test storage information gathering."""
    # Mock JSON output
    mock_lsblk_json = '{"blockdevices": [{"name": "sda", "size": "500G"}]}'
    
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks with different return values for each call
        mock_run.side_effect = [
            # lsblk call
            {
                "success": True,
                "stdout": mock_lsblk_json,
                "stderr": "",
                "returncode": 0
            },
            # df call
            {
                "success": True,
                "stdout": "Filesystem Size Used Avail Use% Mounted on\n/dev/sda1 500G 100G 400G 20% /",
                "stderr": "",
                "returncode": 0
            },
            # fdisk call
            {
                "success": True,
                "stdout": "Disk /dev/sda: 500 GiB\nSector size: 512 bytes",
                "stderr": "",
                "returncode": 0
            }
        ]
        
        # Call the function
        result = get_storage_info()
        
        # Verify results
        assert "lsblk" in result
        assert isinstance(result["lsblk"], dict)
        assert "blockdevices" in result["lsblk"]
        assert "df" in result
        assert "fdisk" in result


def test_get_storage_info_with_errors():
    """Test storage information gathering with errors."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run, \
         patch("json.loads") as mock_json_loads:
        
        # Configure mocks for errors
        mock_run.side_effect = [
            # lsblk call with invalid JSON
            {
                "success": True,
                "stdout": "invalid json",
                "stderr": "",
                "returncode": 0
            },
            # df call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            },
            # fdisk call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            }
        ]
        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        # Call the function
        result = get_storage_info()
        
        # Verify results
        assert "lsblk_raw" in result
        assert "df" not in result
        assert "fdisk" not in result


def test_get_pci_devices():
    """Test PCI device information gathering."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks
        mock_run.side_effect = [
            # lspci -v call
            {
                "success": True,
                "stdout": "00:00.0 Host bridge: Intel Corporation\n00:01.0 VGA compatible controller: NVIDIA",
                "stderr": "",
                "returncode": 0
            },
            # lspci -n call
            {
                "success": True,
                "stdout": "00:00.0 0600: 8086:9b61\n00:01.0 0300: 10de:2520",
                "stderr": "",
                "returncode": 0
            }
        ]
        
        # Call the function
        result = get_pci_devices()
        
        # Verify results
        assert "lspci_verbose" in result
        assert "NVIDIA" in result["lspci_verbose"]
        assert "lspci_numeric" in result
        assert "8086:9b61" in result["lspci_numeric"]


def test_get_pci_devices_with_errors():
    """Test PCI device information gathering with errors."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks for errors
        mock_run.side_effect = [
            # lspci -v call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            },
            # lspci -n call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            }
        ]
        
        # Call the function
        result = get_pci_devices()
        
        # Verify results
        assert "lspci_verbose" not in result
        assert "lspci_numeric" not in result


def test_get_usb_devices():
    """Test USB device information gathering."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks
        mock_run.side_effect = [
            # lsusb -v call
            {
                "success": True,
                "stdout": "Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub",
                "stderr": "",
                "returncode": 0
            },
            # lsusb -t call
            {
                "success": True,
                "stdout": "/:  Bus 01.Port 1: Dev 1, Class=root_hub, Driver=xhci_hcd",
                "stderr": "",
                "returncode": 0
            }
        ]
        
        # Call the function
        result = get_usb_devices()
        
        # Verify results
        assert "lsusb_verbose" in result
        assert "Linux Foundation" in result["lsusb_verbose"]
        assert "lsusb_tree" in result
        assert "root_hub" in result["lsusb_tree"]


def test_get_usb_devices_with_errors():
    """Test USB device information gathering with errors."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks for errors
        mock_run.side_effect = [
            # lsusb -v call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            },
            # lsusb -t call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            }
        ]
        
        # Call the function
        result = get_usb_devices()
        
        # Verify results
        assert "lsusb_verbose" not in result
        assert "lsusb_tree" not in result


def test_get_network_info():
    """Test network information gathering."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks
        mock_run.side_effect = [
            # ip addr show call
            {
                "success": True,
                "stdout": "1: lo: <LOOPBACK,UP> mtu 65536\n2: eth0: <BROADCAST,MULTICAST,UP> mtu 1500",
                "stderr": "",
                "returncode": 0
            },
            # lshw -class network call
            {
                "success": True,
                "stdout": "  *-network\n       description: Ethernet interface\n       product: RTL8111/8168/8411",
                "stderr": "",
                "returncode": 0
            }
        ]
        
        # Call the function
        result = get_network_info()
        
        # Verify results
        assert "ip_addr" in result
        assert "eth0" in result["ip_addr"]
        assert "lshw_network" in result
        assert "Ethernet interface" in result["lshw_network"]


def test_get_network_info_with_errors():
    """Test network information gathering with errors."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks for errors
        mock_run.side_effect = [
            # ip addr show call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            },
            # lshw -class network call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            }
        ]
        
        # Call the function
        result = get_network_info()
        
        # Verify results
        assert "ip_addr" not in result
        assert "lshw_network" not in result


def test_get_graphics_info():
    """Test graphics information gathering."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks
        mock_run.side_effect = [
            # lshw -class display call
            {
                "success": True,
                "stdout": "  *-display\n       description: VGA compatible controller\n       product: NVIDIA GeForce RTX 3080",
                "stderr": "",
                "returncode": 0
            },
            # nvidia-smi -q call
            {
                "success": True,
                "stdout": "==============NVSMI LOG==============\nGPU 0: NVIDIA GeForce RTX 3080\nDriver Version: 470.82.01",
                "stderr": "",
                "returncode": 0
            }
        ]
        
        # Call the function
        result = get_graphics_info()
        
        # Verify results
        assert "lshw_display" in result
        assert "NVIDIA GeForce RTX 3080" in result["lshw_display"]
        assert "nvidia_smi" in result
        assert "Driver Version" in result["nvidia_smi"]


def test_get_graphics_info_with_errors():
    """Test graphics information gathering with errors."""
    # Set up mocks
    with patch("infenix.server.run_command") as mock_run:
        # Configure mocks for errors
        mock_run.side_effect = [
            # lshw -class display call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            },
            # nvidia-smi -q call with error
            {
                "success": False,
                "error": "Command failed",
                "stdout": "",
                "stderr": "Error",
                "returncode": 1
            }
        ]
        
        # Call the function
        result = get_graphics_info()
        
        # Verify results
        assert "lshw_display" not in result
        assert "nvidia_smi" not in result


def test_get_all_hardware_info():
    """Test comprehensive hardware information gathering."""
    # Set up mocks for all hardware functions
    with patch("infenix.server.get_cpu_info") as mock_cpu, \
         patch("infenix.server.get_memory_info") as mock_memory, \
         patch("infenix.server.get_storage_info") as mock_storage, \
         patch("infenix.server.get_pci_devices") as mock_pci, \
         patch("infenix.server.get_usb_devices") as mock_usb, \
         patch("infenix.server.get_network_info") as mock_network, \
         patch("infenix.server.get_graphics_info") as mock_graphics:
        
        # Configure mocks
        mock_cpu.return_value = {"cpu_test": "data"}
        mock_memory.return_value = {"memory_test": "data"}
        mock_storage.return_value = {"storage_test": "data"}
        mock_pci.return_value = {"pci_test": "data"}
        mock_usb.return_value = {"usb_test": "data"}
        mock_network.return_value = {"network_test": "data"}
        mock_graphics.return_value = {"graphics_test": "data"}
        
        # Call the function
        result = get_all_hardware_info()
        
        # Verify results
        assert "cpu" in result
        assert result["cpu"] == {"cpu_test": "data"}
        assert "memory" in result
        assert result["memory"] == {"memory_test": "data"}
        assert "storage" in result
        assert result["storage"] == {"storage_test": "data"}
        assert "pci_devices" in result
        assert result["pci_devices"] == {"pci_test": "data"}
        assert "usb_devices" in result
        assert result["usb_devices"] == {"usb_test": "data"}
        assert "network" in result
        assert result["network"] == {"network_test": "data"}
        assert "graphics" in result
        assert result["graphics"] == {"graphics_test": "data"}


def test_create_tool_result_success():
    """Test creating a successful tool result."""
    data = {"test": "data"}
    result = create_tool_result(data)
    
    assert result.content[0].type == "text"
    assert json.loads(result.content[0].text) == data
    assert not hasattr(result, "isError") or not result.isError


def test_create_tool_result_error():
    """Test creating an error tool result."""
    result = create_tool_result({}, "Test error")
    
    assert result.content[0].type == "text"
    assert result.content[0].text == "Test error"
    assert result.isError is True


@pytest.mark.asyncio
async def test_handle_list_tools():
    """Test listing available tools."""
    result = await handle_list_tools()
    
    assert hasattr(result, "tools")
    assert len(result.tools) == 8
    
    # Check that all expected tools are present
    tool_names = [tool.name for tool in result.tools]
    assert "get_all_hardware" in tool_names
    assert "get_cpu_info" in tool_names
    assert "get_memory_info" in tool_names
    assert "get_storage_info" in tool_names
    assert "get_pci_devices" in tool_names
    assert "get_usb_devices" in tool_names
    assert "get_network_info" in tool_names
    assert "get_graphics_info" in tool_names


@pytest.mark.asyncio
async def test_handle_call_tool_success():
    """Test successful tool call handling."""
    # Create a mock request
    request = CallToolRequest(method="tools/call", params={"name": "get_cpu_info", "arguments": {}})
    
    # Mock the get_cpu_info function
    with patch("infenix.server.get_cpu_info") as mock_get_cpu:
        mock_get_cpu.return_value = {"test": "cpu_data"}
        
        # Call the handler
        result = await handle_call_tool(request)
        
        # Verify results
        assert result.content[0].type == "text"
        assert json.loads(result.content[0].text) == {"test": "cpu_data"}
        assert not hasattr(result, "isError") or not result.isError


@pytest.mark.asyncio
async def test_handle_call_tool_unknown():
    """Test handling of unknown tool calls."""
    # Create a mock request with unknown tool
    request = CallToolRequest(name="unknown_tool", parameters={})
    
    # Call the handler
    result = await handle_call_tool(request)
    
    # Verify results
    assert result.content[0].type == "text"
    assert "Unknown tool" in result.content[0].text
    assert result.isError is True


@pytest.mark.asyncio
async def test_handle_call_tool_exception():
    """Test exception handling in tool calls."""
    # Create a mock request
    request = CallToolRequest(name="get_cpu_info", parameters={})
    
    # Mock the get_cpu_info function to raise an exception
    with patch("infenix.server.get_cpu_info") as mock_get_cpu:
        mock_get_cpu.side_effect = Exception("Test error")
        
        # Call the handler
        result = await handle_call_tool(request)
        
        # Verify results
        assert result.content[0].type == "text"
        assert "Error getting get_cpu_info information" in result.content[0].text
        assert "Test error" in result.content[0].text
        assert result.isError is True


@pytest.mark.asyncio
async def test_main():
    """Test the main entry point."""
    # Mock the stdio_server context manager
    mock_read_stream = MagicMock()
    mock_write_stream = MagicMock()
    mock_stdio_server = MagicMock()
    mock_stdio_server.return_value.__aenter__.return_value = (mock_read_stream, mock_write_stream)
    
    # Mock the server.run method
    mock_run = MagicMock()
    
    with patch("mcp.server.stdio.stdio_server", mock_stdio_server), \
         patch.object(server, "run", mock_run):
        
        # Call the main function
        await main()
        
        # Verify that server.run was called with the correct arguments
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == mock_read_stream
        assert mock_run.call_args[0][1] == mock_write_stream
        assert mock_run.call_args[0][2].server_name == "infenix"
        assert mock_run.call_args[0][2].server_version == "0.1.0"