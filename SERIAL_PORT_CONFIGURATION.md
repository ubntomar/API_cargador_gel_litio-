# 🔧 Configuración Simplificada del Puerto Serial

Este documento explica cómo configurar el puerto serial del ESP32 de forma simple, usando solo el archivo `.env`.

## ✅ **Configuración Súper Simple**

### Método 1: Editar .env directamente
```bash
# Editar el archivo .env
nano .env

# Cambiar la línea:
SERIAL_PORT=/dev/ttyUSB0

# Por tu puerto específico, ejemplo:
SERIAL_PORT=/dev/ttyUSB1

# Reiniciar Docker
docker-compose restart
```

### Método 2: Usar script automático
```bash
# Menú interactivo
./configure_serial_port.sh

# O cambio directo
./configure_serial_port.sh set /dev/ttyUSB1
```

## 🔍 **Identificar tu Puerto Serial**

### En Orange Pi R2S:
```bash
# Ver puertos USB conectados
ls -la /dev/ttyUSB*

# Ver información de dispositivos USB
lsusb

# Ver log del kernel para dispositivos conectados
dmesg | grep tty | tail -10
```

### Puertos Comunes:
- **Orange Pi R2S**: `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyS5`
- **Raspberry Pi**: `/dev/ttyACM0`, `/dev/ttyUSB0`
- **PC Linux**: `/dev/ttyUSB0`, `/dev/ttyACM0`

## 🚀 **Proceso Completo**

1. **Identificar puerto**:
   ```bash
   ./configure_serial_port.sh list
   ```

2. **Configurar puerto**:
   ```bash
   ./configure_serial_port.sh set /dev/ttyUSB1
   ```

3. **Verificar cambio**:
   ```bash
   ./configure_serial_port.sh current
   ```

4. **Reiniciar API**:
   ```bash
   docker-compose restart
   ```

5. **Verificar funcionamiento**:
   ```bash
   curl -s http://localhost:8000/health | jq '.'
   ```

## 📋 **Variables de Entorno Disponibles**

En el archivo `.env` puedes configurar:

```bash
# Puerto serial (lo más importante)
SERIAL_PORT=/dev/ttyUSB0

# Velocidad de comunicación
SERIAL_BAUDRATE=9600

# Timeout de comunicación
SERIAL_TIMEOUT=3.0

# Logging
LOG_LEVEL=INFO

# Rate limiting
MIN_COMMAND_INTERVAL=0.6
MAX_REQUESTS_PER_MINUTE=60
```

## 🔧 **Arquitectura de la Solución**

```mermaid
graph LR
    A[.env] --> B[docker-compose.yml]
    B --> C[Docker Container]
    C --> D[ESP32 via Serial]
    
    E[configure_serial_port.sh] --> A
    F[Usuario] --> E
```

### Flujo:
1. Usuario modifica `.env` (manual o script)
2. Docker Compose lee variables de `.env`
3. Contenedor se configura con puerto correcto
4. API se conecta al ESP32

## ⚠️ **Solución de Problemas**

### Error: "Permission denied"
```bash
# Agregar usuario al grupo dialout
sudo usermod -a -G dialout $USER

# Logout y login nuevamente
```

### Error: "Device not found"
```bash
# Verificar que el dispositivo existe
ls -la /dev/ttyUSB*

# Verificar permisos
ls -la /dev/ttyUSB0
```

### Error: "Device busy"
```bash
# Verificar que no esté siendo usado
lsof /dev/ttyUSB0

# Matar procesos que lo usen
sudo fuser -k /dev/ttyUSB0
```

## 🎯 **Ventajas de esta Implementación**

1. **Simplicidad**: Solo modificar un archivo
2. **Flexibilidad**: Soporte para cualquier puerto
3. **Automatización**: Script para cambios rápidos
4. **Portabilidad**: Funciona en cualquier sistema
5. **Sin Hardcoding**: No hay valores fijos en Docker Compose
6. **Rollback Fácil**: Cambios reversibles instantáneamente

## 📱 **Uso en Diferentes Dispositivos**

### Orange Pi R2S:
```bash
SERIAL_PORT=/dev/ttyUSB0  # Puerto USB más común
```

### Raspberry Pi:
```bash
SERIAL_PORT=/dev/ttyACM0  # Puerto ACM común en RPi
```

### PC de Desarrollo:
```bash
SERIAL_PORT=/dev/ttyUSB0  # Puerto USB estándar
```

¡Ahora solo necesitas modificar el `.env` y reiniciar Docker para cambiar el puerto serial! 🎉
