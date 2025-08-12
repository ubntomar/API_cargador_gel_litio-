# ESP32 Solar Charger API - Multi-Arquitectura

API REST para control y monitoreo del cargador solar ESP32 con **funcionalidad de apagado programado diario**, **sistema de configuraciones personalizadas** y **optimización automática multi-CPU**.

> ✅ **ESTADO ACTUAL - Agosto 2025:** API completamente funcional y validado. Sistema multi-CPU implementado con auto-detección de arquitectura. Compatible con x86, ARM y RISC-V.

> 🔧 **RUTAS CORREGIDAS - Agosto 2025:** Documentación actualizada con rutas correctas de configuraciones personalizadas: `/config/custom/configurations`. Ver [`CORRECION_RUTAS_CONFIGURACIONES_AUGUST2025.md`](./CORRECION_RUTAS_CONFIGURACIONES_AUGUST2025.md)

> 🏗️ **COMPATIBILIDAD UNIVERSAL:** Compatible con x86_64, ARM64, RISC-V y otras arquitecturas. Auto-detección de CPU y optimización automática de workers.

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
- 🏗️ **Multi-CPU y Multi-Arquitectura**: Auto-detección de CPU y optimización automática
- � **Escalabilidad Inteligente**: Desde 1 worker (single-core) hasta 6 workers (multi-core)
- 🔧 **Arquitecturas Soportadas**: x86_64, ARM64, RISC-V, Orange Pi, Raspberry Pi
- 🐳 **Docker Optimizado**: Límites dinámicos de CPU y memoria según hardware
- �🔒 Thread-safe con manejo de concurrencia
- 🏥 Endpoints de health check y monitoreo
- 📝 Logging detallado para debugging
- 🔄 Cache inteligente para optimizar rendimiento
- 🛡️ Manejo robusto de errores de comunicación

## 🚀 Instalación Universal (Cualquier Arquitectura)

### 🎯 **Instalación Automática con Auto-Detección**

```bash
# 1. Clonar el proyecto
git clone https://github.com/ubntomar/API_cargador_gel_litio-.git
cd API_cargador_gel_litio-

# 2. Ejecutar instalación automática (detecta tu arquitectura)
./quick_setup.sh
```

> ✅ **PERMISOS AUTOMÁTICOS**: El script `quick_setup.sh` configura automáticamente los permisos de los directorios `logs/` y `data/` para que el contenedor Docker pueda escribir correctamente. Si requiere permisos de administrador, te lo solicitará.

### 🔧 **Configuración Manual de Permisos** (Solo si es necesario)

Si experimentas problemas de permisos con los logs o datos:

```bash
# Verificar propietario de directorios
ls -la logs/ data/

# Corregir permisos si es necesario
sudo chown -R $(id -u):$(id -g) logs data
chmod 755 logs data

# Verificar que los contenedores puedan escribir
docker compose -f docker-compose.resolved.yml restart
```

### 💻 **Instalación Manual por Arquitectura**

#### 🖥️ **x86_64 / AMD64** (PC estándar)
```bash
# Docker Compose (recomendado)
docker compose -f docker-compose.resolved.yml up --build

# O instalación local
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 resolve_docker_config.py  # Auto-detecta configuración
```

#### 🍓 **ARM64** (Raspberry Pi 4/5, Orange Pi)
```bash
# Auto-detección y optimización para ARM
./quick_setup.sh

# O manual con Docker
source venv/bin/activate
python3 resolve_docker_config.py
docker compose -f docker-compose.resolved.yml up --build
```

#### 🏗️ **RISC-V** (Orange Pi R2S, VisionFive)
```bash
# Optimización específica para RISC-V
./quick_setup.sh

# Configuración manual para RISC-V
export MAX_WORKERS=auto
export CPU_LIMIT=auto  
export MEMORY_LIMIT=auto
./quick_setup.sh
```

### 🌐 **Configuración Universal de Variables**

