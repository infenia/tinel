#!/usr/bin/env python3
"""Infenix Server.

This MCP server provides tools to gather detailed hardware information
from the Linux kernel using various system interfaces like /proc, /sys,
lscpu, lspci, lsusb, and other Linux utilities.

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

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from .system import LinuxSystemInterface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    TextContent,
    Tool,
)

# Initialize the MCP server
server = Server("infenix")





# Initialize system interface and hardware analyzer
system = LinuxSystemInterface()
device_analyzer = DeviceAnalyzer(system)


# Import tool providers
from .tools.hardware_tools import (
    AllHardwareToolProvider,
    CPUInfoToolProvider,
    MemoryInfoToolProvider,
    StorageInfoToolProvider,
    PCIDevicesToolProvider,
    USBDevicesToolProvider,
    NetworkInfoToolProvider,
    GraphicsInfoToolProvider,
)
from .tools.kernel_tools import (
    KernelInfoToolProvider,
    KernelConfigToolProvider,
    KernelConfigAnalysisToolProvider,
    KernelModulesToolProvider,
    KernelParametersToolProvider,
)

# Initialize tool providers
tool_providers = [
    AllHardwareToolProvider(system),
    CPUInfoToolProvider(system),
    MemoryInfoToolProvider(system),
    StorageInfoToolProvider(system),
    PCIDevicesToolProvider(system),
    USBDevicesToolProvider(system),
    NetworkInfoToolProvider(system),
    GraphicsInfoToolProvider(system),
    KernelInfoToolProvider(system),
    KernelConfigToolProvider(system),
    KernelConfigAnalysisToolProvider(system),
    KernelModulesToolProvider(system),
    KernelParametersToolProvider(system),
]

# Create tool mapping for easy lookup
tool_map = {provider.get_tool_name(): provider for provider in tool_providers}


def create_tool_result(data: Dict[str, Any], error_msg: str = "") -> CallToolResult:
    """Create a tool result with proper formatting.
    
    Args:
        data: Data to include in the result
        error_msg: Optional error message
        
    Returns:
        Formatted CallToolResult
    """
    if error_msg:
        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True
        )
    
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(data, indent=2))]
    )


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available hardware information tools."""
    tools = []
    for provider in tool_providers:
        tools.append(Tool(
            name=provider.get_tool_name(),
            description=provider.get_tool_description(),
            inputSchema=provider.get_input_schema()
        ))
    
    return ListToolsResult(tools=tools)


@server.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls for hardware information."""
    provider = tool_map.get(request.name)
    if not provider:
        logger.warning(f"Unknown tool requested: {request.name}")
        return create_tool_result({}, f"Unknown tool: {request.name}")
    
    try:
        logger.info(f"Executing tool: {request.name}")
        # Extract parameters from request arguments if present
        parameters = request.arguments if hasattr(request, 'arguments') and request.arguments else {}
        result = provider.execute(parameters)
        logger.info(f"Successfully executed tool: {request.name}")
        return create_tool_result(result)
    except Exception as e:
        logger.error(f"Error executing {request.name}: {str(e)}", exc_info=True)
        return create_tool_result({}, f"Error executing {request.name}: {str(e)}")


async def main() -> None:
    """Main entry point for the MCP server."""
    # Import here to avoid issues with event loop
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="infenix",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())