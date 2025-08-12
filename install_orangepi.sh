#!/bin/bash
# =============================================================================
# ESP32 Solar Charger API - Instalación Universal Multi-Arquitectura
# Optimizado para Orange Pi R2S RISC-V, ARM y x86_64 con auto-detección
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

print_header() {
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}�️ $1${NC}"
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

# Detección universal de arquitectura y CPU 
detect_cpu_configuration() {
    print_section "Detectando Configuración de CPU y Arquitectura"
    
    ARCH=$(uname -m)
    CPU_COUNT=$(nproc)
    TOTAL_MEMORY_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_MEMORY_GB=$((TOTAL_MEMORY_KB / 1024 / 1024))
    
    print_status "Arquitectura detectada: $ARCH"
    print_status "CPUs disponibles: $CPU_COUNT"
    print_status "Memoria total: ${TOTAL_MEMORY_GB}GB"
    
    # Configuración automática basada en recursos disponibles
    if [ "$CPU_COUNT" -ge 8 ]; then
        OPTIMAL_WORKERS=6
        print_status "CPU alta gama detectada (${CPU_COUNT} cores) → ${OPTIMAL_WORKERS} workers"
    elif [ "$CPU_COUNT" -ge 4 ]; then
        OPTIMAL_WORKERS=3
        print_status "CPU media detectada (${CPU_COUNT} cores) → ${OPTIMAL_WORKERS} workers"
    else
        OPTIMAL_WORKERS=2
        print_status "CPU básica detectada (${CPU_COUNT} cores) → ${OPTIMAL_WORKERS} workers"
    fi
    
    # Validación específica por arquitectura
    case "$ARCH" in
        "riscv64")
            print_success "✅ RISC-V 64-bit detectado - Perfecto para Orange Pi R2S"
            ARCHITECTURE_TYPE="RISC-V"
            ;;
        "aarch64"|"arm64")
            print_success "✅ ARM 64-bit detectado - Compatible con múltiples SBCs"
            ARCHITECTURE_TYPE="ARM64"
            ;;
        "x86_64"|"amd64")
            print_success "✅ x86_64 detectado - Compatible con PC/Servidores"
            ARCHITECTURE_TYPE="x86_64"
            ;;
        *)
            print_warning "⚠️ Arquitectura $ARCH no completamente probada"
            ARCHITECTURE_TYPE="OTHER"
            ;;
    esac
    
    # Verificar espacio disponible
    AVAILABLE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    print_status "Espacio disponible: ${AVAILABLE_SPACE}GB"
    
    if [ "$AVAILABLE_SPACE" -lt 2 ]; then
        print_error "Se necesitan al menos 2GB libres. Disponible: ${AVAILABLE_SPACE}GB"
        exit 1
    else
        print_success "✅ Espacio suficiente: ${AVAILABLE_SPACE}GB"
    fi
    
    # Exportar variables globales
    export OPTIMAL_WORKERS
    export ARCHITECTURE_TYPE
    export CPU_COUNT
    export TOTAL_MEMORY_GB
}

# Detectar distribución específica - ahora universal
detect_os() {
    print_section "Detectando Sistema Operativo - Soporte Universal"
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
        CODENAME=$VERSION_CODENAME
        print_status "SO detectado: $PRETTY_NAME"
        print_status "Codename: $CODENAME"
        print_status "Versión: $VERSION"
    else
        print_error "No se pudo detectar el sistema operativo"
        exit 1
    fi
    
    # Verificar compatibilidad universal
    case $OS in
        "ubuntu")
            if [[ "$VERSION" < "20.04" ]]; then
                print_warning "⚠️ Ubuntu $VERSION - Recomendado 20.04+ para mejor compatibilidad"
            else
                print_success "✅ Ubuntu $VERSION compatible con $ARCHITECTURE_TYPE"
            fi
            ;;
        "debian")
            if [[ "$VERSION" < "10" ]]; then
                print_warning "⚠️ Debian $VERSION - Recomendado 10+ para compatibilidad"
            else
                print_success "✅ Debian $VERSION compatible con $ARCHITECTURE_TYPE"
            fi
            ;;
        "fedora"|"centos"|"rhel")
            print_success "✅ Sistema Red Hat compatible con $ARCHITECTURE_TYPE"
            ;;
        "arch"|"manjaro")
            print_success "✅ Sistema Arch compatible con $ARCHITECTURE_TYPE"
            ;;
        *)
            print_warning "⚠️ SO no probado: $OS - Intentando instalación genérica para $ARCHITECTURE_TYPE..."
            ;;
    esac
}

