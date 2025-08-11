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
        echo "   Archivo .env actualizado correctamente"
        echo
        echo "🔄 IMPORTANTE: Para aplicar los cambios, ejecute:"
        echo "   docker-compose restart"
        echo
        echo "💡 O si prefiere reiniciar completamente:"
        echo "   docker-compose down && docker-compose up -d"
        echo
        read -p "¿Desea reiniciar Docker Compose ahora? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            restart_docker
        else
            echo "⚠️  Recuerde ejecutar 'docker-compose restart' para aplicar los cambios"
        fi
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
        echo "💡 FINALIDAD DEL SCRIPT:"
        echo "   Este script actualiza el archivo .env con el puerto serial correcto"
        echo "   y luego reinicia Docker Compose para aplicar los cambios."
        echo
        echo "📋 PROCESO COMPLETO:"
        echo "   1️⃣  Identificar puerto donde está conectado el ESP32"
        echo "   2️⃣  Actualizar SERIAL_PORT en archivo .env"
        echo "   3️⃣  Reiniciar Docker Compose: docker-compose restart"
        echo "   4️⃣  Verificar que la API se conecte al puerto correcto"
        echo
        echo "🔧 Puerto actual configurado: $(get_current_port)"
        echo
        show_available_ports
        echo "📋 OPCIONES DISPONIBLES:"
        echo "  list    - Mostrar puertos seriales disponibles en el sistema"
        echo "  current - Mostrar puerto configurado actualmente en .env"
        echo "  set     - Cambiar puerto en .env (ej: $0 set /dev/ttyUSB1)"
        echo "  restart - Reiniciar Docker: docker-compose down && docker-compose up -d"
        echo
        echo "⚡ COMANDO RÁPIDO PARA APLICAR CAMBIOS:"
        echo "   docker-compose restart"
        echo
        echo "🎯 RECORDATORIO: Después de cambiar el puerto, siempre ejecutar:"
        echo "   docker-compose restart  (para aplicar cambios)"
        ;;
    
    *)
        echo "🔧 CONFIGURADOR DE PUERTO SERIAL ESP32"
        echo "======================================"
        echo
        echo "💡 FINALIDAD: Actualizar .env y reiniciar Docker para cambiar puerto serial"
        echo
        echo "❌ Uso: $0 [list|current|set <puerto>|restart|menu]"
        echo
        echo "📋 COMANDOS DISPONIBLES:"
        echo "  $0 list                    # Ver puertos seriales disponibles"
        echo "  $0 current                # Ver puerto configurado en .env"
        echo "  $0 set /dev/ttyUSB1       # Cambiar puerto y preguntar si reiniciar"
        echo "  $0 restart                # Solo reiniciar Docker Compose"
        echo "  $0 menu                   # Mostrar menú completo con explicaciones"
        echo
        echo "🎯 PROCESO TÍPICO:"
        echo "  1. ./configure_serial_simple.sh list     (ver puertos disponibles)"
        echo "  2. ./configure_serial_simple.sh set /dev/ttyUSB1  (cambiar puerto)"
        echo "  3. docker-compose restart                 (aplicar cambios)"
        echo
        echo "⚡ Para ayuda completa: $0 menu"
        exit 1
        ;;
esac