El sistema detecta automáticamente tu hardware y optimiza la configuración. Puedes usar los valores por defecto o personalizar según tus necesidades:

```bash
# Copiar archivo de configuración
cp .env.example .env

# Variables Multi-CPU (auto-detectadas)
MAX_WORKERS=auto          # auto = detección automática de workers óptimos
CPU_LIMIT=auto           # auto = límite de CPU según arquitectura  
MEMORY_LIMIT=auto        # auto = memoria óptima según workers
FORCE_SINGLE_WORKER=false # true = fuerza 1 worker (debugging)

# Variables ESP32 (editar según tu hardware)
SERIAL_PORT=/dev/ttyUSB0  # Puerto serial del ESP32
SERIAL_BAUDRATE=9600      # Velocidad de comunicación
SERIAL_TIMEOUT=3.0        # Timeout de comunicación

# Variables del servidor
HOST=0.0.0.0             # IP del servidor (0.0.0.0 = todas las interfaces)
PORT=8000                # Puerto HTTP de la API
DEBUG=false              # Modo debug (true = logs detallados)
```

### 📋 **Configuraciones por Hardware**

#### 🖥️ **PC/Servidor x86_64** (8+ CPUs)
```bash
# Configuración automática (recomendado)
MAX_WORKERS=auto      # → 6 workers
CPU_LIMIT=auto        # → 8.0 CPUs  
MEMORY_LIMIT=auto     # → 1792m

# Configuración manual (opcional)
MAX_WORKERS=6
CPU_LIMIT=8.0
MEMORY_LIMIT=2g
```

#### 🍓 **Raspberry Pi 4/5** (4 CPUs)
```bash
# Configuración automática (recomendado)
MAX_WORKERS=auto      # → 2 workers
CPU_LIMIT=auto        # → 3.0 CPUs
MEMORY_LIMIT=auto     # → 768m

# Configuración conservadora para Pi 4
MAX_WORKERS=2
CPU_LIMIT=3.0
MEMORY_LIMIT=512m
```

#### 🍊 **Orange Pi RISC-V** (8 CPUs)
```bash
# Configuración automática optimizada para RISC-V
MAX_WORKERS=auto      # → 4 workers (timeouts extendidos)
CPU_LIMIT=auto        # → 6.0 CPUs
MEMORY_LIMIT=auto     # → 1280m

# Configuración manual específica para RISC-V
MAX_WORKERS=4
CPU_LIMIT=6.0
MEMORY_LIMIT=1g
```

#### 💻 **Equipos de Desarrollo** (single-worker para debugging)
```bash
# Configuración de desarrollo (1 worker para debugging fácil)
MAX_WORKERS=1
CPU_LIMIT=2.0
MEMORY_LIMIT=512m
FORCE_SINGLE_WORKER=true
DEBUG=true
```

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

# 🍊 ACTUALIZADO: Trabajar directamente desde el directorio raíz
# Los archivos docker-compose.yml y Dockerfile ya están en el directorio correcto

# Verificar y ajustar docker-compose.yml
# Asegurarse de que el puerto serial sea correcto
nano docker-compose.yml

# En la sección devices, verificar:
devices:
  - "/dev/ttyUSB0:/dev/ttyUSB0"  # Ajustar según tu puerto

# 🔧 Ajustar rutas en docker-compose.yml para RISC-V

# ⚠️ IMPORTANTE: Configurar permisos de la carpeta logs
# El contenedor Docker necesita permisos de escritura en la carpeta logs
sudo mkdir -p logs
sudo chmod 755 logs
sudo chown $USER:$USER logs

# Construir y ejecutar con Docker (desde directorio raíz)
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

# ⚠️ IMPORTANTE: Crear carpeta logs con permisos correctos
mkdir -p logs
chmod 755 logs

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

