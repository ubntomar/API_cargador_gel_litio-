#!/usr/bin/env python3
"""
Modelos de datos para la API
"""

# Modelos ESP32
from .esp32_data import ESP32Data, ConfigParameter, ChargeState, ToggleLoadRequest, ParameterInfo
from .responses import (
    ErrorResponse,
    APIResponse,
    ParameterResponse,
    BatchConfigResponse,
    ConnectionStatus,
    CacheStats,
    HealthStatus
)
from .rate_limiting import RateLimitInfo, RateLimitStatus, RateLimitError, RateLimitStats

# Modelos de Schedule
from .schedule_models import (
    ScheduleConfigRequest,
    ScheduleStatusResponse,
    ToggleLoadExtendedRequest,
    ScheduleInfoResponse
)

# NUEVO: Modelos de Configuraciones Personalizadas
from .custom_configurations import (
    CustomConfiguration,
    ConfigurationData,
    ConfigurationRequest,
    ConfigurationResponse,
    ConfigurationsListResponse,
    ConfigurationApplyRequest,
    ConfigurationValidationResponse,
    ConfigurationExportResponse,
    ConfigurationImportRequest,
    ConfigurationImportResponse
)

__all__ = [
    # ESP32 Models
    "ESP32Data",
    "ConfigParameter",
    "ChargeState",
    "ToggleLoadRequest", 
    "ParameterInfo",
    
    # Response Models
    "ErrorResponse",
    "APIResponse",
    "ParameterResponse",
    "BatchConfigResponse",
    "ConnectionStatus",
    "CacheStats",
    "HealthStatus",
    
    # Rate Limiting Models
    "RateLimitInfo",
    "RateLimitStatus", 
    "RateLimitError",
    "RateLimitStats",
    
    # Schedule Models
    "ScheduleConfigRequest",
    "ScheduleStatusResponse",
    "ToggleLoadExtendedRequest",
    "ScheduleInfoResponse",
    
    # Custom Configuration Models
    "CustomConfiguration",
    "ConfigurationData",
    "ConfigurationRequest",
    "ConfigurationResponse", 
    "ConfigurationsListResponse",
    "ConfigurationApplyRequest",
    "ConfigurationValidationResponse",
    "ConfigurationExportResponse",
    "ConfigurationImportRequest",
    "ConfigurationImportResponse"
]