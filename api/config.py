#!/usr/bin/env python3
"""
Endpoints para configuración del ESP32 - ERROR JSON CORREGIDO
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
from models.esp32_data import ConfigParameter
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger
from core.dependencies import check_config_rate_limit

# NUEVO: Importar modelos y servicio para configuraciones personalizadas
from models.custom_configurations import (
    ConfigurationData,
    ConfigurationRequest,
    ConfigurationResponse,
    ConfigurationsListResponse,
    ConfigurationApplyRequest,
    ConfigurationValidationResponse,
    ConfigurationExportResponse,
    ConfigurationImportRequest,
    ConfigurationImportResponse,
    CustomConfiguration
)
from services.custom_configuration_manager_redis import CustomConfigurationManagerRedis

router = APIRouter(prefix="/config", tags=["Configuration"])

# NUEVO: Instancia global del gestor de configuraciones personalizadas con Redis
custom_config_manager = CustomConfigurationManagerRedis()

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
        esp32_result = await manager.set_parameter(parameter_name, validated_value)
        
        if not esp32_result["success"]:
            error_detail = esp32_result.get("error", "Error desconocido")
            logger.error(f"❌ ESP32Manager retornó error para {parameter_name}: {error_detail}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error configurando {parameter_name} en ESP32: {error_detail}"
            )
        
        # Invalidar cache relacionado
        data_cache.invalidate("all_data")
        data_cache.invalidate(f"param_{parameter_name}")
        
        # Respuesta mejorada con información PWM y del ESP32
        response = {
            "success": True,
            "parameter": parameter_name,
            "original_value": config.value,
            "validated_value": validated_value,
            "value_type": type(validated_value).__name__,
            "message": f"{parameter_name} configurado correctamente",
            "esp32_response": esp32_result.get("response", "OK")
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

@router.post("/parameter")
async def set_parameter_post(
    request: dict,
    _: None = Depends(check_config_rate_limit),
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """Configurar un parámetro usando POST - Compatible con Frontend"""
    try:
        # Extraer parameter y value del request body
        if "parameter" not in request or "value" not in request:
            raise HTTPException(
                status_code=400, 
                detail="Request body debe contener 'parameter' y 'value'"
            )
        
        parameter_name = request["parameter"]
        value = request["value"]
        
        logger.info(f"🔧 Solicitud POST /parameter: {parameter_name} = {value} (tipo: {type(value)})")
        
        # Reutilizar la lógica de validación existente
        try:
            validated_value = validate_parameter_value(parameter_name, value)
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
        esp32_result = await manager.set_parameter(parameter_name, validated_value)
        
        if not esp32_result["success"]:
            error_detail = esp32_result.get("error", "Error desconocido")
            logger.error(f"❌ ESP32Manager retornó error para {parameter_name}: {error_detail}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error configurando {parameter_name} en ESP32: {error_detail}"
            )
        
        # Invalidar cache relacionado
        data_cache.invalidate("all_data")
        data_cache.invalidate(f"param_{parameter_name}")
        
        # Respuesta compatible con frontend
        response = {
            "success": True,
            "parameter": parameter_name,
            "value": validated_value,
            "esp32_response": esp32_result.get("response", "OK"),
            "message": f"{parameter_name} configurado correctamente"
        }
        
        logger.info(f"✅ POST /parameter exitoso: {parameter_name} = {value} → {validated_value}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado en POST /parameter: {e}")
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
            esp32_result = await manager.set_parameter(param_name, validated_value)
            
            if esp32_result["success"]:
                results[param_name] = {
                    "success": True,
                    "original_value": param_value,
                    "validated_value": validated_value,
                    "esp32_response": esp32_result.get("response", "OK")
                }
                successful += 1
            else:
                results[param_name] = {
                    "success": False,
                    "error": esp32_result.get("error", "Error comunicando con ESP32"),
                    "esp32_response": esp32_result.get("response")
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
        esp32_result = await manager.set_parameter(parameter, validated_value)
        
        if not esp32_result["success"]:
            error_detail = esp32_result.get("error", "Error desconocido")
            raise HTTPException(
                status_code=500, 
                detail=f"Error enviando comando PWM al ESP32: {error_detail}"
            )
        
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

# ================================================================
# NUEVO: ENDPOINTS PARA CONFIGURACIONES PERSONALIZADAS
# ================================================================

@router.post("/custom/configurations", response_model=ConfigurationResponse)
async def save_configurations(config_data: ConfigurationData):
    """
    Guardar archivo de configuraciones personalizadas
    
    Permite guardar múltiples configuraciones como un archivo JSON.
    Las configuraciones incluyen todos los parámetros necesarios para
    diferentes tipos de baterías y casos de uso específicos.
    """
    try:
        logger.info("💾 Guardando configuraciones personalizadas...")
        
        # Convertir los datos del diccionario a objetos CustomConfiguration
        configurations_dict = {}
        for config_name, config_raw_data in config_data.data.items():
            try:
                # Crear objeto CustomConfiguration desde los datos raw
                configuration = CustomConfiguration(**config_raw_data)
                configurations_dict[config_name] = configuration
                logger.debug(f"✅ Configuración '{config_name}' validada correctamente")
            except Exception as e:
                logger.error(f"❌ Error validando configuración '{config_name}': {e}")
                raise ValueError(f"Error en configuración '{config_name}': {str(e)}")
        
        # Guardar usando el manager
        result = await custom_config_manager.save_configurations(configurations_dict)
        
        logger.info("✅ Configuraciones guardadas exitosamente")
        
        return ConfigurationResponse(
            message=result["message"],
            status=result["status"]
        )
        
    except ValueError as ve:
        logger.error(f"❌ Error de validación: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Error guardando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ============= RUTAS ESPECÍFICAS (antes de las dinámicas) =============
@router.post("/custom/configurations/validate", response_model=ConfigurationValidationResponse)
async def validate_configuration(configuration: CustomConfiguration):
    """
    Validar una configuración
    
    Valida que una configuración tenga todos los parámetros
    requeridos y valores válidos antes de guardarla.
    
    Request body debe contener directamente los parámetros de configuración.
    """
    try:
        logger.info("🔍 Validando configuración...")
        result = await custom_config_manager.validate_configuration(configuration)
        # Loguear usando el dict directamente
        logger.info(f"✅ Validación completada: {'exitosa' if result.get('is_valid') else 'falló'}")
        # Devolver el modelo Pydantic
        from models.custom_configurations import ConfigurationValidationResponse
        return ConfigurationValidationResponse(**result)
    except Exception as e:
        logger.error(f"❌ Error validando configuración: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/custom/configurations/export")
async def export_configurations():
    """
    Exportar configuraciones a JSON
    
    Genera un archivo JSON con todas las configuraciones
    guardadas para portabilidad entre dispositivos.
    
    Respuesta compatible con documentación frontend.
    """
    try:
        logger.info("📤 Exportando configuraciones...")
        
        # Obtener configuraciones del manager
        configurations = await custom_config_manager.load_configurations()
        
        # Preparar respuesta según documentación frontend
        exported_at = datetime.now().isoformat()
        
        export_response = {
            "export_info": {
                "total_configurations": len(configurations),
                "exported_at": exported_at,
                "version": "1.0"
            },
            "configurations": configurations
        }
        
        logger.info(f"✅ Exportadas {len(configurations)} configuraciones")
        
        return export_response
        
    except Exception as e:
        logger.error(f"❌ Error exportando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/custom/configurations/import", response_model=ConfigurationImportResponse)
async def import_configurations(import_request: ConfigurationImportRequest):
    """
    Importar configuraciones desde JSON
    
    Importa configuraciones desde un archivo JSON exportado,
    con opción de sobrescribir configuraciones existentes.
    """
    try:
        logger.info("📥 Importando configuraciones...")
        
        # Convertir los datos del diccionario a formato que espera el manager
        configurations_dict = {}
        for config_name, config_raw_data in import_request.configurations_data.items():
            try:
                # Crear objeto CustomConfiguration desde los datos raw
                configuration = CustomConfiguration(**config_raw_data)
                configurations_dict[config_name] = configuration
                logger.debug(f"✅ Configuración de importación '{config_name}' validada")
            except Exception as e:
                logger.error(f"❌ Error validando configuración de importación '{config_name}': {e}")
                raise ValueError(f"Error en configuración '{config_name}': {str(e)}")
        
        result = await custom_config_manager.import_configurations(
            configurations_dict,
            import_request.overwrite_existing
        )
        
        logger.info(f"✅ Importación completada: {result.imported_count} importadas, " \
                   f"{result.skipped_count} omitidas")
        
        return result
        
    except ValueError as ve:
        logger.error(f"❌ Error de validación en importación: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Error importando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/custom/configurations/info")
async def get_configurations_info():
    """
    Obtener información del sistema de configuraciones
    
    Retorna información sobre el archivo de configuraciones,
    estadísticas y estado del sistema.
    """
    try:
        logger.info("ℹ️ Obteniendo información del sistema de configuraciones...")
        
        # Información del archivo
        file_info = custom_config_manager.get_file_info()
        
        # Cargar configuraciones para estadísticas
        configurations = await custom_config_manager.load_configurations()
        
        # Estadísticas básicas
        stats = {
            "total_configurations": len(configurations),
            "configuration_names": list(configurations.keys()),
            "lithium_configs": sum(1 for cfg in configurations.values() if cfg.get("isLithium", False)),
            "gel_configs": sum(1 for cfg in configurations.values() if not cfg.get("isLithium", True))
        }
        
        info = {
            "file_info": file_info,
            "statistics": stats,
            "system_status": "operational"
        }
        
        logger.info(f"✅ Información obtenida: {stats['total_configurations']} configuraciones")
        
        return info
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo información: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/custom/configurations/storage-info")
async def get_storage_info():
    """
    📊 Obtener información sobre el sistema de almacenamiento actual
    
    Proporciona detalles sobre:
    - Tipo de almacenamiento activo (Redis vs archivo)
    - Estado de conexión Redis
    - Estadísticas de performance
    - Información de configuraciones
    """
    try:
        system_info = await custom_config_manager.get_system_info()
        
        return {
            "storage_info": system_info,
            "timestamp": datetime.now().isoformat(),
            "migration_available": not system_info.get("redis_available", False)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info de storage: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo información: {str(e)}")

# NUEVO: Endpoint con la ruta que esperan los tests y documentación
@router.post("/custom/configurations/{configuration_name}/apply")
async def apply_configuration_alt(
    configuration_name: str, 
    esp32_manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Aplicar una configuración guardada (ruta alternativa)
    
    Esta es la ruta que esperan los tests y la documentación.
    Redirecta a la misma funcionalidad que /custom/config/{name}/apply
    """
    # Redirigir a la función principal
    return await apply_configuration(configuration_name, esp32_manager)