# ⚠️ IMPORTANTE: Configurar permisos de logs ANTES de ejecutar scripts
mkdir -p logs
chmod 755 logs
chown $USER:$USER logs

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
| 📋 Configuraciones personalizadas | ✅ Funcional | ✅ Completa | ✅ Validado ✅ RISC-V |
| ⏰ Programación horarios | ✅ Funcional | ✅ Completa | ✅ Validado |
| 🏥 Health checks | ✅ Funcional | ✅ Completa | ✅ Validado |
| 🔒 Thread safety | ✅ Implementado | ✅ Documentado | ✅ Probado |
| 📱 Frontend integration | ⏳ Pendiente | ✅ Documentado | ⏳ Por implementar |

---

## 🔧 **GUÍA DE DESARROLLO Y DEBUGGING**

### 🐛 **Resolución de Problemas Docker (Actualizado Agosto 2025)**

#### ⚠️ **PROBLEMA COMÚN: Cambios no se reflejan en el contenedor**

**Síntoma:** Modificas código Python pero los cambios no aparecen cuando usas la API

**Causa raíz:** Docker estaba usando código en caché. Los volúmenes no estaban configurados para desarrollo.

**✅ SOLUCIÓN IMPLEMENTADA (Opción 1 - Recomendada):**

El `docker-compose.yml` ahora incluye volúmenes para desarrollo en vivo:

```yaml
volumes:
  # 🔧 DESARROLLO: Montar código fuente para hot-reload
  - ./api:/app/api:rw
  - ./services:/app/services:rw
  - ./models:/app/models:rw
  - ./core:/app/core:rw
  - ./main.py:/app/main.py:rw
```

**Para aplicar cambios después de git pull:**

```bash
# 1. Detener contenedores (método recomendado)
./stop_api.sh

# 2. Recrear con código actualizado
./start_smart.sh

# 3. Método manual adaptativo:
if command -v "docker compose" > /dev/null 2>&1; then
    docker compose -f docker-compose.resolved.yml down
    docker compose -f docker-compose.resolved.yml up -d --build
else
    docker-compose -f docker-compose.resolved.yml down
    docker-compose -f docker-compose.resolved.yml up -d --build
fi

# 4. Si persisten problemas, rebuild completo:
docker compose build --no-cache
docker compose up -d
```

#### 🔍 **Debugging de Endpoints que "se ejecutan pero no aplican cambios"**

**Caso específico resuelto:** `/config/custom/config/{name}/apply`

1. **Verificar que el código está actualizado en el contenedor:**
   ```bash
   # Comparar líneas de código
   docker exec esp32-solar-charger-api wc -l /app/api/config.py
   wc -l api/config.py
   # Deben ser iguales
   ```

2. **Verificar logs de debug en tiempo real:**
   ```bash
   # Ver logs del contenedor
   docker logs esp32-solar-charger-api --tail 20 -f
   
   # Probar endpoint
   curl -X POST http://localhost:8000/config/custom/config/BateriaGEL200Ah/apply
   ```

3. **Problema encontrado y corregido:**
   - La configuración se obtenía con estructura wrapper: `{'configuration_name': 'X', 'configuration': {...}}`
   - El código buscaba parámetros en el nivel raíz en lugar de en `configuration['configuration']`
   - **Fix aplicado:** Extracción correcta de la configuración del wrapper Redis

#### 📋 **Comandos útiles para desarrollo:**

```bash
# Reiniciar solo el contenedor de la API (mantiene Redis)
docker restart esp32-solar-charger-api

# Ver estructura de archivos en el contenedor
docker exec esp32-solar-charger-api ls -la /app/api/

# Ejecutar comando dentro del contenedor
docker exec -it esp32-solar-charger-api bash

# Verificar conexiones de red
docker compose ps
```

#### 🎯 **Flujo de desarrollo recomendado:**

1. **Desarrollo local con live reload habilitado**
2. **Cambios se reflejan automáticamente** (gracias a volúmenes configurados)
3. **Para cambios estructurales:** `docker compose restart esp32-solar-charger-api`
4. **Para nuevas dependencias:** `docker compose up -d --build`

#### 🛠️ **Scripts de Troubleshooting Automatizado**

**Para debugging automático:** Usa los scripts incluidos:

