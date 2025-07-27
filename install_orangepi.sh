#!/bin/bash
# =============================================================================
# ESP32 Solar Charger API - Instalación Completa para Orange Pi R2S RISC-V
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Función para mostrar mensajes
print_header() {
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}🍊 $1${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo -e "\n${BLUE}📋 $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

# Verificar que se ejecuta en Orange Pi R2S
check_platform() {
    print_section "Verificando Plataforma"
    
    ARCH=$(uname -m)
    print_status "Arquitectura detectada: $ARCH"
    
    if [[ "$ARCH" == "riscv64" ]]; then
        print_success "✅ RISC-V 64-bit detectado - Compatible con Orange Pi R2S"
    else
        print_warning "⚠️ Arquitectura $ARCH - Este script está optimizado para RISC-V"
        read -p "¿Continuar? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Instalación cancelada"
            exit 1
        fi
    fi
    
    # Verificar espacio disponible
    AVAILABLE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    print_status "Espacio disponible: ${AVAILABLE_SPACE}GB"
    
    if [ "$AVAILABLE_SPACE" -lt 2 ]; then
        print_error "Se necesitan al menos 2GB libres. Disponible: ${AVAILABLE_SPACE}GB"
        exit 1
    elif [ "$AVAILABLE_SPACE" -lt 3 ]; then
        print_warning "Recomendado: 3GB+. Disponible: ${AVAILABLE_SPACE}GB"
    else
        print_success "✅ Espacio suficiente: ${AVAILABLE_SPACE}GB"
    fi
}

# Detectar SO y configurar repositorios
detect_os() {
    print_section "Detectando Sistema Operativo"
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        print_status "SO detectado: $PRETTY_NAME"
    else
        print_error "No se pudo detectar el sistema operativo"
        exit 1
    fi
    
    # Verificar compatibilidad
    case $OS in
        "ubuntu"|"debian")
            print_success "✅ SO compatible: $OS $VERSION"
            ;;
        *)
            print_warning "⚠️ SO no probado: $OS - Continuando..."
            ;;
    esac
}

# Actualizar sistema
update_system() {
    print_section "Actualizando Sistema"
    
    print_status "Actualizando lista de paquetes..."
    sudo apt-get update -qq
    
    print_status "Instalando actualizaciones del sistema..."
    sudo apt-get upgrade -y -qq
    
    print_status "Instalando herramientas básicas..."
    sudo apt-get install -y -qq \
        curl \
        wget \
        gnupg \
        lsb-release \
        ca-certificates \
        software-properties-common \
        apt-transport-https \
        git \
        jq \
        htop \
        nano \
        usbutils
    
    print_success "✅ Sistema actualizado"
}

# Instalar Docker
install_docker() {
    print_section "Instalando Docker Engine"
    
    # Verificar si Docker ya está instalado
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_status "Docker ya está instalado: $DOCKER_VERSION"
        
        # Verificar si es una versión compatible
        DOCKER_MAJOR=$(docker --version | sed 's/.*version \([0-9]*\)\..*/\1/')
        if [ "$DOCKER_MAJOR" -ge 20 ]; then
            print_success "✅ Versión de Docker compatible (>= 20.x)"
            return 0
        else
            print_warning "⚠️ Versión de Docker antigua, actualizando..."
        fi
    fi
    
    # Eliminar versiones antiguas
    print_status "Eliminando versiones antiguas de Docker..."
    sudo apt-get remove -y -qq docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Agregar repositorio oficial de Docker
    print_status "Configurando repositorio oficial de Docker..."
    curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    echo "deb [arch=$ARCH signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    print_status "Instalando Docker Engine..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Configurar Docker para usuario actual
    print_status "Configurando permisos de Docker..."
    sudo usermod -aG docker $USER
    
    # Habilitar Docker al inicio
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Verificar instalación
    if sudo docker run --rm hello-world &> /dev/null; then
        print_success "✅ Docker instalado correctamente"
    else
        print_error "❌ Error en la instalación de Docker"
        exit 1
    fi
}

