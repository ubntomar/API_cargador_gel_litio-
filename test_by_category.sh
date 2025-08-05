#!/bin/bash
# =============================================================================
# ESP32 API - Pruebas Separadas por Categoría
# =============================================================================

API_BASE="${1:-http://192.168.8.100:8000}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORÍA 1: SOLO LECTURA (GET)
# ═══════════════════════════════════════════════════════════════════════════════
test_read_only() {
    echo -e "${BLUE}🔍 PRUEBAS DE SOLO LECTURA${NC}"
    echo "═══════════════════════════════════════"
    echo ""
    
    # Array de endpoints de lectura
    read_endpoints=(
        "/:Información básica de la API"
        "/health:Health check del sistema"
        "/data/:Todos los datos del ESP32"
        "/data/panelToBatteryCurrent:Corriente panel → batería"
        "/data/batteryToLoadCurrent:Corriente batería → carga"
        "/data/voltagePanel:Voltaje del panel"
        "/data/voltageBatterySensor2:Voltaje de la batería"
        "/data/temperature:Temperatura actual"
        "/data/chargeState:Estado de carga"
        "/data/currentPWM:Valor PWM actual"
        "/data/batteryCapacity:Capacidad de batería"
        "/data/isLithium:Tipo de batería"
        "/data/bulkVoltage:Voltaje BULK"
        "/data/absorptionVoltage:Voltaje ABSORCIÓN"
        "/data/floatVoltage:Voltaje FLOTACIÓN"
        "/data/maxAllowedCurrent:Corriente máxima"
        "/data/loadControlState:Estado control carga"
        "/data/temporaryLoadOff:Apagado temporal activo"
        "/actions/status:Estado de acciones"
        "/data/status/connection:Estado conexión ESP32"
        "/data/status/cache:Estadísticas del cache"
        "/config/:Parámetros configurables"
    )
    
    local passed=0
    local failed=0
    
    for endpoint_info in "${read_endpoints[@]}"; do
        IFS=':' read -r endpoint description <<< "$endpoint_info"
        
        echo -e "${CYAN}📊 $description${NC}"
        echo -n "   GET $endpoint ... "
        
        response=$(curl -s -w "%{http_code}" "$API_BASE$endpoint" 2>/dev/null)
        http_code="${response: -3}"
        
        if [[ "$http_code" == "200" ]]; then
            echo -e "${GREEN}✅ OK${NC}"
            ((passed++))
        else
            echo -e "${RED}❌ FAIL ($http_code)${NC}"
            ((failed++))
        fi
    done
    
    echo ""
    echo -e "${BLUE}📊 Resumen Solo Lectura:${NC}"
    echo "  ✅ Exitosos: $passed"
    echo "  ❌ Fallidos: $failed"
    echo "  📈 Tasa éxito: $((passed * 100 / (passed + failed)))%"
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}🎉 ¡Todos los endpoints de lectura funcionan!${NC}"
    else
        echo -e "${YELLOW}⚠️ Algunos endpoints de lectura tienen problemas${NC}"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORÍA 2: MODIFICABLES (PUT)
