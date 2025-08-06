# ESP32 Solar Charger API

API REST para control y monitoreo del cargador solar ESP32 con **funcionalidad de apagado programado diario** y **sistema de configuraciones personalizadas**.

> ✅ **ESTADO ACTUAL - Agosto 2025:** API completamente funcional y validado. Sistema de configuraciones personalizadas operativo. Listo para integración frontend.

> 📚 **PARA DESARROLLADORES FRONTEND:** Consulta [`FRONTEND_API_DOCUMENTATION.md`](./FRONTEND_API_DOCUMENTATION.md) para documentación completa de endpoints, ejemplos de código y mejores prácticas.

## ⚡ Funcionalidades Principales

### ✅ **Sistema de Monitoreo ESP32**
- 📊 Lectura en tiempo real de voltaje, corriente y temperatura
- 🔋 Cálculo automático de porcentaje de batería
- 📱 API REST para integración con frontend
- 🔄 Polling optimizado cada 3 segundos sin bloqueos

### ✅ **Configuración de Parámetros**
- ⚙️ Configuración individual de parámetros del cargador
- 🔧 Soporte para baterías de Litio y GEL
- 🎯 Validación automática de valores
- 📡 Comunicación serial robusta con ESP32

### ✅ **Sistema de Configuraciones Personalizadas** 🆕
- 💾 Guardar múltiples configuraciones con nombres personalizados
- 🚀 Aplicar configuraciones completas con un solo clic
- 📋 Listado, búsqueda y filtrado de configuraciones
- ✅ Validación antes de guardar
- 📤 Exportar/importar configuraciones en JSON
- 🗑️ Eliminar configuraciones no utilizadas
- 📊 Estadísticas y información del sistema

### ✅ **Programación de Horarios**
- ⏰ Configuración de horarios de apagado y encendido automático
- 📅 Soporte para programación diaria
- 🔔 Notificaciones de próximos eventos programados

### ✅ **Características Técnicas Avanzadas**
- 🔒 Thread-safe con manejo de concurrencia
- 🏥 Endpoints de health check y monitoreo
- 📝 Logging detallado para debugging
- 🔄 Cache inteligente para optimizar rendimiento
- 🛡️ Manejo robusto de errores de comunicación

## 🚀 Instalación Rápida

### 💻 Instalación Estándar (x86/x64)

```bash
# Clonar/crear el proyecto
git clone <tu-repo> esp32_api
cd esp32_api

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# Ejecutar servidor
python main.py
```

### 🍊 Instalación en Orange Pi R2S (RISC-V)

Para usar este proyecto en Orange Pi R2S u otras máquinas RISC-V, sigue estos pasos específicos:

#### 1. Preparación del Sistema
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv python3-dev
sudo apt install -y build-essential git curl wget
sudo apt install -y docker.io docker-compose

# Verificar arquitectura
uname -m  # Debería mostrar: riscv64

# Configurar permisos para Docker
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker
```

#### 2. Configuración del Puerto Serial
```bash
# Verificar dispositivos USB/Serial disponibles
ls -la /dev/ttyUSB* /dev/ttyACM*

# Agregar usuario al grupo dialout para acceso serial
sudo usermod -aG dialout $USER

# Configurar permisos del puerto (ajustar según tu dispositivo)
sudo chmod 666 /dev/ttyUSB0

# Verificar permisos
ls -la /dev/ttyUSB0
```

#### 3. Instalación con Docker (Recomendado para RISC-V)
```bash
# Clonar proyecto
git clone <tu-repo> API_cargador_gel_litio-
cd API_cargador_gel_litio-

# 🍊 IMPORTANTE: Para RISC-V crear carpeta específica Docker
mkdir -p esp32_api_docker
cp docker-compose.yml esp32_api_docker/
cp Dockerfile esp32_api_docker/

# Cambiar al directorio Docker específico
cd esp32_api_docker

# Verificar y ajustar docker-compose.yml
# Asegurarse de que el puerto serial sea correcto
nano docker-compose.yml

# En la sección devices, verificar:
devices:
  - "/dev/ttyUSB0:/dev/ttyUSB0"  # Ajustar según tu puerto

# 🔧 Ajustar rutas en docker-compose.yml para RISC-V
# Cambiar context de "." a ".." para apuntar al directorio raíz
build:
  context: ..
  dockerfile: esp32_api_docker/Dockerfile

# Construir y ejecutar con Docker
docker-compose up --build -d

# Verificar logs
docker-compose logs -f esp32-api
```

#### 4. Instalación Nativa (Alternativa)
```bash
# Solo si Docker presenta problemas en RISC-V
cd API_cargador_gel_litio-

# Crear entorno virtual Python
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias (puede tardar más en RISC-V)
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno
export SERIAL_PORT=/dev/ttyUSB0
export HOST=0.0.0.0
export PORT=8000
export DEBUG=false

