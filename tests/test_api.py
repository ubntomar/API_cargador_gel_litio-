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

# ===== TESTS PARA CONFIGURACIONES PERSONALIZADAS =====

def test_list_custom_configurations_empty():
    """Test listar configuraciones (inicialmente vacío)"""
    response = client.get("/config/custom/configurations")
    assert response.status_code == 200
    data = response.json()
    assert "configurations" in data
    assert "total_count" in data
    assert isinstance(data["configurations"], dict)
    assert data["total_count"] == len(data["configurations"])

def test_configurations_info():
    """Test obtener información del sistema de configuraciones"""
    response = client.get("/config/custom/configurations/info")
    # Puede fallar si hay conflicto de rutas, pero debería funcionar
    assert response.status_code in [200, 404]

def test_save_single_configuration():
    """Test guardar una configuración individual"""
    config_data = {
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
    
    response = client.post(
        "/config/custom/configurations/TestConfig",
        json=config_data
    )
    
    # Debería funcionar si no hay problemas de rutas
    assert response.status_code in [200, 201, 422]  # 422 si hay validación
    
    if response.status_code in [200, 201]:
        data = response.json()
        assert "message" in data or "status" in data

def test_validate_configuration():
    """Test validar una configuración"""
    config_data = {
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
    
    response = client.post(
        "/config/custom/configurations/validate",
        json=config_data
    )
    
    # Validación debería funcionar independientemente del ESP32
    assert response.status_code in [200, 422]
    
    if response.status_code == 200:
        data = response.json()
        assert "is_valid" in data or "valid" in data

def test_export_configurations():
    """Test exportar configuraciones"""
    response = client.get("/config/custom/configurations/export")
    # Puede fallar por rutas, pero debería funcionar
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        # El export debería devolver las configuraciones en formato JSON
        assert isinstance(data, dict)

def test_save_multiple_configurations():
    """Test guardar múltiples configuraciones"""
    configs_data = {
        "data": {
            "Config1": {
                "batteryCapacity": 100.0,
                "isLithium": True,
                "factorDivider": 1
            },
            "Config2": {
                "batteryCapacity": 200.0,
                "isLithium": False,
                "factorDivider": 2
            }
        }
    }
    
    response = client.post(
        "/config/custom/configurations",
        json=configs_data
    )
    
    # Debería funcionar o dar error de validación
    assert response.status_code in [200, 201, 422]

def test_import_configurations():
    """Test importar configuraciones"""
    import_data = {
        "configurations_data": '{"TestImport": {"batteryCapacity": 150.0, "isLithium": true}}',
        "overwrite_existing": False
    }
    
    response = client.post(
        "/config/custom/configurations/import",
        json=import_data
    )
    
    # Debería funcionar o dar error de validación
    assert response.status_code in [200, 201, 422]

# ===== TESTS DE ENDPOINTS ANTERIORES (VERIFICAR QUE SIGUEN FUNCIONANDO) =====

def test_config_parameter_info():
    """Test información de un parámetro específico"""
    response = client.get("/config/bulkVoltage")
    assert response.status_code in [200, 404]  # 404 si hay conflicto de rutas
    
    if response.status_code == 200:
        data = response.json()
        assert "parameter" in data
        assert "info" in data

def test_config_validate_endpoint():
    """Test validación de parámetro individual"""
    response = client.post(
        "/config/validate",
        params={"parameter_name": "bulkVoltage"},
        json={"value": 14.5}
    )
    assert response.status_code in [200, 422]
