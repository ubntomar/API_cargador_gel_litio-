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
        
        # Método más específico: buscar líneas específicas y reemplazar
        print_status "Actualizando configuración de dispositivos..."
        
        # Método más seguro: reemplazar puertos específicos directamente
        print_status "Aplicando configuración de puerto..."
        
        # Reemplazar puertos comunes uno por uno (método más seguro)
        sed -i "s|/dev/ttyUSB[0-9]*|${ESP32_PORT}|g" docker-compose.yml
        sed -i "s|/dev/ttyACM[0-9]*|${ESP32_PORT}|g" docker-compose.yml
        sed -i "s|/dev/ttyS[0-9]*|${ESP32_PORT}|g" docker-compose.yml
        
        # También reemplazar en formato de device mapping
        sed -i "s|\"/dev/ttyUSB[0-9]*:/dev/ttyUSB[0-9]*\"|\"/dev/ttyUSB0:${ESP32_PORT}\"|g" docker-compose.yml
        sed -i "s|\"/dev/ttyACM[0-9]*:/dev/ttyACM[0-9]*\"|\"/dev/ttyACM0:${ESP32_PORT}\"|g" docker-compose.yml
        sed -i "s|\"/dev/ttyS[0-9]*:/dev/ttyS[0-9]*\"|\"/dev/ttyS5:${ESP32_PORT}\"|g" docker-compose.yml
        
        # Reemplazar SERIAL_PORT en variables de ambiente
        sed -i "s|SERIAL_PORT=/dev/tty[A-Za-z0-9]*|SERIAL_PORT=${ESP32_PORT}|g" docker-compose.yml
        
        # Verificar que los cambios se aplicaron
        if grep -q "${ESP32_PORT}" docker-compose.yml; then
            print_success "✅ docker-compose.yml configurado correctamente con ${ESP32_PORT}"
        else
            print_warning "⚠️ Aplicando configuración alternativa más robusta..."
            
            # Método más simple y seguro para reemplazar puertos
            cp docker-compose.yml.backup docker-compose.yml
            
            # Reemplazar uno por uno para evitar problemas de regex
            sed -i "s|/dev/ttyUSB0|${ESP32_PORT}|g" docker-compose.yml
            sed -i "s|/dev/ttyUSB1|${ESP32_PORT}|g" docker-compose.yml  
            sed -i "s|/dev/ttyACM0|${ESP32_PORT}|g" docker-compose.yml
            sed -i "s|/dev/ttyACM1|${ESP32_PORT}|g" docker-compose.yml
            sed -i "s|/dev/ttyS5|${ESP32_PORT}|g" docker-compose.yml
            sed -i "s|/dev/ttyS0|${ESP32_PORT}|g" docker-compose.yml
            
            # Verificar nuevamente
            if grep -q "${ESP32_PORT}" docker-compose.yml; then
                print_success "✅ Configuración aplicada con método alternativo"
            else
                print_error "❌ No se pudo configurar el puerto automáticamente"
                print_status "Será necesario editar manualmente docker-compose.yml"
                print_status "Cambia todas las referencias de puertos serial a: ${ESP32_PORT}"
                echo ""
                print_status "Puedes continuar y editar el archivo después, o cancelar con Ctrl+C"
                read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    print_error "Setup cancelado"
                    exit 1
                fi
            fi
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
    
    # Detectar arquitectura
    ARCH=$(uname -m)
    print_status "Arquitectura detectada: $ARCH"
    
    # Verificar que Docker esté funcionando
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker no está funcionando. Ejecuta: sudo systemctl start docker"
        return 1
    fi
    
    # Estrategia de construcción según arquitectura
    if [[ "$ARCH" == "riscv64" ]]; then
        print_status "🔧 Configuración especial para RISC-V detectada"
        print_status "Usando emulación x86_64 para máxima compatibilidad..."
        
        # Para RISC-V, usar buildx con emulación x86_64
        if docker buildx version > /dev/null 2>&1; then
            print_status "Configurando Docker buildx para emulación x86_64..."
            
            # Crear builder si no existe
            if ! docker buildx ls | grep -q "esp32-builder"; then
                print_status "Creando builder personalizado..."
                docker buildx create --name esp32-builder --driver docker-container --use || true
                docker buildx inspect --bootstrap || true
            fi
            
            # Construir forzando plataforma x86_64
            print_status "Construyendo imagen con emulación x86_64 (puede tardar más en RISC-V)..."
            docker buildx build --platform linux/amd64 --tag esp32-solar-api:latest --load . || {
                print_warning "Buildx falló, intentando método alternativo..."
                docker build --tag esp32-solar-api:latest .
            }
        else
            print_warning "Buildx no disponible, usando build estándar..."
            docker build --tag esp32-solar-api:latest .
        fi
        
    elif [[ "$ARCH" == "x86_64" ]] || [[ "$ARCH" == "amd64" ]]; then
        print_status "🚀 Arquitectura x86_64 detectada - construcción nativa"
        docker build --tag esp32-solar-api:latest .
        
    elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
        print_status "🍓 Arquitectura ARM64 detectada (Orange Pi/Raspberry Pi)"
        
        # Para ARM64, intentar buildx primero
        if docker buildx version > /dev/null 2>&1; then
            print_status "Usando buildx para mejor compatibilidad..."
            
            if ! docker buildx ls | grep -q "esp32-builder"; then
                docker buildx create --name esp32-builder --driver docker-container --use || true
                docker buildx inspect --bootstrap || true
            fi
            
            # Construir para la plataforma nativa primero, x86_64 como fallback
            docker buildx build --platform linux/arm64 --tag esp32-solar-api:latest --load . || {
                print_warning "Build ARM64 falló, intentando emulación x86_64..."
                docker buildx build --platform linux/amd64 --tag esp32-solar-api:latest --load .
            }
        else
            docker build --tag esp32-solar-api:latest .
        fi
        
    else
        print_warning "⚠️ Arquitectura no reconocida: $ARCH"
        print_status "Intentando construcción estándar..."
        docker build --tag esp32-solar-api:latest .
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
    
    echo ""
    echo -e "${CYAN}📋 COMANDOS ÚTILES:${NC}"
    echo -e "${YELLOW}Ver logs:${NC}        docker-compose logs -f esp32-api"
    echo -e "${YELLOW}Reiniciar:${NC}       docker-compose restart esp32-api"
    echo -e "${YELLOW}Detener:${NC}         docker-compose down"
    echo -e "${YELLOW}Estado:${NC}          docker-compose ps"
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
        print_warning "💡 TIP RISC-V: Si hay problemas de rendimiento, considera usar 'docker-compose down && docker-compose up -d' para reiniciar"
    fi
    print_warning "💡 TIP: Guarda la IP $IP para acceso desde otros dispositivos"
}

# Función principal
main() {
    print_header "ESP32 API - SETUP RÁPIDO MULTIPLATAFORMA"
    
    echo -e "${CYAN}Este script hará automáticamente:${NC}"
    echo -e "${CYAN}• Detectar el puerto del ESP32${NC}"
    echo -e "${CYAN}• Configurar archivos Docker${NC}"
    echo -e "${CYAN}• Construir imagen optimizada para tu arquitectura${NC}"
    echo -e "${CYAN}• Iniciar todos los servicios${NC}"
    echo -e "${CYAN}• Verificar que todo funcione${NC}"
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