# Ejecutar servidor
python main.py
```

#### 5. Configuración Específica para Orange Pi R2S
```bash
# Editar docker-compose.yml para optimizar para RISC-V
nano docker-compose.yml

# Ajustar recursos específicos:
environment:
  - OMP_NUM_THREADS=4          # Ajustar según CPUs disponibles
  - PYTHONTHREADS=4            # Optimizar para RISC-V
  - UV_THREADPOOL_SIZE=4       # libuv threadpool
  
# Límites de recursos optimizados
cpus: 4.0                      # Orange Pi R2S tiene 4 cores
mem_limit: 1512m               # Ajustar según RAM disponible
```

#### 6. Scripts de Automatización para Orange Pi R2S
```bash
# Hacer ejecutables los scripts incluidos
chmod +x *.sh

# Instalación automatizada Orange Pi
sudo ./install_orangepi.sh

# Configuración rápida
./quick_setup.sh

# Configurar crontab para inicio automático
crontab -e

# Agregar al final:
# Actualización automática todos los días a las 3 AM
0 3 * * * cd /home/orangepi/API_cargador_gel_litio- && ./quick_setup.sh >> /var/log/api_update.log 2>&1
```

---

## 📚 **DOCUMENTACIÓN PARA DESARROLLADORES**

### 🎯 **Para Desarrolladores Frontend**

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [`FRONTEND_API_DOCUMENTATION.md`](./FRONTEND_API_DOCUMENTATION.md) | 📖 **Documentación completa del API** - Todos los endpoints, ejemplos de peticiones/respuestas, códigos de error | Frontend Developers |
| [`FRONTEND_EXAMPLES.md`](./FRONTEND_EXAMPLES.md) | 💡 **Ejemplos prácticos de código** - Componentes React, hooks, CSS, integraciones | Frontend Developers |
| [`API_QUICK_REFERENCE.md`](./API_QUICK_REFERENCE.md) | ⚡ **Referencia rápida** - Cheat sheet con endpoints y parámetros más comunes | Desarrollo rápido |
| [`README_CONFIGURACIONES.md`](./README_CONFIGURACIONES.md) | 📋 **Sistema de configuraciones** - Documentación específica del sistema de configuraciones personalizadas | Backend/Frontend |

### 🔧 **Para Administradores de Sistema**

- **README.md** (este archivo): Instalación, configuración, troubleshooting
- **`configuraciones.json`**: Archivo de configuraciones guardadas (generado automáticamente)
- **`logs/esp32_api.log`**: Logs detallados del sistema

### 📊 **Estado de Funcionalidades - Agosto 2025**

| Funcionalidad | Estado | Documentación | Validación |
|---------------|--------|---------------|------------|
| 📊 Lectura datos ESP32 | ✅ Funcional | ✅ Completa | ✅ Validado |
| ⚙️ Configuración parámetros | ✅ Funcional | ✅ Completa | ✅ Validado |
| 📋 Configuraciones personalizadas | ✅ Funcional | ✅ Completa | ✅ Validado |
| ⏰ Programación horarios | ✅ Funcional | ✅ Completa | ✅ Validado |
| 🏥 Health checks | ✅ Funcional | ✅ Completa | ✅ Validado |
| 🔒 Thread safety | ✅ Implementado | ✅ Documentado | ✅ Probado |
| 📱 Frontend integration | ⏳ Pendiente | ✅ Documentado | ⏳ Por implementar |

---

crontab -e

# Agregar al final:
```

#### 7. Verificación del Sistema
```bash
# Verificar que la API está corriendo
curl http://localhost:8000/health

# Verificar conexión ESP32
curl http://localhost:8000/data/

# Ver logs en tiempo real (desde directorio esp32_api_docker)
cd esp32_api_docker
docker-compose logs -f esp32-api

# O si es instalación nativa (desde directorio raíz):
cd ..
tail -f logs/esp32_api.log
```

#### 8. Actualización del Código (Git Pull)

**🔄 Proceso de Actualización Automática:**
```bash
# Usar el script de actualización incluido
./quick_setup.sh

# O manualmente paso a paso:
# 1. Obtener últimos cambios (desde directorio raíz)
cd /home/orangepi/API_cargador_gel_litio-
git pull origin main

# 2. Actualizar archivos Docker en carpeta específica
cp docker-compose.yml esp32_api_docker/
cp Dockerfile esp32_api_docker/

# 3. Cambiar a directorio Docker para RISC-V
cd esp32_api_docker

# 4. Detener contenedores actuales
docker-compose down

# 5. Reconstruir imagen con cambios
docker-compose build --no-cache

# 6. Levantar contenedores actualizados
docker-compose up -d

# 7. Verificar que todo funciona
docker-compose logs -f esp32-api
```

**🚀 Script de Actualización Rápida:**
```bash
# Hacer el script ejecutable (solo la primera vez)
chmod +x quick_setup.sh

# Ejecutar actualización completa
./quick_setup.sh

# El script automáticamente:
# - Hace git pull
# - Copia archivos a esp32_api_docker/
# - Detiene contenedores
# - Reconstruye imágenes
# - Levanta servicios actualizados
# - Verifica el estado
```

