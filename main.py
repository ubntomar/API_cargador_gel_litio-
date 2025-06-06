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
