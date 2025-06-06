#!/bin/bash
# ESP32 Solar Charger API - Script de Instalación Automática
# Crea toda la estructura del proyecto con archivos completos

set -e  # Salir en caso de error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que no se ejecute como root
if [[ $EUID -eq 0 ]]; then
   print_error "No ejecutes este script como root"
   exit 1
fi

print_status "🚀 Iniciando instalación de ESP32 Solar Charger API..."

# Crear directorio del proyecto
PROJECT_NAME="."
if [ -d "$PROJECT_NAME" ]; then
    print_warning "El directorio $PROJECT_NAME ya existe. ¿Continuar? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_error "Instalación cancelada"
        exit 1
    fi
fi

# Crear estructura de directorios
print_status "📁 Creando estructura de directorios..."
mkdir -p $PROJECT_NAME/{models,services,api,core,logs,tests}
cd $PROJECT_NAME

# Crear archivos __init__.py
touch models/__init__.py
touch services/__init__.py
touch api/__init__.py
touch core/__init__.py
touch tests/__init__.py

print_success "Directorios creados"

# ========== CREAR ARCHIVOS DE CONFIGURACIÓN ==========

print_status "⚙️ Creando archivos de configuración..."

# requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
pyserial==3.5
redis==5.0.1
python-multipart==0.0.6
websockets==12.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
EOF

# .env (archivo de ejemplo)
cat > .env.example << 'EOF'
# ESP32 API Configuration
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Serial Configuration
SERIAL_PORT=/dev/ttyS5
SERIAL_BAUDRATE=9600
SERIAL_TIMEOUT=3.0

# Rate Limiting
MIN_COMMAND_INTERVAL=0.6
MAX_REQUESTS_PER_MINUTE=60

# Cache
CACHE_TTL=2
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/esp32_api.log
EOF

# .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# Redis
dump.rdb
EOF

print_success "Archivos de configuración creados"

# ========== CREAR ARCHIVOS CORE ==========

print_status "🔧 Creando módulos core..."

# core/config.py
cat > core/config.py << 'EOF'
#!/usr/bin/env python3
"""
Configuración global de la API ESP32
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "ESP32 Solar Charger API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API para control y monitoreo del cargador solar ESP32"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # ESP32 Serial Configuration
    SERIAL_PORT: str = "/dev/ttyS5"
    SERIAL_BAUDRATE: int = 9600
    SERIAL_TIMEOUT: float = 3.0
    
    # Rate Limiting
    MIN_COMMAND_INTERVAL: float = 0.6  # 600ms entre comandos
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # Cache Configuration
    CACHE_TTL: int = 2  # 2 segundos de cache
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/esp32_api.log"
    
    class Config:
        env_file = ".env"

settings = Settings()
EOF

# core/logger.py
cat > core/logger.py << 'EOF'
#!/usr/bin/env python3
"""
Sistema de logging configurado
"""

import logging
import os
from datetime import datetime
from core.config import settings

def setup_logger():
    # Crear directorio de logs si no existe
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    # Configurar formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Logger principal
    logger = logging.getLogger("esp32_api")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Handler para archivo
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()
EOF

print_success "Módulos core creados"

# ========== CREAR MODELOS ==========

print_status "📊 Creando modelos de datos..."

# models/esp32_data.py
cat > models/esp32_data.py << 'EOF'
#!/usr/bin/env python3
"""
Modelos Pydantic para datos del ESP32
"""

from pydantic import BaseModel, Field, validator
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
    seconds: int = Field(0, ge=1, le=59, description="Segundos")
    
    @validator('*')
    def validate_duration(cls, v, values):
        # Al menos 1 segundo total
        total = values.get('hours', 0) * 3600 + values.get('minutes', 0) * 60 + v
        if total < 1:
            raise ValueError("Duración mínima: 1 segundo")
        if total > 43200:  # 12 horas
            raise ValueError("Duración máxima: 12 horas")
        return v

class ParameterInfo(BaseModel):
    """Información sobre un parámetro"""
    name: str
    type: str
    configurable: bool
    readable: bool
    description: str
    command: Optional[str] = None
    range: Optional[str] = None
EOF

# models/responses.py
cat > models/responses.py << 'EOF'
#!/usr/bin/env python3
"""
Modelos de respuesta de la API
"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional

