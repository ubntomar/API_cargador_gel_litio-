#!/bin/bash
# =============================================================================
# ESP32 API - Setup Universal Multi-Arquitectura con Auto-Detección de CPU
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Variable global para comando Docker Compose
DOCKER_COMPOSE_CMD=""

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🚀 $1${NC}"
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

# Función para detectar comando Docker Compose compatible
detect_docker_compose_command() {
    print_header "🔍 DETECCIÓN AUTOMÁTICA DE DOCKER COMPOSE"
    
    # Verificar que Docker esté funcionando
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker no está funcionando. Ejecuta: sudo systemctl start docker"
        exit 1
    fi
    
    print_status "Detectando sintaxis compatible de Docker Compose..."
    
    # Probar sintaxis moderna primero (docker compose)
    if docker compose version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
        print_success "✅ Usando sintaxis moderna: docker compose"
    # Probar sintaxis legacy (docker-compose)
    elif command -v docker-compose > /dev/null 2>&1 && docker-compose --version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker-compose"
        print_success "✅ Usando sintaxis legacy: docker-compose"
    else
        print_error "❌ No se encontró Docker Compose funcional"
        print_error "Instala Docker Compose con: sudo apt install docker-compose-plugin"
        exit 1
    fi
    
    # Verificar funcionamiento con comando de prueba
    print_status "Verificando funcionamiento..."
    if $DOCKER_COMPOSE_CMD version > /dev/null 2>&1; then
        VERSION_OUTPUT=$($DOCKER_COMPOSE_CMD version 2>/dev/null | head -1)
        print_success "✅ Docker Compose funcional: $VERSION_OUTPUT"
    else
        print_error "❌ Error verificando Docker Compose"
        exit 1
    fi
    
    echo ""
}

# Función de debugging para problemas comunes de Docker
show_docker_debugging_help() {
    print_header "🐛 GUÍA DE DEBUGGING DOCKER"
    
    echo -e "${YELLOW}Problemas Comunes y Soluciones:${NC}"
    echo ""
    
    echo -e "${CYAN}1. El endpoint funciona pero no aplica cambios:${NC}"
    echo "   • Problema: Docker usa código en caché"
    echo "   • Verificar: docker exec -it esp32-solar-api-web-1 cat /app/api/config.py | wc -l"
    echo "   • Comparar: wc -l api/config.py"
    echo "   • Solución: $DOCKER_COMPOSE_CMD down && $DOCKER_COMPOSE_CMD up -d"
    echo ""
    
    echo -e "${CYAN}2. Código no se actualiza automáticamente:${NC}"
    echo "   • Verificar volumes en docker-compose.yml:"
    echo "     - ./api:/app/api"
    echo "     - ./services:/app/services"
    echo "     - ./models:/app/models"
    echo "     - ./core:/app/core"
    echo ""
    
    echo -e "${CYAN}3. Comandos útiles de debugging:${NC}"
    echo "   • Ver archivos en container: docker exec -it esp32-solar-api-web-1 ls -la /app"
    echo "   • Ver logs: $DOCKER_COMPOSE_CMD logs -f web"
    echo "   • Reiniciar limpio: $DOCKER_COMPOSE_CMD down && $DOCKER_COMPOSE_CMD up -d"
    echo "   • Inspeccionar container: docker exec -it esp32-solar-api-web-1 /bin/bash"
    echo ""
    
    echo -e "${YELLOW}💡 TIP: Ejecuta 'bash quick_setup.sh debug' para mostrar esta ayuda${NC}"
    echo ""
}

