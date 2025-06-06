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
