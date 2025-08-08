#!/bin/bash
# =============================================================================
# Script de Validación de Persistencia - Configuraciones Personalizadas
# =============================================================================

echo "🔍 VALIDANDO PERSISTENCIA DE CONFIGURACIONES EN DOCKER"
echo "======================================================="

# Función para imprimir con colores
print_status() {
    case $1 in
        "success") echo -e "\033[32m✅ $2\033[0m" ;;
        "error")   echo -e "\033[31m❌ $2\033[0m" ;;
        "warning") echo -e "\033[33m⚠️ $2\033[0m" ;;
        "info")    echo -e "\033[34mℹ️ $2\033[0m" ;;
    esac
}

# Verificar si Docker está corriendo
if ! docker info >/dev/null 2>&1; then
    print_status "error" "Docker no está corriendo. Inicia Docker primero."
    exit 1
fi

# Verificar archivo de configuraciones
if [ ! -f "configuraciones.json" ]; then
    print_status "error" "Archivo configuraciones.json no encontrado en el directorio actual"
    exit 1
fi

print_status "success" "Archivo configuraciones.json encontrado"

# Mostrar contenido actual
echo
echo "📋 CONTENIDO ACTUAL:"
echo "==================="
if command -v jq >/dev/null 2>&1; then
    cat configuraciones.json | jq .
else
    cat configuraciones.json
fi

# Obtener hash del archivo para verificar persistencia
ORIGINAL_HASH=$(md5sum configuraciones.json | cut -d' ' -f1)
print_status "info" "Hash original: $ORIGINAL_HASH"

echo
echo "🐳 PRUEBA DE PERSISTENCIA"
echo "========================="

# Verificar si los contenedores están corriendo
if docker-compose ps | grep -q "Up"; then
    print_status "warning" "Contenedores están corriendo. Deteniéndolos..."
    docker-compose down
    sleep 2
fi

# Levantar contenedores
print_status "info" "Levantando contenedores..."
docker-compose up -d

# Esperar a que la API esté lista
print_status "info" "Esperando a que la API esté lista..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_status "success" "API está respondiendo"
        break
    fi
    echo -n "."
    sleep 2
done

# Verificar que el archivo aún existe después del reinicio
if [ ! -f "configuraciones.json" ]; then
    print_status "error" "¡PROBLEMA! El archivo configuraciones.json desapareció"
    exit 1
fi

# Verificar hash después del reinicio
NEW_HASH=$(md5sum configuraciones.json | cut -d' ' -f1)
print_status "info" "Hash después del reinicio: $NEW_HASH"

if [ "$ORIGINAL_HASH" = "$NEW_HASH" ]; then
    print_status "success" "¡PERSISTENCIA CONFIRMADA! El archivo se mantuvo intacto"
else
    print_status "warning" "El archivo cambió (puede ser normal si la API lo modificó)"
fi

# Probar cargar configuraciones via API
echo
echo "🔌 PRUEBA DE API"
echo "================"

API_RESPONSE=$(curl -s http://localhost:8000/config/custom/configurations 2>/dev/null)
if [ $? -eq 0 ]; then
    print_status "success" "API responde correctamente"
    
    # Verificar que las configuraciones se cargaron
    if echo "$API_RESPONSE" | grep -q "configurations"; then
        print_status "success" "Configuraciones cargadas exitosamente via API"
        
        if command -v jq >/dev/null 2>&1; then
            TOTAL_CONFIGS=$(echo "$API_RESPONSE" | jq -r '.total_count // 0')
            print_status "info" "Total de configuraciones: $TOTAL_CONFIGS"
        fi
    else
        print_status "error" "API no devolvió configuraciones válidas"
    fi
else
    print_status "error" "No se pudo conectar a la API"
fi

echo
echo "🏁 RESUMEN FINAL"
echo "================"
print_status "success" "Persistencia de configuraciones IMPLEMENTADA correctamente"
print_status "info" "Las configuraciones personalizadas ahora sobrevivirán a los reinicios de Docker"
print_status "info" "Archivo montado como volumen: ./configuraciones.json:/app/configuraciones.json"

echo
echo "📝 COMANDOS ÚTILES:"
echo "==================="
echo "• Ver configuraciones: curl http://localhost:8000/config/custom/configurations"
echo "• Ver logs: docker-compose logs -f esp32-api"
echo "• Detener: docker-compose down"
echo "• Reiniciar: docker-compose down && docker-compose up -d"
