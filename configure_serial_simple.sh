#!/bin/bash

# =============================================================================
# ESP32 Solar Charger API - Configurador Serial Universal Multi-Arquitectura
# Auto-detección inteligente para x86_64, ARM64, RISC-V y detección de ESP32
# =============================================================================

set -e

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$CURRENT_DIR/.env"

# Detección de arquitectura
ARCH=$(uname -m)
case "$ARCH" in
    "riscv64") ARCH_NAME="RISC-V 64-bit" ;;
    "aarch64"|"arm64") ARCH_NAME="ARM64" ;;
    "x86_64"|"amd64") ARCH_NAME="x86_64" ;;
    *) ARCH_NAME="$ARCH" ;;
esac

echo "🔧 CONFIGURADOR SERIAL ESP32 - UNIVERSAL MULTI-ARQUITECTURA"
echo "🖥️ Arquitectura detectada: $ARCH_NAME ($ARCH)"
echo "=============================================================="

# Función para obtener información detallada del dispositivo
get_device_info() {
    local port="$1"
    local info=""
    
    # Intentar obtener información del dispositivo USB
    if [[ "$port" =~ /dev/ttyUSB[0-9]+ ]] || [[ "$port" =~ /dev/ttyACM[0-9]+ ]]; then
        # Buscar información en sysfs
        local device_path="/sys/class/tty/$(basename $port)/device"
        if [ -d "$device_path" ]; then
            # Buscar información del producto
            local product_file=""
            local manufacturer_file=""
            
            # Navegar hasta encontrar información USB
            local current_path="$device_path"
            for i in {1..5}; do
                if [ -f "$current_path/product" ]; then
                    product_file="$current_path/product"
                    manufacturer_file="$current_path/manufacturer"
                    break
                fi
                current_path="$(dirname "$current_path")"
            done
            
            if [ -n "$product_file" ] && [ -f "$product_file" ]; then
                local product=$(cat "$product_file" 2>/dev/null)
                local manufacturer=$(cat "$manufacturer_file" 2>/dev/null)
                info="$manufacturer $product"
            fi
        fi
        
        # Información adicional de lsusb si está disponible
        if command -v lsusb &> /dev/null; then
            local usb_info=$(lsusb 2>/dev/null | grep -i "espressif\|silicon.*labs\|ch340\|cp210\|ftdi" | head -1)
            if [ -n "$usb_info" ]; then
                info="$info | $usb_info"
            fi
        fi
    fi
    
    # Si no hay información específica, dar información general
    if [ -z "$info" ]; then
        if [[ "$port" =~ /dev/ttyS[0-9]+ ]]; then
            info="Puerto serial nativo del sistema"
        elif [[ "$port" =~ /dev/ttyUSB[0-9]+ ]]; then
            info="Dispositivo USB-Serial"
        elif [[ "$port" =~ /dev/ttyACM[0-9]+ ]]; then
            info="Dispositivo USB-CDC (ESP32-S2/S3 nativo)"
        fi
    fi
    
    echo "$info"
}