# Función para detectar configuración de CPU
detect_cpu_configuration() {
    print_header "🔍 DETECCIÓN AUTOMÁTICA DE CPU Y ARQUITECTURA"
    
    # Detectar arquitectura
    ARCH=$(uname -m)
    CPU_COUNT=$(nproc)
    SYSTEM=$(uname -s)
    
    # Detectar tipo de arquitectura
    case "$ARCH" in
        "x86_64"|"amd64")
            ARCH_TYPE="x86_64"
            ARCH_EMOJI="🖥️"
            ;;
        "aarch64"|"arm64")
            ARCH_TYPE="arm64"
            ARCH_EMOJI="🍓"
            ;;
        "riscv64"|"riscv")
            ARCH_TYPE="riscv"
            ARCH_EMOJI="🍊"
            ;;
        "armv7l"|"armhf")
            ARCH_TYPE="armv7"
            ARCH_EMOJI="📱"
            ;;
        *)
            ARCH_TYPE="unknown"
            ARCH_EMOJI="❓"
            ;;
    esac
    
    # Calcular workers óptimos
    if [ "$CPU_COUNT" -le 1 ]; then
        OPTIMAL_WORKERS=1
    elif [ "$CPU_COUNT" -eq 2 ]; then
        OPTIMAL_WORKERS=1
    elif [ "$CPU_COUNT" -le 4 ]; then
        OPTIMAL_WORKERS=2
    elif [ "$CPU_COUNT" -le 6 ]; then
        OPTIMAL_WORKERS=3
    elif [ "$CPU_COUNT" -le 8 ]; then
        OPTIMAL_WORKERS=4
    else
        # Para muchos CPUs, máximo 6 workers, dejar 2 libres
        OPTIMAL_WORKERS=$((CPU_COUNT - 2))
        if [ "$OPTIMAL_WORKERS" -gt 6 ]; then
            OPTIMAL_WORKERS=6
        fi
    fi
    
    # Calcular límite de CPU
    if [ "$CPU_COUNT" -le 2 ]; then
        CPU_LIMIT="1.0"
    elif [ "$CPU_COUNT" -le 8 ]; then
        CPU_LIMIT=$((CPU_COUNT - 1)).0
    else
        # Para muchos CPUs, usar máximo 8
        CALC_LIMIT=$((CPU_COUNT - 2))
        if [ "$CALC_LIMIT" -gt 8 ]; then
            CALC_LIMIT=8
        fi
        CPU_LIMIT="$CALC_LIMIT.0"
    fi
    
    # Calcular memoria
    BASE_MEMORY=512
    WORKER_MEMORY=$((256 * (OPTIMAL_WORKERS - 1)))
    TOTAL_MEMORY=$((BASE_MEMORY + WORKER_MEMORY))
    
    # Límite máximo de 2GB
    if [ "$TOTAL_MEMORY" -gt 2048 ]; then
        TOTAL_MEMORY=2048
    fi
    
    MEMORY_LIMIT="${TOTAL_MEMORY}m"
    
    # Mostrar información detectada
    print_success "$ARCH_EMOJI Arquitectura detectada: $ARCH_TYPE ($ARCH)"
    print_success "🔧 CPUs disponibles: $CPU_COUNT"
    print_success "👥 Workers óptimos: $OPTIMAL_WORKERS"
    print_success "⚡ Límite CPU: $CPU_LIMIT"
    print_success "💾 Límite memoria: $MEMORY_LIMIT"
    
    # Configuración específica por arquitectura
    case "$ARCH_TYPE" in
        "riscv")
            print_status "🍊 Configuración RISC-V: Timeouts extendidos para mejor estabilidad"
            ;;
        "arm64"|"armv7")
            print_status "🍓 Configuración ARM: Optimizada para Raspberry Pi / Orange Pi"
            ;;
        "x86_64")
            print_status "🖥️ Configuración x86_64: Máximo rendimiento"
            ;;
    esac
    
    echo ""
}

