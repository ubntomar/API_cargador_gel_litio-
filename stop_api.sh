#!/bin/bash
# =============================================================================
# ESP32 Solar Charger API - Detenedor Universal Multi-Arquitectura
# Compatible con todas las arquitecturas y métodos de ejecución
# =============================================================================

# Detección de arquitectura para información
ARCH=$(uname -m)
case "$ARCH" in
    "riscv64") ARCH_NAME="RISC-V 64-bit" ;;
    "aarch64"|"arm64") ARCH_NAME="ARM64" ;;
    "x86_64"|"amd64") ARCH_NAME="x86_64" ;;
    *) ARCH_NAME="$ARCH" ;;
esac

echo "🛑 ESP32 Solar Charger API - Detenedor Universal"
echo "🖥️ Arquitectura: $ARCH_NAME ($ARCH)"
echo "================================================"

# Detener API en modo desarrollo/directo
echo "🔍 Buscando procesos de la API..."
PROCESSES_FOUND=false

if pkill -f "main.py" 2>/dev/null; then
    echo "✅ API principal (main.py) detenida"
    PROCESSES_FOUND=true
fi

if pkill -f "uvicorn.*main" 2>/dev/null; then
    echo "✅ Servidor Uvicorn detenido"
    PROCESSES_FOUND=true
fi

# Detener contenedores Docker si están ejecutándose
if command -v docker &> /dev/null; then
    echo "🐳 Verificando contenedores Docker..."
    
    # Buscar contenedores relacionados con ESP32 API
    ESP32_CONTAINERS=$(docker ps -q --filter "name=esp32" 2>/dev/null)
    API_CONTAINERS=$(docker ps -q --filter "name=api" 2>/dev/null)
    
    if [ -n "$ESP32_CONTAINERS" ] || [ -n "$API_CONTAINERS" ]; then
        echo "🛑 Deteniendo contenedores Docker..."
        
        if [ -n "$ESP32_CONTAINERS" ]; then
            docker stop $ESP32_CONTAINERS && echo "✅ Contenedores ESP32 detenidos"
        fi
        
        if [ -n "$API_CONTAINERS" ]; then
            docker stop $API_CONTAINERS && echo "✅ Contenedores API detenidos"
        fi
        
        PROCESSES_FOUND=true
    fi
    
    # Verificar docker-compose
    if [ -f "docker-compose.yml" ] || [ -f "docker-compose.resolved.yml" ]; then
        echo "🔧 Verificando docker-compose..."
        if docker-compose ps 2>/dev/null | grep -q "Up"; then
            docker-compose down && echo "✅ Docker Compose detenido"
            PROCESSES_FOUND=true
        fi
    fi
fi

if [ "$PROCESSES_FOUND" = false ]; then
    echo "ℹ️ No se encontraron procesos de la API ejecutándose"
else
    echo ""
    echo "✅ ESP32 Solar Charger API detenida completamente"
    echo "🏁 Todos los procesos relacionados han sido terminados"
fi