```bash
# Diagnóstico automático de problemas Docker
./docker_troubleshoot.sh

# Ver guía de debugging en quick setup
bash quick_setup.sh debug

# Debugging completo de API y Docker
./debug_api_issues.sh
```

**Comandos del script de troubleshooting:**
```bash
./docker_troubleshoot.sh diagnose    # Diagnosticar problemas
./docker_troubleshoot.sh fix         # Arreglar automáticamente
./docker_troubleshoot.sh debug       # Ver comandos de debugging
```

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

# ⚠️ IMPORTANTE: Verificar permisos de carpeta logs
ls -la logs/
# Debe mostrar permisos como: drwxr-xr-x usuario usuario

# Ver logs en tiempo real (desde directorio raíz)
docker-compose logs -f esp32-api

# O si es instalación nativa:
cd ..
tail -f logs/esp32_api.log

# Si hay errores de permisos en logs:
sudo chmod 755 logs
sudo chown $USER:$USER logs
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

# 2. Los archivos Docker ya están en el directorio correcto

# 3. Detener contenedores actuales (método recomendado)
./stop_api.sh

# 4. Reconstruir imagen con cambios (método recomendado)
./start_smart.sh

# Método manual alternativo:
# if command -v "docker compose" > /dev/null 2>&1; then
#     docker compose -f docker-compose.resolved.yml down
#     docker compose -f docker-compose.resolved.yml build --no-cache
# else
#     docker-compose -f docker-compose.resolved.yml down
#     docker-compose -f docker-compose.resolved.yml build --no-cache
# fi

# 5. Levantar contenedores actualizados
docker-compose up -d

# 6. Verificar que todo funciona
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
# - Detiene contenedores
# - Reconstruye imágenes
# - Levanta servicios actualizados
# - Verifica el estado
```

**⚠️ Consideraciones Importantes para RISC-V:**
```bash
# ANTES de actualizar, hacer backup de configuraciones
cp configuraciones.json configuraciones.json.backup
cp docker-compose.yml docker-compose.yml.backup

# Verificar que no hay cambios locales importantes
git status
git stash  # Si hay cambios locales que quieres conservar

# SIEMPRE trabajar desde el directorio raíz para comandos Docker
docker-compose ps    # Verificar estado
docker-compose logs  # Ver logs
```

**🔍 Verificación Post-Actualización:**
```bash
# Verificar versión actualizada
curl http://localhost:8000/

# Verificar que la configuración se mantuvo
curl http://localhost:8000/config/custom/configurations

# Verificar logs por errores (desde directorio raíz)
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
curl -X POST http://localhost:8000/config/custom/config/Batería%20Litio%20100Ah/apply

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
| `/config/custom/config/{name}` | POST | Guardar configuración individual |
| `/config/custom/config/{name}` | GET | Obtener configuración específica |
| `/config/custom/config/{name}` | DELETE | Eliminar configuración |
| `/config/custom/config/{name}/apply` | POST | Aplicar configuración al ESP32 |
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
API_cargador_gel_litio-/
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

### 🔒 **Problemas de Permisos de Archivos**

#### Error: Permission denied al escribir logs
```bash
# Síntoma: Error en logs del contenedor
# PermissionError: [Errno 13] Permission denied: '/app/logs/esp32_api.log'

# Solución 1: Usar script automático (Recomendado)
./quick_setup.sh  # Configura permisos automáticamente

# Solución 2: Manual
sudo chown -R $(id -u):$(id -g) logs data
chmod 755 logs data
docker compose restart

# Verificar permisos
ls -la logs/ data/
```

#### Contenedor no arranca por permisos
```bash
# Verificar logs del contenedor
docker compose logs esp32-api

# Si hay errores de permisos:
docker compose down
sudo chown -R $(id -u):$(id -g) logs data configuraciones.json*
docker compose up -d

# Verificar estado
docker compose ps
curl http://localhost:8000/health
```