# Actualizar sistema
update_system() {
    print_section "Actualizando Sistema"
    
    print_status "Actualizando lista de paquetes..."
    sudo apt-get update -qq
    
    print_status "Instalando actualizaciones críticas..."
    sudo apt-get upgrade -y -qq
    
    print_status "Instalando herramientas esenciales..."
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
        usbutils \
        build-essential \
        python3-pip
    
    print_success "✅ Sistema actualizado"
}

# Instalación universal de Docker con soporte multi-arquitectura
install_docker_universal() {
    print_section "Instalando Docker - Soporte Universal Multi-Arquitectura"
    
    # Verificar si Docker ya está instalado
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_status "Docker ya está instalado: $DOCKER_VERSION"
        
        # Verificar si funciona
        if sudo docker run --rm hello-world &> /dev/null; then
            print_success "✅ Docker funciona correctamente en $ARCHITECTURE_TYPE"
            return 0
        else
            print_warning "⚠️ Docker instalado pero no funciona, reinstalando..."
        fi
    fi
    
    print_status "� Instalando Docker para arquitectura $ARCHITECTURE_TYPE..."
    
    # Estrategia específica por arquitectura
    case "$ARCHITECTURE_TYPE" in
        "RISC-V")
            print_warning "🔧 RISC-V detectado - Usando métodos compatibles"
            install_docker_riscv_method
            ;;
        "ARM64")
            print_status "🔧 ARM64 detectado - Instalación estándar optimizada"
            install_docker_standard_method
            ;;
        "x86_64")
            print_status "🔧 x86_64 detectado - Instalación estándar"
            install_docker_standard_method
            ;;
        *)
            print_warning "🔧 Arquitectura $ARCH - Intentando instalación genérica"
            install_docker_fallback_method
            ;;
    esac
}

# Método específico para RISC-V
install_docker_riscv_method() {
    print_status "Método RISC-V: Instalando desde repositorios de distribución..."
    
    case $OS in
        "ubuntu"|"debian")
            # Repositorios de distribución para RISC-V
            if sudo apt-get install -y -qq docker.io docker-compose; then
                print_success "✅ Docker instalado desde repositorios $OS para RISC-V"
                DOCKER_INSTALLED=true
            else
                print_warning "⚠️ Falló instalación desde repositorios $OS"
                install_docker_fallback_method
            fi
            ;;
        *)
            install_docker_fallback_method
            ;;
    esac
}

# Método estándar para ARM64 y x86_64
install_docker_standard_method() {
    print_status "Instalando Docker usando repositorio oficial..."
    
    # Agregar clave GPG oficial de Docker
    curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Agregar repositorio oficial
    echo "deb [arch=$ARCH signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Actualizar e instalar
    sudo apt-get update -qq
    if sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin; then
        print_success "✅ Docker instalado desde repositorio oficial para $ARCHITECTURE_TYPE"
        DOCKER_INSTALLED=true
    else
        print_warning "⚠️ Falló instalación oficial, intentando método alternativo..."
        install_docker_fallback_method
    fi
}

# Método de respaldo universal
install_docker_fallback_method() {
    print_status "Método de respaldo: Script de conveniencia universal..."
    
    if curl -fsSL https://get.docker.com | sudo sh; then
        print_success "✅ Docker instalado usando script de conveniencia"
        DOCKER_INSTALLED=true
    else
        print_status "Último intento: Instalación desde repositorios genéricos..."
        if sudo apt-get install -y -qq docker.io docker-compose; then
            print_success "✅ Docker instalado desde repositorios genéricos"
            DOCKER_INSTALLED=true
        else
            print_error "❌ No se pudo instalar Docker. Instalación manual requerida."
            DOCKER_INSTALLED=false
        fi
    fi
    fi
    
    # Método 3: Instalar Podman como alternativa (compatible con Docker)
    if [ "$DOCKER_INSTALLED" = false ]; then
        print_status "Método 3: Instalando Podman (compatible con Docker)..."
        
        if sudo apt-get install -y -qq podman podman-docker; then
            print_success "✅ Podman instalado (compatible con comandos Docker)"
            
            # Crear alias para docker -> podman
            echo 'alias docker=podman' | sudo tee -a /etc/bash.bashrc
            echo 'alias docker-compose=podman-compose' | sudo tee -a /etc/bash.bashrc
            
            # Configurar socket de Podman para compatibilidad
            sudo systemctl enable --now podman.socket
            
    
    if [ "$DOCKER_INSTALLED" = false ]; then
        print_error "❌ Falló la instalación de Docker"
        print_error "Consulte la guía MULTI_ARCHITECTURE_GUIDE.md para instalación manual"
        exit 1
    fi
    
    # Configurar permisos y servicios universalmente
    configure_docker_universal
}

