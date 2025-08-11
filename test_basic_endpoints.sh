#!/bin/bash

# =============================================================================
# TEST BÁSICO ENDPOINTS - Orange Pi R2S (RISC-V)
# =============================================================================

echo "🔋 TEST BÁSICO DE ENDPOINTS EN ORANGE PI R2S..."
echo "================================================================"

BASE_URL="http://localhost:8000"

echo "1️⃣ Estado inicial..."
curl -s "$BASE_URL/config/custom/configurations/info"
echo -e "\n"

echo "2️⃣ Listando configuraciones..."
curl -s "$BASE_URL/config/custom/configurations"
echo -e "\n"

echo "3️⃣ Creando configuración TestBasic..."
curl -s -X POST \
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
  "$BASE_URL/config/custom/config/TestBasic"
echo -e "\n"

echo "4️⃣ Verificando creación..."
curl -s "$BASE_URL/config/custom/configurations"
echo -e "\n"

echo "5️⃣ Obteniendo configuración específica..."
curl -s "$BASE_URL/config/custom/config/TestBasic"
echo -e "\n"

echo "6️⃣ Eliminando configuración..."
curl -s -X DELETE "$BASE_URL/config/custom/config/TestBasic"
echo -e "\n"

echo "7️⃣ Verificando eliminación..."
curl -s "$BASE_URL/config/custom/configurations"
echo -e "\n"

echo "✅ TEST BÁSICO COMPLETADO"
