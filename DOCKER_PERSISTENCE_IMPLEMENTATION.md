# 🐳 Persistencia de Configuraciones en Docker - IMPLEMENTADO

## ✅ **PROBLEMA RESUELTO**

### 🚨 **Antes (Riesgo de Pérdida de Datos)**
```yaml
volumes:
  - ./logs:/app/logs
  - ./data:/app/data
  # configuraciones.json NO persistente ❌
```

**Resultado:** Las configuraciones personalizadas se perdían con cada `docker-compose down/up`.

### ✅ **Después (Persistencia Garantizada)**
```yaml
volumes:
  - ./logs:/app/logs
  - ./data:/app/data
  - ./configuraciones.json:/app/configuraciones.json  # ← NUEVO ✅
  - /etc/localtime:/etc/localtime:ro
```

**Resultado:** Las configuraciones personalizadas **sobreviven** a los reinicios de Docker.

---

## 🔧 **Cambios Implementados**

### 1. **docker-compose.yml**
- ✅ Agregado volumen específico para `configuraciones.json`
- ✅ Montaje directo del archivo host → contenedor
- ✅ Compatible con RISC-V y emulación x86_64

### 2. **Script de Validación**
- ✅ `validate_persistence.sh` - Prueba automática de persistencia
- ✅ Verificación de integridad con hash MD5
- ✅ Prueba de API después del reinicio

---

## 🚀 **Uso en Producción**

### **Comandos Básicos**
```bash
# Levantar con persistencia
docker-compose up -d

# Verificar persistencia
./validate_persistence.sh

# Reiniciar (configuraciones se mantienen) - Método recomendado
./stop_api.sh && ./start_smart.sh

# Método manual adaptativo
if command -v "docker compose" > /dev/null 2>&1; then
    docker compose -f docker-compose.resolved.yml down && docker compose -f docker-compose.resolved.yml up -d
else
    docker-compose -f docker-compose.resolved.yml down && docker-compose -f docker-compose.resolved.yml up -d
fi
```

### **Verificar Estado**
```bash
# Ver configuraciones actuales
curl http://localhost:8000/config/custom/configurations

# Ver logs del contenedor
docker-compose logs -f esp32-api

# Verificar archivo en host
ls -la configuraciones.json
```

---

## 🌐 **Compatibilidad RISC-V**

### ✅ **Totalmente Compatible**
- **Emulación x86_64:** `--platform=linux/amd64` funciona en RISC-V
- **Volúmenes Docker:** Idéntico comportamiento en todas las arquitecturas
- **Persistencia:** Garantizada independiente de la arquitectura host

### 📊 **Rendimiento**
- **Overhead emulación:** Mínimo para operaciones de I/O
- **Acceso a archivos:** Nativo (sin penalización)
- **Red y volúmenes:** Rendimiento completo

---

## 🔍 **Verificación de Implementación**

### **Prueba Manual Rápida**
```bash
# 1. Crear configuración de prueba
curl -X POST "http://localhost:8000/config/custom/configurations/TestPersistencia" \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 50.0,
    "isLithium": true,
    "thresholdPercentage": 2.0,
    "maxAllowedCurrent": 5000.0,
    "bulkVoltage": 14.4,
    "absorptionVoltage": 14.4,
    "floatVoltage": 13.6,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 1
  }'

# 2. Verificar que se guardó
curl http://localhost:8000/config/custom/configurations

# 3. Reiniciar contenedores
docker-compose down && docker-compose up -d

# 4. Verificar que la configuración sigue ahí
curl http://localhost:8000/config/custom/configurations | grep TestPersistencia
```

### **Resultado Esperado**
- ✅ La configuración `TestPersistencia` debe aparecer después del reinicio
- ✅ El archivo `configuraciones.json` debe mantener su contenido
- ✅ No debe haber errores en los logs

---

## 📋 **Estado de Configuraciones Actuales**

### **Antes de la Implementación**
```json
{
  "GreenPoint20AH": {
    "batteryCapacity": 20.0,
    "isLithium": false,
    "thresholdPercentage": 3.0,
    "maxAllowedCurrent": 2500.0,
    "bulkVoltage": 14.6,
    "absorptionVoltage": 14.6,
    "floatVoltage": 13.8,
    "useFuenteDC": true,
    "fuenteDC_Amps": 3.0,
    "factorDivider": 5,
    "createdAt": "2025-08-07T17:59:52",
    "updatedAt": "2025-08-07T21:10:16"
  }
}
```

Esta configuración **ahora está protegida** y persistirá entre reinicios.

---

## 🛠️ **Troubleshooting**

### **Problema: Archivo no se monta**
```bash
# Verificar que el archivo existe antes del mount
ls -la configuraciones.json

# Si no existe, crear uno vacío
echo '{}' > configuraciones.json

# Reiniciar contenedores
docker-compose down && docker-compose up -d
```

### **Problema: Permisos**
```bash
# Verificar permisos
ls -la configuraciones.json

# Ajustar si es necesario (el usuario del contenedor necesita acceso)
chmod 666 configuraciones.json
```

### **Problema: Contenedor no inicia**
```bash
# Ver logs de errores
docker-compose logs esp32-api

# Verificar mount points
docker inspect esp32-solar-charger-api | grep -A 10 Mounts
```

---

## 🎯 **Próximos Pasos Recomendados**

1. **✅ COMPLETADO:** Implementar persistencia básica
2. **📋 Opcional:** Backup automático de configuraciones
3. **📋 Opcional:** Sincronización entre múltiples instancias
4. **📋 Opcional:** Versionado de configuraciones

---

## 📞 **Soporte**

Si experimentas problemas con la persistencia:

1. Ejecuta `./validate_persistence.sh`
2. Revisa logs con `docker-compose logs esp32-api`
3. Verifica permisos del archivo `configuraciones.json`
4. Confirma que Docker tiene acceso al directorio

**¡La persistencia de configuraciones está ahora GARANTIZADA en tu entorno RISC-V con Docker! 🚀**
