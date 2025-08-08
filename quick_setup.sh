#!/bin/bash
# =============================================================================
# ESP32 API - Setup Rápido con Configuración Automática de Puerto
# =============================================================================

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

# Detectar puerto serial automáticamente
detect_esp32_port() {
    print_header "🔍 DETECCIÓN AUTOMÁTICA DE PUERTO ESP32"
    
    echo "Buscando puertos seriales disponibles..."
    echo ""
    
    # Listar puertos disponibles
    echo "📋 Puertos seriales encontrados:"
    SERIAL_PORTS=$(ls /dev/tty{S,USB,ACM}* 2>/dev/null || true)
    
    if [ -z "$SERIAL_PORTS" ]; then
        print_warning "No se encontraron puertos seriales"
        echo "Asegúrate de que:"
        echo "  • El ESP32 esté conectado"
        echo "  • El cable USB funcione correctamente"
        echo "  • Los drivers estén instalados"
        echo ""
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
    
    # Autodetección inteligente
    ESP32_PORT=""
    
    # Buscar por patrones conocidos de ESP32
    for PORT in $SERIAL_PORTS; do
        if [ -e "$PORT" ]; then
            # Verificar si es un dispositivo USB común para ESP32
            if [[ "$PORT" == *"ttyUSB"* ]] || [[ "$PORT" == *"ttyACM"* ]]; then
                if command -v udevadm &> /dev/null; then
                    # Buscar por vendor IDs comunes de ESP32
                    VENDOR_INFO=$(udevadm info --name="$PORT" 2>/dev/null | grep -i "ID_VENDOR_ID" || echo "")
                    
                    # IDs comunes: 10c4 (Silicon Labs), 1a86 (QinHeng), 0403 (FTDI)
                    if echo "$VENDOR_INFO" | grep -qE "(10c4|1a86|0403)"; then
                        ESP32_PORT="$PORT"
                        print_success "🎯 ESP32 detectado automáticamente en: $ESP32_PORT"
                        break
                    fi
                fi
                
                # Si no encontramos por vendor ID, usar el primer puerto USB
                if [ -z "$ESP32_PORT" ]; then
                    ESP32_PORT="$PORT"
                fi
            fi
        fi
    done
    
    # Si no se detectó automáticamente, usar ttyS5 por defecto o preguntar
    if [ -z "$ESP32_PORT" ]; then
        if [ -e "/dev/ttyS5" ]; then
            ESP32_PORT="/dev/ttyS5"
            print_status "Usando puerto por defecto: $ESP32_PORT"
        else
            echo "No se pudo detectar el ESP32 automáticamente."
            echo ""
            echo "Selecciona el puerto manualmente:"
            read -p "Número de puerto (1-$((COUNTER-1))) o ruta completa: " PORT_CHOICE
            
            if [[ "$PORT_CHOICE" =~ ^[0-9]+$ ]] && [ "$PORT_CHOICE" -ge 1 ] && [ "$PORT_CHOICE" -lt "$COUNTER" ]; then
                ESP32_PORT="${PORT_ARRAY[$PORT_CHOICE]}"
            elif [ -e "$PORT_CHOICE" ]; then
                ESP32_PORT="$PORT_CHOICE"
            else
                print_error "Puerto inválido: $PORT_CHOICE"
                return 1
            fi
        fi
    fi
    
    # Verificar permisos del puerto
    if [ ! -r "$ESP32_PORT" ] || [ ! -w "$ESP32_PORT" ]; then
        print_warning "Configurando permisos para $ESP32_PORT..."
        sudo chmod 666 "$ESP32_PORT" 2>/dev/null || true
        
        # Agregar al grupo dialout si no está
        if ! groups | grep -q dialout; then
            print_status "Agregando usuario al grupo dialout..."
            sudo usermod -aG dialout $USER
            print_warning "⚠️ Necesitarás reiniciar la sesión para aplicar permisos de grupo"
        fi
    fi
    
    print_success "✅ Puerto ESP32 configurado: $ESP32_PORT"
    echo "$ESP32_PORT"
}

