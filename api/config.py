#!/usr/bin/env python3
"""
Endpoints para configuración del ESP32 - ERROR JSON CORREGIDO
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from models.esp32_data import ConfigParameter
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger
from core.dependencies import check_config_rate_limit

router = APIRouter(prefix="/config", tags=["Configuration"])

# ✅ CORREGIDO: Usar strings en lugar de tipos Python para evitar error de serialización JSON
CONFIGURABLE_PARAMETERS = {
    # Parámetros de voltaje
    "bulkVoltage": {"type": "float", "min": 12.0, "max": 15.0, "description": "Voltaje BULK (V)"},
    "absorptionVoltage": {"type": "float", "min": 12.0, "max": 15.0, "description": "Voltaje ABSORCIÓN (V)"},
    "floatVoltage": {"type": "float", "min": 12.0, "max": 15.0, "description": "Voltaje FLOTACIÓN (V)"},
    
    # Parámetros de batería
    "batteryCapacity": {"type": "float", "min": 1.0, "max": 1000.0, "description": "Capacidad batería (Ah)"},
    "thresholdPercentage": {"type": "float", "min": 0.1, "max": 5.0, "description": "Umbral corriente (%)"},
    "maxAllowedCurrent": {"type": "float", "min": 1000.0, "max": 15000.0, "description": "Corriente máxima (mA)"},
    "isLithium": {"type": "bool", "description": "Tipo batería (true=Litio, false=GEL)"},
    "factorDivider": {"type": "int", "min": 1, "max": 10, "description": "Factor divisor"},
    
    # Parámetros de fuente
    "useFuenteDC": {"type": "bool", "description": "Usar fuente DC"},
    "fuenteDC_Amps": {"type": "float", "min": 0.0, "max": 50.0, "description": "Amperaje fuente DC (A)"},
    
    # Parámetros de control PWM
    "currentPWM": {"type": "int", "min": 0, "max": 255, "description": "Valor PWM directo (0-255)"},
    "pwmPercentage": {"type": "float", "min": 0.0, "max": 100.0, "description": "PWM en porcentaje (0-100%)"},
}

# ✅ CORREGIDO: Mapeo de strings a tipos Python para validación
TYPE_MAPPING = {
    "float": float,
    "int": int,
    "bool": bool,
    "str": str
}

async def get_esp32_manager() -> ESP32Manager:
    """Dependency para obtener ESP32Manager"""
    from main import esp32_manager
    return esp32_manager

def validate_parameter_value(parameter: str, value: Any) -> Any:
    """Validar valor de parámetro - CON MAPEO DE TIPOS CORREGIDO"""
    if parameter not in CONFIGURABLE_PARAMETERS:
        raise ValueError(f"Parámetro '{parameter}' no es configurable")
    
    config = CONFIGURABLE_PARAMETERS[parameter]
    type_str = config["type"]
    
    # ✅ CORREGIDO: Obtener tipo Python desde string
    if type_str not in TYPE_MAPPING:
        raise ValueError(f"Tipo no soportado: {type_str}")
    
    expected_type = TYPE_MAPPING[type_str]
    
    logger.debug(f"🔍 Validando {parameter}: {value} (tipo recibido: {type(value)})")
    
    # Conversiones de tipo mejoradas
    if not isinstance(value, expected_type):
        try:
            if expected_type == bool:
                # Manejo robusto de booleanos
                if isinstance(value, str):
                    value_lower = value.lower().strip()
                    if value_lower in ['true', '1', 'yes', 'on', 'si', 'sí']:
                        value = True
                    elif value_lower in ['false', '0', 'no', 'off']:
                        value = False
                    else:
                        raise ValueError(f"Valor booleano inválido: '{value}'. Use: true/false, 1/0, yes/no")
                elif isinstance(value, (int, float)):
                    value = bool(value)
                else:
                    raise ValueError(f"No se puede convertir {type(value).__name__} a boolean")
                    
            elif expected_type == int:
                # Permitir conversión de float a int (ej: 5.0 -> 5)
                if isinstance(value, float) and value.is_integer():
                    value = int(value)
                else:
                    value = int(value)
                    
            elif expected_type == float:
                value = float(value)
            else:
                value = expected_type(value)
                
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error convirtiendo '{value}' a {expected_type.__name__}: {str(e)}")
    
    # Validar rango para tipos numéricos
    if expected_type in [int, float]:
        if "min" in config and value < config["min"]:
            raise ValueError(f"Valor mínimo para {parameter}: {config['min']} (recibido: {value})")
        
        if "max" in config and value > config["max"]:
            raise ValueError(f"Valor máximo para {parameter}: {config['max']} (recibido: {value})")
    
    # Validaciones especiales para PWM
    if parameter == "currentPWM":
        if not (0 <= value <= 255):
            raise ValueError(f"PWM debe estar entre 0-255 (recibido: {value})")
    
    elif parameter == "pwmPercentage":
        if not (0.0 <= value <= 100.0):
            raise ValueError(f"PWM porcentaje debe estar entre 0-100% (recibido: {value})")
    
    logger.debug(f"✅ Validación exitosa: {parameter} = {value} ({type(value).__name__})")
    return value

@router.get("/")
async def get_configurable_parameters():
    """Obtener lista de parámetros configurables - JSON SERIALIZABLE"""
    return {
        "configurable_parameters": list(CONFIGURABLE_PARAMETERS.keys()),
        "parameter_info": CONFIGURABLE_PARAMETERS,
        "total_configurable": len(CONFIGURABLE_PARAMETERS),
        "pwm_controls": {
            "currentPWM": {
                "description": "Control directo de PWM (0-255)",
                "range": "0-255",
                "note": "Valor directo enviado al ESP32"
            },
            "pwmPercentage": {
                "description": "Control PWM en porcentaje (0-100%)",
                "range": "0.0-100.0",
                "note": "Se convierte automáticamente a 0-255"
            }
        },
        "examples": {
            "batteryCapacity": {"valid": [7.0, 50.0, 100.0], "invalid": [-1, 1001]},
            "isLithium": {"valid": [True, False, "true", "false", 1, 0], "invalid": ["maybe", 2]},
            "currentPWM": {"valid": [0, 128, 255], "invalid": [-1, 256]},
            "pwmPercentage": {"valid": [0.0, 25.0, 50.0, 75.0, 100.0], "invalid": [-1.0, 101.0]},
            "thresholdPercentage": {"valid": [1.0, 3.0, 5.0], "invalid": [0, 6]},
            "factorDivider": {"valid": [1, 5, 10], "invalid": [0, 11]}
        }
    }

@router.put("/{parameter_name}")
async def set_parameter(
    parameter_name: str,
    config: ConfigParameter,
    _: None = Depends(check_config_rate_limit),
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """Configurar un parámetro específico"""
    try:
        logger.info(f"🔧 Solicitud configuración: {parameter_name} = {config.value} (tipo: {type(config.value)})")
        
        # Validación
        try:
            validated_value = validate_parameter_value(parameter_name, config.value)
        except ValueError as ve:
            logger.error(f"❌ Error de validación para {parameter_name}: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))
        
        logger.info(f"✅ Valor validado: {parameter_name} = {validated_value} (tipo: {type(validated_value)})")
        
        # Verificar conexión ESP32
        if not manager.connected:
            logger.error(f"❌ ESP32Manager no está conectado")
            raise HTTPException(
                status_code=503, 
                detail="ESP32 no está conectado. Verifica la conexión serial."
            )
        
        # Logging especial para PWM
        if parameter_name in ["currentPWM", "pwmPercentage"]:
            logger.warning(f"🎛️ CONTROL PWM: {parameter_name} = {validated_value}")
            logger.warning("⚠️ ADVERTENCIA: El control manual de PWM puede afectar la carga automática")
        
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
        
        # Respuesta mejorada con información PWM
        response = {
            "success": True,
            "parameter": parameter_name,
            "original_value": config.value,
            "validated_value": validated_value,
            "value_type": type(validated_value).__name__,
            "message": f"{parameter_name} configurado correctamente"
        }
        
        # Agregar información adicional para PWM
        if parameter_name == "pwmPercentage":
            pwm_direct = int((validated_value / 100.0) * 255.0)
            response["pwm_conversion"] = {
                "percentage": validated_value,
                "direct_value": pwm_direct,
                "note": f"{validated_value}% = {pwm_direct}/255"
            }
        elif parameter_name == "currentPWM":
            pwm_percentage = round((validated_value / 255.0) * 100.0, 1)
            response["pwm_conversion"] = {
                "direct_value": validated_value,
                "percentage": pwm_percentage,
                "note": f"{validated_value}/255 = {pwm_percentage}%"
            }
        
        logger.info(f"✅ {parameter_name} configurado exitosamente: {config.value} → {validated_value}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado configurando {parameter_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{parameter_name}")
async def get_parameter_info(parameter_name: str):
    """Obtener información sobre un parámetro específico"""
    if parameter_name not in CONFIGURABLE_PARAMETERS:
        raise HTTPException(
            status_code=404, 
            detail=f"Parámetro '{parameter_name}' no encontrado o no es configurable"
        )
    
    param_info = CONFIGURABLE_PARAMETERS[parameter_name].copy()
    param_info["name"] = parameter_name
    param_info["configurable"] = True
    
    # Agregar ejemplos específicos
    examples = {
        "batteryCapacity": {"valid_examples": [7.0, 50.0, 100.0], "unit": "Ah"},
        "isLithium": {"valid_examples": [True, False, "true", "false"], "note": "Tipo de batería"},
        "thresholdPercentage": {"valid_examples": [1.0, 2.5, 3.0], "unit": "%"},
        "maxAllowedCurrent": {"valid_examples": [3000.0, 6000.0, 8000.0], "unit": "mA"},
        "bulkVoltage": {"valid_examples": [14.2, 14.4, 14.6], "unit": "V"},
        
        # Ejemplos para PWM
        "currentPWM": {
            "valid_examples": [0, 64, 128, 192, 255],
            "unit": "raw_value",
            "note": "0=0%, 64=25%, 128=50%, 192=75%, 255=100%",
            "conversion": "direct_to_esp32"
        },
        "pwmPercentage": {
            "valid_examples": [0.0, 25.0, 50.0, 75.0, 100.0],
            "unit": "%",
            "note": "Se convierte automáticamente a 0-255",
            "conversion": "percentage_to_raw"
        }
    }
    
    if parameter_name in examples:
        param_info.update(examples[parameter_name])
    
    return {
        "parameter": parameter_name,
        "info": param_info
    }

@router.post("/validate")
async def validate_parameter_endpoint(
    parameter_name: str, 
    config: ConfigParameter,
    _: None = Depends(check_config_rate_limit)
):
    """Validar un valor sin enviarlo al ESP32 (dry-run)"""
    try:
        validated_value = validate_parameter_value(parameter_name, config.value)
        
        response = {
            "valid": True,
            "parameter": parameter_name,
            "original_value": config.value,
            "original_type": type(config.value).__name__,
            "validated_value": validated_value,
            "validated_type": type(validated_value).__name__,
            "conversion_applied": type(config.value) != type(validated_value),
            "message": "Validación exitosa - valor puede ser configurado"
        }
        
        # Información adicional para PWM
        if parameter_name == "pwmPercentage":
            pwm_direct = int((validated_value / 100.0) * 255.0)
            response["pwm_preview"] = {
                "percentage": validated_value,
                "raw_value": pwm_direct,
                "formula": f"{validated_value}% * 255 / 100 = {pwm_direct}"
            }
        elif parameter_name == "currentPWM":
            pwm_percentage = round((validated_value / 255.0) * 100.0, 1)
            response["pwm_preview"] = {
                "raw_value": validated_value,
                "percentage": pwm_percentage,
                "formula": f"{validated_value} / 255 * 100 = {pwm_percentage}%"
            }
        
        return response
        
    except ValueError as e:
        return {
            "valid": False,
            "parameter": parameter_name,
            "original_value": config.value,
            "original_type": type(config.value).__name__,
            "error": str(e),
            "message": "Validación fallida - corrige el valor antes de configurar",
            "suggestions": _get_parameter_suggestions(parameter_name)
        }

def _get_parameter_suggestions(parameter_name: str) -> Dict[str, Any]:
    """Obtener sugerencias para un parámetro específico"""
    suggestions = {
        "batteryCapacity": {
            "range": "1.0 - 1000.0 Ah",
            "common_values": [7.0, 50.0, 100.0, 200.0],
            "note": "Capacidad de tu batería en Amperios-hora"
        },
        "isLithium": {
            "valid_formats": ["true", "false", True, False, 1, 0],
            "note": "true para baterías de Litio, false para GEL/AGM"
        },
        "thresholdPercentage": {
            "range": "0.1 - 5.0 %",
            "recommended": "2.0 - 3.0 para la mayoría de baterías",
            "note": "Porcentaje de corriente para cambio de etapa"
        },
        
        # Sugerencias para PWM
        "currentPWM": {
            "range": "0 - 255",
            "common_values": [0, 64, 128, 192, 255],
            "note": "Valor directo de PWM (0=apagado, 255=máximo)",
            "warning": "Usar con cuidado - puede afectar la carga automática"
        },
        "pwmPercentage": {
            "range": "0.0 - 100.0 %",
            "common_values": [0.0, 25.0, 50.0, 75.0, 100.0],
            "note": "Porcentaje de PWM (se convierte a 0-255)",
            "warning": "Usar con cuidado - puede afectar la carga automática"
        }
    }
    
    return suggestions.get(parameter_name, {"note": "Consulta la documentación para valores válidos"})

@router.post("/batch")
async def set_multiple_parameters(
    parameters: Dict[str, Any],
    _: None = Depends(check_config_rate_limit),
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """Configurar múltiples parámetros de una vez"""
    results = {}
    successful = 0
    failed = 0
    pwm_commands = []
    
    for param_name, param_value in parameters.items():
        try:
            # Validar parámetro
            validated_value = validate_parameter_value(param_name, param_value)
            
            # Rastrear comandos PWM
            if param_name in ["currentPWM", "pwmPercentage"]:
                pwm_commands.append(f"{param_name}={validated_value}")
            
            # Configurar en ESP32
            success = await manager.set_parameter(param_name, validated_value)
            
            if success:
                results[param_name] = {
                    "success": True,
                    "original_value": param_value,
                    "validated_value": validated_value
                }
                successful += 1
            else:
                results[param_name] = {
                    "success": False,
                    "error": "Error comunicando con ESP32"
                }
                failed += 1
                
        except ValueError as e:
            results[param_name] = {
                "success": False,
                "error": f"Validación fallida: {str(e)}"
            }
            failed += 1
        except Exception as e:
            results[param_name] = {
                "success": False,
                "error": f"Error inesperado: {str(e)}"
            }
            failed += 1
    
    # Invalidar cache si hubo cambios exitosos
    if successful > 0:
        data_cache.invalidate("all_data")
    
    response = {
        "results": results,
        "summary": {
            "total_parameters": len(parameters),
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/len(parameters)*100):.1f}%"
        }
    }
    
    # Advertencia si se configuraron PWM
    if pwm_commands:
        response["pwm_warning"] = {
            "commands_sent": pwm_commands,
            "warning": "Se enviaron comandos PWM manuales que pueden afectar la carga automática",
            "recommendation": "Monitorea el sistema después de cambios PWM"
        }
    
    return response

# Endpoint específico para control PWM
@router.post("/pwm/control")
async def pwm_control(
    pwm_type: str,  # "direct" o "percentage" 
    value: float,
    _: None = Depends(check_config_rate_limit),
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """Control directo de PWM con validaciones especiales"""
    try:
        if pwm_type == "direct":
            parameter = "currentPWM"
            if not (0 <= value <= 255):
                raise HTTPException(status_code=400, detail="PWM directo debe estar entre 0-255")
            validated_value = int(value)
            
        elif pwm_type == "percentage":
            parameter = "pwmPercentage"
            if not (0.0 <= value <= 100.0):
                raise HTTPException(status_code=400, detail="PWM porcentaje debe estar entre 0-100%")
            validated_value = float(value)
            
        else:
            raise HTTPException(status_code=400, detail="pwm_type debe ser 'direct' o 'percentage'")
        
        logger.warning(f"🎛️ CONTROL PWM DIRECTO: {pwm_type} = {validated_value}")
        
        # Enviar al ESP32
        success = await manager.set_parameter(parameter, validated_value)
        
        if not success:
            raise HTTPException(status_code=500, detail="Error enviando comando PWM al ESP32")
        
        data_cache.invalidate("all_data")
        
        response = {
            "success": True,
            "pwm_type": pwm_type,
            "value_sent": validated_value,
            "parameter_used": parameter,
            "warning": "Control PWM manual puede afectar la carga automática",
            "message": f"PWM configurado: {pwm_type} = {validated_value}"
        }
        
        if pwm_type == "percentage":
            direct_value = int((validated_value / 100.0) * 255.0)
            response["conversion"] = {
                "percentage": validated_value,
                "direct_equivalent": direct_value
            }
        elif pwm_type == "direct":
            percentage = round((validated_value / 255.0) * 100.0, 1)
            response["conversion"] = {
                "direct": validated_value,
                "percentage_equivalent": percentage
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en control PWM: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")