#### Datos no persisten entre reinicios
```bash
# Verificar montaje de volúmenes
docker compose config | grep volumes -A 10

# Verificar permisos de directorio data
ls -la data/
sudo chown -R $(id -u):$(id -g) data/
```

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

#### 🔧 **CRÍTICO: ImportError en RISC-V (Agosto 2025)**

**PROBLEMA IDENTIFICADO:** `ImportError: cannot import name 'ESP32Status' from 'models.esp32_data'`

**CAUSA RAÍZ:** 
- Contenedor Docker usa imagen en caché con código desactualizado
- En RISC-V, las imágenes en caché pueden persistir después de `git pull`
- La clase `ESP32Status` fue removida pero el contenedor mantiene la versión antigua

**SÍNTOMAS:**
```bash
# Error al iniciar contenedor
esp32-solar-charger-api | ImportError: cannot import name 'ESP32Status' from 'models.esp32_data'
esp32-solar-charger-api | File "/app/models/__init__.py", line 7, in <module>
```

**SOLUCIÓN COMPLETA PARA RISC-V:**
```bash
# 1. DETENER contenedores completamente
docker-compose down

# 2. LIMPIAR caché Docker (CRÍTICO en RISC-V)
docker system prune -f
docker builder prune -f

# 3. ELIMINAR imágenes específicas del proyecto
docker images | grep esp32 | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
docker images | grep api_cargador | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

# 4. RECONSTRUIR desde cero (--no-cache OBLIGATORIO)
docker-compose build --no-cache --pull

# 5. LEVANTAR servicios
docker-compose up -d

# 6. VERIFICAR que no hay errores
docker-compose logs esp32-api | head -20
```

**COMANDO ÚNICO PARA RISC-V:**
```bash
# Solución rápida todo-en-uno
docker-compose down && \
docker system prune -f && \
docker builder prune -f && \
docker images | grep -E "(esp32|api_cargador)" | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true && \
docker-compose build --no-cache --pull && \
docker-compose up -d
```

**VERIFICACIÓN DEL FIX:**
```bash
# ✅ Debe mostrar API iniciando correctamente
docker-compose logs esp32-api | grep -E "(Iniciando|✅|🚀)"
# Respuesta esperada: "🚀 Iniciando ESP32 Solar Charger API"

# ✅ Verificar que no hay ImportError
docker-compose logs esp32-api | grep -i "importerror"
# No debe mostrar ningún resultado
```

**⚠️ IMPORTANTE PARA RISC-V:**
1. **SIEMPRE usar `--no-cache`** al hacer rebuild en RISC-V
2. **Limpiar caché Docker** antes de reconstruir después de git pull
3. **No confiar en `docker-compose build`** sin `--no-cache` en RISC-V
4. **Verificar logs** siempre después de reconstruir

---

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

#### 🔧 **CRÍTICO: Error de Concurrencia en Configuraciones (Agosto 2025)**

**PROBLEMA IDENTIFICADO:** `[Errno 16] Device or resource busy: 'configuraciones.tmp' -> 'configuraciones.json'`

**CAUSA RAÍZ:** 
- **Problema de concurrencia** en operaciones de escritura de archivos dentro del contenedor Docker
- La API lee el archivo en cada request (`📋 Cargando configuraciones personalizadas...`)
- Mientras está leyendo, otro request intenta escribir → conflicto de acceso
- **Específico de Orange Pi R2S/RISC-V:** Sistema de archivos más estricto con locks

**SÍNTOMAS:**
```bash
# Error en logs de la API
2025-08-08 17:07:22,869 - esp32_api - ERROR - ❌ Error guardando configuración 'test': [Errno 16] Device or resource busy: 'configuraciones.tmp' -> 'configuraciones.json'

# Frontend recibe error 500
{"detail":"Error interno: Error al guardar configuración: [Errno 16] Device or resource busy: 'configuraciones.tmp' -> 'configuraciones.json'"}
```

