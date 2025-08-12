#!/usr/bin/env python3
"""
Script para resolver configuración automática de Docker Compose
Convierte valores 'auto' en valores numéricos específicos para docker-compose.yml
"""

import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from utils.cpu_detection import get_runtime_config

def resolve_auto_values():
    """Resolver valores automáticos y generar docker-compose.resolved.yml"""
    print("🔍 Resolviendo configuración automática para Docker Compose...")
    
    # Obtener configuración detectada
    config = get_runtime_config()
    
    # Crear archivo .env.resolved con valores específicos
    env_file = Path(".env")
    env_resolved_file = Path(".env.resolved")
    
    # Leer .env original
    env_content = []
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.readlines()
    
    # Resolver valores automáticos
    resolved_content = []
    replacements = {
        'CPU_LIMIT': config['cpu_limit'],
        'MEMORY_LIMIT': config['memory_limit'],
        'MAX_WORKERS': str(config['workers'])
    }
    
    for line in env_content:
        for key, value in replacements.items():
            if line.startswith(f"{key}=auto"):
                line = f"{key}={value}                 # auto-resuelto\n"
                print(f"  📝 {key}: auto → {value}")
        resolved_content.append(line)
    
    # Escribir archivo resuelto
    with open(env_resolved_file, 'w', encoding='utf-8') as f:
        f.writelines(resolved_content)
    
    # Generar docker-compose.resolved.yml con valores hardcoded
    generate_resolved_docker_compose(config)
    
    print(f"✅ Configuración resuelta guardada en {env_resolved_file}")
    
    # Mostrar resumen
    print("\n📋 Configuración detectada:")
    print(f"   🏗️  Arquitectura: {config['architecture_info']['arch_type']}")
    print(f"   🔧 CPUs: {config['architecture_info']['cpu_count']}")
    print(f"   👥 Workers: {config['workers']}")
    print(f"   ⚡ CPU Limit: {config['cpu_limit']}")
    print(f"   💾 Memory Limit: {config['memory_limit']}")
    print(f"   🚀 Modo: {'Gunicorn' if config['use_gunicorn'] else 'Uvicorn'}")
    
    return config

def generate_resolved_docker_compose(config):
    """Generar docker-compose.yml con valores resueltos"""
    
    # Leer template
    template_content = f"""# =============================================================================
# ESP32 Solar Charger API - Docker Compose RESUELTO automáticamente
# =============================================================================
# CPU_LIMIT: {config['cpu_limit']} | MEMORY_LIMIT: {config['memory_limit']} | WORKERS: {config['workers']}
# Arquitectura: {config['architecture_info']['arch_type']} ({config['architecture_info']['cpu_count']} CPUs)

services:
  esp32-api:
    build:
      context: .
      dockerfile: Dockerfile
    
    image: esp32-solar-api:latest
    container_name: esp32-solar-charger-api
    
    # 🔧 CONFIGURACIÓN DE PUERTO SERIAL DINÁMICO
    devices:
      - "${{SERIAL_PORT:-/dev/ttyUSB0}}:${{SERIAL_PORT:-/dev/ttyUSB0}}"
    
    # Cargar variables desde archivo .env.resolved
    env_file:
      - .env.resolved
    
    # Puertos de red
    ports:
      - "8000:8000"
    
    # ✅ CONFIGURACIÓN MULTI-CPU RESUELTA
    cpus: "{config['cpu_limit']}"
    mem_limit: "{config['memory_limit']}"
    memswap_limit: "{config['memory_limit']}"
    
    # Volúmenes para persistencia y desarrollo
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - .:/app/config:rw
    
    # Conectar a la red de servicios
    networks:
      - esp32-network
    
    # Dependencias de servicios
    depends_on:
      esp32-redis:
        condition: service_healthy
    
    # Health check optimizado
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"] 
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ============================================================================
  # REDIS SERVICE
  # ============================================================================
  esp32-redis:
    image: redis:7-alpine
    container_name: esp32-redis
    
    ports:
      - "6379:6379"
    
    command: >
      redis-server 
      --appendonly yes 
      --save 60 1000 
      --maxmemory 256mb 
      --maxmemory-policy allkeys-lru
      --tcp-keepalive 300
      --timeout 0
    
    volumes:
      - redis-data:/data
    
    networks:
      - esp32-network
    
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

networks:
  esp32-network:
    driver: bridge

volumes:
  redis-data:
    driver: local
"""
    
    # Escribir archivo resuelto
    with open("docker-compose.resolved.yml", "w", encoding="utf-8") as f:
        f.write(template_content)
    
    print("✅ docker-compose.resolved.yml generado con valores hardcoded")

if __name__ == "__main__":
    resolve_auto_values()
