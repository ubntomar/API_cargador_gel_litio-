#!/usr/bin/env python3
"""
Manager de configuraciones personalizadas usando Redis
Solución definitiva para problemas de concurrencia
"""

import redis
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from core.config import settings
from core.logger import logger
from models.custom_configurations import CustomConfiguration

class CustomConfigurationManagerRedis:
    """Manager para configuraciones personalizadas usando Redis"""
    
    def __init__(self):
        """Inicializar conexión Redis y configuración"""
        try:
            # Conectar a Redis con configuración de retry
            self.redis_client = redis.from_url(
                settings.REDIS_URL or "redis://localhost:6379",
                decode_responses=True,
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Prefijo para keys de configuraciones
            self.key_prefix = "esp32:custom_config:"
            
            # Verificar conexión
            self.redis_client.ping()
            logger.info("✅ CustomConfigurationManagerRedis inicializado con Redis")
            
        except redis.RedisError as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            logger.info("🔄 Fallback: Usando manager de archivos como respaldo")
            # Importar manager de archivos como fallback
            from services.custom_configuration_manager import CustomConfigurationManager
            self._fallback_manager = CustomConfigurationManager()
            self.redis_client = None
    
    def _is_redis_available(self) -> bool:
        """Verificar si Redis está disponible"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except redis.RedisError:
            return False
    
    async def save_single_configuration(
        self, 
        name: str, 
        configuration: CustomConfiguration
    ) -> Dict[str, Any]:
        """Guardar una configuración individual"""
        try:
            if not self._is_redis_available():
                logger.warning("⚠️ Redis no disponible, usando fallback")
                return await self._fallback_manager.save_single_configuration(name, configuration)
            
            logger.info(f"💾 Guardando configuración en Redis: {name}")
            
            # Preparar datos con timestamps
            config_data = configuration.dict()
            config_data.update({
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            })
            
            # Guardar en Redis como hash - operación atómica
            key = f"{self.key_prefix}{name}"
            pipe = self.redis_client.pipeline()
            pipe.delete(key)  # Limpiar key existente
            pipe.hset(key, mapping=config_data)  # Guardar nueva configuración
            pipe.execute()
            
            logger.info(f"✅ Configuración '{name}' guardada exitosamente en Redis")
            
            return {
                "message": f"Configuración '{name}' guardada exitosamente",
                "status": "success",
                "configuration_name": name,
                "storage": "redis"
            }
            
        except Exception as e:
            logger.error(f"❌ Error guardando configuración '{name}': {e}")
            # Fallback a manager de archivos
            if hasattr(self, '_fallback_manager'):
                logger.info("🔄 Intentando con fallback manager")
                return await self._fallback_manager.save_single_configuration(name, configuration)
            raise Exception(f"Error al guardar configuración: {e}")
    
    async def get_configuration(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtener una configuración específica"""
        try:
            if not self._is_redis_available():
                return await self._fallback_manager.get_configuration(name)
            
            key = f"{self.key_prefix}{name}"
            config_data = self.redis_client.hgetall(key)
            
            if not config_data:
                return None
            
            # Convertir valores numéricos
            config_data = self._convert_redis_values(config_data)
            
            return {
                "configuration_name": name,
                "configuration": config_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo configuración '{name}': {e}")
            if hasattr(self, '_fallback_manager'):
                return await self._fallback_manager.get_configuration(name)
            return None
    
    async def load_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Cargar todas las configuraciones"""
        try:
            if not self._is_redis_available():
                return await self._fallback_manager.load_configurations()
            
            logger.info("📋 Cargando configuraciones desde Redis...")
            
            # Buscar todas las keys de configuraciones
            pattern = f"{self.key_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            configurations = {}
            
            # Usar pipeline para eficiencia
            if keys:
                pipe = self.redis_client.pipeline()
                for key in keys:
                    pipe.hgetall(key)
                
                results = pipe.execute()
                
                for key, config_data in zip(keys, results):
                    if config_data:
                        name = key.replace(self.key_prefix, "")
                        configurations[name] = self._convert_redis_values(config_data)
            
            logger.info(f"✅ {len(configurations)} configuraciones cargadas desde Redis")
            return configurations
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuraciones: {e}")
            if hasattr(self, '_fallback_manager'):
                return await self._fallback_manager.load_configurations()
            return {}
    
    async def delete_configuration(self, name: str) -> Dict[str, Any]:
        """Eliminar una configuración"""
        try:
            if not self._is_redis_available():
                return await self._fallback_manager.delete_configuration(name)
            
            logger.info(f"🗑️ Eliminando configuración desde Redis: {name}")
            
            key = f"{self.key_prefix}{name}"
            
            # Verificar que existe antes de eliminar
            if not self.redis_client.exists(key):
                return {
                    "message": f"Configuración '{name}' no encontrada",
                    "status": "error"
                }
            
            # Eliminar - operación atómica
            deleted = self.redis_client.delete(key)
            
            if deleted:
                logger.info(f"✅ Configuración '{name}' eliminada exitosamente de Redis")
                return {
                    "message": f"Configuración '{name}' eliminada exitosamente",
                    "status": "success",
                    "storage": "redis"
                }
            else:
                return {
                    "message": f"Error eliminando configuración '{name}'",
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"❌ Error eliminando configuración '{name}': {e}")
            if hasattr(self, '_fallback_manager'):
                return await self._fallback_manager.delete_configuration(name)
            raise Exception(f"Error al eliminar configuración: {e}")
    
    async def export_configurations(self) -> str:
        """Exportar todas las configuraciones como JSON"""
        try:
            configurations = await self.load_configurations()
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_configurations": len(configurations),
                "storage_type": "redis" if self._is_redis_available() else "file",
                "configurations": configurations
            }
            return json.dumps(export_data, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ Error exportando configuraciones: {e}")
            raise Exception(f"Error al exportar: {e}")
    
    async def import_configurations(
        self, 
        configurations_data: str, 
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Importar configuraciones desde JSON"""
        try:
            # Parsear JSON
            import_data = json.loads(configurations_data)
            
            if "configurations" not in import_data:
                raise ValueError("Formato de datos inválido: falta 'configurations'")
            
            configurations = import_data["configurations"]
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for name, config_data in configurations.items():
                try:
                    # Verificar si ya existe
                    existing = await self.get_configuration(name)
                    
                    if existing and not overwrite_existing:
                        skipped_count += 1
                        continue
                    
                    # Convertir a modelo de configuración
                    # Remover timestamps para regenerarlos
                    clean_config = {k: v for k, v in config_data.items() 
                                  if k not in ["createdAt", "updatedAt"]}
                    
                    configuration = CustomConfiguration(**clean_config)
                    await self.save_single_configuration(name, configuration)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Error importando '{name}': {e}")
            
            return {
                "message": "Importación completada",
                "status": "success",
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors,
                "storage": "redis" if self._is_redis_available() else "file"
            }
            
        except Exception as e:
            logger.error(f"❌ Error importando configuraciones: {e}")
            raise Exception(f"Error al importar: {e}")
    
    async def validate_configuration(self, configuration: CustomConfiguration) -> Dict[str, Any]:
        """Validar configuración"""
        try:
            # Validación básica con Pydantic (automática)
            config_dict = configuration.dict()
            
            # Validaciones adicionales
            warnings = []
            
            # Validar voltajes
            if config_dict["bulkVoltage"] <= config_dict["floatVoltage"]:
                warnings.append("Bulk voltage debería ser mayor que float voltage")
            
            if config_dict["absorptionVoltage"] < config_dict["floatVoltage"]:
                warnings.append("Absorption voltage debería ser mayor o igual que float voltage")
            
            # Validar capacidad vs corriente
            if config_dict["maxAllowedCurrent"] > (config_dict["batteryCapacity"] * 1000):
                warnings.append("Corriente máxima muy alta para la capacidad de batería")
            
            return {
                "status": "valid",
                "warnings": warnings,
                "validated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "invalid",
                "error": str(e),
                "validated_at": datetime.now().isoformat()
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Obtener información del sistema de configuraciones"""
        try:
            configurations = await self.load_configurations()
            
            # Estadísticas Redis
            redis_info = {}
            if self._is_redis_available():
                try:
                    info = self.redis_client.info()
                    redis_info = {
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory_human": info.get("used_memory_human", "N/A"),
                        "total_commands_processed": info.get("total_commands_processed", 0),
                        "redis_version": info.get("redis_version", "Unknown")
                    }
                except:
                    redis_info = {"error": "Could not get Redis info"}
            
            return {
                "total_configurations": len(configurations),
                "storage_type": "redis" if self._is_redis_available() else "file_fallback",
                "redis_available": self._is_redis_available(),
                "redis_info": redis_info,
                "configuration_names": list(configurations.keys()),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo info del sistema: {e}")
            return {
                "error": str(e),
                "storage_type": "unknown",
                "redis_available": False
            }
    
    def _convert_redis_values(self, redis_data: Dict[str, str]) -> Dict[str, Any]:
        """Convertir valores de Redis (strings) a tipos apropiados"""
        converted = {}
        
        for key, value in redis_data.items():
            if key in ["batteryCapacity", "thresholdPercentage", "maxAllowedCurrent", 
                      "bulkVoltage", "absorptionVoltage", "floatVoltage", "fuenteDC_Amps"]:
                try:
                    converted[key] = float(value)
                except (ValueError, TypeError):
                    converted[key] = value
            elif key in ["factorDivider"]:
                try:
                    converted[key] = int(value)
                except (ValueError, TypeError):
                    converted[key] = value
            elif key in ["isLithium", "useFuenteDC"]:
                converted[key] = value.lower() in ["true", "1", "yes"]
            else:
                converted[key] = value
        
        return converted

    async def migrate_from_file(self, file_path: str = "configuraciones.json") -> Dict[str, Any]:
        """Migrar configuraciones existentes desde archivo a Redis"""
        try:
            if not self._is_redis_available():
                return {"error": "Redis no disponible para migración"}
            
            # Leer archivo JSON existente
            file_path = Path(file_path)
            if not file_path.exists():
                return {"message": "No hay archivo para migrar", "migrated": 0}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            migrated_count = 0
            errors = []
            
            for name, config_data in file_data.items():
                try:
                    # Limpiar datos de timestamps viejos
                    clean_config = {k: v for k, v in config_data.items() 
                                  if k not in ["createdAt", "updatedAt"]}
                    
                    configuration = CustomConfiguration(**clean_config)
                    await self.save_single_configuration(name, configuration)
                    migrated_count += 1
                    
                except Exception as e:
                    errors.append(f"Error migrando '{name}': {e}")
            
            logger.info(f"✅ Migración completada: {migrated_count} configuraciones")
            
            return {
                "message": f"Migración completada exitosamente",
                "migrated_count": migrated_count,
                "errors": errors,
                "source": "file",
                "destination": "redis"
            }
            
        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            return {"error": f"Error en migración: {e}"}

    async def save_configurations(self, configurations: Dict[str, CustomConfiguration]) -> Dict[str, Any]:
        """Guardar múltiples configuraciones - alias para compatibilidad"""
        try:
            saved_count = 0
            errors = []
            
            for name, config in configurations.items():
                try:
                    await self.save_single_configuration(name, config)
                    saved_count += 1
                except Exception as e:
                    errors.append(f"Error guardando '{name}': {e}")
            
            return {
                "message": f"{saved_count} configuraciones guardadas",
                "status": "success",
                "saved_count": saved_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"❌ Error guardando configuraciones múltiples: {e}")
            raise Exception(f"Error al guardar configuraciones: {e}")
    
    def get_file_info(self) -> Dict[str, Any]:
        """Obtener información del sistema de storage - alias para compatibilidad"""
        try:
            if self._is_redis_available():
                redis_info = self.redis_client.info()
                return {
                    "storage_type": "redis",
                    "redis_version": redis_info.get("redis_version", "Unknown"),
                    "used_memory": redis_info.get("used_memory_human", "Unknown"),
                    "connected_clients": redis_info.get("connected_clients", 0)
                }
            else:
                return {
                    "storage_type": "file_fallback",
                    "fallback_active": True
                }
        except Exception as e:
            return {"error": f"Error obteniendo info: {e}"}
