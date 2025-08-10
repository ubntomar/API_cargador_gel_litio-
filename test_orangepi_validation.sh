#!/bin/bash

# =============================================================================
# TEST DE VALIDACIÓN COMPLETA - Orange Pi R2S (RISC-V)
# =============================================================================

echo "🔋 INICIANDO VALIDACIÓN COMPLETA EN ORANGE PI R2S..."
echo "================================================================"

BASE_URL="http://localhost:8000"

# 1. Verificar estado inicial
echo "1️⃣ Verificando estado inicial..."
curl -s "$BASE_URL/config/custom/configurations/info" | jq '.'

echo -e "\n2️⃣ Creando configuración de prueba (Gel 100Ah)..."
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
  "$BASE_URL/config/custom/configurations/TestGel100Ah")

echo "$RESPONSE" | jq '.'

echo -e "\n3️⃣ Verificando configuración creada..."
curl -s "$BASE_URL/config/custom/configurations" | jq '.'

echo -e "\n4️⃣ Obteniendo configuración específica..."
curl -s "$BASE_URL/config/custom/config/TestGel100Ah" | jq '.'

echo -e "\n5️⃣ Creando configuración Litio para comparar..."
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 200.0,
    "isLithium": true,
    "thresholdPercentage": 3.0,
    "maxAllowedCurrent": 20000.0,
    "bulkVoltage": 14.8,
    "absorptionVoltage": 14.8,
    "floatVoltage": 13.6,
    "useFuenteDC": true,
    "fuenteDC_Amps": 10.0,
    "factorDivider": 3
  }' \
  "$BASE_URL/config/custom/configurations/TestLitio200Ah" | jq '.'

echo -e "\n6️⃣ Verificando ambas configuraciones..."
curl -s "$BASE_URL/config/custom/configurations" | jq '.'

echo -e "\n7️⃣ Aplicando configuración Litio..."
curl -s -X POST "$BASE_URL/config/custom/configurations/TestLitio200Ah/apply" | jq '.'

echo -e "\n8️⃣ Verificando configuración aplicada..."
curl -s "$BASE_URL/config/custom/configurations/applied" | jq '.'

echo -e "\n9️⃣ Export final..."
curl -s "$BASE_URL/config/custom/configurations/export" | jq '.'

echo -e "\n🔟 Información final del sistema..."
curl -s "$BASE_URL/config/custom/configurations/info" | jq '.'

echo -e "\n✅ VALIDACIÓN COMPLETA FINALIZADA"
echo "================================================================"
