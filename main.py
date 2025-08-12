#!/usr/bin/env python3
"""
FastAPI App Principal - ESP32 Solar Charger API con Schedule y Multi-CPU
Soporte universal: x86, ARM, RISC-V con auto-detección de CPU
"""

import asyncio
import uvicorn
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importar configuración y servicios
from core.config import settings
from core.logger import logger
from services.esp32_manager import ESP32Manager
from services.schedule_manager import ScheduleManager

# NUEVO: Importar detección de CPU
try:
    from utils.cpu_detection import get_cached_runtime_config
    CPU_DETECTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ CPU detection no disponible: {e}")
    CPU_DETECTION_AVAILABLE = False

# Importar routers
from api.data import router as data_router
from api.config import router as config_router  
from api.actions import router as actions_router
from api.schedule import router as schedule_router  # NUEVO

# Rate Limiting imports 
from services.rate_limiter import rate_limiter
from models.rate_limiting import RateLimitStats
from core.dependencies import check_health_rate_limit  

# Managers globales - IMPORTANTE: Compartidos entre workers de forma segura
esp32_manager: ESP32Manager = None
schedule_manager: ScheduleManager = None  # NUEVO

# Variable global para configuración de CPU
_cpu_config = None

def get_cpu_configuration():
    """Obtener configuración de CPU (con cache thread-safe)"""
    global _cpu_config
    if _cpu_config is None and CPU_DETECTION_AVAILABLE:
        try:
            _cpu_config = get_cached_runtime_config()
            logger.info("🔍 Configuración de CPU cargada correctamente")
        except Exception as e:
            logger.error(f"❌ Error cargando configuración de CPU: {e}")
            _cpu_config = {"use_gunicorn": False, "workers": 1}
    elif _cpu_config is None:
        _cpu_config = {"use_gunicorn": False, "workers": 1}
    return _cpu_config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación - MEJORADO para multi-worker
    
    IMPORTANTE: Esta función se ejecuta una vez por worker en modo Gunicorn,
    pero el ESP32Manager debe ser compartido de forma segura entre workers.
    """
    global esp32_manager, schedule_manager
    
    # Obtener configuración de CPU
    cpu_config = get_cpu_configuration()
    
    # Startup
    if cpu_config.get("use_gunicorn"):
        logger.info(f"🚀 Iniciando ESP32 Solar API - Worker Gunicorn (PID: {os.getpid()})")
    else:
        logger.info("🚀 Iniciando ESP32 Solar API - Modo Single Worker")
    
    try:
        # NUEVO: Inicialización thread-safe del ESP32Manager
        if esp32_manager is None:
            logger.info("🔌 Inicializando ESP32 Manager...")
            esp32_manager = ESP32Manager(
                port=settings.SERIAL_PORT,
                baudrate=settings.SERIAL_BAUDRATE
            )
            
            if await esp32_manager.start():
                logger.info("✅ ESP32 Manager iniciado correctamente")
            else:
                logger.error("❌ Error iniciando ESP32 Manager")
        else:
            logger.info("🔌 ESP32 Manager ya inicializado (worker compartido)")
        
        # NUEVO: Inicializar Schedule Manager (una vez por aplicación)
        if schedule_manager is None:
            logger.info("⏰ Inicializando Schedule Manager...")
            schedule_manager = ScheduleManager(esp32_manager=esp32_manager)
            await schedule_manager.start()
            logger.info("✅ Schedule Manager iniciado correctamente")
        else:
            logger.info("⏰ Schedule Manager ya inicializado")
            
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        # En modo multi-worker, un fallo no debe tumbar toda la aplicación
        if not cpu_config.get("use_gunicorn"):
            raise  # Solo re-raise en modo single worker
    
    yield
    
    # Shutdown - Solo limpiar en el último worker
    logger.info(f"🛑 Cerrando worker (PID: {os.getpid()})...")
    
    # NOTA: En modo Gunicorn, cada worker ejecuta shutdown, pero solo
    # el último debe hacer la limpieza completa. Por simplicidad,
    # permitimos que cada worker haga su propia limpieza.
    
    try:
        if schedule_manager:
            await schedule_manager.stop()
            logger.info("✅ Schedule Manager detenido")
        
        if esp32_manager:
            await esp32_manager.stop()
            logger.info("✅ ESP32 Manager detenido")
    except Exception as e:
        logger.error(f"❌ Error en shutdown: {e}")
        
    logger.info("✅ Worker cerrado correctamente")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION + " - Con Schedule Diario",  # Actualizar descripción
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

# Rate Limiting Exception Handler
@app.exception_handler(429)
async def rate_limit_handler(request, exc):
    """Handler personalizado para errores de rate limiting"""
    return JSONResponse(
        status_code=429,
        content=exc.detail,
        headers={"Retry-After": str(exc.detail.get("wait_seconds", 60))}
    )

# Incluir routers
app.include_router(data_router)
app.include_router(config_router) 
app.include_router(actions_router)
app.include_router(schedule_router)  # NUEVO

# Endpoints principales
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "features": [
            "ESP32 Communication",
            "Real-time Data Monitoring", 
            "Configuration Management",
            "Manual Load Control",
            "Daily Scheduled Load Control"  # NUEVO
        ],
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "data": "/data",
            "config": "/config", 
            "actions": "/actions",
            "schedule": "/schedule"  # NUEVO
        }
    }

@app.get("/health", dependencies=[Depends(check_health_rate_limit)])
async def health_check():
    """Health check de la API"""
    if not esp32_manager:
        raise HTTPException(status_code=503, detail="ESP32 Manager no inicializado")
    
    connection_info = esp32_manager.get_connection_info()
    
    # NUEVO: Incluir estado del schedule
    schedule_status = None
    if schedule_manager:
        try:
            schedule_status = schedule_manager.get_status()
        except Exception as e:
            schedule_status = {"error": str(e)}
    
    return {
        "status": "healthy" if connection_info["connected"] else "degraded",
        "timestamp": asyncio.get_event_loop().time(),
        "esp32_connection": connection_info,
        "schedule_manager": {
            "initialized": schedule_manager is not None,
            "status": schedule_status
        }
    }

# Rate Limiting Endpoints
@app.get("/rate-limit/stats")
async def get_rate_limit_stats() -> RateLimitStats:
    """Obtener estadísticas de rate limiting"""
    return rate_limiter.get_stats()

@app.post("/rate-limit/reset")
async def reset_rate_limits():
    """Reset rate limits (útil para testing)"""
    rate_limiter.reset_limits()
    return {"message": "Rate limits reset successfully"}

# NUEVO: Endpoint de información general del sistema
@app.get("/system/info")
async def get_system_info():
    """Obtener información completa del sistema"""
    try:
        # Obtener configuración de CPU
        cpu_config = get_cpu_configuration()
        
        system_info = {
            "api": {
                "name": settings.API_TITLE,
                "version": settings.API_VERSION,
                "uptime_seconds": asyncio.get_event_loop().time()
            },
            "esp32": esp32_manager.get_connection_info() if esp32_manager else {"error": "Not initialized"},
            "schedule": schedule_manager.get_status() if schedule_manager else {"error": "Not initialized"},
            "rate_limiting": rate_limiter.get_stats().dict(),
            # NUEVO: Información de CPU y arquitectura
            "cpu_configuration": cpu_config if CPU_DETECTION_AVAILABLE else {"error": "CPU detection not available"},
            "runtime_mode": "multi-worker" if cpu_config.get("use_gunicorn") else "single-worker",
            "process_info": {
                "pid": os.getpid(),
                "workers_configured": cpu_config.get("workers", 1),
                "force_single_worker": os.getenv('FORCE_SINGLE_WORKER', 'false')
            }
        }
        
        return system_info
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info del sistema: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    """
    Punto de entrada principal - MEJORADO con detección multi-CPU
    
    Decide automáticamente entre:
    - Uvicorn single-worker (modo desarrollo, debugging, o hardware limitado)
    - Gunicorn multi-worker (modo producción con múltiples CPUs)
    """
    
    # Obtener configuración de CPU
    cpu_config = get_cpu_configuration()
    
    # Decidir modo de ejecución
    use_gunicorn = cpu_config.get("use_gunicorn", False)
    workers = cpu_config.get("workers", 1)
    force_single = os.getenv('FORCE_SINGLE_WORKER', 'false').lower() == 'true'
    
    if force_single:
        logger.info("🔧 FORCE_SINGLE_WORKER activado - usando Uvicorn single-worker")
        use_gunicorn = False
    
    if use_gunicorn and workers > 1:
        logger.info(f"🚀 Iniciando con Gunicorn multi-worker ({workers} workers)")
        logger.info("💡 Para usar single-worker, configura MAX_WORKERS=1 o FORCE_SINGLE_WORKER=true")
        
        # Usar Gunicorn con configuración dinámica
        import subprocess
        import sys
        
        gunicorn_cmd = [
            sys.executable, "-m", "gunicorn",
            "--config", "gunicorn_conf.py",
            "main:app"
        ]
        
        try:
            subprocess.run(gunicorn_cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error ejecutando Gunicorn: {e}")
            logger.info("🔄 Fallback a Uvicorn single-worker...")
            use_gunicorn = False
        except KeyboardInterrupt:
            logger.info("🛑 Detenido por usuario")
            sys.exit(0)
    
    if not use_gunicorn:
        # Modo single-worker con Uvicorn (comportamiento original)
        logger.info("🔧 Iniciando con Uvicorn single-worker")
        logger.info("💡 Para multi-worker, configura MAX_WORKERS=auto en .env")
        
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower()
        )