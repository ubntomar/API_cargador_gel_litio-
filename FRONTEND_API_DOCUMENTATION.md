# 📡 ESP32 Solar Charger API - Documentación para Frontend

## 🎯 Información General

**Base URL:** `http://localhost:8000`
**Protocolo:** REST API con FastAPI
**Formato de datos:** JSON
**Autenticación:** Sin autenticación (desarrollo local)

**📝 Nota sobre URLs:**
- El endpoint de datos DEBE usar barra final: `/data/` ✅
- NO usar `/data` sin barra final ❌ (no funciona)
- Otros endpoints funcionan con o sin barra final
- Los ejemplos usan la forma correcta que funciona

---

## 🔋 **1. ENDPOINTS DE DATOS DEL ESP32**

### 📊 Obtener Datos Actuales del ESP32

```http
GET /data/
```

**Descripción:** Obtiene todos los datos actuales del cargador solar ESP32

**URL completa:** `http://localhost:8000/data/`
**⚠️ IMPORTANTE:** Debe incluir la barra final `/data/` - `/data` sin barra NO funciona

**Respuesta de éxito (200):**
```json
{
  "panelToBatteryCurrent": 5200.0,
  "batteryToLoadCurrent": 3000.0,
  "voltagePanel": 18.5,
  "voltageBatterySensor2": 12.45,
  "currentPWM": 128,
  "temperature": 25.4,
  "chargeState": "BULK_CHARGE",
  "bulkVoltage": 14.4,
  "absorptionVoltage": 14.4,
  "floatVoltage": 13.6,
  "LVD": 11.5,
  "LVR": 12.0,
  "batteryCapacity": 100.0,
  "thresholdPercentage": 2.5,
  "maxAllowedCurrent": 10000.0,
  "isLithium": false,
  "maxBatteryVoltageAllowed": 15.0,
  "absorptionCurrentThreshold_mA": 2500.0,
  "currentLimitIntoFloatStage": 1000.0,
  "calculatedAbsorptionHours": 2.5,
  "currentBulkHours": 1.2,
  "accumulatedAh": 15.5,
  "estimatedSOC": 85.3,
  "netCurrent": 2200.0,
  "factorDivider": 1,
  "useFuenteDC": true,
  "fuenteDC_Amps": 10.0,
  "maxBulkHours": 6.0,
  "panelSensorAvailable": true,
  "maxAbsorptionHours": 4.0,
  "chargedBatteryRestVoltage": 13.8,
  "reEnterBulkVoltage": 12.8,
  "pwmFrequency": 1000,
  "tempThreshold": 40,
  "temporaryLoadOff": false,
  "loadOffRemainingSeconds": 0,
  "loadOffDuration": 0,
  "loadControlState": true,
  "ledSolarState": true,
  "notaPersonalizada": "Sistema funcionando correctamente",
  "connected": true,
  "firmware_version": "v2.1.0",
  "uptime": 1234567,
  "last_update": "2025-08-06T10:45:23.123456"
}
```

**Errores comunes:**
- `503 Service Unavailable`: ESP32 no conectado
- `500 Internal Server Error`: Error de comunicación

---

## ⚙️ **2. ENDPOINTS DE CONFIGURACIÓN DEL ESP32**

### 🔧 Configurar Parámetro Individual

```http
POST /config/parameter
```

**Descripción:** Configura un parámetro específico del ESP32

**Request Body:**
```json
{
  "parameter": "useFuenteDC",
  "value": true
}
```

**Parámetros disponibles:**
- `batteryCapacity`: número (Ah)
- `isLithium`: booleano
- `thresholdPercentage`: número (%)
- `maxAllowedCurrent`: número (mA)
- `bulkVoltage`: número (V)
- `absorptionVoltage`: número (V)
- `floatVoltage`: número (V)
- `useFuenteDC`: booleano
- `fuenteDC_Amps`: número (A)
- `factorDivider`: número entero

