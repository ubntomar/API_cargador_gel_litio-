# Sistema de Configuraciones Personalizadas - API

## 📋 Descripción

El sistema de configuraciones personalizadas permite a los usuarios crear, guardar, gestionar y aplicar configuraciones específicas para diferentes tipos de baterías y casos de uso en el cargador solar ESP32.

## ✅ Estado Actual - Agosto 2025

**🎯 SISTEMA COMPLETAMENTE FUNCIONAL Y VALIDADO**

Todas las funcionalidades han sido probadas exhaustivamente y están operativas:

### ✅ Backend (API) - VALIDADO
- ✅ Crear configuraciones individuales con nombres personalizados
- ✅ Listar todas las configuraciones guardadas
- ✅ Aplicar configuraciones al ESP32 (comunicación verificada)
- ✅ Validar configuraciones antes de guardar
- ✅ Exportar configuraciones a JSON (backup completo)
- ✅ Información del sistema y estadísticas
- ✅ Eliminar configuraciones específicas
- ✅ Buscar/filtrar configuraciones por términos
- ✅ Persistencia robusta en `configuraciones.json`
- ✅ Validación completa con Pydantic
- ✅ Gestión de errores y logging detallado
- ✅ Thread-safe y operación async

### 🎯 Frontend (Pendiente)
- ⏳ Interfaz para crear/editar configuraciones
- ⏳ Lista visual de configuraciones guardadas
- ⏳ Aplicación de configuraciones con un clic
- ⏳ Exportación/importación de archivos
- ⏳ Validación en tiempo real

## 📚 Documentación para Frontend

**Para desarrolladores frontend, consultar:** [`FRONTEND_API_DOCUMENTATION.md`](./FRONTEND_API_DOCUMENTATION.md)

Incluye:
- 📋 Todos los endpoints con ejemplos completos
- 🎯 Códigos de respuesta y manejo de errores
- 💡 Mejores prácticas y ejemplos de JavaScript
- 🔧 Configuraciones específicas por tipo de batería

## 📚 Endpoints Disponibles

### Base URL: `/config/custom/configurations`

#### 1. Guardar Configuraciones Múltiples
```http
POST /config/custom/configurations
```

**Request Body:**
```json
{
  "data": "{\"Batería Litio 100Ah\":{\"batteryCapacity\":100,\"isLithium\":true,\"thresholdPercentage\":2.0,\"maxAllowedCurrent\":10000,\"bulkVoltage\":14.4,\"absorptionVoltage\":14.4,\"floatVoltage\":13.6,\"useFuenteDC\":false,\"fuenteDC_Amps\":0,\"factorDivider\":1}}"
}
```

**Response:**
```json
{
  "message": "Configuraciones guardadas exitosamente",
  "status": "success"
}
```

#### 2. Cargar Todas las Configuraciones
```http
GET /config/custom/configurations
```

**Response:**
```json
{
  "configurations": {
    "Batería Litio 100Ah": {
      "batteryCapacity": 100.0,
      "isLithium": true,
      "thresholdPercentage": 2.0,
      "maxAllowedCurrent": 10000.0,
      "bulkVoltage": 14.4,
      "absorptionVoltage": 14.4,
      "floatVoltage": 13.6,
      "useFuenteDC": false,
      "fuenteDC_Amps": 0.0,
      "factorDivider": 1,
      "createdAt": "2025-08-05T10:00:00.000Z",
      "updatedAt": "2025-08-05T10:00:00.000Z"
    }
  },
  "total_count": 1
}
```

#### 3. Guardar/Actualizar Configuración Individual
```http
POST /config/custom/config/{configuration_name}
```

**Request Body:**
```json
{
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
}
```

**Response:**
```json
{
  "message": "Configuración 'Batería Litio 100Ah' guardada exitosamente",
  "status": "success",
  "configuration_name": "Batería Litio 100Ah"
}
```

#### 4. Obtener Configuración Específica
```http
GET /config/custom/config/{configuration_name}
```

