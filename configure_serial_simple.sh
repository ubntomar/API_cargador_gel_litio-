#!/bin/bash

# =============================================================================
# Script SIMPLE para configurar puerto serial del ESP32
# =============================================================================

set -e

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$CURRENT_DIR/.env"

echo "🔧 CONFIGURADOR DE PUERTO SERIAL ESP32"
echo "======================================"

# Función para mostrar puertos disponibles
show_available_ports() {
    echo "📋 Puertos seriales disponibles:"
    echo
    
    echo "🔌 Puertos USB (dispositivos conectados):"
    if ls /dev/ttyUSB* >/dev/null 2>&1; then
        ls -la /dev/ttyUSB*
    else
        echo "   (ningún puerto ttyUSB encontrado)"
    fi
    echo
    
    echo "🔌 Puertos ACM (dispositivos conectados):"
    if ls /dev/ttyACM* >/dev/null 2>&1; then
        ls -la /dev/ttyACM*
    else
        echo "   (ningún puerto ttyACM encontrado)"
    fi
    echo
    
    echo "🖥️ Puertos seriales del sistema (primeros 6):"
    if ls /dev/ttyS[0-5] >/dev/null 2>&1; then
        ls -la /dev/ttyS[0-5]
    else
        echo "   (ningún puerto ttyS encontrado)"
    fi
    echo
}

# Función para obtener puerto actual
get_current_port() {
    if [[ -f "$ENV_FILE" ]]; then
        grep "^SERIAL_PORT=" "$ENV_FILE" | cut -d'=' -f2 || echo "/dev/ttyUSB0"
    else
        echo "/dev/ttyUSB0"
    fi
}

# Función para cambiar puerto
change_port() {
    local new_port="$1"
    
    # Validar formato
    if [[ ! "$new_port" =~ ^/dev/tty[A-Za-z0-9]+ ]]; then
        echo "❌ Error: Puerto debe tener formato /dev/ttyXXX"
        return 1
    fi
    
    # Verificar que el archivo .env existe
    if [[ ! -f "$ENV_FILE" ]]; then
        echo "❌ Error: No se encontró el archivo .env"
        return 1
    fi
    
    # Verificar que el puerto existe (opcional)
    if [[ ! -e "$new_port" ]]; then
        echo "⚠️  Advertencia: El puerto $new_port no existe actualmente"
        read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Operación cancelada"
            return 1
        fi
    fi
    
    # Cambiar puerto en .env
    if sed -i "s|^SERIAL_PORT=.*|SERIAL_PORT=$new_port|" "$ENV_FILE"; then
        echo "✅ Puerto serial cambiado a: $new_port"
        echo "   Archivo .env actualizado"
    else
        echo "❌ Error actualizando archivo .env"
        return 1
    fi
}

# Función para reiniciar Docker
restart_docker() {
    echo "🔄 Reiniciando contenedores Docker..."
    if docker-compose down && docker-compose up -d; then
        echo "✅ Contenedores reiniciados exitosamente"
    else
        echo "❌ Error reiniciando contenedores"
        return 1
    fi
}

# Procesar argumentos
case "${1:-menu}" in
    "list")
        show_available_ports
        ;;
    
    "current")
        echo "Puerto actual: $(get_current_port)"
        ;;
    
    "set")
        if [[ -z "$2" ]]; then
            echo "❌ Error: Debe especificar el puerto"
            echo "   Uso: $0 set /dev/ttyUSB1"
            exit 1
        fi
        change_port "$2"
        ;;
    
    "restart")
        restart_docker
        ;;
    
    "menu")
        echo "Puerto actual: $(get_current_port)"
        echo
        show_available_ports
        echo "Opciones disponibles:"
        echo "  list    - Mostrar puertos disponibles"
        echo "  current - Mostrar puerto actual"
        echo "  set     - Cambiar puerto (ej: $0 set /dev/ttyUSB1)"
        echo "  restart - Reiniciar Docker"
        ;;
    
    *)
        echo "❌ Uso: $0 [list|current|set <puerto>|restart|menu]"
        echo
        echo "Ejemplos:"
        echo "  $0 list                    # Mostrar puertos disponibles"
        echo "  $0 current                # Mostrar puerto actual"
        echo "  $0 set /dev/ttyUSB1       # Cambiar a /dev/ttyUSB1"
        echo "  $0 restart                # Reiniciar Docker"
        exit 1
        ;;
esac
