#!/usr/bin/env python3
"""Query Processing Module for Natural Language Queries.

This module provides advanced natural language query interpretation and routing
capabilities for system diagnostics and analysis.

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
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface
from .query_components import (
    QueryNormalizer, 
    IntentClassifier, 
    EntityExtractor, 
    DefaultToolRouter
)
from .exceptions import InvalidQueryError, QueryProcessingError


class QueryIntent(Enum):
    """Query intent classification constants."""
    HARDWARE_INFO = 'hardware_info'
    HARDWARE_DIAGNOSTIC = 'hardware_diagnostic'
    KERNEL_INFO = 'kernel_info'
    KERNEL_CONFIG = 'kernel_config'
    LOG_ANALYSIS = 'log_analysis'
    PERFORMANCE_ANALYSIS = 'performance_analysis'
    SYSTEM_DIAGNOSTIC = 'system_diagnostic'
    TROUBLESHOOTING = 'troubleshooting'
    OPTIMIZATION = 'optimization'
    GENERAL = 'general'


class QueryProcessor:
    """Advanced natural language query interpreter and router."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize query processor.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        
        # Initialize components using dependency injection
        self.normalizer = QueryNormalizer()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.tool_router = DefaultToolRouter()
    
    def interpret_query(self, query: str) -> Dict[str, Any]:
        """Interpret natural language queries about the system.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary containing query interpretation results
            
        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If processing pipeline fails
        """
        if not query or not query.strip():
            raise InvalidQueryError("Query cannot be empty", query)
        
        if len(query) > 1000:  # Reasonable limit
            raise InvalidQueryError("Query too long (max 1000 characters)", query)
        
        try:
            # Process query through pipeline
            normalized_query = self.normalizer.normalize(query)
            intent, confidence = self.intent_classifier.classify(normalized_query)
            entities = self.entity_extractor.extract(normalized_query, intent)
            parameters = self._extract_parameters(normalized_query, intent, entities)
            tool_routing = self.tool_router.route(intent, parameters)
            response_template = self._generate_response_template(intent, parameters)
            
            return {
                "original_query": query,
                "normalized_query": normalized_query,
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "parameters": parameters,
                "tool_routing": tool_routing,
                "response_template": response_template,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise QueryProcessingError(f"Failed to process query: {e}", query) from e
    
    def route_to_tools(self, interpretation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Route interpreted query to appropriate diagnostic tools.
        
        Args:
            interpretation: Query interpretation result
            
        Returns:
            List of tool execution plans
        """
        intent = interpretation.get('intent', QueryIntent.GENERAL.value)
        parameters = interpretation.get('parameters', {})
        
        return self.tool_router.route(intent, parameters)
    
    def _extract_parameters(self, query: str, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional parameters from query.
        
        Args:
            query: Normalized query string
            intent: Classified intent
            entities: Extracted entities
            
        Returns:
            Dictionary of extracted parameters
        """
        parameters = entities.copy()
        
        # Extract numeric values
        numbers = re.findall(r'\b\d+\b', query)
        if numbers:
            parameters['numbers'] = [int(n) for n in numbers]
        
        # Extract file paths
        file_paths = re.findall(r'/[^\s]+', query)
        if file_paths:
            parameters['file_paths'] = file_paths
        
        # Extract device names
        devices = re.findall(r'/dev/[a-zA-Z0-9]+', query)
        if devices:
            parameters['devices'] = devices
        
        # Extract process names
        if 'process' in query or 'service' in query:
            process_matches = re.findall(r'["\']([^"\']+)["\']', query)
            if process_matches:
                parameters['processes'] = process_matches
        
        # Set default values based on intent
        self._set_default_parameters(parameters, intent)
        
        return parameters
    
    def _set_default_parameters(self, parameters: Dict[str, Any], intent: str) -> None:
        """Set default parameter values based on intent.
        
        Args:
            parameters: Parameters dictionary to modify
            intent: Query intent
        """
        if intent == QueryIntent.LOG_ANALYSIS.value and 'timeframe' not in parameters:
            parameters['timeframe'] = 'recent'
        
        if intent in [QueryIntent.HARDWARE_DIAGNOSTIC.value, QueryIntent.SYSTEM_DIAGNOSTIC.value] and 'component' not in parameters:
            parameters['component'] = 'all'
    
    def _generate_response_template(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Generate response template based on intent and parameters.
        
        Args:
            intent: Query intent
            parameters: Extracted parameters
            
        Returns:
            Formatted response template string
        """
        templates = {
            QueryIntent.HARDWARE_INFO.value: "Gathering {component} hardware information...",
            QueryIntent.HARDWARE_DIAGNOSTIC.value: "Running {component} hardware diagnostics...",
            QueryIntent.KERNEL_INFO.value: "Retrieving kernel information...",
            QueryIntent.KERNEL_CONFIG.value: "Analyzing kernel configuration...",
            QueryIntent.LOG_ANALYSIS.value: "Analyzing {timeframe} system logs...",
            QueryIntent.PERFORMANCE_ANALYSIS.value: "Analyzing {component} performance metrics...",
            QueryIntent.SYSTEM_DIAGNOSTIC.value: "Running comprehensive system diagnostics...",
            QueryIntent.TROUBLESHOOTING.value: "Troubleshooting {component} issues...",
            QueryIntent.OPTIMIZATION.value: "Generating optimization recommendations for {component}...",
            QueryIntent.GENERAL.value: "Analyzing system..."
        }
        
        template = templates.get(intent, templates[QueryIntent.GENERAL.value])
        
        # Format template with parameters
        format_params = {
            'component': parameters.get('component', 'system'),
            'timeframe': parameters.get('timeframe', 'recent'),
            'severity': parameters.get('severity', 'all')
        }
        
        try:
            return template.format(**format_params)
        except KeyError:
            return template