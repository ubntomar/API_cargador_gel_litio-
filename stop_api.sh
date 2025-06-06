#!/bin/bash
# Script para detener la API

echo "🛑 Deteniendo ESP32 Solar Charger API..."

# Buscar y matar procesos
pkill -f "main.py" && echo "✅ API detenida"
pkill -f "uvicorn.*main" && echo "✅ Uvicorn detenido"

echo "✅ API detenida completamente"
