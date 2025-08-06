#!/usr/bin/env python3
"""
Test para verificar endpoints de configuraciones personalizadas
Compara documentación frontend vs implementación real
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://192.168.13.253:8000"

def test_create_configuration():
    """Probar creación de configuración según documentación"""
    
    print("🧪 Probando POST /config/custom/configurations/{name}...")
    
    url = f"{API_BASE_URL}/config/custom/configurations/TestConfig"
    
    # Datos según la documentación del frontend
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
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=config_data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"Text Response: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_apply_configuration():
    """Probar aplicación de configuración según documentación"""
    
    print("\\n🧪 Probando POST /config/custom/configurations/{name}/apply...")
    
    url = f"{API_BASE_URL}/config/custom/configurations/TestConfig/apply"
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            # Verificar estructura de respuesta según documentación
            expected_fields = ["message", "status", "configuration_name"]
            missing_fields = []
            
            for field in expected_fields:
                if field not in response_data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ Campos faltantes en respuesta: {missing_fields}")
                return False
            
            # Verificar si la documentación espera esp32_responses pero no está implementado
            if "esp32_responses" not in response_data:
                print("⚠️ La documentación espera 'esp32_responses' pero no está en la implementación")
                
            return True
        else:
            print(f"Text Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_list_configurations():
    """Probar listado de configuraciones"""
    
    print("\\n🧪 Probando GET /config/custom/configurations...")
    
    url = f"{API_BASE_URL}/config/custom/configurations"
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            # Verificar estructura según documentación
            expected_fields = ["configurations", "total_count"]
            
            for field in expected_fields:
                if field not in response_data:
                    print(f"⚠️ Campo faltante: {field}")
                    return False
                    
            return True
        else:
            print(f"Text Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validate_configuration():
    """Probar validación de configuración"""
    
    print("\\n🧪 Probando POST /config/custom/configurations/validate...")
    
    url = f"{API_BASE_URL}/config/custom/configurations/validate"
    
    # Datos según documentación - pero necesitamos verificar el formato correcto
    validation_data = {
        "configuration": {
            "batteryCapacity": 100.0,
            "isLithium": False,
            "thresholdPercentage": 2.5,
            "maxAllowedCurrent": 5000.0,
            "bulkVoltage": 14.4,
            "absorptionVoltage": 14.4,
            "floatVoltage": 13.6,
            "useFuenteDC": True,
            "fuenteDC_Amps": 10.0,
            "factorDivider": 2
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=validation_data, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"Text Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_export_configurations():
    """Probar exportación de configuraciones"""
    
    print("\\n🧪 Probando GET /config/custom/configurations/export...")
    
    url = f"{API_BASE_URL}/config/custom/configurations/export"
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            # Verificar estructura según documentación
            expected_fields = ["filename", "content", "configurations_count"]
            
            for field in expected_fields:
                if field not in response_data:
                    print(f"⚠️ Campo faltante: {field}")
                    return False
                    
            return True
        else:
            print(f"Text Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_info_configurations():
    """Probar información del sistema"""
    
    print("\\n🧪 Probando GET /config/custom/configurations/info...")
    
    url = f"{API_BASE_URL}/config/custom/configurations/info"
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return True
        else:
            print(f"Text Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Probando endpoints de configuraciones personalizadas...\\n")
    
    tests = [
        ("Crear configuración", test_create_configuration),
        ("Listar configuraciones", test_list_configurations),
        ("Validar configuración", test_validate_configuration),
        ("Aplicar configuración", test_apply_configuration),
        ("Exportar configuraciones", test_export_configurations),
        ("Info del sistema", test_info_configurations)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\\n{'='*50}")
        print(f"🧪 {test_name}")
        print('='*50)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Error ejecutando prueba: {e}")
            results[test_name] = False
    
    print(f"\\n{'='*50}")
    print("📊 RESUMEN DE PRUEBAS")
    print('='*50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La documentación está alineada con la implementación.")
    else:
        print("🔧 Hay discrepancias entre la documentación y la implementación que necesitan corrección.")

if __name__ == "__main__":
    main()
