#!/bin/bash
# =============================================================================
# ESP32 Solar Charger API - Configuración para Crontab
# =============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Obtener directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
LOGS_DIR="$PROJECT_DIR/logs"

print_status "🚀 Configurando ESP32 API para arranque automático con crontab..."

# Crear directorios necesarios
mkdir -p "$SCRIPTS_DIR" "$LOGS_DIR/startup"

# ========== CREAR SCRIPT DE SERVICIO PRINCIPAL ==========

print_status "📝 Creando script de servicio principal..."

cat > "$SCRIPTS_DIR/esp32_api_service.sh" << 'EOF'
#!/bin/bash
# ESP32 API Service Manager
# Maneja inicio, parada, reinicio y estado del servicio

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_DIR/esp32_api.pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/esp32_api.log"
ERROR_LOG="$LOG_DIR/esp32_api_error.log"
ENV_FILE="$PROJECT_DIR/.env"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Crear directorios si no existen
mkdir -p "$LOG_DIR"

# Funciones de utilidad
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    else
        echo ""
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Cargar entorno virtual
activate_venv() {
    if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
        source "$PROJECT_DIR/venv/bin/activate"
        return 0
    else
        log_message "ERROR: Entorno virtual no encontrado en $PROJECT_DIR/venv"
        return 1
    fi
}

# Verificar dependencias
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        log_message "ERROR: Python3 no está instalado"
        return 1
    fi
    
    if [ ! -f "$PROJECT_DIR/main.py" ]; then
        log_message "ERROR: main.py no encontrado en $PROJECT_DIR"
        return 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        log_message "WARNING: .env no encontrado, usando .env.example"
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
        else
            log_message "ERROR: No se encontró .env ni .env.example"
            return 1
        fi
    fi
    
    return 0
}

