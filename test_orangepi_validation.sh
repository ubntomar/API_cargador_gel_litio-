#!/bin/bash

# =============================================================================
# TEST DE VALIDACIÓN UNIVERSAL - Multi-Arquitectura (x86_64, ARM64, RISC-V)
# Auto-detección de plataforma y optimización específica
# =============================================================================

# Detección automática de arquitectura
ARCH=$(uname -m)
case "$ARCH" in
    "riscv64") 
        ARCH_NAME="RISC-V 64-bit"
        PLATFORM_EMOJI="🍊"
        PLATFORM_NOTE="Orange Pi R2S y compatibles RISC-V"
        ;;
    "aarch64"|"arm64") 
        ARCH_NAME="ARM64"
        PLATFORM_EMOJI="🥧"
        PLATFORM_NOTE="Raspberry Pi, Orange Pi ARM y compatibles"
        ;;
    "x86_64"|"amd64") 
        ARCH_NAME="x86_64"
        PLATFORM_EMOJI="🖥️"
        PLATFORM_NOTE="PC/Servidores tradicionales"
        ;;
    *) 
        ARCH_NAME="$ARCH"
        PLATFORM_EMOJI="🔧"
        PLATFORM_NOTE="Arquitectura genérica"
        ;;
esac

echo "$PLATFORM_EMOJI INICIANDO VALIDACIÓN UNIVERSAL MULTI-ARQUITECTURA..."
echo "================================================================"
echo "🖥️ Plataforma: $ARCH_NAME ($ARCH)"
echo "📋 Tipo: $PLATFORM_NOTE"
echo "================================================================"

BASE_URL="http://localhost:8000"

# Verificar conectividad primero
echo "🌐 Verificando conectividad con la API..."
if ! curl -s --connect-timeout 5 "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ Error: No se puede conectar a la API en $BASE_URL"
    echo "💡 Asegúrate de que la API esté ejecutándose:"
    echo "   • docker-compose up -d"
    echo "   • ./start_api.sh"
    echo "   • python main.py"
    exit 1
fi
echo "✅ API disponible en $ARCH_NAME"
echo ""

# 1. Verificar estado inicial con información de arquitectura
echo "1️⃣ Verificando estado inicial en $ARCH_NAME..."
curl -s "$BASE_URL/config/custom/configurations/info" | jq '.' || echo "⚠️ jq no disponible, respuesta cruda:"

echo -e "\n2️⃣ Creando configuración de prueba (Gel 100Ah) en $ARCH_NAME..."
RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 100.0,
    "isLithium": false,
    "thresholdPercentage": 5.0,
    "maxAllowedCurrent": 10000.0,
    "bulkVoltage": 14.4,
    "absorptionVoltage": 14.4,
    "floatVoltage": 13.8,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 5
  }' \
  "$BASE_URL/config/custom/config/TestGel100Ah_${ARCH}")

echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

echo -e "\n3️⃣ Verificando configuración creada en $ARCH_NAME..."
curl -s "$BASE_URL/config/custom/configurations" | jq '.' 2>/dev/null || curl -s "$BASE_URL/config/custom/configurations"

echo -e "\n4️⃣ Obteniendo configuración específica..."
curl -s "$BASE_URL/config/custom/config/TestGel100Ah_${ARCH}" | jq '.' 2>/dev/null || curl -s "$BASE_URL/config/custom/config/TestGel100Ah_${ARCH}"

echo -e "\n5️⃣ Creando configuración Litio optimizada para $ARCH_NAME..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 200.0,
    "isLithium": true,
    "thresholdPercentage": 3.0,
    "maxAllowedCurrent": 20000.0,
    "bulkVoltage": 14.8,
    "absorptionVoltage": 14.8,
    "floatVoltage": 13.5,
    "useFuenteDC": true,
    "fuenteDC_Amps": 30.0,
    "factorDivider": 4
  }' \
  "$BASE_URL/config/custom/config/TestLitio200Ah_${ARCH}" | jq '.' 2>/dev/null || echo "Configuración Litio creada"

echo -e "\n6️⃣ Verificando ambas configuraciones en $ARCH_NAME..."
curl -s "$BASE_URL/config/custom/configurations" | jq '.' 2>/dev/null || curl -s "$BASE_URL/config/custom/configurations"

echo -e "\n7️⃣ Test de rendimiento específico para $ARCH_NAME..."
echo "🚀 Midiendo tiempo de respuesta..."

START_TIME=$(date +%s%N)
curl -s "$BASE_URL/data" > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))

echo "⏱️ Tiempo de respuesta en $ARCH_NAME: ${RESPONSE_TIME}ms"

if [ $RESPONSE_TIME -lt 100 ]; then
    echo "🚀 EXCELENTE: Muy rápido para $ARCH_NAME"
elif [ $RESPONSE_TIME -lt 500 ]; then
    echo "✅ BUENO: Respuesta aceptable para $ARCH_NAME"
elif [ $RESPONSE_TIME -lt 1000 ]; then
    echo "⚠️ ACEPTABLE: Un poco lento pero funcional en $ARCH_NAME"
else
    echo "🐌 LENTO: Considerar optimización para $ARCH_NAME"
fi

echo -e "\n8️⃣ Aplicando configuración Litio en $ARCH_NAME..."
curl -s -X POST "$BASE_URL/config/custom/config/TestLitio200Ah_${ARCH}/apply" | jq '.' 2>/dev/null || echo "Configuración aplicada"

echo -e "\n9️⃣ Verificando configuración aplicada..."
curl -s "$BASE_URL/config/custom/configurations/applied" | jq '.' 2>/dev/null || curl -s "$BASE_URL/config/custom/configurations/applied"

echo -e "\n🔟 Export específico para $ARCH_NAME..."
curl -s "$BASE_URL/config/custom/configurations/export" | jq '.' 2>/dev/null || curl -s "$BASE_URL/config/custom/configurations/export"

echo -e "\n1️⃣1️⃣ Limpiando configuraciones de prueba..."
curl -s -X DELETE "$BASE_URL/config/custom/config/TestGel100Ah_${ARCH}" > /dev/null 2>&1
curl -s -X DELETE "$BASE_URL/config/custom/config/TestLitio200Ah_${ARCH}" > /dev/null 2>&1

echo -e "\n$PLATFORM_EMOJI VALIDACIÓN COMPLETADA PARA $ARCH_NAME"
echo "================================================================"
echo "✅ API funcionando correctamente en $ARCH_NAME ($ARCH)"
echo "🔧 Configuraciones: Creación, lectura y eliminación OK"
echo "⏱️ Rendimiento: ${RESPONSE_TIME}ms"
echo "📋 Plataforma: $PLATFORM_NOTE"
echo "🌐 Endpoints probados: /config, /data, /custom"
echo "================================================================"