# ═══════════════════════════════════════════════════════════════════════════════
test_configurable() {
    echo -e "${BLUE}⚙️ PRUEBAS DE CONFIGURACIÓN${NC}"
    echo "═══════════════════════════════════════"
    echo ""
    
    # Obtener valores originales
    echo "🔄 Obteniendo configuración actual..."
    original_data=$(curl -s "$API_BASE/data/" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$original_data" ]; then
        echo -e "${RED}❌ Error obteniendo datos originales${NC}"
        return 1
    fi
    
    original_capacity=$(echo "$original_data" | jq -r '.batteryCapacity')
    original_lithium=$(echo "$original_data" | jq -r '.isLithium')
    original_bulk=$(echo "$original_data" | jq -r '.bulkVoltage')
    original_threshold=$(echo "$original_data" | jq -r '.thresholdPercentage')
    
    echo "📋 Valores originales:"
    echo "  - Capacidad: ${original_capacity}Ah"
    echo "  - Es Litio: $original_lithium"
    echo "  - Voltaje BULK: ${original_bulk}V"
    echo "  - Umbral: ${original_threshold}%"
    echo ""
    
    # Tests de configuración
    config_tests=(
        "batteryCapacity:50.0:Capacidad batería 50Ah"
        "batteryCapacity:100.0:Capacidad batería 100Ah"
        "isLithium:true:Batería tipo Litio"
        "isLithium:false:Batería tipo GEL"
        "bulkVoltage:14.4:Voltaje BULK 14.4V"
        "bulkVoltage:14.6:Voltaje BULK 14.6V"
        "absorptionVoltage:14.4:Voltaje ABSORCIÓN 14.4V"
        "floatVoltage:13.6:Voltaje FLOTACIÓN 13.6V"
        "thresholdPercentage:2.5:Umbral corriente 2.5%"
        "maxAllowedCurrent:6000.0:Corriente máxima 6000mA"
        "useFuenteDC:true:Activar fuente DC"
        "useFuenteDC:false:Desactivar fuente DC"
        "fuenteDC_Amps:10.0:Amperaje fuente DC 10A"
        "factorDivider:5:Factor divisor 5"
    )
    
    local passed=0
    local failed=0
    
    for test_info in "${config_tests[@]}"; do
        IFS=':' read -r param value description <<< "$test_info"
        
        echo -e "${CYAN}⚙️ $description${NC}"
        echo -n "   PUT /config/$param = $value ... "
        
        response=$(curl -s -w "%{http_code}" \
            -X PUT "$API_BASE/config/$param" \
            -H 'Content-Type: application/json' \
            -d "{\"value\": $value}" 2>/dev/null)
        
        http_code="${response: -3}"
        
        if [[ "$http_code" == "200" ]]; then
            echo -e "${GREEN}✅ OK${NC}"
            ((passed++))
        else
            echo -e "${RED}❌ FAIL ($http_code)${NC}"
            ((failed++))
        fi
        
        sleep 0.2  # Pequeña pausa entre requests
    done
    
    echo ""
    echo -e "${BLUE}🔄 Restaurando valores originales...${NC}"
    
    # Restaurar valores originales
    restore_configs=(
        "batteryCapacity:$original_capacity"
        "isLithium:$original_lithium"
        "bulkVoltage:$original_bulk"
        "thresholdPercentage:$original_threshold"
    )
    
    for restore_info in "${restore_configs[@]}"; do
        IFS=':' read -r param value <<< "$restore_info"
        
        if [ "$value" != "null" ] && [ -n "$value" ]; then
            echo -n "   Restaurando $param = $value ... "
            
            response=$(curl -s -w "%{http_code}" \
                -X PUT "$API_BASE/config/$param" \
                -H 'Content-Type: application/json' \
                -d "{\"value\": $value}" 2>/dev/null)
            
            http_code="${response: -3}"
            
            if [[ "$http_code" == "200" ]]; then
                echo -e "${GREEN}✅ OK${NC}"
            else
                echo -e "${RED}❌ FAIL${NC}"
            fi
        fi
    done
    
    echo ""
    echo -e "${BLUE}📊 Resumen Configuración:${NC}"
    echo "  ✅ Exitosos: $passed"
    echo "  ❌ Fallidos: $failed"
    echo "  📈 Tasa éxito: $((passed * 100 / (passed + failed)))%"
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}🎉 ¡Todas las configuraciones funcionan!${NC}"
    else
        echo -e "${YELLOW}⚠️ Algunas configuraciones tienen problemas${NC}"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORÍA 3: ACCIONES (POST)
# ═══════════════════════════════════════════════════════════════════════════════
test_actions() {
    echo -e "${BLUE}🎯 PRUEBAS DE ACCIONES${NC}"
    echo "═══════════════════════════════════════"
    echo ""
    
    # Verificar estado inicial
    echo -e "${CYAN}📊 Verificando estado inicial...${NC}"
    initial_status=$(curl -s "$API_BASE/actions/status" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$initial_status" ]; then
        echo -e "${RED}❌ Error obteniendo estado inicial${NC}"
        return 1
    fi
    
    echo "Estado inicial:"
    echo "$initial_status" | jq '.' 2>/dev/null || echo "$initial_status"
    echo ""
    
    local passed=0
    local failed=0
    
    # Test 1: Apagar por 10 segundos
    echo -e "${CYAN}🔌 Test 1: Apagar carga por 10 segundos${NC}"
    echo -n "   POST /actions/toggle_load ... "
    
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/actions/toggle_load" \
        -H 'Content-Type: application/json' \
        -d '{"hours": 0, "minutes": 0, "seconds": 10}' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}✅ OK${NC}"
        ((passed++))
        
        # Verificar que se aplicó
        echo -n "   Verificando estado después del comando ... "
        sleep 1
        status_after=$(curl -s "$API_BASE/actions/status" 2>/dev/null)
        temp_off=$(echo "$status_after" | jq -r '.temporary_load_off' 2>/dev/null)
        
        if [ "$temp_off" = "true" ]; then
            echo -e "${GREEN}✅ APLICADO${NC}"
            remaining=$(echo "$status_after" | jq -r '.load_off_remaining_seconds' 2>/dev/null)
            echo "     ⏰ Tiempo restante: ${remaining}s"
        else
            echo -e "${YELLOW}⚠️ NO APLICADO (puede ser problema de comunicación real)${NC}"
        fi
        
    else
        echo -e "${RED}❌ FAIL ($http_code)${NC}"
        ((failed++))
    fi
    
    echo ""
    
    # Test 2: Cancelar apagado
    echo -e "${CYAN}❌ Test 2: Cancelar apagado temporal${NC}"
    echo -n "   POST /actions/cancel_temp_off ... "
    
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/actions/cancel_temp_off" \
        -H 'Content-Type: application/json' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "${GREEN}✅ OK${NC}"
        ((passed++))
        
        # Verificar que se canceló
        echo -n "   Verificando cancelación ... "
        sleep 1
        status_after=$(curl -s "$API_BASE/actions/status" 2>/dev/null)
        temp_off=$(echo "$status_after" | jq -r '.temporary_load_off' 2>/dev/null)
        
        if [ "$temp_off" = "false" ]; then
            echo -e "${GREEN}✅ CANCELADO${NC}"
        else
            echo -e "${YELLOW}⚠️ NO CANCELADO${NC}"
        fi
        
    else
        echo -e "${RED}❌ FAIL ($http_code)${NC}"
        ((failed++))
    fi
    
    echo ""
    
    # Test 3: Diferentes duraciones
    durations=(
        "0:0:30:30 segundos"
        "0:2:0:2 minutos"
        "1:0:0:1 hora"
    )
    
    for duration_info in "${durations[@]}"; do
        IFS=':' read -r hours minutes seconds description <<< "$duration_info"
        
        echo -e "${CYAN}⏰ Test: Apagar por $description${NC}"
        echo -n "   POST /actions/toggle_load ... "
        
        response=$(curl -s -w "%{http_code}" \
            -X POST "$API_BASE/actions/toggle_load" \
            -H 'Content-Type: application/json' \
            -d "{\"hours\": $hours, \"minutes\": $minutes, \"seconds\": $seconds}" 2>/dev/null)
        
        http_code="${response: -3}"
        
        if [[ "$http_code" == "200" ]]; then
            echo -e "${GREEN}✅ OK${NC}"
            ((passed++))
            
            # Cancelar inmediatamente para siguiente test
            curl -s -X POST "$API_BASE/actions/cancel_temp_off" \
                -H 'Content-Type: application/json' >/dev/null 2>&1
        else
            echo -e "${RED}❌ FAIL ($http_code)${NC}"
            ((failed++))
        fi
    done
    
    echo ""
    echo -e "${BLUE}📊 Resumen Acciones:${NC}"
    echo "  ✅ Exitosos: $passed"
    echo "  ❌ Fallidos: $failed"
    echo "  📈 Tasa éxito: $((passed * 100 / (passed + failed)))%"
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}🎉 ¡Todas las acciones funcionan!${NC}"
    else
        echo -e "${YELLOW}⚠️ Algunas acciones tienen problemas${NC}"
    fi
    
    # Estado final
    echo ""
    echo -e "${CYAN}📊 Estado final:${NC}"
    curl -s "$API_BASE/actions/status" | jq '.' 2>/dev/null
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
show_help() {
    echo -e "${BLUE}ESP32 API - Pruebas por Categoría${NC}"
    echo "Uso: $0 [API_URL] [CATEGORÍA]"
    echo ""
    echo "Categorías:"
    echo "  read      - Solo endpoints de lectura (GET)"
    echo "  config    - Solo endpoints de configuración (PUT)"
    echo "  actions   - Solo endpoints de acciones (POST)"
    echo "  all       - Todas las categorías"
    echo ""
    echo "Ejemplos:"
    echo "  $0 read"
    echo "  $0 http://192.168.1.100:8000 config"
    echo "  $0 actions"
}

main() {
    case "${2:-all}" in
        "read")
            test_read_only
            ;;
        "config")
            test_configurable
            ;;
        "actions")
            test_actions
            ;;
        "all")
            test_read_only
            echo ""
            echo ""
            test_configurable
            echo ""
            echo ""
            test_actions
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}Categoría desconocida: ${2}${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Verificar conectividad inicial
echo -e "${BLUE}🔍 Verificando conectividad con $API_BASE${NC}"
if curl -s "$API_BASE/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ API accesible${NC}"
    echo ""
    main "$@"
else
    echo -e "${RED}❌ No se puede conectar a la API${NC}"
    echo "Verifica que:"
    echo "  1. La API esté ejecutándose"
    echo "  2. La URL sea correcta: $API_BASE"
    echo "  3. No haya problemas de red"
    exit 1
fi