# Configuración universal de Docker
configure_docker_universal() {
    print_status "Configurando Docker para $ARCHITECTURE_TYPE..."
    
    # Agregar usuario al grupo docker
    sudo usermod -aG docker $USER 2>/dev/null || true
    
    # Habilitar y iniciar servicio
    sudo systemctl enable docker 2>/dev/null || true
    sudo systemctl start docker 2>/dev/null || true
    
    # Verificar funcionamiento
    print_status "Probando instalación de Docker..."
    if sudo docker run --rm hello-world &> /dev/null; then
        print_success "✅ Docker funciona correctamente en $ARCHITECTURE_TYPE"
    else
        print_warning "⚠️ Docker instalado pero el test falló - Continuando..."
    fi
    
    # Mostrar información de Docker
    DOCKER_VERSION=$(docker --version 2>/dev/null || echo "Docker version unknown")
    print_status "Docker instalado: $DOCKER_VERSION"
}

# Instalar Docker Compose universal
install_docker_compose_universal() {
    print_section "Instalando Docker Compose - Universal"
    
    # Verificar si ya está instalado
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version)
        print_status "Docker Compose ya está instalado: $COMPOSE_VERSION"
        return 0
    fi
    
    # Verificar plugin de Docker Compose
    if sudo docker compose version &> /dev/null; then
        print_success "✅ Docker Compose plugin disponible"
        
        # Crear alias para compatibilidad
        echo '#!/bin/bash\ndocker compose "$@"' | sudo tee /usr/local/bin/docker-compose > /dev/null
        sudo chmod +x /usr/local/bin/docker-compose
        return 0
    fi
    
    # Método 1: Desde repositorios (universal)
    if sudo apt-get install -y -qq docker-compose; then
        print_success "✅ Docker Compose instalado desde repositorios"
        return 0
    fi
    
    # Método 2: Usando pip (más compatible multi-arquitectura)
    print_status "Instalando Docker Compose usando pip..."
    if sudo pip3 install docker-compose; then
        print_success "✅ Docker Compose instalado usando pip"
        return 0
    fi
    
    print_warning "⚠️ Docker Compose no disponible - Usaremos 'docker compose' en su lugar"
}

