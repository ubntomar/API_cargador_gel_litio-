#!/bin/bash
# =============================================================================
# Script de prueba para endpoints de Configuraciones Personalizadas
# ESP32 Solar Charger API - Comandos curl
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_BASE="http://localhost:8000"

echo -e "${BLUE}🚀 Probando endpoints de Configuraciones Personalizadas${NC}"
echo "=================================================================="

# Función helper para mostrar resultados
show_result() {
    local title="$1"
    local response="$2"
    
    echo -e "\n${YELLOW}📋 $title${NC}"
    echo "------------------------------------------------------"
    echo "$response" | jq . 2>/dev/null || echo "$response"
    echo ""
}

# 1. LISTAR TODAS LAS CONFIGURACIONES
echo -e "${GREEN}1. Listar configuraciones existentes${NC}"
RESPONSE=$(curl -s "$API_BASE/config/custom/configurations")
show_result "GET /config/custom/configurations" "$RESPONSE"

# 2. CREAR UNA CONFIGURACIÓN NUEVA
echo -e "${GREEN}2. Crear configuración nueva - Batería Litio 100Ah${NC}"
CONFIG_DATA='{
  "batteryCapacity": 100.0,
  "isLithium": true,
  "thresholdPercentage": 2.5,
  "maxAllowedCurrent": 12000.0,
  "bulkVoltage": 14.4,
  "absorptionVoltage": 14.4,
  "floatVoltage": 13.6,
  "useFuenteDC": false,
  "fuenteDC_Amps": 0.0,
  "factorDivider": 1
}'

RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$CONFIG_DATA" \
  "$API_BASE/config/custom/config/BateriaLitio100Ah")
show_result "POST /config/custom/config/BateriaLitio100Ah" "$RESPONSE"

# 3. CREAR SEGUNDA CONFIGURACIÓN - Batería GEL
echo -e "${GREEN}3. Crear configuración - Batería GEL 200Ah${NC}"
CONFIG_GEL='{
  "batteryCapacity": 200.0,
  "isLithium": false,
  "thresholdPercentage": 3.0,
  "maxAllowedCurrent": 15000.0,
  "bulkVoltage": 14.8,
  "absorptionVoltage": 14.8,
  "floatVoltage": 13.8,
  "useFuenteDC": false,
  "fuenteDC_Amps": 0.0,
  "factorDivider": 5
}'

RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$CONFIG_GEL" \
  "$API_BASE/config/custom/config/BateriaGEL200Ah")
show_result "POST /config/custom/config/BateriaGEL200Ah" "$RESPONSE"

# 4. OBTENER CONFIGURACIÓN ESPECÍFICA
echo -e "${GREEN}4. Obtener configuración específica${NC}"
RESPONSE=$(curl -s "$API_BASE/config/custom/config/BateriaLitio100Ah")
show_result "GET /config/custom/config/BateriaLitio100Ah" "$RESPONSE"

# 5. VALIDAR CONFIGURACIÓN
echo -e "${GREEN}5. Validar configuración${NC}"
VALIDATE_DATA='{
  "batteryCapacity": 150.0,
  "isLithium": true,
  "thresholdPercentage": 2.0,
  "maxAllowedCurrent": 8000.0,
  "bulkVoltage": 14.6,
  "absorptionVoltage": 14.6,
  "floatVoltage": 13.7,
  "useFuenteDC": false,
  "fuenteDC_Amps": 0.0,
  "factorDivider": 1
}'

RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$VALIDATE_DATA" \
  "$API_BASE/config/custom/configurations/validate")
show_result "POST /config/custom/configurations/validate" "$RESPONSE"

# 6. LISTAR NUEVAMENTE PARA VER LAS NUEVAS CONFIGURACIONES
echo -e "${GREEN}6. Listar configuraciones después de crear nuevas${NC}"
RESPONSE=$(curl -s "$API_BASE/config/custom/configurations")
show_result "GET /config/custom/configurations (actualizado)" "$RESPONSE"

