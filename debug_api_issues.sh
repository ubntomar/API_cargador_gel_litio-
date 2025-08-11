#!/bin/bash
# =============================================================================
# ESP32 API - Script de Diagnóstico para Problemas Detectados
# =============================================================================

API_HOST="${1:-192.168.8.100}"
API_PORT="${2:-8000}"
API_BASE="http://${API_HOST}:${API_PORT}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}ESP32 API - Diagnóstico de Problemas${NC}"
echo "Servidor: $API_BASE"
echo ""

# 1. Verificar el JSON completo de datos
echo -e "${YELLOW}=== 1. ANÁLISIS DEL JSON COMPLETO ===${NC}"
echo "Obteniendo datos completos..."
all_data=$(curl -s "$API_BASE/data/" 2>/dev/null)
echo "Longitud del JSON: ${#all_data} caracteres"

# Guardar JSON para análisis
echo "$all_data" > debug_full_data.json
echo "JSON guardado en: debug_full_data.json"

# Mostrar estructura del JSON (primeros 500 caracteres)
echo ""
echo "Estructura del JSON (preview):"
echo "$all_data" | head -c 500
echo "..."
echo ""

# 2. Verificar campos específicos problemáticos
echo -e "${YELLOW}=== 2. VERIFICACIÓN DE CAMPOS PROBLEMÁTICOS ===${NC}"

problem_fields=("isLithium" "panelSensorAvailable" "temporaryLoadOff" "ledSolarState")

for field in "${problem_fields[@]}"; do
    echo -n "Campo '$field': "
    if echo "$all_data" | grep -q "\"$field\""; then
        value=$(echo "$all_data" | grep -o "\"$field\":[^,}]*" | sed 's/.*://')
        echo -e "${GREEN}PRESENTE${NC} - Valor: $value"
    else
        echo -e "${RED}AUSENTE${NC}"
    fi
done

echo ""

# 3. Probar configuraciones problemáticas individualmente
echo -e "${YELLOW}=== 3. PRUEBA DE CONFIGURACIONES PROBLEMÁTICAS ===${NC}"

# Probar batteryCapacity con diferentes valores
echo "Probando batteryCapacity..."
for value in "50.0" "100.0" "7.0"; do
    echo -n "  batteryCapacity = $value: "
    response=$(curl -s -w "%{http_code}" -o /tmp/debug_response.tmp \
        -X PUT \
        -H "Content-Type: application/json" \
        -d "{\"value\": $value}" \
        "$API_BASE/config/batteryCapacity" 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}ERROR ($http_code)${NC}"
        echo "    Respuesta: $(cat /tmp/debug_response.tmp)"
    fi
done

echo ""

# Probar isLithium con diferentes formatos
echo "Probando isLithium..."
for value in "true" "false" "\"true\"" "\"false\""; do
    echo -n "  isLithium = $value: "
    response=$(curl -s -w "%{http_code}" -o /tmp/debug_response.tmp \
        -X PUT \
        -H "Content-Type: application/json" \
        -d "{\"value\": $value}" \
        "$API_BASE/config/isLithium" 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${RED}ERROR ($http_code)${NC}"
        echo "    Respuesta: $(cat /tmp/debug_response.tmp)"
    fi
done

echo ""

# 4. Verificar endpoint de acciones
echo -e "${YELLOW}=== 4. DIAGNÓSTICO DE ACCIONES ===${NC}"

echo -n "GET /actions/status: "
response=$(curl -s -w "%{http_code}" -o /tmp/debug_actions.tmp "$API_BASE/actions/status" 2>/dev/null)
http_code="${response: -3}"

if [[ "$http_code" == "200" ]]; then
    echo -e "${GREEN}OK${NC}"
    echo "Respuesta: $(cat /tmp/debug_actions.tmp)"
else
    echo -e "${RED}ERROR ($http_code)${NC}"
    echo "Respuesta de error: $(cat /tmp/debug_actions.tmp)"
fi

echo ""

# 5. Verificar logs de la API si está disponible
echo -e "${YELLOW}=== 5. INFORMACIÓN ADICIONAL ===${NC}"

echo "Health check:"
curl -s "$API_BASE/health" | head -c 200
echo ""

echo ""
echo "Cache status:"
curl -s "$API_BASE/data/status/cache" 2>/dev/null | head -c 200
echo ""

echo ""
echo "Connection status:"
curl -s "$API_BASE/data/status/connection" 2>/dev/null | head -c 200
echo ""

# 6. Prueba de lectura individual de campos problemáticos
echo ""
echo -e "${YELLOW}=== 6. LECTURA INDIVIDUAL DE CAMPOS PROBLEMÁTICOS ===${NC}"

for field in "${problem_fields[@]}"; do
    echo -n "GET /data/$field: "
    response=$(curl -s -w "%{http_code}" -o /tmp/debug_field.tmp "$API_BASE/data/$field" 2>/dev/null)
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}OK${NC}"
        echo "    $(cat /tmp/debug_field.tmp)"
    else
        echo -e "${RED}ERROR ($http_code)${NC}"
        echo "    $(cat /tmp/debug_field.tmp)"
    fi
done

echo ""
echo -e "${BLUE}=== DIAGNÓSTICO COMPLETO ===${NC}"

# 7. NUEVO: Diagnóstico específico de Docker
echo ""
echo -e "${YELLOW}=== 7. DIAGNÓSTICO DOCKER ===${NC}"

echo "Verificando si el código del container está actualizado..."

# Verificar si Docker está corriendo
if docker ps | grep -q "esp32-solar-api"; then
    container_name=$(docker ps --format "table {{.Names}}" | grep esp32)
    if [ -n "$container_name" ]; then
        echo "Container encontrado: $container_name"
        
        # Comparar líneas de código entre container y host
        if [ -f "api/config.py" ]; then
            host_lines=$(wc -l < api/config.py)
            container_lines=$(docker exec "$container_name" wc -l < /app/api/config.py 2>/dev/null || echo "0")
            
            echo "Líneas en host: $host_lines"
            echo "Líneas en container: $container_lines"
            
            if [ "$host_lines" -eq "$container_lines" ]; then
                echo -e "${GREEN}✅ Código sincronizado${NC}"
            else
                echo -e "${RED}❌ CÓDIGO DESINCRONIZADO - Este puede ser el problema${NC}"
                echo -e "${YELLOW}Solución: docker-compose down && docker-compose up -d${NC}"
            fi
        fi
        
        # Verificar volúmenes
        echo ""
        echo "Verificando configuración de volúmenes..."
        if docker inspect "$container_name" | grep -q "/app/api"; then
            echo -e "${GREEN}✅ Volúmenes de desarrollo configurados${NC}"
        else
            echo -e "${RED}❌ Volúmenes de desarrollo NO configurados${NC}"
            echo -e "${YELLOW}Necesitas configurar volumes en docker-compose.yml${NC}"
        fi
    fi
else
    echo -e "${RED}❌ Container de ESP32 API no está corriendo${NC}"
fi

echo ""
echo "Archivos generados:"
echo "  • debug_full_data.json - JSON completo de la API"
echo "  • /tmp/debug_*.tmp - Respuestas de pruebas"
echo ""
echo "💡 Revisa debug_full_data.json para ver la estructura exacta del JSON"

# Limpiar archivos temporales
rm -f /tmp/debug_*.tmp