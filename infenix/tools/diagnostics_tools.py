#!/usr/bin/env python3
"""AI Diagnostics Tools for MCP Server.

This module provides MCP tools for AI-powered diagnostics including system
analysis, natural language query processing, and intelligent recommendations.

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
from datetime import datetime

from .base import BaseToolProvider
from ..interfaces import SystemInterface
from ..diagnostics import DiagnosticsEngine, QueryProcessor, RecommendationGenerator, HardwareDiagnostics
from ..system import LinuxSystemInterface


class SystemDiagnosticsToolProvider(BaseToolProvider):
    """Tool provider for comprehensive system diagnostics."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize system diagnostics tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "diagnose_system",
            "Perform comprehensive AI-powered system diagnostics including hardware analysis, kernel configuration review, and log analysis"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.diagnostics_engine = DiagnosticsEngine(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "include_hardware": {
                    "type": "boolean",
                    "description": "Include hardware analysis in diagnostics",
                    "default": True
                },
                "include_kernel": {
                    "type": "boolean",
                    "description": "Include kernel configuration analysis",
                    "default": True
                },
                "include_logs": {
                    "type": "boolean",
                    "description": "Include log analysis in diagnostics",
                    "default": True
                },
                "log_sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific log sources to analyze",
                    "default": ["journald", "kern.log", "syslog"]
                },
                "generate_recommendations": {
                    "type": "boolean",
                    "description": "Generate actionable recommendations",
                    "default": True
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive system diagnostics.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing diagnostic results
        """
        try:
            include_hardware = parameters.get("include_hardware", True)
            include_kernel = parameters.get("include_kernel", True)
            include_logs = parameters.get("include_logs", True)
            log_sources = parameters.get("log_sources", ["journald", "kern.log", "syslog"])
            generate_recommendations = parameters.get("generate_recommendations", True)
            
            # Gather data based on parameters
            hardware_info = None
            kernel_config = None
            log_analysis = None
            
            if include_hardware:
                hardware_info = self.diagnostics_engine._gather_hardware_info()
            
            if include_kernel:
                kernel_config = self.diagnostics_engine._parse_kernel_config()
            
            if include_logs:
                log_analysis = self.diagnostics_engine._analyze_logs()
            
            # Perform comprehensive diagnostics
            diagnostic = self.diagnostics_engine.diagnose_system(
                hardware=hardware_info,
                kernel_config=kernel_config,
                log_analysis=log_analysis
            )
            
            # Serialize the diagnostic result
            result = {
                "success": True,
                "diagnostic_summary": diagnostic.explanation,
                "hardware_analysis": self._serialize_hardware_info(diagnostic.hardware) if diagnostic.hardware else None,
                "kernel_analysis": self._serialize_kernel_config(diagnostic.kernel_config) if diagnostic.kernel_config else None,
                "log_analysis": self._serialize_log_analysis(diagnostic.log_analysis) if diagnostic.log_analysis else None,
                "recommendations": diagnostic.recommendations if generate_recommendations else {},
                "analysis_metadata": {
                    "included_hardware": include_hardware,
                    "included_kernel": include_kernel,
                    "included_logs": include_logs,
                    "log_sources": log_sources if include_logs else [],
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to perform system diagnostics: {str(e)}",
                "diagnostic_summary": "Unable to complete system diagnostics",
                "hardware_analysis": None,
                "kernel_analysis": None,
                "log_analysis": None,
                "recommendations": {},
                "analysis_metadata": {
                    "generated_at": datetime.now().isoformat()
                }
            }
    
    def _serialize_hardware_info(self, hardware_info) -> Dict[str, Any]:
        """Serialize hardware information for JSON output."""
        if not hardware_info:
            return {}
        
        return {
            "cpu": hardware_info.cpu if hasattr(hardware_info, 'cpu') else {},
            "memory": hardware_info.memory if hasattr(hardware_info, 'memory') else {},
            "storage": hardware_info.storage if hasattr(hardware_info, 'storage') else {},
            "network": hardware_info.network if hasattr(hardware_info, 'network') else {},
            "graphics": hardware_info.graphics if hasattr(hardware_info, 'graphics') else {},
            "pci_devices": hardware_info.pci_devices if hasattr(hardware_info, 'pci_devices') else {},
            "usb_devices": hardware_info.usb_devices if hasattr(hardware_info, 'usb_devices') else {}
        }
    
    def _serialize_kernel_config(self, kernel_config) -> Dict[str, Any]:
        """Serialize kernel configuration for JSON output."""
        if not kernel_config:
            return {}
        
        return {
            "version": kernel_config.version if hasattr(kernel_config, 'version') else "Unknown",
            "options_count": len(kernel_config.options) if hasattr(kernel_config, 'options') and kernel_config.options else 0,
            "analysis": kernel_config.analysis if hasattr(kernel_config, 'analysis') else {},
            "recommendations": kernel_config.recommendations if hasattr(kernel_config, 'recommendations') else {}
        }
    
    def _serialize_log_analysis(self, log_analysis) -> Dict[str, Any]:
        """Serialize log analysis for JSON output."""
        if not log_analysis:
            return {}
        
        # Serialize log entries with timestamp conversion
        entries = []
        if hasattr(log_analysis, 'entries') and log_analysis.entries:
            for entry in log_analysis.entries[:50]:  # Limit to 50 entries
                entries.append({
                    "timestamp": entry.timestamp.isoformat() if hasattr(entry, 'timestamp') else None,
                    "facility": entry.facility if hasattr(entry, 'facility') else "unknown",
                    "severity": entry.severity if hasattr(entry, 'severity') else "info",
                    "message": entry.message if hasattr(entry, 'message') else "",
                    "source": entry.source if hasattr(entry, 'source') else "unknown"
                })
        
        return {
            "total_entries": len(log_analysis.entries) if hasattr(log_analysis, 'entries') and log_analysis.entries else 0,
            "sample_entries": entries,
            "patterns": log_analysis.patterns if hasattr(log_analysis, 'patterns') else {},
            "issues": log_analysis.issues if hasattr(log_analysis, 'issues') else {},
            "summary": log_analysis.summary if hasattr(log_analysis, 'summary') else {}
        }


class QueryProcessorToolProvider(BaseToolProvider):
    """Tool provider for natural language query processing."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize query processor tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "process_natural_language_query",
            "Process natural language queries about the system and route them to appropriate diagnostic tools"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.query_processor = QueryProcessor(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query about the system (e.g., 'What is my CPU temperature?', 'Are there any errors in the logs?')"
                },
                "include_tool_routing": {
                    "type": "boolean",
                    "description": "Include tool routing information in the response",
                    "default": True
                },
                "execute_tools": {
                    "type": "boolean",
                    "description": "Automatically execute recommended tools",
                    "default": False
                }
            },
            "required": ["query"]
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute natural language query processing.
        
        Args:
            parameters: Tool parameters containing the query
            
        Returns:
            Dictionary containing query interpretation and routing
        """
        try:
            query = parameters.get("query", "")
            include_tool_routing = parameters.get("include_tool_routing", True)
            execute_tools = parameters.get("execute_tools", False)
            
            if not query.strip():
                return {
                    "success": False,
                    "error": "Query cannot be empty",
                    "interpretation": {},
                    "tool_routing": [],
                    "execution_results": []
                }
            
            # Process the query
            interpretation = self.query_processor.interpret_query(query)
            
            # Generate tool routing if requested
            tool_routing = []
            if include_tool_routing:
                tool_routing = self.query_processor.route_to_tools(interpretation)
            
            # Execute tools if requested (simplified implementation)
            execution_results = []
            if execute_tools and tool_routing:
                execution_results = self._execute_recommended_tools(tool_routing)
            
            return {
                "success": True,
                "interpretation": interpretation,
                "tool_routing": tool_routing if include_tool_routing else [],
                "execution_results": execution_results,
                "response_template": interpretation.get("response_template", "Processing your query..."),
                "confidence": interpretation.get("confidence", 0.5)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process query: {str(e)}",
                "interpretation": {},
                "tool_routing": [],
                "execution_results": []
            }
    
    def _execute_recommended_tools(self, tool_routing: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute recommended tools (simplified implementation).
        
        Args:
            tool_routing: List of tool execution plans
            
        Returns:
            List of execution results
        """
        results = []
        
        for tool_plan in tool_routing[:3]:  # Limit to 3 tools
            tool_name = tool_plan.get('tool', 'unknown')
            try:
                # This is a simplified implementation
                # In a full implementation, you would route to actual tools
                results.append({
                    "tool": tool_name,
                    "status": "simulated",
                    "message": f"Tool {tool_name} would be executed with parameters: {tool_plan.get('parameters', {})}"
                })
            except Exception as e:
                results.append({
                    "tool": tool_name,
                    "status": "error",
                    "error": str(e)
                })
        
        return results


