#!/usr/bin/env python3
"""
Modelos de respuesta de la API
"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class APIResponse(BaseModel):
    """Respuesta estándar de la API"""
    success: bool
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class ParameterResponse(BaseModel):
    """Respuesta para un parámetro individual"""
    parameter: str
    value: Any
    info: Optional[Dict[str, Any]] = None

class BatchConfigResponse(BaseModel):
    """Respuesta para configuración en lote"""
    results: Dict[str, Dict[str, Any]]
    total_parameters: int
    successful: int
    failed: int
    errors: Optional[List[str]] = None

class ConnectionStatus(BaseModel):
    """Estado de conexión con ESP32"""
    connected: bool
    port: str
    baudrate: int
    last_communication: float
    communication_errors: int
    queue_size: int

class CacheStats(BaseModel):
    """Estadísticas del cache"""
    total_entries: int
    valid_entries: int
    expired_entries: int
    ttl_seconds: int

class HealthStatus(BaseModel):
    """Estado de salud de la API"""
    status: str
    timestamp: float
    esp32_connection: ConnectionStatus