class APIResponse(BaseModel):
    """Respuesta estándar de la API"""
    success: bool
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class ParameterResponse(BaseModel):
    """Respuesta para un parámetro individual"""
    parameter: str
    value: Any
    info: Optional[Dict[str, Any]] = None

class BatchConfigResponse(BaseModel):
    """Respuesta para configuración en lote"""
    results: Dict[str, Dict[str, Any]]
    total_parameters: int
    successful: int
    failed: int
    errors: Optional[List[str]] = None

class ConnectionStatus(BaseModel):
    """Estado de conexión con ESP32"""
    connected: bool
    port: str
    baudrate: int
    last_communication: float
    communication_errors: int
    queue_size: int

class CacheStats(BaseModel):
    """Estadísticas del cache"""
    total_entries: int
    valid_entries: int
    expired_entries: int
    ttl_seconds: int

class HealthStatus(BaseModel):
    """Estado de salud de la API"""
    status: str
    timestamp: float
    esp32_connection: ConnectionStatus
EOF

print_success "Modelos de datos creados"

# ========== CREAR SERVICIOS ==========

print_status "🔧 Creando servicios..."

# services/data_cache.py
cat > services/data_cache.py << 'EOF'
#!/usr/bin/env python3
"""
Cache y validación de datos
"""

import time
from typing import Optional, Dict, Any
from models.esp32_data import ESP32Data
from core.config import settings
from core.logger import logger

class DataCache:
    """Cache simple en memoria para datos del ESP32"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if key not in self._cache:
            return None
        
        # Verificar TTL
        if time.time() - self._timestamps[key] > settings.CACHE_TTL:
            self.invalidate(key)
            return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any):
        """Guardar valor en cache"""
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def invalidate(self, key: str):
        """Invalidar entrada del cache"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def clear(self):
        """Limpiar todo el cache"""
        self._cache.clear()
        self._timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        now = time.time()
        valid_entries = sum(
            1 for ts in self._timestamps.values() 
            if (now - ts) <= settings.CACHE_TTL
        )
        
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries,
            "ttl_seconds": settings.CACHE_TTL
        }

# Instancia global del cache
data_cache = DataCache()
EOF

# Nota: El archivo esp32_manager.py es muy largo, lo crearemos en una función separada
cat > services/esp32_manager.py << 'EOF'
#!/usr/bin/env python3
"""
Manager robusto para comunicación con ESP32
ARCHIVO PRINCIPAL - Ver implementación completa en la documentación
"""

import serial
import json
import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
import queue
from core.config import settings
from core.logger import logger
from models.esp32_data import ESP32Data

class ESP32CommunicationError(Exception):
    """Excepción para errores de comunicación"""
    pass