# Verificar puerto serial
check_serial_port() {
    # Leer puerto del .env
    if [ -f "$ENV_FILE" ]; then
        SERIAL_PORT=$(grep "^SERIAL_PORT=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    fi
    
    SERIAL_PORT=${SERIAL_PORT:-/dev/ttyS5}
    
    if [ ! -e "$SERIAL_PORT" ]; then
        log_message "WARNING: Puerto serial $SERIAL_PORT no encontrado"
        log_message "Puertos disponibles:"
        ls -la /dev/tty* | grep -E "(ttyS|ttyUSB|ttyACM)" >> "$LOG_FILE" 2>&1 || echo "No se encontraron puertos seriales" >> "$LOG_FILE"
        return 1
    else
        log_message "Puerto serial $SERIAL_PORT disponible"
        # Verificar permisos
        if [ ! -r "$SERIAL_PORT" ] || [ ! -w "$SERIAL_PORT" ]; then
            log_message "WARNING: Sin permisos para $SERIAL_PORT. Intentando agregar usuario a dialout..."
            sudo usermod -a -G dialout $USER 2>/dev/null || true
        fi
        return 0
    fi
}

# Función START
start_api() {
    log_message "========================================="
    log_message "Iniciando ESP32 Solar Charger API..."
    
    if is_running; then
        local pid=$(get_pid)
        log_message "La API ya está ejecutándose (PID: $pid)"
        return 0
    fi
    
    # Verificaciones previas
    if ! check_dependencies; then
        log_message "ERROR: Falló verificación de dependencias"
        return 1
    fi
    
    check_serial_port
    
    # Activar entorno virtual
    if ! activate_venv; then
        log_message "ERROR: No se pudo activar el entorno virtual"
        return 1
    fi
    
    # Cambiar al directorio del proyecto
    cd "$PROJECT_DIR"
    
    # Iniciar la API
    log_message "Ejecutando: python main.py"
    nohup python main.py >> "$LOG_FILE" 2>> "$ERROR_LOG" &
    local pid=$!
    
    # Guardar PID
    echo $pid > "$PID_FILE"
    
    # Esperar un momento para verificar que arrancó
    sleep 3
    
    if is_running; then
        log_message "✅ API iniciada exitosamente (PID: $pid)"
        
        # Verificar conectividad
        sleep 2
        if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
            log_message "✅ API respondiendo correctamente en http://localhost:8000"
        else
            log_message "⚠️ API iniciada pero aún no responde (puede estar inicializando)"
        fi
        
        return 0
    else
        log_message "❌ ERROR: La API no pudo iniciarse"
        rm -f "$PID_FILE"
        
        # Mostrar últimas líneas del log de error
        if [ -f "$ERROR_LOG" ]; then
            log_message "Últimos errores:"
            tail -n 10 "$ERROR_LOG" | while read line; do
                log_message "  $line"
            done
        fi
        
        return 1
    fi
}

# Función STOP
stop_api() {
    log_message "Deteniendo ESP32 Solar Charger API..."
    
    if ! is_running; then
        log_message "La API no está ejecutándose"
        rm -f "$PID_FILE"
        return 0
    fi
    
    local pid=$(get_pid)
    log_message "Enviando señal TERM a PID $pid..."
    
    kill -TERM "$pid" 2>/dev/null
    
    # Esperar hasta 10 segundos
    local count=0
    while [ $count -lt 10 ] && is_running; do
        sleep 1
        count=$((count + 1))
    done
    
    if is_running; then
        log_message "El proceso no se detuvo, enviando KILL..."
        kill -KILL "$pid" 2>/dev/null
        sleep 1
    fi
    
    if ! is_running; then
        log_message "✅ API detenida correctamente"
        rm -f "$PID_FILE"
        return 0
    else
        log_message "❌ ERROR: No se pudo detener la API"
        return 1
    fi
}

# Función RESTART
restart_api() {
    log_message "Reiniciando ESP32 Solar Charger API..."
    stop_api
    sleep 2
    start_api
}

# Función STATUS
status_api() {
    echo -e "${BLUE}ESP32 Solar Charger API - Estado${NC}"
    echo "=================================="
    
    if is_running; then
        local pid=$(get_pid)
        echo -e "Estado: ${GREEN}● ACTIVO${NC}"
        echo "PID: $pid"
        echo "Uptime: $(ps -o etime= -p $pid 2>/dev/null | xargs)"
        
        # Verificar respuesta HTTP
        if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
            echo -e "API HTTP: ${GREEN}● Respondiendo${NC}"
            
            # Obtener información adicional
            health_data=$(curl -s "http://localhost:8000/health" 2>/dev/null)
            if [ -n "$health_data" ]; then
                echo "Health Check:"
                echo "$health_data" | python3 -m json.tool 2>/dev/null | head -n 10 || echo "$health_data"
            fi
        else
            echo -e "API HTTP: ${RED}● No responde${NC}"
        fi
        
        # Uso de memoria
        if command -v ps &> /dev/null; then
            mem_usage=$(ps -p $pid -o %mem,rss --no-headers 2>/dev/null)
            if [ -n "$mem_usage" ]; then
                echo "Memoria: $mem_usage"
            fi
        fi
        
    else
        echo -e "Estado: ${RED}● INACTIVO${NC}"
        
        if [ -f "$PID_FILE" ]; then
            echo "PID file existe pero el proceso no está ejecutándose"
            rm -f "$PID_FILE"
        fi
    fi
    
    echo ""
    echo "Archivos de log:"
    echo "  Principal: $LOG_FILE"
    echo "  Errores: $ERROR_LOG"
    
    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "Últimas entradas del log:"
        tail -n 5 "$LOG_FILE"
    fi
}

# Función principal
case "$1" in
    start)
        start_api
        exit $?
        ;;
    stop)
        stop_api
        exit $?
        ;;
    restart)
        restart_api
        exit $?
        ;;
    status)
        status_api
        exit 0
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status}"
        echo ""
        echo "Comandos:"
        echo "  start   - Iniciar la API"
        echo "  stop    - Detener la API"
        echo "  restart - Reiniciar la API"
        echo "  status  - Ver estado actual"
        exit 1
        ;;
