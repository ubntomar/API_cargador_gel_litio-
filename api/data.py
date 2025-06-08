#!/usr/bin/env python3
"""
Endpoints para datos del ESP32
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, Union
from models.esp32_data import ESP32Data, ParameterInfo
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger
from core.dependencies import check_read_rate_limit  


router = APIRouter(prefix="/data", tags=["Data"])

async def get_esp32_manager() -> ESP32Manager:
    """Dependency para obtener ESP32Manager"""
    from main import esp32_manager
    return esp32_manager

@router.get("/", response_model=ESP32Data, dependencies=[Depends(check_read_rate_limit)])
async def get_all_data(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Obtener todos los datos del ESP32
    """
    try:
        # Verificar cache primero
        cached_data = data_cache.get("all_data")
        if cached_data:
            return cached_data
        
        # Obtener datos frescos
        data = await manager.get_data()
        if not data:
            raise HTTPException(status_code=503, detail="Error comunicándose con ESP32")
        
        # Guardar en cache
        data_cache.set("all_data", data)
        
        return data
        
    except Exception as e:
        logger.error(f"❌ Error en get_all_data: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{parameter_name}", dependencies=[Depends(check_read_rate_limit)])
async def get_parameter(
    parameter_name: str, 
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Obtener un parámetro específico
    """
    try:
        # Obtener datos completos
        data = await manager.get_data()
        if not data:
            raise HTTPException(status_code=503, detail="Error comunicándose con ESP32")
        
        # Extraer parámetro específico
        value = getattr(data, parameter_name, None)
        if value is None:
            raise HTTPException(status_code=404, detail="Parámetro no encontrado")
        
        return {
            "parameter": parameter_name,
            "value": value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo {parameter_name}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/status/connection", dependencies=[Depends(check_read_rate_limit)])
async def get_connection_status(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Obtener estado de conexión con ESP32
    """
    return manager.get_connection_info()

@router.get("/status/cache", dependencies=[Depends(check_read_rate_limit)])
async def get_cache_status():
    """
    Obtener estadísticas del cache
    """
    return data_cache.get_stats()
