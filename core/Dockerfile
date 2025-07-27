# =============================================================================
# ESP32 Solar Charger API - Dockerfile para Emulación x86_64 en RISC-V
# =============================================================================

# STAGE 1: Builder (Emulado x86_64)
FROM --platform=linux/amd64 python:3.11-slim as builder

# Metadatos
LABEL maintainer="ESP32 Solar API"
LABEL description="ESP32 Solar Charger API emulado en x86_64 para RISC-V"
LABEL version="1.0.0"
LABEL platform="linux/amd64-emulated"

# Variables de entorno para build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema para build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements primero (para cache de Docker layers)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# =============================================================================
# STAGE 2: Runtime (Solo lo necesario para ejecución)
FROM --platform=linux/amd64 python:3.11-slim as runtime

# Variables de entorno para runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

# Crear usuario no-root para seguridad
RUN groupadd -r esp32api && \
    useradd -r -g esp32api -s /bin/bash esp32api

# Instalar solo dependencias runtime necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear directorios necesarios
RUN mkdir -p /app/logs /app/data && \
    chown -R esp32api:esp32api /app

# Copiar dependencias Python desde builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Establecer directorio de trabajo
WORKDIR /app

# Copiar código de la aplicación
COPY --chown=esp32api:esp32api . .

# Crear script de healthcheck
RUN echo '#!/bin/bash\ncurl -f http://localhost:8000/health || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh && \
    chown esp32api:esp32api /app/healthcheck.sh

# Crear script de inicio
RUN echo '#!/bin/bash\n\
echo "🚀 Iniciando ESP32 Solar Charger API (Emulado x86_64)"\n\
echo "📡 Puerto Serial: ${SERIAL_PORT:-/dev/ttyS5}"\n\
echo "🌐 Puerto HTTP: ${PORT:-8000}"\n\
echo "🏗️ Plataforma: $(uname -m) (emulado en RISC-V)"\n\
echo "🕐 Hora: $(date)"\n\
echo "==============================================="\n\
\n\
# Verificar puerto serial\n\
if [ ! -e "${SERIAL_PORT:-/dev/ttyS5}" ]; then\n\
    echo "⚠️ Puerto serial ${SERIAL_PORT:-/dev/ttyS5} no encontrado"\n\
    echo "Puertos disponibles:"\n\
    ls -la /dev/tty* 2>/dev/null | grep -E "(ttyS|ttyUSB|ttyACM)" || echo "No se encontraron puertos seriales"\n\
    echo ""\n\
fi\n\
\n\
# Verificar permisos\n\
if [ -e "${SERIAL_PORT:-/dev/ttyS5}" ]; then\n\
    if [ ! -r "${SERIAL_PORT:-/dev/ttyS5}" ] || [ ! -w "${SERIAL_PORT:-/dev/ttyS5}" ]; then\n\
        echo "⚠️ Sin permisos para ${SERIAL_PORT:-/dev/ttyS5}"\n\
        echo "Ejecuta: sudo chmod 666 ${SERIAL_PORT:-/dev/ttyS5}"\n\
    else\n\
        echo "✅ Permisos OK para ${SERIAL_PORT:-/dev/ttyS5}"\n\
    fi\n\
fi\n\
\n\
echo "🚀 Iniciando servidor..."\n\
exec python main.py' > /app/start.sh && \
    chmod +x /app/start.sh && \
    chown esp32api:esp32api /app/start.sh

# Cambiar a usuario no-root
USER esp32api

# Configurar variables de entorno por defecto
ENV SERIAL_PORT=/dev/ttyS5 \
    SERIAL_BAUDRATE=9600 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=False \
    LOG_LEVEL=INFO

# Exponer puerto
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ["/app/healthcheck.sh"]

# Punto de entrada
ENTRYPOINT ["/app/start.sh"]