**⚠️ Consideraciones Importantes para RISC-V:**
```bash
# ANTES de actualizar, hacer backup de configuraciones
cp configuraciones.json configuraciones.json.backup
cp esp32_api_docker/docker-compose.yml esp32_api_docker/docker-compose.yml.backup

# Verificar que no hay cambios locales importantes
git status
git stash  # Si hay cambios locales que quieres conservar

# SIEMPRE trabajar desde esp32_api_docker/ para comandos Docker
cd esp32_api_docker
docker-compose ps    # Verificar estado
docker-compose logs  # Ver logs
```

**🔍 Verificación Post-Actualización:**
```bash
# Verificar versión actualizada
curl http://localhost:8000/

# Verificar que la configuración se mantuvo
curl http://localhost:8000/config/custom/configurations

# Verificar logs por errores (desde esp32_api_docker/)
cd esp32_api_docker
docker-compose logs esp32-api | grep -i error

# Test completo de funcionalidad
curl http://localhost:8000/health
curl http://localhost:8000/data/
curl http://localhost:8000/schedule/
```

#### 9. Solución de Problemas Específicos RISC-V

**Puerto Serial no detectado:**
```bash
# Instalar drivers USB adicionales
sudo apt install -y linux-modules-extra-$(uname -r)

# Verificar módulos USB cargados
lsmod | grep usbserial
lsmod | grep ftdi_sio

# Cargar módulos manualmente si es necesario
sudo modprobe usbserial
sudo modprobe ftdi_sio
```

**Problemas de rendimiento:**
```bash
# Monitorear recursos del sistema
htop
iostat -x 1

# Ajustar swap si es necesario
sudo swapon --show
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Errores de compilación de dependencias:**
```bash
# Instalar herramientas de compilación adicionales
sudo apt install -y gcc-riscv64-linux-gnu
sudo apt install -y python3-wheel python3-setuptools

# Usar pre-compiled wheels cuando sea posible
pip install --only-binary=all -r requirements.txt
```

## ✨ Nuevas Características

### 🕐 Schedule Diario Automático
- **Apagado programado**: Configura hora de inicio y duración (máx 8 horas)
- **Override manual**: Los comandos manuales anulan el schedule hasta el siguiente día
- **Configuración flexible**: Habilitar/deshabilitar sin perder configuración
- **Zona horaria local**: Manejo automático desde la OrangePi
- **Límite de seguridad**: Máximo 8 horas de apagado continuo

### � Sistema de Configuraciones Personalizadas
- **Guardar configuraciones**: Crear perfiles específicos para diferentes tipos de baterías
- **Aplicar con un clic**: Cambiar todos los parámetros del ESP32 instantáneamente
- **Exportar/Importar**: Transferir configuraciones entre diferentes Orange Pi
- **Validación automática**: Verificación de rangos y compatibilidad
- **Gestión completa**: Crear, editar, eliminar y organizar configuraciones
- **Portabilidad**: Archivos JSON legibles y transferibles

### �🛡️ Seguridad Mejorada
- **Validación ESP32**: Límite de 8 horas implementado en firmware
- **Rate limiting**: Protección contra abuse de API
- **Prioridades**: Toggle manual > Schedule diario > LVD/LVR

## 📡 Uso de la API

### Obtener todos los datos
```bash
curl http://localhost:8000/data/
```

### Configurar parámetro del ESP32
```bash
curl -X PUT http://localhost:8000/config/bulkVoltage \
  -H "Content-Type: application/json" \
  -d '{"value": 14.5}'
```

### ⏰ **NUEVO**: Configurar Schedule Diario
```bash
# Configurar apagado de 12:00 AM a 6:00 AM (6 horas)
curl -X PUT http://localhost:8000/schedule/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "start_time": "00:00",
    "duration_seconds": 21600
  }'
```

### ⚡ Toggle Manual (anula schedule)
```bash
# Apagar por 30 minutos (anula schedule hasta mañana)
curl -X POST http://localhost:8000/actions/toggle_load \
  -H "Content-Type: application/json" \
  -d '{"hours": 0, "minutes": 30, "seconds": 0}'
```

### 📊 Estado del Schedule
```bash
# Ver estado actual del schedule
curl http://localhost:8000/schedule/

# Ver estado completo (ESP32 + Schedule)
curl http://localhost:8000/actions/status
```

### 📋 **NUEVO**: Configuraciones Personalizadas
```bash
# Listar todas las configuraciones guardadas
curl http://localhost:8000/config/custom/configurations

# Guardar configuración actual con un nombre
curl -X POST http://localhost:8000/config/custom/configurations/Batería%20Litio%20100Ah \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 100.0,
    "isLithium": true,
    "thresholdPercentage": 2.0,
    "maxAllowedCurrent": 10000.0,
    "bulkVoltage": 14.4,
    "absorptionVoltage": 14.4,
    "floatVoltage": 13.6,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 1
  }'

