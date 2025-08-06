#!/usr/bin/env python3
"""
Test script para verificar que la nueva ruta POST /config/parameter funciona
"""

import requests
import json

# URL de la API
API_BASE_URL = "http://192.168.13.253:8000"

def test_post_parameter():
    """Probar la nueva ruta POST /config/parameter"""
    
    url = f"{API_BASE_URL}/config/parameter"
    
    # Datos de prueba - igual a lo que envía el frontend
    test_data = {
        "parameter": "useFuenteDC",
        "value": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧪 Probando POST /config/parameter...")
    print(f"URL: {url}")
    print(f"Datos: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=10)
        
        print(f"\n📋 Respuesta:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"JSON Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"Text Response: {response.text}")
            
        # Verificar si fue exitoso
        if response.status_code == 200:
            print("✅ ¡Prueba exitosa! La ruta POST /config/parameter funciona correctamente")
            return True
        elif response.status_code == 405:
            print("❌ Error 405 (Method Not Allowed) - El problema aún persiste")
            return False
        else:
            print(f"⚠️ Status code inesperado: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión - ¿Está la API ejecutándose?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - La API no respondió a tiempo")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_old_method():
    """Probar el método antiguo PUT /config/{parameter} para comparación"""
    
    url = f"{API_BASE_URL}/config/useFuenteDC"
    
    # Datos para el método PUT
    test_data = {
        "value": True
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("\n🧪 Probando PUT /config/useFuenteDC (método original)...")
    print(f"URL: {url}")
    print(f"Datos: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.put(url, json=test_data, headers=headers, timeout=10)
        
        print(f"\n📋 Respuesta:")
        print(f"Status Code: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            response_data = response.json()
            print(f"JSON Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"Text Response: {response.text}")
            
        if response.status_code == 200:
            print("✅ Método PUT original funciona correctamente")
            return True
        else:
            print(f"⚠️ Status code inesperado: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas del endpoint de configuración...\n")
    
    # Probar nueva ruta POST
    post_success = test_post_parameter()
    
    # Probar ruta PUT original  
    put_success = test_old_method()
    
    print(f"\n📊 Resumen de pruebas:")
    print(f"POST /config/parameter: {'✅ FUNCIONA' if post_success else '❌ FALLA'}")
    print(f"PUT /config/useFuenteDC: {'✅ FUNCIONA' if put_success else '❌ FALLA'}")
    
    if post_success:
        print("\n🎉 ¡El problema está resuelto! El frontend ahora puede usar POST /config/parameter")
    else:
        print("\n🔧 Necesita más investigación o la API necesita reiniciarse")

if __name__ == "__main__":
    main()
