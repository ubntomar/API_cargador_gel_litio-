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
