#!/usr/bin/env python3
"""Log Analyzer Module.

This module provides comprehensive log analysis capabilities including
summary generation for critical issues and detailed analysis of specific
log entries.

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

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..interfaces import LogAnalysis, LogEntry, SystemInterface
from ..system import LinuxSystemInterface
from .log_parser import LogParser
from .pattern_detector import PatternDetector


class LogAnalyzer:
    """System log analyzer with summary generation capabilities."""
    
    def __init__(self, system_interface: Optional[SystemInterface] = None):
        """Initialize log analyzer.
        
        Args:
            system_interface: System interface for command execution
        """
        self.system = system_interface or LinuxSystemInterface()
        self.parser = LogParser(self.system)
        self.detector = PatternDetector(self.system)
    
    def analyze_logs(self, log_sources: List[str]) -> LogAnalysis:
        """Analyze logs from various sources and generate comprehensive analysis.
        
        Args:
            log_sources: List of log source paths or identifiers
            
        Returns:
            LogAnalysis object containing analysis results
        """
        # Parse logs from sources
        entries = self.parser.parse_logs(log_sources)
        
        # Detect patterns
        hardware_patterns = self.detector.detect_hardware_patterns(entries)
        kernel_patterns = self.detector.detect_kernel_patterns(entries)
        
        # Combine all patterns
        patterns = {
            'hardware': hardware_patterns,
            'kernel': kernel_patterns
        }
        
        # Identify issues
        issues = self._identify_issues(patterns)
        
        # Generate summary
        summary = self._generate_summary(entries, patterns, issues)
        
        return LogAnalysis(
            entries=entries,
            patterns=patterns,
            issues=issues,
            summary=summary
        )
    
    def generate_critical_issues_summary(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Generate summary of critical issues from log entries.
        
        Args:
            entries: List of log entries to analyze
            
        Returns:
            Dictionary containing critical issues summary
        """
        # Detect patterns
        hardware_patterns = self.detector.detect_hardware_patterns(entries)
        kernel_patterns = self.detector.detect_kernel_patterns(entries)
        
        # Extract critical issues
        critical_issues = []
        
        # Add critical hardware issues
        for category, issues in hardware_patterns.items():
            for issue in issues:
                if issue.get('severity') in ['critical', 'high']:
                    critical_issues.append({
                        'category': 'hardware',
                        'subcategory': category,
                        'type': issue['type'],
                        'severity': issue['severity'],
                        'timestamp': issue['timestamp'],
                        'description': issue['description'],
                        'recommendation': issue['recommendation']
                    })
        
        # Add critical kernel issues
        for category, issues in kernel_patterns.items():
            for issue in issues:
                if issue.get('severity') in ['critical', 'high']:
                    critical_issues.append({
                        'category': 'kernel',
                        'subcategory': category,
                        'type': issue['type'],
                        'severity': issue['severity'],
                        'timestamp': issue['timestamp'],
                        'description': issue['description'],
                        'recommendation': issue['recommendation']
                    })
        
        # Sort by severity and timestamp
        critical_issues.sort(key=lambda x: (
            0 if x['severity'] == 'critical' else 1,
            x['timestamp']
        ), reverse=True)
        
        # Generate summary statistics
        summary_stats = self._generate_critical_summary_stats(critical_issues)
        
        return {
            'total_critical_issues': len(critical_issues),
            'issues': critical_issues[:20],  # Limit to top 20 issues
            'statistics': summary_stats,
            'recommendations': self._generate_priority_recommendations(critical_issues)
        }
    
    def analyze_specific_entry(self, entry: LogEntry) -> Dict[str, Any]:
        """Provide detailed analysis of a specific log entry.
        
        Args:
            entry: Log entry to analyze
            
        Returns:
            Dictionary containing detailed analysis
        """
        analysis = {
            'entry': {
                'timestamp': entry.timestamp,
                'facility': entry.facility,
                'severity': entry.severity,
                'message': entry.message,
                'source': entry.source
            },
            'classification': {},
            'context': {},
            'recommendations': []
        }
        
        # Classify the entry
        analysis['classification'] = self._classify_log_entry(entry)
        
        # Provide context
        analysis['context'] = self._provide_entry_context(entry)
        
        # Generate specific recommendations
        analysis['recommendations'] = self._generate_entry_recommendations(entry, analysis['classification'])
        
        return analysis
    
    def _identify_issues(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Identify issues from detected patterns.
        
        Args:
            patterns: Detected patterns
            
        Returns:
            Dictionary containing identified issues
        """
        issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # Process hardware patterns
        for category, category_issues in patterns['hardware'].items():
            for issue in category_issues:
                severity = issue.get('severity', 'medium')
                issues[severity].append(issue)
        
        # Process kernel patterns
        for category, category_issues in patterns['kernel'].items():
            for issue in category_issues:
                severity = issue.get('severity', 'medium')
                issues[severity].append(issue)
        
        return issues
    
    def _generate_summary(self, entries: List[LogEntry], patterns: Dict[str, Any], issues: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary of log analysis.
        
        Args:
            entries: Log entries
            patterns: Detected patterns
            issues: Identified issues
            
        Returns:
            Dictionary containing summary
        """
        summary = {}
        
        # Basic statistics
        summary['statistics'] = self._generate_basic_statistics(entries)
        
        # Issue summary
        summary['issue_summary'] = self._generate_issue_summary(issues)
        
        # Timeline analysis
        summary['timeline'] = self._generate_timeline_analysis(entries, issues)
        
        # Top issues
        summary['top_issues'] = self._generate_top_issues(issues)
        
        # System health assessment
        summary['health_assessment'] = self._generate_health_assessment(issues)
        
        # Recommendations
        summary['recommendations'] = self._generate_summary_recommendations(issues)
        
        return summary
    
    def _generate_basic_statistics(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Generate basic statistics from log entries.
        
        Args:
            entries: Log entries
            
        Returns:
            Dictionary containing basic statistics
        """
        if not entries:
            return {}
        
        # Count entries by severity
        severity_counts = Counter(entry.severity for entry in entries)
        
        # Count entries by facility
        facility_counts = Counter(entry.facility for entry in entries)
        
        # Count entries by source
        source_counts = Counter(entry.source for entry in entries)
        
        # Time range
        timestamps = [entry.timestamp for entry in entries]
        time_range = {
            'start': min(timestamps),
            'end': max(timestamps),
            'duration': (max(timestamps) - min(timestamps)).total_seconds()
        }
        
        return {
            'total_entries': len(entries),
            'severity_distribution': dict(severity_counts),
            'facility_distribution': dict(facility_counts),
            'source_distribution': dict(source_counts.most_common(10)),
            'time_range': time_range
        }
    
    def _generate_issue_summary(self, issues: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of identified issues.
        
        Args:
            issues: Identified issues
            
        Returns:
            Dictionary containing issue summary
        """
        return {
            'total_issues': sum(len(issue_list) for issue_list in issues.values()),
            'by_severity': {
                severity: len(issue_list) 
                for severity, issue_list in issues.items()
            },
            'critical_count': len(issues.get('critical', [])),
            'high_count': len(issues.get('high', [])),
            'medium_count': len(issues.get('medium', [])),
            'low_count': len(issues.get('low', []))
        }
    
    def _generate_timeline_analysis(self, entries: List[LogEntry], issues: Dict[str, Any]) -> Dict[str, Any]:
        """Generate timeline analysis of entries and issues.
        
        Args:
            entries: Log entries
            issues: Identified issues
            
        Returns:
            Dictionary containing timeline analysis
        """
        if not entries:
            return {}
        
        # Group entries by hour
        hourly_counts = defaultdict(int)
        for entry in entries:
            hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] += 1
        
        # Group issues by hour
        hourly_issues = defaultdict(int)
        for severity, issue_list in issues.items():
            for issue in issue_list:
                if 'timestamp' in issue:
                    hour_key = issue['timestamp'].replace(minute=0, second=0, microsecond=0)
                    hourly_issues[hour_key] += 1
        
        # Find peak activity periods
        peak_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'hourly_entry_counts': dict(hourly_counts),
            'hourly_issue_counts': dict(hourly_issues),
            'peak_activity_hours': [
                {'hour': hour.isoformat(), 'count': count}
                for hour, count in peak_hours
            ]
        }
    
    def _generate_top_issues(self, issues: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate list of top issues by severity and frequency.
        
        Args:
            issues: Identified issues
            
        Returns:
            List of top issues
        """
        all_issues = []
        
        # Collect all issues with priority scoring
        for severity, issue_list in issues.items():
            priority_score = {
                'critical': 4,
                'high': 3,
                'medium': 2,
                'low': 1
            }.get(severity, 1)
            
            for issue in issue_list:
                all_issues.append({
                    **issue,
                    'priority_score': priority_score
                })
        
        # Sort by priority score and timestamp
        all_issues.sort(key=lambda x: (x['priority_score'], x.get('timestamp', datetime.min)), reverse=True)
        
        return all_issues[:10]  # Return top 10 issues
    
    def _generate_health_assessment(self, issues: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system health assessment based on issues.
        
        Args:
            issues: Identified issues
            
        Returns:
            Dictionary containing health assessment
        """
        critical_count = len(issues.get('critical', []))
        high_count = len(issues.get('high', []))
        medium_count = len(issues.get('medium', []))
        low_count = len(issues.get('low', []))
        
        total_issues = critical_count + high_count + medium_count + low_count
        
        # Calculate health score (0-100)
        if total_issues == 0:
            health_score = 100
        else:
            # Weight issues by severity
            weighted_issues = (critical_count * 4) + (high_count * 3) + (medium_count * 2) + (low_count * 1)
            max_possible_score = total_issues * 4
            health_score = max(0, 100 - int((weighted_issues / max_possible_score) * 100))
        
        # Determine health status
        if health_score >= 90:
            health_status = 'excellent'
        elif health_score >= 75:
            health_status = 'good'
        elif health_score >= 50:
            health_status = 'fair'
        elif health_score >= 25:
            health_status = 'poor'
        else:
            health_status = 'critical'
        
        return {
            'health_score': health_score,
            'health_status': health_status,
            'total_issues': total_issues,
            'critical_issues': critical_count,
            'high_issues': high_count,
            'assessment': self._get_health_assessment_text(health_status, critical_count, high_count)
        }
    
    def _generate_summary_recommendations(self, issues: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate summary recommendations based on issues.
        
        Args:
            issues: Identified issues
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Priority recommendations for critical issues
        critical_issues = issues.get('critical', [])
        if critical_issues:
            recommendations.append({
                'priority': 'critical',
                'title': 'Address Critical Issues Immediately',
                'description': f'Found {len(critical_issues)} critical issues that require immediate attention',
                'actions': [
                    'Review critical issues in detail',
                    'Take immediate corrective action',
                    'Monitor system stability',
                    'Consider emergency maintenance if necessary'
                ]
            })
        
        # High priority recommendations
        high_issues = issues.get('high', [])
        if high_issues:
            recommendations.append({
                'priority': 'high',
                'title': 'Resolve High Priority Issues',
                'description': f'Found {len(high_issues)} high priority issues that should be addressed soon',
                'actions': [
                    'Schedule maintenance window',
                    'Update drivers and firmware',
                    'Check hardware health',
                    'Review system configuration'
                ]
            })
        
        # General maintenance recommendations
        medium_issues = issues.get('medium', [])
        if medium_issues:
            recommendations.append({
                'priority': 'medium',
                'title': 'Perform Regular Maintenance',
                'description': f'Found {len(medium_issues)} medium priority issues for routine maintenance',
                'actions': [
                    'Schedule regular maintenance',
                    'Update system software',
                    'Review log rotation settings',
                    'Monitor system performance'
                ]
            })
        
        return recommendations
    
    def _generate_critical_summary_stats(self, critical_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics for critical issues summary.
        
        Args:
            critical_issues: List of critical issues
            
        Returns:
            Dictionary containing statistics
        """
        if not critical_issues:
            return {}
        
        # Count by category
        category_counts = Counter(issue['category'] for issue in critical_issues)
        
        # Count by type
        type_counts = Counter(issue['type'] for issue in critical_issues)
        
        # Count by severity
        severity_counts = Counter(issue['severity'] for issue in critical_issues)
        
        # Recent issues (last 24 hours)
        recent_threshold = datetime.now() - timedelta(hours=24)
        recent_issues = [
            issue for issue in critical_issues 
            if issue['timestamp'] > recent_threshold
        ]
        
        return {
            'by_category': dict(category_counts),
            'by_type': dict(type_counts.most_common(10)),
            'by_severity': dict(severity_counts),
            'recent_issues_count': len(recent_issues),
            'oldest_issue': min(issue['timestamp'] for issue in critical_issues),
            'newest_issue': max(issue['timestamp'] for issue in critical_issues)
        }
    
    def _generate_priority_recommendations(self, critical_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate priority recommendations based on critical issues.
        
        Args:
            critical_issues: List of critical issues
            
        Returns:
            List of priority recommendations
        """
        recommendations = []
        
        # Count issue types
        type_counts = Counter(issue['type'] for issue in critical_issues)
        
        # Generate recommendations based on most common issues
        for issue_type, count in type_counts.most_common(5):
            if issue_type == 'kernel_panic':
                recommendations.append(f'Address {count} kernel panic(s) - check hardware and update kernel')
            elif issue_type == 'out_of_memory':
                recommendations.append(f'Resolve {count} out of memory condition(s) - add RAM or optimize memory usage')
            elif issue_type == 'io_error':
                recommendations.append(f'Fix {count} I/O error(s) - check storage devices and run diagnostics')
            elif issue_type == 'machine_check_exception':
                recommendations.append(f'Investigate {count} machine check exception(s) - possible CPU hardware error')
            else:
                recommendations.append(f'Address {count} {issue_type.replace("_", " ")} issue(s)')
        
        return recommendations
    
    def _classify_log_entry(self, entry: LogEntry) -> Dict[str, Any]:
        """Classify a log entry for detailed analysis.
        
        Args:
            entry: Log entry to classify
            
        Returns:
            Dictionary containing classification
        """
        classification = {
            'category': 'general',
            'subcategory': 'unknown',
            'severity_level': entry.severity,
            'urgency': 'low',
            'component': 'system'
        }
        
        message_lower = entry.message.lower()
        
        # Classify by content
        if any(keyword in message_lower for keyword in ['kernel', 'panic', 'oops']):
            classification['category'] = 'kernel'
            classification['urgency'] = 'high'
        elif any(keyword in message_lower for keyword in ['hardware', 'device', 'pci', 'usb']):
            classification['category'] = 'hardware'
            classification['urgency'] = 'medium'
        elif any(keyword in message_lower for keyword in ['network', 'eth', 'wifi']):
            classification['category'] = 'network'
            classification['component'] = 'network'
        elif any(keyword in message_lower for keyword in ['disk', 'filesystem', 'storage']):
            classification['category'] = 'storage'
            classification['component'] = 'storage'
        elif any(keyword in message_lower for keyword in ['memory', 'oom', 'ram']):
            classification['category'] = 'memory'
            classification['urgency'] = 'high'
        
        # Adjust urgency based on severity
        if entry.severity in ['critical', 'emergency']:
            classification['urgency'] = 'critical'
        elif entry.severity in ['error', 'alert']:
            classification['urgency'] = 'high'
        elif entry.severity == 'warning':
            classification['urgency'] = 'medium'
        
        return classification
    
    def _provide_entry_context(self, entry: LogEntry) -> Dict[str, Any]:
        """Provide context for a log entry.
        
        Args:
            entry: Log entry
            
        Returns:
            Dictionary containing context information
        """
        context = {
            'timestamp_info': {
                'formatted': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'age_hours': (datetime.now() - entry.timestamp).total_seconds() / 3600,
                'day_of_week': entry.timestamp.strftime('%A'),
                'time_of_day': self._classify_time_of_day(entry.timestamp)
            },
            'source_info': {
                'facility': entry.facility,
                'source': entry.source,
                'is_kernel': entry.facility == 'kernel' or 'kernel' in entry.source.lower()
            },
            'message_info': {
                'length': len(entry.message),
                'word_count': len(entry.message.split()),
                'contains_numbers': any(char.isdigit() for char in entry.message),
                'contains_paths': '/' in entry.message,
                'contains_addresses': any(keyword in entry.message.lower() for keyword in ['0x', 'address', 'pointer'])
            }
        }
        
        return context
    
    def _generate_entry_recommendations(self, entry: LogEntry, classification: Dict[str, Any]) -> List[str]:
        """Generate recommendations for a specific log entry.
        
        Args:
            entry: Log entry
            classification: Entry classification
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        category = classification['category']
        urgency = classification['urgency']
        
        # General recommendations based on urgency
        if urgency == 'critical':
            recommendations.append('Take immediate action - system stability may be at risk')
            recommendations.append('Consider emergency maintenance or system restart if necessary')
        elif urgency == 'high':
            recommendations.append('Address this issue promptly to prevent system problems')
            recommendations.append('Schedule maintenance window if hardware intervention is needed')
        
        # Category-specific recommendations
        if category == 'kernel':
            recommendations.extend([
                'Check kernel version and consider updating',
                'Review hardware compatibility',
                'Check system memory and CPU health'
            ])
        elif category == 'hardware':
            recommendations.extend([
                'Run hardware diagnostics',
                'Check device connections and cables',
                'Update device drivers and firmware'
            ])
        elif category == 'network':
            recommendations.extend([
                'Check network connectivity',
                'Verify network configuration',
                'Update network drivers'
            ])
        elif category == 'storage':
            recommendations.extend([
                'Check disk health with SMART tools',
                'Run filesystem check',
                'Verify storage device connections'
            ])
        elif category == 'memory':
            recommendations.extend([
                'Run memory test (memtest86+)',
                'Check available memory and swap usage',
                'Consider adding more RAM if needed'
            ])
        
        return recommendations
    
    def _classify_time_of_day(self, timestamp: datetime) -> str:
        """Classify time of day for context.
        
        Args:
            timestamp: Timestamp to classify
            
        Returns:
            Time of day classification
        """
        hour = timestamp.hour
        
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def _get_health_assessment_text(self, health_status: str, critical_count: int, high_count: int) -> str:
        """Get health assessment text.
        
        Args:
            health_status: Health status
            critical_count: Number of critical issues
            high_count: Number of high priority issues
            
        Returns:
            Health assessment text
        """
        if health_status == 'excellent':
            return 'System is running well with minimal issues detected'
        elif health_status == 'good':
            return 'System is generally healthy with some minor issues to address'
        elif health_status == 'fair':
            return 'System has moderate issues that should be addressed during maintenance'
        elif health_status == 'poor':
            return f'System has significant issues including {high_count} high priority problems'
        else:  # critical
            return f'System requires immediate attention with {critical_count} critical and {high_count} high priority issues'