esac
EOF

chmod +x "$SCRIPTS_DIR/esp32_api_service.sh"
print_success "Script de servicio creado"

# ========== CREAR SCRIPT PARA CRONTAB ==========

print_status "📝 Creando script wrapper para crontab..."

cat > "$SCRIPTS_DIR/esp32_api_crontab.sh" << 'EOF'
#!/bin/bash
# Wrapper script para crontab - Asegura que la API esté ejecutándose

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SCRIPT="$SCRIPT_DIR/esp32_api_service.sh"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
STARTUP_LOG="$PROJECT_DIR/logs/startup/startup_$(date +%Y%m%d).log"

# Crear directorio de logs si no existe
mkdir -p "$(dirname "$STARTUP_LOG")"

# Función de logging
log_startup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$STARTUP_LOG"
}

# Esperar un momento para que el sistema esté completamente iniciado
if [ "$1" == "--boot" ]; then
    log_startup "Esperando 30 segundos para arranque completo del sistema..."
    sleep 30
fi

log_startup "========================================="
log_startup "Verificando ESP32 Solar Charger API..."

# Verificar si el script de servicio existe
if [ ! -f "$SERVICE_SCRIPT" ]; then
    log_startup "ERROR: Script de servicio no encontrado: $SERVICE_SCRIPT"
    exit 1
fi

# Verificar estado actual
if "$SERVICE_SCRIPT" status | grep -q "ACTIVO"; then
    log_startup "La API ya está ejecutándose"
    
    # Verificar que responda
    if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
        log_startup "API respondiendo correctamente"
    else
        log_startup "API ejecutándose pero no responde, reiniciando..."
        "$SERVICE_SCRIPT" restart >> "$STARTUP_LOG" 2>&1
    fi
else
    log_startup "La API no está ejecutándose, iniciando..."
    "$SERVICE_SCRIPT" start >> "$STARTUP_LOG" 2>&1
    
    if [ $? -eq 0 ]; then
        log_startup "API iniciada exitosamente"
    else
        log_startup "ERROR: No se pudo iniciar la API"
        exit 1
    fi
fi

# Limpiar logs antiguos (mantener solo últimos 7 días)
find "$PROJECT_DIR/logs/startup" -name "startup_*.log" -mtime +7 -delete 2>/dev/null

log_startup "Verificación completada"
EOF

chmod +x "$SCRIPTS_DIR/esp32_api_crontab.sh"
print_success "Script wrapper para crontab creado"

# ========== CREAR SCRIPT DE MONITOREO ==========

print_status "📝 Creando script de monitoreo..."

cat > "$SCRIPTS_DIR/esp32_api_monitor.sh" << 'EOF'
#!/bin/bash
# Monitor para verificar y reiniciar la API si es necesario

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SCRIPT="$SCRIPT_DIR/esp32_api_service.sh"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MONITOR_LOG="$PROJECT_DIR/logs/monitor.log"
MAX_RETRIES=3
RETRY_DELAY=10

# Función de logging
log_monitor() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"
}

# Verificar salud de la API
check_api_health() {
    # Primero verificar si el proceso está ejecutándose
    if ! "$SERVICE_SCRIPT" status | grep -q "ACTIVO"; then
        return 1
    fi
    
    # Luego verificar respuesta HTTP
    if ! curl -s -f "http://localhost:8000/health" > /dev/null 2>&1; then
        return 2
    fi
    
    # Verificar conexión con ESP32 (opcional)
    health_response=$(curl -s "http://localhost:8000/health" 2>/dev/null)
    if echo "$health_response" | grep -q '"connected":false'; then
        log_monitor "WARNING: API activa pero ESP32 desconectado"
        # No reiniciar por esto, solo advertir
    fi
    
    return 0
}

