#!/usr/bin/env python3
"""
Test rápido para verificar correcciones de configuraciones personalizadas
"""

import requests
import json

API_BASE_URL = "http://192.168.13.253:8000"

def test_quick_flow():
    """Prueba el flujo completo: crear -> listar -> aplicar -> exportar"""
    
    print("🚀 Iniciando prueba rápida del flujo de configuraciones personalizadas...\n")
    
    # 1. Crear configuración
    print("1️⃣ Creando configuración de prueba...")
    create_url = f"{API_BASE_URL}/config/custom/configurations/TestLitio"
    
    config_data = {
        "batteryCapacity": 200.0,
        "isLithium": True,
        "thresholdPercentage": 3.0,
        "maxAllowedCurrent": 15000.0,
        "bulkVoltage": 14.6,
        "absorptionVoltage": 14.6,
        "floatVoltage": 13.8,
        "useFuenteDC": False,
        "fuenteDC_Amps": 0.0,
        "factorDivider": 1
    }
    
    try:
        response = requests.post(create_url, json=config_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Configuración creada exitosamente")
        else:
            print(f"   ❌ Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False
    
    # 2. Listar configuraciones
    print("\n2️⃣ Listando configuraciones...")
    list_url = f"{API_BASE_URL}/config/custom/configurations"
    
    try:
        response = requests.get(list_url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Total configuraciones: {data.get('total_count', 0)}")
            if 'TestLitio' in data.get('configurations', {}):
                print("   ✅ Configuración TestLitio encontrada")
            else:
                print("   ⚠️ Configuración TestLitio no encontrada")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 3. Validar configuración
    print("\n3️⃣ Validando configuración...")
    validate_url = f"{API_BASE_URL}/config/custom/configurations/validate"
    
    try:
        response = requests.post(validate_url, json=config_data, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Validación: {'Exitosa' if data.get('is_valid') else 'Falló'}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Exportar configuraciones
    print("\n4️⃣ Exportando configuraciones...")
    export_url = f"{API_BASE_URL}/config/custom/configurations/export"
    
    try:
        response = requests.get(export_url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            export_info = data.get('export_info', {})
            print(f"   ✅ Exportadas: {export_info.get('total_configurations', 0)} configuraciones")
            print(f"   ✅ Estructura compatible con documentación: {'export_info' in data}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 5. Aplicar configuración (si ESP32 está conectado)
    print("\n5️⃣ Intentando aplicar configuración...")
    apply_url = f"{API_BASE_URL}/config/custom/configurations/TestLitio/apply"
    
    try:
        response = requests.post(apply_url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Configuración aplicada exitosamente")
            print(f"   ✅ Respuesta incluye 'esp32_responses': {'esp32_responses' in data}")
            print(f"   ✅ Respuesta incluye 'applied_at': {'applied_at' in data}")
            
            # Mostrar algunos detalles
            esp32_responses = data.get('esp32_responses', {})
            print(f"   📊 Parámetros procesados: {len(esp32_responses)}")
            
        elif response.status_code == 503:
            print("   ⚠️ ESP32 no está conectado (esperado en pruebas)")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎯 Prueba completada. Verificar que:")
    print("   - Las respuestas coinciden con la documentación del frontend")
    print("   - Los endpoints funcionan como se espera")
    print("   - La estructura de datos es correcta")
    
    return True

if __name__ == "__main__":
    test_quick_flow()
