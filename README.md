# ESP32 Solar Charger API

API REST para control y monitoreo del cargador solar ESP32 con **funcionalidad de apagado programado diario**.

## 🚀 Instalación Rápida

```bash
# Clonar/crear el proyecto
git clone <tu-repo> esp32_api
cd esp32_api

# Crear entorno virtual..
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

## ✨ Nuevas Características

### 🕐 Schedule Diario Automático
- **Apagado programado**: Configura hora de inicio y duración (máx 8 horas)
- **Override manual**: Los comandos manuales anulan el schedule hasta el siguiente día
- **Configuración flexible**: Habilitar/deshabilitar sin perder configuración
- **Zona horaria local**: Manejo automático desde la OrangePi
- **Límite de seguridad**: Máximo 8 horas de apagado continuo

### 🛡️ Seguridad Mejorada
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
├── main.py              # FastAPI app principal
├── models/              # Modelos Pydantic
│   ├── esp32_data.py   # Modelos ESP32
│   └── schedule_models.py # 🆕 Modelos Schedule
├── services/            # Lógica de negocio
│   ├── esp32_manager.py
│   └── schedule_manager.py # 🆕 Gestión Schedule
├── api/                 # Endpoints REST
│   ├── data.py
│   ├── config.py
│   ├── actions.py       # 🔄 Actualizado con Schedule
│   └── schedule.py      # 🆕 Endpoints Schedule
├── core/                # Configuración
└── logs/                # Archivos de log
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

### Schedule no funciona
```bash
# Verificar estado
curl http://localhost:8000/schedule/

# Verificar si hay override activo
curl http://localhost:8000/actions/status

# Limpiar override manual
curl -X POST http://localhost:8000/schedule/clear_override
```

### Toggle manual no anula schedule
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

### ESP32 no responde a comandos
```bash
# Verificar conexión
curl http://localhost:8000/health

# Ver logs
tail -f logs/esp32_api.log
```

## 📞 Soporte

- **Documentación completa**: `/docs`
- **Información del sistema**: `/system/info`
- **Estado de conexión**: `/data/status/connection`
- **Rate limiting stats**: `/rate-limit/stats`

---

## 🔄 Migración desde Versión Anterior

Si actualizas desde una versión sin schedule:

1. **Los endpoints existentes siguen funcionando igual**
2. **Toggle manual ahora anula schedule** (nuevo comportamiento)
3. **Nuevos endpoints bajo `/schedule/`**
4. **Configuración por defecto**: Schedule habilitado de 12 AM - 6 AM

No se requieren cambios en el código del frontend existente.