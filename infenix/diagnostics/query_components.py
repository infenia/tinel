#!/usr/bin/env python3
"""Query Processing Components.

Modular components for query processing pipeline.
"""

import re
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Dict, List, Optional, Pattern, Tuple

from .constants import INTENT_CLASSIFIERS, ENTITY_EXTRACTORS


class QueryNormalizer:
    """Handles query text normalization."""
    
    CONTRACTIONS = {
        "what's": "what is",
        "how's": "how is", 
        "where's": "where is",
        "can't": "cannot",
        "won't": "will not",
        "don't": "do not",
        "isn't": "is not",
        "aren't": "are not"
    }
    
    def normalize(self, query: str) -> str:
        """Normalize query text for processing."""
        normalized = query.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        for contraction, expansion in self.CONTRACTIONS.items():
            normalized = normalized.replace(contraction, expansion)
        
        return normalized


class IntentClassifier:
    """Handles intent classification with confidence scoring."""
    
    def __init__(self, classifiers: Optional[Dict[str, Dict[str, Any]]] = None):
        self.classifiers = classifiers or INTENT_CLASSIFIERS
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[Pattern[str]]]:
        """Pre-compile regex patterns for better performance."""
        compiled = {}
        for intent, classifier in self.classifiers.items():
            patterns = classifier.get('patterns', [])
            compiled[intent] = [re.compile(pattern) for pattern in patterns]
        return compiled
    
    @lru_cache(maxsize=128)
    def classify(self, query: str) -> Tuple[str, float]:
        """Classify query intent with confidence score."""
        intent_scores = {}
        
        for intent, classifier in self.classifiers.items():
            score = self._calculate_score(query, classifier, intent)
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return 'general', 0.5
        
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[best_intent], 1.0)
        
        return best_intent, confidence
    
    def _calculate_score(self, query: str, classifier: Dict[str, Any], intent: str) -> float:
        """Calculate intent score based on classifier rules."""
        score = 0.0
        
        # Primary keywords (higher weight)
        for keyword in classifier.get('primary_keywords', []):
            if keyword in query:
                score += classifier.get('primary_weight', 1.0)
        
        # Secondary keywords (lower weight)
        for keyword in classifier.get('secondary_keywords', []):
            if keyword in query:
                score += classifier.get('secondary_weight', 0.5)
        
        # Pattern matching with pre-compiled patterns
        compiled_patterns = self._compiled_patterns.get(intent, [])
        for pattern in compiled_patterns:
            if pattern.search(query):
                score += classifier.get('pattern_weight', 0.8)
        
        return score


class EntityExtractor:
    """Handles entity extraction from queries."""
    
    def __init__(self, extractors: Optional[Dict[str, Dict[str, Any]]] = None):
        self.extractors = extractors or ENTITY_EXTRACTORS
    
    def extract(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract entities from query based on intent."""
        entities = {}
        
        if intent not in self.extractors:
            return entities
        
        extractor = self.extractors[intent]
        
        # Extract different entity types
        for entity_type in ['components', 'timeframes', 'severities', 'actions']:
            if entity_type in extractor:
                entity_value = self._extract_entity_type(query, extractor[entity_type])
                if entity_value:
                    entities[entity_type.rstrip('s')] = entity_value
        
        return entities
    
    def _extract_entity_type(self, query: str, entity_patterns: Dict[str, List[str]]) -> Optional[str]:
        """Extract specific entity type from query."""
        for entity, patterns in entity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return entity
        return None


class ToolRouter(ABC):
    """Abstract base class for tool routing strategies."""
    
    @abstractmethod
    def route(self, intent: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Route query to appropriate tools."""
        pass


class DefaultToolRouter(ToolRouter):
    """Default implementation of tool routing."""
    
    TOOL_MAPPING = {
        'hardware_info': ['get_hardware_info', 'get_cpu_info', 'get_memory_info'],
        'hardware_diagnostic': ['run_hardware_diagnostics', 'check_hardware_health'],
        'kernel_info': ['get_kernel_info', 'get_kernel_version'],
        'kernel_config': ['analyze_kernel_config', 'get_kernel_recommendations'],
        'log_analysis': ['analyze_logs', 'get_log_summary'],
        'performance_analysis': ['analyze_performance', 'get_performance_metrics'],
        'system_diagnostic': ['diagnose_system', 'run_comprehensive_diagnostics'],
        'troubleshooting': ['diagnose_system', 'analyze_logs', 'run_hardware_diagnostics'],
        'optimization': ['get_optimization_recommendations', 'analyze_kernel_config']
    }
    
    def route(self, intent: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Route query to appropriate tools."""
        tools = []
        
        # Get primary tools for intent
        primary_tools = self.TOOL_MAPPING.get(intent, ['diagnose_system'])
        for i, tool in enumerate(primary_tools):
            tools.append({'tool': tool, 'priority': i + 1})
        
        # Add component-specific tools
        component = parameters.get('component')
        if component and component != 'all':
            component_tools = self._get_component_tools(component)
            for tool in component_tools:
                tools.append({'tool': tool, 'priority': len(tools) + 1})
        
        return tools
    
    def _get_component_tools(self, component: str) -> List[str]:
        """Get tools specific to a component."""
        component_mapping = {
            'cpu': ['get_cpu_info', 'check_cpu_temperature'],
            'memory': ['get_memory_info', 'check_memory_usage'],
            'storage': ['get_storage_info', 'check_disk_usage'],
            'network': ['get_network_info', 'check_network_status']
        }
        return component_mapping.get(component, [])