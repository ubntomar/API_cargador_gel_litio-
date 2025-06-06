#!/usr/bin/env python3
"""
Endpoints para acciones de control del ESP32
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
    Apagar la carga temporalmente
    """
    try:
        # Calcular tiempo total en segundos
        total_seconds = request.hours * 3600 + request.minutes * 60 + request.seconds
        
        # Enviar comando al ESP32
        success = await manager.toggle_load(total_seconds)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error enviando comando al ESP32"
            )
        
        # Invalidar cache para reflejar cambios
        data_cache.invalidate("all_data")
        
        return {
            "success": True,
            "message": f"Carga apagada por {total_seconds} segundos",
            "duration": {
                "hours": request.hours,
                "minutes": request.minutes,
                "seconds": request.seconds,
                "total_seconds": total_seconds
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en toggle_load: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/cancel_temp_off")
async def cancel_temporary_off(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Cancelar el apagado temporal de la carga
    """
    try:
        success = await manager.cancel_temporary_off()
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error enviando comando al ESP32"
            )
        
        # Invalidar cache
        data_cache.invalidate("all_data")
        
        return {
            "success": True,
            "message": "Apagado temporal cancelado correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cancelando apagado temporal: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/status")
async def get_actions_status(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Obtener estado actual de las acciones
    """
    try:
        data = await manager.get_data()
        if not data:
            raise HTTPException(status_code=503, detail="Error comunicándose con ESP32")
        
        return {
            "temporary_load_off": data.temporaryLoadOff,
            "load_off_remaining_seconds": data.loadOffRemainingSeconds,
            "load_off_duration": data.loadOffDuration,
            "load_control_state": data.loadControlState,
            "charge_state": data.chargeState
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de acciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
