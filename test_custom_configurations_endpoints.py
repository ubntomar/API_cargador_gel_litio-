#!/usr/bin/env python3
"""
Script de pruebas específico para endpoints de configuraciones personalizadas
"""

import requests
import json
import time

# URL base de la API
BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, expected_status=[200, 201]):
    """Función helper para probar endpoints"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🧪 Probando: {method.upper()} {endpoint}")
    
    try:
        if method.lower() == 'get':
            response = requests.get(url)
        elif method.lower() == 'post':
            response = requests.post(url, json=data)
        elif method.lower() == 'put':
            response = requests.put(url, json=data)
        elif method.lower() == 'delete':
            response = requests.delete(url)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code in expected_status:
            print("✅ ÉXITO")
            try:
                json_data = response.json()
                print(f"Respuesta: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
                return json_data
            except:
                print(f"Respuesta (texto): {response.text[:200]}")
                return response.text
        else:
            print(f"❌ ERROR - Status esperado: {expected_status}, recibido: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se puede conectar a la API. ¿Está ejecutándose?")
        return None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def main():
    """Función principal de pruebas"""
    
    print("🚀 Iniciando pruebas de configuraciones personalizadas")
    print("=" * 60)
    
    # 1. Probar listar configuraciones (debería estar vacío inicialmente)
    print("\n📋 1. LISTAR CONFIGURACIONES")
    configs = test_endpoint('GET', '/config/custom/configurations')
    
    # 2. Probar información del sistema
    print("\n🔍 2. INFORMACIÓN DEL SISTEMA")
    info = test_endpoint('GET', '/config/custom/configurations/info', expected_status=[200, 404])
    
    # 3. Probar validación de configuración
    print("\n✅ 3. VALIDAR CONFIGURACIÓN")
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
    
    validation = test_endpoint('POST', '/config/custom/configurations/validate', 
                              config_data, expected_status=[200, 422])
    
    # 4. Probar guardar configuración individual
    print("\n💾 4. GUARDAR CONFIGURACIÓN INDIVIDUAL")
    save_result = test_endpoint('POST', '/config/custom/configurations/TestBateria100Ah', 
                               config_data, expected_status=[200, 201, 422])
    
    # 5. Probar exportar configuraciones
    print("\n📤 5. EXPORTAR CONFIGURACIONES")
    export = test_endpoint('GET', '/config/custom/configurations/export', 
                          expected_status=[200, 404])
    
    # 6. Probar listar configuraciones de nuevo (debería tener la que guardamos)
    print("\n📋 6. LISTAR CONFIGURACIONES (DESPUÉS DE GUARDAR)")
    configs_after = test_endpoint('GET', '/config/custom/configurations')
    
    # 7. Probar obtener configuración específica
    print("\n🔍 7. OBTENER CONFIGURACIÓN ESPECÍFICA")
    specific = test_endpoint('GET', '/config/custom/configurations/TestBateria100Ah',
                           expected_status=[200, 404])
    
    # 8. Probar guardar múltiples configuraciones
    print("\n💾 8. GUARDAR MÚLTIPLES CONFIGURACIONES")
    multiple_data = {
        "data": {
            "BateriaLitio200Ah": {
                **config_data,
                "batteryCapacity": 200.0,
                "maxAllowedCurrent": 15000.0
            },
            "BateriaGEL150Ah": {
                **config_data,
                "batteryCapacity": 150.0,
                "isLithium": False,
                "bulkVoltage": 14.1,
                "absorptionVoltage": 14.1,
                "floatVoltage": 13.3
            }
        }
    }
    
    multiple_save = test_endpoint('POST', '/config/custom/configurations', 
                                 multiple_data, expected_status=[200, 201, 422])
    
    # 9. Probar importar configuraciones
    print("\n📥 9. IMPORTAR CONFIGURACIONES")
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
    
    import_result = test_endpoint('POST', '/config/custom/configurations/import', 
                                 import_data, expected_status=[200, 201, 422])
    
    # 10. Estado final - listar todas las configuraciones
    print("\n📋 10. ESTADO FINAL - TODAS LAS CONFIGURACIONES")
    final_configs = test_endpoint('GET', '/config/custom/configurations')
    
    print("\n" + "=" * 60)
    print("🏁 Pruebas completadas")
    
    if final_configs and isinstance(final_configs, dict):
        total = final_configs.get('total_count', 0)
        print(f"📊 Total de configuraciones guardadas: {total}")
        
        if total > 0:
            print("✅ ¡El sistema de configuraciones personalizadas está funcionando!")
        else:
            print("⚠️  No se guardaron configuraciones. Revisa los logs de la API.")
    
    print("\n💡 Para ver más detalles, revisa los logs de la API:")
    print("   tail -f logs/esp32_api.log")
    print("\n🌐 Documentación interactiva disponible en:")
    print("   http://localhost:8000/docs")

if __name__ == "__main__":
    main()
