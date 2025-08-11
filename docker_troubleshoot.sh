#!/bin/bash
# =============================================================================
# ESP32 API - Docker Troubleshooting Script
# =============================================================================
# Este script implementa las soluciones documentadas en DOCKER_DEBUGGING_GUIDE.md
# para problemas comunes de Docker encontrados durante el desarrollo.

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🐛 $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
}

print_status() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función principal de diagnóstico
diagnose_docker_issues() {
    print_header "DIAGNÓSTICO DOCKER ESP32 API"
    
    # 1. Verificar que Docker esté corriendo
    print_status "Verificando Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker no está corriendo"
        print_status "Ejecuta: sudo systemctl start docker"
        return 1
    fi
    print_success "Docker está corriendo"
    
    # 2. Verificar contenedores
    print_status "Verificando contenedores ESP32 API..."
    CONTAINER_NAME=$(docker ps --format "table {{.Names}}" | grep esp32 | head -1)
    
    if [ -z "$CONTAINER_NAME" ]; then
        print_error "No se encontró contenedor ESP32 API corriendo"
        print_status "Ejecuta: docker-compose up -d"
        return 1
    fi
    
    print_success "Contenedor encontrado: $CONTAINER_NAME"
    
    # 3. Verificar sincronización de código
    print_status "Verificando sincronización de código..."
    
    if [ -f "api/config.py" ]; then
        HOST_LINES=$(wc -l < api/config.py)
        CONTAINER_LINES=$(docker exec "$CONTAINER_NAME" wc -l < /app/api/config.py 2>/dev/null || echo "0")
        
        echo "  Host: $HOST_LINES líneas"
        echo "  Container: $CONTAINER_LINES líneas"
        
        if [ "$HOST_LINES" -eq "$CONTAINER_LINES" ]; then
            print_success "Código sincronizado correctamente"
        else
            print_error "CÓDIGO DESINCRONIZADO - Este es probablemente el problema"
            print_warning "El contenedor está usando código en caché"
            return 2
        fi
    else
        print_warning "Archivo api/config.py no encontrado en host"
    fi
    
    # 4. Verificar volúmenes
    print_status "Verificando configuración de volúmenes..."
    
    VOLUME_CHECK=$(docker inspect "$CONTAINER_NAME" 2>/dev/null | grep -o "/app/api\|/app/services\|/app/models\|/app/core" | wc -l)
    
    if [ "$VOLUME_CHECK" -ge 3 ]; then
        print_success "Volúmenes de desarrollo configurados correctamente"
    else
        print_warning "Volúmenes de desarrollo no están completamente configurados"
        print_status "Verifica que docker-compose.yml tenga volumes para: ./api, ./services, ./models, ./core"
    fi
    
    # 5. Verificar logs recientes
    print_status "Verificando logs recientes..."
    echo "Últimas 5 líneas de logs:"
    docker logs --tail 5 "$CONTAINER_NAME" 2>/dev/null || print_warning "No se pudieron obtener logs"
    
    return 0
}

# Función para arreglar problemas de código desincronizado
fix_code_sync() {
    print_header "ARREGLANDO SINCRONIZACIÓN DE CÓDIGO"
    
    print_status "Deteniendo servicios..."
    docker-compose down
    
    print_status "Reiniciando servicios..."
    docker-compose up -d
    
    print_status "Esperando a que los servicios estén listos..."
    sleep 5
    
    # Verificar que el fix funcionó
    CONTAINER_NAME=$(docker ps --format "table {{.Names}}" | grep esp32 | head -1)
    if [ -n "$CONTAINER_NAME" ] && [ -f "api/config.py" ]; then
        HOST_LINES=$(wc -l < api/config.py)
        CONTAINER_LINES=$(docker exec "$CONTAINER_NAME" wc -l < /app/api/config.py 2>/dev/null || echo "0")
        
        if [ "$HOST_LINES" -eq "$CONTAINER_LINES" ]; then
            print_success "✅ Problema resuelto - Código sincronizado"
        else
            print_error "❌ Problema persiste - Verifica configuración de volúmenes"
        fi
    fi
}

# Función para mostrar información de debugging
show_debug_info() {
    print_header "INFORMACIÓN DE DEBUGGING"
    
    echo -e "${CYAN}Comandos útiles para debugging:${NC}"
    echo ""
    echo "1. Ver archivos en el contenedor:"
    echo "   docker exec -it \$(docker ps | grep esp32 | awk '{print \$1}') ls -la /app/api/"
    echo ""
    echo "2. Comparar archivos host vs contenedor:"
    echo "   wc -l api/config.py"
    echo "   docker exec \$(docker ps | grep esp32 | awk '{print \$1}') wc -l /app/api/config.py"
    echo ""
    echo "3. Ver logs en tiempo real:"
    echo "   docker-compose logs -f web"
    echo ""
    echo "4. Inspeccionar contenedor:"
    echo "   docker exec -it \$(docker ps | grep esp32 | awk '{print \$1}') /bin/bash"
    echo ""
    echo "5. Reiniciar servicios completamente:"
    echo "   docker-compose down && docker-compose up -d"
    echo ""
    echo "6. Ver configuración de volúmenes:"
    echo "   docker inspect \$(docker ps | grep esp32 | awk '{print \$1}') | grep -A 10 \"Mounts\""
}

# Función principal
main() {
    case "${1:-diagnose}" in
        "diagnose"|"check")
            RESULT=$(diagnose_docker_issues)
            EXIT_CODE=$?
            
            if [ $EXIT_CODE -eq 2 ]; then
                echo ""
                print_warning "Se detectó problema de sincronización de código"
                read -p "¿Quieres que lo arregle automáticamente? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    fix_code_sync
                fi
            fi
            ;;
        "fix"|"repair")
            fix_code_sync
            ;;
        "info"|"debug")
            show_debug_info
            ;;
        "help"|"--help")
            echo "Uso: $0 [comando]"
            echo ""
            echo "Comandos:"
            echo "  diagnose, check  - Diagnosticar problemas (por defecto)"
            echo "  fix, repair      - Arreglar problemas de sincronización"
            echo "  info, debug      - Mostrar información de debugging"
            echo "  help             - Mostrar esta ayuda"
            echo ""
            echo "Ejemplos:"
            echo "  $0               # Diagnosticar problemas"
            echo "  $0 fix           # Arreglar problemas automáticamente"
            echo "  $0 debug         # Ver comandos de debugging"
            ;;
        *)
            print_error "Comando desconocido: $1"
            echo "Usa '$0 help' para ver comandos disponibles"
            exit 1
            ;;
    esac
}

# Verificar que estemos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    print_error "Este script debe ejecutarse desde el directorio del proyecto"
    print_error "Asegúrate de estar en el directorio que contiene docker-compose.yml"
    exit 1
fi

main "$@"
