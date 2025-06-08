#!/usr/bin/env python3
"""
Endpoints para acciones de control del ESP32 - Versión Corregida
"""

from fastapi import APIRouter, HTTPException, Depends
from models.esp32_data import ToggleLoadRequest
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger

router = APIRouter(prefix="/actions", tags=["Actions"])

async def get_esp32_manager() -> ESP32Manager:
    """Dependency para obtener ESP32Manager"""
    from main import esp32_manager
    return esp32_manager

@router.post("/toggle_load")
async def toggle_load(
    request: ToggleLoadRequest,
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Apagar la carga temporalmente - MEJORADO
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
        
        # Enviar comando al ESP32
        success = await manager.toggle_load(total_seconds)
        
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

@router.post("/cancel_temp_off")
async def cancel_temporary_off(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Cancelar el apagado temporal de la carga - MEJORADO
    """
    try:
        logger.info("🔌 Solicitud de cancelar apagado temporal")
        
        success = await manager.cancel_temporary_off()
        
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

@router.get("/status")
async def get_actions_status(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Obtener estado actual de las acciones - CORREGIDO
    """
    try:
        logger.debug("📊 Obteniendo estado de acciones")
        
        # Verificar que el manager esté conectado
        if not manager.connected:
            logger.warning("⚠️ ESP32Manager no está conectado")
            raise HTTPException(
                status_code=503, 
                detail="ESP32 no está conectado. Verifica la conexión."
            )
        
        # Obtener datos del ESP32
        data = await manager.get_data()
        if not data:
            logger.error("❌ No se pudieron obtener datos del ESP32")
            raise HTTPException(
                status_code=503, 
                detail="Error comunicándose con ESP32"
            )
        
        # Extraer información relevante para acciones
        actions_status = {
            "temporary_load_off": data.temporaryLoadOff,
            "load_off_remaining_seconds": data.loadOffRemainingSeconds,
            "load_off_duration": data.loadOffDuration,
            "load_control_state": data.loadControlState,
            "charge_state": data.chargeState,
            "esp32_connected": True,
            "last_update": data.last_update
        }
        
        logger.debug(f"✅ Estado de acciones obtenido: temporaryLoadOff={data.temporaryLoadOff}")
        return actions_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado obteniendo estado de acciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/info")
async def get_actions_info():
    """
    Obtener información sobre las acciones disponibles
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