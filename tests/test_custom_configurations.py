#!/usr/bin/env python3
"""
Tests para el sistema de configuraciones personalizadas
"""

import json
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile
import os

# Importar la clase del servicio para testing directo
import sys
sys.path.append('/home/omar/Documentos/API_cargador_gel_litio-')

from services.custom_configuration_manager import CustomConfigurationManager
from models.custom_configurations import CustomConfiguration

class TestCustomConfigurationManager:
    """Tests para el gestor de configuraciones personalizadas"""
    
    def setup_method(self):
        """Setup para cada test"""
        # Crear archivo temporal para testing
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        
        # Inicializar manager con archivo temporal
        self.manager = CustomConfigurationManager(self.temp_file.name)
        
        # Configuración de ejemplo
        self.sample_config = {
            "batteryCapacity": 100.0,
            "isLithium": True,
            "thresholdPercentage": 2.0,
            "maxAllowedCurrent": 10000.0,
            "bulkVoltage": 14.4,
            "absorptionVoltage": 14.4,
            "floatVoltage": 13.6,
            "useFuenteDC": False,
            "fuenteDC_Amps": 0.0,
            "factorDivider": 1
        }
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        # Eliminar archivo temporal
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    @pytest.mark.asyncio
    async def test_save_and_load_configurations(self):
        """Test guardar y cargar configuraciones"""
        
        # Preparar datos de configuraciones
        configurations = {
            "Batería Litio 100Ah": self.sample_config,
            "Batería GEL 200Ah": {
                **self.sample_config,
                "batteryCapacity": 200.0,
                "isLithium": False,
                "bulkVoltage": 14.1,
                "absorptionVoltage": 14.1,
                "floatVoltage": 13.3
            }
        }
        
        configurations_json = json.dumps(configurations)
        
        # Test guardar
        result = await self.manager.save_configurations(configurations_json)
        
        assert result["status"] == "success"
        assert "exitosamente" in result["message"]
        
        # Test cargar
        loaded_configs = await self.manager.load_configurations()
        
        assert len(loaded_configs) == 2
        assert "Batería Litio 100Ah" in loaded_configs
        assert "Batería GEL 200Ah" in loaded_configs
        
        # Verificar que los valores se mantuvieron
        litio_config = loaded_configs["Batería Litio 100Ah"]
        assert litio_config["batteryCapacity"] == 100.0
        assert litio_config["isLithium"] is True
        
        gel_config = loaded_configs["Batería GEL 200Ah"]
        assert gel_config["batteryCapacity"] == 200.0
        assert gel_config["isLithium"] is False
    
    @pytest.mark.asyncio
    async def test_save_single_configuration(self):
        """Test guardar configuración individual"""
        
        # Crear configuración usando el modelo Pydantic
        config = CustomConfiguration(**self.sample_config)
        
        # Guardar configuración
        result = await self.manager.save_single_configuration("Test Config", config)
        
        assert result["status"] == "success"
        
        # Verificar que se guardó
        loaded_configs = await self.manager.load_configurations()
        assert "Test Config" in loaded_configs
        
        # Verificar valores
        saved_config = loaded_configs["Test Config"]
        assert saved_config["batteryCapacity"] == 100.0
        assert saved_config["isLithium"] is True
    
    @pytest.mark.asyncio
    async def test_delete_configuration(self):
        """Test eliminar configuración"""
        
        # Primero guardar una configuración
        config = CustomConfiguration(**self.sample_config)
        await self.manager.save_single_configuration("Test Delete", config)
        
        # Verificar que existe
        loaded_configs = await self.manager.load_configurations()
        assert "Test Delete" in loaded_configs
        
        # Eliminar configuración
        result = await self.manager.delete_configuration("Test Delete")
        
        assert result["status"] == "success"
        assert "eliminada exitosamente" in result["message"]
        
        # Verificar que ya no existe
        loaded_configs = await self.manager.load_configurations()
        assert "Test Delete" not in loaded_configs
    
    @pytest.mark.asyncio
    async def test_get_configuration(self):
        """Test obtener configuración específica"""
        
        # Guardar configuración
        config = CustomConfiguration(**self.sample_config)
        await self.manager.save_single_configuration("Test Get", config)
        
        # Obtener configuración específica
        retrieved_config = await self.manager.get_configuration("Test Get")
        
        assert retrieved_config is not None
        assert retrieved_config["batteryCapacity"] == 100.0
        assert retrieved_config["isLithium"] is True
        
        # Test obtener configuración inexistente
        nonexistent_config = await self.manager.get_configuration("No Existe")
        assert nonexistent_config is None
    
    @pytest.mark.asyncio
    async def test_validate_configuration(self):
        """Test validación de configuración"""
        
        # Test configuración válida
        valid_result = await self.manager.validate_configuration(self.sample_config)
        assert valid_result.is_valid is True
        assert valid_result.errors is None
        
        # Test configuración inválida (valor fuera de rango)
        invalid_config = {**self.sample_config, "batteryCapacity": -10.0}
        invalid_result = await self.manager.validate_configuration(invalid_config)
        assert invalid_result.is_valid is False
        assert invalid_result.errors is not None
    
    @pytest.mark.asyncio
    async def test_export_configurations(self):
        """Test exportar configuraciones"""
        
        # Guardar algunas configuraciones
        config1 = CustomConfiguration(**self.sample_config)
        config2 = CustomConfiguration(**{**self.sample_config, "batteryCapacity": 200.0})
        
        await self.manager.save_single_configuration("Config 1", config1)
        await self.manager.save_single_configuration("Config 2", config2)
        
        # Exportar
        content, count = await self.manager.export_configurations()
        
        assert count == 2
        assert isinstance(content, str)
        
        # Verificar que el JSON es válido
        exported_data = json.loads(content)
        assert len(exported_data) == 2
        assert "Config 1" in exported_data
        assert "Config 2" in exported_data
    
    @pytest.mark.asyncio
    async def test_import_configurations(self):
        """Test importar configuraciones"""
        
        # Preparar datos para importar
        import_data = {
            "Imported Config 1": self.sample_config,
            "Imported Config 2": {**self.sample_config, "batteryCapacity": 150.0}
        }
        
        import_json = json.dumps(import_data)
        
        # Importar
        result = await self.manager.import_configurations(import_json, overwrite_existing=False)
        
        assert result.success is True
        assert result.imported_count == 2
        assert result.skipped_count == 0
        
        # Verificar que se importaron
        loaded_configs = await self.manager.load_configurations()
        assert "Imported Config 1" in loaded_configs
        assert "Imported Config 2" in loaded_configs
    
    @pytest.mark.asyncio
    async def test_import_with_existing_configs(self):
        """Test importar con configuraciones existentes"""
        
        # Guardar configuración existente
        config = CustomConfiguration(**self.sample_config)
        await self.manager.save_single_configuration("Existing Config", config)
        
        # Intentar importar configuración con mismo nombre
        import_data = {
            "Existing Config": {**self.sample_config, "batteryCapacity": 999.0},
            "New Config": {**self.sample_config, "batteryCapacity": 150.0}
        }
        
        import_json = json.dumps(import_data)
        
        # Importar sin sobrescribir
        result = await self.manager.import_configurations(import_json, overwrite_existing=False)
        
        assert result.imported_count == 1  # Solo la nueva
        assert result.skipped_count == 1   # La existente se omitió
        
        # Verificar que la existente no cambió
        existing_config = await self.manager.get_configuration("Existing Config")
        assert existing_config["batteryCapacity"] == 100.0  # Valor original
        
        # Importar con sobrescritura
        result2 = await self.manager.import_configurations(import_json, overwrite_existing=True)
        
        assert result2.imported_count == 2  # Ambas configuraciones
        assert result2.skipped_count == 0
        
        # Verificar que la existente cambió
        updated_config = await self.manager.get_configuration("Existing Config")
        assert updated_config["batteryCapacity"] == 999.0  # Valor actualizado

