#!/usr/bin/env python3
"""
Endpoints para acciones de control del ESP32 - CON INTEGRACIÓN SCHEDULE
"""

from fastapi import APIRouter, HTTPException, Depends
from models.esp32_data import ToggleLoadRequest
from models.schedule_models import ToggleLoadExtendedRequest
from services.esp32_manager import ESP32Manager
from services.schedule_manager import ScheduleManager
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

async def get_schedule_manager() -> ScheduleManager:
    """Dependency para obtener ScheduleManager"""
    from main import schedule_manager
    return schedule_manager

@router.post("/toggle_load", dependencies=[Depends(check_action_rate_limit)])
async def toggle_load(
    request: ToggleLoadRequest,
    manager: ESP32Manager = Depends(get_esp32_manager),
    schedule_mgr: ScheduleManager = Depends(get_schedule_manager)
):
    """
    Apagar la carga temporalmente - INTEGRADO CON SCHEDULE
    
    IMPORTANTE: Este toggle manual anula cualquier schedule diario activo
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
        
        # ✅ NUEVO: Límite de 8 horas
        if total_seconds > 28800:  # 8 horas
            raise HTTPException(
                status_code=400,
                detail="Duración máxima: 8 horas (28800 segundos)"
            )
        
        # ✅ NUEVO: Verificar si hay schedule activo
        schedule_was_active = False
        if schedule_mgr:
            schedule_status = schedule_mgr.get_status()
            schedule_was_active = schedule_status.get("currently_active", False)
        
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
        
        # ✅ NUEVO: Establecer override manual en schedule
        schedule_impact = {"schedule_cancelled": False, "was_active": schedule_was_active}
        if schedule_mgr:
            schedule_mgr.set_manual_override(total_seconds)
            schedule_impact["schedule_cancelled"] = True
            logger.info("🔄 Schedule anulado por toggle manual")
        
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
            },
            "schedule_impact": schedule_impact,
            "note": "Este comando manual anula cualquier schedule diario hasta mañana"
        }
        
        logger.info(f"✅ Toggle load exitoso: {total_seconds}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en toggle_load: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/cancel_temp_off", dependencies=[Depends(check_action_rate_limit)])
async def cancel_temporary_off(
    manager: ESP32Manager = Depends(get_esp32_manager),
    schedule_mgr: ScheduleManager = Depends(get_schedule_manager)
):
    """
    Cancelar el apagado temporal de la carga - INTEGRADO CON SCHEDULE
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
        
        # ✅ NUEVO: NO limpiar override automáticamente
        # El usuario debe decidir si quiere reactivar el schedule
        schedule_info = {}
        if schedule_mgr:
            schedule_status = schedule_mgr.get_status()
            schedule_info = {
                "override_still_active": schedule_status.get("manual_override_active", False),
                "note": "Para reactivar schedule, usar /schedule/clear_override"
            }
        
        # Invalidar cache
        data_cache.invalidate("all_data")
        
        response = {
            "success": True,
            "message": "Apagado temporal cancelado correctamente",
            "schedule_info": schedule_info
        }
        
        logger.info("✅ Apagado temporal cancelado exitosamente")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado cancelando apagado temporal: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/status", dependencies=[Depends(check_read_rate_limit)])
