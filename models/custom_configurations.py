#!/usr/bin/env python3
"""
Modelos para el sistema de configuraciones personalizadas
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from datetime import datetime
import json

class CustomConfiguration(BaseModel):
    """Modelo para una configuración personalizada individual"""
    
    # Parámetros de batería
    batteryCapacity: float = Field(..., ge=1.0, le=1000.0, description="Capacidad de la batería en Ah")
    isLithium: bool = Field(..., description="Tipo de batería: true=Litio, false=GEL/AGM")
    thresholdPercentage: float = Field(..., ge=0.1, le=5.0, description="Umbral de corriente en %")
    maxAllowedCurrent: float = Field(..., ge=1000.0, le=15000.0, description="Corriente máxima permitida en mA")
    
    # Parámetros de voltaje
    bulkVoltage: float = Field(..., ge=12.0, le=15.0, description="Voltaje BULK en V")
    absorptionVoltage: float = Field(..., ge=12.0, le=15.0, description="Voltaje de absorción en V")
    floatVoltage: float = Field(..., ge=12.0, le=15.0, description="Voltaje de flotación en V")
    
    # Parámetros de fuente DC
    useFuenteDC: bool = Field(..., description="Usar fuente DC adicional")
    fuenteDC_Amps: float = Field(..., ge=0.0, le=50.0, description="Corriente de la fuente DC en A")
    
    # Parámetros avanzados
    factorDivider: int = Field(..., ge=1, le=10, description="Factor divisor para cálculos internos")
    
    # Metadatos
    createdAt: datetime = Field(default_factory=datetime.now, description="Fecha y hora de creación")
    updatedAt: datetime = Field(default_factory=datetime.now, description="Fecha y hora de última actualización")
    
    @validator('absorptionVoltage')
    def validate_absorption_voltage(cls, v, values):
        """Validar que el voltaje de absorción sea válido"""
        if 'bulkVoltage' in values and v < values['bulkVoltage']:
            raise ValueError('El voltaje de absorción debe ser mayor o igual al voltaje BULK')
        return v
    
    @validator('floatVoltage') 
    def validate_float_voltage(cls, v, values):
        """Validar que el voltaje de flotación sea válido"""
        if 'absorptionVoltage' in values and v > values['absorptionVoltage']:
            raise ValueError('El voltaje de flotación debe ser menor o igual al voltaje de absorción')
        return v

class ConfigurationData(BaseModel):
    """Modelo para el payload de guardado de configuraciones"""
    data: str = Field(..., description="Datos de configuraciones como string JSON")
    
    @validator('data')
    def validate_json_data(cls, v):
        """Validar que los datos sean JSON válido"""
        try:
            parsed_data = json.loads(v)
            if not isinstance(parsed_data, dict):
                raise ValueError("Los datos deben ser un objeto JSON")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {str(e)}")

class ConfigurationRequest(BaseModel):
    """Modelo para solicitud de creación/actualización de configuración"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre único de la configuración")
    configuration: CustomConfiguration = Field(..., description="Datos de la configuración")

class ConfigurationResponse(BaseModel):
    """Modelo para respuesta de configuración"""
    message: str = Field(..., description="Mensaje de respuesta")
    status: str = Field(..., description="Estado de la operación")
    configuration_name: Optional[str] = Field(None, description="Nombre de la configuración afectada")

class ConfigurationsListResponse(BaseModel):
    """Modelo para respuesta de lista de configuraciones"""
    configurations: Dict[str, CustomConfiguration] = Field(..., description="Diccionario de configuraciones guardadas")
    total_count: int = Field(..., description="Número total de configuraciones")

class ConfigurationApplyRequest(BaseModel):
    """Modelo para solicitud de aplicación de configuración"""
    configuration_name: str = Field(..., min_length=1, description="Nombre de la configuración a aplicar")

class ConfigurationValidationResponse(BaseModel):
    """Modelo para respuesta de validación de configuración"""
    is_valid: bool = Field(..., description="Si la configuración es válida")
    errors: Optional[Dict[str, str]] = Field(None, description="Errores de validación por campo")
    warnings: Optional[Dict[str, str]] = Field(None, description="Advertencias por campo")

class ConfigurationExportResponse(BaseModel):
    """Modelo para respuesta de exportación"""
    filename: str = Field(..., description="Nombre del archivo generado")
    content: str = Field(..., description="Contenido JSON para descarga")
    configurations_count: int = Field(..., description="Número de configuraciones exportadas")

class ConfigurationImportRequest(BaseModel):
    """Modelo para solicitud de importación"""
    configurations_data: str = Field(..., description="Datos JSON de configuraciones a importar")
    overwrite_existing: bool = Field(default=False, description="Si sobrescribir configuraciones existentes")
    
    @validator('configurations_data')
    def validate_import_data(cls, v):
        """Validar datos de importación"""
        try:
            parsed_data = json.loads(v)
            if not isinstance(parsed_data, dict):
                raise ValueError("Los datos deben ser un objeto JSON")
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON inválido: {str(e)}")

class ConfigurationImportResponse(BaseModel):
    """Modelo para respuesta de importación"""
    success: bool = Field(..., description="Si la importación fue exitosa")
    imported_count: int = Field(..., description="Número de configuraciones importadas")
    skipped_count: int = Field(..., description="Número de configuraciones omitidas")
    errors: Optional[Dict[str, str]] = Field(None, description="Errores durante la importación")
    warnings: Optional[Dict[str, str]] = Field(None, description="Advertencias durante la importación")
