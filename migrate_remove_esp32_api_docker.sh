#!/bin/bash
# =============================================================================
# Script de Migración - Eliminar esp32_api_docker/ 
# =============================================================================

echo "🚀 MIGRACIÓN: Eliminando carpeta esp32_api_docker/"
echo "================================================="

# Función para imprimir con colores
print_status() {
    case $1 in
        "success") echo -e "\033[32m✅ $2\033[0m" ;;
        "error")   echo -e "\033[31m❌ $2\033[0m" ;;
        "warning") echo -e "\033[33m⚠️ $2\033[0m" ;;
        "info")    echo -e "\033[34mℹ️ $2\033[0m" ;;
    esac
}

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ] || [ ! -f "docker-compose.yml" ]; then
    print_status "error" "Debes ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

print_status "success" "Directorio correcto detectado"

# Verificar si la carpeta esp32_api_docker existe
if [ -d "esp32_api_docker" ]; then
    print_status "info" "Carpeta esp32_api_docker/ encontrada"
    
    # Verificar si hay archivos importantes en la carpeta
    IMPORTANT_FILES=""
    if [ -f "esp32_api_docker/docker-compose.yml" ]; then
        IMPORTANT_FILES="$IMPORTANT_FILES docker-compose.yml"
    fi
    if [ -f "esp32_api_docker/Dockerfile" ]; then
        IMPORTANT_FILES="$IMPORTANT_FILES Dockerfile"
    fi
    if [ -f "esp32_api_docker/.env" ]; then
        IMPORTANT_FILES="$IMPORTANT_FILES .env"
    fi
    
    if [ -n "$IMPORTANT_FILES" ]; then
        print_status "warning" "Archivos importantes encontrados en esp32_api_docker/:"
        echo "   $IMPORTANT_FILES"
        echo
        read -p "¿Quieres hacer backup de estos archivos antes de eliminar la carpeta? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            print_status "info" "Creando backup..."
            mkdir -p backup_esp32_api_docker
            cp -r esp32_api_docker/* backup_esp32_api_docker/ 2>/dev/null
            print_status "success" "Backup creado en backup_esp32_api_docker/"
        fi
    fi
    
    echo
    read -p "¿Confirmas eliminar la carpeta esp32_api_docker/? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf esp32_api_docker/
        print_status "success" "Carpeta esp32_api_docker/ eliminada"
    else
        print_status "info" "Eliminación cancelada"
        exit 0
    fi
else
    print_status "info" "La carpeta esp32_api_docker/ no existe"
fi

# Verificar que los archivos Docker están en el directorio raíz
echo
print_status "info" "Verificando archivos Docker en directorio raíz..."

if [ -f "docker-compose.yml" ]; then
    print_status "success" "docker-compose.yml ✓"
else
    print_status "error" "docker-compose.yml NO encontrado en directorio raíz"
fi

if [ -f "Dockerfile" ]; then
    print_status "success" "Dockerfile ✓"
else
    print_status "warning" "Dockerfile no encontrado (puede estar en core/)"
fi

if [ -f "configuraciones.json" ]; then
    print_status "success" "configuraciones.json ✓"
else
    print_status "info" "configuraciones.json será creado automáticamente"
fi

echo
print_status "success" "MIGRACIÓN COMPLETADA"
echo "=============================="
print_status "info" "Ahora ejecuta Docker desde el directorio raíz:"
echo "   docker-compose up -d"
echo "   docker-compose logs -f esp32-api"

echo
print_status "info" "Archivos modificados para evitar recreación de esp32_api_docker/:"
echo "   ✅ install_orangepi.sh - Ya no crea la carpeta"
echo "   ✅ docker-compose.yml - Comentarios actualizados"  
echo "   ✅ README.md - Documentación actualizada"

if [ -d "backup_esp32_api_docker" ]; then
    echo
    print_status "info" "Backup disponible en: backup_esp32_api_docker/"
    print_status "info" "Puedes eliminar el backup cuando confirmes que todo funciona"
fi
