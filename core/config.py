#!/usr/bin/env python3
"""
Configuración global de la API ESP32 - RATE LIMITING CORREGIDO
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
    
    # Rate Limiting BASE - LEE DEL .env
    MIN_COMMAND_INTERVAL: float = 0.1  #  (valor por defecto)
    MAX_REQUESTS_PER_MINUTE: int = 600
    
    # Cache Configuration
    CACHE_TTL: int = 2  # 2 segundos de cache
    REDIS_URL: Optional[str] = "redis://esp32-redis:6379"  # Default para Docker
    
    # Redis Configuration
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/esp32_api.log"
    
    # Timezone Configuration
    TZ: str = "America/Bogota"
    
    # NUEVO: Multi-CPU Configuration
    MAX_WORKERS: str = "auto"
    CPU_LIMIT: str = "auto" 
    MEMORY_LIMIT: str = "auto"
    FORCE_SINGLE_WORKER: bool = False
    
    class Config:
        env_file = ".env"
    
    # ✅ CORRECCIÓN: Rate Limiting calculado DESPUÉS de leer .env
    @property
    def READ_DATA_INTERVAL(self) -> float:
        """Intervalo mínimo para lectura de datos"""
        return self.MIN_COMMAND_INTERVAL
    
    @property 
    def READ_DATA_PER_MINUTE(self) -> int:
        """Máximo requests por minuto para lectura"""
        return self.MAX_REQUESTS_PER_MINUTE
    
    @property
    def CONFIG_CHANGE_INTERVAL(self) -> float:
        """Intervalo mínimo para cambios de configuración (3x más restrictivo)"""
        return self.MIN_COMMAND_INTERVAL * 3
    
    @property
    def CONFIG_CHANGE_PER_MINUTE(self) -> int:
        """Máximo cambios de configuración por minuto"""
        return max(6, self.MAX_REQUESTS_PER_MINUTE // 10)  # Mínimo 6, máximo 10% del total
    
    @property
    def ACTION_INTERVAL(self) -> float:
        """Intervalo mínimo para acciones críticas (10x más restrictivo)"""
        return self.MIN_COMMAND_INTERVAL * 10
    
    @property
    def ACTION_PER_MINUTE(self) -> int:
        """Máximo acciones por minuto"""
        return max(3, self.MAX_REQUESTS_PER_MINUTE // 20)  # Mínimo 3, máximo 5% del total
    
    @property
    def HEALTH_CHECK_INTERVAL(self) -> float:
        """Intervalo mínimo para health checks (más permisivo)"""
        return max(1.0, self.MIN_COMMAND_INTERVAL / 2)  # Mínimo 1s, o la mitad del interval base
    
    @property
    def HEALTH_CHECK_PER_MINUTE(self) -> int:
        """Máximo health checks por minuto"""
        return self.MAX_REQUESTS_PER_MINUTE

# Crear instancia global
settings = Settings()

# Opcional: Imprimir configuración de rate limiting al iniciar
if __name__ == "__main__":
    print("🔧 Configuración de Rate Limiting:")
    print(f"  MIN_COMMAND_INTERVAL: {settings.MIN_COMMAND_INTERVAL}s")
    print(f"  MAX_REQUESTS_PER_MINUTE: {settings.MAX_REQUESTS_PER_MINUTE}")
    print(f"  READ_DATA_INTERVAL: {settings.READ_DATA_INTERVAL}s")
    print(f"  CONFIG_CHANGE_INTERVAL: {settings.CONFIG_CHANGE_INTERVAL}s") 
    print(f"  ACTION_INTERVAL: {settings.ACTION_INTERVAL}s")
    print(f"  HEALTH_CHECK_INTERVAL: {settings.HEALTH_CHECK_INTERVAL}s")