# Función principal de monitoreo
monitor_api() {
    log_monitor "Iniciando monitoreo de API..."
    
    check_api_health
    status=$?
    
    case $status in
        0)
            log_monitor "✅ API funcionando correctamente"
            ;;
        1)
            log_monitor "❌ API no está ejecutándose"
            restart_with_retries
            ;;
        2)
            log_monitor "⚠️ API ejecutándose pero no responde"
            restart_with_retries
            ;;
    esac
}

# Reiniciar con reintentos
restart_with_retries() {
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        log_monitor "Intento de reinicio $((retries + 1))/$MAX_RETRIES..."
        
        "$SERVICE_SCRIPT" restart >> "$MONITOR_LOG" 2>&1
        
        sleep $RETRY_DELAY
        
        if check_api_health; then
            log_monitor "✅ API reiniciada exitosamente"
            return 0
        else
            retries=$((retries + 1))
            if [ $retries -lt $MAX_RETRIES ]; then
                log_monitor "Reinicio falló, esperando antes de reintentar..."
                sleep $((RETRY_DELAY * 2))
            fi
        fi
    done
    
    log_monitor "❌ ERROR: No se pudo reiniciar la API después de $MAX_RETRIES intentos"
    
    # Enviar alerta (puedes agregar envío de email o notificación aquí)
    # echo "ESP32 API Down" | mail -s "Alert: ESP32 API Failure" admin@example.com
    
    return 1
}

# Rotar log si es muy grande (>10MB)
rotate_log() {
    if [ -f "$MONITOR_LOG" ]; then
        log_size=$(stat -f%z "$MONITOR_LOG" 2>/dev/null || stat -c%s "$MONITOR_LOG" 2>/dev/null)
        if [ "$log_size" -gt 10485760 ]; then
            mv "$MONITOR_LOG" "$MONITOR_LOG.old"
            log_monitor "Log rotado (tamaño: $log_size bytes)"
        fi
    fi
}

# Ejecutar monitoreo
rotate_log
monitor_api
EOF

chmod +x "$SCRIPTS_DIR/esp32_api_monitor.sh"
print_success "Script de monitoreo creado"

# ========== CREAR CONFIGURACIÓN DE CRONTAB ==========

print_status "📝 Creando archivo de configuración para crontab..."

CRONTAB_FILE="$PROJECT_DIR/crontab_config.txt"

cat > "$CRONTAB_FILE" << EOF
# ESP32 Solar Charger API - Configuración de Crontab
# 
# Para instalar, ejecuta:
#   crontab -l > current_cron.txt
#   cat crontab_config.txt >> current_cron.txt
#   crontab current_cron.txt
#   rm current_cron.txt

# Arranque automático al iniciar el sistema
@reboot $SCRIPTS_DIR/esp32_api_crontab.sh --boot

# Verificación cada 5 minutos para asegurar que esté ejecutándose
*/5 * * * * $SCRIPTS_DIR/esp32_api_crontab.sh

# Monitoreo detallado cada 15 minutos
*/15 * * * * $SCRIPTS_DIR/esp32_api_monitor.sh

# Reinicio diario a las 3:00 AM (opcional - comenta si no lo necesitas)
# 0 3 * * * $SCRIPTS_DIR/esp32_api_service.sh restart

# Limpieza de logs antiguos cada domingo a las 2:00 AM
0 2 * * 0 find $LOGS_DIR -name "*.log" -mtime +30 -delete
EOF

print_success "Configuración de crontab creada"

# ========== CREAR SCRIPT DE INSTALACIÓN ==========

print_status "📝 Creando script de instalación de crontab..."

cat > "$SCRIPTS_DIR/install_crontab.sh" << 'EOF'
#!/bin/bash
# Instalar configuración en crontab

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CRONTAB_CONFIG="$PROJECT_DIR/crontab_config.txt"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Instalando configuración de crontab para ESP32 API..."

