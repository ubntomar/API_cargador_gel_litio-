# 🚀 ESP32 Solar Charger API - Resumen Ejecutivo para Frontend

## 📋 **INFORMACIÓN ESENCIAL**

- **🌐 Base URL:** `http://localhost:8000`
- **🔧 Estado:** Sistema completamente funcional y validado
- **📚 Documentación completa:** Ver archivos adjuntos
- **⚡ Polling recomendado:** 3 segundos para datos en tiempo real

---

## 🎯 **ENDPOINTS CRÍTICOS PARA FRONTEND**

### 1. 📊 **Datos en Tiempo Real**
```http
GET /data/
```
- **Función:** Obtener todos los datos actuales del ESP32
- **URL:** `http://localhost:8000/data/` ⚠️ DEBE incluir barra final
- **Frecuencia:** Cada 3 segundos (polling)
- **Datos clave:** voltaje, porcentaje batería, temperatura, estado carga

### 2. ⚙️ **Configuración Individual**
```http
POST /config/parameter
Body: {"parameter": "useFuenteDC", "value": true}
```
- **Función:** Cambiar parámetros individuales del cargador
- **Validación:** Inmediata del ESP32
- **Parámetros:** 10 parámetros configurables

### 3. 📋 **Gestión de Configuraciones**
```http
GET  /config/custom/configurations              # Listar
POST /config/custom/configurations/{name}       # Crear
POST /config/custom/configurations/{name}/apply # Aplicar
DELETE /config/custom/configurations/{name}     # Eliminar
```
- **Función:** Sistema completo de configuraciones predefinidas
- **Características:** CRUD completo, búsqueda, exportación

---

## 🔋 **CONFIGURACIONES TIPO BATERÍA**

### Litio (LiFePO4)
```json
{
  "batteryCapacity": 200.0,
  "isLithium": true,
  "thresholdPercentage": 3.0,
  "bulkVoltage": 14.6,
  "absorptionVoltage": 14.6,
  "floatVoltage": 13.8,
  "useFuenteDC": false
}
```

### GEL/AGM
```json
{
  "batteryCapacity": 100.0,
  "isLithium": false,
  "thresholdPercentage": 2.5,
  "bulkVoltage": 14.4,
  "absorptionVoltage": 14.4,
  "floatVoltage": 13.6,
  "useFuenteDC": true,
  "fuenteDC_Amps": 10.0
}
```

---

## 💡 **EJEMPLOS DE CÓDIGO MÍNIMOS**

### React - Polling de Datos
```javascript
const [data, setData] = useState(null);

useEffect(() => {
  const fetchData = async () => {
    // IMPORTANTE: usar /data/ con barra final
    const response = await fetch('http://localhost:8000/data/');
    setData(await response.json());
  };
  
  fetchData();
  const interval = setInterval(fetchData, 3000);
  return () => clearInterval(interval);
}, []);

// Uso: data.voltageBatterySensor2, data.estimatedSOC, data.chargeState, etc.
```

### Configurar Parámetro
```javascript
const setParameter = async (param, value) => {
  const response = await fetch('http://localhost:8000/config/parameter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parameter: param, value: value })
  });
  return response.json();
};

// Uso: setParameter('useFuenteDC', true)
```

### Aplicar Configuración Guardada
```javascript
const applyConfig = async (name) => {
  const response = await fetch(
    `http://localhost:8000/config/custom/configurations/${name}/apply`,
    { method: 'POST' }
  );
  return response.json();
};

