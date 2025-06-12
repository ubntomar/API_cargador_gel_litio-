#!/bin/bash
# =============================================================================
# ESP32 API - Pruebas Completas de Funcionalidad Schedule
# =============================================================================

API_BASE="${1:-http://192.168.8.100:8000}"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🕐 ESP32 API - PRUEBAS COMPLETAS DE SCHEDULE${NC}"
echo "API: $API_BASE"
echo "Fecha: $(date)"
echo "═══════════════════════════════════════════════════════════"

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 1: VERIFICAR DISPONIBILIDAD DEL SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════
test_schedule_availability() {
    echo -e "\n${PURPLE}📋 1. VERIFICACIÓN DE DISPONIBILIDAD${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local passed=0
    local total=3
    
    # Test 1: Health check incluye schedule
    echo -e "\n${CYAN}🔍 Health check con schedule...${NC}"
    response=$(curl -s "$API_BASE/health" 2>/dev/null)
    if echo "$response" | grep -q "schedule_manager"; then
        echo -e "   ${GREEN}✅ Schedule manager presente en health check${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Schedule manager no encontrado${NC}"
    fi
    
    # Test 2: Endpoint /schedule/ disponible
    echo -e "\n${CYAN}🔍 Endpoint /schedule/ disponible...${NC}"
    response=$(curl -s -w "%{http_code}" "$API_BASE/schedule/" 2>/dev/null)
    http_code="${response: -3}"
    if [[ "$http_code" == "200" ]]; then
        echo -e "   ${GREEN}✅ Endpoint /schedule/ respondiendo${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Endpoint /schedule/ no disponible ($http_code)${NC}"
    fi
    
    # Test 3: Schedule info disponible
    echo -e "\n${CYAN}🔍 Información de schedule...${NC}"
    response=$(curl -s "$API_BASE/schedule/info" 2>/dev/null)
    if echo "$response" | grep -q "max_duration_hours"; then
        echo -e "   ${GREEN}✅ Información de schedule disponible${NC}"
        max_hours=$(echo "$response" | jq -r '.max_duration_hours' 2>/dev/null)
        echo -e "   ${BLUE}ℹ️ Duración máxima: ${max_hours} horas${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Información de schedule no disponible${NC}"
    fi
    
    echo -e "\n${BLUE}📊 Resultado Disponibilidad: ${passed}/${total}${NC}"
    return $((total - passed))
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 2: CONFIGURACIÓN DEL SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════
test_schedule_configuration() {
    echo -e "\n${PURPLE}⚙️ 2. PRUEBAS DE CONFIGURACIÓN${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local passed=0
    local total=8
    
    # Obtener configuración inicial
    echo -e "\n${CYAN}📋 Obteniendo configuración inicial...${NC}"
    original_config=$(curl -s "$API_BASE/schedule/" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$original_config" ]; then
        echo -e "   ${GREEN}✅ Configuración inicial obtenida${NC}"
        echo "$original_config" | jq '.' 2>/dev/null | head -n 5
    else
        echo -e "   ${RED}❌ Error obteniendo configuración inicial${NC}"
        return 1
    fi
    
    # Test configuraciones válidas
    echo -e "\n${CYAN}⚙️ Pruebas de configuraciones válidas...${NC}"
    
    configs=(
        "true:02:00:7200:2 horas desde 2 AM"
        "true:13:30:10800:3 horas desde 1:30 PM"
        "false:00:00:21600:Deshabilitado"
        "true:23:00:3600:1 hora desde 11 PM"
        "true:12:00:28800:8 horas (máximo)"
    )
    
    for config_info in "${configs[@]}"; do
        IFS=':' read -r enabled start_time duration description <<< "$config_info"
        
        echo -e "\n   ${BLUE}🔧 $description${NC}"
        
        response=$(curl -s -w "%{http_code}" \
            -X PUT "$API_BASE/schedule/config" \
            -H 'Content-Type: application/json' \
            -d "{
                \"enabled\": $enabled,
                \"start_time\": \"$start_time\",
                \"duration_seconds\": $duration
            }" 2>/dev/null)
        
        http_code="${response: -3}"
        
        if [[ "$http_code" == "200" ]]; then
            echo -e "      ${GREEN}✅ Configurado correctamente${NC}"
            ((passed++))
        else
            echo -e "      ${RED}❌ Error ($http_code)${NC}"
        fi
        
        sleep 0.3
    done
    
    # Test configuraciones inválidas
    echo -e "\n${CYAN}🚫 Pruebas de configuraciones inválidas...${NC}"
    
    invalid_configs=(
        "true:25:00:3600:Hora inválida (25:00)"
        "true:12:60:3600:Minutos inválidos (:60)"
        "true:12:00:28801:Duración excesiva (>8h)"
        "true:12:00:0:Duración cero"
    )
    
    for config_info in "${invalid_configs[@]}"; do
        IFS=':' read -r enabled start_time duration description <<< "$config_info"
        
        echo -e "\n   ${BLUE}🚫 $description${NC}"
        
        response=$(curl -s -w "%{http_code}" \
            -X PUT "$API_BASE/schedule/config" \
            -H 'Content-Type: application/json' \
            -d "{
                \"enabled\": $enabled,
                \"start_time\": \"$start_time\",
                \"duration_seconds\": $duration
            }" 2>/dev/null)
        
        http_code="${response: -3}"
        
        if [[ "$http_code" == "400" || "$http_code" == "422" ]]; then
            echo -e "      ${GREEN}✅ Rechazado correctamente ($http_code)${NC}"
            ((passed++))
        else
            echo -e "      ${RED}❌ Debería haberse rechazado ($http_code)${NC}"
        fi
        
        sleep 0.3
    done
    
    echo -e "\n${BLUE}📊 Resultado Configuración: ${passed}/${total}${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 3: TOGGLE MANUAL Y OVERRIDE
# ═══════════════════════════════════════════════════════════════════════════════
test_manual_override() {
    echo -e "\n${PURPLE}🔧 3. PRUEBAS DE OVERRIDE MANUAL${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local passed=0
    local total=5
    
    # Configurar schedule activo para las pruebas
    echo -e "\n${CYAN}📅 Configurando schedule de prueba...${NC}"
    curl -s -X PUT "$API_BASE/schedule/config" \
        -H 'Content-Type: application/json' \
        -d '{
            "enabled": true,
            "start_time": "00:00",
            "duration_seconds": 21600
        }' > /dev/null 2>&1
    
    # Test 1: Toggle manual básico
    echo -e "\n${CYAN}🔧 Toggle manual básico (30 segundos)...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/actions/toggle_load" \
        -H 'Content-Type: application/json' \
        -d '{"hours": 0, "minutes": 0, "seconds": 30}' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "   ${GREEN}✅ Toggle manual ejecutado${NC}"
        ((passed++))
        
        # Verificar que se estableció el override
        sleep 1
        status=$(curl -s "$API_BASE/actions/status" 2>/dev/null)
        override_active=$(echo "$status" | jq -r '.schedule.manual_override_active' 2>/dev/null)
        
        if [ "$override_active" = "true" ]; then
            echo -e "   ${GREEN}✅ Override manual activado correctamente${NC}"
            ((passed++))
        else
            echo -e "   ${RED}❌ Override manual no se activó${NC}"
        fi
    else
        echo -e "   ${RED}❌ Error en toggle manual ($http_code)${NC}"
    fi
    
    # Test 2: Clear override
    echo -e "\n${CYAN}🔄 Limpiar override manual...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/schedule/clear_override" \
        -H 'Content-Type: application/json' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "   ${GREEN}✅ Override limpiado${NC}"
        ((passed++))
        
        # Verificar que se limpió
        sleep 1
        status=$(curl -s "$API_BASE/actions/status" 2>/dev/null)
        override_active=$(echo "$status" | jq -r '.schedule.manual_override_active' 2>/dev/null)
        
        if [ "$override_active" = "false" ]; then
            echo -e "   ${GREEN}✅ Override desactivado correctamente${NC}"
            ((passed++))
        else
            echo -e "   ${RED}❌ Override no se desactivó${NC}"
        fi
    else
        echo -e "   ${RED}❌ Error limpiando override ($http_code)${NC}"
    fi
    
    # Test 3: Toggle con duración máxima
    echo -e "\n${CYAN}⏰ Toggle con duración máxima (8 horas)...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/actions/toggle_load" \
        -H 'Content-Type: application/json' \
        -d '{"hours": 8, "minutes": 0, "seconds": 0}' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "   ${GREEN}✅ Toggle 8 horas aceptado${NC}"
        ((passed++))
        
        # Cancelar inmediatamente
        curl -s -X POST "$API_BASE/actions/cancel_temp_off" > /dev/null 2>&1
        curl -s -X POST "$API_BASE/schedule/clear_override" > /dev/null 2>&1
    else
        echo -e "   ${RED}❌ Error con toggle 8 horas ($http_code)${NC}"
    fi
    
    echo -e "\n${BLUE}📊 Resultado Override Manual: ${passed}/${total}${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 4: HABILITAR/DESHABILITAR SCHEDULE
# ═══════════════════════════════════════════════════════════════════════════════
test_enable_disable() {
    echo -e "\n${PURPLE}🔛 4. PRUEBAS HABILITAR/DESHABILITAR${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local passed=0
    local total=4
    
    # Test 1: Deshabilitar schedule
    echo -e "\n${CYAN}🔛 Deshabilitando schedule...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/schedule/disable" \
        -H 'Content-Type: application/json' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "   ${GREEN}✅ Schedule deshabilitado${NC}"
        ((passed++))
        
        # Verificar estado
        sleep 1
        status=$(curl -s "$API_BASE/schedule/" 2>/dev/null)
        enabled=$(echo "$status" | jq -r '.enabled' 2>/dev/null)
        
        if [ "$enabled" = "false" ]; then
            echo -e "   ${GREEN}✅ Estado 'enabled' = false${NC}"
            ((passed++))
        else
            echo -e "   ${RED}❌ Estado 'enabled' no cambió${NC}"
        fi
    else
        echo -e "   ${RED}❌ Error deshabilitando ($http_code)${NC}"
    fi
    
    # Test 2: Habilitar schedule
    echo -e "\n${CYAN}🔛 Habilitando schedule...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/schedule/enable" \
        -H 'Content-Type: application/json' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "200" ]]; then
        echo -e "   ${GREEN}✅ Schedule habilitado${NC}"
        ((passed++))
        
        # Verificar estado
        sleep 1
        status=$(curl -s "$API_BASE/schedule/" 2>/dev/null)
        enabled=$(echo "$status" | jq -r '.enabled' 2>/dev/null)
        
        if [ "$enabled" = "true" ]; then
            echo -e "   ${GREEN}✅ Estado 'enabled' = true${NC}"
            ((passed++))
        else
            echo -e "   ${RED}❌ Estado 'enabled' no cambió${NC}"
        fi
    else
        echo -e "   ${RED}❌ Error habilitando ($http_code)${NC}"
    fi
    
    echo -e "\n${BLUE}📊 Resultado Enable/Disable: ${passed}/${total}${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 5: INTEGRACIÓN CON ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════
test_actions_integration() {
    echo -e "\n${PURPLE}🎭 5. INTEGRACIÓN CON ACTIONS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local passed=0
    local total=3
    
    # Test 1: Actions/status incluye schedule
    echo -e "\n${CYAN}📊 Estado de actions incluye schedule...${NC}"
    response=$(curl -s "$API_BASE/actions/status" 2>/dev/null)
    
    if echo "$response" | grep -q "schedule"; then
        echo -e "   ${GREEN}✅ Schedule presente en actions/status${NC}"
        ((passed++))
        
        # Mostrar información de schedule
        schedule_info=$(echo "$response" | jq '.schedule' 2>/dev/null)
        if [ "$schedule_info" != "null" ]; then
            echo -e "   ${BLUE}ℹ️ Info schedule:${NC}"
            echo "$schedule_info" | jq -r '. | "      Enabled: \(.enabled), Override: \(.manual_override_active)"' 2>/dev/null
        fi
    else
        echo -e "   ${RED}❌ Schedule no presente en actions/status${NC}"
    fi
    
    # Test 2: Actions/info incluye información de schedule
    echo -e "\n${CYAN}ℹ️ Actions/info incluye schedule...${NC}"
    response=$(curl -s "$API_BASE/actions/info" 2>/dev/null)
    
    if echo "$response" | grep -q "schedule_integration"; then
        echo -e "   ${GREEN}✅ Información de schedule en actions/info${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Sin información de schedule en actions/info${NC}"
    fi
    
    # Test 3: System/info incluye schedule
    echo -e "\n${CYAN}🖥️ System/info incluye schedule...${NC}"
    response=$(curl -s "$API_BASE/system/info" 2>/dev/null)
    
    if echo "$response" | grep -q "schedule"; then
        echo -e "   ${GREEN}✅ Schedule presente en system/info${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Schedule no presente en system/info${NC}"
    fi
    
    echo -e "\n${BLUE}📊 Resultado Integración: ${passed}/${total}${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN 6: VALIDACIONES Y LÍMITES
# ═══════════════════════════════════════════════════════════════════════════════
test_validation_limits() {
    echo -e "\n${PURPLE}🛡️ 6. VALIDACIONES Y LÍMITES${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    local passed=0
    local total=4
    
    # Test 1: Límite 8 horas en configuración
    echo -e "\n${CYAN}⏰ Límite 8 horas en configuración...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X PUT "$API_BASE/schedule/config" \
        -H 'Content-Type: application/json' \
        -d '{
            "enabled": true,
            "start_time": "12:00",
            "duration_seconds": 28801
        }' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "400" || "$http_code" == "422" ]]; then
        echo -e "   ${GREEN}✅ Límite 8 horas respetado en config${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Límite 8 horas no respetado ($http_code)${NC}"
    fi
    
    # Test 2: Límite 8 horas en toggle
    echo -e "\n${CYAN}⏰ Límite 8 horas en toggle...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X POST "$API_BASE/actions/toggle_load" \
        -H 'Content-Type: application/json' \
        -d '{"hours": 8, "minutes": 0, "seconds": 1}' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "400" ]]; then
        echo -e "   ${GREEN}✅ Límite 8 horas respetado en toggle${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Límite 8 horas no respetado ($http_code)${NC}"
    fi
    
    # Test 3: Formato de hora inválido
    echo -e "\n${CYAN}🕐 Formato de hora inválido...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X PUT "$API_BASE/schedule/config" \
        -H 'Content-Type: application/json' \
        -d '{
            "enabled": true,
            "start_time": "25:99",
            "duration_seconds": 3600
        }' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "400" || "$http_code" == "422" ]]; then
        echo -e "   ${GREEN}✅ Formato de hora validado${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Formato de hora no validado ($http_code)${NC}"
    fi
    
    # Test 4: Duración mínima
    echo -e "\n${CYAN}⏱️ Duración mínima (0 segundos)...${NC}"
    response=$(curl -s -w "%{http_code}" \
        -X PUT "$API_BASE/schedule/config" \
        -H 'Content-Type: application/json' \
        -d '{
            "enabled": true,
            "start_time": "12:00",
            "duration_seconds": 0
        }' 2>/dev/null)
    
    http_code="${response: -3}"
    
    if [[ "$http_code" == "400" || "$http_code" == "422" ]]; then
        echo -e "   ${GREEN}✅ Duración mínima validada${NC}"
        ((passed++))
    else
        echo -e "   ${RED}❌ Duración mínima no validada ($http_code)${NC}"
    fi
    
    echo -e "\n${BLUE}📊 Resultado Validaciones: ${passed}/${total}${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
run_all_tests() {
    echo -e "\n${BLUE}🚀 INICIANDO SUITE COMPLETA DE PRUEBAS${NC}"
    
    local total_errors=0
    
    # Verificar conectividad inicial
    echo -e "\n${CYAN}🔍 Verificando conectividad...${NC}"
    if curl -s "$API_BASE/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ API accesible${NC}"
    else
        echo -e "${RED}❌ No se puede conectar a la API${NC}"
        echo "Verifica que la API esté ejecutándose en $API_BASE"
        exit 1
    fi
    
    # Ejecutar todas las pruebas
    test_schedule_availability
    ((total_errors += $?))
    
    test_schedule_configuration
    ((total_errors += $?))
    
    test_manual_override
    ((total_errors += $?))
    
    test_enable_disable
    ((total_errors += $?))
    
    test_actions_integration
    ((total_errors += $?))
    
    test_validation_limits
    ((total_errors += $?))
    
    # Resumen final
    echo -e "\n${PURPLE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}🎯 RESUMEN FINAL DE PRUEBAS${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
    
    if [ $total_errors -eq 0 ]; then
        echo -e "${GREEN}🎉 ¡TODAS LAS PRUEBAS PASARON!${NC}"
        echo -e "${GREEN}✅ La funcionalidad Schedule está completamente operativa${NC}"
    else
        echo -e "${RED}⚠️ Se encontraron $total_errors errores en las pruebas${NC}"
        echo -e "${YELLOW}🔧 Revisa los logs para más detalles${NC}"
    fi
    
    echo -e "\n${BLUE}📊 Estado actual del schedule:${NC}"
    curl -s "$API_BASE/schedule/" | jq '.' 2>/dev/null || echo "Error obteniendo estado"
    
    echo -e "\n${BLUE}🕐 Hora actual del sistema: $(date)${NC}"
    echo -e "${BLUE}🌐 API testeada: $API_BASE${NC}"
    
    return $total_errors
}

# Ejecutar pruebas
run_all_tests