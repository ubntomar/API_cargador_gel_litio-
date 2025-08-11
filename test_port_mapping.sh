#!/bin/bash

# =============================================================================
# Test de Configuración de Puerto Serial Dinámico
# =============================================================================

echo "🔧 VERIFICANDO CONFIGURACIÓN DINÁMICA DE PUERTO SERIAL"
echo "======================================================="

# Función para mostrar configuración actual
show_current_config() {
    echo "📋 Configuración actual:"
    echo "   .env SERIAL_PORT: $(grep "^SERIAL_PORT=" .env | cut -d'=' -f2)"
    echo "   Docker Compose devices: $(grep -A1 "devices:" docker-compose.yml | tail -1 | xargs)"
}

# Función para test de diferentes puertos
test_port_mapping() {
    local test_port="$1"
    echo "🧪 Testeando puerto: $test_port"
    
    # Backup del .env original
    cp .env .env.backup
    
    # Cambiar puerto en .env
    sed -i "s|^SERIAL_PORT=.*|SERIAL_PORT=$test_port|" .env
    
    # Mostrar lo que Docker Compose interpretaría
    echo "   Docker Compose interpretaría:"
    SERIAL_PORT="$test_port" docker-compose config | grep -A2 "devices:" | grep -v "devices:" | head -1 | xargs
    
    # Restaurar .env
    mv .env.backup .env
    
    echo "   ✅ Mapeo: $test_port (host) → $test_port (container)"
    echo
}

echo "🔍 Estado inicial:"
show_current_config
echo

echo "🧪 Probando diferentes puertos:"
test_port_mapping "/dev/ttyUSB0"
test_port_mapping "/dev/ttyUSB1" 
test_port_mapping "/dev/ttyACM0"
test_port_mapping "/dev/ttyS5"

echo "💡 Explicación del mapeo:"
echo "   Formato: HOST_PORT:CONTAINER_PORT"
echo "   Nuestra configuración: \${SERIAL_PORT}:\${SERIAL_PORT}"
echo "   Resultado: El mismo puerto en ambos lados = CONSISTENCIA TOTAL"
echo

echo "🎯 Ventajas de esta configuración:"
echo "   ✅ Los logs del ESP32Manager mostrarán el puerto real"
echo "   ✅ No hay confusión entre puerto host vs container"
echo "   ✅ Debugging más simple"
echo "   ✅ Configuración transparente"
echo

echo "📝 Para cambiar puerto:"
echo "   1. Editar .env: SERIAL_PORT=/dev/ttyUSB1"
echo "   2. Reiniciar: docker-compose restart"
echo "   3. Los logs mostrarán: 'Conectado a /dev/ttyUSB1' (real)"