# Verificar que existe el archivo de configuración
if [ ! -f "$CRONTAB_CONFIG" ]; then
    echo -e "${RED}ERROR: No se encontró $CRONTAB_CONFIG${NC}"
    exit 1
fi

# Hacer backup del crontab actual
echo "Haciendo backup del crontab actual..."
crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || true

# Verificar si ya están instaladas las entradas
if crontab -l 2>/dev/null | grep -q "esp32_api_crontab.sh"; then
    echo -e "${RED}Las entradas de crontab ya existen. ¿Deseas reinstalarlas? (y/N)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Instalación cancelada"
        exit 0
    fi
    
    # Remover entradas existentes
    echo "Removiendo entradas existentes..."
    crontab -l 2>/dev/null | grep -v "esp32_api" > temp_cron.txt || true
    crontab temp_cron.txt
    rm temp_cron.txt
fi

# Instalar nuevas entradas
echo "Instalando nuevas entradas de crontab..."
(crontab -l 2>/dev/null; echo ""; cat "$CRONTAB_CONFIG" | grep -v "^#") | crontab -

echo -e "${GREEN}✅ Configuración de crontab instalada exitosamente${NC}"
echo ""
echo "Entradas agregadas:"
crontab -l | grep "esp32_api"
echo ""
echo "La API se iniciará:"
echo "  - Automáticamente al reiniciar el sistema"
echo "  - Se verificará cada 5 minutos"
echo "  - Se monitoreará detalladamente cada 15 minutos"
echo ""
echo "Para ver los logs:"
echo "  tail -f $PROJECT_DIR/logs/startup/startup_$(date +%Y%m%d).log"
EOF

chmod +x "$SCRIPTS_DIR/install_crontab.sh"
print_success "Script de instalación creado"

# ========== CREAR SCRIPT DE DESINSTALACIÓN ==========

print_status "📝 Creando script de desinstalación..."

cat > "$SCRIPTS_DIR/uninstall_crontab.sh" << 'EOF'
#!/bin/bash
# Desinstalar configuración de crontab

echo "Desinstalando configuración de crontab para ESP32 API..."

# Verificar si hay entradas instaladas
if ! crontab -l 2>/dev/null | grep -q "esp32_api"; then
    echo "No se encontraron entradas de ESP32 API en crontab"
    exit 0
fi

# Hacer backup
crontab -l > "crontab_backup_before_uninstall_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null

# Remover entradas
crontab -l 2>/dev/null | grep -v "esp32_api" > temp_cron.txt || true

if [ -s temp_cron.txt ]; then
    crontab temp_cron.txt
else
    # Si el archivo está vacío, eliminar completamente el crontab
    crontab -r 2>/dev/null || true
fi

rm -f temp_cron.txt

echo "✅ Entradas de ESP32 API removidas de crontab"
EOF

chmod +x "$SCRIPTS_DIR/uninstall_crontab.sh"
print_success "Script de desinstalación creado"

# ========== CREAR SCRIPT DE GESTIÓN ==========

print_status "📝 Creando script de gestión maestro..."

cat > "$PROJECT_DIR/manage_api.sh" << 'EOF'
#!/bin/bash
# Script maestro de gestión para ESP32 Solar Charger API

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    echo -e "${BLUE}ESP32 Solar Charger API - Gestión${NC}"
    echo "===================================="
    echo "1) Iniciar API"
    echo "2) Detener API"
    echo "3) Reiniciar API"
    echo "4) Ver estado"
    echo "5) Instalar en crontab"
    echo "6) Desinstalar de crontab"
    echo "7) Ver logs en tiempo real"
    echo "8) Ver logs de startup"
    echo "9) Ejecutar monitoreo manual"
    echo "0) Salir"
    echo ""
    echo -n "Selecciona una opción: "
}

