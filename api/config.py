#!/usr/bin/env python3
"""
Endpoints para configuración del ESP32
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from models.esp32_data import ConfigParameter
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger

router = APIRouter(prefix="/config", tags=["Configuration"])

# Parámetros configurables con validación
CONFIGURABLE_PARAMETERS = {
    "bulkVoltage": {"type": float, "min": 12.0, "max": 15.0},
    "absorptionVoltage": {"type": float, "min": 12.0, "max": 15.0},
    "floatVoltage": {"type": float, "min": 12.0, "max": 15.0},
    "batteryCapacity": {"type": float, "min": 1.0, "max": 1000.0},
    "thresholdPercentage": {"type": float, "min": 0.1, "max": 5.0},
    "maxAllowedCurrent": {"type": float, "min": 1000.0, "max": 15000.0},
    "isLithium": {"type": bool},
    "factorDivider": {"type": int, "min": 1, "max": 10},
    "useFuenteDC": {"type": bool},
    "fuenteDC_Amps": {"type": float, "min": 0.0, "max": 50.0},
}

async def get_esp32_manager() -> ESP32Manager:
    """Dependency para obtener ESP32Manager"""
    from main import esp32_manager
    return esp32_manager

def validate_parameter_value(parameter: str, value: Any) -> Any:
    """Validar valor de parámetro"""
    if parameter not in CONFIGURABLE_PARAMETERS:
        raise ValueError(f"Parámetro '{parameter}' no es configurable")
    
    config = CONFIGURABLE_PARAMETERS[parameter]
    expected_type = config["type"]
    
    # Validar tipo
    if not isinstance(value, expected_type):
        try:
            value = expected_type(value)
        except (ValueError, TypeError):
            raise ValueError(f"Valor debe ser de tipo {expected_type.__name__}")
    
    # Validar rango
    if "min" in config and value < config["min"]:
        raise ValueError(f"Valor mínimo: {config['min']}")
    
    if "max" in config and value > config["max"]:
        raise ValueError(f"Valor máximo: {config['max']}")
    
    return value

@router.get("/")
async def get_configurable_parameters():
    """
    Obtener lista de parámetros configurables
    """
    return {
        "configurable_parameters": list(CONFIGURABLE_PARAMETERS.keys()),
        "parameter_info": CONFIGURABLE_PARAMETERS
    }

@router.put("/{parameter_name}")
async def set_parameter(
    parameter_name: str,
    config: ConfigParameter,
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Configurar un parámetro específico
    """
    try:
        # Validar parámetro
        validated_value = validate_parameter_value(parameter_name, config.value)
        
        # Enviar al ESP32
        success = await manager.set_parameter(parameter_name, validated_value)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail=f"Error configurando {parameter_name} en ESP32"
            )
        
        # Invalidar cache relacionado
        data_cache.invalidate("all_data")
        data_cache.invalidate(f"param_{parameter_name}")
        
        return {
            "success": True,
            "parameter": parameter_name,
            "value": validated_value,
            "message": f"{parameter_name} configurado correctamente"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error configurando {parameter_name}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
