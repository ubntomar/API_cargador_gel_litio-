#!/usr/bin/env python3
"""
Test para verificar el endpoint correcto de /data
"""

import requests

API_BASE_URL = "http://192.168.13.253:8000"

def test_data_endpoints():
    """Probar ambas variantes del endpoint /data"""
    
    endpoints_to_test = [
        "/data",     # Sin barra final
        "/data/",    # Con barra final
    ]
    
    print("🧪 Probando endpoints de datos del ESP32...")
    
    for endpoint in endpoints_to_test:
        url = f"{API_BASE_URL}{endpoint}"
        print(f"\n📍 Probando: {endpoint}")
        print(f"   URL completa: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Funciona correctamente")
                
                # Verificar que es JSON válido
                try:
                    data = response.json()
                    print(f"   📊 Campos en respuesta: {len(data)} campos")
                    
                    # Mostrar algunos campos importantes
                    important_fields = ["batteryVoltage", "batteryPercentage", "isCharging"]
                    found_fields = [field for field in important_fields if field in data]
                    print(f"   🔍 Campos importantes encontrados: {found_fields}")
                    
                except Exception as json_error:
                    print(f"   ⚠️ Respuesta no es JSON válido: {json_error}")
                    
            elif response.status_code == 404:
                print("   ❌ Endpoint no encontrado (404)")
            elif response.status_code == 503:
                print("   ⚠️ ESP32 no conectado (503) - esperado en pruebas")
            else:
                print(f"   ⚠️ Status inesperado: {response.status_code}")
                print(f"   📝 Respuesta: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Error de conexión - API no está ejecutándose")
        except requests.exceptions.Timeout:
            print("   ❌ Timeout - API no responde")
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")
    
    print(f"\n🎯 Conclusión:")
    print("   - Ambos endpoints deberían funcionar en FastAPI")
    print("   - Recomendado usar /data (sin barra) para consistencia")
    print("   - Actualizar documentación si es necesario")

if __name__ == "__main__":
    test_data_endpoints()