class RecommendationGeneratorToolProvider(BaseToolProvider):
    """Tool provider for generating intelligent recommendations."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize recommendation generator tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "generate_recommendations",
            "Generate intelligent recommendations for system optimization, security, and performance improvements"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.recommendation_generator = RecommendationGenerator(self.system)
        self.diagnostics_engine = DiagnosticsEngine(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "focus_areas": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["hardware", "kernel", "security", "performance", "maintenance", "all"]
                    },
                    "description": "Specific areas to focus recommendations on",
                    "default": ["all"]
                },
                "priority_filter": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low"]
                    },
                    "description": "Filter recommendations by priority levels",
                    "default": ["critical", "high", "medium", "low"]
                },
                "max_recommendations": {
                    "type": "integer",
                    "description": "Maximum number of recommendations to return",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                },
                "include_implementation_guides": {
                    "type": "boolean",
                    "description": "Include step-by-step implementation guides",
                    "default": True
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recommendation generation.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing recommendations
        """
        try:
            focus_areas = parameters.get("focus_areas", ["all"])
            priority_filter = parameters.get("priority_filter", ["critical", "high", "medium", "low"])
            max_recommendations = parameters.get("max_recommendations", 20)
            include_implementation_guides = parameters.get("include_implementation_guides", True)
            
            # Perform system diagnostics to get current state
            diagnostic = self.diagnostics_engine.diagnose_system()
            
            # Generate comprehensive recommendations
            recommendations_result = self.recommendation_generator.generate_recommendations(diagnostic)
            
            # Filter recommendations based on parameters
            filtered_recommendations = self._filter_recommendations(
                recommendations_result,
                focus_areas,
                priority_filter,
                max_recommendations
            )
            
            # Add implementation guides if requested
            if include_implementation_guides and "implementation_guides" not in filtered_recommendations:
                filtered_recommendations["implementation_guides"] = self._generate_implementation_guides(
                    filtered_recommendations.get("prioritized", [])[:5]
                )
            
            return {
                "success": True,
                "recommendations": filtered_recommendations,
                "filter_criteria": {
                    "focus_areas": focus_areas,
                    "priority_filter": priority_filter,
                    "max_recommendations": max_recommendations
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate recommendations: {str(e)}",
                "recommendations": {},
                "filter_criteria": {},
                "generated_at": datetime.now().isoformat()
            }
    
    def _filter_recommendations(
        self,
        recommendations_result: Dict[str, Any],
        focus_areas: List[str],
        priority_filter: List[str],
        max_recommendations: int
    ) -> Dict[str, Any]:
        """Filter recommendations based on criteria."""
        filtered_result = recommendations_result.copy()
        
        # Filter by focus areas
        if "all" not in focus_areas:
            filtered_recommendations = {}
            for area in focus_areas:
                if area in recommendations_result.get("recommendations", {}):
                    filtered_recommendations[area] = recommendations_result["recommendations"][area]
            filtered_result["recommendations"] = filtered_recommendations
        
        # Filter prioritized recommendations by priority
        prioritized = recommendations_result.get("prioritized", [])
        if priority_filter and priority_filter != ["critical", "high", "medium", "low"]:
            prioritized = [
                rec for rec in prioritized 
                if rec.get("priority", "medium") in priority_filter
            ]
        
        # Limit number of recommendations
        if len(prioritized) > max_recommendations:
            prioritized = prioritized[:max_recommendations]
        
        filtered_result["prioritized"] = prioritized
        
        return filtered_result
    
    def _generate_implementation_guides(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate implementation guides for top recommendations."""
        guides = []
        
        for rec in recommendations:
            component = rec.get("component", "system")
            action = rec.get("action", "")
            
            guide = {
                "recommendation": action,
                "component": component,
                "steps": self._get_implementation_steps(component, action),
                "estimated_time": self._estimate_implementation_time(component, action),
                "difficulty": self._assess_difficulty(component, action),
                "prerequisites": self._get_prerequisites(component, action)
            }
            
            guides.append(guide)
        
        return guides
    
    def _get_implementation_steps(self, component: str, action: str) -> List[str]:
        """Get implementation steps for a recommendation."""
        # Simplified implementation - in practice, this would be more sophisticated
        if "temperature" in action.lower():
            return [
                "Check current CPU temperature with sensors",
                "Clean dust from CPU cooler and case fans",
                "Verify thermal paste application",
                "Check fan speeds and replace if necessary",
                "Monitor temperature after changes"
            ]
        elif "memory" in action.lower():
            return [
                "Check current memory usage with free -h",
                "Identify memory-intensive processes",
                "Close unnecessary applications",
                "Consider adding more RAM if consistently high",
                "Monitor memory usage over time"
            ]
        else:
            return [
                "Review the specific recommendation details",
                "Research the recommended changes",
                "Create a backup if making system changes",
                "Implement the changes carefully",
                "Monitor system behavior after changes"
            ]
    
    def _estimate_implementation_time(self, component: str, action: str) -> str:
        """Estimate time required for implementation."""
        if "critical" in action.lower():
            return "15-30 minutes"
        elif "kernel" in component.lower():
            return "1-2 hours"
        elif "hardware" in component.lower():
            return "30-60 minutes"
        else:
            return "15-45 minutes"
    
    def _assess_difficulty(self, component: str, action: str) -> str:
        """Assess difficulty level of implementation."""
        if "kernel" in component.lower():
            return "Advanced"
        elif "hardware" in component.lower():
            return "Intermediate"
        else:
            return "Beginner"
    
    def _get_prerequisites(self, component: str, action: str) -> List[str]:
        """Get prerequisites for implementation."""
        prerequisites = ["Administrative access to the system"]
        
        if "kernel" in component.lower():
            prerequisites.extend([
                "Understanding of kernel configuration",
                "Ability to recompile kernel (if needed)",
                "System backup recommended"
            ])
        elif "hardware" in component.lower():
            prerequisites.extend([
                "Physical access to the system",
                "Basic hardware knowledge",
                "Appropriate tools (screwdrivers, thermal paste, etc.)"
            ])
        
        return prerequisites


class HardwareDiagnosticsToolProvider(BaseToolProvider):
    """Tool provider for specialized hardware diagnostics."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize hardware diagnostics tool provider.
        
        Args:
            system_interface: System interface for command execution
        """
        super().__init__(
            "run_hardware_diagnostics",
            "Run comprehensive hardware diagnostics including temperature monitoring, performance analysis, and health checks"
        )
        self.system = system_interface or LinuxSystemInterface()
        self.hardware_diagnostics = HardwareDiagnostics(self.system)
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "components": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["all", "cpu", "memory", "storage", "network", "graphics"]
                    },
                    "description": "Specific hardware components to diagnose",
                    "default": ["all"]
                },
                "include_temperature": {
                    "type": "boolean",
                    "description": "Include temperature monitoring in diagnostics",
                    "default": True
                },
                "include_performance": {
                    "type": "boolean",
                    "description": "Include performance analysis",
                    "default": True
                },
                "include_health": {
                    "type": "boolean",
                    "description": "Include hardware health checks",
                    "default": True
                }
            },
            "required": []
        }
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hardware diagnostics.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Dictionary containing hardware diagnostic results
        """
        try:
            components = parameters.get("components", ["all"])
            include_temperature = parameters.get("include_temperature", True)
            include_performance = parameters.get("include_performance", True)
            include_health = parameters.get("include_health", True)
            
            # Run comprehensive hardware diagnostics
            diagnostic_results = self.hardware_diagnostics.run_comprehensive_diagnostics()
            
            # Filter results based on requested components
            if "all" not in components:
                filtered_results = {}
                for component in components:
                    if component in diagnostic_results:
                        filtered_results[component] = diagnostic_results[component]
                diagnostic_results = filtered_results
            
            # Filter by diagnostic types
            if not include_temperature:
                self._remove_temperature_data(diagnostic_results)
            if not include_performance:
                self._remove_performance_data(diagnostic_results)
            if not include_health:
                self._remove_health_data(diagnostic_results)
            
            return {
                "success": True,
                "hardware_diagnostics": diagnostic_results,
                "diagnostic_criteria": {
                    "components": components,
                    "include_temperature": include_temperature,
                    "include_performance": include_performance,
                    "include_health": include_health
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run hardware diagnostics: {str(e)}",
                "hardware_diagnostics": {},
                "diagnostic_criteria": {},
                "generated_at": datetime.now().isoformat()
            }
    
    def _remove_temperature_data(self, results: Dict[str, Any]) -> None:
        """Remove temperature data from results."""
        for component_data in results.values():
            if isinstance(component_data, dict):
                component_data.pop('temperature', None)
                component_data.pop('thermal_status', None)
    
    def _remove_performance_data(self, results: Dict[str, Any]) -> None:
        """Remove performance data from results."""
        for component_data in results.values():
            if isinstance(component_data, dict):
                component_data.pop('performance_metrics', None)
                component_data.pop('benchmarks', None)
    
    def _remove_health_data(self, results: Dict[str, Any]) -> None:
        """Remove health data from results."""
        for component_data in results.values():
            if isinstance(component_data, dict):
                component_data.pop('health_status', None)
                component_data.pop('smart_data', None)