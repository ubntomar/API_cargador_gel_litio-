#!/bin/bash
# =============================================================================
# 🚀 COMANDOS CURL ESENCIALES - Configuraciones Personalizadas ESP32
# =============================================================================

API="http://localhost:8000"

echo "📋 ESP32 Solar Charger API - Configuraciones Personalizadas"
echo "============================================================"

# COMANDOS BÁSICOS PARA COPIAR Y PEGAR
echo ""
echo "🔍 1. LISTAR CONFIGURACIONES:"
echo "curl -s $API/config/custom/configurations"
echo ""

echo "➕ 2. CREAR CONFIGURACIÓN RÁPIDA (Litio 100Ah):"
echo "curl -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"batteryCapacity\": 100.0, \"isLithium\": true, \"thresholdPercentage\": 2.5, \"maxAllowedCurrent\": 12000.0, \"bulkVoltage\": 14.4, \"absorptionVoltage\": 14.4, \"floatVoltage\": 13.6, \"useFuenteDC\": false, \"fuenteDC_Amps\": 0.0, \"factorDivider\": 1}' \\"
echo "  $API/config/custom/config/BateriaLitio100Ah"
echo ""

echo "➕ 3. CREAR CONFIGURACIÓN RÁPIDA (GEL 200Ah):"
echo "curl -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"batteryCapacity\": 200.0, \"isLithium\": false, \"thresholdPercentage\": 3.0, \"maxAllowedCurrent\": 15000.0, \"bulkVoltage\": 14.8, \"absorptionVoltage\": 14.8, \"floatVoltage\": 13.8, \"useFuenteDC\": false, \"fuenteDC_Amps\": 0.0, \"factorDivider\": 5}' \\"
echo "  $API/config/custom/config/BateriaGEL200Ah"
echo ""

echo "🚀 4. APLICAR CONFIGURACIÓN AL ESP32:"
echo "curl -X POST $API/config/custom/config/BateriaLitio100Ah/apply"
echo ""

echo "📖 5. VER CONFIGURACIÓN ESPECÍFICA:"
echo "curl -s $API/config/custom/config/BateriaLitio100Ah"
echo ""

echo "🗑️ 6. ELIMINAR CONFIGURACIÓN:"
echo "curl -X DELETE $API/config/custom/config/BateriaLitio100Ah"
echo ""

echo "📦 7. BACKUP/EXPORTAR TODAS:"
echo "curl -s $API/config/custom/configurations/export"
echo ""

echo "📊 8. INFO DEL SISTEMA:"
echo "curl -s $API/config/custom/configurations/info"
echo ""

echo "✅ 9. VALIDAR CONFIGURACIÓN:"
echo "curl -X POST -H 'Content-Type: application/json' \\"
echo "  -d '{\"batteryCapacity\": 150.0, \"isLithium\": true, \"thresholdPercentage\": 2.0, \"maxAllowedCurrent\": 8000.0, \"bulkVoltage\": 14.6, \"absorptionVoltage\": 14.6, \"floatVoltage\": 13.7, \"useFuenteDC\": false, \"fuenteDC_Amps\": 0.0, \"factorDivider\": 1}' \\"
echo "  $API/config/custom/configurations/validate"
echo ""

# VARIABLES PARA COPIAR Y MODIFICAR
echo "🎛️ PLANTILLAS DE CONFIGURACIÓN:"
echo "================================"
echo ""
echo "# Batería Litio pequeña (50Ah):"
echo 'LITIO_50='"'"'{"batteryCapacity": 50.0, "isLithium": true, "thresholdPercentage": 2.0, "maxAllowedCurrent": 5000.0, "bulkVoltage": 14.2, "absorptionVoltage": 14.2, "floatVoltage": 13.4, "useFuenteDC": false, "fuenteDC_Amps": 0.0, "factorDivider": 1}'"'"
echo ""
echo "# Batería GEL grande (400Ah):"
echo 'GEL_400='"'"'{"batteryCapacity": 400.0, "isLithium": false, "thresholdPercentage": 3.5, "maxAllowedCurrent": 20000.0, "bulkVoltage": 15.0, "absorptionVoltage": 15.0, "floatVoltage": 14.0, "useFuenteDC": true, "fuenteDC_Amps": 10.0, "factorDivider": 10}'"'"
echo ""
echo "# Usar plantillas:"
echo "curl -X POST -H 'Content-Type: application/json' -d \"\$LITIO_50\" $API/config/custom/config/Litio50Ah"
echo "curl -X POST -H 'Content-Type: application/json' -d \"\$GEL_400\" $API/config/custom/config/GEL400Ah"
echo ""

echo "🔄 FLUJO TÍPICO DE USO:"
echo "======================"
echo "1. curl -s $API/config/custom/configurations  # Ver qué hay"
echo "2. # Crear nueva configuración con curl -X POST..."
echo "3. curl -X POST $API/config/custom/config/MiConfig/apply  # Aplicar"
echo "4. curl -s $API/config/custom/configurations/export  # Backup"
echo ""

echo "💡 TIPS:"
echo "========="
echo "- Agrega | jq . al final para pretty-print JSON"
echo "- Nombres sin espacios ni caracteres especiales"
echo "- Content-Type: application/json es obligatorio para POST"
echo "- La API valida automáticamente antes de guardar"
echo "- factorDivider: 1=Litio, 5=GEL, 10=AGM típicos"
echo ""
