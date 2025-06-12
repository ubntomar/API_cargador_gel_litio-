#!/usr/bin/env python3
"""
Endpoints para Schedule Diario - ESP32 API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from models.schedule_models import (
    ScheduleConfigRequest, 
    ScheduleStatusResponse, 
    ScheduleInfoResponse,
    ToggleLoadExtendedRequest
)
from services.schedule_manager import ScheduleManager
from core.logger import logger
from core.dependencies import check_config_rate_limit, check_action_rate_limit, check_read_rate_limit

router = APIRouter(prefix="/schedule", tags=["Schedule"])

async def get_schedule_manager() -> ScheduleManager:
    """Dependency para obtener ScheduleManager"""
    from main import schedule_manager
    return schedule_manager

@router.get("/", response_model=ScheduleStatusResponse, dependencies=[Depends(check_read_rate_limit)])
async def get_schedule_status(manager: ScheduleManager = Depends(get_schedule_manager)):
    """
    Obtener estado actual del schedule diario
    """
    try:
        logger.debug("📊 Obteniendo estado del schedule")
        
        status = manager.get_status()
        
        return ScheduleStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado del schedule: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.put("/config", dependencies=[Depends(check_config_rate_limit)])
async def configure_schedule(
    config: ScheduleConfigRequest,
    manager: ScheduleManager = Depends(get_schedule_manager)
):
    """
    Configurar el schedule diario
    """
    try:
        logger.info(f"⚙️ Configurando schedule: {config.enabled}, {config.start_time}, {config.duration_seconds}s")
        
        success = manager.configure_schedule(
            enabled=config.enabled,
            start_time=config.start_time,
            duration_seconds=config.duration_seconds
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Error configurando schedule. Verifica los parámetros."
            )
        
        # Obtener estado actualizado
        status = manager.get_status()
        
        response = {
            "success": True,
            "message": "Schedule configurado correctamente",
            "config": {
                "enabled": config.enabled,
                "start_time": config.start_time,
                "duration_seconds": config.duration_seconds,
                "duration_hours": round(config.duration_seconds / 3600, 2)
            },
            "current_status": status
        }
        
        logger.info("✅ Schedule configurado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error configurando schedule: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/toggle", dependencies=[Depends(check_action_rate_limit)])
async def toggle_with_schedule_override(
    request: ToggleLoadExtendedRequest,
    manager: ScheduleManager = Depends(get_schedule_manager)
):
    """
    Toggle manual que puede anular el schedule diario
    """
    try:
        # Calcular tiempo total
        total_seconds = request.hours * 3600 + request.minutes * 60 + request.seconds
        
        logger.info(f"🔧 Toggle con override: {total_seconds}s, manual={request.is_manual_override}")
        
        # Obtener ESP32Manager
        from main import esp32_manager
        if not esp32_manager:
            raise HTTPException(status_code=503, detail="ESP32Manager no disponible")
        
        # Enviar comando al ESP32
        success = await esp32_manager.toggle_load(total_seconds)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error enviando comando al ESP32"
            )
        
        # Si es override manual, anular schedule
        if request.is_manual_override:
            manager.set_manual_override(total_seconds)
            logger.info("🔄 Schedule anulado por override manual")
        
        # Obtener estado actualizado
        schedule_status = manager.get_status()
        
        response = {
            "success": True,
            "message": f"Toggle ejecutado por {total_seconds} segundos",
            "toggle_info": {
                "hours": request.hours,
                "minutes": request.minutes,
                "seconds": request.seconds,
                "total_seconds": total_seconds,
                "is_manual_override": request.is_manual_override
            },
            "schedule_impact": {
                "schedule_cancelled": request.is_manual_override,
                "override_active": schedule_status.get("manual_override_active", False),
                "next_schedule": schedule_status.get("next_execution")
            }
        }
        
        logger.info("✅ Toggle con schedule ejecutado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en toggle con schedule: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/clear_override", dependencies=[Depends(check_action_rate_limit)])
async def clear_manual_override(manager: ScheduleManager = Depends(get_schedule_manager)):
    """
    Limpiar override manual (permitir que schedule funcione normalmente)
    """
    try:
        logger.info("🔄 Limpiando override manual")
        
        success = manager.clear_manual_override()
        
        if success:
            message = "Override manual limpiado correctamente"
        else:
            message = "No había override manual activo"
        
        # Obtener estado actualizado
        status = manager.get_status()
        
        response = {
            "success": True,
            "message": message,
            "current_status": status
        }
        
        logger.info("✅ Override manual procesado")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error limpiando override: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/info", response_model=ScheduleInfoResponse, dependencies=[Depends(check_read_rate_limit)])
async def get_schedule_info(manager: ScheduleManager = Depends(get_schedule_manager)):
    """
    Obtener información sobre las capacidades del schedule
    """
    try:
        info = manager.get_info()
        return ScheduleInfoResponse(**info)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info del schedule: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/enable", dependencies=[Depends(check_config_rate_limit)])
async def enable_schedule(manager: ScheduleManager = Depends(get_schedule_manager)):
    """
    Habilitar schedule con configuración actual
    """
    try:
        logger.info("🔛 Habilitando schedule")
        
        # Obtener configuración actual
        current_status = manager.get_status()
        
        # Habilitar con configuración actual
        success = manager.configure_schedule(
            enabled=True,
            start_time=current_status.get("start_time", "00:00"),
            duration_seconds=current_status.get("duration_seconds", 21600)
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Error habilitando schedule")
        
        # Obtener estado actualizado
        updated_status = manager.get_status()
        
        response = {
            "success": True,
            "message": "Schedule habilitado correctamente",
            "current_status": updated_status
        }
        
        logger.info("✅ Schedule habilitado")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error habilitando schedule: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/disable", dependencies=[Depends(check_config_rate_limit)])
async def disable_schedule(manager: ScheduleManager = Depends(get_schedule_manager)):
    """
    Deshabilitar schedule diario
    """
    try:
        logger.info("🔛 Deshabilitando schedule")
        
        # Obtener configuración actual
        current_status = manager.get_status()
        
        # Deshabilitar manteniendo configuración
        success = manager.configure_schedule(
            enabled=False,
            start_time=current_status.get("start_time", "00:00"),
            duration_seconds=current_status.get("duration_seconds", 21600)
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Error deshabilitando schedule")
        
        # Obtener estado actualizado
        updated_status = manager.get_status()
        
        response = {
            "success": True,
            "message": "Schedule deshabilitado correctamente",
            "current_status": updated_status
        }
        
        logger.info("✅ Schedule deshabilitado")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deshabilitando schedule: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")