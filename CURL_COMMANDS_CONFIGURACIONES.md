# =============================================================================
# 📋 COMANDOS CURL - Configuraciones Personalizadas ESP32 Solar Charger API
# =============================================================================

## 🔍 1. LISTAR TODAS LAS CONFIGURACIONES
```bash
curl -s http://localhost:8000/config/custom/configurations | jq .
```

## ➕ 2. CREAR CONFIGURACIÓN NUEVA

### Batería Litio 100Ah
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 100.0,
    "isLithium": true,
    "thresholdPercentage": 2.5,
    "maxAllowedCurrent": 12000.0,
    "bulkVoltage": 14.4,
    "absorptionVoltage": 14.4,
    "floatVoltage": 13.6,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 1
  }' \
  http://localhost:8000/config/custom/config/BateriaLitio100Ah
```

### Batería GEL 200Ah
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 200.0,
    "isLithium": false,
    "thresholdPercentage": 3.0,
    "maxAllowedCurrent": 15000.0,
    "bulkVoltage": 14.8,
    "absorptionVoltage": 14.8,
    "floatVoltage": 13.8,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 5
  }' \
  http://localhost:8000/config/custom/config/BateriaGEL200Ah
```

### Configuración Compacta (una línea)
```bash
curl -X POST -H "Content-Type: application/json" -d '{"batteryCapacity": 50.0, "isLithium": true, "thresholdPercentage": 2.0, "maxAllowedCurrent": 5000.0, "bulkVoltage": 14.2, "absorptionVoltage": 14.2, "floatVoltage": 13.4, "useFuenteDC": false, "fuenteDC_Amps": 0.0, "factorDivider": 1}' http://localhost:8000/config/custom/config/ConfigPequena
```

## 📖 3. OBTENER CONFIGURACIÓN ESPECÍFICA
```bash
curl -s http://localhost:8000/config/custom/config/BateriaLitio100Ah | jq .
```

## ✅ 4. VALIDAR CONFIGURACIÓN ANTES DE GUARDAR
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 150.0,
    "isLithium": true,
    "thresholdPercentage": 2.0,
    "maxAllowedCurrent": 8000.0,
    "bulkVoltage": 14.6,
    "absorptionVoltage": 14.6,
    "floatVoltage": 13.7,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 1
  }' \
  http://localhost:8000/config/custom/configurations/validate
```

## 🚀 5. APLICAR CONFIGURACIÓN AL ESP32
```bash
curl -X POST http://localhost:8000/config/custom/config/BateriaLitio100Ah/apply
```

## 🗑️ 6. ELIMINAR CONFIGURACIÓN
```bash
curl -X DELETE http://localhost:8000/config/custom/config/BateriaLitio100Ah
```

## 📦 7. EXPORTAR TODAS LAS CONFIGURACIONES (BACKUP)
```bash
curl -s http://localhost:8000/config/custom/configurations/export | jq .
```

## 📊 8. INFORMACIÓN DEL SISTEMA
```bash
curl -s http://localhost:8000/config/custom/configurations/info | jq .
```

## 📥 9. CREAR MÚLTIPLES CONFIGURACIONES DE UNA VEZ
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "ConfigPequena": {
        "batteryCapacity": 50.0,
        "isLithium": true,
        "thresholdPercentage": 2.0,
        "maxAllowedCurrent": 5000.0,
        "bulkVoltage": 14.2,
        "absorptionVoltage": 14.2,
        "floatVoltage": 13.4,
        "useFuenteDC": false,
        "fuenteDC_Amps": 0.0,
        "factorDivider": 1
      },
      "ConfigGrande": {
        "batteryCapacity": 400.0,
        "isLithium": false,
        "thresholdPercentage": 3.5,
        "maxAllowedCurrent": 20000.0,
        "bulkVoltage": 15.0,
        "absorptionVoltage": 15.0,
        "floatVoltage": 14.0,
        "useFuenteDC": true,
        "fuenteDC_Amps": 10.0,
        "factorDivider": 10
      }
    }
  }' \
  http://localhost:8000/config/custom/configurations
```

# =============================================================================
# 🎯 EJEMPLOS DE RESPUESTAS ESPERADAS
# =============================================================================

## Respuesta de Crear Configuración:
```json
{
  "message": "Configuración 'BateriaLitio100Ah' guardada exitosamente",
  "status": "success", 
  "configuration_name": "BateriaLitio100Ah"
}
```

## Respuesta de Listar Configuraciones:
```json
{
  "configurations": {
    "BateriaLitio100Ah": {
      "batteryCapacity": 100.0,
      "isLithium": true,
      "thresholdPercentage": 2.5,
      "maxAllowedCurrent": 12000.0,
      "bulkVoltage": 14.4,
      "absorptionVoltage": 14.4,
      "floatVoltage": 13.6,
      "useFuenteDC": false,
      "fuenteDC_Amps": 0.0,
      "factorDivider": 1,
      "createdAt": "2025-08-09T20:23:20.538135",
      "updatedAt": "2025-08-09T20:23:20.538140"
    }
  },
  "total_count": 1
}
```

## Respuesta de Aplicar Configuración:
```json
{
  "message": "Configuración 'BateriaLitio100Ah' aplicada exitosamente al ESP32",
  "status": "success",
  "configuration_name": "BateriaLitio100Ah",
  "esp32_responses": {},
  "applied_at": "2025-08-09T20:23:40.711722"
}
```

# =============================================================================
# 🛠️ COMANDOS DE PRUEBA RÁPIDA
# =============================================================================

## Secuencia completa de prueba:
```bash
# 1. Crear configuración
curl -X POST -H "Content-Type: application/json" -d '{"batteryCapacity": 100.0, "isLithium": true, "thresholdPercentage": 2.5, "maxAllowedCurrent": 12000.0, "bulkVoltage": 14.4, "absorptionVoltage": 14.4, "floatVoltage": 13.6, "useFuenteDC": false, "fuenteDC_Amps": 0.0, "factorDivider": 1}' http://localhost:8000/config/custom/config/TestConfig

# 2. Listar para verificar
curl -s http://localhost:8000/config/custom/configurations

# 3. Aplicar al ESP32
curl -X POST http://localhost:8000/config/custom/config/TestConfig/apply

# 4. Eliminar
curl -X DELETE http://localhost:8000/config/custom/config/TestConfig
```

# =============================================================================
# 📝 NOTAS IMPORTANTES
# =============================================================================

- Todos los endpoints requieren Content-Type: application/json para POST/PUT
- Los nombres de configuración no pueden contener espacios ni caracteres especiales
- La validación se hace automáticamente antes de guardar
- Las configuraciones se almacenan con timestamps automáticos
- Use | jq . al final para pretty-print JSON
- La API corre en http://localhost:8000 por defecto
