#!/usr/bin/env python3
"""
Rate Limiter Avanzado para ESP32 API
"""

import time
import threading
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from fastapi import HTTPException

from models.rate_limiting import (
    OperationType, RateLimitInfo, RateLimitStatus, 
    RateLimitError, RateLimitStats
)
from core.logger import logger
from core.config import settings

class RateLimiter:
    """Rate limiter thread-safe con diferentes límites por operación"""
    
    def __init__(self):
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Configuración de límites por tipo de operación
        self.limits = {
            OperationType.READ_DATA: RateLimitInfo(
                min_interval_seconds=settings.READ_DATA_INTERVAL,
                max_per_minute=settings.READ_DATA_PER_MINUTE,
                description="Lectura de datos del ESP32"
            ),
            OperationType.SET_CONFIG: RateLimitInfo(
                min_interval_seconds=settings.CONFIG_CHANGE_INTERVAL,
                max_per_minute=settings.CONFIG_CHANGE_PER_MINUTE,
                description="Modificación de configuración"
            ),
            OperationType.EXECUTE_ACTION: RateLimitInfo(
                min_interval_seconds=settings.ACTION_INTERVAL,
                max_per_minute=settings.ACTION_PER_MINUTE,
                description="Ejecución de acciones críticas"
            ),
            OperationType.HEALTH_CHECK: RateLimitInfo(
                min_interval_seconds=settings.HEALTH_CHECK_INTERVAL,
                max_per_minute=settings.HEALTH_CHECK_PER_MINUTE,
                description="Health checks del sistema"
            )
        }
        
        # Tracking por operación y cliente
        self.last_request: Dict[tuple, float] = {}  # (operation, client_id) -> timestamp
        self.request_history: Dict[tuple, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Estadísticas globales
        self.total_requests = 0
        self.blocked_requests = 0
        
        logger.info("✅ Rate Limiter inicializado con límites diferenciados")
    
    def check_rate_limit(self, operation_type: OperationType, 
                        client_id: str = "default") -> bool:
        """
        Verificar si la request está dentro de los límites
        
        Returns:
            True si está permitido
            
        Raises:
            HTTPException: Si excede los límites
        """
        with self.lock:
            now = time.time()
            key = (operation_type, client_id)
            limits = self.limits[operation_type]
            
            self.total_requests += 1
            
            # 1. Verificar intervalo mínimo
            if key in self.last_request:
                time_since_last = now - self.last_request[key]
                min_interval = limits.min_interval_seconds
                
                if time_since_last < min_interval:
                    remaining = min_interval - time_since_last
                    self.blocked_requests += 1
                    
                    logger.warning(
                        f"⚡ Rate limit: {operation_type.value} [{client_id}] - "
                        f"Intervalo mínimo: {remaining:.1f}s restantes"
                    )
                    logger.debug(
                        f"Última request: {self.last_request[key]} ({time_since_last:.1f}s atrás)"
                    )
                    logger.debug(
                        f"Límite: {limits.min_interval_seconds}s, "
                        f"Descripción: {limits.description}"
                    )
                    logger.debug(
                        f"Historial de requests: {list(self.request_history[key])}"
                    )
                    logger.debug(
                        f"Total requests: {self.total_requests}, "
                        f"Bloqueadas: {self.blocked_requests}"
                    )
                    # Lanzar excepción con detalles del error
                    raise HTTPException(
                        status_code=429,
                        detail=RateLimitError(
                            operation=operation_type.value,
                            limit_type="minimum_interval",
                            description=limits.description,
                            wait_seconds=round(remaining, 1)
                        ).model_dump()
                    )
            
            # 2. Verificar límite por minuto
            history = self.request_history[key]
            
            # Limpiar requests antiguos (más de 1 minuto)
            cutoff = now - 60
            while history and history[0] <= cutoff:
                history.popleft()
            
            if len(history) >= limits.max_per_minute:
                self.blocked_requests += 1
                oldest_request = history[0] if history else now
                reset_in = 60 - (now - oldest_request)
                
                logger.warning(
                    f"⚡ Rate limit: {operation_type.value} [{client_id}] - "
                    f"Máximo {limits.max_per_minute}/min excedido"
                )
                
                raise HTTPException(
                    status_code=429,
                    detail=RateLimitError(
                        operation=operation_type.value,
                        limit_type="requests_per_minute",
                        description=limits.description,
                        requests_in_last_minute=len(history),
                        max_per_minute=limits.max_per_minute,
                        reset_in_seconds=max(0, round(reset_in, 1))
                    ).dict()
                )
            
            # 3. Registrar request exitosa
            self.last_request[key] = now
            history.append(now)
            
            logger.debug(
                f"✅ Rate limit OK: {operation_type.value} [{client_id}] - "
                f"{len(history)}/{limits.max_per_minute} en último minuto"
            )
            
            return True
    
    def get_operation_status(self, operation_type: OperationType, 
                           client_id: str = "default") -> RateLimitStatus:
        """Obtener estado de rate limiting para una operación específica"""
        with self.lock:
            now = time.time()
            key = (operation_type, client_id)
            limits = self.limits[operation_type]
            
            # Limpiar historia antigua
            history = self.request_history[key]
            cutoff = now - 60
            while history and history[0] <= cutoff:
                history.popleft()
            
            # Calcular tiempo hasta próxima request permitida
            next_allowed = 0
            if key in self.last_request:
                time_since_last = now - self.last_request[key]
                if time_since_last < limits.min_interval_seconds:
                    next_allowed = limits.min_interval_seconds - time_since_last
            
            # Determinar status
            if next_allowed > 0:
                status = "blocked"
            elif len(history) >= limits.max_per_minute:
                status = "blocked"
            elif len(history) >= limits.max_per_minute * 0.8:
                status = "warning"
            else:
                status = "available"
            
            return RateLimitStatus(
                operation_type=operation_type.value,
                limits=limits,
                current_usage={
                    "requests_in_last_minute": len(history),
                    "last_request_seconds_ago": (
                        now - self.last_request[key] 
                        if key in self.last_request else None
                    ),
                    "usage_percentage": round(len(history) / limits.max_per_minute * 100, 1)
                },
                status=status,
                next_allowed_in_seconds=max(0, next_allowed)
            )
    
    def get_stats(self) -> RateLimitStats:
        """Obtener estadísticas completas"""
        with self.lock:
            operations_status = {}
            
            # Obtener status para cada tipo de operación (cliente default)
            for op_type in OperationType:
                operations_status[op_type.value] = self.get_operation_status(op_type)
            
            success_rate = (
                (self.total_requests - self.blocked_requests) / self.total_requests * 100
                if self.total_requests > 0 else 100.0
            )
            
            return RateLimitStats(
                enabled=True,
                total_requests=self.total_requests,
                blocked_requests=self.blocked_requests,
                success_rate=round(success_rate, 2),
                operations=operations_status,
                uptime_seconds=round(time.time() - self.start_time, 1)
            )
    
    def reset_limits(self, operation_type: Optional[OperationType] = None, 
                    client_id: str = "default"):
        """Reset límites (útil para testing)"""
        with self.lock:
            if operation_type:
                key = (operation_type, client_id)
                self.last_request.pop(key, None)
                if key in self.request_history:
                    self.request_history[key].clear()
                logger.info(f"🔄 Rate limits reset para {operation_type.value} [{client_id}]")
            else:
                self.last_request.clear()
                self.request_history.clear()
                self.total_requests = 0
                self.blocked_requests = 0
                logger.info("🔄 Todos los rate limits reset")
    
    def update_limits(self, operation_type: OperationType, 
                     min_interval: Optional[int] = None,
                     max_per_minute: Optional[int] = None):
        """Actualizar límites dinámicamente"""
        with self.lock:
            current_limits = self.limits[operation_type]
            
            if min_interval is not None:
                current_limits.min_interval_seconds = min_interval
            
            if max_per_minute is not None:
                current_limits.max_per_minute = max_per_minute
            
            logger.info(
                f"🔧 Límites actualizados para {operation_type.value}: "
                f"interval={current_limits.min_interval_seconds}s, "
                f"max_per_min={current_limits.max_per_minute}"
            )

# Instancia global del rate limiter
rate_limiter = RateLimiter()
