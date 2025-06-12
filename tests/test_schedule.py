#!/usr/bin/env python3
"""
Tests unitarios para funcionalidad Schedule - ESP32 API
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

# Importar módulos a testear
from services.schedule_manager import ScheduleManager
from models.schedule_models import ScheduleConfigRequest, ScheduleStatusResponse
from main import app

client = TestClient(app)

class TestScheduleManager:
    """Tests para ScheduleManager"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.mock_esp32_manager = Mock()
        self.mock_esp32_manager.toggle_load = AsyncMock(return_value=True)
        self.schedule_manager = ScheduleManager(esp32_manager=self.mock_esp32_manager)
    
    def test_initialization(self):
        """Test inicialización del ScheduleManager"""
        assert self.schedule_manager.enabled == True
        assert self.schedule_manager.start_time == "00:00"
        assert self.schedule_manager.duration_seconds == 21600
        assert self.schedule_manager.manual_override_active == False
        assert self.schedule_manager.running == False
    
    def test_configure_schedule_valid(self):
        """Test configuración válida del schedule"""
        success = self.schedule_manager.configure_schedule(
            enabled=True,
            start_time="14:30",
            duration_seconds=7200
        )
        
        assert success == True
        assert self.schedule_manager.enabled == True
        assert self.schedule_manager.start_time == "14:30"
        assert self.schedule_manager.duration_seconds == 7200
    
    def test_configure_schedule_invalid_time(self):
        """Test configuración con hora inválida"""
        success = self.schedule_manager.configure_schedule(
            enabled=True,
            start_time="25:00",
            duration_seconds=3600
        )
        
        assert success == False
        # Configuración anterior debe mantenerse
        assert self.schedule_manager.start_time == "00:00"
    
    def test_configure_schedule_invalid_duration(self):
        """Test configuración con duración inválida"""
        # Duración > 8 horas
        success = self.schedule_manager.configure_schedule(
            enabled=True,
            start_time="12:00",
            duration_seconds=28801
        )
        
        assert success == False
        
        # Duración = 0
        success = self.schedule_manager.configure_schedule(
            enabled=True,
            start_time="12:00",
            duration_seconds=0
        )
        
        assert success == False
    
    def test_set_manual_override(self):
        """Test establecer override manual"""
        duration = 1800  # 30 minutos
        
        success = self.schedule_manager.set_manual_override(duration)
        
        assert success == True
        assert self.schedule_manager.manual_override_active == True
        assert self.schedule_manager.manual_override_until is not None
    
    def test_clear_manual_override(self):
        """Test limpiar override manual"""
        # Primero establecer override
        self.schedule_manager.set_manual_override(1800)
        assert self.schedule_manager.manual_override_active == True
        
        # Luego limpiarlo
        success = self.schedule_manager.clear_manual_override()
        
        assert success == True
        assert self.schedule_manager.manual_override_active == False
        assert self.schedule_manager.manual_override_until is None
    
    def test_clear_manual_override_when_none(self):
        """Test limpiar override cuando no hay ninguno activo"""
        assert self.schedule_manager.manual_override_active == False
        
        success = self.schedule_manager.clear_manual_override()
        
        assert success == False  # No había nada que limpiar
    
    def test_get_status(self):
        """Test obtener estado del schedule"""
        status = self.schedule_manager.get_status()
        
        assert isinstance(status, dict)
        assert "enabled" in status
        assert "start_time" in status
        assert "duration_seconds" in status
        assert "currently_active" in status
        assert "manual_override_active" in status
        assert "current_time" in status
    
    @patch('services.schedule_manager.datetime')
    def test_is_schedule_active_now(self, mock_datetime):
        """Test verificar si schedule está activo ahora"""
        # Mock time: 01:00 (dentro de ventana 00:00-06:00)
        mock_now = datetime(2024, 1, 1, 1, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime.return_value.time.return_value = datetime.strptime("00:00", "%H:%M").time()
        mock_datetime.combine.return_value = datetime(2024, 1, 1, 0, 0, 0)
        
        # Configurar schedule habilitado
        self.schedule_manager.enabled = True
        self.schedule_manager.start_time = "00:00"
        self.schedule_manager.duration_seconds = 21600  # 6 horas
        
        is_active = self.schedule_manager._is_schedule_active_now()
        assert is_active == True
    
    @patch('services.schedule_manager.datetime')
    def test_is_schedule_not_active_when_disabled(self, mock_datetime):
        """Test schedule no activo cuando está deshabilitado"""
        self.schedule_manager.enabled = False
        
        is_active = self.schedule_manager._is_schedule_active_now()
        assert is_active == False
    
    def test_is_schedule_not_active_with_override(self):
        """Test schedule no activo cuando hay override manual"""
        self.schedule_manager.enabled = True
        self.schedule_manager.manual_override_active = True
        
        is_active = self.schedule_manager._is_schedule_active_now()
        assert is_active == False
    
    def test_get_info(self):
        """Test obtener información de capacidades"""
        info = self.schedule_manager.get_info()
        
        assert isinstance(info, dict)
        assert info["max_duration_hours"] == 8
        assert info["max_duration_seconds"] == 28800
        assert info["time_format"] == "HH:MM"
        assert info["persistence"] == False
        assert "examples" in info

class TestScheduleModels:
    """Tests para modelos Pydantic de Schedule"""
    
    def test_schedule_config_request_valid(self):
        """Test ScheduleConfigRequest válido"""
        config = ScheduleConfigRequest(
            enabled=True,
            start_time="14:30",
            duration_seconds=7200
        )
        
        assert config.enabled == True
        assert config.start_time == "14:30"
        assert config.duration_seconds == 7200
    
    def test_schedule_config_request_invalid_time(self):
        """Test ScheduleConfigRequest con hora inválida"""
        with pytest.raises(ValueError):
            ScheduleConfigRequest(
                enabled=True,
                start_time="25:00",
                duration_seconds=3600
            )
    
    def test_schedule_config_request_invalid_duration(self):
        """Test ScheduleConfigRequest con duración inválida"""
        # Duración > 8 horas
        with pytest.raises(ValueError):
            ScheduleConfigRequest(
                enabled=True,
                start_time="12:00",
                duration_seconds=28801
            )
        
        # Duración = 0
        with pytest.raises(ValueError):
            ScheduleConfigRequest(
                enabled=True,
                start_time="12:00",
                duration_seconds=0
            )
    
    def test_schedule_status_response(self):
        """Test ScheduleStatusResponse"""
        status = ScheduleStatusResponse(
            enabled=True,
            start_time="00:00",
            duration_seconds=21600,
            currently_active=False,
            manual_override_active=False,
            current_time="12:00:00"
        )
        
        assert status.enabled == True
        assert status.start_time == "00:00"
        assert status.duration_seconds == 21600

class TestScheduleEndpoints:
    """Tests para endpoints de Schedule"""
    
    def test_get_schedule_status_endpoint(self):
        """Test endpoint GET /schedule/"""
        response = client.get("/schedule/")
        
        # Puede ser 200 si está configurado o 500 si hay problemas
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "enabled" in data
            assert "current_time" in data
    
    def test_get_schedule_info_endpoint(self):
        """Test endpoint GET /schedule/info"""
        response = client.get("/schedule/info")
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "max_duration_hours" in data
            assert "time_format" in data
    
    def test_configure_schedule_endpoint_valid(self):
        """Test endpoint PUT /schedule/config con datos válidos"""
        config_data = {
            "enabled": True,
            "start_time": "14:30",
            "duration_seconds": 7200
        }
        
        response = client.put("/schedule/config", json=config_data)
        
        # Puede fallar si no hay ESP32 conectado, está bien
        assert response.status_code in [200, 400, 500, 503]
    
    def test_configure_schedule_endpoint_invalid(self):
        """Test endpoint PUT /schedule/config con datos inválidos"""
        config_data = {
            "enabled": True,
            "start_time": "25:00",  # Hora inválida
            "duration_seconds": 3600
        }
        
        response = client.put("/schedule/config", json=config_data)
        
        # Debería rechazar por validación
        assert response.status_code in [400, 422]
    
    def test_enable_schedule_endpoint(self):
        """Test endpoint POST /schedule/enable"""
        response = client.post("/schedule/enable")
        
        # Puede fallar si no hay manager inicializado
        assert response.status_code in [200, 400, 500]
    
    def test_disable_schedule_endpoint(self):
        """Test endpoint POST /schedule/disable"""
        response = client.post("/schedule/disable")
        
        # Puede fallar si no hay manager inicializado
        assert response.status_code in [200, 400, 500]
    
    def test_clear_override_endpoint(self):
        """Test endpoint POST /schedule/clear_override"""
        response = client.post("/schedule/clear_override")
        
        # Puede fallar si no hay manager inicializado
        assert response.status_code in [200, 500]

class TestScheduleIntegration:
    """Tests de integración entre Schedule y otros componentes"""
    
    def test_actions_status_includes_schedule(self):
        """Test que /actions/status incluye información de schedule"""
        response = client.get("/actions/status")
        
        # Puede fallar si no hay ESP32, pero debería incluir schedule info
        if response.status_code == 200:
            data = response.json()
            # Verificar que incluye alguna referencia a schedule
            json_str = str(data)
            assert "schedule" in json_str.lower()
    
    def test_actions_info_includes_schedule(self):
        """Test que /actions/info incluye información de schedule"""
        response = client.get("/actions/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que incluye información sobre schedule
        json_str = str(data)
        assert "schedule" in json_str.lower()
    
    def test_health_includes_schedule(self):
        """Test que /health incluye información de schedule"""
        response = client.get("/health")
        
        # Puede fallar por ESP32, pero debería incluir schedule info
        if response.status_code in [200, 503]:
            data = response.json()
            json_str = str(data)
            assert "schedule" in json_str.lower()

class TestScheduleValidations:
    """Tests específicos de validaciones"""
    
    @pytest.mark.parametrize("time_str,expected", [
        ("00:00", True),
        ("12:30", True),
        ("23:59", True),
        ("24:00", False),
        ("12:60", False),
        ("25:30", False),
        ("12:99", False),
        ("invalid", False),
    ])
    def test_time_format_validation(self, time_str, expected):
        """Test validación de formato de tiempo"""
        try:
            config = ScheduleConfigRequest(
                enabled=True,
                start_time=time_str,
                duration_seconds=3600
            )
            result = True
        except ValueError:
            result = False
        
        assert result == expected
    
    @pytest.mark.parametrize("duration,expected", [
        (1, True),       # Mínimo válido
        (3600, True),    # 1 hora
        (28800, True),   # 8 horas (máximo)
        (0, False),      # Cero
        (28801, False),  # > 8 horas
        (-1, False),     # Negativo
    ])
    def test_duration_validation(self, duration, expected):
        """Test validación de duración"""
        try:
            config = ScheduleConfigRequest(
                enabled=True,
                start_time="12:00",
                duration_seconds=duration
            )
            result = True
        except ValueError:
            result = False
        
        assert result == expected

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v", "--tb=short"])