# Aplicar configuración guardada al ESP32
curl -X POST http://localhost:8000/config/custom/configurations/Batería%20Litio%20100Ah/apply

# Exportar todas las configuraciones para backup
curl http://localhost:8000/config/custom/configurations/export

# Importar configuraciones desde archivo JSON
curl -X POST http://localhost:8000/config/custom/configurations/import \
  -H "Content-Type: application/json" \
  -d '{
    "configurations_data": "{\"Nueva Config\":{\"batteryCapacity\":150,...}}",
    "overwrite_existing": false
  }'

# Obtener información del sistema de configuraciones
curl http://localhost:8000/config/custom/configurations/info
```

### 🔄 Gestión de Override
```bash
# Limpiar override manual (reactivar schedule)
curl -X POST http://localhost:8000/schedule/clear_override

# Habilitar/deshabilitar schedule
curl -X POST http://localhost:8000/schedule/enable
curl -X POST http://localhost:8000/schedule/disable
```

## 📊 Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 🆕 Nuevos Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/schedule/` | GET | Estado del schedule diario |
| `/schedule/config` | PUT | Configurar schedule |
| `/schedule/enable` | POST | Habilitar schedule |
| `/schedule/disable` | POST | Deshabilitar schedule |
| `/schedule/clear_override` | POST | Limpiar override manual |
| `/schedule/info` | GET | Info sobre capacidades |
| `/config/custom/configurations` | GET | Listar configuraciones guardadas |
| `/config/custom/configurations` | POST | Guardar múltiples configuraciones |
| `/config/custom/configurations/{name}` | POST | Guardar configuración individual |
| `/config/custom/configurations/{name}` | GET | Obtener configuración específica |
| `/config/custom/configurations/{name}` | DELETE | Eliminar configuración |
| `/config/custom/configurations/{name}/apply` | POST | Aplicar configuración al ESP32 |
| `/config/custom/configurations/validate` | POST | Validar configuración |
| `/config/custom/configurations/export` | GET | Exportar a JSON |
| `/config/custom/configurations/import` | POST | Importar desde JSON |
| `/config/custom/configurations/info` | GET | Info del sistema |

## 🧪 Tests

```bash
# Tests básicos
pytest tests/

# Tests específicos de schedule
python test_schedule_functionality.py

# Tests por categoría
./test_by_category.sh schedule
```

## 📁 Estructura del Proyecto

```
esp32_api/
├── main.py                    # FastAPI app principal
├── models/                    # Modelos Pydantic
│   ├── esp32_data.py         # Modelos ESP32
│   ├── schedule_models.py    # 🆕 Modelos Schedule
│   └── custom_configurations.py # 🆕 Modelos Configuraciones
├── services/                  # Lógica de negocio
│   ├── esp32_manager.py
│   ├── schedule_manager.py   # 🆕 Gestión Schedule
│   └── custom_configuration_manager.py # 🆕 Gestión Configuraciones
├── api/                       # Endpoints REST
│   ├── data.py
│   ├── config.py             # 🔄 Actualizado con Configuraciones
│   ├── actions.py            # 🔄 Actualizado con Schedule
│   └── schedule.py           # 🆕 Endpoints Schedule
├── core/                      # Configuración
├── tests/                     # Tests automatizados
│   ├── test_custom_configurations.py # 🆕 Tests Configuraciones
│   └── test_schedule.py      # 🆕 Tests Schedule
├── logs/                      # Archivos de log
├── configuraciones.json      # 🆕 Archivo de configuraciones personalizadas
├── demo_configuraciones.py   # 🆕 Script de demostración
└── README_CONFIGURACIONES.md # 🆕 Documentación detallada
```

## ⚙️ Configuración Schedule

### Configuración por Defecto
```json
{
  "enabled": true,
  "start_time": "00:00",
  "duration_seconds": 21600,
  "max_duration_hours": 8
}
```

### Ejemplos de Configuración

```bash
# Schedule nocturno (12 AM - 6 AM)
{
  "enabled": true,
  "start_time": "00:00",
  "duration_seconds": 21600
}

# Schedule diurno (1 PM - 5 PM) 
{
  "enabled": true,
  "start_time": "13:00", 
  "duration_seconds": 14400
}

# Schedule personalizado (10 PM - 2 AM = 4 horas)
{
  "enabled": true,
  "start_time": "22:00",
  "duration_seconds": 14400
}
```

## 🔗 Endpoints Principales

### ESP32 Core
- `GET /data/` - Todos los datos del ESP32
- `PUT /config/{parameter}` - Configurar parámetro
- `GET /health` - Estado de la API

### Control de Carga
- `POST /actions/toggle_load` - Toggle manual (anula schedule)
- `POST /actions/cancel_temp_off` - Cancelar apagado temporal
- `GET /actions/status` - Estado acciones + schedule

