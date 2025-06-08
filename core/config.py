#!/usr/bin/env python3
"""
Configuración global de la API ESP32
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "ESP32 Solar Charger API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API para control y monitoreo del cargador solar ESP32"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # ESP32 Serial Configuration
    SERIAL_PORT: str = "/dev/ttyS5"
    SERIAL_BAUDRATE: int = 9600
    SERIAL_TIMEOUT: float = 3.0
    
    # Rate Limiting
    MIN_COMMAND_INTERVAL: float = 0.6  # 600ms entre comandos
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # Cache Configuration
    CACHE_TTL: int = 2  # 2 segundos de cache
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/esp32_api.log"
    
    class Config:
        env_file = ".env"

    # Rate Limiting Configuration - LEE DEL .env
    RATE_LIMITING_ENABLED: bool = True
    RATE_LIMITING_STORAGE: str = "memory"  # memory | redis
    RATE_LIMITING_CLIENT_TRACKING: bool = True

    # Rate Limiting por Operación - USA .env como base
    READ_DATA_INTERVAL: int = MIN_COMMAND_INTERVAL  # Usa tu valor del .env
    READ_DATA_PER_MINUTE: int = MAX_REQUESTS_PER_MINUTE // 2  # Más restrictivo para lecturas

    CONFIG_CHANGE_INTERVAL: int = MIN_COMMAND_INTERVAL * 3  # 3x más restrictivo que lectura
    CONFIG_CHANGE_PER_MINUTE: int = 6  # Muy restrictivo para cambios

    ACTION_INTERVAL: int = MIN_COMMAND_INTERVAL * 10  # 10x más restrictivo
    ACTION_PER_MINUTE: int = 3  # Máximo 3 acciones por minuto

    HEALTH_CHECK_INTERVAL: int = 1  # Health checks pueden ser frecuentes
    HEALTH_CHECK_PER_MINUTE: int = MAX_REQUESTS_PER_MINUTE  # Usa tu valor del .env

settings = Settings()