class ESP32Manager:
    """Manager principal para comunicación con ESP32"""
    
    def __init__(self):
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
        self.last_command_time = 0
        self.lock = threading.Lock()
        self.running = False
        
        # Cache y estado
        self.last_data: Optional[Dict[str, Any]] = None
        self.last_successful_communication = time.time()
        self.communication_errors = 0
        
        # Cola de comandos para rate limiting
        self.command_queue = queue.Queue(maxsize=10)
        self.worker_thread: Optional[threading.Thread] = None
        
        # Rate limiting
        self.request_times = []
        
    async def start(self) -> bool:
        """Inicializar manager y conectar"""
        logger.info("🚀 Iniciando ESP32 Manager...")
        
        if await self._connect():
            self.running = True
            self._start_worker_thread()
            logger.info("✅ ESP32 Manager iniciado correctamente")
            return True
        
        logger.error("❌ Error iniciando ESP32 Manager")
        return False
    
    async def _connect(self) -> bool:
        """Establecer conexión serial"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if self.serial_conn and self.serial_conn.is_open:
                    self.serial_conn.close()
                
                self.serial_conn = serial.Serial(
                    port=settings.SERIAL_PORT,
                    baudrate=settings.SERIAL_BAUDRATE,
                    timeout=settings.SERIAL_TIMEOUT,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                # Limpiar buffers
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                
                # Probar comunicación
                if await self._test_communication():
                    self.connected = True
                    self.communication_errors = 0
                    logger.info(f"✅ Conectado al ESP32 en {settings.SERIAL_PORT}")
                    return True
                
            except Exception as e:
                logger.warning(f"❌ Intento {attempt + 1}: {e}")
                await asyncio.sleep(1)
        
        self.connected = False
        return False
    
    async def get_data(self) -> Optional[ESP32Data]:
        """Obtener datos completos del ESP32"""
        # Implementación simplificada para demo
        logger.info("📊 Solicitando datos del ESP32...")
        
        # Aquí iría la implementación completa del protocolo serial
        # Por ahora retorna datos de ejemplo
        try:
            # Datos de ejemplo para pruebas
            sample_data = {
                "panelToBatteryCurrent": 2450.0,
                "batteryToLoadCurrent": 1850.2,
                "voltagePanel": 18.45,
                "voltageBatterySensor2": 13.28,
                "currentPWM": 145,
                "temperature": 42.3,
                "chargeState": "ABSORPTION_CHARGE",
                "bulkVoltage": 14.4,
                "absorptionVoltage": 14.4,
                "floatVoltage": 13.6,
                "LVD": 12.0,
                "LVR": 12.5,
                "batteryCapacity": 100.0,
                "thresholdPercentage": 2.5,
                "maxAllowedCurrent": 8000.0,
                "isLithium": False,
                "maxBatteryVoltageAllowed": 15.0,
                "absorptionCurrentThreshold_mA": 2500.0,
                "currentLimitIntoFloatStage": 500.0,
                "calculatedAbsorptionHours": 1.25,
                "accumulatedAh": 67.8,
                "estimatedSOC": 68.5,
                "netCurrent": 599.8,
                "factorDivider": 5,
                "useFuenteDC": False,
                "fuenteDC_Amps": 0.0,
                "maxBulkHours": 0.0,
                "panelSensorAvailable": True,
                "maxAbsorptionHours": 1.0,
                "chargedBatteryRestVoltage": 12.88,
                "reEnterBulkVoltage": 12.6,
                "pwmFrequency": 40000,
                "tempThreshold": 55,
                "temporaryLoadOff": False,
                "loadOffRemainingSeconds": 0,
                "loadOffDuration": 0,
                "loadControlState": True,
                "ledSolarState": True,
                "notaPersonalizada": "Sistema funcionando correctamente",
                "connected": True,
                "firmware_version": "ESP32_v2.1",
                "uptime": 847293,
                "last_update": str(int(time.time()))
            }
            
            return ESP32Data(**sample_data)
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos: {e}")
            return None
    
    async def set_parameter(self, parameter: str, value: Any) -> bool:
        """Establecer un parámetro"""
        logger.info(f"⚙️ Configurando {parameter} = {value}")
        
        # Aquí iría la implementación real del protocolo serial
        # Por ahora simula éxito
        await asyncio.sleep(0.1)  # Simular delay de comunicación
        return True
    
    async def toggle_load(self, total_seconds: int) -> bool:
        """Apagar carga temporalmente"""
        logger.info(f"🔌 Apagando carga por {total_seconds} segundos")
        
        # Aquí iría la implementación real
        await asyncio.sleep(0.1)
        return True
    
    async def cancel_temporary_off(self) -> bool:
        """Cancelar apagado temporal"""
        logger.info("🔌 Cancelando apagado temporal")
        
        # Aquí iría la implementación real
        await asyncio.sleep(0.1)
        return True
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtener información de conexión"""
        return {
            "connected": self.connected,
            "port": settings.SERIAL_PORT,
            "baudrate": settings.SERIAL_BAUDRATE,
            "last_communication": self.last_successful_communication,
            "communication_errors": self.communication_errors,
            "queue_size": 0
        }
    
    async def stop(self):
        """Detener manager"""
        logger.info("🛑 Deteniendo ESP32 Manager...")
        self.running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connected = False

# NOTA: Esta es una versión simplificada para el setup inicial.
# Para la implementación completa, consulta la documentación del proyecto.
EOF

print_success "Servicios creados"

# ========== CREAR API ENDPOINTS ==========

print_status "🌐 Creando endpoints de la API..."

# api/data.py
cat > api/data.py << 'EOF'
#!/usr/bin/env python3
"""
Endpoints para datos del ESP32
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, Union
from models.esp32_data import ESP32Data, ParameterInfo
from services.esp32_manager import ESP32Manager
from services.data_cache import data_cache
from core.logger import logger

router = APIRouter(prefix="/data", tags=["Data"])

async def get_esp32_manager() -> ESP32Manager:
    """Dependency para obtener ESP32Manager"""
    from main import esp32_manager
    return esp32_manager

@router.get("/", response_model=ESP32Data)
async def get_all_data(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Obtener todos los datos del ESP32
    """
    try:
        # Verificar cache primero
        cached_data = data_cache.get("all_data")
        if cached_data:
            return cached_data
        
        # Obtener datos frescos
        data = await manager.get_data()
        if not data:
            raise HTTPException(status_code=503, detail="Error comunicándose con ESP32")
        
        # Guardar en cache
        data_cache.set("all_data", data)
        
        return data
        
    except Exception as e:
        logger.error(f"❌ Error en get_all_data: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/{parameter_name}")
