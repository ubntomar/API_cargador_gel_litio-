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
