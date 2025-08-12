#!/bin/bash
# =============================================================================
# ESP32 Solar Charger API - Script de inicio con auto-detección de CPU
# =============================================================================

echo "🚀 ESP32 Solar Charger API - Startup con Multi-CPU"
echo "=================================================="

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
fi

# Resolver configuración automática
echo "🔍 Resolviendo configuración automática..."
python3 resolve_docker_config.py

if [ $? -ne 0 ]; then
    echo "❌ Error resolviendo configuración automática"
    exit 1
fi

# Construir y ejecutar con Docker Compose
echo "🐳 Construyendo y ejecutando contenedores..."
docker compose -f docker-compose.resolved.yml up --build

echo "✅ API iniciada con configuración multi-CPU"
