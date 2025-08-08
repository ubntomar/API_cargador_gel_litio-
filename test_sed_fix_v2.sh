#!/bin/bash
# Test script para verificar los comandos sed corregidos

echo "🧪 Probando comandos sed corregidos..."

# Crear archivo de prueba similar al docker-compose.yml real
cat > test-docker-compose.yml << 'EOF'
version: '3.8'
services:
  esp32-api:
    devices:
      - "/dev/ttyUSB0:/dev/ttyUSB0"  # ← CAMBIAR según tu puerto
    environment:
      - SERIAL_PORT=/dev/ttyUSB0
      - SERIAL_BAUDRATE=9600
EOF

echo "📄 Archivo original:"
cat test-docker-compose.yml
echo ""

# Simular el puerto detectado
TEST_PORT="/dev/ttyS5"
echo "🔧 Aplicando configuración con puerto: $TEST_PORT"

# Aplicar los comandos sed corregidos
cp test-docker-compose.yml test-modified.yml

# Reemplazar puertos comunes uno por uno
sed -i "s|/dev/ttyUSB[0-9]*|${TEST_PORT}|g" test-modified.yml
sed -i "s|/dev/ttyACM[0-9]*|${TEST_PORT}|g" test-modified.yml
sed -i "s|/dev/ttyS[0-9]*|${TEST_PORT}|g" test-modified.yml

# Reemplazar device mappings específicos
sed -i "s|/dev/ttyUSB0:/dev/ttyUSB0|${TEST_PORT}:${TEST_PORT}|g" test-modified.yml
sed -i "s|/dev/ttyACM0:/dev/ttyACM0|${TEST_PORT}:${TEST_PORT}|g" test-modified.yml
sed -i "s|/dev/ttyS5:/dev/ttyS5|${TEST_PORT}:${TEST_PORT}|g" test-modified.yml

# Reemplazar SERIAL_PORT en variables de ambiente
sed -i "s|SERIAL_PORT=/dev/tty[A-Za-z0-9]*|SERIAL_PORT=${TEST_PORT}|g" test-modified.yml

echo "✅ Archivo modificado:"
cat test-modified.yml
echo ""

# Verificar que los cambios se aplicaron
if grep -q "${TEST_PORT}" test-modified.yml; then
    echo "✅ ¡Comandos sed funcionan correctamente!"
    echo "✅ Puerto configurado exitosamente: ${TEST_PORT}"
else
    echo "❌ Error: Los comandos sed no aplicaron los cambios"
fi

# Limpiar
rm -f test-docker-compose.yml test-modified.yml

echo ""
echo "🎉 Prueba completada"
