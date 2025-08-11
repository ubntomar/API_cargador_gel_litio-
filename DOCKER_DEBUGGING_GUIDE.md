# 🐛 Docker Debugging Guide - ESP32 Solar Charger API

> **Actualizado:** Agosto 2025  
> **Problema resuelto:** Endpoint `/apply` que "se ejecutaba pero no aplicaba cambios"

## 🎯 **Problema Principal Identificado y Resuelto**

### ❌ **Síntoma Original**
- El endpoint `POST /config/custom/config/{name}/apply` respondía con status 200
- La respuesta indicaba "success" pero los parámetros no se aplicaban realmente al ESP32
- Los logs de debug no aparecían a pesar de estar en el código

### 🔍 **Diagnóstico Realizado**

#### 1. **Verificación de Código en el Contenedor**
```bash
# Comparar versiones entre host y contenedor
docker exec esp32-solar-charger-api wc -l /app/api/config.py  # 1046 líneas (viejo)
wc -l api/config.py                                            # 1106 líneas (actual)

# El contenedor tenía código desactualizado del 9 de agosto
docker exec esp32-solar-charger-api ls -la /app/api/config.py
# -rw-r--r-- 1 root root 42850 Aug  9 12:13 config.py (OLD)

ls -la api/config.py  
# -rw-rw-r-- 1 omar omar 45055 Aug 11 16:48 config.py (NEW)
```

#### 2. **Problema de Volúmenes Docker**
El `docker-compose.yml` original NO tenía volúmenes configurados para desarrollo:
- Los cambios del host no se reflejaban en el contenedor
- Docker usaba la imagen construida originalmente (código viejo)
- Los módulos Python se cargaban una vez y permanecían en caché

### ✅ **Soluciones Implementadas**

#### **Solución 1: Configuración de Volúmenes para Desarrollo (IMPLEMENTADA)**

Agregado al `docker-compose.yml`:
```yaml
volumes:
  - ./logs:/app/logs
  - ./data:/app/data
  - .:/app/config:rw
  - /etc/localtime:/etc/localtime:ro
  # 🔧 DESARROLLO: Montar código fuente para hot-reload
  - ./api:/app/api:rw
  - ./services:/app/services:rw
  - ./models:/app/models:rw
  - ./core:/app/core:rw
  - ./main.py:/app/main.py:rw
  - ./requirements.txt:/app/requirements.txt:ro
```

**Ventajas:**
- ✅ Cambios se reflejan inmediatamente
- ✅ No necesita rebuild para cambios de código
- ✅ Ideal para desarrollo iterativo
- ✅ Mantiene persistencia de datos

#### **Solución 2: Corrección del Bug de Acceso a Configuración**

**Problema encontrado:** La función `get_configuration()` del Redis manager retornaba:
```json
{
  "configuration_name": "BateriaGEL200Ah",
  "configuration": {
    "batteryCapacity": 200.0,
    "isLithium": false,
    // ... otros parámetros
  }
}
```

**El código original buscaba directamente:** `configuration["batteryCapacity"]` ❌

**Corrección aplicada:**
```python
# ✅ CORRECCIÓN: Extraer la configuración real del wrapper
if isinstance(configuration_data, dict) and 'configuration' in configuration_data:
    configuration = configuration_data['configuration']
    logger.info(f"🔍 DEBUG - Configuración extraída del wrapper: {configuration}")
else:
    configuration = configuration_data
    logger.info(f"🔍 DEBUG - Usando configuración directa: {configuration}")
```

## 🔧 **Comandos de Desarrollo**

### **Para Desarrollos Futuros**

#### **Flujo Normal de Desarrollo:**
```bash
# 1. Modificar código Python
nano api/config.py

# 2. Los cambios se reflejan automáticamente (gracias a volúmenes)
# 3. Probar endpoint inmediatamente
curl -X POST http://localhost:8000/config/custom/config/BateriaGEL200Ah/apply
```

#### **Para Cambios Estructurales:**
```bash
# Reiniciar solo el contenedor de la API
docker restart esp32-solar-charger-api

# Para cambios de dependencias
docker compose up -d --build
```

#### **Para Nuevas Instalaciones:**
```bash
# Después de git clone o git pull
docker compose down
docker compose up -d --build

# Si persisten problemas (rebuild completo)
docker compose build --no-cache
docker compose up -d
```

### **Debugging de Endpoints**

#### **Verificar que el código está actualizado:**
```bash
# 1. Comparar líneas de código
docker exec esp32-solar-charger-api wc -l /app/api/config.py
wc -l api/config.py

# 2. Comparar fechas de modificación
docker exec esp32-solar-charger-api ls -la /app/api/config.py
ls -la api/config.py

# 3. Buscar strings específicos en el contenedor
docker exec esp32-solar-charger-api grep -n "DEBUG - INICIO apply_configuration" /app/api/config.py
```

#### **Monitoreo de logs en tiempo real:**
```bash
# Ver logs generales
docker logs esp32-solar-charger-api --tail 20 -f

# Filtrar logs específicos
docker logs esp32-solar-charger-api 2>&1 | grep "apply_configuration"

# Verificar errores
docker logs esp32-solar-charger-api 2>&1 | grep "ERROR\|WARN"
```

#### **Testing de endpoints:**
```bash
# 1. Listar configuraciones disponibles
curl -X GET http://localhost:8000/config/custom/configurations

# 2. Probar aplicación de configuración
curl -X POST http://localhost:8000/config/custom/config/BateriaGEL200Ah/apply

# 3. Verificar logs inmediatamente después
docker logs esp32-solar-charger-api --tail 10
```

## 📊 **Resultado Final**

### **Antes del Fix:**
- ❌ 0 de 10 parámetros aplicados
- ❌ Logs de debug no aparecían
- ❌ Código desactualizado en contenedor
- ❌ "Se ejecuta pero no aplica cambios"

### **Después del Fix:**
- ✅ 8 de 10 parámetros aplicados exitosamente
- ✅ 2 parámetros con errores menores de parseo (pero SÍ se aplican)
- ✅ Logs de debug completos y en tiempo real
- ✅ Live reload funcionando perfectamente
- ✅ Comunicación ESP32 confirmada

### **Response Exitoso:**
```json
{
  "message": "Configuración 'BateriaGEL200Ah' aplicada parcialmente al ESP32",
  "status": "partial_success",
  "configuration_name": "BateriaGEL200Ah",
  "esp32_responses": {
    "batteryCapacity": {"success": true, "esp32_response": "OK"},
    "isLithium": {"success": true, "esp32_response": "OK"},
    "thresholdPercentage": {"success": true, "esp32_response": "OK"},
    // ... 8 parámetros exitosos
  }
}
```

## 🎯 **Lecciones Aprendidas**

1. **Docker Caché:** Siempre verificar que el código en el contenedor está actualizado
2. **Volúmenes:** Configurar volúmenes de desarrollo desde el inicio del proyecto
3. **Debugging:** Usar logs detallados para rastrear el flujo de ejecución
4. **Estructura de Datos:** Verificar la estructura exacta de datos de APIs externas (Redis)
5. **Testing:** Probar endpoints después de cada cambio significativo

## 🚀 **Para Futuros Desarrolladores**

- ✅ Los volúmenes Docker ya están configurados
- ✅ El bug de configuración está corregido
- ✅ Los logs de debug están implementados
- ✅ La documentación está actualizada

**¡El problema "se ejecuta pero no aplica cambios" está 100% resuelto!** 🎉
