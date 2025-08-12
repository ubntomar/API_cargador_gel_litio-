#!/bin/bash
# Script de prueba para la detección de puertos USB

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_status() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🚀 $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
}

# Función simplificada para probar
test_detect_esp32_port() {
    print_header "🔍 PRUEBA DE DETECCIÓN DE PUERTO ESP32"
    
    echo "Buscando puertos seriales disponibles..."
    echo ""
    
    # Listar puertos disponibles
    echo "📋 Puertos seriales encontrados:"
    SERIAL_PORTS=$(ls /dev/tty{S,USB,ACM}* 2>/dev/null || true)
    
    if [ -z "$SERIAL_PORTS" ]; then
        print_warning "No se encontraron puertos seriales"
        return 1
    fi
    
    # Mostrar puertos con información
    COUNTER=1
    declare -a PORT_ARRAY
    
    for PORT in $SERIAL_PORTS; do
        echo "  $COUNTER) $PORT"
        
        # Obtener información adicional si está disponible
        if command -v udevadm &> /dev/null; then
            INFO=$(udevadm info --name="$PORT" 2>/dev/null | grep -E "ID_VENDOR|ID_MODEL|ID_SERIAL" | head -1 | cut -d= -f2 || echo "")
            if [ -n "$INFO" ]; then
                echo "     └─ $INFO"
            fi
        fi
        
        PORT_ARRAY[$COUNTER]=$PORT
        ((COUNTER++))
    done
    
    echo ""
    
    # Autodetección inteligente y selección de puerto
    ESP32_PORT=""
    USB_PORTS=()
    ESP32_CANDIDATE=""
    
    # Buscar por patrones conocidos de ESP32 y recopilar puertos USB
    for PORT in $SERIAL_PORTS; do
        if [ -e "$PORT" ]; then
            # Verificar si es un dispositivo USB común para ESP32
            if [[ "$PORT" == *"ttyUSB"* ]] || [[ "$PORT" == *"ttyACM"* ]]; then
                USB_PORTS+=("$PORT")
                
                if command -v udevadm &> /dev/null; then
                    # Buscar por vendor IDs comunes de ESP32
                    VENDOR_INFO=$(udevadm info --name="$PORT" 2>/dev/null | grep -i "ID_VENDOR_ID" || echo "")
                    
                    # IDs comunes: 10c4 (Silicon Labs), 1a86 (QinHeng), 0403 (FTDI)
                    if echo "$VENDOR_INFO" | grep -qE "(10c4|1a86|0403)"; then
                        ESP32_CANDIDATE="$PORT"
                        print_success "🎯 ESP32 detectado por vendor ID en: $ESP32_CANDIDATE"
                    fi
                fi
            fi
        fi
    done
    
    # Decidir qué puerto usar basado en lo que encontramos
    if [ ${#USB_PORTS[@]} -eq 0 ]; then
        # No hay puertos USB, continuar con lógica original
        echo "No se encontraron puertos USB (ttyUSB* o ttyACM*)"
    elif [ ${#USB_PORTS[@]} -eq 1 ]; then
        # Solo un puerto USB, usarlo automáticamente
        ESP32_PORT="${USB_PORTS[0]}"
        if [ -n "$ESP32_CANDIDATE" ]; then
            print_success "🎯 ESP32 detectado automáticamente en: $ESP32_PORT"
        else
            print_success "📱 Puerto USB único detectado: $ESP32_PORT"
        fi
    else
        # Múltiples puertos USB, permitir selección
        echo "🔍 Se encontraron múltiples puertos USB:"
        echo ""
        
        for i in "${!USB_PORTS[@]}"; do
            PORT="${USB_PORTS[$i]}"
            echo "  $((i+1))) $PORT"
            
            # Mostrar información adicional si está disponible
            if command -v udevadm &> /dev/null; then
                VENDOR_INFO=$(udevadm info --name="$PORT" 2>/dev/null | grep -E "ID_VENDOR|ID_MODEL|ID_SERIAL" | head -1 | cut -d= -f2 || echo "")
                if [ -n "$VENDOR_INFO" ]; then
                    echo "     └─ $VENDOR_INFO"
                fi
                
                # Marcar si es candidato ESP32
                VENDOR_ID=$(udevadm info --name="$PORT" 2>/dev/null | grep -i "ID_VENDOR_ID" | cut -d= -f2 || echo "")
                if echo "$VENDOR_ID" | grep -qE "(10c4|1a86|0403)"; then
                    echo "     └─ ⭐ Posible ESP32 (Vendor ID: $VENDOR_ID)"
                fi
            fi
        done
        
        echo ""
        if [ -n "$ESP32_CANDIDATE" ]; then
            echo "💡 Recomendado: $ESP32_CANDIDATE (detectado como ESP32)"
            echo ""
        fi
        
        # Pedir selección al usuario
        while true; do
            read -p "Selecciona el puerto para ESP32 (1-${#USB_PORTS[@]}): " CHOICE
            
            if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "${#USB_PORTS[@]}" ]; then
                ESP32_PORT="${USB_PORTS[$((CHOICE-1))]}"
                print_success "✅ Puerto seleccionado: $ESP32_PORT"
                break
            else
                echo "❌ Selección inválida. Ingresa un número entre 1 y ${#USB_PORTS[@]}"
            fi
        done
    fi
    
    echo ""
    print_success "✅ Puerto final configurado: $ESP32_PORT"
    echo "$ESP32_PORT"
}

# Ejecutar la función de prueba
test_detect_esp32_port
