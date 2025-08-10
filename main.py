#!/usr/bin/env python3
"""
FastAPI App Principal - ESP32 Solar Charger API con Schedule
"""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importar configuración y servicios
from core.config import settings
from core.logger import logger
from services.esp32_manager import ESP32Manager
from services.schedule_manager import ScheduleManager

# Importar routers
from api.data import router as data_router
from api.config import router as config_router  
from api.actions import router as actions_router
from api.schedule import router as schedule_router  # NUEVO

# Rate Limiting imports 
from services.rate_limiter import rate_limiter
from models.rate_limiting import RateLimitStats
from core.dependencies import check_health_rate_limit  

# Managers globales
esp32_manager: ESP32Manager = None
schedule_manager: ScheduleManager = None  # NUEVO

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global esp32_manager, schedule_manager
    
    # Startup
    logger.info("🚀 Iniciando ESP32 Solar Charger API con Schedule...")
    
    try:
        # Inicializar ESP32 Manager con configuración correcta
        esp32_manager = ESP32Manager(
            port=settings.SERIAL_PORT,
            baudrate=settings.SERIAL_BAUDRATE
        )
        
        if await esp32_manager.start():
            logger.info("✅ ESP32 Manager iniciado correctamente")
        else:
            logger.error("❌ Error iniciando ESP32 Manager")
        
        # NUEVO: Inicializar Schedule Manager
        schedule_manager = ScheduleManager(esp32_manager=esp32_manager)
        await schedule_manager.start()
        logger.info("✅ Schedule Manager iniciado correctamente")
            
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando ESP32 Solar Charger API...")
    
    # NUEVO: Detener Schedule Manager
    if schedule_manager:
        await schedule_manager.stop()
        logger.info("✅ Schedule Manager detenido")
    
    if esp32_manager:
        await esp32_manager.stop()
        logger.info("✅ ESP32 Manager detenido")
        
    logger.info("✅ API cerrada correctamente")

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
        system_info = {
            "api": {
                "name": settings.API_TITLE,
                "version": settings.API_VERSION,
                "uptime_seconds": asyncio.get_event_loop().time()
            },
            "esp32": esp32_manager.get_connection_info() if esp32_manager else {"error": "Not initialized"},
            "schedule": schedule_manager.get_status() if schedule_manager else {"error": "Not initialized"},
            "rate_limiting": rate_limiter.get_stats().dict()
        }
        
        return system_info
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo info del sistema: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    # Ejecutar servidor
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )