#!/usr/bin/env python3
"""Custom exceptions for diagnostics module.

Copyright 2024 Infenia Private Limited
Licensed under the Apache License, Version 2.0
"""


class DiagnosticsError(Exception):
    """Base exception for diagnostics module."""
    
    def __init__(self, message: str, component: str = None, error_code: str = None):
        """Initialize diagnostics error.
        
        Args:
            message: Error message
            component: Component that caused the error
            error_code: Specific error code for categorization
        """
        super().__init__(message)
        self.component = component
        self.error_code = error_code
        self.message = message
    
    def __str__(self) -> str:
        """Return string representation of error."""
        parts = [self.message]
        if self.component:
            parts.append(f"Component: {self.component}")
        if self.error_code:
            parts.append(f"Error Code: {self.error_code}")
        return " | ".join(parts)


class HardwareDiagnosticsError(DiagnosticsError):
    """Exception for hardware diagnostics errors."""
    
    def __init__(self, message: str, hardware_component: str = None):
        """Initialize hardware diagnostics error."""
        super().__init__(message, component=hardware_component, error_code="HW_DIAG")


class KernelConfigError(DiagnosticsError):
    """Exception for kernel configuration errors."""
    
    def __init__(self, message: str, config_option: str = None):
        """Initialize kernel configuration error."""
        super().__init__(message, component=config_option, error_code="KERNEL_CFG")


class LogAnalysisError(DiagnosticsError):
    """Exception for log analysis errors."""
    
    def __init__(self, message: str, log_source: str = None):
        """Initialize log analysis error."""
        super().__init__(message, component=log_source, error_code="LOG_ANALYSIS")


class QueryProcessingError(DiagnosticsError):
    """Exception for query processing errors."""
    
    def __init__(self, message: str, query: str = None):
        """Initialize query processing error."""
        super().__init__(message, component=query, error_code="QUERY_PROC")


class SystemInterfaceError(DiagnosticsError):
    """Exception for system interface errors."""
    
    def __init__(self, message: str, command: str = None):
        """Initialize system interface error."""
        super().__init__(message, component=command, error_code="SYS_INTERFACE")


class ConfigurationError(DiagnosticsError):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None):
        """Initialize configuration error."""
        super().__init__(message, component=config_key, error_code="CONFIG")


class ThresholdExceededError(DiagnosticsError):
    """Exception for when diagnostic thresholds are exceeded."""
    
    def __init__(self, message: str, threshold_type: str = None, current_value: float = None, threshold_value: float = None):
        """Initialize threshold exceeded error."""
        super().__init__(message, component=threshold_type, error_code="THRESHOLD")
        self.current_value = current_value
        self.threshold_value = threshold_value
    
    def __str__(self) -> str:
        """Return string representation with threshold details."""
        base_str = super().__str__()
        if self.current_value is not None and self.threshold_value is not None:
            base_str += f" | Current: {self.current_value}, Threshold: {self.threshold_value}"
        return base_str


class InvalidQueryError(QueryProcessingError):
    """Exception for invalid or malformed queries."""
    
    def __init__(self, message: str, query: str = None):
        """Initialize invalid query error."""
        super().__init__(message, query)
        self.error_code = "INVALID_QUERY"


class IntentClassificationError(QueryProcessingError):
    """Exception for intent classification failures."""
    
    def __init__(self, message: str, query: str = None):
        """Initialize intent classification error."""
        super().__init__(message, query)
        self.error_code = "INTENT_CLASSIFICATION"


class EntityExtractionError(QueryProcessingError):
    """Exception for entity extraction failures."""
    
    def __init__(self, message: str, query: str = None):
        """Initialize entity extraction error."""
        super().__init__(message, query)
        self.error_code = "ENTITY_EXTRACTION"


class ToolRoutingError(QueryProcessingError):
    """Exception for tool routing failures."""
    
    def __init__(self, message: str, intent: str = None):
        """Initialize tool routing error."""
        super().__init__(message, intent)
        self.error_code = "TOOL_ROUTING"