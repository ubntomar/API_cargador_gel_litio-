# 📋 Quick Reference - ESP32 Solar Charger API

## 🚀 Base URL
```
http://localhost:8000
```

## 📊 Endpoints Core

### Datos ESP32
```http
GET /data                           # Obtener datos actuales
GET /health                         # Estado del sistema
```

### Configuración
```http
POST /config/parameter              # Configurar parámetro individual
```

## 📋 Sistema de Configuraciones Personalizadas

```http
POST /config/custom/configurations/{name}           # Crear configuración
GET  /config/custom/configurations                  # Listar todas
GET  /config/custom/configurations?search={term}    # Buscar configuraciones
POST /config/custom/configurations/{name}/apply     # Aplicar al ESP32
POST /config/custom/configurations/validate         # Validar configuración
GET  /config/custom/configurations/export           # Exportar backup JSON
GET  /config/custom/configurations/info             # Estadísticas sistema
DELETE /config/custom/configurations/{name}         # Eliminar configuración
```

## ⏰ Programación
```http
GET  /schedule                      # Obtener horarios actuales
POST /schedule/set                  # Configurar horarios
```

---

## 🔋 Parámetros Configurables

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `batteryCapacity` | number | Capacidad batería (Ah) |
| `isLithium` | boolean | Tipo: true=Litio, false=GEL |
| `thresholdPercentage` | number | Umbral porcentaje (%) |
| `maxAllowedCurrent` | number | Corriente máxima (mA) |
| `bulkVoltage` | number | Voltaje bulk (V) |
| `absorptionVoltage` | number | Voltaje absorción (V) |
| `floatVoltage` | number | Voltaje flotación (V) |
| `useFuenteDC` | boolean | Usar fuente DC |
| `fuenteDC_Amps` | number | Amperaje fuente DC (A) |
| `factorDivider` | number | Factor divisor |

---

## 📱 Respuestas Comunes

### ✅ Datos ESP32 (GET /data)
```json
{
  "batteryVoltage": 12.45,
  "batteryPercentage": 85.3,
  "batteryCapacity": 100.0,
  "isCharging": true,
  "chargingCurrent": 5.2,
  "temperatureC": 25.4,
  "isLithium": false,
  "useFuenteDC": true
}
```

### ⚙️ Configurar Parámetro (POST /config/parameter)
```json
// Request
{
  "parameter": "useFuenteDC",
  "value": true
}

// Response Success
{
  "success": true,
  "esp32_response": "OK:useFuenteDC updated to True",
  "parameter": "useFuenteDC",
  "value": true
}
```

### 📋 Listar Configuraciones (GET /config/custom/configurations)
```json
{
  "configurations": {
    "BateriaLitio200Ah": {
      "batteryCapacity": 200.0,
      "isLithium": true,
      "thresholdPercentage": 3.0,
      "maxAllowedCurrent": 15000.0,
      "bulkVoltage": 14.6,
      "createdAt": "2024-01-01T00:00:00",
      "updatedAt": "2025-08-06T10:39:25"
    }
  },
  "total_count": 1
}
```

### 🚀 Aplicar Configuración (POST /config/custom/configurations/{name}/apply)
```json
{
  "message": "Configuración 'BateriaLitio200Ah' aplicada exitosamente al ESP32",
  "status": "success",
  "configuration_name": "BateriaLitio200Ah",
  "esp32_responses": {
    "batteryCapacity": {
      "success": true,
      "esp32_response": "OK:batteryCapacity updated to 200.0"
    }
  },
  "applied_at": "2025-08-06T10:40:15.123456"
}
```

---

## 🚨 Códigos de Error

| Código | Descripción |
|--------|-------------|
| `200` | ✅ Éxito |
| `400` | ❌ Petición incorrecta |
| `404` | ❌ No encontrado |
| `409` | ⚠️ Conflicto (ya existe) |
| `422` | ❌ Datos inválidos |
| `500` | 💥 Error interno servidor |
| `503` | 🔌 ESP32 no conectado |

---

## 💡 Tips Rápidos

### 🔄 Polling Frontend
```javascript
// Obtener datos cada 3 segundos
setInterval(async () => {
  const response = await fetch('http://localhost:8000/data');
  const data = await response.json();
  updateUI(data);
}, 3000);
```

### ⚙️ Configurar Parámetro
```javascript
await fetch('http://localhost:8000/config/parameter', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    parameter: 'useFuenteDC',
    value: true
  })
});
```

### 📋 Aplicar Configuración
```javascript
await fetch(`http://localhost:8000/config/custom/configurations/${name}/apply`, {
  method: 'POST'
});
```

---

## 🔋 Configuraciones Predeterminadas

### Batería Litio 100Ah
```json
{
  "batteryCapacity": 100.0,
  "isLithium": true,
  "thresholdPercentage": 3.0,
  "maxAllowedCurrent": 10000.0,
  "bulkVoltage": 14.6,
  "absorptionVoltage": 14.6,
  "floatVoltage": 13.8,
  "useFuenteDC": false,
  "fuenteDC_Amps": 0.0,
  "factorDivider": 1
}
```

### Batería GEL 100Ah
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

**📚 Para más detalles ver:** [`FRONTEND_API_DOCUMENTATION.md`](./FRONTEND_API_DOCUMENTATION.md) | [`FRONTEND_EXAMPLES.md`](./FRONTEND_EXAMPLES.md)