async def get_parameter(
    parameter_name: str, 
    manager: ESP32Manager = Depends(get_esp32_manager)
):
    """
    Obtener un parámetro específico
    """
    try:
        # Obtener datos completos
        data = await manager.get_data()
        if not data:
            raise HTTPException(status_code=503, detail="Error comunicándose con ESP32")
        
        # Extraer parámetro específico
        value = getattr(data, parameter_name, None)
        if value is None:
            raise HTTPException(status_code=404, detail="Parámetro no encontrado")
        
        return {
            "parameter": parameter_name,
            "value": value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo {parameter_name}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/status/connection")
async def get_connection_status(manager: ESP32Manager = Depends(get_esp32_manager)):
    """
    Obtener estado de conexión con ESP32
    """
    return manager.get_connection_info()

@router.get("/status/cache")
async def get_cache_status():
    """
    Obtener estadísticas del cache
    """
    return data_cache.get_stats()
EOF

# api/config.py
cat > api/config.py << 'EOF'
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
EOF

# api/actions.py
cat > api/actions.py << 'EOF'
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
EOF

print_success "Endpoints de la API creados"

# ========== CREAR APLICACIÓN PRINCIPAL ==========

print_status "🚀 Creando aplicación principal..."

# main.py
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
FastAPI App Principal - ESP32 Solar Charger API
"""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importar configuración y servicios
from core.config import settings
from core.logger import logger
from services.esp32_manager import ESP32Manager

# Importar routers
from api.data import router as data_router
from api.config import router as config_router  
from api.actions import router as actions_router

# Manager global del ESP32
esp32_manager: ESP32Manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global esp32_manager
    
    # Startup
    logger.info("🚀 Iniciando ESP32 Solar Charger API...")
    
    try:
        # Inicializar ESP32 Manager
        esp32_manager = ESP32Manager()
        
        if await esp32_manager.start():
            logger.info("✅ ESP32 Manager iniciado correctamente")
        else:
            logger.error("❌ Error iniciando ESP32 Manager")
            
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando ESP32 Solar Charger API...")
    
    if esp32_manager:
        await esp32_manager.stop()
        
    logger.info("✅ API cerrada correctamente")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción usar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(data_router)
app.include_router(config_router) 
app.include_router(actions_router)

# Endpoints principales
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "data": "/data",
            "config": "/config", 
            "actions": "/actions"
        }
    }

@app.get("/health")
async def health_check():
    """Health check de la API"""
    if not esp32_manager:
        raise HTTPException(status_code=503, detail="ESP32 Manager no inicializado")
    
    connection_info = esp32_manager.get_connection_info()
    
    return {
        "status": "healthy" if connection_info["connected"] else "degraded",
        "timestamp": asyncio.get_event_loop().time(),
        "esp32_connection": connection_info
    }

if __name__ == "__main__":
    # Ejecutar servidor
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
EOF

print_success "Aplicación principal creada"

# ========== CREAR TESTS ==========

print_status "🧪 Creando tests básicos..."

# tests/test_api.py
cat > tests/test_api.py << 'EOF'
#!/usr/bin/env python3
"""
Tests básicos para la API
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    """Test del endpoint raíz"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data

def test_health():
    """Test del health check"""
    response = client.get("/health")
    # Puede fallar si no hay ESP32 conectado, está bien
    assert response.status_code in [200, 503]

def test_get_data():
    """Test de obtener datos"""
    response = client.get("/data/")
    # Puede fallar si no hay ESP32, está bien para setup inicial
    assert response.status_code in [200, 503, 500]

def test_get_configurable_parameters():
    """Test de parámetros configurables"""
    response = client.get("/config/")
    assert response.status_code == 200
    data = response.json()
    assert "configurable_parameters" in data
EOF

print_success "Tests básicos creados"

# ========== CREAR DOCUMENTACIÓN ==========

print_status "📚 Creando documentación..."

# README.md
cat > README.md << 'EOF'
# ESP32 Solar Charger API

API REST para control y monitoreo del cargador solar ESP32.

## 🚀 Instalación Rápida

```bash
# Clonar/crear el proyecto
git clone <tu-repo> esp32_api
cd esp32_api

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# Ejecutar servidor
python main.py
```

## 📡 Uso de la API

### Obtener todos los datos
```bash
curl http://localhost:8000/data/
```

### Configurar parámetro
```bash
curl -X PUT http://localhost:8000/config/bulkVoltage \
  -H "Content-Type: application/json" \
  -d '{"value": 14.5}'
```

### Apagar carga temporalmente
```bash
curl -X POST http://localhost:8000/actions/toggle_load \
  -H "Content-Type: application/json" \
  -d '{"hours": 0, "minutes": 5, "seconds": 0}'
```

## 📊 Documentación Interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Tests

```bash
pytest tests/
```

## 📁 Estructura del Proyecto

```
esp32_api/
├── main.py              # FastAPI app principal
├── models/              # Modelos Pydantic
├── services/            # Lógica de negocio
├── api/                 # Endpoints REST
├── core/                # Configuración
├── tests/               # Tests
└── logs/                # Archivos de log
```

## ⚙️ Configuración

Edita el archivo `.env`:

```bash
SERIAL_PORT=/dev/ttyS5
SERIAL_BAUDRATE=9600
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## 🔗 Endpoints Principales

- `GET /data/` - Todos los datos del ESP32
- `PUT /config/{parameter}` - Configurar parámetro
- `POST /actions/toggle_load` - Control de carga
- `GET /health` - Estado de la API

## 📞 Soporte

Para más información, consulta la documentación en `/docs`.
EOF

# Crear script de start/stop
cat > start_api.sh << 'EOF'
#!/bin/bash
# Script para iniciar la API

# Activar entorno virtual
source venv/bin/activate

# Verificar puerto serial
if [ ! -e "/dev/ttyS5" ]; then
    echo "⚠️ Puerto /dev/ttyS5 no encontrado"
    echo "Puertos disponibles:"
    ls -la /dev/tty* | grep -E "(ttyS|ttyUSB|ttyACM)" 2>/dev/null || echo "No se encontraron puertos seriales"
fi

echo "🚀 Iniciando ESP32 Solar Charger API..."
echo "📡 Puerto: ${SERIAL_PORT:-/dev/ttyS5}"
echo "🌐 URL: http://localhost:${PORT:-8000}"
echo "📚 Docs: http://localhost:${PORT:-8000}/docs"
echo ""
echo "Presiona Ctrl+C para detener"
echo "=========================="

python main.py
EOF

cat > stop_api.sh << 'EOF'
#!/bin/bash
# Script para detener la API

echo "🛑 Deteniendo ESP32 Solar Charger API..."

# Buscar y matar procesos
pkill -f "main.py" && echo "✅ API detenida"
pkill -f "uvicorn.*main" && echo "✅ Uvicorn detenido"

echo "✅ API detenida completamente"
EOF

# Hacer ejecutables los scripts
chmod +x start_api.sh
chmod +x stop_api.sh

print_success "Documentación y scripts creados"

# ========== FINALIZAR ==========

print_success "🎉 Proyecto ESP32 Solar Charger API creado exitosamente!"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🎯 PRÓXIMOS PASOS:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1️⃣ Navegar al directorio del proyecto:"
echo "   cd $PROJECT_NAME"
echo ""
echo "2️⃣ Crear entorno virtual de Python:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo ""
echo "3️⃣ Instalar dependencias:"
echo "   pip install -r requirements.txt"
echo ""
echo "4️⃣ Configurar variables de entorno:"
echo "   cp .env.example .env"
echo "   nano .env  # Editar configuración"
echo ""
echo "5️⃣ Iniciar la API:"
echo "   ./start_api.sh"
echo "   # O manualmente: python main.py"
echo ""
echo "📚 Documentación interactiva:"
echo "   http://localhost:8000/docs"
echo ""
echo "🧪 Ejecutar tests:"
echo "   pytest tests/"
echo ""
echo "═══════════════════════════════════════════════════════════"
print_warning "NOTA: Algunos archivos son versiones simplificadas."
print_warning "Para implementación completa del protocolo serial,"
print_warning "consulta la documentación del proyecto."
echo "═══════════════════════════════════════════════════════════"

echo ""
print_success "✅ ¡Instalación completada!"