### 🆕 Schedule Diario
- `GET /schedule/` - Estado del schedule
- `PUT /schedule/config` - Configurar schedule
- `POST /schedule/clear_override` - Reactivar schedule
- `GET /schedule/info` - Información de capacidades

## 📐 Comportamiento del Sistema

### Prioridades (Mayor a Menor)
1. **LVD/LVR** (Low Voltage Disconnect/Recovery)
2. **Toggle Manual** (8 horas máx)
3. **Schedule Diario** (8 horas máx)
4. **Estado Normal**

### Interacciones Importantes

| Situación | Comportamiento |
|-----------|----------------|
| Schedule activo + Toggle manual | Toggle anula schedule hasta mañana |
| Schedule activo + LVD | LVD tiene prioridad, schedule se pausa |
| Override activo + Schedule | Schedule no funciona hasta clear_override |
| Reinicio OrangePi | Schedule reinicia con configuración por defecto |
| Duración > 8 horas | Limitado automáticamente a 8 horas |

## 🛡️ Medidas de Seguridad

### En ESP32 (.ino)
- ✅ Límite máximo: 28800 segundos (8 horas)
- ✅ Validación de comandos recibidos
- ✅ Control de tiempo en firmware

### En API (OrangePi)
- ✅ Validación de parámetros
- ✅ Rate limiting por tipo de operación
- ✅ Manejo de timeouts en comunicación
- ✅ No persistencia (no sobrevive reinicios)

## 🚨 Solución de Problemas

### Problemas Generales

#### Schedule no funciona
```bash
# Verificar estado
curl http://localhost:8000/schedule/

# Verificar si hay override activo
curl http://localhost:8000/actions/status

# Limpiar override manual
curl -X POST http://localhost:8000/schedule/clear_override
```

#### Toggle manual no anula schedule
```bash
# Verificar que el toggle se ejecutó correctamente
curl http://localhost:8000/actions/status

# El override debería estar activo
{
  "schedule": {
    "manual_override_active": true
  }
}
```

#### ESP32 no responde a comandos
```bash
# Verificar conexión
curl http://localhost:8000/health

# Ver logs
tail -f logs/esp32_api.log
```

#### 🔧 **CRÍTICO: Protocolo de Comunicación ESP32 (Agosto 2025)**

**PROBLEMA IDENTIFICADO:** Los comandos SET (POST/PUT) fallan con error 500 o "Respuesta inválida del ESP32: None"

**CAUSA RAÍZ:** 
- Los comandos `GET_DATA` devuelven JSON completo
- Los comandos `SET_*` devuelven texto plano: `"OK:parameter updated to value"`
- La API originalmente esperaba JSON para todos los comandos

**SÍNTOMAS:**
```bash
# ❌ FALLA: Endpoints de configuración
curl -X PUT http://localhost:8000/config/bulkVoltage -H "Content-Type: application/json" -d '{"value": 14.6}'
# Error: "Respuesta inválida del ESP32: None"

# ✅ FUNCIONA: Endpoint de datos
curl http://localhost:8000/data/
# Devuelve JSON completo
```

**SOLUCIÓN IMPLEMENTADA:**
- **Archivo:** `services/esp32_manager.py`
- **Método nuevo:** `_send_command_and_read_text()` para respuestas de texto plano
- **Método modificado:** `set_parameter()` usa texto plano en lugar de JSON
- **Validación:** Busca `"OK:"` o `"ERROR:"` en respuestas de texto

**CÓDIGO CRÍTICO:**
```python
# ✅ CORRECTO - Para comandos SET
response = await self._send_command_and_read_text(command, timeout=4.0)
if response and response.startswith("OK:"):
    result["success"] = True

# ✅ CORRECTO - Para comandos GET_DATA  
response = await self._get_json_with_strategies("CMD:GET_DATA")
if response and self._is_json_complete(response):
    return response
```

**VERIFICACIÓN DEL FIX:**
```bash
# ✅ Debe funcionar después del fix
curl -X PUT http://localhost:8000/config/bulkVoltage -H "Content-Type: application/json" -d '{"value": 14.6}'
# Respuesta esperada: {"success":true,"esp32_response":"OK:bulkVoltage updated to 14.6"}
```

**⚠️ IMPORTANTE PARA FUTURO:**
1. **NO mezclar** métodos JSON y texto plano en el mismo endpoint
2. Los comandos SET siempre usan `_send_command_and_read_text()`
3. Los comandos GET siempre usan `_get_json_with_strategies()`
4. Si cambias el firmware ESP32, mantén consistencia en el protocolo

---

### 🍊 Problemas Específicos Orange Pi R2S / RISC-V

#### Puerto Serial no funciona
```bash
# Verificar dispositivos conectados
dmesg | grep tty
lsusb

# Verificar permisos
ls -la /dev/ttyUSB*
sudo chmod 666 /dev/ttyUSB0

# Verificar si el usuario está en el grupo correcto
groups $USER | grep dialout

# Agregar usuario al grupo si no está
sudo usermod -aG dialout $USER
newgrp dialout
```