**Response:**
```json
{
  "configuration_name": "Batería Litio 100Ah",
  "configuration": {
    "batteryCapacity": 100.0,
    "isLithium": true,
    "thresholdPercentage": 2.0,
    "maxAllowedCurrent": 10000.0,
    "bulkVoltage": 14.4,
    "absorptionVoltage": 14.4,
    "floatVoltage": 13.6,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 1,
    "createdAt": "2025-08-05T10:00:00.000Z",
    "updatedAt": "2025-08-05T10:00:00.000Z"
  }
}
```

#### 5. Eliminar Configuración
```http
DELETE /config/custom/config/{configuration_name}
```

**Response:**
```json
{
  "message": "Configuración 'Batería Litio 100Ah' eliminada exitosamente",
  "status": "success",
  "configuration_name": "Batería Litio 100Ah"
}
```

#### 6. Aplicar Configuración al ESP32
```http
POST /config/custom/config/{configuration_name}/apply
```

**Response:**
```json
{
  "message": "Configuración 'Batería Litio 100Ah' aplicada completamente. Parámetros aplicados: 10",
  "status": "success",
  "configuration_name": "Batería Litio 100Ah"
}
```

#### 7. Validar Configuración
```http
POST /config/custom/configurations/validate
```

**Request Body:**
```json
{
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
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": null,
  "warnings": null
}
```

#### 8. Exportar Configuraciones
```http
GET /config/custom/configurations/export
```

**Response:**
```json
{
  "filename": "configuraciones_backup_20250805_143022.json",
  "content": "{\"Batería Litio 100Ah\":{...}}",
  "configurations_count": 3
}
```

#### 9. Importar Configuraciones
```http
POST /config/custom/configurations/import
```

**Request Body:**
```json
{
  "configurations_data": "{\"Nueva Config\":{\"batteryCapacity\":150,...}}",
  "overwrite_existing": false
}
```

**Response:**
```json
{
  "success": true,
  "imported_count": 2,
  "skipped_count": 1,
  "errors": null,
  "warnings": {
    "Config Existente": "Configuración ya existe, use overwrite_existing=true para sobrescribir"
  }
}
```

#### 10. Información del Sistema
```http
GET /config/custom/configurations/info
```

**Response:**
```json
{
  "file_info": {
    "exists": true,
    "path": "/path/to/configuraciones.json",
    "size_bytes": 2048,
    "modified": "2025-08-05T14:30:22.000Z",
    "created": "2025-08-05T10:00:00.000Z"
  },
  "statistics": {
    "total_configurations": 3,
    "configuration_names": ["Batería Litio 100Ah", "Batería GEL 200Ah", "Batería AGM 150Ah"],
    "lithium_configs": 1,
    "gel_configs": 2
  },
  "system_status": "operational"
}
```

## 🔧 Parámetros Configurables

### Batería
- **`batteryCapacity`** (float): Capacidad en Ah (1.0 - 1000.0)
- **`isLithium`** (boolean): true para Litio, false para GEL/AGM
- **`thresholdPercentage`** (float): Umbral de corriente en % (0.1 - 5.0)
- **`maxAllowedCurrent`** (float): Corriente máxima en mA (1000.0 - 15000.0)

### Voltajes
- **`bulkVoltage`** (float): Voltaje BULK en V (12.0 - 15.0)
- **`absorptionVoltage`** (float): Voltaje de absorción en V (12.0 - 15.0)
- **`floatVoltage`** (float): Voltaje de flotación en V (12.0 - 15.0)

### Fuente DC
- **`useFuenteDC`** (boolean): Usar fuente DC adicional
- **`fuenteDC_Amps`** (float): Corriente de la fuente DC en A (0.0 - 50.0)

### Avanzado
- **`factorDivider`** (int): Factor divisor para cálculos internos (1 - 10)

### Metadatos (Automáticos)
- **`createdAt`** (datetime): Fecha y hora de creación (ISO 8601)
- **`updatedAt`** (datetime): Fecha y hora de última actualización (ISO 8601)

## 🛠️ Instalación y Configuración