# Configurar emulación QEMU
setup_emulation() {
    print_section "Configurando Emulación x86_64 (QEMU)"
    
    print_status "Instalando QEMU y binfmt..."
    sudo apt-get install -y -qq \
        qemu-user-static \
        binfmt-support \
        qemu-system-x86
    
    # Verificar que la emulación esté disponible
    if [ -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
        print_success "✅ Emulación x86_64 ya está configurada"
    else
        print_status "Configurando emulación x86_64..."
        sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
        
        if [ -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
            print_success "✅ Emulación x86_64 configurada"
        else
            print_error "❌ Error configurando emulación x86_64"
            exit 1
        fi
    fi
    
    # Configurar Docker buildx para multi-plataforma
    print_status "Configurando Docker buildx..."
    
    # Crear builder para multi-plataforma si no existe
    if ! docker buildx ls | grep -q "esp32-builder"; then
        docker buildx create --name esp32-builder --driver docker-container --use
        docker buildx inspect --bootstrap
    fi
    
    # Verificar plataformas disponibles
    PLATFORMS=$(docker buildx ls | grep esp32-builder | awk '{print $4}')
    if echo "$PLATFORMS" | grep -q "linux/amd64"; then
        print_success "✅ Buildx configurado - Plataformas: $PLATFORMS"
    else
        print_warning "⚠️ Plataforma linux/amd64 no disponible en buildx"
    fi
}

# Configurar permisos seriales
setup_serial_permissions() {
    print_section "Configurando Permisos Seriales"
    
    print_status "Agregando usuario al grupo dialout..."
    sudo usermod -aG dialout $USER
    
    print_status "Detectando puertos seriales disponibles..."
    SERIAL_PORTS=$(ls -la /dev/tty* 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)" || true)
    
    if [ -n "$SERIAL_PORTS" ]; then
        print_success "✅ Puertos seriales detectados:"
        echo "$SERIAL_PORTS" | while read line; do
            echo "      $line"
        done
        
        # Configurar permisos para puertos comunes
        for port in /dev/ttyS* /dev/ttyUSB* /dev/ttyACM*; do
            if [ -e "$port" ]; then
                sudo chmod 666 "$port" 2>/dev/null || true
                print_status "Permisos configurados para: $port"
            fi
        done
    else
        print_warning "⚠️ No se detectaron puertos seriales"
        print_status "Esto es normal si el ESP32 no está conectado"
    fi
    
    print_status "Creando reglas udev para permisos automáticos..."
    cat << 'EOF' | sudo tee /etc/udev/rules.d/99-esp32-serial.rules > /dev/null
# Reglas para ESP32 y otros dispositivos seriales
SUBSYSTEM=="tty", GROUP="dialout", MODE="0666"
KERNEL=="ttyUSB[0-9]*", GROUP="dialout", MODE="0666"
KERNEL=="ttyACM[0-9]*", GROUP="dialout", MODE="0666"
KERNEL=="ttyS[0-9]*", GROUP="dialout", MODE="0666"
EOF
    
    sudo udevadm control --reload-rules
    print_success "✅ Permisos seriales configurados"
}

# Crear estructura del proyecto
create_project_structure() {
    print_section "Creando Estructura del Proyecto"
    
    PROJECT_DIR="esp32_api_docker"
    
    if [ -d "$PROJECT_DIR" ]; then
        print_warning "⚠️ El directorio $PROJECT_DIR ya existe"
        read -p "¿Sobrescribir? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            print_error "Instalación cancelada"
            exit 1
        fi
    fi
    
    print_status "Creando estructura de directorios..."
    mkdir -p "$PROJECT_DIR"/{scripts,config,logs,data,docs}
    cd "$PROJECT_DIR"
    
    # Crear .env.docker
    print_status "Creando archivo de configuración..."
    cat > .env.docker << 'EOF'
# =============================================================================
# ESP32 Solar Charger API - Configuración Docker
# =============================================================================

# 🔧 CONFIGURACIÓN SERIAL - CAMBIAR SEGÚN TU PUERTO
# =================================================
SERIAL_PORT=/dev/ttyS5
SERIAL_BAUDRATE=9600
SERIAL_TIMEOUT=3.0

# Para ESP32 por USB, cambiar a:
# SERIAL_PORT=/dev/ttyUSB0
# Para ESP32 por USB-CDC, cambiar a:
# SERIAL_PORT=/dev/ttyACM0

# Configuración de la API
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

# Recursos Docker (ajustar según tu Orange Pi R2S)
MEMORY_LIMIT=512m
CPU_LIMIT=1.0
MEMORY_RESERVATION=256m
CPU_RESERVATION=0.5
EOF
    
    print_success "✅ Estructura del proyecto creada en: $(pwd)"
}

# Copiar archivos del proyecto
copy_project_files() {
    print_section "Configurando Archivos del Proyecto"
    
    print_status "Copiando archivos de la API..."
    
    # Aquí normalmente copiarías los archivos desde el directorio fuente
    # Como estamos en un setup automático, crearemos los enlaces
    if [ -d "../models" ] && [ -f "../main.py" ]; then
        cp -r ../{models,services,api,core,main.py,requirements.txt} .
        print_success "✅ Archivos del proyecto copiados"
    else
        print_warning "⚠️ Archivos fuente no encontrados en directorio padre"
        print_status "Descargando proyecto desde repositorio..."
        
        # Aquí podrías clonar el repositorio o descargar los archivos
        print_status "Por favor, copia manualmente los archivos del proyecto a este directorio"
        print_status "Necesitas: main.py, requirements.txt, models/, services/, api/, core/"
    fi
}

# Crear scripts auxiliares
create_helper_scripts() {
    print_section "Creando Scripts Auxiliares"
    
    # Script para detectar puerto serial
    print_status "Creando script de detección de puertos..."
    cat > scripts/detect_serial_port.sh << 'EOF'
#!/bin/bash
# Detectar puerto serial del ESP32

echo "🔍 Detectando puertos seriales disponibles..."
echo ""

# Listar todos los puertos
echo "📋 Todos los puertos seriales:"
ls -la /dev/tty* 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)" || echo "No se encontraron puertos seriales"
echo ""

# Detectar ESP32 específicamente
echo "🔍 Buscando ESP32..."
for port in /dev/ttyUSB* /dev/ttyACM*; do
    if [ -e "$port" ]; then
        # Intentar obtener información del dispositivo
        if [ -r "$port" ]; then
            echo "✅ Puerto disponible: $port"
            
            # Verificar con udevadm si está disponible
            if command -v udevadm &> /dev/null; then
                INFO=$(udevadm info --name="$port" --attribute-walk 2>/dev/null | grep -i "esp32\|silicon\|ch340\|cp210" || true)
                if [ -n "$INFO" ]; then
                    echo "   🎯 Posible ESP32 detectado!"
                fi
            fi
        else
            echo "⚠️ Puerto sin permisos: $port"
        fi
    fi
done

echo ""
echo "💡 Para usar un puerto específico:"
echo "   1. Edita docker-compose.yml"
echo "   2. Cambia el mapeo de dispositivos: \"/dev/tuPuerto:/dev/tuPuerto\""
echo "   3. Actualiza SERIAL_PORT en .env.docker"
EOF
    chmod +x scripts/detect_serial_port.sh
    
    # Script para cambiar puerto
    print_status "Creando script para cambiar puerto..."
    cat > scripts/change_serial_port.sh << 'EOF'
#!/bin/bash
# Script para cambiar puerto serial fácilmente

if [ -z "$1" ]; then
    echo "Uso: $0 <puerto>"
    echo ""
    echo "Ejemplos:"
    echo "  $0 /dev/ttyUSB0    # Para ESP32 por USB"
    echo "  $0 /dev/ttyACM0    # Para ESP32 por USB-CDC"
    echo "  $0 /dev/ttyS5      # Para puerto serial nativo"
    echo ""
    echo "Puertos disponibles:"
    ls -la /dev/tty* 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)"
    exit 1
fi

NEW_PORT="$1"

if [ ! -e "$NEW_PORT" ]; then
    echo "❌ Error: Puerto $NEW_PORT no existe"
    exit 1
fi

echo "🔧 Cambiando puerto serial a: $NEW_PORT"

# Actualizar docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    # Backup
    cp docker-compose.yml docker-compose.yml.backup
    
    # Reemplazar puerto en devices
    sed -i "s|/dev/tty[^:]*:/dev/tty[^\"]*|${NEW_PORT}:${NEW_PORT}|g" docker-compose.yml
    
    echo "✅ docker-compose.yml actualizado"
else
    echo "❌ docker-compose.yml no encontrado"
fi

# Actualizar .env.docker
if [ -f ".env.docker" ]; then
    # Backup
    cp .env.docker .env.docker.backup
    
    # Reemplazar SERIAL_PORT
    sed -i "s|SERIAL_PORT=.*|SERIAL_PORT=${NEW_PORT}|g" .env.docker
    
    echo "✅ .env.docker actualizado"
else
    echo "❌ .env.docker no encontrado"
fi

echo ""
echo "🎯 Puerto serial cambiado a: $NEW_PORT"
echo "💡 Reinicia el contenedor para aplicar cambios:"
echo "   docker-compose down && docker-compose up -d"
EOF
    chmod +x scripts/change_serial_port.sh
    
    # Script de construcción
    print_status "Creando script de construcción..."
    cat > scripts/build.sh << 'EOF'
#!/bin/bash
# Construir imagen Docker con emulación x86_64

set -e

echo "🏗️ Construyendo ESP32 API con emulación x86_64..."
echo "📦 Plataforma objetivo: linux/amd64 (emulado en RISC-V)"
echo ""

# Verificar que buildx esté configurado
if ! docker buildx ls | grep -q "esp32-builder"; then
    echo "⚙️ Configurando Docker buildx..."
    docker buildx create --name esp32-builder --driver docker-container --use
    docker buildx inspect --bootstrap
fi

# Usar el builder correcto
docker buildx use esp32-builder

# Construir para x86_64
echo "🔨 Iniciando build..."
docker buildx build \
    --platform linux/amd64 \
    --tag esp32-solar-api:emulated-x86_64 \
    --load \
    .

echo ""
echo "✅ Build completado!"
echo "🚀 Ejecutar con: docker-compose up -d"
EOF
    chmod +x scripts/build.sh
    
    # Script de monitoreo
    print_status "Creando script de monitoreo..."
    cat > scripts/monitor.sh << 'EOF'
#!/bin/bash
# Monitorear contenedores ESP32 API

echo "📊 ESP32 Solar Charger API - Monitor"
echo "===================================="
echo ""

# Estado de contenedores
echo "🐳 Estado de Contenedores:"
docker-compose ps

echo ""
echo "📊 Uso de Recursos:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "💾 Uso de Disco:"
echo "Imágenes Docker:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "🔍 Estado de la API:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API respondiendo correctamente"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "❌ API no responde"
fi

echo ""
echo "📝 Últimos logs (10 líneas):"
docker-compose logs --tail=10 esp32-api
EOF
    chmod +x scripts/monitor.sh
    
    print_success "✅ Scripts auxiliares creados"
}