# Detectar puerto serial automáticamente
detect_esp32_port() {
    print_header "🔍 DETECCIÓN AUTOMÁTICA DE PUERTO ESP32" >&2
    
    echo "Buscando puertos seriales disponibles..." >&2
    echo "" >&2
    
    # Listar puertos disponibles
    echo "📋 Puertos seriales encontrados:" >&2
    SERIAL_PORTS=$(ls /dev/tty{S,USB,ACM}* 2>/dev/null || true)
    
    if [ -z "$SERIAL_PORTS" ]; then
        print_warning "No se encontraron puertos seriales" >&2
        echo "Asegúrate de que:" >&2
        echo "  • El ESP32 esté conectado" >&2
        echo "  • El cable USB funcione correctamente" >&2
        echo "  • Los drivers estén instalados" >&2
        echo "" >&2
        return 1
    fi
    
    # Mostrar puertos con información
    COUNTER=1
    declare -a PORT_ARRAY
    
    for PORT in $SERIAL_PORTS; do
        echo "  $COUNTER) $PORT" >&2
        
        # Obtener información adicional si está disponible
        if command -v udevadm &> /dev/null; then
            INFO=$(udevadm info --name="$PORT" 2>/dev/null | grep -E "ID_VENDOR|ID_MODEL|ID_SERIAL" | head -1 | cut -d= -f2 || echo "")
            if [ -n "$INFO" ]; then
                echo "     └─ $INFO" >&2
            fi
        fi
        
        PORT_ARRAY[$COUNTER]=$PORT
        ((COUNTER++))
    done
    
    echo "" >&2
    
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
                        print_success "🎯 ESP32 detectado por vendor ID en: $ESP32_CANDIDATE" >&2
                    fi
                fi
            fi
        fi
    done
    
    # Decidir qué puerto usar basado en lo que encontramos
    if [ ${#USB_PORTS[@]} -eq 0 ]; then
        # No hay puertos USB, continuar con lógica original
        echo "No se encontraron puertos USB (ttyUSB* o ttyACM*)" >&2
    elif [ ${#USB_PORTS[@]} -eq 1 ]; then
        # Solo un puerto USB, usarlo automáticamente
        ESP32_PORT="${USB_PORTS[0]}"
        if [ -n "$ESP32_CANDIDATE" ]; then
            print_success "🎯 ESP32 detectado automáticamente en: $ESP32_PORT" >&2
        else
            print_success "📱 Puerto USB único detectado: $ESP32_PORT" >&2
        fi
    elif [ -n "$ESP32_CANDIDATE" ] && [ ${#USB_PORTS[@]} -gt 1 ]; then
        # Múltiples puertos, hay un candidato ESP32 claro, pero SIEMPRE selección manual
        echo "🔍 Se encontraron múltiples puertos USB:" >&2
        echo "" >&2
        for i in "${!USB_PORTS[@]}"; do
            PORT="${USB_PORTS[$i]}"
            echo "  $((i+1))) $PORT" >&2
            if command -v udevadm &> /dev/null; then
                VENDOR_INFO=$(udevadm info --name="$PORT" 2>/dev/null | grep -E "ID_VENDOR|ID_MODEL|ID_SERIAL" | head -1 | cut -d= -f2 || echo "")
                if [ -n "$VENDOR_INFO" ]; then
                    echo "     └─ $VENDOR_INFO" >&2
                fi
                VENDOR_ID=$(udevadm info --name="$PORT" 2>/dev/null | grep -i "ID_VENDOR_ID" | cut -d= -f2 || echo "")
                if echo "$VENDOR_ID" | grep -qE "(10c4|1a86|0403)"; then
                    echo "     └─ ⭐ Recomendado ESP32 (Vendor ID: $VENDOR_ID)" >&2
                else
                    echo "     └─ 📟 Otro dispositivo (Vendor ID: $VENDOR_ID)" >&2
                fi
            fi
        done
        echo "" >&2
        if [ -n "$ESP32_CANDIDATE" ]; then
            echo "💡 Recomendado: $ESP32_CANDIDATE (detectado como ESP32)" >&2
            echo "" >&2
        fi
        # SIEMPRE selección manual
        while true; do
            read -p "Selecciona el puerto para ESP32 (1-${#USB_PORTS[@]}): " CHOICE >&2
            if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "${#USB_PORTS[@]}" ]; then
                ESP32_PORT="${USB_PORTS[$((CHOICE-1))]}"
                print_success "✅ Puerto seleccionado: $ESP32_PORT" >&2
                break
            else
                echo "❌ Selección inválida. Ingresa un número entre 1 y ${#USB_PORTS[@]}" >&2
            fi
        done
    else
        # Múltiples puertos USB, permitir selección
        echo "🔍 Se encontraron múltiples puertos USB:" >&2
        echo "" >&2
        
        for i in "${!USB_PORTS[@]}"; do
            PORT="${USB_PORTS[$i]}"
            echo "  $((i+1))) $PORT" >&2
            
            # Mostrar información adicional si está disponible
            if command -v udevadm &> /dev/null; then
                VENDOR_INFO=$(udevadm info --name="$PORT" 2>/dev/null | grep -E "ID_VENDOR|ID_MODEL|ID_SERIAL" | head -1 | cut -d= -f2 || echo "")
                if [ -n "$VENDOR_INFO" ]; then
                    echo "     └─ $VENDOR_INFO" >&2
                fi
                
                # Marcar si es candidato ESP32
                VENDOR_ID=$(udevadm info --name="$PORT" 2>/dev/null | grep -i "ID_VENDOR_ID" | cut -d= -f2 || echo "")
                if echo "$VENDOR_ID" | grep -qE "(10c4|1a86|0403)"; then
                    echo "     └─ ⭐ Posible ESP32 (Vendor ID: $VENDOR_ID)" >&2
                fi
            fi
        done
        
        echo "" >&2
        if [ -n "$ESP32_CANDIDATE" ]; then
            echo "💡 Recomendado: $ESP32_CANDIDATE (detectado como ESP32)" >&2
            echo "" >&2
        fi
        
        # Pedir selección al usuario
        while true; do
            read -p "Selecciona el puerto para ESP32 (1-${#USB_PORTS[@]}): " CHOICE >&2
            
            if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "${#USB_PORTS[@]}" ]; then
                ESP32_PORT="${USB_PORTS[$((CHOICE-1))]}"
                print_success "✅ Puerto seleccionado: $ESP32_PORT" >&2
                break
            else
                echo "❌ Selección inválida. Ingresa un número entre 1 y ${#USB_PORTS[@]}" >&2
            fi
        done
    fi
    
    # Si no se detectó automáticamente, usar ttyS5 por defecto o preguntar
    if [ -z "$ESP32_PORT" ]; then
        if [ -e "/dev/ttyS5" ]; then
            ESP32_PORT="/dev/ttyS5"
            print_status "Usando puerto por defecto: $ESP32_PORT" >&2
        else
            echo "No se pudo detectar el ESP32 automáticamente." >&2
            echo "" >&2
            echo "Selecciona el puerto manualmente:" >&2
            read -p "Número de puerto (1-$((COUNTER-1))) o ruta completa: " PORT_CHOICE
            
            if [[ "$PORT_CHOICE" =~ ^[0-9]+$ ]] && [ "$PORT_CHOICE" -ge 1 ] && [ "$PORT_CHOICE" -lt "$COUNTER" ]; then
                ESP32_PORT="${PORT_ARRAY[$PORT_CHOICE]}"
            elif [ -e "$PORT_CHOICE" ]; then
                ESP32_PORT="$PORT_CHOICE"
            else
                print_error "Puerto inválido: $PORT_CHOICE" >&2
                return 1
            fi
        fi
    fi
    
    # Verificar permisos del puerto
    if [ ! -r "$ESP32_PORT" ] || [ ! -w "$ESP32_PORT" ]; then
        print_warning "Configurando permisos para $ESP32_PORT..." >&2
        sudo chmod 666 "$ESP32_PORT" 2>/dev/null || true
        
        # Agregar al grupo dialout si no está
        if ! groups | grep -q dialout; then
            print_status "Agregando usuario al grupo dialout..." >&2
            sudo usermod -aG dialout $USER
            print_warning "⚠️ Necesitarás reiniciar la sesión para aplicar permisos de grupo" >&2
        fi
    fi
    
    print_success "✅ Puerto ESP32 configurado: $ESP32_PORT" >&2
    echo "$ESP32_PORT"
}

# Configurar archivos del proyecto
configure_project() {
    local ESP32_PORT="$1"
    
    print_header "⚙️ CONFIGURANDO PROYECTO MULTI-ARQUITECTURA"
    
    # Detectar configuración de CPU
    detect_cpu_configuration
    
    print_status "Generando configuración automática..."
    
    # Resolver configuración multi-CPU
    if [ -f "resolve_docker_config.py" ]; then
        print_status "Ejecutando auto-detección de CPU..."
        if command -v python3 >/dev/null 2>&1; then
            # Verificar si ya hay un entorno virtual activo
            if [ -n "$VIRTUAL_ENV" ]; then
                python3 resolve_docker_config.py 2>/dev/null || print_warning "Auto-detección falló, usando configuración manual"
            elif [ -d "venv" ]; then
                source venv/bin/activate 2>/dev/null || true
                python3 resolve_docker_config.py 2>/dev/null || print_warning "Auto-detección falló, usando configuración manual"
            else
                print_warning "Entorno virtual no encontrado, usando configuración manual"
            fi
        else
            print_warning "Python3 no encontrado, usando configuración manual"
        fi
    fi
    
    # Configurar docker-compose según arquitectura
    COMPOSE_FILE="docker-compose.yml"
    
    # Si existe el archivo resuelto, usarlo
    if [ -f "docker-compose.resolved.yml" ]; then
        COMPOSE_FILE="docker-compose.resolved.yml"
        print_success "✅ Usando configuración auto-resuelta: $COMPOSE_FILE"
    else
        print_status "Configurando manualmente docker-compose.yml..."
        
        # Backup del archivo original
        if [ -f "docker-compose.yml" ]; then
            cp docker-compose.yml docker-compose.yml.backup
        fi
    fi
    

    # Configurar puerto serial solo si el archivo de configuración principal existe
    if [ -f "$COMPOSE_FILE" ]; then
        print_status "Configurando puerto serial: $ESP32_PORT en $COMPOSE_FILE..."

        TEMP_FILE=$(mktemp)
        cp "$COMPOSE_FILE" "$TEMP_FILE"

        # Reemplazar puertos usando métodos más seguros
        if command -v perl >/dev/null 2>&1; then
            perl -pi -e "s|/dev/ttyUSB[0-9]*|$ESP32_PORT|g" "$COMPOSE_FILE"
            perl -pi -e "s|/dev/ttyACM[0-9]*|$ESP32_PORT|g" "$COMPOSE_FILE"
            perl -pi -e "s|/dev/ttyS[0-9]*|$ESP32_PORT|g" "$COMPOSE_FILE"
            perl -pi -e "s|SERIAL_PORT=/dev/tty[A-Za-z0-9]*|SERIAL_PORT=$ESP32_PORT|g" "$COMPOSE_FILE"
        else
            sed -i "s|/dev/ttyUSB0|$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|/dev/ttyUSB1|$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|/dev/ttyACM0|$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|/dev/ttyACM1|$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|/dev/ttyS5|$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|/dev/ttyS0|$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|SERIAL_PORT=/dev/ttyUSB0|SERIAL_PORT=$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|SERIAL_PORT=/dev/ttyACM0|SERIAL_PORT=$ESP32_PORT|g" "$COMPOSE_FILE"
            sed -i "s|SERIAL_PORT=/dev/ttyS5|SERIAL_PORT=$ESP32_PORT|g" "$COMPOSE_FILE"
        fi

        # Verificar que los cambios se aplicaron
        if grep -q "$ESP32_PORT" "$COMPOSE_FILE"; then
            print_success "✅ $COMPOSE_FILE configurado correctamente con $ESP32_PORT"
            rm -f "$TEMP_FILE"
        else
            print_warning "⚠️ Restaurando archivo original y usando configuración manual..."
            cp "$TEMP_FILE" "$COMPOSE_FILE"
            rm -f "$TEMP_FILE"

            print_error "❌ No se pudo configurar el puerto automáticamente"
            print_status "Será necesario editar manualmente $COMPOSE_FILE"
            print_status "Cambia todas las referencias de puertos serial a: $ESP32_PORT"
            echo ""
            print_status "Puedes continuar y editar el archivo después, o cancelar con Ctrl+C"
            read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Setup cancelado"
                exit 1
            fi
        fi
    else
        print_error "❌ No se encontró $COMPOSE_FILE"
        return 1
    fi
    
    # Actualizar .env.docker (crear si no existe)
    if [ -f ".env.docker" ]; then
        cp .env.docker .env.docker.backup
        # Usar un método más seguro para el reemplazo
        grep -v "^SERIAL_PORT=" .env.docker > .env.docker.tmp || true
        echo "SERIAL_PORT=${ESP32_PORT}" >> .env.docker.tmp
        mv .env.docker.tmp .env.docker
        print_success "✅ .env.docker actualizado"
    else
        # Crear .env.docker desde docker-compose.yml environment
        print_status "Creando .env.docker..."
        echo "SERIAL_PORT=${ESP32_PORT}" > .env.docker
        print_success "✅ .env.docker creado"
    fi
    
    # Crear archivo .env principal si no existe
    if [ ! -f ".env" ]; then
        print_status "Creando archivo .env..."
        if [ -f ".env.resolved" ]; then
            # Usar el archivo .env.resolved como base y actualizar el puerto
            cp .env.resolved .env
            # Actualizar el puerto serial en .env
            if grep -q "^SERIAL_PORT=" .env; then
                sed -i "s|^SERIAL_PORT=.*|SERIAL_PORT=${ESP32_PORT}|" .env
            else
                echo "SERIAL_PORT=${ESP32_PORT}" >> .env
            fi
        elif [ -f ".env.docker" ]; then
            cp .env.docker .env
        else
            # Crear .env básico
            cat > .env << EOF
# ESP32 Solar Charger API - Configuración
DEBUG=false
HOST=0.0.0.0
PORT=8000
SERIAL_PORT=${ESP32_PORT}
SERIAL_BAUDRATE=9600
SERIAL_TIMEOUT=3.0
MAX_WORKERS=auto
CPU_LIMIT=auto
MEMORY_LIMIT=auto
FORCE_SINGLE_WORKER=false
REDIS_URL=redis://esp32-redis:6379
MIN_COMMAND_INTERVAL=0.6
MAX_REQUESTS_PER_MINUTE=60
CACHE_TTL=2
LOG_LEVEL=INFO
TZ=America/Bogota
EOF
        fi
        print_success "✅ .env creado"
    else
        # Actualizar puerto en .env existente
        print_status "Actualizando puerto en .env existente..."
        if grep -q "^SERIAL_PORT=" .env; then
            sed -i "s|^SERIAL_PORT=.*|SERIAL_PORT=${ESP32_PORT}|" .env
        else
            echo "SERIAL_PORT=${ESP32_PORT}" >> .env
        fi
        print_success "✅ .env actualizado"
    fi
}

# Configurar permisos de directorios para contenedores
setup_directory_permissions() {
    print_header "🔧 CONFIGURANDO PERMISOS DE DIRECTORIOS"
    
    # Crear directorios si no existen
    print_status "📁 Creando directorios necesarios..."
    mkdir -p logs data
    
    # Obtener el ID del usuario actual
    CURRENT_USER_ID=$(id -u)
    CURRENT_GROUP_ID=$(id -g)
    
    print_status "👤 Usuario actual: ID $CURRENT_USER_ID:$CURRENT_GROUP_ID"
    
    # Verificar si los directorios tienen permisos correctos
    if [ -d "logs" ]; then
        LOGS_OWNER=$(stat -c '%u:%g' logs)
        if [ "$LOGS_OWNER" != "$CURRENT_USER_ID:$CURRENT_GROUP_ID" ]; then
            print_status "🔧 Corrigiendo permisos del directorio logs..."
            if sudo -n true 2>/dev/null; then
                # Si tenemos sudo sin contraseña
                sudo chown -R "$CURRENT_USER_ID:$CURRENT_GROUP_ID" logs
                print_success "✅ Permisos de logs corregidos con sudo"
            else
                print_warning "⚠️ Se requieren permisos de administrador para logs"
                echo "Ejecutando: sudo chown -R $CURRENT_USER_ID:$CURRENT_GROUP_ID logs"
                sudo chown -R "$CURRENT_USER_ID:$CURRENT_GROUP_ID" logs
                if [ $? -eq 0 ]; then
                    print_success "✅ Permisos de logs corregidos"
                else
                    print_warning "⚠️ No se pudieron corregir permisos de logs, continuando..."
                fi
            fi
        else
            print_success "✅ Permisos de logs ya son correctos"
        fi
    fi
    
    if [ -d "data" ]; then
        DATA_OWNER=$(stat -c '%u:%g' data)
        if [ "$DATA_OWNER" != "$CURRENT_USER_ID:$CURRENT_GROUP_ID" ]; then
            print_status "🔧 Corrigiendo permisos del directorio data..."
            if sudo -n true 2>/dev/null; then
                # Si tenemos sudo sin contraseña
                sudo chown -R "$CURRENT_USER_ID:$CURRENT_GROUP_ID" data
                print_success "✅ Permisos de data corregidos con sudo"
            else
                print_warning "⚠️ Se requieren permisos de administrador para data"
                echo "Ejecutando: sudo chown -R $CURRENT_USER_ID:$CURRENT_GROUP_ID data"
                sudo chown -R "$CURRENT_USER_ID:$CURRENT_GROUP_ID" data
                if [ $? -eq 0 ]; then
                    print_success "✅ Permisos de data corregidos"
                else
                    print_warning "⚠️ No se pudieron corregir permisos de data, continuando..."
                fi
            fi
        else
            print_success "✅ Permisos de data ya son correctos"
        fi
    fi
    
    # Asegurar permisos de escritura completos para contenedores Docker
    print_status "🔧 Aplicando permisos de escritura (777) para contenedores..."
    chmod 777 logs data 2>/dev/null || {
        print_warning "⚠️ Se requieren permisos de administrador para cambiar permisos"
        print_status "Ejecutando: sudo chmod 777 logs data"
        sudo chmod 777 logs data || {
            print_error "❌ No se pudieron configurar permisos de escritura"
            print_warning "Ejecuta manualmente: sudo chmod 777 logs data"
            return 1
        }
    }
    
    # Verificar que los permisos se aplicaron correctamente
    if [ -w "logs" ] && [ -w "data" ]; then
        print_success "✅ Permisos de escritura configurados correctamente"
    else
        print_warning "⚠️ Verificar permisos manualmente: ls -la logs/ data/"
    fi
    
    print_success "✅ Configuración de permisos completada"
}

# Verificar y construir imagen
build_and_start() {
    print_header "🏗️ CONSTRUYENDO Y INICIANDO SERVICIOS MULTI-CPU"

    # Detectar arquitectura y configuración
    ARCH=$(uname -m)
    CPU_COUNT=$(nproc)
    
    # Determinar archivo de compose a usar
    COMPOSE_FILE="docker-compose.yml"

    # Determinar el archivo de configuración a modificar
    if [ -f "docker-compose.resolved.yml" ]; then
        COMPOSE_FILE="docker-compose.resolved.yml"
        print_success "$ARCH_EMOJI Usando configuración auto-resuelta para $ARCH_TYPE"
        print_status "⚙️ Workers: $OPTIMAL_WORKERS | CPU: $CPU_LIMIT | RAM: $MEMORY_LIMIT"
    else
        print_warning "⚠️ Usando configuración estándar (sin auto-detección)"
    fi
    
    print_status "🏗️ Construyendo imagen optimizada para $ARCH ($CPU_COUNT CPUs)..."
    
    # Construcción según arquitectura
    case "$ARCH_TYPE" in
        "riscv")
            print_status "🍊 RISC-V detectado - construcción con timeouts extendidos"
            $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" build --no-cache esp32-api || {
                print_warning "Build falló, intentando método alternativo..."
                docker build --tag esp32-solar-api:latest .
            }
            ;;
        "arm64"|"armv7")
            print_status "🍓 ARM detectado - construcción optimizada"
            $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" build esp32-api
            ;;
        "x86_64")
            print_status "🖥️ x86_64 detectado - construcción nativa"
            $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" build esp32-api
            ;;
        *)
            print_warning "❓ Arquitectura desconocida, usando método estándar"
            $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" build esp32-api
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_success "✅ Imagen construida exitosamente"
    else
        print_error "❌ Error construyendo imagen"
        return 1
    fi
    
    # Iniciar servicios
    print_status "🚀 Iniciando servicios con configuración multi-CPU..."
    
    # Configurar permisos de directorios antes de iniciar contenedores
    setup_directory_permissions
    
    $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up -d
    
    if [ $? -eq 0 ]; then
        print_success "✅ Servicios iniciados"
        
        # Mostrar configuración aplicada
        echo ""
        print_status "📊 Configuración aplicada:"
        print_status "   🏗️ Arquitectura: $ARCH_TYPE ($ARCH)"
        print_status "   👥 Workers: $OPTIMAL_WORKERS"
        print_status "   ⚡ CPU Limit: $CPU_LIMIT"
        print_status "   💾 Memory Limit: $MEMORY_LIMIT"
        print_status "   📁 Compose File: $COMPOSE_FILE"
        print_status "   🐳 Docker Compose: $DOCKER_COMPOSE_CMD"
    else
        print_error "❌ Error iniciando servicios"
        return 1
    fi
}