def test_configuration_model_validation():
    """Test validación del modelo Pydantic"""
    
    # Test configuración válida
    valid_config = CustomConfiguration(
        batteryCapacity=100.0,
        isLithium=True,
        thresholdPercentage=2.0,
        maxAllowedCurrent=10000.0,
        bulkVoltage=14.4,
        absorptionVoltage=14.4,
        floatVoltage=13.6,
        useFuenteDC=False,
        fuenteDC_Amps=0.0,
        factorDivider=1
    )
    
    assert valid_config.batteryCapacity == 100.0
    assert valid_config.isLithium is True
    
    # Test configuración inválida (valores fuera de rango)
    with pytest.raises(ValueError):
        CustomConfiguration(
            batteryCapacity=-10.0,  # Valor inválido
            isLithium=True,
            thresholdPercentage=2.0,
            maxAllowedCurrent=10000.0,
            bulkVoltage=14.4,
            absorptionVoltage=14.4,
            floatVoltage=13.6,
            useFuenteDC=False,
            fuenteDC_Amps=0.0,
            factorDivider=1
        )

if __name__ == "__main__":
    # Ejecutar tests básicos
    print("🧪 Ejecutando tests del sistema de configuraciones personalizadas...")
    
    # Test del modelo de validación
    try:
        test_configuration_model_validation()
        print("✅ Test del modelo: PASÓ")
    except Exception as e:
        print(f"❌ Test del modelo: FALLÓ - {e}")
    
    # Test básico del manager
    async def run_basic_test():
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            manager = CustomConfigurationManager(temp_file.name)
            
            # Test básico de guardado y carga
            sample_config = {
                "batteryCapacity": 100.0,
                "isLithium": True,
                "thresholdPercentage": 2.0,
                "maxAllowedCurrent": 10000.0,
                "bulkVoltage": 14.4,
                "absorptionVoltage": 14.4,
                "floatVoltage": 13.6,
                "useFuenteDC": False,
                "fuenteDC_Amps": 0.0,
                "factorDivider": 1
            }
            
            configurations = {"Test Config": sample_config}
            configurations_json = json.dumps(configurations)
            
            # Guardar
            result = await manager.save_configurations(configurations_json)
            assert result["status"] == "success"
            
            # Cargar
            loaded = await manager.load_configurations()
            assert len(loaded) == 1
            assert "Test Config" in loaded
            
            print("✅ Test básico del manager: PASÓ")
            
        except Exception as e:
            print(f"❌ Test básico del manager: FALLÓ - {e}")
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    # Ejecutar test async
    asyncio.run(run_basic_test())
    
    print("🏁 Tests completados")
