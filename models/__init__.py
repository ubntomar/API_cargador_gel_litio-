#!/usr/bin/env python3
"""
Modelos de datos para la API
"""

# Modelos ESP32
from .esp32_data import ESP32Data, ConfigParameter, ESP32Status
from .responses import (
    ErrorResponse, 
    SuccessResponse, 
    ESP32Response,
    ValidationErrorResponse
)
from .rate_limiting import RateLimit, RateLimitStats

# Modelos de Schedule
from .schedule_models import (
    ScheduleEntry,
    ScheduleRequest,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleStatus,
    ScheduleUpdateRequest
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
    "ESP32Status",
    "ErrorResponse",
    "SuccessResponse",
    "ESP32Response",
    "ValidationErrorResponse",
    "RateLimit",
    "RateLimitStats",
    
    # Schedule Models
    "ScheduleEntry",
    "ScheduleRequest", 
    "ScheduleResponse",
    "ScheduleListResponse",
    "ScheduleStatus",
    "ScheduleUpdateRequest",
    
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