#!/bin/bash
# =============================================================================
# ESP32 Solar Charger API - Iniciador Universal Multi-Arquitectura  
# Compatible con x86_64, ARM64, RISC-V y auto-detección de puertos
# =============================================================================

# Darle tiempo al crontab para que se ejecute
sleep 10

# Activar entorno virtual
source venv/bin/activate

# Detección automática de arquitectura
ARCH=$(uname -m)
case "$ARCH" in
    "riscv64") ARCH_NAME="RISC-V 64-bit" ;;
    "aarch64"|"arm64") ARCH_NAME="ARM64" ;;
    "x86_64"|"amd64") ARCH_NAME="x86_64" ;;
    *) ARCH_NAME="$ARCH" ;;
esac

echo "🏗️ ESP32 Solar Charger API - Iniciador Universal"
echo "🖥️ Arquitectura detectada: $ARCH_NAME ($ARCH)"
echo "=================================================="

# Auto-detección inteligente de puerto serial
detect_serial_port() {
    local detected_port=""
    
    # Prioridad de detección: ESP32 específicos > USB genéricos > Seriales nativos
    for port in /dev/ttyUSB* /dev/ttyACM* /dev/ttyS*; do
        if [ -e "$port" ] && [ -r "$port" ] && [ -w "$port" ]; then
            detected_port="$port"
            break
        fi
    done
    
    echo "$detected_port"
}

# Verificar puerto serial con auto-detección
SERIAL_PORT_DEFAULT="/dev/ttyS5"
DETECTED_PORT=$(detect_serial_port)

if [ -n "$DETECTED_PORT" ]; then
    SERIAL_PORT="${SERIAL_PORT:-$DETECTED_PORT}"
    echo "🔍 Puerto auto-detectado: $DETECTED_PORT"
elif [ -e "$SERIAL_PORT_DEFAULT" ]; then
    SERIAL_PORT="${SERIAL_PORT:-$SERIAL_PORT_DEFAULT}"
    echo "📡 Usando puerto por defecto: $SERIAL_PORT_DEFAULT"
else
    SERIAL_PORT="${SERIAL_PORT:-$SERIAL_PORT_DEFAULT}"
    echo "⚠️ Puerto $SERIAL_PORT no encontrado - Continuando de todos modos"
    echo "💡 Puertos disponibles:"
    ls -la /dev/tty* 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)" | head -5 || echo "   No se encontraron puertos seriales"
fi

echo ""
echo "🚀 Iniciando ESP32 Solar Charger API..."
echo "🖥️ Arquitectura: $ARCH_NAME"
echo "📡 Puerto: $SERIAL_PORT"
echo "🌐 URL: http://localhost:${PORT:-8000}"
echo "📚 Docs: http://localhost:${PORT:-8000}/docs"
echo "🔧 Admin: http://localhost:${PORT:-8000}/admin"
echo ""
echo "💡 Presiona Ctrl+C para detener"
echo "====================================="

python main.py
