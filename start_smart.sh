#!/bin/bash
# =============================================================================
# ESP32 Solar Charger API - Smart Startup Script
# Script de inicio inteligente con detección multi-CPU universal
# Compatible con: x86, ARM, RISC-V
# =============================================================================

set -e  # Salir en caso de error

echo "==============================================="
echo "🚀 ESP32 Solar Charger API - Startup Inteligente"
echo "==============================================="

# Variables de entorno con defaults
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export SERIAL_PORT=${SERIAL_PORT:-/dev/ttyUSB0}
export DEBUG=${DEBUG:-false}
export MAX_WORKERS=${MAX_WORKERS:-auto}
export CPU_LIMIT=${CPU_LIMIT:-auto}
export MEMORY_LIMIT=${MEMORY_LIMIT:-auto}
export FORCE_SINGLE_WORKER=${FORCE_SINGLE_WORKER:-false}

# Detectar información del sistema
echo "🔍 Detectando configuración del sistema..."
echo "📡 Puerto Serial: ${SERIAL_PORT}"
echo "🌐 Puerto HTTP: ${PORT}"
echo "🏗️ Plataforma: $(uname -m)"
echo "🔧 CPUs disponibles: $(nproc)"
echo "💾 Memoria total: $(free -h | grep '^Mem:' | awk '{print $2}' || echo 'N/A')"
echo "🚀 Workers configurados: ${MAX_WORKERS}"
echo "⚡ Límite CPU: ${CPU_LIMIT}"
echo "💾 Límite memoria: ${MEMORY_LIMIT}"
echo "🏃 Modo debug: ${DEBUG}"
echo "🔐 Forzar single worker: ${FORCE_SINGLE_WORKER}"
echo "🕐 Hora: $(date)"
echo "==============================================="

# Verificar puerto serial
echo "🔌 Verificando puerto serial..."
if [ ! -e "${SERIAL_PORT}" ]; then
    echo "⚠️ Puerto serial ${SERIAL_PORT} no encontrado"
    echo "📋 Puertos disponibles:"
    ls -la /dev/tty* 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)" || echo "   No se encontraron puertos seriales"
    echo ""
    echo "💡 Sugerencias por plataforma:"
    echo "   🍊 Orange Pi R2S: /dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyS5"
    echo "   🍓 Raspberry Pi: /dev/ttyACM0, /dev/ttyUSB0"
    echo "   🖥️ PC Linux: /dev/ttyUSB0, /dev/ttyACM0"
    echo ""
else
    echo "✅ Puerto serial ${SERIAL_PORT} encontrado"
fi

# Verificar permisos
if [ -e "${SERIAL_PORT}" ]; then
    if [ ! -r "${SERIAL_PORT}" ] || [ ! -w "${SERIAL_PORT}" ]; then
        echo "⚠️ Sin permisos para ${SERIAL_PORT}"
        echo "🔧 Ejecuta: sudo chmod 666 ${SERIAL_PORT}"
        echo "   O agrega usuario al grupo dialout: sudo usermod -a -G dialout \$USER"
    else
        echo "✅ Permisos OK para ${SERIAL_PORT}"
    fi
fi

# Verificar dependencias Python críticas
echo ""
echo "🐍 Verificando dependencias Python..."
python3 -c "
import sys
try:
    import fastapi, uvicorn, gunicorn
    print('✅ FastAPI, Uvicorn, Gunicorn disponibles')
except ImportError as e:
    print(f'❌ Error importando dependencias: {e}')
    sys.exit(1)

try:
    import multiprocessing
    cpus = multiprocessing.cpu_count()
    print(f'✅ Detección de CPU OK: {cpus} núcleos')
except Exception as e:
    print(f'⚠️ Error detección CPU: {e}')
"

# Configurar variables de entorno para threading
echo ""
echo "🔧 Configurando variables de threading..."

# Si OMP_NUM_THREADS es 'auto', detectar automáticamente
if [ "${OMP_NUM_THREADS:-auto}" = "auto" ]; then
    CPU_COUNT=$(nproc)
    if [ "$CPU_COUNT" -gt 4 ]; then
        export OMP_NUM_THREADS=4
    else
        export OMP_NUM_THREADS=$CPU_COUNT
    fi
    echo "🔢 OMP_NUM_THREADS auto-detectado: ${OMP_NUM_THREADS}"
else
    echo "🔢 OMP_NUM_THREADS manual: ${OMP_NUM_THREADS}"
fi

# Configurar otras variables de optimización
export MALLOC_ARENA_MAX=4
export UV_THREADPOOL_SIZE=4

echo "✅ Variables de threading configuradas"

# Función para detectar modo de ejecución
detect_execution_mode() {
    # Si está forzado single worker
    if [ "${FORCE_SINGLE_WORKER}" = "true" ]; then
        echo "single"
        return
    fi
    
    # Si MAX_WORKERS es un número específico > 1
    if [ "${MAX_WORKERS}" != "auto" ] && [ "${MAX_WORKERS}" -gt 1 ] 2>/dev/null; then
        echo "multi"
        return
    fi
    
    # Si MAX_WORKERS es auto, detectar según CPUs
    if [ "${MAX_WORKERS}" = "auto" ]; then
        CPU_COUNT=$(nproc)
        if [ "$CPU_COUNT" -gt 2 ]; then
            echo "multi"
        else
            echo "single"
        fi
        return
    fi
    
    # Default: single worker
    echo "single"
}

# Detectar modo de ejecución
EXECUTION_MODE=$(detect_execution_mode)

echo ""
echo "🎯 Modo de ejecución detectado: ${EXECUTION_MODE}"

# Configurar CMD según el modo
if [ "$EXECUTION_MODE" = "multi" ]; then
    echo "🚀 Iniciando con Gunicorn multi-worker..."
    echo "💡 Para single-worker: MAX_WORKERS=1 o FORCE_SINGLE_WORKER=true"
    
    # Verificar que gunicorn_conf.py existe
    if [ ! -f "gunicorn_conf.py" ]; then
        echo "❌ gunicorn_conf.py no encontrado, fallback a single-worker"
        EXECUTION_MODE="single"
    else
        echo "✅ Configuración Gunicorn encontrada"
        
        # Intentar con Gunicorn
        echo "🏃 Ejecutando: gunicorn --config gunicorn_conf.py main:app"
        exec gunicorn --config gunicorn_conf.py main:app
    fi
fi

if [ "$EXECUTION_MODE" = "single" ]; then
    echo "🔧 Iniciando con Uvicorn single-worker..."
    echo "💡 Para multi-worker: MAX_WORKERS=auto en .env"
    
    # Configurar argumentos de Uvicorn
    UVICORN_ARGS="main:app --host ${HOST} --port ${PORT}"
    
    if [ "${DEBUG}" = "true" ]; then
        UVICORN_ARGS="${UVICORN_ARGS} --reload"
        echo "🔧 Modo debug activado (auto-reload)"
    fi
    
    echo "🏃 Ejecutando: uvicorn ${UVICORN_ARGS}"
    exec uvicorn $UVICORN_ARGS
fi

echo "❌ Error: No se pudo determinar modo de ejecución"
exit 1