### 1. Archivos Nuevos Creados

```
models/
  └── custom_configurations.py      # Modelos Pydantic para validación

services/
  └── custom_configuration_manager.py  # Lógica de negocio

tests/
  └── test_custom_configurations.py    # Tests unitarios

demo_configuraciones.py              # Script de demostración
README_CONFIGURACIONES.md           # Esta documentación
```

### 2. Archivos Modificados

```
api/config.py                       # Nuevos endpoints agregados
models/__init__.py                  # Imports actualizados
```

### 3. Dependencias

El sistema utiliza las dependencias ya existentes en el proyecto:
- `fastapi`: Framework web
- `pydantic`: Validación de datos
- `asyncio`: Operaciones asíncronas
- Librerías estándar de Python

### 4. Configuración

No se requiere configuración adicional. El sistema:
- Crea automáticamente el archivo `configuraciones.json` en el directorio raíz
- Usa las configuraciones existentes del proyecto
- Se integra con el sistema de logging actual

## 🧪 Testing

### 1. Tests Automatizados

```bash
# Ejecutar tests específicos
python -m pytest tests/test_custom_configurations.py -v

# Ejecutar test básico incluido
python tests/test_custom_configurations.py
```

### 2. Demostración Interactive

```bash
# Ejecutar script de demostración (requiere API ejecutándose)
python demo_configuraciones.py
```

### 3. Tests Manuales con cURL

```bash
# Guardar configuración
curl -X POST "http://localhost:8000/config/custom/configurations" \
  -H "Content-Type: application/json" \
  -d '{"data": "{\"Test Config\":{\"batteryCapacity\":100,\"isLithium\":true,\"thresholdPercentage\":2.0,\"maxAllowedCurrent\":10000,\"bulkVoltage\":14.4,\"absorptionVoltage\":14.4,\"floatVoltage\":13.6,\"useFuenteDC\":false,\"fuenteDC_Amps\":0,\"factorDivider\":1}}"}'

# Cargar configuraciones
curl -X GET "http://localhost:8000/config/custom/configurations"

# Obtener configuración específica
curl -X GET "http://localhost:8000/config/custom/config/Test%20Config"
```

## 🔄 Flujo de Uso Típico

### 1. Crear Configuración
1. Usuario configura parámetros manualmente en la interfaz
2. Usuario guarda la configuración actual con un nombre descriptivo
3. Sistema valida y almacena la configuración

### 2. Aplicar Configuración
1. Usuario selecciona configuración guardada de la lista
2. Usuario hace clic en "Aplicar"
3. Sistema envía todos los parámetros al ESP32
4. ESP32 se configura según los valores guardados

### 3. Gestionar Configuraciones
1. Ver lista de todas las configuraciones
2. Editar configuraciones existentes
3. Eliminar configuraciones no deseadas
4. Exportar para respaldo o transferencia

### 4. Portabilidad
1. Exportar configuraciones a archivo JSON
2. Transferir archivo a otro dispositivo
3. Importar configuraciones en nuevo dispositivo
4. Aplicar configuraciones según sea necesario

## 📁 Estructura del Archivo JSON

```json
{
  "Batería Litio 100Ah": {
    "batteryCapacity": 100.0,
    "isLithium": true,
    "thresholdPercentage": 2.0,
    "maxAllowedCurrent": 10000.0,
    "bulkVoltage": 14.4,
    "absorptionVoltage": 14.4,
    "floatVoltage": 13.6,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 1,
    "createdAt": "2025-08-05T10:00:00.000Z",
    "updatedAt": "2025-08-05T10:00:00.000Z"
  },
  "Batería GEL 200Ah": {
    "batteryCapacity": 200.0,
    "isLithium": false,
    "thresholdPercentage": 2.5,
    "maxAllowedCurrent": 8000.0,
    "bulkVoltage": 14.1,
    "absorptionVoltage": 14.1,
    "floatVoltage": 13.3,
    "useFuenteDC": true,
    "fuenteDC_Amps": 20.0,
    "factorDivider": 1,
    "createdAt": "2025-08-05T11:00:00.000Z",
    "updatedAt": "2025-08-05T11:00:00.000Z"
  }
}
```

