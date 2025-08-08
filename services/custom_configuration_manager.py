#!/usr/bin/env python3
"""
Servicio para gestión de configuraciones personalizadas
"""

import json
import os
import asyncio
import fcntl  # File locking para resolver concurrencia en RISC-V
import time
import tempfile
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from pathlib import Path

from core.logger import logger
from models.custom_configurations import (
    CustomConfiguration, 
    ConfigurationImportResponse,
    ConfigurationValidationResponse
)

class CustomConfigurationManager:
    """Gestor de configuraciones personalizadas con file locking para RISC-V"""
    
    def __init__(self, config_file_path: str = "configuraciones.json"):
        """
        Inicializar el gestor de configuraciones
        
        Args:
            config_file_path: Ruta al archivo de configuraciones
        """
        self.config_file_path = Path(config_file_path)
        self.lock_file_path = Path(f"{config_file_path}.lock")
        self.asyncio_lock = asyncio.Lock()
        
        # Configuración de reintentos para RISC-V
        self.max_retries = 5
        self.retry_delay = 0.1
        self.lock_timeout = 30.0  # 30 segundos max para obtener lock
        
        # Asegurar que el directorio existe
        self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📋 ConfigurationManager inicializado con archivo: {self.config_file_path}")
        logger.info(f"🔒 File locking habilitado para RISC-V con lock: {self.lock_file_path}")
    
    async def _acquire_file_lock(self, timeout: float = None) -> int:
        """
        Obtener lock de archivo para prevenir concurrencia en RISC-V
        
        Args:
            timeout: Tiempo máximo para esperar el lock
            
        Returns:
            File descriptor del lock
            
        Raises:
            Exception: Si no se puede obtener el lock
        """
        if timeout is None:
            timeout = self.lock_timeout
            
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                # Crear archivo de lock
                lock_fd = os.open(self.lock_file_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
                
                # Intentar obtener lock exclusivo no-bloqueante
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # Escribir PID en el archivo de lock para debugging
                os.write(lock_fd, f"{os.getpid()}\n".encode())
                os.fsync(lock_fd)
                
                logger.debug(f"🔒 File lock obtenido en intento {attempt + 1}")
                return lock_fd
                
            except (OSError, IOError) as e:
                # Si el error es "Resource temporarily unavailable" = lock ocupado
                if e.errno == 11 or "Resource temporarily unavailable" in str(e):
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        os.close(lock_fd)
                        raise Exception(f"No se pudo obtener file lock después de {timeout}s")
                    
                    # Esperar antes del siguiente intento
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    # Error diferente, cerrar y re-lanzar
                    if 'lock_fd' in locals():
                        os.close(lock_fd)
                    raise Exception(f"Error obteniendo file lock: {e}")
            
        raise Exception(f"No se pudo obtener file lock después de {self.max_retries} intentos")
    
    def _release_file_lock(self, lock_fd: int) -> None:
        """
        Liberar lock de archivo
        
        Args:
            lock_fd: File descriptor del lock a liberar
        """
        try:
            if lock_fd is not None:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
                
                # Remover archivo de lock
                if self.lock_file_path.exists():
                    self.lock_file_path.unlink()
                
                logger.debug("🔓 File lock liberado")
        except Exception as e:
            logger.warning(f"⚠️ Error liberando file lock: {e}")
    
    async def _save_to_file_with_lock(self, configurations: Dict[str, Dict]) -> None:
        """
        Método para guardar configuraciones con file locking robusto para RISC-V
        
        Args:
            configurations: Configuraciones a guardar
            
        Raises:
            Exception: Si hay error al guardar
        """
        lock_fd = None
        temp_file_path = None
        
        try:
            # 1. Obtener file lock del sistema operativo
            lock_fd = await self._acquire_file_lock()
            
            # 2. Crear archivo temporal en el mismo directorio (para rename atómico)
            temp_file_path = self.config_file_path.with_suffix(f'.tmp.{os.getpid()}')
            
            # 3. Escribir datos al archivo temporal
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(configurations, f, indent=2, ensure_ascii=False)
                f.flush()  # Forzar escritura al disco
                os.fsync(f.fileno())  # Sincronizar con sistema de archivos
            
            # 4. Mover archivo temporal al destino final (operación atómica)
            temp_file_path.replace(self.config_file_path)
            temp_file_path = None  # Marcar como movido exitosamente
            
            logger.debug(f"✅ Configuraciones guardadas con file lock (PID: {os.getpid()})")
            
        except Exception as e:
            error_msg = f"Error guardando con file lock: {e}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
            
        finally:
            # Limpiar archivo temporal si existe
            if temp_file_path and temp_file_path.exists():
                try:
                    temp_file_path.unlink()
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Error limpiando archivo temporal: {cleanup_error}")
            
            # Liberar file lock
            if lock_fd is not None:
                self._release_file_lock(lock_fd)
    
    async def save_configurations(self, configurations_data: str) -> Dict[str, str]:
        """
        Guardar configuraciones desde string JSON con file locking
        
        Args:
            configurations_data: String JSON con las configuraciones
            
        Returns:
            Dict con mensaje y status
            
        Raises:
            ValueError: Si el JSON es inválido
            Exception: Si hay error al guardar
        """
        async with self.asyncio_lock:
            try:
                # Validar que sea JSON válido
                configurations = json.loads(configurations_data)
                
                if not isinstance(configurations, dict):
                    raise ValueError("Los datos deben ser un objeto JSON")
                
                # Validar cada configuración
                validated_configs = {}
                for name, config_data in configurations.items():
                    if not isinstance(config_data, dict):
                        raise ValueError(f"La configuración '{name}' debe ser un objeto")
                    
                    # Agregar timestamps si no existen (como strings ISO)
                    current_time = datetime.now().isoformat()
                    if 'createdAt' not in config_data:
                        config_data['createdAt'] = current_time
                    config_data['updatedAt'] = current_time
                    
                    # Validar estructura usando el modelo Pydantic
                    try:
                        validated_config = CustomConfiguration(**config_data)
                        validated_configs[name] = validated_config.dict()
                    except Exception as e:
                        raise ValueError(f"Error en configuración '{name}': {str(e)}")
                
                # Guardar en archivo con file locking
                await self._save_to_file_with_lock(validated_configs)
                
                logger.info(f"✅ Guardadas {len(validated_configs)} configuraciones en {self.config_file_path}")
                
                return {
                    "message": "Configuraciones guardadas exitosamente",
                    "status": "success"
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON inválido: {e}")
                raise ValueError(f"JSON inválido: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Error guardando configuraciones: {e}")
                raise Exception(f"Error al guardar: {str(e)}")
    
    async def load_configurations(self) -> Dict[str, Dict]:
        """
        Cargar configuraciones desde archivo con file locking
        
        Returns:
            Dict con las configuraciones cargadas
        """
        # Usar asyncio lock para coordinación entre corrutinas
        async with self.asyncio_lock:
            return await self._load_configurations_internal()
    
    async def _load_configurations_internal(self) -> Dict[str, Dict]:
        """
        Método interno para cargar configuraciones con file locking robusto
        """
        lock_fd = None
        
        try:
            logger.info("📋 Cargando configuraciones personalizadas...")
            
            if not self.config_file_path.exists():
                logger.info("📋 Archivo de configuraciones no existe, devolviendo vacío")
                return {}
            
            # Obtener shared lock para lectura (permite múltiples lectores)
            try:
                lock_fd = os.open(self.lock_file_path, os.O_CREAT | os.O_RDONLY)
                fcntl.flock(lock_fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except (OSError, IOError):
                # Si no se puede obtener shared lock, intentar sin lock (degraded mode)
                logger.warning("⚠️ No se pudo obtener shared lock, leyendo sin lock")
                if lock_fd:
                    os.close(lock_fd)
                    lock_fd = None
            
            # Leer archivo de configuraciones
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                configurations = json.load(f)
            
            logger.info(f"✅ Cargadas {len(configurations)} configuraciones")
            return configurations
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando JSON: {e}")
            # Crear archivo limpio en caso de corrupción
            await self._create_empty_config_file()
            return {}
        except Exception as e:
            logger.error(f"❌ Error cargando configuraciones: {e}")
            return {}
        finally:
            # Liberar lock de lectura
            if lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                except Exception:
                    pass
    
    async def _save_to_file(self, configurations: Dict[str, Dict]) -> None:
        """
        Método interno para guardar configuraciones en archivo
        """
        # ✅ CORRECCIÓN: Guardar en archivo temporal primero para atomicidad
        temp_file = self.config_file_path.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(configurations, f, indent=2, ensure_ascii=False)
            
            # Mover archivo temporal al destino final (operación atómica)
            temp_file.replace(self.config_file_path)
            
        except Exception as e:
            # Limpiar archivo temporal si algo sale mal
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    async def _create_empty_config_file(self) -> None:
        """
        Crear archivo de configuraciones vacío
        """
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Archivo de configuraciones recreado: {self.config_file_path}")
        except Exception as e:
            logger.error(f"❌ Error creando archivo de configuraciones: {e}")
    
    async def save_single_configuration(self, name: str, configuration: CustomConfiguration) -> Dict[str, str]:
        """
        Guardar una configuración individual con file locking para RISC-V
        
        Args:
            name: Nombre de la configuración
            configuration: Datos de la configuración
            
        Returns:
            Dict con mensaje y status
        """
        logger.info(f"💾 Guardando configuración individual: {name}")
        
        try:
            # Usar tanto asyncio lock como file lock para máxima seguridad
            async with self.asyncio_lock:
                # Cargar configuraciones existentes
                existing_configs = await self._load_configurations_internal()
                
                # Convertir CustomConfiguration a dict
                config_dict = configuration.dict()
                current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                
                if name in existing_configs:
                    # Mantener fecha de creación original
                    config_dict['createdAt'] = existing_configs[name].get('createdAt', current_time)
                else:
                    config_dict['createdAt'] = current_time
                
                config_dict['updatedAt'] = current_time
                
                # Agregar la nueva configuración
                existing_configs[name] = config_dict
                
                # Guardar con file locking robusto
                await self._save_to_file_with_lock(existing_configs)
                
                logger.info(f"✅ Configuración '{name}' guardada correctamente")
                
                return {
                    "message": f"Configuración '{name}' guardada exitosamente",
                    "status": "success"
                }
                    
        except Exception as e:
            logger.error(f"❌ Error guardando configuración '{name}': {e}")
            raise Exception(f"Error al guardar configuración: {str(e)}")
    
    async def delete_configuration(self, name: str) -> Dict[str, str]:
        """
        Eliminar configuración personalizada con file locking
        
        Args:
            name: Nombre de la configuración a eliminar
            
        Returns:
            Dict con mensaje y status
            
        Raises:
            ValueError: Si la configuración no existe
        """
        async with self.asyncio_lock:
            try:
                # Cargar configuraciones actuales
                configurations = await self.load_configurations()
                
                if name not in configurations:
                    raise ValueError(f"Configuración '{name}' no encontrada")
                
                # Eliminar configuración
                del configurations[name]
                
                # Guardar las configuraciones actualizadas con file locking
                await self._save_to_file_with_lock(configurations)
                
                logger.info(f"🗑️ Configuración '{name}' eliminada exitosamente")
                
                return {
                    "message": f"Configuración '{name}' eliminada exitosamente",
                    "status": "success"
                }
                
            except Exception as e:
                logger.error(f"❌ Error eliminando configuración '{name}': {e}")
                raise Exception(f"Error al eliminar configuración: {str(e)}")
    
    async def get_configuration(self, name: str) -> Optional[Dict]:
        """
        Obtener una configuración específica
        
        Args:
            name: Nombre de la configuración
            
        Returns:
            Dict con los datos de la configuración o None si no existe
        """
        configurations = await self.load_configurations()
        return configurations.get(name)
    
    async def import_configurations(
        self, 
        configurations_data: str, 
        overwrite_existing: bool = False
    ) -> ConfigurationImportResponse:
        """
        Importar configuraciones desde datos JSON con file locking
        
        Args:
            configurations_data: String JSON con configuraciones
            overwrite_existing: Si sobrescribir configuraciones existentes
            
        Returns:
            ConfigurationImportResponse con resultado de la importación
        """
        async with self.asyncio_lock:
            try:
                # Validar JSON
                import_configs = json.loads(configurations_data)
                if not isinstance(import_configs, dict):
                    raise ValueError("Los datos deben ser un objeto JSON")
                
                # Cargar configuraciones existentes
                existing_configs = await self.load_configurations()
                
                imported_count = 0
                skipped_count = 0
                errors = {}
                warnings = {}
                
                for name, config_data in import_configs.items():
                    try:
                        # Verificar si ya existe
                        if name in existing_configs and not overwrite_existing:
                            skipped_count += 1
                            warnings[name] = "Configuración ya existe, use overwrite_existing=true para sobrescribir"
                            continue
                        
                        # Validar configuración
                        if not isinstance(config_data, dict):
                            errors[name] = "La configuración debe ser un objeto"
                            continue
                        
                        # Agregar timestamps
                        current_time = datetime.now().isoformat()
                        if name in existing_configs:
                            # Mantener fecha de creación original
                            config_data['createdAt'] = existing_configs[name].get('createdAt', current_time)
                        else:
                            config_data['createdAt'] = current_time
                        config_data['updatedAt'] = current_time
                        
                        # Validar usando modelo Pydantic
                        validated_config = CustomConfiguration(**config_data)
                        existing_configs[name] = validated_config.dict()
                        imported_count += 1
                        
                    except Exception as e:
                        errors[name] = str(e)
                
                # Guardar configuraciones actualizadas con file locking
                if imported_count > 0:
                    await self._save_to_file_with_lock(existing_configs)
                
                logger.info(f"📋 Importación completada: {imported_count} importadas, {skipped_count} omitidas")
                
                return ConfigurationImportResponse(
                    success=len(errors) == 0,
                    imported_count=imported_count,
                    skipped_count=skipped_count,
                    errors=errors if errors else None,
                    warnings=warnings if warnings else None
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON inválido en importación: {e}")
                raise ValueError(f"JSON inválido: {str(e)}")
            except Exception as e:
                logger.error(f"❌ Error en importación: {e}")
                raise Exception(f"Error durante la importación: {str(e)}")
    
    async def validate_configuration(self, configuration_data: Dict) -> ConfigurationValidationResponse:
        """
        Validar una configuración
        
        Args:
            configuration_data: Datos de la configuración
            
        Returns:
            ConfigurationValidationResponse con resultado de validación
        """
        try:
            # Intentar crear el modelo Pydantic
            CustomConfiguration(**configuration_data)
            
            return ConfigurationValidationResponse(
                is_valid=True,
                errors=None,
                warnings=None
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Validación falló: {e}")
            
            return ConfigurationValidationResponse(
                is_valid=False,
                errors={"validation": str(e)},
                warnings=None
            )
    
    async def export_configurations(self) -> Tuple[str, int]:
        """
        Exportar todas las configuraciones a JSON
        
        Returns:
            Tuple con (contenido_json, cantidad_configuraciones)
        """
        configurations = await self.load_configurations()
        content = json.dumps(configurations, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Exportadas {len(configurations)} configuraciones")
        
        return content, len(configurations)
    
    def get_file_info(self) -> Dict[str, any]:
        """
        Obtener información del archivo de configuraciones
        
        Returns:
            Dict con información del archivo
        """
        try:
            if self.config_file_path.exists():
                stat = self.config_file_path.stat()
                return {
                    "exists": True,
                    "path": str(self.config_file_path),
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                }
            else:
                return {
                    "exists": False,
                    "path": str(self.config_file_path),
                    "size_bytes": 0,
                    "modified": None,
                    "created": None
                }
        except Exception as e:
            logger.error(f"❌ Error obteniendo info del archivo: {e}")
            return {
                "exists": False,
                "error": str(e)
            }