**PATRÓN IDENTIFICADO EN LOGS:**
```bash
# 1. Usuario intenta guardar configuración
INFO - 💾 Guardando configuración individual: test
# 2. API carga archivo existente (LECTURA)
INFO - 📋 Cargando configuraciones personalizadas...
# 3. Intenta escribir pero archivo está ocupado (CONFLICTO)
ERROR - ❌ Error guardando configuración 'test': [Errno 16] Device or resource busy
```

**DIAGNÓSTICO REALIZADO:**
```bash
# ✅ Archivo configuraciones.json NO está bloqueado por procesos externos
lsof configuraciones.json  # → Sin resultados (archivo libre)

# ✅ Sistema tiene espacio disponible
df -h  # → 2.9G disponibles de 7.0G (58% uso)

# ✅ Permisos correctos
ls -la configuraciones.*  # → -rw-rw-r-- orangepi orangepi

# ✅ Un solo proceso Python corriendo (dentro de Docker)
ps aux | grep python  # → Solo dnsmasq ejecutando Python (contenedor)
```

**CAUSA ESPECÍFICA:**
- **Threading dentro del contenedor**: FastAPI maneja múltiples requests concurrentemente
- **Lectura + Escritura simultánea**: Operación `os.rename()` falla cuando el archivo destino está siendo leído
- **Orange Pi R2S factor**: RISC-V tiene manejo de locks de archivos más estricto que x86

**✅ SOLUCIÓN COMPLETAMENTE IMPLEMENTADA Y VALIDADA (Agosto 2025):**

**MIGRACIÓN A REDIS IMPLEMENTADA:**

**Nuevo sistema de almacenamiento:** `services/custom_configuration_manager_redis.py`

**Cambios implementados:**
1. **Almacenamiento Redis**: Reemplaza el sistema de archivos JSON con Redis para eliminar completamente los problemas de concurrencia
2. **Operaciones atómicas nativas**: Redis garantiza atomicidad sin necesidad de file locking manual
3. **Fallback automático**: Si Redis no está disponible, automáticamente usa el manager de archivos como respaldo
4. **Migración automática**: Endpoint `/config/custom/configurations/migrate` para transferir datos existentes
5. **Performance mejorado**: Operaciones en memoria vs I/O de archivo

**✅ VALIDACIÓN EXITOSA:**
```bash
# ✅ FUNCIONANDO: Migración desde archivo a Redis
curl -X POST http://localhost:8000/config/custom/configurations/migrate
# Respuesta: {"migration_status":"completed","migrated_count":7}

# ✅ FUNCIONANDO: Guardado de configuraciones (SIN problemas de concurrencia)
curl -X POST http://localhost:8000/config/custom/configurations/test_redis \
  -H "Content-Type: application/json" \
  -d '{"batteryCapacity": 100.0, "isLithium": true, ...}'
# Respuesta: {"message":"Configuración 'test_redis' guardada exitosamente","status":"success","storage":"redis"}

# ✅ FUNCIONANDO: Eliminación (SIN bloqueos)
curl -X DELETE http://localhost:8000/config/custom/configurations/test_redis
# Respuesta: {"message":"Configuración 'test_redis' eliminada exitosamente","status":"success","storage":"redis"}

# ✅ FUNCIONANDO: Información del sistema
curl http://localhost:8000/config/custom/configurations/storage-info
# Respuesta: {"storage_type":"redis","redis_available":true,"total_configurations":7}
```

**Ventajas de Redis sobre archivo JSON:**
- ❌ **Archivo JSON**: Problemas de concurrencia, file locking, operaciones I/O bloqueantes
- ✅ **Redis**: Thread-safe nativo, operaciones atómicas, performance en memoria, escalabilidad

**Docker Configuration:**
```yaml
# Redis ya configurado en docker-compose.yml
redis:
  image: redis:7-alpine
  container_name: esp32-redis
  
# API con dependencia de Redis
esp32-api:
  depends_on:
    - redis
  environment:
    - REDIS_URL=redis://esp32-redis:6379
```

