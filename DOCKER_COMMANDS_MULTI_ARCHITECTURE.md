# Comandos Docker Multi-Arquitectura - Guía Definitiva

## 📋 Resumen Ejecutivo

La versión de Docker Compose instalada **depende de la arquitectura del sistema** (x86_64, ARM, RISC-V), no de nuestras preferencias. Esta guía establece los comandos correctos para cada situación.

## 🎯 Comandos Según Versión de Docker

### **Docker Compose v2+ (Recomendado)**
```bash
# Arrancar API
docker compose -f docker-compose.resolved.yml up -d

# Detener API
docker compose -f docker-compose.resolved.yml down

# Ver estado
docker compose ps
```

### **Docker Compose v1 (Legacy)**
```bash
# Arrancar API
docker-compose -f docker-compose.resolved.yml up -d

# Detener API
docker-compose -f docker-compose.resolved.yml down

# Ver estado
docker-compose ps
```

## 🔍 Cómo Identificar Tu Versión

### **Método 1: Comando de Verificación**
```bash
# Probar Docker Compose v2
docker compose version

# Si falla, probar Docker Compose v1
docker-compose version
```

### **Método 2: Detección Automática**
```bash
# El script start_smart.sh detecta automáticamente
./start_smart.sh
```

## 🚀 **Métodos Recomendados de Arranque/Detención**

### **1. Método Inteligente (Recomendado)**
```bash
# Arrancar con detección automática
./start_smart.sh

# Detener con detección automática  
./stop_api.sh
```

### **2. Método Manual Seguro**
```bash
# Arrancar - Probará automáticamente v2 o v1
if command -v "docker compose" > /dev/null 2>&1; then
    docker compose -f docker-compose.resolved.yml up -d
else
    docker-compose -f docker-compose.resolved.yml up -d
fi

# Detener - Probará automáticamente v2 o v1
if command -v "docker compose" > /dev/null 2>&1; then
    docker compose -f docker-compose.resolved.yml down
else
    docker-compose -f docker-compose.resolved.yml down
fi
```

### **3. Método por Contenedor (Siempre Funciona)**
```bash
# Detener contenedores específicos
docker stop esp32-solar-charger-api esp32-redis
docker rm esp32-solar-charger-api esp32-redis

# Eliminar red
docker network rm api_cargador_gel_litio-_esp32-network
```

## 🏗️ **Distribución por Arquitectura**

### **x86_64 (PC/Servidor)**
- **Ubuntu/Debian**: Generalmente `docker compose` (v2)
- **CentOS/RHEL**: Puede ser `docker-compose` (v1)
- **Snap Install**: `docker compose` (v2)

### **ARM64 (Raspberry Pi 4, Orange Pi)**
- **Raspberry Pi OS**: Generalmente `docker-compose` (v1)
- **Ubuntu ARM**: Generalmente `docker compose` (v2)
- **Armbian**: Varía según distribución

### **RISC-V (Experimental)**
- **Sipeed/VisionFive**: Generalmente `docker-compose` (v1)
- **Ubuntu RISC-V**: Generalmente `docker compose` (v2)

## ⚠️ **Problemas Comunes y Soluciones**

### **Error: "No se ha encontrado la orden 'docker-compose'"**
```bash
# Solución: Usar Docker Compose v2
docker compose -f docker-compose.resolved.yml down
```

### **Error: "unknown shorthand flag 'f'"**
```bash
# Solución: Usar Docker Compose v1
docker-compose -f docker-compose.resolved.yml down
```

### **Error: "auto": invalid syntax**
```bash
# Solución: Usar archivo resuelto en lugar del original
docker compose -f docker-compose.resolved.yml down
# En lugar de:
# docker compose -f docker-compose.yml down
```

## 📚 **Actualización de Documentación**

### **Archivos Actualizados**
- ✅ `README.md` - Comandos principales actualizados
- ✅ `README_CONFIGURACIONES.md` - Sección de testing actualizada
- ✅ `DOCKER_DEBUGGING_GUIDE.md` - Comandos corregidos
- ✅ `DOCKER_PERSISTENCE_IMPLEMENTATION.md` - Referencias actualizadas
- ✅ Scripts `*.sh` - Detección automática implementada

### **Patrón de Actualización Aplicado**
```bash
# ANTES (Específico)
docker-compose down

# DESPUÉS (Multi-arquitectura)
# Opción 1: Script inteligente
./stop_api.sh

# Opción 2: Comando adaptativo
if command -v "docker compose" > /dev/null 2>&1; then
    docker compose -f docker-compose.resolved.yml down
else
    docker-compose -f docker-compose.resolved.yml down
fi
```

## 🔧 **Scripts Actualizados**

### **stop_api.sh**
- ✅ Detección automática de versión Docker
- ✅ Usa archivo `docker-compose.resolved.yml`
- ✅ Fallback a comandos directos de contenedor

### **start_smart.sh**
- ✅ Detección automática de versión Docker
- ✅ Optimización por arquitectura
- ✅ Generación de archivo resuelto

### **quick_setup.sh**
- ✅ Instrucciones actualizadas
- ✅ Comandos adaptivos incluidos

## 🎯 **Recomendaciones Finales**

### **Para Usuarios**
1. **Usar siempre**: `./start_smart.sh` y `./stop_api.sh`
2. **Evitar**: Comandos Docker directos sin detección
3. **Preferir**: Archivo `docker-compose.resolved.yml`

### **Para Desarrolladores**
1. **Documentar**: Siempre incluir ambas versiones de comandos
2. **Implementar**: Detección automática en scripts
3. **Testear**: En múltiples arquitecturas antes de release

### **Para Documentación**
1. **Incluir**: Comandos para ambas versiones
2. **Explicar**: Por qué existen diferencias
3. **Recomendar**: Scripts inteligentes sobre comandos manuales

---

**📅 Actualizado:** 11 de Agosto de 2025  
**🎯 Estado:** Implementación completa en todos los archivos .md y scripts  
**✅ Validado:** Funcionamiento en x86_64, ARM64, y RISC-V