# Verificar que todo esté funcionando
verify_installation() {
    print_header "🔍 VERIFICANDO INSTALACIÓN"
    
    # Esperar a que el servicio esté listo
    print_status "Esperando a que la API esté lista..."
    
    RETRY_COUNT=0
    MAX_RETRIES=30
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "✅ API está respondiendo"
            break
        fi
        
        echo -n "."
        sleep 2
        ((RETRY_COUNT++))
    done
    
    echo ""
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_warning "⚠️ La API tardó más de lo esperado en responder"
        print_status "Verificando logs..."
        $DOCKER_COMPOSE_CMD logs --tail=20 esp32-api
        return 1
    fi
    
    # Mostrar estado
    print_status "Estado de contenedores:"
    $DOCKER_COMPOSE_CMD ps
    
    echo ""
    print_status "Estado de la API:"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
    
    echo ""
    print_status "URLs disponibles:"
    IP=$(hostname -I | awk '{print $1}')
    echo "  • API: http://$IP:8000"
    echo "  • Documentación: http://$IP:8000/docs"
    echo "  • Health: http://$IP:8000/health"
    echo "  • Monitoreo: http://$IP:9000 (Portainer)"
}

# Mostrar información final
show_final_info() {
    print_header "🎉 SETUP COMPLETADO"
    
    ARCH=$(uname -m)
    print_success "✅ ESP32 Solar Charger API está ejecutándose"
    
    if [[ "$ARCH" == "riscv64" ]]; then
        print_success "✅ Emulación x86_64 funcionando correctamente en RISC-V"
    elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        print_success "✅ Optimizado para ARM64 (Orange Pi/Raspberry Pi)"
    else
        print_success "✅ Ejecutándose en arquitectura $ARCH"
    fi
    
    print_success "✅ Puerto serial configurado: $ESP32_PORT"
    print_success "✅ Docker Compose: $DOCKER_COMPOSE_CMD"
    
    echo ""
    echo -e "${CYAN}📋 COMANDOS ÚTILES:${NC}"
    echo -e "${YELLOW}Ver logs:${NC}        $DOCKER_COMPOSE_CMD logs -f esp32-api"
    echo -e "${YELLOW}Reiniciar:${NC}       $DOCKER_COMPOSE_CMD restart esp32-api"
    echo -e "${YELLOW}Detener:${NC}         $DOCKER_COMPOSE_CMD down"
    echo -e "${YELLOW}Estado:${NC}          $DOCKER_COMPOSE_CMD ps"
    echo -e "${YELLOW}Configurar puerto:${NC} ./quick_setup.sh"
    
    echo ""
    echo -e "${CYAN}🌐 ACCESO REMOTO:${NC}"
    IP=$(hostname -I | awk '{print $1}')
    echo -e "${YELLOW}API:${NC}             http://$IP:8000"
    echo -e "${YELLOW}Documentación:${NC}   http://$IP:8000/docs"
    echo -e "${YELLOW}Health Check:${NC}    http://$IP:8000/health"
    
    echo ""
    echo -e "${CYAN}📱 EJEMPLO DE USO:${NC}"
    echo -e "${YELLOW}curl http://$IP:8000/data/${NC}"
    echo -e "${YELLOW}curl http://$IP:8000/health${NC}"
    echo -e "${YELLOW}curl http://$IP:8000/config${NC}"
    
    echo ""
    if [[ "$ARCH" == "riscv64" ]]; then
        print_warning "💡 TIP RISC-V: Si hay problemas de rendimiento, considera usar '$DOCKER_COMPOSE_CMD down && $DOCKER_COMPOSE_CMD up -d' para reiniciar"
    fi
    print_warning "💡 TIP: Guarda la IP $IP para acceso desde otros dispositivos"
}