#### Docker no inicia en RISC-V
```bash
# Verificar estado de Docker
sudo systemctl status docker

# Verificar arquitectura soportada
docker version
docker info | grep Architecture

# Reiniciar Docker si es necesario
sudo systemctl restart docker
```

#### Problemas de memoria/rendimiento
```bash
# Verificar uso de memoria
free -h
cat /proc/meminfo

# Verificar procesos que más consumen
top -o %MEM

# Optimizar configuración Docker para RISC-V
# En docker-compose.yml:
mem_limit: 1024m        # Reducir si hay poca RAM
cpus: 2.0              # Reducir si hay pocos cores
```

#### Errores de compilación Python
```bash
# Limpiar cache de pip
pip cache purge

# Instalar dependencias de compilación
sudo apt install -y python3-dev build-essential

# Usar wheels pre-compilados
pip install --only-binary=all package_name

# Alternativa: instalar desde repositorios del sistema
sudo apt install python3-numpy python3-scipy python3-pandas
```

#### ESP32 se desconecta frecuentemente
```bash
# Verificar alimentación USB
dmesg | grep -i usb | tail -10

# Verificar configuración de energía USB
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{power/control}="on"' | sudo tee /etc/udev/rules.d/99-usb-power.rules
sudo udevadm control --reload-rules

# Deshabilitar suspensión USB
echo 'SUBSYSTEM=="usb", ACTION=="add", ATTR{power/autosuspend}="-1"' | sudo tee -a /etc/udev/rules.d/99-usb-power.rules
```

#### La API es lenta en Orange Pi
```bash
# Configurar variables de optimización
export OMP_NUM_THREADS=4
export PYTHONTHREADS=4
export UV_THREADPOOL_SIZE=4

# Usar configuración optimizada en docker-compose.yml
environment:
  - OMP_NUM_THREADS=4
  - MALLOC_ARENA_MAX=4
  - PYTHONTHREADS=4
  - UV_THREADPOOL_SIZE=4
  
# Verificar si hay swap disponible
sudo swapon --show

# Crear swap si es necesario (ayuda con la memoria)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

#### Problemas de red/conectividad
```bash
# Verificar configuración de red
ip addr show
ping 8.8.8.8

# Verificar puertos abiertos
sudo netstat -tlnp | grep :8000

# Verificar firewall
sudo ufw status

# Abrir puerto si es necesario
sudo ufw allow 8000/tcp
```

### 🔧 Configuraciones Adicionales para Orange Pi R2S

#### Optimización del Sistema Operativo
```bash
# Ajustar parámetros del kernel para mejor rendimiento
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max=16777216' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max=16777216' | sudo tee -a /etc/sysctl.conf

# Aplicar cambios
sudo sysctl -p
```

#### Configuración de Red Estática (Opcional)
```bash
# Editar configuración de red
sudo nano /etc/netplan/99-orangepi-static.yaml

# Contenido de ejemplo:
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.100/24
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]

# Aplicar configuración
sudo netplan apply
```

#### Inicio Automático con systemd
```bash
# Crear servicio systemd
sudo nano /etc/systemd/system/esp32-api.service

# Contenido del servicio:
[Unit]
Description=ESP32 Solar Charger API
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/home/orangepi/API_cargador_gel_litio-
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=orangepi
Group=orangepi

[Install]
WantedBy=multi-user.target

# Habilitar servicio
sudo systemctl enable esp32-api.service
sudo systemctl start esp32-api.service
```

## 📞 Soporte

- **Documentación completa**: `/docs`
- **Información del sistema**: `/system/info`
- **Estado de conexión**: `/data/status/connection`
- **Rate limiting stats**: `/rate-limit/stats`
- **Configuraciones personalizadas**: `README_CONFIGURACIONES.md`

### 🍊 Recursos Adicionales para Orange Pi R2S

- **Scripts de instalación automática**: `install_orangepi.sh`, `quick_setup.sh`
- **Configuración de crontab**: `crontab/setup_api_crontab.sh`
- **Tests específicos**: `test_by_category.sh`, `test_schedule_functionality.sh`
- **Debugging**: `debug_api_issues.sh`
- **Optimización Docker**: `docker-compose.yml` con configuraciones multi-CPU

#### 🚀 Scripts Incluidos

| Script | Descripción | Uso |
|--------|-------------|-----|
| `quick_setup.sh` | **Actualización completa automática** | `./quick_setup.sh` |
| `install_orangepi.sh` | Instalación inicial en Orange Pi | `sudo ./install_orangepi.sh` |
| `start_api.sh` | Iniciar API manualmente | `./start_api.sh` |
| `stop_api.sh` | Detener API manualmente | `./stop_api.sh` |
| `debug_api_issues.sh` | Diagnóstico de problemas | `./debug_api_issues.sh` |
| `test_by_category.sh` | Tests por categoría | `./test_by_category.sh all` |

#### 📝 Ejemplo de Flujo de Actualización Diario

```bash
# 1. Verificar si hay actualizaciones disponibles
git fetch origin main
git status