# Configurar archivos del proyecto
configure_project() {
    local ESP32_PORT="$1"
    
    print_header "⚙️ CONFIGURANDO PROYECTO"
    
    print_status "Configurando docker-compose.yml..."
    
    # Actualizar docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        # Backup
        cp docker-compose.yml docker-compose.yml.backup
        
        # Reemplazar puerto en devices (línea con formato "- "/dev/ttyXXX:/dev/ttyXXX")
        if sed -i "s#\"/dev/tty[^\"]*:/dev/tty[^\"]*\"#\"${ESP32_PORT}:${ESP32_PORT}\"#g" docker-compose.yml; then
            print_success "✅ Dispositivos actualizados en docker-compose.yml"
        else
            print_warning "⚠️ No se pudo actualizar dispositivos en docker-compose.yml"
        fi
        
        # Reemplazar puerto en environment (línea con formato SERIAL_PORT=/dev/ttyXXX)
        if sed -i "s#SERIAL_PORT=/dev/tty[^[:space:]]*#SERIAL_PORT=${ESP32_PORT}#g" docker-compose.yml; then
            print_success "✅ Variables de entorno actualizadas en docker-compose.yml"
        else
            print_warning "⚠️ No se pudo actualizar variables de entorno en docker-compose.yml"
        fi
        
        # Verificar que los cambios se aplicaron
        if grep -q "${ESP32_PORT}" docker-compose.yml; then
            print_success "✅ docker-compose.yml configurado correctamente con ${ESP32_PORT}"
        else
            print_warning "⚠️ docker-compose.yml puede no estar configurado correctamente"
        fi
    else
        print_error "❌ No se encontró docker-compose.yml"
        return 1
    fi
    
    # Actualizar .env.docker (crear si no existe)
    if [ -f ".env.docker" ]; then
        cp .env.docker .env.docker.backup
        sed -i "s#SERIAL_PORT=.*#SERIAL_PORT=${ESP32_PORT}#g" .env.docker
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
        if [ -f ".env.docker" ]; then
            cp .env.docker .env
        else
            echo "SERIAL_PORT=${ESP32_PORT}" > .env
        fi
        print_success "✅ .env creado"
    fi
}

# Verificar y construir imagen
build_and_start() {
    print_header "🏗️ CONSTRUYENDO Y INICIANDO SERVICIOS"
    
    # Verificar que Docker esté funcionando
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker no está funcionando. Ejecuta: sudo systemctl start docker"
        return 1
    fi
    
    # Verificar buildx
    if ! docker buildx ls | grep -q "esp32-builder"; then
        print_status "Configurando Docker buildx para emulación..."
        docker buildx create --name esp32-builder --driver docker-container --use || true
        docker buildx inspect --bootstrap || true
    fi
    
    # Construir imagen
    print_status "Construyendo imagen Docker (esto puede tomar varios minutos)..."
    
    if [ -f "scripts/build.sh" ]; then
        chmod +x scripts/build.sh
        ./scripts/build.sh
    else
        # Build directo
        docker buildx build --platform linux/amd64 --tag esp32-solar-api:emulated-x86_64 --load .
    fi
    
    print_success "✅ Imagen construida"
    
    # Iniciar servicios
    print_status "Iniciando servicios Docker..."
    docker-compose up -d
    
    print_success "✅ Servicios iniciados"
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
        docker-compose logs --tail=20 esp32-api
        return 1
    fi
    
    # Mostrar estado
    print_status "Estado de contenedores:"
    docker-compose ps
    
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
    
    print_success "✅ ESP32 Solar Charger API está ejecutándose"
    print_success "✅ Emulación x86_64 funcionando en RISC-V"
    print_success "✅ Puerto serial configurado: $ESP32_PORT"
    
    echo ""
    echo -e "${CYAN}📋 COMANDOS ÚTILES:${NC}"
    echo -e "${YELLOW}Ver logs:${NC}        docker-compose logs -f esp32-api"
    echo -e "${YELLOW}Reiniciar:${NC}       docker-compose restart esp32-api"
    echo -e "${YELLOW}Detener:${NC}         docker-compose down"
    echo -e "${YELLOW}Monitor:${NC}         ./scripts/monitor.sh"
    echo -e "${YELLOW}Cambiar puerto:${NC}  ./scripts/change_serial_port.sh /dev/ttyUSB0"
    
    echo ""
    echo -e "${CYAN}🌐 ACCESO REMOTO:${NC}"
    IP=$(hostname -I | awk '{print $1}')
    echo -e "${YELLOW}API:${NC}             http://$IP:8000"
    echo -e "${YELLOW}Documentación:${NC}   http://$IP:8000/docs"
    echo -e "${YELLOW}Monitoreo:${NC}       http://$IP:9000"
    
    echo ""
    echo -e "${CYAN}📱 EJEMPLO DE USO:${NC}"
    echo -e "${YELLOW}curl http://$IP:8000/data/${NC}"
    echo -e "${YELLOW}curl http://$IP:8000/health${NC}"
    
    echo ""
    print_warning "💡 TIP: Guarda la IP $IP para acceso desde otros dispositivos"
}

# Función principal
main() {
    print_header "ESP32 API - SETUP RÁPIDO PARA ORANGE PI R2S"
    
    echo -e "${CYAN}Este script hará automáticamente:${NC}"
    echo -e "${CYAN}• Detectar el puerto del ESP32${NC}"
    echo -e "${CYAN}• Configurar archivos Docker${NC}"
    echo -e "${CYAN}• Construir imagen con emulación x86_64${NC}"
    echo -e "${CYAN}• Iniciar todos los servicios${NC}"
    echo -e "${CYAN}• Verificar que todo funcione${NC}"
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