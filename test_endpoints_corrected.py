#!/usr/bin/env python3
"""
Script de prueba CORREGIDO para endpoints de configuraciones personalizadas
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, description=""):
    """Función auxiliar para probar endpoints"""
    print(f"\n{description}")
    print(f"🧪 Probando: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            headers = {"Content-Type": "application/json"}
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        elif method == "PUT":
            headers = {"Content-Type": "application/json"}
            response = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}")
        else:
            print(f"❌ Método no soportado: {method}")
            return False
            
        print(f"Status: {response.status_code}")
        
        if response.status_code < 400:
            print("✅ ÉXITO")
        else:
            print("⚠️  ERROR ESPERADO O PROBLEMA")
            
        try:
            result = response.json()
            print(f"Respuesta: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except:
            print(f"Respuesta (texto): {response.text}")
            
        return response.status_code < 400
        
    except Exception as e:
        print(f"❌ Error en la solicitud: {e}")
        return False

def main():
    print("🚀 Iniciando pruebas CORREGIDAS de configuraciones personalizadas")
    print("=" * 60)
    
    # 1. Verificar endpoints específicos primero (no deben ser capturados por rutas dinámicas)
    test_endpoint("GET", "/config/custom/configurations/info", 
                 description="🔍 1. INFORMACIÓN DEL SISTEMA (ruta específica)")
    
    test_endpoint("GET", "/config/custom/configurations/export", 
                 description="📤 2. EXPORTAR CONFIGURACIONES (ruta específica)")
    
    # 2. Listar configuraciones (debe estar vacío inicialmente)
    test_endpoint("GET", "/config/custom/configurations", 
                 description="📋 3. LISTAR CONFIGURACIONES")
    
    # 3. Validar configuración (formato correcto con ConfigurationRequest)
    config_validation_data = {
        "name": "TestValidation",
        "configuration": {
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
    }
    
    test_endpoint("POST", "/config/custom/configurations/validate", 
                 data=config_validation_data,
                 description="✅ 4. VALIDAR CONFIGURACIÓN (formato correcto)")
    
    # 4. Guardar configuración individual (formato correcto con CustomConfiguration directamente)
    config_individual_data = {
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
    
    test_endpoint("POST", "/config/custom/configurations/BateriaLitio100Ah", 
                 data=config_individual_data,
                 description="💾 5. GUARDAR CONFIGURACIÓN INDIVIDUAL (formato correcto)")
    
    # 5. Listar configuraciones después de guardar
    test_endpoint("GET", "/config/custom/configurations", 
                 description="📋 6. LISTAR CONFIGURACIONES (después de guardar)")
    
    # 6. Obtener configuración específica
    test_endpoint("GET", "/config/custom/configurations/BateriaLitio100Ah", 
                 description="🔍 7. OBTENER CONFIGURACIÓN ESPECÍFICA")
    
    # 7. Guardar múltiples configuraciones (formato correcto con ConfigurationData)
    multiple_configs = {
        "BateriaLitio200Ah": {
            "batteryCapacity": 200.0,
            "isLithium": True,
            "thresholdPercentage": 2.0,
            "maxAllowedCurrent": 15000.0,
            "bulkVoltage": 14.4,
            "absorptionVoltage": 14.4,
            "floatVoltage": 13.6,
            "useFuenteDC": False,
            "fuenteDC_Amps": 0.0,
            "factorDivider": 1
        },
        "BateriaGEL150Ah": {
            "batteryCapacity": 150.0,
            "isLithium": False,
            "thresholdPercentage": 2.0,
            "maxAllowedCurrent": 10000.0,
            "bulkVoltage": 14.1,
            "absorptionVoltage": 14.1,
            "floatVoltage": 13.3,
            "useFuenteDC": False,
            "fuenteDC_Amps": 0.0,
            "factorDivider": 1
        }
    }
    
    config_multiple_data = {
        "data": json.dumps(multiple_configs)
    }
    
    test_endpoint("POST", "/config/custom/configurations", 
                 data=config_multiple_data,
                 description="💾 8. GUARDAR MÚLTIPLES CONFIGURACIONES (formato correcto)")
    
    # 8. Importar configuraciones (formato correcto con ConfigurationImportRequest)
    import_data = {
        "configurations_data": json.dumps({
            "BateriaImportada": {
                "batteryCapacity": 300.0,
                "isLithium": True,
                "thresholdPercentage": 1.5,
                "maxAllowedCurrent": 12000.0,
                "bulkVoltage": 14.6,
                "absorptionVoltage": 14.6,
                "floatVoltage": 13.8,
                "useFuenteDC": False,
                "fuenteDC_Amps": 0.0,
                "factorDivider": 1
            }
        }),
        "overwrite_existing": False
    }
    
    test_endpoint("POST", "/config/custom/configurations/import", 
                 data=import_data,
                 description="📥 9. IMPORTAR CONFIGURACIONES (formato correcto)")
    
    # 9. Aplicar configuración al ESP32
    test_endpoint("POST", "/config/custom/configurations/BateriaLitio100Ah/apply", 
                 description="⚡ 10. APLICAR CONFIGURACIÓN AL ESP32")
    
    # 10. Estado final
    test_endpoint("GET", "/config/custom/configurations", 
                 description="📋 11. ESTADO FINAL - TODAS LAS CONFIGURACIONES")
    
    # 11. Exportar al final
    test_endpoint("GET", "/config/custom/configurations/export", 
                 description="📤 12. EXPORTAR CONFIGURACIONES (después de guardar)")
    
    print("\n" + "=" * 60)
    print("🏁 Pruebas CORREGIDAS completadas")
    print("🔧 Este script usa los formatos de datos correctos para cada endpoint")
    print("📊 Los errores 422 anteriores deberían estar resueltos")
    print("\n💡 Para ver logs detallados:")
    print("   tail -f logs/esp32_api.log")
    print("\n🌐 Documentación interactiva:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()