# 2. Si hay actualizaciones, usar script automático
./quick_setup.sh

# 3. Verificar que todo funciona
curl http://localhost:8000/health

# 4. Opcional: ejecutar tests para verificar funcionalidad
./test_by_category.sh api
```

---

## 🔄 Migración desde Versión Anterior

Si actualizas desde una versión sin schedule o configuraciones personalizadas:

### ✅ **Compatibilidad Completa**
1. **Los endpoints existentes siguen funcionando igual**
2. **Toggle manual ahora anula schedule** (nuevo comportamiento)
3. **Nuevos endpoints bajo `/schedule/` y `/config/configurations/`**
4. **Configuración por defecto**: Schedule habilitado de 12 AM - 6 AM
5. **Configuraciones personalizadas**: Sistema completamente nuevo

### 🚀 **Pasos de Migración Recomendados**

```bash
# 1. Hacer backup completo antes de migrar
cp -r API_cargador_gel_litio- API_cargador_gel_litio-backup-$(date +%Y%m%d)

# 2. Usar script de actualización automática
cd API_cargador_gel_litio-
./quick_setup.sh

# 3. Verificar nuevas funcionalidades
curl http://localhost:8000/schedule/        # Nuevo sistema de schedule
curl http://localhost:8000/config/custom/configurations  # Nuevo sistema de configuraciones

# 4. Crear configuraciones iniciales basadas en tu setup actual
curl http://localhost:8000/data/  # Ver configuración actual
# Usar estos datos para crear tu primera configuración personalizada
```

### 📋 **No se requieren cambios en frontend existente**
- Todos los endpoints anteriores mantienen la misma funcionalidad
- Las nuevas características son adicionales y opcionales
- El comportamiento por defecto es compatible con versiones anteriores

## 🏆 Mejores Prácticas para Mantenimiento

### 📅 **Rutina Diaria**
```bash
# Verificar estado del sistema
curl http://localhost:8000/health
docker-compose ps

# Ver logs recientes por errores
docker-compose logs --tail=50 esp32-api | grep -i error
```

### 📅 **Rutina Semanal**
```bash
# Verificar actualizaciones disponibles
git fetch origin main
git status

# Limpiar recursos Docker innecesarios
docker system prune -f

# Backup de configuraciones
cp configuraciones.json backups/configuraciones-$(date +%Y%m%d).json
```

### 📅 **Rutina Mensual**
```bash
# Actualizar sistema operativo
sudo apt update && sudo apt upgrade -y

# Verificar espacio en disco
df -h

# Revisar logs del sistema
journalctl -u esp32-api --since "1 month ago" | grep -i error

# Ejecutar tests completos
./test_by_category.sh all
```

### 🔐 **Seguridad y Backup**
```bash
# Backup completo mensual
tar -czf esp32-api-backup-$(date +%Y%m%d).tar.gz \
    configuraciones.json \
    docker-compose.yml \
    logs/ \
    data/

# Verificar permisos de archivos críticos
ls -la configuraciones.json docker-compose.yml

# Rotar logs antiguos
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 📚 Documentación Adicional

- **📋 Configuraciones Personalizadas**: [`README_CONFIGURACIONES.md`](README_CONFIGURACIONES.md)
- **🐳 Docker y Contenedores**: [`docker-compose.yml`](docker-compose.yml)
- **🧪 Tests y Validación**: [`tests/`](tests/)
- **🔧 Scripts de Automatización**: [`*.sh`](*.sh)

**💡 Tip**: Mantén siempre un backup reciente de `configuraciones.json` antes de cualquier actualización importante.

---

## 🔄 Gestión de Actualizaciones

### 📦 Actualización Automática (Recomendado)

```bash
# Actualización completa con un solo comando
./quick_setup.sh

# Lo que hace automáticamente:
# 1. Git pull para obtener últimos cambios
# 2. Backup automático de configuraciones
# 3. Detener contenedores actuales
# 4. Reconstruir imagen Docker con cambios
# 5. Levantar servicios actualizados
# 6. Verificar estado de la API
# 7. Mostrar logs de verificación
```

### 🛠️ Actualización Manual (Paso a Paso)

```bash
# 1. Hacer backup de configuraciones importantes
cp configuraciones.json configuraciones.json.backup-$(date +%Y%m%d_%H%M%S)
cp docker-compose.yml docker-compose.yml.backup

# 2. Verificar estado actual antes de actualizar
git status
docker-compose ps

# 3. Obtener últimos cambios del repositorio
git pull origin main

# 4. Detener servicios actuales
docker-compose down

# 5. Limpiar imágenes antiguas (opcional, ahorra espacio)
docker system prune -f

# 6. Reconstruir imagen con los nuevos cambios
docker-compose build --no-cache esp32-api

# 7. Levantar servicios actualizados
docker-compose up -d

# 8. Verificar que todo funciona correctamente
docker-compose logs -f esp32-api
```