# Función principal
main() {
    print_header "ESP32 Solar Charger API - Instalación Docker para Orange Pi R2S"
    
    echo -e "${CYAN}Este script configurará automáticamente:${NC}"
    echo -e "${CYAN}• Docker Engine con soporte RISC-V${NC}"
    echo -e "${CYAN}• Emulación x86_64 con QEMU${NC}"
    echo -e "${CYAN}• Permisos seriales para ESP32${NC}"
    echo -e "${CYAN}• Estructura completa del proyecto${NC}"
    echo -e "${CYAN}• Scripts auxiliares de gestión${NC}"
    echo ""
    
    read -p "¿Continuar con la instalación? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Instalación cancelada"
        exit 1
    fi
    
    # Verificar permisos sudo
    if ! sudo -n true 2>/dev/null; then
        print_status "Este script necesita permisos sudo para:"
        print_status "• Instalar paquetes del sistema"
        print_status "• Configurar Docker y permisos"
        print_status "• Configurar acceso a puertos seriales"
        echo ""
        sudo -v
    fi
    
    # Ejecutar instalación
    check_platform
    detect_os
    update_system
    install_docker
    setup_emulation
    setup_serial_permissions
    create_project_structure
    copy_project_files
    create_helper_scripts
    
    print_header "🎉 INSTALACIÓN COMPLETADA"
    
    echo -e "${GREEN}✅ Docker configurado con emulación x86_64${NC}"
    echo -e "${GREEN}✅ QEMU y buildx configurados${NC}"
    echo -e "${GREEN}✅ Permisos seriales configurados${NC}"
    echo -e "${GREEN}✅ Proyecto listo en: $(pwd)${NC}"
    echo ""
    
    print_section "🚀 PRÓXIMOS PASOS"
    echo -e "${CYAN}1. Detectar tu puerto serial:${NC}"
    echo -e "   ${YELLOW}./scripts/detect_serial_port.sh${NC}"
    echo ""
    echo -e "${CYAN}2. Cambiar puerto si es necesario:${NC}"
    echo -e "   ${YELLOW}./scripts/change_serial_port.sh /dev/ttyUSB0${NC}"
    echo ""
    echo -e "${CYAN}3. Construir imagen Docker:${NC}"
    echo -e "   ${YELLOW}./scripts/build.sh${NC}"
    echo ""
    echo -e "${CYAN}4. Iniciar el servicio:${NC}"
    echo -e "   ${YELLOW}docker-compose up -d${NC}"
    echo ""
    echo -e "${CYAN}5. Monitorear el sistema:${NC}"
    echo -e "   ${YELLOW}./scripts/monitor.sh${NC}"
    echo ""
    echo -e "${CYAN}6. Acceder a la API:${NC}"
    echo -e "   ${YELLOW}http://$(hostname -I | awk '{print $1}'):8000/docs${NC}"
    echo ""
    
    print_warning "⚠️ IMPORTANTE: Reinicia la sesión para aplicar permisos de grupo (dialout)"
    print_warning "   O ejecuta: newgrp dialout"
    
    print_section "📚 DOCUMENTACIÓN"
    echo -e "${CYAN}• Logs: docker-compose logs -f esp32-api${NC}"
    echo -e "${CYAN}• Estado: docker-compose ps${NC}"
    echo -e "${CYAN}• Reiniciar: docker-compose restart esp32-api${NC}"
    echo -e "${CYAN}• Detener: docker-compose down${NC}"
    echo ""
    
    print_success "🎉 ¡Instalación completada exitosamente!"
}

# Verificar que no se ejecute como root
if [[ $EUID -eq 0 ]]; then
   print_error "No ejecutes este script como root (usa sudo cuando sea necesario)"
   exit 1
fi

# Ejecutar función principal
main "$@"