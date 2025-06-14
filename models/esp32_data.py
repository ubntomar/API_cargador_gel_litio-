#!/usr/bin/env python3
"""
Modelos Pydantic para datos del ESP32 - Versión Corregida
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, Union
from enum import Enum

class ChargeState(str, Enum):
    BULK_CHARGE = "BULK_CHARGE"
    ABSORPTION_CHARGE = "ABSORPTION_CHARGE"
    FLOAT_CHARGE = "FLOAT_CHARGE"
    ERROR = "ERROR"

class ESP32Data(BaseModel):
    """Modelo completo de datos del ESP32"""
    
    # Mediciones en tiempo real
    panelToBatteryCurrent: float = Field(..., description="Corriente panel a batería (mA)")
    batteryToLoadCurrent: float = Field(..., description="Corriente batería a carga (mA)")
    voltagePanel: float = Field(..., description="Voltaje panel solar (V)")
    voltageBatterySensor2: float = Field(..., description="Voltaje batería (V)")
    currentPWM: int = Field(..., ge=0, le=255, description="Valor PWM actual")
    temperature: float = Field(..., description="Temperatura (°C)")
    chargeState: ChargeState = Field(..., description="Estado de carga")
    
    # Parámetros de carga
    bulkVoltage: float = Field(..., ge=12.0, le=15.0, description="Voltaje BULK (V)")
    absorptionVoltage: float = Field(..., ge=12.0, le=15.0, description="Voltaje ABSORCIÓN (V)")
    floatVoltage: float = Field(..., ge=12.0, le=15.0, description="Voltaje FLOTACIÓN (V)")
    LVD: float = Field(..., description="Low Voltage Disconnect (V)")
    LVR: float = Field(..., description="Low Voltage Reconnect (V)")
    
    # Configuración de batería
    batteryCapacity: float = Field(..., ge=1, le=1000, description="Capacidad batería (Ah)")
    thresholdPercentage: float = Field(..., ge=0.1, le=5.0, description="Umbral corriente (%)")
    maxAllowedCurrent: float = Field(..., ge=1000, le=15000, description="Corriente máxima (mA)")
    isLithium: bool = Field(..., description="Tipo de batería (true=Litio, false=GEL)")
    maxBatteryVoltageAllowed: float = Field(..., description="Voltaje máximo batería (V)")
    
    # Valores calculados
    absorptionCurrentThreshold_mA: float = Field(..., description="Umbral corriente absorción (mA)")
    currentLimitIntoFloatStage: float = Field(..., description="Límite corriente float (mA)")
    calculatedAbsorptionHours: float = Field(..., description="Horas absorción calculadas")
    currentBulkHours: float = Field(..., ge=0, description="Horas transcurridas en BULK actual")
    accumulatedAh: float = Field(..., description="Ah acumulados")
    estimatedSOC: float = Field(..., ge=0, le=100, description="SOC estimado (%)")
    netCurrent: float = Field(..., description="Corriente neta (mA)")
    factorDivider: int = Field(..., ge=1, le=10, description="Factor divisor")
    
    # Configuración de fuente
    useFuenteDC: bool = Field(..., description="Usar fuente DC")
    fuenteDC_Amps: float = Field(..., ge=0, le=50, description="Amperios fuente DC")
    maxBulkHours: float = Field(..., description="Horas máx en BULK")
    panelSensorAvailable: bool = Field(..., description="Sensor paneles disponible")
    
    # Configuración avanzada
    maxAbsorptionHours: float = Field(..., description="Horas máx absorción")
    chargedBatteryRestVoltage: float = Field(..., description="Voltaje batería cargada")
    reEnterBulkVoltage: float = Field(..., description="Voltaje re-entrada BULK")
    pwmFrequency: int = Field(..., description="Frecuencia PWM (Hz)")
    tempThreshold: int = Field(..., description="Umbral temperatura (°C)")
    
    # Estado de apagado temporal
    temporaryLoadOff: bool = Field(..., description="Apagado temporal activo")
    loadOffRemainingSeconds: int = Field(..., ge=0, description="Segundos restantes")
    loadOffDuration: int = Field(..., ge=0, description="Duración total apagado")
    
    # Estado del sistema
    loadControlState: bool = Field(..., description="Estado control carga")
    ledSolarState: bool = Field(..., description="Estado LED solar")
    notaPersonalizada: str = Field(..., description="Nota del sistema")
    
    # Metadatos
    connected: bool = Field(..., description="Conexión activa")
    firmware_version: str = Field(..., description="Versión firmware")
    uptime: int = Field(..., ge=0, description="Uptime (ms)")
    last_update: str = Field(..., description="Última actualización")

class ConfigParameter(BaseModel):
    """Modelo para configurar un parámetro"""
    value: Union[float, int, bool, str] = Field(..., description="Nuevo valor del parámetro")

class ToggleLoadRequest(BaseModel):
    """Modelo para apagar carga temporalmente"""
    hours: int = Field(0, ge=0, le=12, description="Horas")
    minutes: int = Field(0, ge=0, le=59, description="Minutos")
    seconds: int = Field(0, ge=0, le=59, description="Segundos")
    
    @model_validator(mode='after')
    def validate_total_duration(self):
        # Calcular tiempo total en segundos
        total_seconds = self.hours * 3600 + self.minutes * 60 + self.seconds
        
        if total_seconds < 1:
            raise ValueError("Duración mínima: 1 segundo total")
        if total_seconds > 43200:  # 12 horas
            raise ValueError("Duración máxima: 12 horas")
        
        return self

class ParameterInfo(BaseModel):
    """Información sobre un parámetro"""
    name: str
    type: str
    configurable: bool
    readable: bool
    description: str
    command: Optional[str] = None
    range: Optional[str] = None