# 7. APLICAR CONFIGURACIÓN AL ESP32
echo -e "${GREEN}7. Aplicar configuración al ESP32${NC}"
RESPONSE=$(curl -s -X POST "$API_BASE/config/custom/config/BateriaLitio100Ah/apply")
show_result "POST /config/custom/config/BateriaLitio100Ah/apply" "$RESPONSE"

# 8. EXPORTAR CONFIGURACIONES
echo -e "${GREEN}8. Exportar todas las configuraciones${NC}"
RESPONSE=$(curl -s "$API_BASE/config/custom/configurations/export")
show_result "GET /config/custom/configurations/export" "$RESPONSE"

# 9. INFORMACIÓN DEL SISTEMA
echo -e "${GREEN}9. Obtener información del sistema${NC}"
RESPONSE=$(curl -s "$API_BASE/config/custom/configurations/info")
show_result "GET /config/custom/configurations/info" "$RESPONSE"

# 10. ELIMINAR UNA CONFIGURACIÓN
echo -e "${GREEN}10. Eliminar configuración${NC}"
RESPONSE=$(curl -s -X DELETE "$API_BASE/config/custom/config/BateriaGEL200Ah")
show_result "DELETE /config/custom/config/BateriaGEL200Ah" "$RESPONSE"

# 11. VERIFICAR QUE SE ELIMINÓ
echo -e "${GREEN}11. Verificar configuraciones después de eliminar${NC}"
RESPONSE=$(curl -s "$API_BASE/config/custom/configurations")
show_result "GET /config/custom/configurations (después de eliminar)" "$RESPONSE"

# 12. CREAR CONFIGURACIONES MÚLTIPLES
echo -e "${GREEN}12. Crear múltiples configuraciones de una vez${NC}"
MULTIPLE_CONFIGS='{
  "data": {
    "ConfigPequena": {
      "batteryCapacity": 50.0,
      "isLithium": true,
      "thresholdPercentage": 2.0,
      "maxAllowedCurrent": 5000.0,
      "bulkVoltage": 14.2,
      "absorptionVoltage": 14.2,
      "floatVoltage": 13.4,
      "useFuenteDC": false,
      "fuenteDC_Amps": 0.0,
      "factorDivider": 1
    },
    "ConfigGrande": {
      "batteryCapacity": 400.0,
      "isLithium": false,
      "thresholdPercentage": 3.5,
      "maxAllowedCurrent": 20000.0,
      "bulkVoltage": 15.0,
      "absorptionVoltage": 15.0,
      "floatVoltage": 14.0,
      "useFuenteDC": true,
      "fuenteDC_Amps": 10.0,
      "factorDivider": 10
    }
  }
}'

RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "$MULTIPLE_CONFIGS" \
  "$API_BASE/config/custom/configurations")
show_result "POST /config/custom/configurations (múltiples)" "$RESPONSE"

echo -e "${BLUE}✅ Pruebas completadas!${NC}"
echo "=================================================================="
echo -e "${YELLOW}💡 Comandos curl individuales para uso manual:${NC}"
echo ""
echo "# Listar configuraciones:"
echo "curl -s $API_BASE/config/custom/configurations | jq ."
echo ""
echo "# Crear configuración:"
echo "curl -X POST -H 'Content-Type: application/json' \\"
echo "  -d '$(echo "$CONFIG_DATA" | tr -d '\n' | tr -s ' ')' \\"
echo "  $API_BASE/config/custom/config/MiConfiguracion"
echo ""
echo "# Aplicar configuración:"
echo "curl -X POST $API_BASE/config/custom/config/MiConfiguracion/apply"
echo ""
echo "# Eliminar configuración:"
echo "curl -X DELETE $API_BASE/config/custom/config/MiConfiguracion"
echo ""
echo "# Exportar backup:"
echo "curl -s $API_BASE/config/custom/configurations/export | jq ."