# Función para detectar ESP32 automáticamente
auto_detect_esp32() {
    echo "🔍 Auto-detección de ESP32 en $ARCH_NAME..."
    
    local esp32_ports=()
    
    # Buscar en todos los puertos disponibles
    for port in /dev/ttyUSB* /dev/ttyACM* /dev/ttyS*; do
        if [ -e "$port" ] && [ -r "$port" ] && [ -w "$port" ]; then
            local device_info=$(get_device_info "$port")
            
            # Buscar patrones conocidos de ESP32
            if echo "$device_info" | grep -iq "espressif\|esp32\|silicon.*labs\|ch340\|cp210"; then
                esp32_ports+=("$port")
                echo "   🎯 ESP32 detectado: $port"
                echo "      └─ $device_info"
            fi
        fi
    done
    
    if [ ${#esp32_ports[@]} -gt 0 ]; then
        echo "✅ ESP32(s) encontrado(s): ${esp32_ports[*]}"
        echo "${esp32_ports[0]}"  # Retornar el primer puerto detectado
    else
        echo "⚠️ No se detectó ESP32 automáticamente"
        echo ""
    fi
}

# Función para mostrar puertos disponibles con detección inteligente
show_available_ports() {
    echo "📋 Puertos seriales disponibles en $ARCH_NAME:"
    echo
    
    # Auto-detección de ESP32
    local esp32_detected=$(auto_detect_esp32)
    
    echo "🔌 Puertos USB (dispositivos conectados):"
    local usb_found=false
    for port in /dev/ttyUSB*; do
        if [ -e "$port" ]; then
            usb_found=true
            local info=$(get_device_info "$port")
            local permissions=$(ls -la "$port" | awk '{print $1 " " $3 ":" $4}')
            echo "   $port - $permissions"
            if [ -n "$info" ]; then
                echo "      └─ $info"
            fi
            
            # Marcar si es ESP32 detectado
            if [[ "$esp32_detected" == *"$port"* ]]; then
                echo "      🎯 ESP32 DETECTADO"
            fi
        fi
    done
    if [ "$usb_found" = false ]; then
        echo "   (ningún puerto ttyUSB encontrado)"
    fi
    echo
    
    echo "🔌 Puertos ACM (USB-CDC, ESP32-S2/S3 nativo):"
    local acm_found=false
    for port in /dev/ttyACM*; do
        if [ -e "$port" ]; then
            acm_found=true
            local info=$(get_device_info "$port")
            local permissions=$(ls -la "$port" | awk '{print $1 " " $3 ":" $4}')
            echo "   $port - $permissions"
            if [ -n "$info" ]; then
                echo "      └─ $info"
            fi
            
            # Marcar si es ESP32 detectado
            if [[ "$esp32_detected" == *"$port"* ]]; then
                echo "      🎯 ESP32 DETECTADO"
            fi
        fi
    done
    if [ "$acm_found" = false ]; then
        echo "   (ningún puerto ttyACM encontrado)"
    fi
    echo
    
    echo "🖥️ Puertos seriales del sistema (primeros 6):"
    local serial_found=false
    for port in /dev/ttyS{0..5}; do
        if [ -e "$port" ]; then
            serial_found=true
            local permissions=$(ls -la "$port" | awk '{print $1 " " $3 ":" $4}')
            echo "   $port - $permissions"
        fi
    done
    if [ "$serial_found" = false ]; then
        echo "   (ningún puerto ttyS encontrado)"
    fi
    echo

# Función para obtener puerto actual
get_current_port() {
    if [[ -f "$ENV_FILE" ]]; then
        grep "^SERIAL_PORT=" "$ENV_FILE" | cut -d'=' -f2 || echo "/dev/ttyUSB0"
    else
        echo "/dev/ttyUSB0"
    fi
}

# Función para cambiar puerto con validación multi-arquitectura
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
        echo "💡 Creando archivo .env con configuración por defecto..."
        create_default_env_file "$new_port"
        return 0
    fi
    
    # Verificar que el puerto existe y permisos
    if [[ ! -e "$new_port" ]]; then
        echo "⚠️ Advertencia: El puerto $new_port no existe actualmente en $ARCH_NAME"
        echo "💡 Esto puede ser normal si el ESP32 no está conectado"
        read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Operación cancelada"
            return 1
        fi
    elif [[ ! -r "$new_port" ]] || [[ ! -w "$new_port" ]]; then
        echo "⚠️ Advertencia: Sin permisos de lectura/escritura en $new_port"
        echo "🔧 Configurando permisos automáticamente..."
        
        # Agregar usuario al grupo dialout
        sudo usermod -aG dialout $USER 2>/dev/null || true
        
        # Configurar permisos temporales
        sudo chmod 666 "$new_port" 2>/dev/null || true
        
        echo "✅ Permisos configurados. Reinicia la sesión para aplicar cambios permanentes."
    fi
    
    # Cambiar puerto en .env
    if sed -i "s|^SERIAL_PORT=.*|SERIAL_PORT=$new_port|" "$ENV_FILE"; then
        echo "✅ Puerto serial cambiado a: $new_port en $ARCH_NAME"
        echo "   Archivo .env actualizado correctamente"
        
        # Mostrar información adicional del dispositivo si está disponible
        local device_info=$(get_device_info "$new_port")
        if [ -n "$device_info" ]; then
            echo "   📡 Dispositivo: $device_info"
        fi
        
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
            echo "⚠️ Recuerde ejecutar 'docker-compose restart' para aplicar los cambios"
        fi
    else
        echo "❌ Error actualizando archivo .env"
        return 1
    fi
}

# Función para crear archivo .env por defecto
create_default_env_file() {
    local default_port="$1"
    
    cat > "$ENV_FILE" << EOF
# ESP32 Solar Charger API - Configuración Multi-Arquitectura
# Generado automáticamente para $ARCH_NAME ($ARCH)

SERIAL_PORT=$default_port
SERIAL_BAUDRATE=9600
SERIAL_TIMEOUT=3.0

HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Rate Limiting
MIN_COMMAND_INTERVAL=0.6
MAX_REQUESTS_PER_MINUTE=60

# Cache
CACHE_TTL=2

# Timezone
TZ=America/Bogota
EOF
    
    echo "✅ Archivo .env creado con puerto $default_port"
}

# Función para reiniciar Docker con detección universal
restart_docker() {
    echo "🔄 Reiniciando contenedores Docker en $ARCH_NAME..."
    
    # Verificar qué método de compose está disponible
    if command -v docker-compose &> /dev/null; then
        if docker-compose down && docker-compose up -d; then
            echo "✅ Contenedores reiniciados exitosamente con docker-compose"
        else
            echo "❌ Error reiniciando contenedores con docker-compose"
            return 1
        fi
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        if docker compose down && docker compose up -d; then
            echo "✅ Contenedores reiniciados exitosamente con docker compose"
        else
            echo "❌ Error reiniciando contenedores con docker compose"
            return 1
        fi
    else
        echo "❌ No se encontró docker-compose o docker compose"
        echo "💡 Reinicie manualmente los contenedores"
        return 1
    fi
}

# Procesar argumentos con opciones multi-arquitectura
case "${1:-menu}" in
    "list")
        show_available_ports
        ;;
    
    "current")
        current_port=$(get_current_port)
        echo "📡 Puerto actual: $current_port"
        if [ -e "$current_port" ]; then
            local device_info=$(get_device_info "$current_port")
            if [ -n "$device_info" ]; then
                echo "   📋 Dispositivo: $device_info"
            fi
            echo "   ✅ Puerto disponible en $ARCH_NAME"
        else
            echo "   ⚠️ Puerto no disponible actualmente"
        fi
        ;;
    
    "auto")
        echo "🔍 Iniciando auto-detección en $ARCH_NAME..."
        esp32_port=$(auto_detect_esp32)
        if [ -n "$esp32_port" ]; then
            echo ""
            echo "🎯 ESP32 detectado automáticamente: $esp32_port"
            read -p "¿Configurar este puerto automáticamente? (Y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                change_port "$esp32_port"
            else
                echo "❌ Auto-configuración cancelada"
            fi
        else
            echo "❌ No se pudo detectar ESP32 automáticamente en $ARCH_NAME"
            echo "💡 Use './configure_serial_simple.sh list' para ver puertos disponibles"
            echo "💡 Use './configure_serial_simple.sh /dev/ttyXXX' para configurar manualmente"
        fi
        ;;
    
    "/dev/"*)
        change_port "$1"
        ;;
    
    "help"|"-h"|"--help")
        echo "Uso: $0 [opción|puerto]"
        echo
        echo "Opciones:"
        echo "  list       - Mostrar puertos disponibles con detección ESP32"
        echo "  current    - Mostrar puerto actual configurado"
        echo "  auto       - Auto-detección y configuración de ESP32"
        echo "  /dev/ttyX  - Configurar puerto específico"
        echo "  help       - Mostrar esta ayuda"
        echo
        echo "Ejemplos para $ARCH_NAME:"
        echo "  $0 list                    # Ver todos los puertos"
        echo "  $0 auto                    # Auto-detectar ESP32"
        echo "  $0 /dev/ttyUSB0           # Configurar puerto USB"
        echo "  $0 /dev/ttyACM0           # Configurar puerto ACM (ESP32-S2/S3)"
        echo "  $0 /dev/ttyS5             # Configurar puerto serial nativo"
        ;;
    
    "menu"|*)
        # Menú interactivo mejorado
        while true; do
            clear
            echo "🔧 CONFIGURADOR SERIAL ESP32 - $ARCH_NAME"
            echo "============================================"
            echo
            echo "Puerto actual: $(get_current_port)"
            echo
            echo "Opciones:"
            echo "1) 📋 Listar puertos disponibles"
            echo "2) 🔍 Auto-detectar ESP32"
            echo "3) ⚙️ Configurar puerto manualmente"
            echo "4) 🔄 Reiniciar Docker Compose"
            echo "5) ❌ Salir"
            echo
            read -p "Selecciona una opción (1-5): " choice
            
            case $choice in
                1)
                    echo
                    show_available_ports
                    read -p "Presiona Enter para continuar..." dummy
                    ;;
                2)
                    echo
                    esp32_port=$(auto_detect_esp32)
                    if [ -n "$esp32_port" ]; then
                        echo ""
                        echo "🎯 ESP32 detectado: $esp32_port"
                        read -p "¿Configurar este puerto? (Y/n): " -n 1 -r
                        echo
                        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                            change_port "$esp32_port"
                        fi
                    else
                        echo "❌ No se detectó ESP32 automáticamente"
                    fi
                    read -p "Presiona Enter para continuar..." dummy
                    ;;
                3)
                    echo
                    show_available_ports
                    echo
                    read -p "Ingresa el puerto (ej: /dev/ttyUSB0): " manual_port
                    if [ -n "$manual_port" ]; then
                        change_port "$manual_port"
                    fi
                    read -p "Presiona Enter para continuar..." dummy
                    ;;
                4)
                    echo
                    restart_docker
                    read -p "Presiona Enter para continuar..." dummy
                    ;;
                5)
                    echo "👋 ¡Hasta luego!"
                    exit 0
                    ;;
                *)
                    echo "❌ Opción inválida"
                    sleep 1
                    ;;
            esac
        done
        ;;
esac
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
