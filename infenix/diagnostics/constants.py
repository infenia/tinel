#!/usr/bin/env python3
"""Constants for diagnostics module.

Copyright 2024 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""

from typing import Dict, Any

# Temperature thresholds (in Celsius)
TEMPERATURE_THRESHOLDS = {
    'CPU': {
        'WARNING': 70,
        'CRITICAL': 80
    },
    'GPU': {
        'WARNING': 75,
        'CRITICAL': 85
    }
}

# Resource usage thresholds (in percentage)
RESOURCE_THRESHOLDS = {
    'MEMORY': {
        'WARNING': 80,
        'CRITICAL': 90
    },
    'DISK': {
        'WARNING': 85,
        'CRITICAL': 95
    },
    'CPU_LOAD': {
        'WARNING': 80,
        'CRITICAL': 95
    }
}

# Log analysis patterns
LOG_PATTERNS = {
    'ERROR_KEYWORDS': [
        'error', 'failed', 'failure', 'panic', 'oops', 'bug',
        'segfault', 'kernel bug', 'call trace'
    ],
    'WARNING_KEYWORDS': [
        'warning', 'warn', 'deprecated', 'timeout'
    ],
    'CRITICAL_KEYWORDS': [
        'critical', 'fatal', 'emergency', 'alert'
    ]
}

# Query classification patterns
QUERY_CLASSIFICATION = {
    'HARDWARE': ['cpu', 'processor', 'memory', 'ram', 'disk', 'storage', 'gpu', 'graphics'],
    'KERNEL': ['kernel', 'config', 'module', 'driver'],
    'LOGS': ['log', 'error', 'warning', 'issue', 'problem'],
    'PERFORMANCE': ['performance', 'slow', 'fast', 'optimize', 'speed'],
    'DIAGNOSTIC': ['diagnose', 'check', 'status', 'health']
}

# Recommendation priorities
PRIORITY_LEVELS = {
    'HIGH': 3,
    'MEDIUM': 2,
    'LOW': 1
}

# System paths
SYSTEM_PATHS = {
    'THERMAL_ZONES': '/sys/class/thermal/',
    'PROC_MEMINFO': '/proc/meminfo',
    'PROC_LOADAVG': '/proc/loadavg',
    'SYS_CLASS_NET': '/sys/class/net/',
    'LOG_PATHS': [
        '/var/log/kern.log',
        '/var/log/syslog',
        '/var/log/messages'
    ]
}

# Default timeframes for log analysis (in hours)
LOG_TIMEFRAMES = {
    'RECENT': 1,
    'HOUR': 1,
    'DAY': 24,
    'WEEK': 168
}

# Diagnostic check intervals (in seconds)
CHECK_INTERVALS = {
    'TEMPERATURE': 30,
    'RESOURCE_USAGE': 60,
    'NETWORK': 120,
    'LOG_ANALYSIS': 300
}

# File size limits for log parsing (in MB)
FILE_SIZE_LIMITS = {
    'MAX_LOG_FILE_SIZE': 100,
    'MAX_CONFIG_FILE_SIZE': 10
}

# Timeout values (in seconds)
TIMEOUTS = {
    'COMMAND_EXECUTION': 30,
    'FILE_READ': 10,
    'NETWORK_CHECK': 15
}

# Query processing intent classifiers
INTENT_CLASSIFIERS = {
    'hardware_info': {
        'primary_keywords': ['hardware', 'cpu', 'processor', 'memory', 'ram', 'disk', 'storage', 'gpu', 'graphics'],
        'secondary_keywords': ['info', 'information', 'details', 'specs', 'specifications'],
        'patterns': [r'what.*hardware', r'show.*hardware', r'get.*info'],
        'primary_weight': 1.0,
        'secondary_weight': 0.5,
        'pattern_weight': 0.8
    },
    'hardware_diagnostic': {
        'primary_keywords': ['diagnose', 'diagnostic', 'test', 'check', 'health'],
        'secondary_keywords': ['hardware', 'cpu', 'memory', 'disk', 'temperature'],
        'patterns': [r'check.*hardware', r'test.*hardware', r'diagnose.*hardware'],
        'primary_weight': 1.0,
        'secondary_weight': 0.6,
        'pattern_weight': 0.9
    },
    'kernel_info': {
        'primary_keywords': ['kernel', 'version'],
        'secondary_keywords': ['info', 'information', 'details'],
        'patterns': [r'kernel.*version', r'what.*kernel'],
        'primary_weight': 1.0,
        'secondary_weight': 0.5,
        'pattern_weight': 0.8
    },
    'kernel_config': {
        'primary_keywords': ['kernel', 'config', 'configuration', 'module'],
        'secondary_keywords': ['analyze', 'check', 'optimize'],
        'patterns': [r'kernel.*config', r'analyze.*kernel', r'kernel.*module'],
        'primary_weight': 1.0,
        'secondary_weight': 0.6,
        'pattern_weight': 0.9
    },
    'log_analysis': {
        'primary_keywords': ['log', 'logs', 'error', 'warning', 'issue'],
        'secondary_keywords': ['analyze', 'check', 'show', 'recent'],
        'patterns': [r'show.*log', r'analyze.*log', r'check.*error'],
        'primary_weight': 1.0,
        'secondary_weight': 0.5,
        'pattern_weight': 0.8
    },
    'performance_analysis': {
        'primary_keywords': ['performance', 'slow', 'fast', 'speed', 'benchmark'],
        'secondary_keywords': ['analyze', 'check', 'optimize', 'improve'],
        'patterns': [r'why.*slow', r'performance.*issue', r'speed.*up'],
        'primary_weight': 1.0,
        'secondary_weight': 0.6,
        'pattern_weight': 0.9
    },
    'system_diagnostic': {
        'primary_keywords': ['system', 'diagnose', 'diagnostic', 'health', 'status'],
        'secondary_keywords': ['check', 'analyze', 'overall', 'comprehensive'],
        'patterns': [r'system.*health', r'diagnose.*system', r'system.*status'],
        'primary_weight': 1.0,
        'secondary_weight': 0.6,
        'pattern_weight': 0.9
    },
    'troubleshooting': {
        'primary_keywords': ['troubleshoot', 'problem', 'issue', 'fix', 'solve'],
        'secondary_keywords': ['help', 'debug', 'resolve', 'repair'],
        'patterns': [r'fix.*problem', r'solve.*issue', r'troubleshoot.*'],
        'primary_weight': 1.0,
        'secondary_weight': 0.7,
        'pattern_weight': 0.9
    },
    'optimization': {
        'primary_keywords': ['optimize', 'optimization', 'improve', 'tune', 'enhance'],
        'secondary_keywords': ['performance', 'speed', 'efficiency', 'better'],
        'patterns': [r'optimize.*system', r'improve.*performance', r'make.*faster'],
        'primary_weight': 1.0,
        'secondary_weight': 0.6,
        'pattern_weight': 0.9
    }
}

# Entity extraction patterns
ENTITY_EXTRACTORS = {
    'hardware_info': {
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
    'log_analysis': {
        'timeframes': {
            'recent': [r'\brecent\b', r'\btoday\b', r'\blast\b'],
            'hour': [r'\bhour\b', r'\b1h\b'],
            'day': [r'\bday\b', r'\b24h\b', r'\byesterday\b'],
            'week': [r'\bweek\b', r'\b7d\b']
        },
        'severities': {
            'critical': [r'\bcritical\b', r'\bfatal\b', r'\bemergency\b'],
            'high': [r'\bhigh\b', r'\bsevere\b', r'\burgent\b'],
            'medium': [r'\bwarning\b', r'\bmedium\b'],
            'low': [r'\binfo\b', r'\blow\b', r'\bnotice\b']
        }
    },
    'troubleshooting': {
        'actions': {
            'diagnose': [r'\bdiagnose\b', r'\bcheck\b'],
            'fix': [r'\bfix\b', r'\brepair\b', r'\bresolve\b'],
            'analyze': [r'\banalyze\b', r'\binvestigate\b']
        }
    }
}