# Configurar emulación multi-arquitectura (opcional para RISC-V)
setup_emulation() {
    print_section "Configurando Emulación Multi-Arquitectura (Opcional)"
    
    if [ "$ARCHITECTURE_TYPE" != "RISC-V" ]; then
        print_status "Emulación no necesaria para $ARCHITECTURE_TYPE"
        return 0
    fi
    
    print_status "Instalando QEMU para emulación multi-arquitectura en RISC-V..."
    sudo apt-get install -y -qq \
        qemu-user-static \
        binfmt-support \
        qemu-system-x86 \
        qemu-system-arm
    
    # Configurar binfmt para emulación
    print_status "Configurando binfmt para emulación multi-arquitectura..."
    
    # Verificar si ya está configurado
    if [ -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
        print_success "✅ Emulación multi-arquitectura ya está configurada"
    else
        print_status "Activando emulación multi-arquitectura..."
        
        # Usando Docker para configurar emulación
        if sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes &> /dev/null; then
            print_success "✅ Emulación configurada usando Docker"
        else
            print_warning "⚠️ No se pudo configurar emulación automática"
        fi
    fi
    
    # Verificar emulación
    if [ -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
        print_success "✅ Emulación x86_64 funcionando"
    else
        print_warning "⚠️ Emulación x86_64 no confirmada - Continuando..."
    fi
    
    # Configurar Docker buildx para multi-plataforma
    print_status "Configurando Docker buildx..."
    
    # Verificar si buildx está disponible
    if docker buildx version &> /dev/null; then
        print_status "Docker buildx disponible"
    else
        print_warning "⚠️ Docker buildx no disponible - Usando build clásico"
        return 0
    fi
    
    # Crear builder personalizado si no existe
    if ! docker buildx ls | grep -q "esp32-builder"; then
        print_status "Creando builder esp32 para multi-plataforma..."
        docker buildx create --name esp32-builder --driver docker-container --use || {
            print_warning "⚠️ No se pudo crear builder personalizado - Usando default"
            return 0
        }
        
        docker buildx inspect --bootstrap || {
            print_warning "⚠️ No se pudo inicializar builder"
            return 0
        }
    fi
    
    # Verificar plataformas disponibles
    PLATFORMS=$(docker buildx ls | grep esp32-builder | awk '{print $4}' || echo "")
    if echo "$PLATFORMS" | grep -q "linux/amd64"; then
        print_success "✅ Buildx configurado - Plataformas: $PLATFORMS"
    else
        print_warning "⚠️ Plataforma linux/amd64 no confirmada en buildx"
    fi
}

# Configurar permisos seriales - MEJORADO
setup_serial_permissions() {
    print_section "Configurando Permisos Seriales"
    
    print_status "Agregando usuario al grupo dialout..."
    sudo usermod -aG dialout $USER
    
    print_status "Detectando puertos seriales disponibles..."
    SERIAL_PORTS=$(find /dev -name "tty*" -type c 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)" | head -10 || true)
    
    if [ -n "$SERIAL_PORTS" ]; then
        print_success "✅ Puertos seriales detectados:"
        echo "$SERIAL_PORTS" | while read port; do
            if [ -e "$port" ]; then
                echo "      $port"
            fi
        done
        
        # Configurar permisos para puertos existentes
        echo "$SERIAL_PORTS" | while read port; do
            if [ -e "$port" ]; then
                sudo chmod 666 "$port" 2>/dev/null || true
            fi
        done
        
        print_status "Permisos temporales configurados"
    else
        print_warning "⚠️ No se detectaron puertos seriales actualmente"
        print_status "Esto es normal si el ESP32 no está conectado"
    fi
    
    # Crear reglas udev más completas
    print_status "Creando reglas udev para permisos automáticos..."
    cat << 'EOF' | sudo tee /etc/udev/rules.d/99-esp32-serial.rules > /dev/null
# Reglas udev para ESP32 y dispositivos seriales
# Aplicar permisos automáticamente cuando se conecten dispositivos

# Puertos seriales nativos
KERNEL=="ttyS[0-9]*", GROUP="dialout", MODE="0666"

# Dispositivos USB-Serial (CH340, CP2102, FTDI, etc.)
KERNEL=="ttyUSB[0-9]*", GROUP="dialout", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", GROUP="dialout", MODE="0666"  # CH340
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", GROUP="dialout", MODE="0666"  # CP210x
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", GROUP="dialout", MODE="0666"  # FTDI

# Dispositivos USB-CDC (ESP32-S2/S3 native USB)
KERNEL=="ttyACM[0-9]*", GROUP="dialout", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", GROUP="dialout", MODE="0666"  # Espressif

# ESP32 específicos por Product ID
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1001", GROUP="dialout", MODE="0666"  # ESP32-S2
SUBSYSTEM=="tty", ATTRS{idVendor}=="303a", ATTRS{idProduct}=="1002", GROUP="dialout", MODE="0666"  # ESP32-S3

EOF
    
    # Recargar reglas udev
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    print_success "✅ Reglas udev configuradas"
    print_status "Los permisos se aplicarán automáticamente al conectar dispositivos"
}

# Crear estructura del proyecto
create_project_structure() {
    print_section "Configurando Estructura del Proyecto"
    
    # NOTA: Ahora trabajamos directamente en el directorio raíz del proyecto
    # No creamos carpeta esp32_api_docker/ separada
    
    print_status "Creando estructura de directorios necesarios..."
    mkdir -p {scripts,config,logs,data,docs}
    
    # Verificar que estamos en el directorio correcto del proyecto
    if [ ! -f "main.py" ]; then
        print_error "Error: No se encontró main.py. Asegúrate de estar en el directorio raíz del proyecto API_cargador_gel_litio-"
        exit 1
    fi
    
    # Crear .env.docker con configuración por defecto
    print_status "Creando archivo de configuración..."
    cat > .env.docker << 'EOF'
# =============================================================================
# ESP32 Solar Charger API - Configuración Docker para RISC-V
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

# Recursos Docker (optimizado para Orange Pi R2S)
MEMORY_LIMIT=512m
CPU_LIMIT=1.0
MEMORY_RESERVATION=256m
CPU_RESERVATION=0.5

# Configuración específica RISC-V
PLATFORM=linux/amd64
EMULATION=qemu-x86_64
EOF
    
    print_success "✅ Estructura del proyecto creada en: $(pwd)"
}

# Crear scripts auxiliares mejorados
create_helper_scripts() {
    print_section "Creando Scripts Auxiliares"
    
    # Script para detectar capacidades del sistema
    print_status "Creando script de diagnóstico..."
    cat > scripts/diagnose_system.sh << 'EOF'
#!/bin/bash
# Diagnóstico completo del sistema RISC-V

echo "🔍 ESP32 API - Diagnóstico del Sistema RISC-V"
echo "============================================="
echo ""

echo "📋 Información del Sistema:"
echo "  Arquitectura: $(uname -m)"
echo "  Kernel: $(uname -r)"
echo "  OS: $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2)"
echo "  Memoria: $(free -h | awk 'NR==2{printf "%s/%s (%.0f%%)", $3,$2,$3*100/$2}')"
echo "  Espacio: $(df -h / | awk 'NR==2{printf "%s/%s (%s)", $3,$2,$5}')"
echo ""

echo "🐳 Docker/Podman:"
if command -v docker &> /dev/null; then
    echo "  Docker: $(docker --version)"
    echo "  Estado: $(systemctl is-active docker 2>/dev/null || echo 'No disponible')"
else
    echo "  Docker: No instalado"
fi

if command -v podman &> /dev/null; then
    echo "  Podman: $(podman --version)"
fi

echo ""

echo "🔧 Emulación:"
if [ -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
    echo "  x86_64: ✅ Disponible"
else
    echo "  x86_64: ❌ No configurada"
fi

echo ""

echo "📡 Puertos Seriales:"
find /dev -name "tty*" -type c 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)" | head -5 | while read port; do
    if [ -r "$port" ] && [ -w "$port" ]; then
        echo "  $port: ✅ Accesible"
    else
        echo "  $port: ⚠️ Sin permisos"
    fi
done

echo ""

echo "👥 Grupos del Usuario:"
echo "  Grupos: $(groups)"
if groups | grep -q dialout; then
    echo "  dialout: ✅"
else
    echo "  dialout: ❌ (ejecuta: sudo usermod -aG dialout $USER)"
fi

echo ""

echo "🔍 Recomendaciones:"
if ! command -v docker &> /dev/null; then
    echo "  • Instalar Docker/Podman"
fi

if [ ! -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
    echo "  • Configurar emulación x86_64"
fi

if ! groups | grep -q dialout; then
    echo "  • Agregar usuario a grupo dialout"
fi
EOF
    chmod +x scripts/diagnose_system.sh
    
    # Script de detección de puerto mejorado
    print_status "Creando script de detección de puertos..."
    cat > scripts/detect_serial_port.sh << 'EOF'
#!/bin/bash
# Detectar puerto serial del ESP32 - Versión RISC-V

echo "🔍 Detectando puertos seriales en Orange Pi R2S..."
echo ""

# Función para obtener información del dispositivo
get_device_info() {
    local port="$1"
    local info=""
    
    if command -v udevadm &> /dev/null; then
        # Intentar obtener vendor/product info
        vendor=$(udevadm info --name="$port" --query=property 2>/dev/null | grep "ID_VENDOR=" | cut -d= -f2)
        model=$(udevadm info --name="$port" --query=property 2>/dev/null | grep "ID_MODEL=" | cut -d= -f2)
        
        if [ -n "$vendor" ] || [ -n "$model" ]; then
            info="$vendor $model"
        fi
    fi
    
    echo "$info"
}

# Buscar puertos seriales
echo "📋 Puertos seriales encontrados:"
found_ports=0

for port in /dev/ttyS* /dev/ttyUSB* /dev/ttyACM*; do
    if [ -e "$port" ]; then
        ((found_ports++))
        
        # Verificar permisos
        if [ -r "$port" ] && [ -w "$port" ]; then
            status="✅ Accesible"
        else
            status="⚠️ Sin permisos"
        fi
        
        # Obtener información del dispositivo
        device_info=$(get_device_info "$port")
        
        echo "  $found_ports) $port - $status"
        if [ -n "$device_info" ]; then
            echo "     └─ $device_info"
        fi
    fi
done

if [ $found_ports -eq 0 ]; then
    echo "❌ No se encontraron puertos seriales"
    echo ""
    echo "💡 Soluciones:"
    echo "  • Conecta el ESP32 al Orange Pi R2S"
    echo "  • Verifica el cable USB"
    echo "  • Ejecuta: lsusb (para ver dispositivos USB)"
    echo "  • Ejecuta: dmesg | tail (para ver mensajes del kernel)"
    exit 1
fi

echo ""
echo "🎯 Detección automática de ESP32:"

# Intentar detectar ESP32 automáticamente
esp32_found=false

for port in /dev/ttyUSB* /dev/ttyACM*; do
    if [ -e "$port" ]; then
        device_info=$(get_device_info "$port")
        
        # Buscar patrones conocidos de ESP32
        if echo "$device_info" | grep -iq "espressif\|esp32\|silicon.*labs\|ch340\|cp210"; then
            echo "🎉 ESP32 detectado en: $port"
            echo "   Información: $device_info"
            esp32_found=true
            break
        fi
    fi
done

if [ "$esp32_found" = false ]; then
    echo "⚠️ ESP32 no detectado automáticamente"
    echo "Usa el primer puerto USB disponible o configura manualmente"
fi

echo ""
echo "🔧 Para cambiar puerto:"
echo "  ./scripts/change_serial_port.sh /dev/ttyUSB0"
EOF
    chmod +x scripts/detect_serial_port.sh
    
    # Script de construcción adaptado para RISC-V
    print_status "Creando script de construcción..."
    cat > scripts/build.sh << 'EOF'
#!/bin/bash
# Construir imagen Docker con emulación x86_64 en RISC-V

set -e

echo "🏗️ ESP32 API - Build para Orange Pi R2S RISC-V"
echo "=============================================="
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

# Verificar que Docker funcione
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está funcionando"
    echo "💡 Intenta: sudo systemctl start docker"
    exit 1
fi

echo "📦 Plataforma objetivo: linux/amd64 (emulado en RISC-V)"
echo "🔧 Método de build: $(docker version --format '{{.Server.Version}}')"
echo ""

# Verificar buildx
if docker buildx version &> /dev/null; then
    echo "🚀 Usando Docker buildx para multi-plataforma"
    
    # Configurar builder si no existe
    if ! docker buildx ls | grep -q "esp32-builder"; then
        echo "⚙️ Configurando builder para emulación..."
        docker buildx create --name esp32-builder --driver docker-container --use || true
        docker buildx inspect --bootstrap || true
    fi
    
    # Usar buildx
    docker buildx use esp32-builder 2>/dev/null || docker buildx use default
    
    echo "🔨 Iniciando build con buildx..."
    docker buildx build \
        --platform linux/amd64 \
        --tag esp32-solar-api:emulated-x86_64 \
        --load \
        .
else
    echo "🚀 Usando Docker build clásico con emulación"
    
    # Verificar emulación
    if [ ! -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
        echo "⚠️ Emulación x86_64 no detectada, configurando..."
        sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || true
    fi
    
    echo "🔨 Iniciando build clásico..."
    docker build \
        --platform linux/amd64 \
        --tag esp32-solar-api:emulated-x86_64 \
        .
fi

echo ""
echo "✅ Build completado!"
echo "🚀 Ejecutar con: docker-compose up -d"
echo "📊 Verificar con: docker images | grep esp32"
EOF
    chmod +x scripts/build.sh
    
    print_success "✅ Scripts auxiliares creados"
}

# Función principal universal
main() {
    print_header "ESP32 Solar Charger API - Instalación Universal Multi-Arquitectura"
    
    echo -e "${CYAN}🌟 Este script instala automáticamente en cualquier arquitectura:${NC}"
    echo -e "${CYAN}• x86_64 (PC/Servidores tradicionales)${NC}"
    echo -e "${CYAN}• ARM64 (Raspberry Pi, Orange Pi ARM)${NC}"
    echo -e "${CYAN}• RISC-V (Orange Pi R2S y compatibles)${NC}"
    echo -e "${CYAN}• Auto-detección de CPU y configuración optimizada${NC}"
    echo -e "${CYAN}• Docker con estrategias específicas por arquitectura${NC}"
    echo ""
    
    read -p "¿Continuar con la instalación universal? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Instalación cancelada"
        exit 1
    fi
    
    # Verificar permisos sudo
    if ! sudo -n true 2>/dev/null; then
        print_status "Este script necesita permisos sudo para:"
        print_status "• Instalar Docker desde repositorios oficiales"
        print_status "• Configurar emulación multi-arquitectura (RISC-V)"
        print_status "• Configurar permisos seriales universales"
        echo ""
        sudo -v
    fi
    
    # Ejecutar instalación universal
    detect_cpu_configuration       # ← NUEVA DETECCIÓN AUTOMÁTICA
    detect_os
    update_system
    install_docker_universal       # ← MÉTODO UNIVERSAL
    install_docker_compose_universal # ← MÉTODO UNIVERSAL
    setup_emulation                # ← EMULACIÓN CUANDO SEA NECESARIA
    setup_serial_permissions
    create_project_structure
    create_helper_scripts
    
    print_header "🎉 INSTALACIÓN UNIVERSAL COMPLETADA"
    
    echo -e "${GREEN}✅ Arquitectura $ARCHITECTURE_TYPE detectada y configurada${NC}"
    echo -e "${GREEN}✅ Docker instalado para $ARCHITECTURE_TYPE${NC}"
    echo -e "${GREEN}✅ Configuración optimizada: $OPTIMAL_WORKERS workers${NC}"
    echo -e "${GREEN}✅ Permisos seriales configurados universalmente${NC}"
    echo -e "${GREEN}✅ Proyecto listo en: $(pwd)${NC}"
    echo ""
    
    # Verificación final universal
    print_section "🔍 VERIFICACIÓN FINAL"
    
    echo "�️ Sistema detectado:"
    echo "   Arquitectura: $ARCHITECTURE_TYPE ($ARCH)"
    echo "   CPUs: $CPU_COUNT cores → $OPTIMAL_WORKERS workers optimizados"
    echo "   Memoria: ${TOTAL_MEMORY_GB}GB"
    echo ""
    
    echo "�🐳 Docker instalado:"
    if command -v docker &> /dev/null; then
        docker --version
        echo "   Estado: $(systemctl is-active docker 2>/dev/null || echo 'Funcionando')"
    fi
    
    echo ""
    if [ "$ARCHITECTURE_TYPE" = "RISC-V" ]; then
        echo "🔧 Emulación multi-arquitectura:"
        if [ -f /proc/sys/fs/binfmt_misc/qemu-x86_64 ]; then
            echo "   x86_64: ✅ Configurada para RISC-V"
        else
            echo "   x86_64: ⚠️ Se configurará automáticamente cuando sea necesaria"
        fi
        echo ""
    fi
    
    print_section "🚀 PRÓXIMOS PASOS UNIVERSALES"
    echo -e "${CYAN}1. Diagnosticar sistema específico:${NC}"
    echo -e "   ${YELLOW}./scripts/diagnose_system.sh${NC}"
    echo ""
    echo -e "${CYAN}2. Detectar puerto ESP32:${NC}"
    echo -e "   ${YELLOW}./scripts/detect_serial_port.sh${NC}"
    echo ""
    echo -e "${CYAN}3. Configurar proyecto automáticamente:${NC}"
    echo -e "   ${YELLOW}./quick_setup.sh${NC}"
    echo -e "   ${WHITE}(Auto-detectará $OPTIMAL_WORKERS workers para tu CPU)${NC}"
    echo ""
    echo -e "${CYAN}4. O construcción manual específica:${NC}"
    echo -e "   ${YELLOW}./scripts/build.sh${NC}"
    echo ""
    
    print_warning "⚠️ INFORMACIÓN IMPORTANTE:"
    print_warning "   • Reinicia la sesión para aplicar permisos: newgrp dialout"
    print_warning "   • La configuración está optimizada para $ARCHITECTURE_TYPE"
    print_warning "   • Consulta MULTI_ARCHITECTURE_GUIDE.md para detalles específicos"
    
    print_success "🎉 ¡Instalación universal completada para $ARCHITECTURE_TYPE!"
}

# Ejecutar función principal
main "$@"