**Respuesta de éxito (200):**
```json
{
  "success": true,
  "esp32_response": "OK:useFuenteDC updated to True",
  "parameter": "useFuenteDC",
  "value": true
}
```

**Respuesta de error (400/500):**
```json
{
  "success": false,
  "error": "Sin respuesta del ESP32",
  "parameter": "useFuenteDC",
  "value": true
}
```

---

## 📋 **3. SISTEMA DE CONFIGURACIONES PERSONALIZADAS**

### 📝 Crear Nueva Configuración

```http
POST /config/custom/configurations/{name}
```

**Descripción:** Crea una nueva configuración personalizada

**Parámetros de URL:**
- `name`: Nombre de la configuración (string)

**Request Body:**
```json
{
  "batteryCapacity": 200.0,
  "isLithium": true,
  "thresholdPercentage": 3.0,
  "maxAllowedCurrent": 15000.0,
  "bulkVoltage": 14.6,
  "absorptionVoltage": 14.6,
  "floatVoltage": 13.8,
  "useFuenteDC": false,
  "fuenteDC_Amps": 0.0,
  "factorDivider": 1
}
```

**Respuesta de éxito (200):**
```json
{
  "message": "Configuración 'BateriaLitio200Ah' creada exitosamente",
  "status": "success",
  "configuration_name": "BateriaLitio200Ah",
  "saved_at": "2025-08-06T10:39:25.123456"
}
```

### 📋 Listar Todas las Configuraciones

```http
GET /config/custom/configurations
```

**Parámetros de consulta opcionales:**
- `search`: Filtrar por término de búsqueda (string)

**Ejemplo con filtro:**
```http
GET /config/custom/configurations?search=litio
```

**Respuesta de éxito (200):**
```json
{
  "configurations": {
    "BateriaLitio200Ah": {
      "batteryCapacity": 200.0,
      "isLithium": true,
      "thresholdPercentage": 3.0,
      "maxAllowedCurrent": 15000.0,
      "bulkVoltage": 14.6,
      "absorptionVoltage": 14.6,
      "floatVoltage": 13.8,
      "useFuenteDC": false,
      "fuenteDC_Amps": 0.0,
      "factorDivider": 1,
      "createdAt": "2024-01-01T00:00:00",
      "updatedAt": "2025-08-06T10:39:25"
    }
  },
  "total_count": 1
}
```

### ⚡ Aplicar Configuración al ESP32

```http
POST /config/custom/configurations/{name}/apply
```

**Descripción:** Aplica una configuración guardada al ESP32

**Parámetros de URL:**
- `name`: Nombre de la configuración a aplicar

**Respuesta de éxito (200):**
```json
{
  "message": "Configuración 'BateriaLitio200Ah' aplicada exitosamente al ESP32",
  "status": "success",
  "configuration_name": "BateriaLitio200Ah",
  "esp32_responses": {
    "batteryCapacity": {
      "success": true,
      "esp32_response": "OK:batteryCapacity updated to 200.0"
    },
    "isLithium": {
      "success": true,
      "esp32_response": "OK:isLithium updated to True"
    }
  },
  "applied_at": "2025-08-06T10:40:15.123456"
}
```

### ✅ Validar Configuración

```http
POST /config/custom/configurations/validate
```

**Descripción:** Valida una configuración antes de guardarla

**Request Body:**
```json
{
  "batteryCapacity": 100.0,
  "isLithium": false,
  "thresholdPercentage": 2.5,
  "maxAllowedCurrent": 5000.0,
  "bulkVoltage": 14.4,
  "absorptionVoltage": 14.4,
  "floatVoltage": 13.6,
  "useFuenteDC": true,
  "fuenteDC_Amps": 10.0,
  "factorDivider": 2
}
```

