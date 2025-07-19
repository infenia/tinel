#!/usr/bin/env python3
"""Diagnostics Engine Module.

This module provides the core diagnostics engine for system analysis,
gathering data from all modules and providing comprehensive diagnostics.

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

from datetime import datetime
from typing import Any, Dict, Optional

from ..interfaces import (
    Diagnostic, DiagnosticsProvider, HardwareInfo, KernelConfig, 
    LogAnalysis, SystemInterface
)
from ..system import LinuxSystemInterface
from ..hardware.device_analyzer import DeviceAnalyzer
from ..kernel.config_analyzer import KernelConfigAnalyzer
from ..kernel.config_parser import KernelConfigParser
from ..logs.log_analyzer import LogAnalyzer
from ..logs.log_parser import LogParser
from .query_processor import QueryProcessor
from .query_processor import QueryProcessor
from .recommendation_generator import RecommendationGenerator
from .hardware_diagnostics import HardwareDiagnostics


class DiagnosticsEngine(DiagnosticsProvider):
    """Core diagnostics engine that orchestrates system analysis."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize the diagnostics engine.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # Initialize analyzers
        self.device_analyzer = DeviceAnalyzer(self.system)
        self.kernel_config_parser = KernelConfigParser(self.system)
        self.kernel_config_analyzer = KernelConfigAnalyzer()
        self.log_parser = LogParser(self.system)
        self.log_analyzer = LogAnalyzer()
        
        # Initialize specialized processors
        self.query_processor = QueryProcessor(self.system)
        self.recommendation_generator = RecommendationGenerator()
        self.hardware_diagnostics = HardwareDiagnostics(self.system)
    
    def diagnose_system(
        self,
        hardware: Optional[HardwareInfo] = None,
        kernel_config: Optional[KernelConfig] = None,
        log_analysis: Optional[LogAnalysis] = None
    ) -> Diagnostic:
        """Provide comprehensive system diagnostics.
        
        Args:
            hardware: Pre-gathered hardware information (optional)
            kernel_config: Pre-parsed kernel configuration (optional)
            log_analysis: Pre-analyzed log data (optional)
            
        Returns:
            Comprehensive system diagnostic
        """
        # Gather hardware information if not provided
        if hardware is None:
            hardware = self._gather_hardware_info()
        
        # Parse kernel configuration if not provided
        if kernel_config is None:
            kernel_config = self._parse_kernel_config()
        
        # Analyze logs if not provided
        if log_analysis is None:
            log_analysis = self._analyze_logs()
        
        # Generate comprehensive recommendations
        temp_diagnostic = Diagnostic(
            hardware=hardware,
            kernel_config=kernel_config,
            log_analysis=log_analysis,
            recommendations={},
            explanation=""
        )
        recommendations = self.recommendation_generator.generate_recommendations(temp_diagnostic)['recommendations']
        
        # Generate human-readable explanation
        explanation = self._generate_explanation(
            hardware, kernel_config, log_analysis, recommendations
        )
        
        return Diagnostic(
            hardware=hardware,
            kernel_config=kernel_config,
            log_analysis=log_analysis,
            recommendations=recommendations,
            explanation=explanation
        )
    
    def interpret_query(self, query: str) -> Dict[str, Any]:
        """Interpret natural language queries about the system.
        
        Args:
            query: Natural language query
            
        Returns:
            Interpreted query with routing information
        """
        return self.query_processor.interpret_query(query)
    
    def generate_recommendations(self, diagnostic: Diagnostic) -> Dict[str, Any]:
        """Generate actionable recommendations based on diagnostics.
        
        Args:
            diagnostic: System diagnostic information
            
        Returns:
            Detailed recommendations with priorities and explanations
        """
        return self.recommendation_generator.generate_recommendations(diagnostic)
    
    def run_hardware_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive hardware diagnostics.
        
        Returns:
            Hardware diagnostic results
        """
        return self.hardware_diagnostics.run_comprehensive_diagnostics()
    
    def _gather_hardware_info(self) -> HardwareInfo:
        """Gather comprehensive hardware information."""
        return self.device_analyzer.get_all_hardware_info()
    
    def _parse_kernel_config(self) -> Optional[KernelConfig]:
        """Parse kernel configuration."""
        try:
            return self.kernel_config_parser.parse_config()
        except Exception:
            return None
    
    def _analyze_logs(self) -> Optional[LogAnalysis]:
        """Analyze system logs."""
        try:
            # Parse recent system logs from various sources
            log_sources = ['journald', 'kern.log', 'syslog']
            all_logs = self.log_parser.parse_logs(log_sources)
            
            # Analyze for patterns and issues
            analysis = self.log_analyzer.analyze_logs(all_logs)
            
            return analysis
        except Exception:
            return None
    
    def _generate_explanation(
        self,
        hardware: HardwareInfo,
        kernel_config: Optional[KernelConfig],
        log_analysis: Optional[LogAnalysis],
        recommendations: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation of the system state."""
        explanation_parts = ["System Diagnostic Summary:", "=" * 30]
        
        # Hardware summary
        if hardware and hasattr(hardware, 'cpu') and hardware.cpu:
            cpu_info = hardware.cpu if isinstance(hardware.cpu, dict) else {}
            cpu_model = cpu_info.get('model', 'Unknown CPU')
            
            memory_info = hardware.memory if isinstance(hardware.memory, dict) else {}
            memory_total = memory_info.get('total_gb', 0)
            explanation_parts.append(f"Hardware: {cpu_model} with {memory_total}GB RAM")
        
        # Kernel configuration summary
        if kernel_config:
            explanation_parts.append(f"Kernel: {kernel_config.version} with {len(kernel_config.options)} configuration options")
        
        # Recommendations summary
        total_recommendations = sum(
            len(recs) if isinstance(recs, list) else 1 
            for recs in recommendations.values() 
            if recs
        )
        if total_recommendations > 0:
            explanation_parts.append(f"Recommendations: {total_recommendations} optimization suggestions available")
        else:
            explanation_parts.append("System appears to be running optimally")
        
        return "\n".join(explanation_parts)