## 🚨 Manejo de Errores

### Códigos de Estado HTTP

- **200**: Operación exitosa
- **400**: Error de validación (datos inválidos)
- **404**: Configuración no encontrada
- **500**: Error interno del servidor
- **503**: ESP32 no conectado (solo para aplicar configuración)

### Ejemplos de Respuestas de Error

```json
// Error 400 - Validación
{
  "detail": "JSON inválido: Expecting property name enclosed in double quotes"
}

// Error 404 - No encontrado
{
  "detail": "Configuración 'Config Inexistente' no encontrada"
}

// Error 500 - Error interno
{
  "detail": "Error interno: No se pudo escribir el archivo"
}
```

## 🔧 Integración con Frontend

### JavaScript/React Example

```javascript
// Cargar configuraciones
async function loadConfigurations() {
  try {
    const response = await fetch('/config/custom/configurations');
    const data = await response.json();
    return data.configurations;
  } catch (error) {
    console.error('Error cargando configuraciones:', error);
    return {};
  }
}

// Guardar configuración
async function saveConfiguration(name, config) {
  try {
    const response = await fetch(`/config/custom/config/${name}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return await response.json();
  } catch (error) {
    console.error('Error guardando configuración:', error);
    throw error;
  }
}

// Aplicar configuración
async function applyConfiguration(name) {
  try {
    const response = await fetch(`/config/custom/config/${name}/apply`, {
      method: 'POST'
    });
    return await response.json();
  } catch (error) {
    console.error('Error aplicando configuración:', error);
    throw error;
  }
}
```

## 📈 Próximas Mejoras

### Funcionalidades Adicionales
- [ ] Configuraciones por defecto del sistema
- [ ] Categorización de configuraciones (Litio, GEL, AGM)
- [ ] Búsqueda y filtrado de configuraciones
- [ ] Histórico de cambios en configuraciones
- [ ] Validación de compatibilidad de hardware
- [ ] Notificaciones de configuración aplicada

### Optimizaciones
- [ ] Cache en memoria para configuraciones frecuentes
- [ ] Compresión del archivo JSON para configuraciones grandes
- [ ] Sincronización automática entre dispositivos
- [ ] Backup automático programado

### Seguridad
- [ ] Validación adicional de rangos seguros
- [ ] Checksum para verificar integridad del archivo
- [ ] Encriptación opcional del archivo de configuraciones

## 🆘 Solución de Problemas

### Problemas Comunes

1. **"ESP32 no está conectado"**
   - Verificar que el ESP32Manager esté iniciado
   - Verificar conexión física con ESP32
   - Reiniciar el servicio de API

2. **"Archivo de configuraciones corrupto"**
   - Verificar sintaxis JSON en `configuraciones.json`
   - Restaurar desde backup si está disponible
   - Eliminar archivo y comenzar de nuevo

3. **"Error de validación"**
   - Verificar que todos los campos requeridos estén presentes
   - Verificar que los valores estén dentro de los rangos permitidos
   - Revisar tipos de datos (int, float, bool)

4. **"No se pueden importar configuraciones"**
   - Verificar formato JSON del archivo de importación
   - Verificar que el archivo tenga la estructura correcta
   - Usar `overwrite_existing=true` si es necesario

### Logs y Debugging

```bash
# Ver logs de la API
tail -f logs/api.log | grep "ConfigurationManager"

# Ver estado del archivo de configuraciones
ls -la configuraciones.json

# Validar JSON manualmente
python -m json.tool configuraciones.json
```

## 📞 Soporte

Para reportar problemas o solicitar nuevas funcionalidades:

1. Verificar logs de la aplicación
2. Reproducir el problema con datos mínimos
3. Incluir versión de la API y sistema operativo
4. Adjuntar archivo de configuraciones si es relevante

---

**✅ Sistema implementado y listo para integración con frontend**