async def get_actions_status(
    manager: ESP32Manager = Depends(get_esp32_manager),
    schedule_mgr: ScheduleManager = Depends(get_schedule_manager)
):
    """
    Obtener estado actual de las acciones - CON INFORMACIÓN DE SCHEDULE
    """
    try:
        logger.debug("📊 Obteniendo estado de acciones")
        
        # ✅ NUEVO: Verificación rápida de conexión sin bloqueo
        connection_info = manager.get_connection_info()
        if not connection_info.get("connected", False):
            logger.warning("⚠️ ESP32Manager no está conectado")
            
            # ✅ NUEVO: Retornar estado parcial en lugar de error
            base_response = {
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
            
            # Agregar info de schedule si está disponible
            if schedule_mgr:
                try:
                    schedule_status = schedule_mgr.get_status()
                    base_response["schedule"] = schedule_status
                except Exception:
                    base_response["schedule"] = {"error": "Schedule manager error"}
            
            return base_response
        
        # ✅ NUEVO: Timeout agresivo para prevenir congelamiento
        try:
            data = await asyncio.wait_for(
                manager.get_data(), 
                timeout=5.0  # Solo 5 segundos para status
            )
        except asyncio.TimeoutError:
            logger.error("❌ Timeout obteniendo datos para status")
            
            # ✅ NUEVO: Retornar estado de error en lugar de excepción
            error_response = {
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
            
            # Agregar schedule info
            if schedule_mgr:
                try:
                    schedule_status = schedule_mgr.get_status()
                    error_response["schedule"] = schedule_status
                except Exception:
                    error_response["schedule"] = {"error": "Schedule timeout"}
            
            return error_response
        
        if not data:
            logger.error("❌ No se pudieron obtener datos del ESP32")
            
            # ✅ NUEVO: Retornar estado parcial en lugar de error 503
            error_response = {
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
            
            if schedule_mgr:
                try:
                    schedule_status = schedule_mgr.get_status()
                    error_response["schedule"] = schedule_status
                except Exception:
                    error_response["schedule"] = {"error": "Schedule error"}
            
            return error_response
        
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
            
            # ✅ NUEVO: Agregar información de schedule
            if schedule_mgr:
                try:
                    schedule_status = schedule_mgr.get_status()
                    actions_status["schedule"] = schedule_status
                    
                    # Agregar contexto de interacción
                    actions_status["interaction_context"] = {
                        "manual_override_active": schedule_status.get("manual_override_active", False),
                        "schedule_enabled": schedule_status.get("enabled", False),
                        "schedule_currently_active": schedule_status.get("currently_active", False)
                    }
                except Exception as e:
                    actions_status["schedule"] = {"error": f"Schedule error: {str(e)}"}
            
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
            
            if schedule_mgr:
                try:
                    schedule_status = schedule_mgr.get_status()
                    actions_status["schedule"] = schedule_status
                except Exception:
                    actions_status["schedule"] = {"error": "Schedule parse error"}
        
        logger.debug(f"✅ Estado de acciones obtenido: temporaryLoadOff={actions_status.get('temporary_load_off')}")
        return actions_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado obteniendo estado de acciones: {e}")
        
        # ✅ NUEVO: En lugar de error 500, retornar estado de error
        error_response = {
            "esp32_connected": False,
            "temporary_load_off": None,
            "load_off_remaining_seconds": None,
            "load_off_duration": None,
            "load_control_state": None,
            "charge_state": "SYSTEM_ERROR",
            "last_update": None,
            "error": f"Error interno: {str(e)}"
        }
        
        # Intentar obtener schedule status
        if schedule_mgr:
            try:
                schedule_status = schedule_mgr.get_status()
                error_response["schedule"] = schedule_status
            except Exception:
                error_response["schedule"] = {"error": "Schedule system error"}
        
        return error_response

@router.get("/info")
async def get_actions_info():
    """
    Obtener información sobre las acciones disponibles - CON SCHEDULE
    """
    return {
        "available_actions": [
            {
                "name": "toggle_load",
                "method": "POST",
                "endpoint": "/actions/toggle_load",
                "description": "Apagar carga temporalmente (anula schedule diario)",
                "parameters": {
                    "hours": "0-8",
                    "minutes": "0-59", 
                    "seconds": "0-59"
                },
                "constraints": {
                    "min_duration": "1 segundo total",
                    "max_duration": "8 horas (28800 segundos)"
                },
                "schedule_impact": "Anula schedule diario hasta el siguiente día"
            },
            {
                "name": "cancel_temp_off",
                "method": "POST",
                "endpoint": "/actions/cancel_temp_off",
                "description": "Cancelar apagado temporal",
                "parameters": "none",
                "schedule_impact": "No afecta override manual (usar /schedule/clear_override)"
            }
        ],
        "schedule_integration": {
            "toggle_behavior": "Manual toggle cancela schedule hasta siguiente día",
            "max_duration": "8 horas para cualquier comando",
            "priority": "Toggle manual > Schedule diario > LVD/LVR",
            "endpoints": {
                "schedule_status": "/schedule/",
                "clear_override": "/schedule/clear_override",
                "configure_schedule": "/schedule/config"
            }
        },
        "status_endpoints": [
            {
                "name": "status",
                "method": "GET",
                "endpoint": "/actions/status",
                "description": "Estado actual de acciones y schedule"
            },
            {
                "name": "info",
                "method": "GET", 
                "endpoint": "/actions/info",
                "description": "Información sobre acciones disponibles"
            }
        ]
    }