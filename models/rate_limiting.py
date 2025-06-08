#!/usr/bin/env python3
"""
Modelos Pydantic para Rate Limiting
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

class OperationType(str, Enum):
    """Tipos de operaciones para rate limiting"""
    READ_DATA = "read_data"
    SET_CONFIG = "set_config"
    EXECUTE_ACTION = "execute_action"
    HEALTH_CHECK = "health_check"

class RateLimitInfo(BaseModel):
    """Información de límites para un tipo de operación"""
    min_interval_seconds: float = Field(..., description="Intervalo mínimo entre requests")  # CORREGIDO: int -> float
    max_per_minute: int = Field(..., description="Máximo requests por minuto")
    description: str = Field(..., description="Descripción del tipo de operación")

class RateLimitStatus(BaseModel):
    """Estado actual de rate limiting para una operación"""
    operation_type: str
    limits: RateLimitInfo
    current_usage: Dict[str, Any]
    status: str = Field(..., description="available, blocked, warning")
    next_allowed_in_seconds: float = Field(0, description="Segundos hasta próxima request permitida")

class RateLimitError(BaseModel):
    """Detalles de error de rate limiting"""
    error: str = "Rate limit exceeded"
    operation: str
    limit_type: str = Field(..., description="minimum_interval o requests_per_minute")
    description: str
    wait_seconds: Optional[float] = None
    requests_in_last_minute: Optional[int] = None
    max_per_minute: Optional[int] = None
    reset_in_seconds: Optional[float] = None

class RateLimitStats(BaseModel):
    """Estadísticas completas de rate limiting"""
    enabled: bool
    total_requests: int
    blocked_requests: int
    success_rate: float
    operations: Dict[str, RateLimitStatus]
    uptime_seconds: float
    
class ClientRateLimitInfo(BaseModel):
    """Información de rate limiting por cliente"""
    client_id: str
    total_requests: int
    blocked_requests: int
    last_request: Optional[datetime] = None
    operations_used: List[str]