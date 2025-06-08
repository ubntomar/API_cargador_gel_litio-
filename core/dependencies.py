#!/usr/bin/env python3
"""
Dependencies de FastAPI para Rate Limiting
"""

from fastapi import Request, Depends
from typing import Optional
from models.rate_limiting import OperationType
from services.rate_limiter import rate_limiter
from core.logger import logger

def get_client_id(request: Request) -> str:
    """
    Obtener identificador único del cliente
    
    Prioridad:
    1. Header X-Client-ID (si existe)
    2. IP del cliente
    3. "unknown" como fallback
    """
    # Intentar obtener client ID custom
    client_id = request.headers.get("X-Client-ID")
    if client_id:
        return f"client_{client_id}"
    
    # Obtener IP del cliente
    # Considerar proxies y load balancers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Tomar la primera IP (cliente original)
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = getattr(request.client, "host", "unknown")
    
    return f"ip_{client_ip}"

async def check_read_rate_limit(request: Request):
    """
    Dependency para endpoints de lectura de datos
    Aplicar rate limiting ligero para lecturas
    """
    client_id = get_client_id(request)
    
    try:
        rate_limiter.check_rate_limit(OperationType.READ_DATA, client_id)
        logger.debug(f"✅ Rate limit READ OK para {client_id}")
    except Exception as e:
        logger.warning(f"⚡ Rate limit READ bloqueado para {client_id}")
        raise

async def check_config_rate_limit(request: Request):
    """
    Dependency para endpoints de configuración
    Aplicar rate limiting moderado para cambios de configuración
    """
    client_id = get_client_id(request)
    
    try:
        rate_limiter.check_rate_limit(OperationType.SET_CONFIG, client_id)
        logger.debug(f"✅ Rate limit CONFIG OK para {client_id}")
    except Exception as e:
        logger.warning(f"⚡ Rate limit CONFIG bloqueado para {client_id}")
        raise

async def check_action_rate_limit(request: Request):
    """
    Dependency para endpoints de acciones críticas
    Aplicar rate limiting estricto para acciones
    """
    client_id = get_client_id(request)
    
    try:
        rate_limiter.check_rate_limit(OperationType.EXECUTE_ACTION, client_id)
        logger.debug(f"✅ Rate limit ACTION OK para {client_id}")
    except Exception as e:
        logger.warning(f"⚡ Rate limit ACTION bloqueado para {client_id}")
        raise

async def check_health_rate_limit(request: Request):
    """
    Dependency para health checks
    Aplicar rate limiting muy ligero para health checks
    """
    client_id = get_client_id(request)
    
    try:
        rate_limiter.check_rate_limit(OperationType.HEALTH_CHECK, client_id)
        logger.debug(f"✅ Rate limit HEALTH OK para {client_id}")
    except Exception as e:
        logger.debug(f"⚡ Rate limit HEALTH bloqueado para {client_id}")
        raise

# Dependency para obtener rate limiter (útil para endpoints de estadísticas)
async def get_rate_limiter():
    """Dependency para obtener instancia del rate limiter"""
    return rate_limiter

# Dependency opcional que no falla (para endpoints de monitoreo)
async def check_rate_limit_optional(request: Request):
    """
    Rate limiting opcional que no bloquea
    Solo registra en logs pero permite continuar
    """
    client_id = get_client_id(request)
    
    try:
        rate_limiter.check_rate_limit(OperationType.READ_DATA, client_id)
        return {"rate_limited": False}
    except Exception as e:
        logger.info(f"ℹ️ Rate limit aplicado a {client_id} (request continuó)")
        return {"rate_limited": True, "reason": str(e)}