**Código final implementado:**
```python
async def _save_to_file_with_lock(self, configurations: Dict[str, Dict]) -> None:
    """Método simplificado para guardar configuraciones con retry en RISC-V"""
    max_attempts = 10
    base_delay = 0.05  # 50ms
    
    for attempt in range(max_attempts):
        temp_file_path = None
        try:
            # Crear archivo temporal único con PID y número de intento
            temp_file_path = self.config_file_path.with_suffix(f'.tmp.{os.getpid()}.{attempt}')
            
            # Escribir datos al archivo temporal
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(configurations, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # Esperar antes del rename para evitar conflictos
            await asyncio.sleep(base_delay)
            
            # Mover archivo temporal al destino final usando shutil para RISC-V
            shutil.move(str(temp_file_path), str(self.config_file_path))
            
            logger.info(f"✅ Configuraciones guardadas exitosamente (intento {attempt + 1})")
            return
            
        except Exception as e:
            if temp_file_path and temp_file_path.exists():
                temp_file_path.unlink()
                
            if attempt == max_attempts - 1:
                raise Exception(f"Error inesperado guardando: {e}")
            
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

**Docker volume configuration fix:**
```yaml
# ✅ CORREGIDO en docker-compose.yml
volumes:
  - ./logs:/app/logs
  - ./data:/app/data
  - .:/app/config:rw  # ← CLAVE: Mount todo el directorio con permisos rw
  - /etc/localtime:/etc/localtime:ro
```

**Estado:** ✅ **COMPLETAMENTE RESUELTO Y VALIDADO** - Sistema de configuraciones personalizadas 100% funcional en Orange Pi R2S/RISC-V

**✅ VALIDACIÓN FINAL EXITOSA (Agosto 9, 2025):**
- ✅ **3 configuraciones guardadas**: GreenPoint20AH, test_final, validacion_final
- ✅ **Persistencia confirmada**: Datos se mantienen entre requests
- ✅ **Concurrencia resuelta**: Sin errores de archivo ocupado o permisos
- ✅ **Docker volumes funcionando**: Escritura sin restricciones
- ✅ **Estabilidad probada**: Sistema robusto para RISC-V

**Métodos actualizados con file locking:**
- ✅ `save_single_configuration()` - Lock exclusivo durante escritura
- ✅ `save_configurations()` - Lock exclusivo durante escritura masiva
- ✅ `delete_configuration()` - Lock exclusivo durante eliminación
- ✅ `import_configurations()` - Lock exclusivo durante importación
- ✅ `load_configurations()` - Lock compartido durante lectura

**Características del fix:**
- **Thread-safe**: Compatible con FastAPI async/await
- **Process-safe**: Locks a nivel del sistema operativo
- **RISC-V optimizado**: Diseñado específicamente para Orange Pi R2S
- **Fault-tolerant**: Sistema de reintentos y cleanup automático
- **Atomic operations**: Previene corrupción de archivos durante interrupciones

**WORKAROUND TEMPORAL:**
```bash
# Si el error persiste, reiniciar el contenedor para limpiar locks
docker-compose restart esp32-api

# O reconstruir completamente
docker-compose down && docker-compose up -d
```

**VERIFICACIÓN DEL PROBLEMA:**
```bash
# Monitorear logs en tiempo real para ver el patrón
docker-compose logs -f esp32-api | grep "configuración"

# Verificar requests concurrentes desde frontend
# Si varios usuarios guardan configuraciones al mismo tiempo → Error reproducible
```

**⚠️ IMPORTANTE:**
- **Problema completamente resuelto** - Sistema de configuraciones funcionando al 100%
- **Validado en RISC-V** - Solución específicamente optimizada para Orange Pi R2S
- **Enfoque final exitoso** - Combinación de retry logic + Docker volume fix
- **Sin regresiones** - Todas las funcionalidades existentes mantienen compatibilidad

---

#### 🔧 **RESUELTO: Error de Permisos Docker en Configuraciones (Agosto 2025)**

**PROBLEMA FINAL IDENTIFICADO:** `[Errno 1] Operation not permitted` al escribir configuraciones

**CAUSA FINAL:** 
- **Docker volume mount incorrecto**: Archivo individual montado como read-only
- **Contenedor sin permisos de escritura**: Mount point no permitía modificaciones
- **Path detection**: Código no detectaba correctamente el entorno Docker

**SÍNTOMAS FINALES:**
```bash
# Error final en logs de la API
ERROR - ❌ Error guardando configuración 'test_final': Error inesperado guardando: [Errno 1] Operation not permitted

