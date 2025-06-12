#!/usr/bin/env python3
"""
Modelos Pydantic para Schedule Diario - ESP32 API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import time
import re

class ScheduleConfigRequest(BaseModel):
    """Modelo para configurar schedule diario"""
    enabled: bool = Field(..., description="Habilitar/deshabilitar schedule diario")
    start_time: str = Field(..., description="Hora de inicio en formato HH:MM (24h)")
    duration_seconds: int = Field(..., ge=1, le=28800, description="Duración en segundos (máx 8 horas)")
    
    @validator('start_time')
    def validate_time_format(cls, v):
        """Validar formato HH:MM"""
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Formato debe ser HH:MM (24 horas). Ejemplo: 14:30')
        return v
    
    @validator('duration_seconds')
    def validate_duration(cls, v):
        """Validar duración máxima de 8 horas"""
        if v > 28800:  # 8 horas = 28800 segundos
            raise ValueError('Duración máxima: 8 horas (28800 segundos)')
        if v < 1:
            raise ValueError('Duración mínima: 1 segundo')
        return v

class ScheduleStatusResponse(BaseModel):
    """Respuesta del estado actual del schedule"""
    enabled: bool = Field(..., description="Schedule habilitado")
    start_time: Optional[str] = Field(None, description="Hora de inicio configurada")
    duration_seconds: Optional[int] = Field(None, description="Duración en segundos")
    duration_hours: Optional[float] = Field(None, description="Duración en horas (calculado)")
    end_time: Optional[str] = Field(None, description="Hora de fin calculada")
    currently_active: bool = Field(..., description="Schedule activo en este momento")
    next_execution: Optional[str] = Field(None, description="Próxima ejecución")
    manual_override_active: bool = Field(..., description="Override manual activo (anula schedule)")
    current_time: str = Field(..., description="Hora actual del sistema")

class ToggleLoadExtendedRequest(BaseModel):
    """Modelo extendido para toggle con información de override"""
    hours: int = Field(0, ge=0, le=8, description="Horas")
    minutes: int = Field(0, ge=0, le=59, description="Minutos") 
    seconds: int = Field(0, ge=0, le=59, description="Segundos")
    is_manual_override: bool = Field(True, description="Es override manual (anula schedule)")
    
    @validator('*')
    def validate_total_duration(cls, v, values):
        """Validar duración total"""
        hours = values.get('hours', 0)
        minutes = values.get('minutes', 0)
        seconds = v if cls.__name__ == 'seconds' else values.get('seconds', 0)
        
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        if total_seconds < 1:
            raise ValueError("Duración mínima: 1 segundo total")
        if total_seconds > 28800:  # 8 horas
            raise ValueError("Duración máxima: 8 horas (28800 segundos)")
        
        return v

class ScheduleInfoResponse(BaseModel):
    """Información sobre las capacidades del schedule"""
    max_duration_hours: int = Field(8, description="Duración máxima en horas")
    max_duration_seconds: int = Field(28800, description="Duración máxima en segundos")
    time_format: str = Field("HH:MM", description="Formato de hora esperado")
    timezone: str = Field(..., description="Zona horaria del sistema")
    persistence: bool = Field(False, description="Configuración se persiste entre reinicios")
    manual_override_behavior: str = Field(
        "cancels_daily_schedule", 
        description="Comportamiento del override manual"
    )
    examples: dict = Field(
        default={
            "schedule_config": {
                "enabled": True,
                "start_time": "00:00",
                "duration_seconds": 21600
            },
            "toggle_manual": {
                "hours": 0,
                "minutes": 30,
                "seconds": 0,
                "is_manual_override": True
            }
        }
    )