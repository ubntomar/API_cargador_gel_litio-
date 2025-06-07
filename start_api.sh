#!/bin/bash
# Script para iniciar la API

#darle tiempo al crontab para que se ejecute
sleep 10

# Activar entorno virtual
source venv/bin/activate

# Verificar puerto serial
if [ ! -e "/dev/ttyS5" ]; then
    echo "⚠️ Puerto /dev/ttyS5 no encontrado"
    echo "Puertos disponibles:"
    ls -la /dev/tty* | grep -E "(ttyS|ttyUSB|ttyACM)" 2>/dev/null || echo "No se encontraron puertos seriales"
fi

echo "🚀 Iniciando ESP32 Solar Charger API..."
echo "📡 Puerto: ${SERIAL_PORT:-/dev/ttyS5}"
echo "🌐 URL: http://localhost:${PORT:-8000}"
echo "📚 Docs: http://localhost:${PORT:-8000}/docs"
echo ""
echo "Presiona Ctrl+C para detener"
echo "=========================="

python main.py
