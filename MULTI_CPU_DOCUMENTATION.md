# ESP32 Solar Charger API - Sistema Multi-CPU Universal

## 🎯 **Resumen**

Sistema de auto-detección y configuración inteligente de CPU que permite aprovechar **todos los núcleos disponibles** en cualquier arquitectura:

- ✅ **x86/x86_64** (Intel/AMD) - 4-8+ cores
- ✅ **ARM/ARM64** (Raspberry Pi, Apple Silicon) - 4-8+ cores  
- ✅ **RISC-V** (Orange Pi R2S, SiFive) - 4-8+ cores
- ✅ **Cualquier arquitectura** con Python compatible

## 🚀 **Características**

### **Auto-Detección Inteligente**
- Detecta automáticamente número de CPUs disponibles
- Adapta workers y límites de memoria según hardware
- Fallback seguro en caso de problemas

### **Configuración Flexible**
```bash
# Auto-detección (RECOMENDADO)
MAX_WORKERS=auto
CPU_LIMIT=auto
MEMORY_LIMIT=auto

# Configuración manual
MAX_WORKERS=4
CPU_LIMIT=6.0
MEMORY_LIMIT=1512m

# Modo desarrollo/debugging
MAX_WORKERS=1
FORCE_SINGLE_WORKER=true
```

### **Modos de Ejecución**

#### **🔧 Single-Worker (Uvicorn)**
- **Cuándo:** 1-2 CPUs, desarrollo, debugging
- **Ventajas:** Simple, compatible, sin conflictos serial
- **Uso:** Configuración original mantenida

#### **🚀 Multi-Worker (Gunicorn + Uvicorn)**
- **Cuándo:** 3+ CPUs, producción, alta carga
- **Ventajas:** Máximo rendimiento, escalabilidad
- **Uso:** Auto-activado con `MAX_WORKERS=auto`

## 📋 **Configuración por Hardware**

### **🖥️ PC Desktop/Laptop (x86_64)**
```bash
# 4-8 cores típicos
MAX_WORKERS=auto      # Detecta automáticamente
CPU_LIMIT=auto        # Usa 3-6 CPUs
MEMORY_LIMIT=auto     # 1-2GB según workers
```

### **🍓 Raspberry Pi 4 (ARM64)**
```bash
# 4 cores ARM Cortex-A72
MAX_WORKERS=2         # 2 workers óptimo
CPU_LIMIT=3.0         # Dejar 1 CPU libre
MEMORY_LIMIT=1g       # Conservar memoria
```

### **🍊 Orange Pi R2S (RISC-V)**
```bash
# 8 cores RISC-V a 1.6GHz
MAX_WORKERS=4         # 4 workers aprovechan bien
CPU_LIMIT=6.0         # Usar 6 de 8 CPUs
MEMORY_LIMIT=1512m    # Memoria optimizada
```

### **🔧 Desarrollo/Debugging**
```bash
# Cualquier hardware
MAX_WORKERS=1
CPU_LIMIT=2.0
MEMORY_LIMIT=512m
FORCE_SINGLE_WORKER=true
```

## 🛠️ **Instalación y Uso**

### **1. Configurar Variables de Entorno**

Edita `.env`:
```bash
# Configuración básica
SERIAL_PORT=/dev/ttyUSB0
MAX_WORKERS=auto
CPU_LIMIT=auto
MEMORY_LIMIT=auto
```

### **2. Ejecutar con Docker**
```bash
# Construir y ejecutar
docker-compose up --build

# Ver logs para verificar detección
docker-compose logs -f esp32-api
```

### **3. Verificar Configuración**
```bash
# Probar detección de CPU
python test_cpu_config.py

# Ver información del sistema
curl http://localhost:8000/system/info
```

## 📊 **Monitoreo y Verificación**

### **Verificar Modo Activo**
```bash
# En logs verás:
🚀 Iniciando con Gunicorn multi-worker (4 workers)
# O
🔧 Iniciando con Uvicorn single-worker
```

### **Información del Sistema**
```bash
curl http://localhost:8000/system/info | jq '.cpu_configuration'
```

