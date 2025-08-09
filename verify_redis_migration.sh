#!/bin/bash
# Verificación de migración a Redis para configuraciones personalizadas

API_URL="http://localhost:8000"
REMOTE_URL="http://192.168.13.180:8000"

echo "🔍 VERIFICACIÓN DE MIGRACIÓN A REDIS"
echo "======================================"

# Seleccionar URL según disponibilidad
if curl -s --connect-timeout 3 "$API_URL/health" > /dev/null 2>&1; then
    BASE_URL="$API_URL"
    echo "✅ Usando API local: $BASE_URL"
elif curl -s --connect-timeout 3 "$REMOTE_URL/health" > /dev/null 2>&1; then
    BASE_URL="$REMOTE_URL"
    echo "✅ Usando API remota: $BASE_URL"
else
    echo "❌ ERROR: No se puede conectar a ninguna API"
    exit 1
fi

echo ""

# 1. Verificar información de storage
echo "📊 1. Verificando información de storage..."
STORAGE_INFO=$(curl -s "$BASE_URL/config/custom/configurations/storage-info")
echo "$STORAGE_INFO" | python3 -m json.tool 2>/dev/null || echo "$STORAGE_INFO"
echo ""

# 2. Verificar configuraciones existentes ANTES de migración
echo "📋 2. Configuraciones existentes..."
CONFIGS_BEFORE=$(curl -s "$BASE_URL/config/custom/configurations")
COUNT_BEFORE=$(echo "$CONFIGS_BEFORE" | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
echo "Total configuraciones antes: $COUNT_BEFORE"
echo ""

# 3. Ejecutar migración
echo "🔄 3. Ejecutando migración a Redis..."
MIGRATION_RESULT=$(curl -s -X POST "$BASE_URL/config/custom/configurations/migrate")
echo "$MIGRATION_RESULT" | python3 -m json.tool 2>/dev/null || echo "$MIGRATION_RESULT"
echo ""

# 4. Verificar configuraciones DESPUÉS de migración
echo "✅ 4. Verificando configuraciones después de migración..."
sleep 2  # Dar tiempo para que se complete
CONFIGS_AFTER=$(curl -s "$BASE_URL/config/custom/configurations")
COUNT_AFTER=$(echo "$CONFIGS_AFTER" | grep -o '"total_count":[0-9]*' | cut -d':' -f2)
echo "Total configuraciones después: $COUNT_AFTER"
echo ""

# 5. Verificar información de storage actualizada
echo "📊 5. Información de storage post-migración..."
STORAGE_INFO_AFTER=$(curl -s "$BASE_URL/config/custom/configurations/storage-info")
echo "$STORAGE_INFO_AFTER" | python3 -m json.tool 2>/dev/null || echo "$STORAGE_INFO_AFTER"
echo ""

# 6. Prueba de operaciones con Redis
echo "🧪 6. Probando operaciones con Redis..."

# Crear configuración de prueba
echo "   • Creando configuración de prueba..."
CREATE_RESULT=$(curl -s -X POST "$BASE_URL/config/custom/configurations/test_redis_migration" \
  -H "Content-Type: application/json" \
  -d '{
    "batteryCapacity": 99.0,
    "isLithium": true,
    "thresholdPercentage": 1.5,
    "maxAllowedCurrent": 9999.0,
    "bulkVoltage": 14.3,
    "absorptionVoltage": 14.3,
    "floatVoltage": 13.5,
    "useFuenteDC": false,
    "fuenteDC_Amps": 0.0,
    "factorDivider": 1
  }')

if echo "$CREATE_RESULT" | grep -q "success"; then
    echo "   ✅ Configuración creada exitosamente"
else
    echo "   ❌ Error creando configuración: $CREATE_RESULT"
fi

# Verificar que se puede leer
echo "   • Verificando lectura..."
READ_RESULT=$(curl -s "$BASE_URL/config/custom/configurations/test_redis_migration")
if echo "$READ_RESULT" | grep -q "test_redis_migration"; then
    echo "   ✅ Configuración leída exitosamente"
else
    echo "   ❌ Error leyendo configuración"
fi

# Eliminar configuración de prueba
echo "   • Eliminando configuración de prueba..."
DELETE_RESULT=$(curl -s -X DELETE "$BASE_URL/config/custom/configurations/test_redis_migration")
if echo "$DELETE_RESULT" | grep -q "success"; then
    echo "   ✅ Configuración eliminada exitosamente"
else
    echo "   ❌ Error eliminando configuración: $DELETE_RESULT"
fi

echo ""
echo "🏆 MIGRACIÓN COMPLETADA"
echo "======================"

# Resumen final
if [ "$COUNT_BEFORE" = "$COUNT_AFTER" ] && [ "$COUNT_AFTER" -gt 0 ]; then
    echo "✅ ÉXITO: Todas las configuraciones migradas correctamente"
    echo "   Configuraciones: $COUNT_AFTER"
    echo "   Storage: Redis (activo)"
else
    echo "⚠️  VERIFICAR: Revisar resultados de migración"
    echo "   Antes: $COUNT_BEFORE | Después: $COUNT_AFTER"
fi

echo ""
echo "💡 Próximos pasos:"
echo "   1. Verificar que no hay errores en logs de la API"
echo "   2. Probar operaciones CRUD desde frontend"
echo "   3. Confirmar que no hay más problemas de concurrencia"