while true; do
    show_menu
    read -r option
    
    case $option in
        1)
            echo -e "\n${YELLOW}Iniciando API...${NC}"
            "$SCRIPTS_DIR/esp32_api_service.sh" start
            ;;
        2)
            echo -e "\n${YELLOW}Deteniendo API...${NC}"
            "$SCRIPTS_DIR/esp32_api_service.sh" stop
            ;;
        3)
            echo -e "\n${YELLOW}Reiniciando API...${NC}"
            "$SCRIPTS_DIR/esp32_api_service.sh" restart
            ;;
        4)
            echo ""
            "$SCRIPTS_DIR/esp32_api_service.sh" status
            ;;
        5)
            echo -e "\n${YELLOW}Instalando en crontab...${NC}"
            "$SCRIPTS_DIR/install_crontab.sh"
            ;;
        6)
            echo -e "\n${YELLOW}Desinstalando de crontab...${NC}"
            "$SCRIPTS_DIR/uninstall_crontab.sh"
            ;;
        7)
            echo -e "\n${YELLOW}Mostrando logs (Ctrl+C para salir)...${NC}"
            tail -f "$SCRIPT_DIR/logs/esp32_api.log"
            ;;
        8)
            echo -e "\n${YELLOW}Logs de startup de hoy:${NC}"
            cat "$SCRIPT_DIR/logs/startup/startup_$(date +%Y%m%d).log" 2>/dev/null || echo "No hay logs de startup para hoy"
            ;;
        9)
            echo -e "\n${YELLOW}Ejecutando monitoreo manual...${NC}"
            "$SCRIPTS_DIR/esp32_api_monitor.sh"
            ;;
        0)
            echo -e "\n${GREEN}¡Hasta luego!${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${RED}Opción inválida${NC}"
            ;;
    esac
    
    echo -e "\nPresiona Enter para continuar..."
    read
    clear
done
EOF

chmod +x "$PROJECT_DIR/manage_api.sh"
print_success "Script de gestión creado"

# ========== CREAR README DE CRONTAB ==========

print_status "📝 Creando documentación..."

cat > "$PROJECT_DIR/CRONTAB_README.md" << 'EOF'
# ESP32 Solar Charger API - Configuración Crontab

## 🚀 Instalación Rápida

```bash
# Opción 1: Usar el menú interactivo
./manage_api.sh
# Seleccionar opción 5

# Opción 2: Instalación directa
./scripts/install_crontab.sh
```

## 📋 Scripts Disponibles

### 1. **manage_api.sh** - Gestión Principal
Menú interactivo para todas las operaciones.

### 2. **scripts/esp32_api_service.sh** - Control del Servicio
```bash
./scripts/esp32_api_service.sh start    # Iniciar
./scripts/esp32_api_service.sh stop     # Detener
./scripts/esp32_api_service.sh restart  # Reiniciar
./scripts/esp32_api_service.sh status   # Ver estado
```

### 3. **scripts/esp32_api_crontab.sh** - Wrapper para Crontab
Ejecutado automáticamente por cron para verificar que la API esté activa.

### 4. **scripts/esp32_api_monitor.sh** - Monitor Detallado
Verifica la salud de la API y la reinicia si es necesario.

## ⚙️ Configuración de Crontab

Las siguientes tareas se configuran automáticamente:

1. **@reboot** - Inicia la API al arrancar el sistema
2. ***/5 * * * *** - Verifica cada 5 minutos que esté ejecutándose
3. ***/15 * * * *** - Monitoreo detallado cada 15 minutos
4. **0 2 * * 0** - Limpieza de logs antiguos los domingos

## 📁 Estructura de Logs

```
logs/
├── esp32_api.log          # Log principal de la API
├── esp32_api_error.log    # Errores de la API
├── monitor.log            # Log del monitor
└── startup/               # Logs de arranque por día
    └── startup_YYYYMMDD.log
```

