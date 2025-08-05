#!/usr/bin/env python3
"""
Servicio para gestión de configuraciones personalizadas
"""

import json
import os
import asyncio
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
    """Gestor de configuraciones personalizadas"""
    
    def __init__(self, config_file_path: str = "configuraciones.json"):
        """
        Inicializar el gestor de configuraciones
        
        Args:
            config_file_path: Ruta al archivo de configuraciones
        """
        self.config_file_path = Path(config_file_path)
        self.lock = asyncio.Lock()
        
        # Asegurar que el directorio existe
        self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📋 ConfigurationManager inicializado con archivo: {self.config_file_path}")
    
    async def save_configurations(self, configurations_data: str) -> Dict[str, str]:
        """
        Guardar configuraciones desde string JSON
        
        Args:
            configurations_data: String JSON con las configuraciones
            
        Returns:
            Dict con mensaje y status
            
        Raises:
            ValueError: Si el JSON es inválido
            Exception: Si hay error al guardar
        """
        async with self.lock:
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
                    
                    # Agregar timestamps si no existen
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
                
                # Guardar en archivo
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(validated_configs, f, indent=2, ensure_ascii=False)
                
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
        Cargar configuraciones desde archivo
        
        Returns:
            Dict con las configuraciones cargadas
        """
        async with self.lock:
            try:
                if not self.config_file_path.exists():
                    logger.info("📋 Archivo de configuraciones no existe, devolviendo vacío")
                    return {}
                
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    configurations = json.load(f)
                
                logger.info(f"📋 Cargadas {len(configurations)} configuraciones desde {self.config_file_path}")
                return configurations
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error decodificando JSON: {e}")
                return {}
            except Exception as e:
                logger.error(f"❌ Error cargando configuraciones: {e}")
                return {}
    
    async def save_single_configuration(self, name: str, configuration: CustomConfiguration) -> Dict[str, str]:
        """
        Guardar una configuración individual
        
        Args:
            name: Nombre de la configuración
            configuration: Datos de la configuración
            
        Returns:
            Dict con mensaje y status
        """
        async with self.lock:
            try:
                # Cargar configuraciones existentes
                existing_configs = await self.load_configurations()
                
                # Actualizar timestamps
                config_dict = configuration.dict()
                current_time = datetime.now().isoformat()
                
                if name in existing_configs:
                    # Mantener fecha de creación original
                    config_dict['createdAt'] = existing_configs[name].get('createdAt', current_time)
                else:
                    config_dict['createdAt'] = current_time
                
                config_dict['updatedAt'] = current_time
                
                # Agregar la nueva configuración
                existing_configs[name] = config_dict
                
                # Guardar todo
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_configs, f, indent=2, ensure_ascii=False)
                
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
        Eliminar una configuración específica
        
        Args:
            name: Nombre de la configuración a eliminar
            
        Returns:
            Dict con mensaje y status
        """
        async with self.lock:
            try:
                # Cargar configuraciones existentes
                configurations = await self.load_configurations()
                
                if name not in configurations:
                    raise ValueError(f"La configuración '{name}' no existe")
                
                # Eliminar la configuración
                del configurations[name]
                
                # Guardar el archivo actualizado
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(configurations, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ Configuración '{name}' eliminada correctamente")
                
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
        Importar configuraciones desde datos JSON
        
        Args:
            configurations_data: String JSON con configuraciones
            overwrite_existing: Si sobrescribir configuraciones existentes
            
        Returns:
            ConfigurationImportResponse con resultado de la importación
        """
        async with self.lock:
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
                
                # Guardar configuraciones actualizadas
                if imported_count > 0:
                    with open(self.config_file_path, 'w', encoding='utf-8') as f:
                        json.dump(existing_configs, f, indent=2, ensure_ascii=False)
                
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
