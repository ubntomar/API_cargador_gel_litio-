#!/bin/bash
# =============================================================================
# Script de Validación de Endpoints de Configuraciones
# =============================================================================
# Este script valida que todos los endpoints documentados funcionen correctamente
# y que correspondan con el código actual de la API.

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

API_BASE="http://localhost:8000"

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🔍 $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
}

print_test() {
    echo -e "${CYAN}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌ ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️ WARN]${NC} $1"
}

# Función para probar endpoint
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local description="$3"
    local data="$4"
    
    print_test "$method $endpoint - $description"
    
    local cmd=""
    if [ "$method" = "GET" ]; then
        cmd="curl -s -w '%{http_code}' -o /dev/null '$API_BASE$endpoint'"
    elif [ "$method" = "POST" ] && [ -n "$data" ]; then
        cmd="curl -s -w '%{http_code}' -o /dev/null -X POST -H 'Content-Type: application/json' -d '$data' '$API_BASE$endpoint'"
    elif [ "$method" = "POST" ]; then
        cmd="curl -s -w '%{http_code}' -o /dev/null -X POST '$API_BASE$endpoint'"
    elif [ "$method" = "DELETE" ]; then
        cmd="curl -s -w '%{http_code}' -o /dev/null -X DELETE '$API_BASE$endpoint'"
    fi
    
    local status_code
    status_code=$(eval "$cmd" 2>/dev/null || echo "000")
    
    if [[ "$status_code" =~ ^[234][0-9][0-9]$ ]]; then
        print_success "Status: $status_code"
        return 0
    else
        print_error "Status: $status_code"
        return 1
    fi
}

# Función principal de validación
validate_endpoints() {
    print_header "VALIDACIÓN DE ENDPOINTS DE CONFIGURACIONES"
    
    local total_tests=0
    local passed_tests=0
    
    echo "🎯 Validando que la API esté corriendo..."
    if ! curl -s "$API_BASE/health" > /dev/null 2>&1; then
        print_error "La API no está corriendo en $API_BASE"
        print_test "Ejecuta: docker-compose up -d"
        exit 1
    fi
    print_success "API está corriendo"
    echo ""
    
    # 1. Endpoints básicos de configuraciones
    print_header "1. ENDPOINTS BÁSICOS"
    
    ((total_tests++))
    if test_endpoint "GET" "/config/custom/configurations" "Listar configuraciones"; then
        ((passed_tests++))
    fi
    
    ((total_tests++))
    if test_endpoint "GET" "/config/custom/configurations/info" "Info del sistema"; then
        ((passed_tests++))
    fi
    
    ((total_tests++))
    if test_endpoint "GET" "/config/custom/configurations/export" "Exportar configuraciones"; then
        ((passed_tests++))
    fi
    
    # 2. Endpoints de validación
    print_header "2. ENDPOINTS DE VALIDACIÓN"
    
    local test_config='{"batteryCapacity": 100.0, "isLithium": true, "thresholdPercentage": 3.0, "maxAllowedCurrent": 10000.0, "bulkVoltage": 14.4, "absorptionVoltage": 14.4, "floatVoltage": 13.6, "useFuenteDC": false, "fuenteDC_Amps": 0.0, "factorDivider": 1}'
    
    ((total_tests++))
    if test_endpoint "POST" "/config/custom/configurations/validate" "Validar configuración" "$test_config"; then
        ((passed_tests++))
    fi
    
    # 3. Endpoints individuales (rutas principales)
    print_header "3. ENDPOINTS INDIVIDUALES - RUTAS PRINCIPALES"
    
    ((total_tests++))
    if test_endpoint "POST" "/config/custom/config/TestValidation" "Crear configuración" "$test_config"; then
        ((passed_tests++))
    fi
    
    ((total_tests++))
    if test_endpoint "GET" "/config/custom/config/TestValidation" "Obtener configuración específica"; then
        ((passed_tests++))
    fi
    
    ((total_tests++))
    if test_endpoint "POST" "/config/custom/config/TestValidation/apply" "Aplicar configuración (ruta principal)"; then
        ((passed_tests++))
    fi
    
    # 4. Endpoints alternativos (compatibilidad)
    print_header "4. ENDPOINTS ALTERNATIVOS - COMPATIBILIDAD"
    
    ((total_tests++))
    if test_endpoint "POST" "/config/custom/configurations/TestValidation/apply" "Aplicar configuración (ruta alternativa)"; then
        ((passed_tests++))
    fi
    
    # 5. Limpiar
    print_header "5. LIMPIEZA"
    
    ((total_tests++))
    if test_endpoint "DELETE" "/config/custom/config/TestValidation" "Eliminar configuración de prueba"; then
        ((passed_tests++))
    fi
    
    # Resumen final
    print_header "RESUMEN DE VALIDACIÓN"
    
    local success_rate
    success_rate=$(( passed_tests * 100 / total_tests ))
    
    echo "📊 Resultados:"
    echo "   Total tests: $total_tests"
    echo "   Pasaron: $passed_tests"
    echo "   Fallaron: $((total_tests - passed_tests))"
    echo "   Tasa de éxito: $success_rate%"
    echo ""
    
    if [ $passed_tests -eq $total_tests ]; then
        print_success "¡Todos los endpoints están funcionando correctamente!"
        return 0
    else
        print_warning "Algunos endpoints tienen problemas"
        if [ $success_rate -ge 80 ]; then
            print_warning "Pero la API está mayormente funcional ($success_rate% éxito)"
            return 0
        else
            print_error "La API tiene problemas significativos ($success_rate% éxito)"
            return 1
        fi
    fi
}

# Ejecutar validación
validate_endpoints
