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
from typing import Any, Dict, List, Optional, Tuple

from ..interfaces import SystemInterface
from ..system import LinuxSystemInterface
from .query_components import (
    QueryNormalizer, 
    IntentClassifier, 
    EntityExtractor, 
    DefaultToolRouter
)


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
        
        # Initialize components
        self.normalizer = QueryNormalizer()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.tool_router = DefaultToolRouter()
        
        self.query_patterns = self._load_query_patterns()
    
    def interpret_query(self, query: str) -> Dict[str, Any]:
        """Interpret natural language queries about the system.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary containing query interpretation results
        """
        # Normalize query
        normalized_query = self.normalizer.normalize(query)
        
        # Extract intent and confidence
        intent, confidence = self.intent_classifier.classify(normalized_query)
        
        # Extract entities and parameters
        entities = self.entity_extractor.extract(normalized_query, intent)
        parameters = self._extract_parameters(normalized_query, intent, entities)
        
        # Generate tool routing information
        tool_routing = self.tool_router.route(intent, parameters)
        
        # Generate response template
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
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query text for processing."""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle common contractions
        contractions = {
            "what's": "what is",
            "how's": "how is",
            "where's": "where is",
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "isn't": "is not",
            "aren't": "are not"
        }
        
        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)
        
        return normalized
    
    def _classify_intent(self, query: str) -> Tuple[str, float]:
        """Classify query intent with confidence score.
        
        Args:
            query: Normalized query string
            
        Returns:
            Tuple of (intent, confidence_score)
        """
        intent_scores = {}
        
        # Score each intent based on keyword matches
        for intent, classifier in self.intent_classifiers.items():
            score = self._calculate_intent_score(query, classifier)
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return QueryIntent.GENERAL, 0.5
        
        # Return intent with highest score
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[best_intent], 1.0)
        
        return best_intent, confidence
    
    def _calculate_intent_score(self, query: str, classifier: Dict[str, Any]) -> float:
        """Calculate intent score based on classifier rules."""
        score = 0.0
        word_count = len(query.split())
        
        # Primary keywords (higher weight)
        primary_keywords = classifier.get('primary_keywords', [])
        primary_matches = 0
        for keyword in primary_keywords:
            if keyword in query:
                score += classifier.get('primary_weight', 1.0)
                primary_matches += 1
        
        # Secondary keywords (lower weight)
        secondary_keywords = classifier.get('secondary_keywords', [])
        secondary_matches = 0
        for keyword in secondary_keywords:
            if keyword in query:
                score += classifier.get('secondary_weight', 0.5)
                secondary_matches += 1
        
        # Pattern matching
        patterns = classifier.get('patterns', [])
        pattern_matches = 0
        for pattern in patterns:
            if re.search(pattern, query):
                score += classifier.get('pattern_weight', 0.8)
                pattern_matches += 1
        
        # Context modifiers
        context_modifiers = classifier.get('context_modifiers', {})
        for modifier, weight in context_modifiers.items():
            if modifier in query:
                score *= weight
        
        # Normalize score based on query length and match density
        if word_count > 0:
            match_density = (primary_matches + secondary_matches + pattern_matches) / word_count
            score = score * (0.5 + 0.5 * match_density)
        
        # Cap the maximum score
        return min(score, 2.0)
    
    def _extract_entities(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract entities from query based on intent."""
        entities = {}
        
        # Use intent-specific entity extractors
        if intent in self.entity_extractors:
            extractor = self.entity_extractors[intent]
            
            # Extract components
            components = extractor.get('components', {})
            for component, patterns in components.items():
                for pattern in patterns:
                    if re.search(pattern, query):
                        entities['component'] = component
                        break
                if 'component' in entities:
                    break
            
            # Extract timeframes
            timeframes = extractor.get('timeframes', {})
            for timeframe, patterns in timeframes.items():
                for pattern in patterns:
                    if re.search(pattern, query):
                        entities['timeframe'] = timeframe
                        break
                if 'timeframe' in entities:
                    break
            
            # Extract severity levels
            severities = extractor.get('severities', {})
            for severity, patterns in severities.items():
                for pattern in patterns:
                    if re.search(pattern, query):
                        entities['severity'] = severity
                        break
                if 'severity' in entities:
                    break
            
            # Extract actions
            actions = extractor.get('actions', {})
            for action, patterns in actions.items():
                for pattern in patterns:
                    if re.search(pattern, query):
                        entities['action'] = action
                        break
                if 'action' in entities:
                    break
        
        return entities
    
    def _extract_parameters(self, query: str, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional parameters from query."""
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
            # Look for quoted process names or common process patterns
            process_matches = re.findall(r'["\']([^"\']+)["\']', query)
            if process_matches:
                parameters['processes'] = process_matches
        
        # Set default values based on intent
        if intent == QueryIntent.LOG_ANALYSIS and 'timeframe' not in parameters:
            parameters['timeframe'] = 'recent'
        
        if intent in [QueryIntent.HARDWARE_DIAGNOSTIC, QueryIntent.SYSTEM_DIAGNOSTIC] and 'component' not in parameters:
            parameters['component'] = 'all'
        
        return parameters
    
    def _generate_tool_routing(self, intent: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tool routing information based on intent and parameters."""
        routing = {
            'primary_tools': [],
            'secondary_tools': [],
            'execution_order': 'parallel'
        }
        
        # Map intents to tools
        tool_mapping = {
            QueryIntent.HARDWARE_INFO: ['get_hardware_info', 'get_cpu_info', 'get_memory_info'],
            QueryIntent.HARDWARE_DIAGNOSTIC: ['run_hardware_diagnostics', 'check_hardware_health'],
            QueryIntent.KERNEL_INFO: ['get_kernel_info', 'get_kernel_version'],
            QueryIntent.KERNEL_CONFIG: ['analyze_kernel_config', 'get_kernel_recommendations'],
            QueryIntent.LOG_ANALYSIS: ['analyze_logs', 'get_log_summary'],
            QueryIntent.PERFORMANCE_ANALYSIS: ['analyze_performance', 'get_performance_metrics'],
            QueryIntent.SYSTEM_DIAGNOSTIC: ['diagnose_system', 'run_comprehensive_diagnostics'],
            QueryIntent.TROUBLESHOOTING: ['diagnose_system', 'analyze_logs', 'run_hardware_diagnostics'],
            QueryIntent.OPTIMIZATION: ['get_optimization_recommendations', 'analyze_kernel_config']
        }
        
        if intent in tool_mapping:
            routing['primary_tools'] = tool_mapping[intent]
        
        # Add component-specific tools
        component = parameters.get('component')
        if component:
            component_tools = {
                'cpu': ['get_cpu_info', 'check_cpu_temperature', 'analyze_cpu_performance'],
                'memory': ['get_memory_info', 'check_memory_usage', 'analyze_memory_performance'],
                'storage': ['get_storage_info', 'check_disk_usage', 'analyze_storage_performance'],
                'network': ['get_network_info', 'check_network_status', 'analyze_network_performance']
            }
            
            if component in component_tools:
                routing['secondary_tools'].extend(component_tools[component])
        
        # Set execution order based on intent
        if intent in [QueryIntent.TROUBLESHOOTING, QueryIntent.SYSTEM_DIAGNOSTIC]:
            routing['execution_order'] = 'sequential'
        
        return routing
    
    def _generate_response_template(self, intent: str, parameters: Dict[str, Any]) -> str:
        """Generate response template based on intent and parameters."""
        templates = {
            QueryIntent.HARDWARE_INFO: "Gathering {component} hardware information...",
            QueryIntent.HARDWARE_DIAGNOSTIC: "Running {component} hardware diagnostics...",
            QueryIntent.KERNEL_INFO: "Retrieving kernel information...",
            QueryIntent.KERNEL_CONFIG: "Analyzing kernel configuration...",
            QueryIntent.LOG_ANALYSIS: "Analyzing {timeframe} system logs...",
            QueryIntent.PERFORMANCE_ANALYSIS: "Analyzing {component} performance metrics...",
            QueryIntent.SYSTEM_DIAGNOSTIC: "Running comprehensive system diagnostics...",
            QueryIntent.TROUBLESHOOTING: "Troubleshooting {component} issues...",
            QueryIntent.OPTIMIZATION: "Generating optimization recommendations for {component}...",
            QueryIntent.GENERAL: "Analyzing system..."
        }
        
        template = templates.get(intent, templates[QueryIntent.GENERAL])
        
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
    
    def _build_intent_classifiers(self) -> Dict[str, Dict[str, Any]]:
        """Build intent classification rules."""
        return {
            QueryIntent.HARDWARE_INFO: {
                'primary_keywords': ['hardware', 'info', 'information', 'details', 'specs', 'specifications'],
                'secondary_keywords': ['cpu', 'processor', 'memory', 'ram', 'disk', 'storage', 'gpu', 'graphics'],
                'patterns': [r'what.*hardware', r'show.*hardware', r'get.*info', r'what.*cpu', r'what.*memory'],
                'primary_weight': 1.0,
                'secondary_weight': 0.7,
                'pattern_weight': 0.9
            },
            QueryIntent.HARDWARE_DIAGNOSTIC: {
                'primary_keywords': ['diagnose', 'diagnostic', 'test', 'health'],
                'secondary_keywords': ['hardware', 'cpu', 'memory', 'disk', 'temperature', 'check'],
                'patterns': [r'check.*hardware', r'test.*hardware', r'diagnose.*hardware', r'check.*temperature'],
                'primary_weight': 1.0,
                'secondary_weight': 0.6,
                'pattern_weight': 0.9
            },
            QueryIntent.KERNEL_INFO: {
                'primary_keywords': ['kernel', 'version'],
                'secondary_keywords': ['info', 'information', 'details'],
                'patterns': [r'kernel.*version', r'what.*kernel'],
                'primary_weight': 1.0,
                'secondary_weight': 0.5,
                'pattern_weight': 0.8
            },
            QueryIntent.KERNEL_CONFIG: {
                'primary_keywords': ['kernel', 'config', 'configuration', 'module'],
                'secondary_keywords': ['analyze', 'check', 'show'],
                'patterns': [r'kernel.*config', r'analyze.*kernel', r'kernel.*module', r'show.*kernel'],
                'primary_weight': 1.2,
                'secondary_weight': 0.6,
                'pattern_weight': 0.9
            },
            QueryIntent.LOG_ANALYSIS: {
                'primary_keywords': ['log', 'logs', 'error', 'warning', 'issue'],
                'secondary_keywords': ['analyze', 'check', 'show', 'recent'],
                'patterns': [r'show.*log', r'analyze.*log', r'check.*error'],
                'primary_weight': 1.0,
                'secondary_weight': 0.5,
                'pattern_weight': 0.8
            },
            QueryIntent.PERFORMANCE_ANALYSIS: {
                'primary_keywords': ['performance', 'slow', 'fast', 'speed', 'benchmark'],
                'secondary_keywords': ['analyze', 'check', 'metrics'],
                'patterns': [r'why.*slow', r'performance.*issue', r'speed.*up', r'analyze.*performance'],
                'primary_weight': 1.0,
                'secondary_weight': 0.6,
                'pattern_weight': 0.9
            },
            QueryIntent.SYSTEM_DIAGNOSTIC: {
                'primary_keywords': ['system', 'diagnose', 'diagnostic', 'health', 'status'],
                'secondary_keywords': ['check', 'analyze', 'overall', 'comprehensive'],
                'patterns': [r'system.*health', r'diagnose.*system', r'system.*status'],
                'primary_weight': 1.0,
                'secondary_weight': 0.6,
                'pattern_weight': 0.9
            },
            QueryIntent.TROUBLESHOOTING: {
                'primary_keywords': ['troubleshoot', 'problem', 'issue', 'fix', 'solve'],
                'secondary_keywords': ['help', 'debug', 'resolve', 'repair'],
                'patterns': [r'fix.*problem', r'solve.*issue', r'troubleshoot.*'],
                'primary_weight': 1.0,
                'secondary_weight': 0.7,
                'pattern_weight': 0.9
            },
            QueryIntent.OPTIMIZATION: {
                'primary_keywords': ['optimize', 'optimization', 'tune', 'enhance'],
                'secondary_keywords': ['better', 'efficiency', 'settings', 'system'],
                'patterns': [r'optimize.*system', r'tune.*system', r'enhance.*system'],
                'primary_weight': 1.5,
                'secondary_weight': 0.7,
                'pattern_weight': 1.0
            }
        }
    
    def _build_entity_extractors(self) -> Dict[str, Dict[str, Any]]:
        """Build entity extraction rules for different intents."""
        return {
            QueryIntent.HARDWARE_INFO: {
                'components': {
                    'cpu': [r'\bcpu\b', r'\bprocessor\b', r'\bcore\b'],
                    'memory': [r'\bmemory\b', r'\bram\b'],
                    'storage': [r'\bdisk\b', r'\bstorage\b', r'\bssd\b', r'\bhdd\b'],
                    'network': [r'\bnetwork\b', r'\bnic\b', r'\bethernet\b', r'\bwifi\b'],
                    'graphics': [r'\bgpu\b', r'\bgraphics\b', r'\bvideo\b']
                },
                'timeframes': {
                    'current': [r'\bcurrent\b', r'\bnow\b'],
                    'recent': [r'\brecent\b', r'\blatest\b']
                }
            },
            QueryIntent.LOG_ANALYSIS: {
                'timeframes': {
                    'hour': [r'\bhour\b', r'\b1h\b', r'last hour'],
                    'day': [r'\bday\b', r'\b24h\b', r'\byesterday\b'],
                    'week': [r'\bweek\b', r'\b7d\b', r'weekly'],
                    'recent': [r'\brecent\b', r'\btoday\b', r'\blast\b']
                },
                'severities': {
                    'critical': [r'\bcritical\b', r'\bfatal\b', r'\bemergency\b'],
                    'high': [r'\bhigh\b', r'\bsevere\b', r'\burgent\b'],
                    'medium': [r'\bwarning\b', r'\bmedium\b'],
                    'low': [r'\binfo\b', r'\blow\b', r'\bnotice\b']
                }
            },
            QueryIntent.TROUBLESHOOTING: {
                'actions': {
                    'diagnose': [r'\bdiagnose\b', r'\bcheck\b'],
                    'fix': [r'\bfix\b', r'\brepair\b', r'\bresolve\b'],
                    'analyze': [r'\banalyze\b', r'\binvestigate\b']
                }
            }
        }
    
    def _load_query_patterns(self) -> Dict[str, Any]:
        """Load additional query patterns from configuration."""
        # This could be expanded to load from external configuration files
        return {
            'common_phrases': {
                'what_is': ['what is', 'what are', 'tell me about'],
                'how_to': ['how to', 'how do i', 'how can i'],
                'show_me': ['show me', 'display', 'list'],
                'check_if': ['check if', 'verify', 'confirm']
            },
            'technical_terms': {
                'cpu_terms': ['processor', 'core', 'thread', 'frequency', 'cache'],
                'memory_terms': ['ram', 'memory', 'swap', 'buffer', 'cache'],
                'storage_terms': ['disk', 'drive', 'partition', 'filesystem', 'mount'],
                'network_terms': ['interface', 'connection', 'bandwidth', 'latency']
            }
        }
    
    # Tool planning methods
    def _plan_hardware_info_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan hardware information gathering tools."""
        tools = []
        component = parameters.get('component', 'all')
        
        if component == 'all' or component == 'cpu':
            tools.append({'tool': 'get_cpu_info', 'priority': 1})
        if component == 'all' or component == 'memory':
            tools.append({'tool': 'get_memory_info', 'priority': 1})
        if component == 'all' or component == 'storage':
            tools.append({'tool': 'get_storage_info', 'priority': 1})
        if component == 'all' or component == 'network':
            tools.append({'tool': 'get_network_info', 'priority': 1})
        if component == 'all' or component == 'graphics':
            tools.append({'tool': 'get_graphics_info', 'priority': 1})
        
        return tools
    
    def _plan_hardware_diagnostic_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan hardware diagnostic tools."""
        return [
            {'tool': 'run_hardware_diagnostics', 'priority': 1, 'parameters': parameters}
        ]
    
    def _plan_kernel_info_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan kernel information tools."""
        return [
            {'tool': 'get_kernel_info', 'priority': 1}
        ]
    
    def _plan_kernel_config_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan kernel configuration tools."""
        return [
            {'tool': 'analyze_kernel_config', 'priority': 1},
            {'tool': 'get_kernel_recommendations', 'priority': 2}
        ]
    
    def _plan_log_analysis_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan log analysis tools."""
        return [
            {'tool': 'analyze_logs', 'priority': 1, 'parameters': parameters},
            {'tool': 'get_log_summary', 'priority': 2}
        ]
    
    def _plan_performance_analysis_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan performance analysis tools."""
        return [
            {'tool': 'analyze_performance', 'priority': 1, 'parameters': parameters},
            {'tool': 'get_performance_metrics', 'priority': 2}
        ]
    
    def _plan_system_diagnostic_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan system diagnostic tools."""
        return [
            {'tool': 'diagnose_system', 'priority': 1},
            {'tool': 'run_comprehensive_diagnostics', 'priority': 2}
        ]
    
    def _plan_troubleshooting_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan troubleshooting tools."""
        return [
            {'tool': 'diagnose_system', 'priority': 1},
            {'tool': 'analyze_logs', 'priority': 2, 'parameters': parameters},
            {'tool': 'run_hardware_diagnostics', 'priority': 3}
        ]
    
    def _plan_optimization_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan optimization tools."""
        return [
            {'tool': 'get_optimization_recommendations', 'priority': 1},
            {'tool': 'analyze_kernel_config', 'priority': 2}
        ]
    
    def _plan_general_tools(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Plan general analysis tools."""
        return [
            {'tool': 'diagnose_system', 'priority': 1}
        ]