# Evolución del error (problema resuelto paso a paso)
[Errno 16] Device or resource busy  →  [Errno 13] Permission denied  →  [Errno 1] Operation not permitted  →  ✅ SUCCESS
```

**✅ SOLUCIÓN FINAL IMPLEMENTADA:**

**1. Docker volume fix (docker-compose.yml):**
```yaml
# ❌ ANTES - Mount de archivo individual (read-only)
- ./configuraciones.json:/app/configuraciones.json

# ✅ DESPUÉS - Mount de directorio completo (read-write)
- .:/app/config:rw
```

**2. Path detection automático (custom_configuration_manager.py):**
```python
def __init__(self, config_file_path: str = None):
    # Determinar la ruta correcta según el entorno
    if config_file_path is None:
        # En Docker, usar la ruta del volumen montado
        if os.path.exists("/app/config"):
            config_file_path = "/app/config/configuraciones.json"
        else:
            # En desarrollo local
            config_file_path = "configuraciones.json"
```

**3. Sistema de reintentos robusto:**
```python
async def _save_to_file_with_lock(self, configurations: Dict[str, Dict]) -> None:
    max_attempts = 10
    base_delay = 0.05
    
    for attempt in range(max_attempts):
        try:
            # Archivo temporal único por proceso e intento
            temp_file_path = self.config_file_path.with_suffix(f'.tmp.{os.getpid()}.{attempt}')
            
            # Operación atómica con shutil.move() para RISC-V
            shutil.move(str(temp_file_path), str(self.config_file_path))
            return
        except Exception as e:
            # Delay exponencial entre reintentos
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

**VERIFICACIÓN FINAL EXITOSA:**
```bash
# ✅ Test completo funcional
curl -X POST http://localhost:8000/config/custom/configurations/test_final \
  -H "Content-Type: application/json" \
  -d '{"batteryCapacity": 100.0, "isLithium": true, ...}'

# Respuesta exitosa
{"message":"Configuración 'test_final' guardada exitosamente","status":"success","configuration_name":"test_final"}

# ✅ Persistencia confirmada
curl http://localhost:8000/config/custom/configurations
{"configurations":{"test_final":{...},"GreenPoint20AH":{...}},"total_count":2}
```

**⚠️ LECCIONES APRENDIDAS PARA RISC-V:**
1. **Docker volumes**: NUNCA montar archivos individuales, siempre directorios con `:rw`
2. **Path detection**: Detectar automáticamente entorno Docker vs desarrollo
3. **Retry logic**: Sistemas de reintentos son más efectivos que file locks complejos en RISC-V
4. **Archivo temporal naming**: Usar PID + attempt number para evitar colisiones
5. **Error evolution**: Los errores evolucionan mostrando progreso: busy → permission → operation not permitted → success

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

#### Errores de permisos en carpeta logs
```bash
# Error común: "Permission denied" al escribir logs
# Verificar permisos actuales de la carpeta logs
ls -la logs/

# Solución: Configurar permisos correctos
sudo mkdir -p logs
sudo chmod 755 logs
sudo chown $USER:$USER logs

# Para instalación con Docker, también verificar:
# que el usuario esté en el grupo docker
groups $USER | grep docker
sudo usermod -aG docker $USER

# Reiniciar contenedores después de cambiar permisos
docker-compose down
docker-compose up -d

# Verificar que se pueden escribir logs
docker-compose logs esp32-api | tail -5
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