// Uso: applyConfig('BateriaLitio200Ah')
```

---

## 📊 **DATOS DISPONIBLES EN TIEMPO REAL**

| Campo | Tipo | Descripción | Unidad |
|-------|------|-------------|--------|
| `voltageBatterySensor2` | number | Voltaje batería | V |
| `estimatedSOC` | number | Porcentaje carga estimado | % |
| `batteryCapacity` | number | Capacidad total | Ah |
| `chargeState` | string | Estado de carga (BULK_CHARGE, ABSORPTION_CHARGE, FLOAT_CHARGE) | - |
| `panelToBatteryCurrent` | number | Corriente panel a batería | mA |
| `batteryToLoadCurrent` | number | Corriente batería a carga | mA |
| `netCurrent` | number | Corriente neta | mA |
| `temperature` | number | Temperatura | °C |
| `currentPWM` | number | Valor PWM actual | 0-255 |
| `voltagePanel` | number | Voltaje panel solar | V |
| `isLithium` | boolean | Tipo batería | - |
| `useFuenteDC` | boolean | Fuente DC activa | - |
| `fuenteDC_Amps` | number | Amperaje fuente DC | A |
| `connected` | boolean | Conexión ESP32 activa | - |
| `firmware_version` | string | Versión firmware | - |
| `last_update` | string | Última actualización | ISO DateTime |

---

## 🚨 **MANEJO DE ERRORES**

### Estados de Conexión
```javascript
const checkConnection = async () => {
  try {
    const response = await fetch('http://localhost:8000/health');
    const health = await response.json();
    return health.esp32_connected; // true/false
  } catch {
    return false; // API no disponible
  }
};
```

### Códigos de Respuesta
- **200**: ✅ Éxito
- **400**: ❌ Parámetros incorrectos
- **503**: 🔌 ESP32 desconectado
- **500**: 💥 Error interno

---

## 📱 **COMPONENTES UI RECOMENDADOS**

### Dashboard Principal
1. **📊 Panel de datos** - Voltaje, porcentaje, temperatura
2. **⚡ Estado de carga** - Indicador visual + corriente
3. **🔋 Tipo de batería** - Litio/GEL con configuración
4. **🔌 Estado fuente DC** - Switch para activar/desactivar

### Gestión de Configuraciones
1. **📋 Lista de configuraciones** - Scroll con búsqueda
2. **➕ Crear nueva** - Formulario con validación
3. **🚀 Aplicar configuración** - Botón con confirmación
4. **💾 Exportar/Importar** - Backup y restauración

### Alertas y Notificaciones
1. **⚠️ Voltaje bajo** - < 11.5V
2. **🌡️ Temperatura alta** - > 40°C
3. **❌ Desconexión ESP32** - Pérdida de comunicación
4. **✅ Cambios aplicados** - Confirmación de parámetros

---

## 🔧 **PARÁMETROS CONFIGURABLES**

| Parámetro | Rango | Descripción |
|-----------|-------|-------------|
| `batteryCapacity` | 50-500 Ah | Capacidad nominal |
| `isLithium` | true/false | Tipo química |
| `thresholdPercentage` | 1-5% | Umbral descarga |
| `maxAllowedCurrent` | 1000-20000 mA | Corriente máxima |
| `bulkVoltage` | 13.8-15.0V | Voltaje bulk |
| `absorptionVoltage` | 13.8-15.0V | Voltaje absorción |
| `floatVoltage` | 13.0-14.0V | Voltaje flotación |
| `useFuenteDC` | true/false | Activar fuente DC |
| `fuenteDC_Amps` | 0-20A | Amperaje fuente DC |
| `factorDivider` | 1-10 | Factor división |

---

## 📚 **DOCUMENTACIÓN DETALLADA**

### Para implementación completa consultar:

1. **[`FRONTEND_API_DOCUMENTATION.md`](./FRONTEND_API_DOCUMENTATION.md)**
   - 📖 Documentación completa de todos los endpoints
   - 🔍 Ejemplos de peticiones y respuestas
   - 🚨 Códigos de error y manejo

2. **[`FRONTEND_EXAMPLES.md`](./FRONTEND_EXAMPLES.md)**
   - 💡 Componentes React completos
   - 🎨 Estilos CSS recomendados
   - 🔧 Hooks personalizados
   - 📱 Integraciones con frameworks

3. **[`API_QUICK_REFERENCE.md`](./API_QUICK_REFERENCE.md)**
   - ⚡ Cheat sheet de endpoints
   - 📋 Referencia rápida de parámetros
   - 🎯 Ejemplos de código mínimos

---

## ✅ **CHECKLIST DE IMPLEMENTACIÓN**

### Frontend Básico
- [ ] 📊 Dashboard con datos en tiempo real (polling 3s)
- [ ] ⚙️ Panel configuración parámetros individuales
- [ ] 🏥 Indicador estado conexión ESP32
- [ ] 🚨 Sistema básico de alertas

### Frontend Avanzado
- [ ] 📋 Lista de configuraciones personalizadas
- [ ] ➕ Formulario crear nueva configuración
- [ ] 🚀 Aplicar configuraciones con un clic
- [ ] 💾 Exportar/importar configuraciones
- [ ] 🔍 Búsqueda y filtrado
- [ ] 📱 Diseño responsive

### Opcional
- [ ] ⏰ Programación de horarios
- [ ] 📊 Gráficos históricos
- [ ] 🔔 Notificaciones push
- [ ] 🎨 Temas personalizables

---

## 🎯 **RESUMEN EJECUTIVO**

**El API está 100% funcional y listo para integración frontend.**

- ✅ **Comunicación ESP32**: Probada y estable
- ✅ **Endpoints**: Todos validados y documentados
- ✅ **Configuraciones**: Sistema completo operativo
- ✅ **Thread safety**: Soporta múltiples peticiones concurrentes
- ✅ **Documentación**: Completa con ejemplos prácticos

**🚀 Puedes comenzar la implementación frontend inmediatamente usando esta documentación.**

---

**📞 Para dudas específicas o problemas técnicos, consultar los logs del API o revisar la documentación detallada en los archivos adjuntos.**
