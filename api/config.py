#!/usr/bin/env python3
"""
Endpoints para configuración del ESP32 - Versión Corregida
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from models.esp32_data import ConfigParameter
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger

router = APIRouter(prefix="/config", tags=["Configuration"])

# Parámetros configurables con validación CORREGIDA
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
    """Validar valor de parámetro - MEJORADO"""
    if parameter not in CONFIGURABLE_PARAMETERS:
        raise ValueError(f"Parámetro '{parameter}' no es configurable")
    
    config = CONFIGURABLE_PARAMETERS[parameter]
    expected_type = config["type"]
    
    # Validar tipo con mejor manejo de conversiones
    if not isinstance(value, expected_type):
        try:
            if expected_type == bool:
                # Manejo especial para booleanos
                if isinstance(value, str):
                    if value.lower() in ['true', '1', 'yes', 'on']:
                        value = True
                    elif value.lower() in ['false', '0', 'no', 'off']:
                        value = False
                    else:
                        raise ValueError(f"Valor booleano inválido: {value}")
                elif isinstance(value, (int, float)):
                    value = bool(value)
                else:
                    raise ValueError(f"No se puede convertir {type(value)} a boolean")
            elif expected_type == int:
                value = int(float(value))  # Permite "5.0" -> 5
            elif expected_type == float:
                value = float(value)
            else:
                value = expected_type(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Valor debe ser de tipo {expected_type.__name__}: {e}")
    
    # Validar rango para tipos numéricos
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
        "parameter_info": CONFIGURABLE_PARAMETERS,
        "total_configurable": len(CONFIGURABLE_PARAMETERS)
    }

@router.put("/{parameter_name}")
async def set_parameter(
    parameter_name: str,
    config: ConfigParameter,
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Configurar un parámetro específico - MEJORADO
    """
    try:
        logger.info(f"🔧 Recibida solicitud para configurar {parameter_name} = {config.value}")
        
        # Validar parámetro
        validated_value = validate_parameter_value(parameter_name, config.value)
        logger.info(f"✅ Valor validado: {parameter_name} = {validated_value} (tipo: {type(validated_value)})")
        
        # Enviar al ESP32
        success = await manager.set_parameter(parameter_name, validated_value)
        
        if not success:
            logger.error(f"❌ ESP32Manager retornó error para {parameter_name}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error configurando {parameter_name} en ESP32"
            )
        
        # Invalidar cache relacionado
        data_cache.invalidate("all_data")
        data_cache.invalidate(f"param_{parameter_name}")
        
        response = {
            "success": True,
            "parameter": parameter_name,
            "value": validated_value,
            "value_type": type(validated_value).__name__,
            "message": f"{parameter_name} configurado correctamente"
        }
        
        logger.info(f"✅ {parameter_name} configurado exitosamente a {validated_value}")
        return response
        
    except ValueError as e:
        logger.error(f"❌ Error de validación para {parameter_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado configurando {parameter_name}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{parameter_name}")
async def get_parameter_info(parameter_name: str):
    """
    Obtener información sobre un parámetro específico
    """
    if parameter_name not in CONFIGURABLE_PARAMETERS:
        raise HTTPException(
            status_code=404, 
            detail=f"Parámetro '{parameter_name}' no encontrado o no es configurable"
        )
    
    param_info = CONFIGURABLE_PARAMETERS[parameter_name].copy()
    param_info["name"] = parameter_name
    param_info["configurable"] = True
    
    return {
        "parameter": parameter_name,
        "info": param_info
    }

@router.post("/validate")
async def validate_parameter_endpoint(parameter_name: str, config: ConfigParameter):
    """
    Validar un valor sin enviarlo al ESP32 (dry-run)
    """
    try:
        validated_value = validate_parameter_value(parameter_name, config.value)
        
        return {
            "valid": True,
            "parameter": parameter_name,
            "original_value": config.value,
            "validated_value": validated_value,
            "value_type": type(validated_value).__name__,
            "message": "Validación exitosa"
        }
        
    except ValueError as e:
        return {
            "valid": False,
            "parameter": parameter_name,
            "original_value": config.value,
            "error": str(e),
            "message": "Validación fallida"
        }