**Respuesta de éxito (200):**
```json
{
  "valid": true,
  "message": "Configuración válida",
  "configuration": {
    "batteryCapacity": 100.0,
    "isLithium": false,
    "thresholdPercentage": 2.5,
    "maxAllowedCurrent": 5000.0,
    "bulkVoltage": 14.4,
    "absorptionVoltage": 14.4,
    "floatVoltage": 13.6,
    "useFuenteDC": true,
    "fuenteDC_Amps": 10.0,
    "factorDivider": 2
  }
}
```

### 💾 Exportar Configuraciones

```http
GET /config/custom/configurations/export
```

**Descripción:** Exporta todas las configuraciones en formato JSON

**Respuesta de éxito (200):**
```json
{
  "export_info": {
    "total_configurations": 2,
    "exported_at": "2025-08-06T10:42:10.123456",
    "version": "1.0"
  },
  "configurations": {
    "BateriaLitio200Ah": {
      "batteryCapacity": 200.0,
      "isLithium": true,
      "thresholdPercentage": 3.0,
      "maxAllowedCurrent": 15000.0,
      "bulkVoltage": 14.6,
      "absorptionVoltage": 14.6,
      "floatVoltage": 13.8,
      "useFuenteDC": false,
      "fuenteDC_Amps": 0.0,
      "factorDivider": 1,
      "createdAt": "2024-01-01T00:00:00",
      "updatedAt": "2025-08-06T10:39:25"
    }
  }
}
```

### 📊 Información del Sistema

```http
GET /config/custom/configurations/info
```

**Descripción:** Obtiene información estadística del sistema de configuraciones

**Respuesta de éxito (200):**
```json
{
  "file_info": {
    "exists": true,
    "path": "configuraciones.json",
    "size_bytes": 775,
    "modified": "2025-08-06T10:44:24.162318",
    "created": "2025-08-06T10:44:24.162396"
  },
  "statistics": {
    "total_configurations": 2,
    "configuration_names": ["BateriaLitio200Ah", "Batería GEL 100Ah"],
    "lithium_configs": 1,
    "gel_configs": 1
  },
  "system_status": "operational"
}
```

### 🗑️ Eliminar Configuración

```http
DELETE /config/custom/configurations/{name}
```

**Descripción:** Elimina una configuración específica

**Parámetros de URL:**
- `name`: Nombre de la configuración a eliminar

**Respuesta de éxito (200):**
```json
{
  "message": "Configuración 'BateriaGEL100Ah' eliminada exitosamente",
  "status": "success",
  "configuration_name": "BateriaGEL100Ah"
}
```

---

## 📱 **4. ENDPOINTS DE PROGRAMACIÓN (SCHEDULE)**

### 📅 Configurar Horario de Apagado

```http
POST /schedule/set
```

**Request Body:**
```json
{
  "enabled": true,
  "shutdown_time": "22:30",
  "startup_time": "06:00"
}
```

**Respuesta de éxito (200):**
```json
{
  "success": true,
  "message": "Horario configurado exitosamente",
  "schedule": {
    "enabled": true,
    "shutdown_time": "22:30",
    "startup_time": "06:00"
  }
}
```

### 📋 Obtener Configuración Actual

```http
GET /schedule
```

**Respuesta de éxito (200):**
```json
{
  "enabled": true,
  "shutdown_time": "22:30",
  "startup_time": "06:00",
  "next_shutdown": "2025-08-06T22:30:00",
  "next_startup": "2025-08-07T06:00:00",
  "is_active": true
}
```

---

## 🔍 **5. ENDPOINTS DE INFORMACIÓN**

### 🏥 Estado de Salud del API

```http
GET /health
```

**Respuesta de éxito (200):**
```json
{
  "status": "healthy",
  "esp32_connected": true,
  "timestamp": "2025-08-06T10:45:23.123456",
  "version": "1.0.0"
}
```

### 📖 Documentación del API

```http
GET /docs
```

**Descripción:** Interfaz interactiva de Swagger UI para probar endpoints

```http
GET /redoc
```

**Descripción:** Documentación alternativa con ReDoc

---

## 🚨 **6. CÓDIGOS DE ERROR COMUNES**

