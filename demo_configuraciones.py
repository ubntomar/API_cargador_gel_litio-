#!/usr/bin/env python3
"""
Script de demostración para el sistema de configuraciones personalizadas
"""

import requests
import json
import sys
from datetime import datetime

# Configuración de la API
API_BASE_URL = "http://localhost:8000"
CONFIG_ENDPOINT = f"{API_BASE_URL}/config/configurations"

def print_separator(title):
    """Imprimir separador con título"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_response(response, action):
    """Imprimir respuesta de la API de manera legible"""
    print(f"\n🔍 {action}")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Éxito")
        try:
            data = response.json()
            print(f"Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except:
            print(f"Respuesta: {response.text}")
    else:
        print(f"❌ Error: {response.text}")

def create_sample_configurations():
    """Crear configuraciones de ejemplo"""
    configurations = {
        "Batería Litio 100Ah": {
            "batteryCapacity": 100.0,
            "isLithium": True,
            "thresholdPercentage": 2.0,
            "maxAllowedCurrent": 10000.0,
            "bulkVoltage": 14.4,
            "absorptionVoltage": 14.4,
            "floatVoltage": 13.6,
            "useFuenteDC": False,
            "fuenteDC_Amps": 0.0,
            "factorDivider": 1,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        },
        "Batería GEL 200Ah": {
            "batteryCapacity": 200.0,
            "isLithium": False,
            "thresholdPercentage": 2.5,
            "maxAllowedCurrent": 8000.0,
            "bulkVoltage": 14.1,
            "absorptionVoltage": 14.1,
            "floatVoltage": 13.3,
            "useFuenteDC": True,
            "fuenteDC_Amps": 20.0,
            "factorDivider": 1,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        },
        "Batería AGM 150Ah": {
            "batteryCapacity": 150.0,
            "isLithium": False,
            "thresholdPercentage": 2.2,
            "maxAllowedCurrent": 9000.0,
            "bulkVoltage": 14.2,
            "absorptionVoltage": 14.2,
            "floatVoltage": 13.4,
            "useFuenteDC": False,
            "fuenteDC_Amps": 0.0,
            "factorDivider": 1,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
    }
    return configurations

def demo_save_configurations():
    """Demostrar guardado de configuraciones"""
    print_separator("DEMOSTRACIÓN: Guardar Configuraciones")
    
    configurations = create_sample_configurations()
    
    # Convertir a JSON string como requiere la API
    payload = {
        "data": json.dumps(configurations)
    }
    
    print("📝 Configuraciones a guardar:")
    for name, config in configurations.items():
        battery_type = "Litio" if config["isLithium"] else "GEL/AGM"
        print(f"  • {name}: {config['batteryCapacity']}Ah ({battery_type})")
    
    try:
        response = requests.post(CONFIG_ENDPOINT, json=payload)
        print_response(response, "Guardando configuraciones")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API. ¿Está ejecutándose el servidor?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def demo_load_configurations():
    """Demostrar carga de configuraciones"""
    print_separator("DEMOSTRACIÓN: Cargar Configuraciones")
    
    try:
        response = requests.get(CONFIG_ENDPOINT)
        print_response(response, "Cargando configuraciones")
        
        if response.status_code == 200:
            data = response.json()
            configurations = data.get("configurations", {})
            total_count = data.get("total_count", 0)
            
            print(f"\n📋 Resumen de configuraciones cargadas:")
            print(f"  Total: {total_count} configuraciones")
            
            for name, config in configurations.items():
                battery_type = "Litio" if config.get("isLithium") else "GEL/AGM"
                capacity = config.get("batteryCapacity", "?")
                bulk_voltage = config.get("bulkVoltage", "?")
                print(f"  • {name}:")
                print(f"    - Capacidad: {capacity}Ah")
                print(f"    - Tipo: {battery_type}")
                print(f"    - Voltaje BULK: {bulk_voltage}V")
            
            return True
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def demo_get_single_configuration():
    """Demostrar obtención de configuración individual"""
    print_separator("DEMOSTRACIÓN: Obtener Configuración Individual")
    
    config_name = "Batería Litio 100Ah"
    endpoint = f"{CONFIG_ENDPOINT}/{config_name}"
    
    try:
        response = requests.get(endpoint)
        print_response(response, f"Obteniendo configuración '{config_name}'")
        
        if response.status_code == 200:
            data = response.json()
            config = data.get("configuration", {})
            
            print(f"\n📄 Detalles de '{config_name}':")
            print(f"  Capacidad: {config.get('batteryCapacity')}Ah")
            print(f"  Tipo: {'Litio' if config.get('isLithium') else 'GEL/AGM'}")
            print(f"  Voltajes: BULK={config.get('bulkVoltage')}V, Float={config.get('floatVoltage')}V")
            print(f"  Corriente máx: {config.get('maxAllowedCurrent')}mA")
            print(f"  Fuente DC: {'Sí' if config.get('useFuenteDC') else 'No'}")
            return True
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def demo_save_single_configuration():
    """Demostrar guardado de configuración individual"""
    print_separator("DEMOSTRACIÓN: Guardar Configuración Individual")
    
    config_name = "Batería Personalizada Demo"
    configuration = {
        "batteryCapacity": 75.0,
        "isLithium": True,
        "thresholdPercentage": 1.8,
        "maxAllowedCurrent": 12000.0,
        "bulkVoltage": 14.5,
        "absorptionVoltage": 14.5,
        "floatVoltage": 13.7,
        "useFuenteDC": True,
        "fuenteDC_Amps": 15.0,
        "factorDivider": 1
    }
    
    endpoint = f"{CONFIG_ENDPOINT}/{config_name}"
    
    print(f"💾 Guardando configuración personalizada '{config_name}':")
    print(f"  Capacidad: {configuration['batteryCapacity']}Ah (Litio)")
    print(f"  Voltaje BULK: {configuration['bulkVoltage']}V")
    print(f"  Fuente DC: {configuration['fuenteDC_Amps']}A")
    
    try:
        response = requests.post(endpoint, json=configuration)
        print_response(response, f"Guardando configuración '{config_name}'")
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def demo_export_configurations():
    """Demostrar exportación de configuraciones"""
    print_separator("DEMOSTRACIÓN: Exportar Configuraciones")
    
    endpoint = f"{CONFIG_ENDPOINT}/export"
    
    try:
        response = requests.get(endpoint)
        print_response(response, "Exportando configuraciones")
        
        if response.status_code == 200:
            data = response.json()
            filename = data.get("filename", "configuraciones.json")
            content = data.get("content", "{}")
            count = data.get("configurations_count", 0)
            
            print(f"\n📤 Exportación completada:")
            print(f"  Archivo: {filename}")
            print(f"  Configuraciones: {count}")
            print(f"  Tamaño: {len(content)} caracteres")
            
            # Guardar archivo localmente para demostración
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  💾 Archivo guardado localmente: {filename}")
            except Exception as e:
                print(f"  ⚠️ No se pudo guardar localmente: {e}")
            
            return True
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def demo_configuration_info():
    """Demostrar información del sistema de configuraciones"""
    print_separator("DEMOSTRACIÓN: Información del Sistema")
    
    endpoint = f"{CONFIG_ENDPOINT}/info"
    
    try:
        response = requests.get(endpoint)
        print_response(response, "Obteniendo información del sistema")
        
        if response.status_code == 200:
            data = response.json()
            file_info = data.get("file_info", {})
            stats = data.get("statistics", {})
            
            print(f"\n📊 Información del sistema:")
            print(f"  Archivo de configuraciones:")
            print(f"    - Existe: {'Sí' if file_info.get('exists') else 'No'}")
            print(f"    - Ruta: {file_info.get('path', 'N/A')}")
            print(f"    - Tamaño: {file_info.get('size_bytes', 0)} bytes")
            
            print(f"  Estadísticas:")
            print(f"    - Total configuraciones: {stats.get('total_configurations', 0)}")
            print(f"    - Configuraciones Litio: {stats.get('lithium_configs', 0)}")
            print(f"    - Configuraciones GEL: {stats.get('gel_configs', 0)}")
            
            names = stats.get('configuration_names', [])
            if names:
                print(f"  Nombres de configuraciones:")
                for name in names:
                    print(f"    • {name}")
            
            return True
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    """Función principal de demostración"""
    print("🚀 DEMOSTRACIÓN DEL SISTEMA DE CONFIGURACIONES PERSONALIZADAS")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Asegúrate de que la API esté ejecutándose en {API_BASE_URL}")
    
    # Secuencia de demostraciones
    demos = [
        ("Guardar configuraciones de ejemplo", demo_save_configurations),
        ("Cargar todas las configuraciones", demo_load_configurations),
        ("Obtener configuración individual", demo_get_single_configuration),
        ("Guardar configuración individual", demo_save_single_configuration),
        ("Cargar configuraciones actualizadas", demo_load_configurations),
        ("Exportar configuraciones", demo_export_configurations),
        ("Información del sistema", demo_configuration_info)
    ]
    
    print(f"\n🎯 Se ejecutarán {len(demos)} demostraciones:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    
    input("\n⏎ Presiona ENTER para continuar...")
    
    success_count = 0
    
    for i, (name, demo_func) in enumerate(demos, 1):
        print(f"\n🔄 Ejecutando demostración {i}/{len(demos)}: {name}")
        
        try:
            if demo_func():
                success_count += 1
                print("✅ Demostración completada exitosamente")
            else:
                print("❌ Demostración falló")
        except KeyboardInterrupt:
            print("\n🛑 Demostración interrumpida por el usuario")
            break
        except Exception as e:
            print(f"❌ Error inesperado en demostración: {e}")
        
        if i < len(demos):
            input("\n⏎ Presiona ENTER para continuar con la siguiente demostración...")
    
    # Resumen final
    print_separator("RESUMEN DE DEMOSTRACIONES")
    print(f"✅ Exitosas: {success_count}/{len(demos)}")
    print(f"❌ Fallidas: {len(demos) - success_count}/{len(demos)}")
    
    if success_count == len(demos):
        print("\n🎉 ¡Todas las demostraciones fueron exitosas!")
        print("El sistema de configuraciones personalizadas está funcionando correctamente.")
    else:
        print("\n⚠️ Algunas demostraciones fallaron.")
        print("Verifica que la API esté ejecutándose y sea accesible.")
    
    print("\n📝 Próximos pasos recomendados:")
    print("1. Integrar con el frontend para la interfaz de usuario")
    print("2. Implementar la aplicación automática de configuraciones")
    print("3. Agregar validaciones adicionales según necesidades específicas")
    print("4. Configurar respaldos automáticos del archivo de configuraciones")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Demostración interrumpida")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(1)