### 🚨 Resolución de Problemas en Actualizaciones

#### Error: "Contenedor no se detiene"
```bash
# Forzar detención de contenedores
docker-compose kill
docker-compose rm -f

# Limpiar recursos Docker
docker system prune -f

# Intentar nuevamente
docker-compose up --build -d
```

#### Error: "Git pull falló por cambios locales"
```bash
# Ver qué archivos tienen cambios
git status

# Guardar cambios locales temporalmente
git stash

# Actualizar código
git pull origin main

# Recuperar cambios locales si son necesarios
git stash pop
```

#### Error: "Configuraciones perdidas después de actualizar"
```bash
# Restaurar configuraciones desde backup
cp configuraciones.json.backup configuraciones.json

# Verificar que se restauraron
curl http://localhost:8000/config/configurations

# Reiniciar API para cargar configuraciones
docker-compose restart esp32-api
```

#### Error: "Nueva versión no inicia"
```bash
# Ver logs detallados del error
docker-compose logs esp32-api

# Verificar imagen construida correctamente
docker images | grep esp32-solar-api

# Reconstruir imagen desde cero
docker-compose build --no-cache --pull

# Si persiste el error, volver a versión anterior
git log --oneline -5  # Ver últimos commits
git checkout HEAD~1   # Volver al commit anterior
docker-compose build --no-cache
docker-compose up -d
```

### 📋 Checklist de Actualización

**Antes de Actualizar:**
- [ ] ✅ Hacer backup de `configuraciones.json`
- [ ] ✅ Verificar que la API actual funciona: `curl http://localhost:8000/health`
- [ ] ✅ Anotar versión actual: `git log --oneline -1`
- [ ] ✅ Verificar espacio en disco: `df -h`

---

## 📋 Historial de Cambios Críticos

### 🚨 **Agosto 2025 - Fix Protocolo Comunicación ESP32**

**Problema:** Comandos SET (POST/PUT) fallaban con error 500 - "Respuesta inválida del ESP32: None"

**Solución:** 
- **Archivo modificado:** `services/esp32_manager.py`
- **Cambios:** Separación de protocolos JSON vs texto plano
- **Nuevo método:** `_send_command_and_read_text()` para comandos SET
- **Resultado:** 100% endpoints POST/PUT funcionando

**Detalles técnicos:**
```diff
# ❌ ANTES - Todos los comandos esperaban JSON
response = await self._get_json_with_strategies(command, timeout=4.0)

# ✅ DESPUÉS - Comandos SET usan texto plano
response = await self._send_command_and_read_text(command, timeout=4.0)
```

**Archivos afectados:**
- `services/esp32_manager.py` - Protocolo de comunicación
- `README.md` - Documentación del fix

**Testing realizado:**
- ✅ Endpoints GET: `/data/` funcionando
- ✅ Endpoints PUT: `/config/bulkVoltage`, `/config/batteryCapacity`, `/config/thresholdPercentage`
- ✅ Sin regresiones en funcionalidad existente

**Nota crítica:** Este fix es fundamental para el correcto funcionamiento de todos los endpoints de configuración. No modificar sin entender completamente la diferencia entre protocolos JSON y texto plano del ESP32.

---

**Durante la Actualización:**
- [ ] ✅ Ejecutar `./quick_setup.sh` o proceso manual
- [ ] ✅ Verificar que no hay errores en la construcción
- [ ] ✅ Esperar a que todos los servicios estén "healthy"

**Después de Actualizar:**
- [ ] ✅ Verificar API: `curl http://localhost:8000/health`
- [ ] ✅ Verificar ESP32: `curl http://localhost:8000/data/`
- [ ] ✅ Verificar configuraciones: `curl http://localhost:8000/config/configurations`
- [ ] ✅ Verificar schedule: `curl http://localhost:8000/schedule/`
- [ ] ✅ Revisar logs por errores: `docker-compose logs esp32-api | grep -i error`

### 🔧 Configuración de Actualizaciones Automáticas

#### Cron Job para Actualizaciones Nocturnas (Opcional)
```bash
# Editar crontab
crontab -e

# Agregar línea para actualización diaria a las 3 AM
0 3 * * * cd /home/orangepi/API_cargador_gel_litio- && ./quick_setup.sh >> /var/log/esp32-api-update.log 2>&1

# Verificar cron job
crontab -l
```

#### Script de Monitoreo de Actualizaciones
```bash
# Crear script de verificación
nano check_updates.sh

#!/bin/bash
cd /home/orangepi/API_cargador_gel_litio-
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ $LOCAL != $REMOTE ]; then
    echo "Nueva actualización disponible"
    echo "Local: $LOCAL"
    echo "Remote: $REMOTE"
    # Opcional: ejecutar actualización automática
    # ./quick_setup.sh
else
    echo "Sistema actualizado"
fi

# Hacer ejecutable
chmod +x check_updates.sh

# Ejecutar manualmente para verificar
./check_updates.sh
```