## 🔧 Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f logs/esp32_api.log

# Ver estado del crontab
crontab -l | grep esp32_api

# Ver logs de startup de hoy
cat logs/startup/startup_$(date +%Y%m%d).log

# Verificar si la API está respondiendo
curl http://localhost:8000/health
```

## 🚨 Solución de Problemas

### La API no se inicia automáticamente
1. Verifica que crontab esté instalado: `crontab -l`
2. Revisa los logs de startup en `logs/startup/`
3. Verifica permisos del puerto serial: `ls -la /dev/ttyS*`

### Error de permisos en puerto serial
```bash
# Agregar usuario al grupo dialout
sudo usermod -a -G dialout $USER
# Cerrar sesión y volver a entrar
```

### La API se detiene frecuentemente
1. Revisa `logs/monitor.log` para patrones
2. Verifica recursos del sistema: `free -h` y `df -h`
3. Revisa `logs/esp32_api_error.log` para errores

## 🔐 Seguridad

- Los scripts solo afectan al usuario actual
- No se requiere sudo para la operación normal
- Los logs se rotan automáticamente

## 📊 Monitoreo

Para monitoreo continuo, puedes usar:

```bash
# Terminal 1 - Ver logs de la API
tail -f logs/esp32_api.log

# Terminal 2 - Ver estado del sistema
watch -n 5 './scripts/esp32_api_service.sh status'

# Terminal 3 - Monitorear recursos
htop
```

## 🛑 Desinstalación

```bash
# Detener la API
./scripts/esp32_api_service.sh stop

# Remover de crontab
./scripts/uninstall_crontab.sh

# O usar el menú
./manage_api.sh
# Seleccionar opción 6
```
EOF

print_success "Documentación creada"

# ========== RESUMEN FINAL ==========

print_success "✅ Configuración completada exitosamente!"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📋 RESUMEN DE ARCHIVOS CREADOS:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📁 Scripts principales:"
echo "   • manage_api.sh - Menú de gestión principal"
echo "   • scripts/esp32_api_service.sh - Control del servicio"
echo "   • scripts/esp32_api_crontab.sh - Wrapper para crontab"
echo "   • scripts/esp32_api_monitor.sh - Monitor de salud"
echo ""
echo "📁 Scripts de instalación:"
echo "   • scripts/install_crontab.sh - Instalar en crontab"
echo "   • scripts/uninstall_crontab.sh - Desinstalar de crontab"
echo ""
echo "📁 Configuración:"
echo "   • crontab_config.txt - Configuración de crontab"
echo "   • CRONTAB_README.md - Documentación completa"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🚀 PRÓXIMOS PASOS:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1️⃣ Instalar en crontab (RECOMENDADO):"
echo "   ./manage_api.sh"
echo "   # Seleccionar opción 5"
echo ""
echo "2️⃣ O instalación manual directa:"
echo "   ./scripts/install_crontab.sh"
echo ""
echo "3️⃣ Verificar que esté funcionando:"
echo "   ./scripts/esp32_api_service.sh status"
echo ""
echo "4️⃣ Ver logs de arranque:"
echo "   tail -f logs/startup/startup_$(date +%Y%m%d).log"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "💡 TIPS:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "• La API se iniciará automáticamente al reiniciar el sistema"
echo "• Se verificará cada 5 minutos que esté ejecutándose"
echo "• Los logs se guardan en el directorio 'logs/'"
echo "• Usa './manage_api.sh' para gestión fácil"
echo ""
echo "═══════════════════════════════════════════════════════════"

# Preguntar si desea instalar ahora
echo ""
echo -e "${YELLOW}¿Deseas instalar la configuración en crontab ahora? (y/N)${NC}"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    "$SCRIPTS_DIR/install_crontab.sh"
else
    echo -e "${BLUE}Puedes instalar más tarde ejecutando: ./manage_api.sh${NC}"
fi