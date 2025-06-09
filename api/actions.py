#!/usr/bin/env python3
"""
Endpoints para acciones de control del ESP32 - VERSIÓN OPTIMIZADA ANTI-CONGELAMIENTO
"""

from fastapi import APIRouter, HTTPException, Depends
from models.esp32_data import ToggleLoadRequest
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger
from core.dependencies import check_action_rate_limit, check_read_rate_limit
import asyncio
import time

router = APIRouter(prefix="/actions", tags=["Actions"])

async def get_esp32_manager() -> ESP32Manager:
    """Dependency para obtener ESP32Manager"""
    from main import esp32_manager
    return esp32_manager

@router.post("/toggle_load", dependencies=[Depends(check_action_rate_limit)])
async def toggle_load(
    request: ToggleLoadRequest,
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Apagar la carga temporalmente - OPTIMIZADO
    """
    try:
        logger.info(f"🔌 Solicitud de toggle_load: {request.hours}h {request.minutes}m {request.seconds}s")
        
        # Calcular tiempo total en segundos
        total_seconds = request.hours * 3600 + request.minutes * 60 + request.seconds
        logger.info(f"🔌 Tiempo total calculado: {total_seconds} segundos")
        
        # Validación adicional (por si acaso)
        if total_seconds < 1:
            raise HTTPException(
                status_code=400,
                detail="Duración mínima: 1 segundo total"
            )
        
        if total_seconds > 43200:  # 12 horas
            raise HTTPException(
                status_code=400,
                detail="Duración máxima: 12 horas (43200 segundos)"
            )
        
        # ✅ NUEVO: Timeout con asyncio para prevenir congelamiento
        try:
            success = await asyncio.wait_for(
                manager.toggle_load(total_seconds), 
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error("❌ Timeout en toggle_load")
            raise HTTPException(
                status_code=504,
                detail="Timeout comunicándose con ESP32"
            )
        
        if not success:
            logger.error(f"❌ ESP32Manager falló en toggle_load")
            raise HTTPException(
                status_code=500,
                detail="Error enviando comando al ESP32"
            )
        
        # Invalidar cache para reflejar cambios
        data_cache.invalidate("all_data")
        
        response = {
            "success": True,
            "message": f"Carga apagada por {total_seconds} segundos",
            "duration": {
                "hours": request.hours,
                "minutes": request.minutes,
                "seconds": request.seconds,
                "total_seconds": total_seconds
            }
        }
        
        logger.info(f"✅ Toggle load exitoso: {total_seconds}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en toggle_load: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/cancel_temp_off", dependencies=[Depends(check_action_rate_limit)])
async def cancel_temporary_off(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Cancelar el apagado temporal de la carga - OPTIMIZADO
    """
    try:
        logger.info("🔌 Solicitud de cancelar apagado temporal")
        
        # ✅ NUEVO: Timeout para prevenir congelamiento
        try:
            success = await asyncio.wait_for(
                manager.cancel_temporary_off(), 
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error("❌ Timeout en cancel_temporary_off")
            raise HTTPException(
                status_code=504,
                detail="Timeout comunicándose con ESP32"
            )
        
        if not success:
            logger.error("❌ ESP32Manager falló en cancel_temporary_off")
            raise HTTPException(
                status_code=500,
                detail="Error enviando comando al ESP32"
            )
        
        # Invalidar cache
        data_cache.invalidate("all_data")
        
        response = {
            "success": True,
            "message": "Apagado temporal cancelado correctamente"
        }
        
        logger.info("✅ Apagado temporal cancelado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado cancelando apagado temporal: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/status", dependencies=[Depends(check_read_rate_limit)])
async def get_actions_status(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Obtener estado actual de las acciones - OPTIMIZADO ANTI-CONGELAMIENTO
    """
    try:
        logger.debug("📊 Obteniendo estado de acciones")
        
        # ✅ NUEVO: Verificación rápida de conexión sin bloqueo
        connection_info = manager.get_connection_info()
        if not connection_info.get("connected", False):
            logger.warning("⚠️ ESP32Manager no está conectado")
            
            # ✅ NUEVO: Retornar estado parcial en lugar de error
            return {
                "esp32_connected": False,
                "temporary_load_off": False,
                "load_off_remaining_seconds": 0,
                "load_off_duration": 0,
                "load_control_state": False,
                "charge_state": "UNKNOWN",
                "last_update": None,
                "error": "ESP32 no está conectado",
                "connection_info": connection_info
            }
        
        # ✅ NUEVO: Timeout agresivo para prevenir congelamiento
        try:
            data = await asyncio.wait_for(
                manager.get_data(), 
                timeout=5.0  # Solo 5 segundos para status
            )
        except asyncio.TimeoutError:
            logger.error("❌ Timeout obteniendo datos para status")
            
            # ✅ NUEVO: Retornar estado de error en lugar de excepción
            return {
                "esp32_connected": True,
                "temporary_load_off": None,
                "load_off_remaining_seconds": None,
                "load_off_duration": None,
                "load_control_state": None,
                "charge_state": "TIMEOUT",
                "last_update": None,
                "error": "Timeout comunicándose con ESP32",
                "connection_info": connection_info
            }
        
        if not data:
            logger.error("❌ No se pudieron obtener datos del ESP32")
            
            # ✅ NUEVO: Retornar estado parcial en lugar de error 503
            return {
                "esp32_connected": False,
                "temporary_load_off": None,
                "load_off_remaining_seconds": None,
                "load_off_duration": None,
                "load_control_state": None,
                "charge_state": "ERROR",
                "last_update": None,
                "error": "Error comunicándose con ESP32",
                "connection_info": connection_info
            }
        
        # ✅ OPTIMIZADO: Extraer información con manejo de errores
        try:
            actions_status = {
                "esp32_connected": True,
                "temporary_load_off": getattr(data, 'temporaryLoadOff', False),
                "load_off_remaining_seconds": getattr(data, 'loadOffRemainingSeconds', 0),
                "load_off_duration": getattr(data, 'loadOffDuration', 0),
                "load_control_state": getattr(data, 'loadControlState', False),
                "charge_state": getattr(data, 'chargeState', 'UNKNOWN'),
                "last_update": getattr(data, 'last_update', str(int(time.time()))),
                "connection_info": connection_info
            }
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos: {e}")
            actions_status = {
                "esp32_connected": True,
                "temporary_load_off": False,
                "load_off_remaining_seconds": 0,
                "load_off_duration": 0,
                "load_control_state": False,
                "charge_state": "PARSE_ERROR",
                "last_update": str(int(time.time())),
                "error": f"Error procesando datos: {str(e)}",
                "connection_info": connection_info
            }
        
        logger.debug(f"✅ Estado de acciones obtenido: temporaryLoadOff={actions_status.get('temporary_load_off')}")
        return actions_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado obteniendo estado de acciones: {e}")
        
        # ✅ NUEVO: En lugar de error 500, retornar estado de error
        return {
            "esp32_connected": False,
            "temporary_load_off": None,
            "load_off_remaining_seconds": None,
            "load_off_duration": None,
            "load_control_state": None,
            "charge_state": "SYSTEM_ERROR",
            "last_update": None,
            "error": f"Error interno: {str(e)}"
        }

@router.get("/info")
async def get_actions_info():
    """
    Obtener información sobre las acciones disponibles - LIVIANO
    """
    return {
        "available_actions": [
            {
                "name": "toggle_load",
                "method": "POST",
                "endpoint": "/actions/toggle_load",
                "description": "Apagar carga temporalmente",
                "parameters": {
                    "hours": "0-12",
                    "minutes": "0-59", 
                    "seconds": "0-59"
                },
                "constraints": {
                    "min_duration": "1 segundo total",
                    "max_duration": "12 horas (43200 segundos)"
                }
            },
            {
                "name": "cancel_temp_off",
                "method": "POST",
                "endpoint": "/actions/cancel_temp_off",
                "description": "Cancelar apagado temporal",
                "parameters": "none"
            }
        ],
        "status_endpoints": [
            {
                "name": "status",
                "method": "GET",
                "endpoint": "/actions/status",
                "description": "Estado actual de acciones"
            },
            {
                "name": "info",
                "method": "GET", 
                "endpoint": "/actions/info",
                "description": "Información sobre acciones disponibles"
            }
        ]
    }