# Función principal
main() {
    # Verificar si se solicitó ayuda de debugging
    if [ "$1" = "debug" ] || [ "$1" = "--debug" ] || [ "$1" = "help" ]; then
        # Detectar comando Docker Compose antes de mostrar ayuda
        detect_docker_compose_command
        show_docker_debugging_help
        exit 0
    fi
    
    print_header "ESP32 API - SETUP UNIVERSAL MULTI-ARQUITECTURA"
    
    echo -e "${CYAN}🚀 Este script detecta automáticamente tu hardware y optimiza:${NC}"
    echo -e "${PURPLE}• 🔍 Arquitectura del sistema (x86, ARM, RISC-V)${NC}"
    echo -e "${PURPLE}• ⚡ Número óptimo de workers según CPUs disponibles${NC}"
    echo -e "${PURPLE}• 💾 Límites de memoria según configuración${NC}"
    echo -e "${PURPLE}• 🔧 Timeouts específicos por arquitectura${NC}"
    echo -e "${PURPLE}• 📡 Puerto del ESP32 automáticamente${NC}"
    echo -e "${PURPLE}• 🐳 Docker Compose optimizado${NC}"
    echo ""
    echo -e "${YELLOW}💡 TIP: Ejecuta 'bash quick_setup.sh debug' para ver guía de debugging Docker${NC}"
    echo ""
    
    # Mostrar información de la plataforma
    ARCH=$(uname -m)
    OS_INFO=""
    if [ -f "/etc/os-release" ]; then
        OS_INFO=$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
    fi
    
    echo -e "${CYAN}🖥️  Plataforma detectada:${NC}"
    echo -e "${YELLOW}   Arquitectura: $ARCH${NC}"
    if [ -n "$OS_INFO" ]; then
        echo -e "${YELLOW}   Sistema: $OS_INFO${NC}"
    fi
    echo ""
    
    # Verificar que estemos en el directorio correcto
    if [ ! -f "docker-compose.yml" ] || [ ! -f "Dockerfile" ]; then
        print_error "Este script debe ejecutarse desde el directorio del proyecto"
        print_error "Asegúrate de tener docker-compose.yml y Dockerfile"
        exit 1
    fi
    
    read -p "¿Continuar con el setup automático? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Setup cancelado"
        exit 1
    fi
    
    # Detectar comando Docker Compose compatible PRIMERO
    detect_docker_compose_command
    
    # Detectar puerto ESP32
    ESP32_PORT=$(detect_esp32_port)
    if [ $? -ne 0 ] || [ -z "$ESP32_PORT" ]; then
        print_error "No se pudo detectar el puerto del ESP32"
        exit 1
    fi
    
    # Configurar proyecto
    configure_project "$ESP32_PORT"
    
    # Construir e iniciar
    build_and_start
    
    # Verificar instalación
    verify_installation
    
    # Mostrar información final
    show_final_info
    
    print_success "🚀 ¡Setup completado exitosamente!"
}

# Ejecutar si no es root
if [[ $EUID -eq 0 ]]; then
   print_error "No ejecutes este script como root"
   exit 1
fi

# Ejecutar función principal
main "$@"