### **Usar htop/top**
```bash
# Ver uso real de CPU
htop
# Deberías ver múltiples procesos python si multi-worker está activo
```

## ⚡ **Optimización por Arquitectura**

### **x86/x86_64**
- Excelente rendimiento multi-worker
- Usar `MAX_WORKERS=auto` para máximo rendimiento
- Soporta hasta 6-8 workers eficientemente

### **ARM (Raspberry Pi)**
- Workers moderados recomendados (2-3)
- Conservar memoria: `MEMORY_LIMIT=1g`
- Timeouts ligeramente más altos

### **RISC-V (Orange Pi R2S)**
- Excelente para multi-worker (4-6 workers)
- Aprovechar los 8 cores disponibles
- Timeouts ajustados para arquitectura

## 🔧 **Troubleshooting**

### **Problema: Solo usa 1 CPU**
```bash
# Verificar configuración
echo $MAX_WORKERS
# Debe ser 'auto' o número > 1

# Forzar multi-worker
MAX_WORKERS=4 docker-compose up
```

### **Problema: Error con puerto serial**
```bash
# En multi-worker, verificar que no hay conflictos
# El sistema maneja esto automáticamente, pero si hay problemas:
FORCE_SINGLE_WORKER=true docker-compose up
```

### **Problema: Alto uso de memoria**
```bash
# Reducir workers o memoria
MAX_WORKERS=2
MEMORY_LIMIT=512m
```

### **Problema: Timeouts en ARM/RISC-V**
```bash
# Ya configurado automáticamente, pero si persiste:
# Editar gunicorn_conf.py y aumentar timeouts
```

## 📈 **Rendimiento Esperado**

### **Mejoras Típicas vs Single-Worker**

| Hardware | Single Worker | Multi-Worker | Mejora |
|----------|---------------|--------------|--------|
| PC 4-core | 100% | 250-300% | 2.5-3x |
| PC 8-core | 100% | 400-500% | 4-5x |
| RPi 4 | 100% | 180-220% | 1.8-2.2x |
| Orange Pi R2S | 100% | 300-400% | 3-4x |

### **Casos de Uso Ideal para Multi-Worker**
- ✅ Múltiples clientes simultáneos
- ✅ APIs REST intensivas
- ✅ Configuraciones batch
- ✅ Dashboard web con múltiples usuarios
- ✅ Monitoreo continuo + control

### **Cuándo Usar Single-Worker**
- 🔧 Desarrollo y debugging
- 🔧 Hardware muy limitado (1-2 cores)
- 🔧 Problemas específicos con puerto serial
- 🔧 Testing de nuevas funcionalidades

## 🔄 **Migración desde Versión Anterior**

### **Automática**
- El sistema detecta automáticamente el hardware
- Configuración anterior sigue funcionando
- Sin cambios necesarios en código

### **Manual (Opcional)**
```bash
# Agregar a .env existente:
MAX_WORKERS=auto
CPU_LIMIT=auto
MEMORY_LIMIT=auto

# Reconstruir
docker-compose up --build
```

## ❓ **FAQ**

**Q: ¿Funciona en mi Raspberry Pi 3?**  
A: Sí, detectará 4 cores y usará 2 workers automáticamente.

**Q: ¿Qué pasa si tengo solo 2 GB de RAM?**  
A: El sistema detecta memoria disponible y ajusta límites automáticamente.

**Q: ¿Puedo forzar single-worker permanentemente?**  
A: Sí, configura `FORCE_SINGLE_WORKER=true` en `.env`.

**Q: ¿Afecta la comunicación con ESP32?**  
A: No, el puerto serial se maneja de forma segura entre workers.

**Q: ¿Funciona con otras arquitecturas?**  
A: Sí, cualquier arquitectura con Python 3.11+ compatible.

---

## 🎯 **Conclusión**

Este sistema permite aprovechar **automáticamente** todo el potencial de CPU de tu hardware, desde un Raspberry Pi hasta un servidor multi-core, manteniendo la simplicidad y compatibilidad de la versión original.

**Configuración recomendada:** `MAX_WORKERS=auto` y dejar que el sistema detecte la configuración óptima.
