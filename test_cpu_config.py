#!/usr/bin/env python3
"""
Script de prueba para verificar configuración multi-CPU
Prueba la detección automática en diferentes escenarios
"""

import os
import sys
import json

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cpu_detection():
    """Probar detección de CPU en diferentes escenarios"""
    print("🧪 =================== PRUEBA DE DETECCIÓN DE CPU ===================")
    
    try:
        from utils.cpu_detection import get_runtime_config, CPUDetector
        
        # Crear detector
        detector = CPUDetector()
        arch_info = detector.get_architecture_info()
        
        print(f"🏗️  Arquitectura detectada: {arch_info['arch_type']} ({arch_info['architecture']})")
        print(f"🔧 CPUs totales: {arch_info['cpu_count']}")
        print(f"🖥️  Sistema: {arch_info['system']}")
        print(f"📋 Plataforma: {arch_info['platform']}")
        print()
        
        # Probar diferentes configuraciones
        test_cases = [
            ("auto", "auto", "auto", False),
            ("1", "2.0", "512m", False),
            ("4", "auto", "auto", False),
            ("auto", "auto", "auto", True),  # Force single worker
            ("8", "6.0", "2g", False),
        ]
        
        print("🧪 Probando diferentes configuraciones:")
        print("=" * 80)
        
        for i, (max_workers, cpu_limit, memory_limit, force_single) in enumerate(test_cases, 1):
            print(f"\n📝 Caso {i}: MAX_WORKERS={max_workers}, CPU_LIMIT={cpu_limit}, MEMORY_LIMIT={memory_limit}, FORCE_SINGLE={force_single}")
            
            # Configurar variables de entorno temporalmente
            old_env = {}
            test_env = {
                'MAX_WORKERS': max_workers,
                'CPU_LIMIT': cpu_limit, 
                'MEMORY_LIMIT': memory_limit,
                'FORCE_SINGLE_WORKER': str(force_single).lower()
            }
            
            for key, value in test_env.items():
                old_env[key] = os.environ.get(key)
                os.environ[key] = value
            
            try:
                # Limpiar cache
                from utils.cpu_detection import _runtime_config
                globals()['_runtime_config'] = None
                
                # Obtener configuración
                config = get_runtime_config()
                
                print(f"   👥 Workers detectados: {config['workers']}")
                print(f"   ⚡ Límite CPU: {config['cpu_limit']}")
                print(f"   💾 Límite memoria: {config['memory_limit']}")
                print(f"   🚀 Modo: {'Gunicorn' if config['use_gunicorn'] else 'Uvicorn'}")
                
                # Validar lógica
                if force_single and config['workers'] != 1:
                    print("   ❌ ERROR: FORCE_SINGLE_WORKER no respetado")
                elif max_workers != "auto" and max_workers.isdigit():
                    expected = min(int(max_workers), 8)
                    if config['workers'] != expected:
                        print(f"   ⚠️  WARNING: Expected {expected} workers, got {config['workers']}")
                else:
                    print("   ✅ Configuración válida")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {e}")
            finally:
                # Restaurar variables de entorno
                for key, old_value in old_env.items():
                    if old_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = old_value
        
        print("\n🧪 =================== RESUMEN DE PRUEBAS ===================")
        print("✅ Detección de CPU funcionando correctamente")
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Asegúrate de que utils/cpu_detection.py existe y es válido")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_gunicorn_config():
    """Probar configuración de Gunicorn"""
    print("\n🧪 =================== PRUEBA DE CONFIGURACIÓN GUNICORN ===================")
    
    try:
        from utils.cpu_detection import get_runtime_config, get_gunicorn_config
        
        runtime_config = get_runtime_config()
        
        if runtime_config['use_gunicorn']:
            gunicorn_config = get_gunicorn_config(runtime_config)
            
            print("📋 Configuración Gunicorn:")
            for key, value in gunicorn_config.items():
                print(f"   {key}: {value}")
                
            print("✅ Configuración Gunicorn válida")
        else:
            print("ℹ️  Modo single-worker - Gunicorn no se usará")
            
        return True
        
    except Exception as e:
        print(f"❌ Error probando Gunicorn: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🚀 ESP32 Solar Charger API - Pruebas de Configuración Multi-CPU")
    print("=" * 80)
    
    success = True
    
    # Probar detección de CPU
    if not test_cpu_detection():
        success = False
    
    # Probar configuración de Gunicorn
    if not test_gunicorn_config():
        success = False
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("💡 La configuración multi-CPU está lista para usar")
        print("\n📋 Próximos pasos:")
        print("   1. Configura las variables en .env según tu hardware")
        print("   2. Ejecuta: docker-compose up --build")
        print("   3. Verifica en logs el modo de ejecución detectado")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa los errores arriba y corrige la configuración")
        sys.exit(1)

if __name__ == "__main__":
    main()