@router.get("/custom/configurations", response_model=ConfigurationsListResponse)
async def load_configurations():
    """
    Cargar archivo de configuraciones personalizadas
    
    Retorna todas las configuraciones guardadas en el sistema.
    Si no existen configuraciones, retorna un objeto vacío......
    """
    try:
        logger.info("📋 Cargando configuraciones personalizadas...")
        
        configurations = await custom_config_manager.load_configurations()
        
        logger.info(f"✅ Cargadas {len(configurations)} configuraciones")
        
        return ConfigurationsListResponse(
            configurations=configurations,
            total_count=len(configurations)
        )
        
    except Exception as e:
        logger.error(f"❌ Error cargando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

# ============= RUTAS DINÁMICAS (después de las específicas) =============

@router.get("/custom/config/{configuration_name}")
async def get_configuration(configuration_name: str):
    """
    Obtener una configuración específica
    
    Retorna los datos de una configuración guardada por su nombre.
    """
    try:
        logger.info(f"📋 Obteniendo configuración: {configuration_name}")
        
        configuration = await custom_config_manager.get_configuration(configuration_name)
        
        if configuration is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Configuración '{configuration_name}' no encontrada"
            )
        
        logger.info(f"✅ Configuración '{configuration_name}' encontrada")
        
        return {
            "configuration_name": configuration_name,
            "configuration": configuration
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo configuración '{configuration_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/custom/config/{configuration_name}", response_model=ConfigurationResponse)
async def save_configuration(configuration_name: str, configuration: CustomConfiguration):
    """
    Guardar una configuración individual
    
    Permite guardar o actualizar una configuración específica
    con un nombre único.
    """
    try:
        logger.info(f"💾 Guardando configuración individual: {configuration_name}")
        
        # ✅ CORRECCIÓN: Pasar el objeto CustomConfiguration directamente, no .dict()
        result = await custom_config_manager.save_single_configuration(
            configuration_name, 
            configuration
        )
        
        logger.info(f"✅ Configuración '{configuration_name}' guardada exitosamente")
        
        return ConfigurationResponse(
            message=result["message"],
            status=result["status"],
            configuration_name=configuration_name
        )
        
    except Exception as e:
        logger.error(f"❌ Error guardando configuración '{configuration_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/custom/config/{configuration_name}", response_model=ConfigurationResponse)
async def delete_configuration(configuration_name: str):
    """
    Eliminar una configuración específica
    
    Elimina permanentemente una configuración guardada.
    """
    try:
        logger.info(f"🗑️ Eliminando configuración: {configuration_name}")
        
        result = await custom_config_manager.delete_configuration(configuration_name)
        
        logger.info(f"✅ Configuración '{configuration_name}' eliminada exitosamente")
        
        return ConfigurationResponse(
            message=result["message"],
            status=result["status"],
            configuration_name=configuration_name
        )
        
    except ValueError as ve:
        logger.error(f"❌ Configuración no encontrada: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"❌ Error eliminando configuración '{configuration_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/custom/config/{configuration_name}/apply")
async def apply_configuration(
    configuration_name: str, 
    esp32_manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Aplicar una configuración guardada
    
    Aplica todos los parámetros de una configuración guardada
    al ESP32, configurando la batería según los valores almacenados.
    """
    # DEBUG: Log inmediato al entrar en la función
    logger.info(f"🎯 DEBUG - INICIO apply_configuration para: {configuration_name}")
    
    try:
        logger.info(f"🔧 Aplicando configuración: {configuration_name}")
        
        # Obtener la configuración
        configuration_data = await custom_config_manager.get_configuration(configuration_name)
        
        # DEBUG: Log de la configuración obtenida
        logger.info(f"🔍 DEBUG - Configuración obtenida: {configuration_data}")
        logger.info(f"🔍 DEBUG - Tipo de configuración: {type(configuration_data)}")
        
        if configuration_data is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Configuración '{configuration_name}' no encontrada"
            )
        
        # ✅ CORRECCIÓN: Extraer la configuración real del wrapper
        if isinstance(configuration_data, dict) and 'configuration' in configuration_data:
            configuration = configuration_data['configuration']
            logger.info(f"🔍 DEBUG - Configuración extraída del wrapper: {configuration}")
        else:
            configuration = configuration_data
            logger.info(f"🔍 DEBUG - Usando configuración directa: {configuration}")
        
        if configuration:
            logger.info(f"🔍 DEBUG - Keys en configuración: {list(configuration.keys()) if hasattr(configuration, 'keys') else 'No tiene keys'}")
        
        # Verificar conexión ESP32
        if not esp32_manager or not esp32_manager.connected:
            raise HTTPException(
                status_code=503, 
                detail="ESP32 no está conectado"
            )
        
        # Aplicar cada parámetro de la configuración
        applied_params = []
        failed_params = []
        esp32_responses = {}
        
        # Mapeo de parámetros del modelo a nombres ESP32
        param_mapping = {
            "batteryCapacity": "batteryCapacity",
            "isLithium": "isLithium", 
            "thresholdPercentage": "thresholdPercentage",
            "maxAllowedCurrent": "maxAllowedCurrent",
            "bulkVoltage": "bulkVoltage",
            "absorptionVoltage": "absorptionVoltage",
            "floatVoltage": "floatVoltage",
            "useFuenteDC": "useFuenteDC",
            "fuenteDC_Amps": "fuenteDC_Amps",
            "factorDivider": "factorDivider"
        }
        
        # DEBUG: Log del mapeo y verificación
        logger.info(f"🔍 DEBUG - Param mapping definido con {len(param_mapping)} parámetros")
        logger.info(f"🔍 DEBUG - Iniciando bucle de aplicación...")
        
        for config_key, esp32_param in param_mapping.items():
            logger.info(f"🔍 DEBUG - Procesando {config_key} -> {esp32_param}")
            logger.info(f"🔍 DEBUG - ¿{config_key} in configuration? {config_key in configuration if configuration else 'configuration is None'}")
            
            if config_key in configuration:
                try:
                    value = configuration[config_key]
                    
                    # Validar el parámetro
                    validated_value = validate_parameter_value(esp32_param, value)
                    
                    # Enviar al ESP32
                    result = await esp32_manager.set_parameter(esp32_param, validated_value)
                    
                    if result.get("success"):
                        applied_params.append(f"{esp32_param}={validated_value}")
                        esp32_responses[esp32_param] = {
                            "success": True,
                            "esp32_response": result.get("response", "OK")
                        }
                        logger.info(f"✅ Aplicado: {esp32_param} = {validated_value}")
                    else:
                        error_msg = result.get('error', 'Error desconocido')
                        failed_params.append(f"{esp32_param}: {error_msg}")
                        esp32_responses[esp32_param] = {
                            "success": False,
                            "esp32_response": result.get("response", "ERROR"),
                            "error": error_msg
                        }
                        logger.error(f"❌ Error aplicando {esp32_param}: {error_msg}")
                        
                except Exception as param_error:
                    error_msg = str(param_error)
                    failed_params.append(f"{esp32_param}: {error_msg}")
                    esp32_responses[esp32_param] = {
                        "success": False,
                        "error": error_msg
                    }
                    logger.error(f"❌ Error con parámetro {esp32_param}: {param_error}")
        
        # Preparar respuesta compatible con documentación frontend
        from datetime import datetime
        applied_at = datetime.now().isoformat()
        
        if failed_params:
            message = f"Configuración '{configuration_name}' aplicada parcialmente al ESP32"
            status = "partial_success"
        else:
            message = f"Configuración '{configuration_name}' aplicada exitosamente al ESP32"
            status = "success"
        
        logger.info(f"🔧 Aplicación completada: {message}")
        
        response = {
            "message": message,
            "status": status,
            "configuration_name": configuration_name,
            "esp32_responses": esp32_responses,
            "applied_at": applied_at
        }
        
        # Agregar resumen si hay fallos
        if failed_params:
            response["summary"] = {
                "total_parameters": len(param_mapping),
                "applied_successfully": len(applied_params),
                "failed": len(failed_params),
                "failed_parameters": failed_params
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error aplicando configuración '{configuration_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/custom/configurations/applied")
async def get_applied_configuration():
    """
    Obtener información sobre la última configuración aplicada
    
    Retorna detalles sobre la configuración que está actualmente
    activa en el ESP32.
    """
    try:
        logger.info("📋 Obteniendo configuración aplicada...")
        
        # Por ahora, devolvemos información básica
        # En una implementación completa, esto podría trackear la última configuración aplicada
        applied_info = {
            "message": "Información de configuración aplicada no está disponible en esta versión",
            "status": "info_not_available",
            "timestamp": datetime.now().isoformat(),
            "note": "Para verificar parámetros actuales del ESP32, use el endpoint /data/real-time"
        }
        
        logger.info("✅ Información de configuración aplicada obtenida")
        
        return applied_info
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo configuración aplicada: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")