### Errores de Conexión ESP32
- **503 Service Unavailable**: ESP32 no conectado
- **500 Internal Server Error**: Error de comunicación serial

### Errores de Validación
- **422 Unprocessable Entity**: Datos de entrada inválidos
- **400 Bad Request**: Parámetros incorrectos

### Errores de Configuraciones
- **404 Not Found**: Configuración no encontrada
- **409 Conflict**: Configuración ya existe

---

## 💡 **7. MEJORES PRÁCTICAS PARA EL FRONTEND**

### 🔄 Polling de Datos
```javascript
// Obtener datos cada 3 segundos
const fetchESP32Data = async () => {
  try {
    const response = await fetch('http://localhost:8000/data/');
    if (response.ok) {
      const data = await response.json();
      updateUI(data);
    }
  } catch (error) {
    console.error('Error fetching ESP32 data:', error);
  }
};

setInterval(fetchESP32Data, 3000);
```

### ⚙️ Configurar Parámetros
```javascript
const setParameter = async (parameter, value) => {
  try {
    const response = await fetch('http://localhost:8000/config/parameter', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        parameter: parameter,
        value: value
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log(`${parameter} configurado exitosamente`);
    } else {
      console.error(`Error configurando ${parameter}:`, result.error);
    }
  } catch (error) {
    console.error('Error en la petición:', error);
  }
};
```

### 📋 Gestión de Configuraciones
```javascript
const applyConfiguration = async (configName) => {
  try {
    const response = await fetch(`http://localhost:8000/config/custom/configurations/${configName}/apply`, {
      method: 'POST'
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      console.log('Configuración aplicada exitosamente');
      // Actualizar UI
    }
  } catch (error) {
    console.error('Error aplicando configuración:', error);
  }
};
```

---

## 🔧 **8. CONFIGURACIONES ESPECÍFICAS POR TIPO DE BATERÍA**

### 🔋 Batería de Litio (LiFePO4)
```json
{
  "batteryCapacity": 200.0,
  "isLithium": true,
  "thresholdPercentage": 3.0,
  "maxAllowedCurrent": 15000.0,
  "bulkVoltage": 14.6,
  "absorptionVoltage": 14.6,
  "floatVoltage": 13.8,
  "useFuenteDC": false,
  "fuenteDC_Amps": 0.0,
  "factorDivider": 1
}
```

### 🔋 Batería GEL
```json
{
  "batteryCapacity": 100.0,
  "isLithium": false,
  "thresholdPercentage": 2.5,
  "maxAllowedCurrent": 5000.0,
  "bulkVoltage": 14.4,
  "absorptionVoltage": 14.4,
  "floatVoltage": 13.6,
  "useFuenteDC": true,
  "fuenteDC_Amps": 10.0,
  "factorDivider": 2
}
```

---

## 📞 **9. SOPORTE Y RESOLUCIÓN DE PROBLEMAS**

### 🔍 Verificar Estado del API
1. Verificar que el API está corriendo: `GET /health`
2. Verificar conexión ESP32: Campo `esp32_connected` en `/health`
3. Revisar logs en consola del servidor

### 🔌 Problemas de Conexión ESP32
- Verificar puerto USB conectado
- Revisar permisos del puerto serial
- Reiniciar API si es necesario

### 📊 Validación de Datos
- Usar endpoint `/config/custom/configurations/validate` antes de guardar
- Verificar tipos de datos en requests
- Comprobar rangos de valores permitidos

---

## 🏷️ **10. VERSIÓN Y CHANGELOG**

**Versión actual:** 1.0.0
**Última actualización:** 6 de agosto de 2025

### ✅ Funcionalidades validadas:
- ✅ Obtención de datos ESP32
- ✅ Configuración de parámetros individuales
- ✅ Sistema completo de configuraciones personalizadas
- ✅ Programación de horarios
- ✅ Endpoints de información y salud
- ✅ Validación y manejo de errores

---

**🎯 Este API está completamente funcional y listo para integración frontend.**
