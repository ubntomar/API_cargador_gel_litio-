# 🚀 Ejemplos Prácticos para Frontend - ESP32 Solar Charger API

## 📱 Componentes Frontend Recomendados

### 1. 📊 Dashboard de Monitoreo en Tiempo Real

```javascript
// React Component Example
import React, { useState, useEffect } from 'react';

const ESP32Dashboard = () => {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // IMPORTANTE: usar /data/ con barra final
        const response = await fetch('http://localhost:8000/data/');
        if (response.ok) {
          const esp32Data = await response.json();
          setData(esp32Data);
          setConnected(true);
        } else {
          setConnected(false);
        }
      } catch (error) {
        console.error('Error fetching ESP32 data:', error);
        setConnected(false);
      } finally {
        setLoading(false);
      }
    };

    // Polling cada 3 segundos
    fetchData();
    const interval = setInterval(fetchData, 3000);

    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Cargando datos del ESP32...</div>;
  if (!connected) return <div>❌ ESP32 no conectado</div>;

  return (
    <div className="esp32-dashboard">
      <h2>🔋 Monitor del Cargador Solar</h2>
      
      <div className="data-grid">
        <div className="data-card">
          <h3>🔋 Batería</h3>
          <p>{data.voltageBatterySensor2}V ({data.estimatedSOC}%)</p>
          <p>Capacidad: {data.batteryCapacity}Ah</p>
        </div>
        
        <div className="data-card">
          <h3>⚡ Carga</h3>
          <p>Estado: {data.chargeState}</p>
          <p>Panel→Batería: {data.panelToBatteryCurrent}mA</p>
          <p>Batería→Carga: {data.batteryToLoadCurrent}mA</p>
        </div>
        
        <div className="data-card">
          <h3>🌡️ Temperatura</h3>
          <p>{data.temperature}°C</p>
          <p>PWM: {data.currentPWM}/255</p>
        </div>
        
        <div className="data-card">
          <h3>🔧 Configuración</h3>
          <p>Tipo: {data.isLithium ? 'Litio' : 'GEL'}</p>
          <p>Fuente DC: {data.useFuenteDC ? 'Activa' : 'Inactiva'}</p>
        </div>
      </div>
    </div>
  );
};
```

### 2. ⚙️ Panel de Configuración de Parámetros

```javascript
// React Component para configurar parámetros individuales
const ParameterConfig = () => {
  const [parameters, setParameters] = useState({
    batteryCapacity: 100,
    isLithium: false,
    thresholdPercentage: 2.5,
    maxAllowedCurrent: 10000,
    useFuenteDC: true,
    fuenteDC_Amps: 10
  });
  
  const [saving, setSaving] = useState(false);
  
  const updateParameter = async (parameter, value) => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/config/parameter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          parameter: parameter,
          value: value
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert(`✅ ${parameter} configurado exitosamente`);
        setParameters(prev => ({...prev, [parameter]: value}));
      } else {
        alert(`❌ Error: ${result.error}`);
      }
    } catch (error) {
      alert(`❌ Error de comunicación: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="parameter-config">
      <h3>⚙️ Configuración de Parámetros</h3>
      
      <div className="parameter-item">
        <label>🔋 Capacidad de Batería (Ah):</label>
        <input
          type="number"
          value={parameters.batteryCapacity}
          onChange={(e) => setParameters(prev => ({...prev, batteryCapacity: parseFloat(e.target.value)}))}
          disabled={saving}
        />
        <button onClick={() => updateParameter('batteryCapacity', parameters.batteryCapacity)}>
          Actualizar
        </button>
      </div>
      
      <div className="parameter-item">
        <label>🔋 Tipo de Batería:</label>
        <select
          value={parameters.isLithium}
          onChange={(e) => setParameters(prev => ({...prev, isLithium: e.target.value === 'true'}))}
          disabled={saving}
        >
          <option value={false}>GEL/AGM</option>
          <option value={true}>Litio (LiFePO4)</option>
        </select>
        <button onClick={() => updateParameter('isLithium', parameters.isLithium)}>
          Actualizar
        </button>
      </div>
      
      <div className="parameter-item">
        <label>⚡ Usar Fuente DC:</label>
        <input
          type="checkbox"
          checked={parameters.useFuenteDC}
          onChange={(e) => setParameters(prev => ({...prev, useFuenteDC: e.target.checked}))}
          disabled={saving}
        />
        <button onClick={() => updateParameter('useFuenteDC', parameters.useFuenteDC)}>
          Actualizar
        </button>
      </div>
    </div>
  );
};
```

### 3. 📋 Gestor de Configuraciones Personalizadas

```javascript
// React Component para gestionar configuraciones guardadas
const ConfigurationManager = () => {
  const [configurations, setConfigurations] = useState({});
  const [selectedConfig, setSelectedConfig] = useState('');
  const [newConfigName, setNewConfigName] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  // Cargar configuraciones
  const loadConfigurations = async () => {
    try {
      const url = searchTerm 
        ? `http://localhost:8000/config/custom/configurations?search=${encodeURIComponent(searchTerm)}`
        : 'http://localhost:8000/config/custom/configurations';
        
      const response = await fetch(url);
      const data = await response.json();
      setConfigurations(data.configurations || {});
    } catch (error) {
      console.error('Error loading configurations:', error);
    }
  };

  // Aplicar configuración
  const applyConfiguration = async (configName) => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/config/custom/configurations/${configName}/apply`,
        { method: 'POST' }
      );
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert(`✅ Configuración "${configName}" aplicada exitosamente`);
      } else {
        alert(`❌ Error aplicando configuración: ${result.error}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Crear nueva configuración
  const createConfiguration = async (configData) => {
    if (!newConfigName.trim()) {
      alert('Ingresa un nombre para la configuración');
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/config/custom/configurations/${newConfigName}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(configData)
        }
      );
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert(`✅ Configuración "${newConfigName}" creada exitosamente`);
        setNewConfigName('');
        loadConfigurations();
      } else {
        alert(`❌ Error: ${result.error}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  // Eliminar configuración
  const deleteConfiguration = async (configName) => {
    if (!confirm(`¿Eliminar la configuración "${configName}"?`)) return;

    try {
      const response = await fetch(
        `http://localhost:8000/config/custom/configurations/${configName}`,
        { method: 'DELETE' }
      );
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert(`✅ Configuración "${configName}" eliminada`);
        loadConfigurations();
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    }
  };

  useEffect(() => {
    loadConfigurations();
  }, [searchTerm]);

  return (
    <div className="configuration-manager">
      <h3>📋 Configuraciones Personalizadas</h3>
      
      {/* Búsqueda */}
      <div className="search-section">
        <input
          type="text"
          placeholder="🔍 Buscar configuraciones..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Lista de configuraciones */}
      <div className="configurations-list">
        {Object.entries(configurations).map(([name, config]) => (
          <div key={name} className="config-item">
            <div className="config-info">
              <h4>{name}</h4>
              <p>
                🔋 {config.batteryCapacity}Ah | 
                {config.isLithium ? ' ⚡ Litio' : ' 🔋 GEL'} | 
                {config.useFuenteDC ? ' 🔌 DC' : ' ❌ Sin DC'}
              </p>
              <small>Actualizado: {new Date(config.updatedAt).toLocaleString()}</small>
            </div>
            
            <div className="config-actions">
              <button 
                onClick={() => applyConfiguration(name)}
                disabled={loading}
                className="apply-btn"
              >
                🚀 Aplicar
              </button>
              <button 
                onClick={() => deleteConfiguration(name)}
                className="delete-btn"
              >
                🗑️ Eliminar
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Crear nueva configuración */}
      <div className="new-config-section">
        <h4>➕ Nueva Configuración</h4>
        <input
          type="text"
          placeholder="Nombre de la configuración"
          value={newConfigName}
          onChange={(e) => setNewConfigName(e.target.value)}
        />
        <button onClick={() => {
          // Aquí deberías obtener los datos actuales del ESP32 o usar un formulario
          const configData = {
            batteryCapacity: 100,
            isLithium: false,
            thresholdPercentage: 2.5,
            maxAllowedCurrent: 10000,
            bulkVoltage: 14.4,
            absorptionVoltage: 14.4,
            floatVoltage: 13.6,
            useFuenteDC: true,
            fuenteDC_Amps: 10,
            factorDivider: 1
          };
          createConfiguration(configData);
        }}>
          💾 Guardar Configuración Actual
        </button>
      </div>
    </div>
  );
};
```

### 4. 📊 Hook Personalizado para Datos ESP32

```javascript
// Custom Hook para gestionar datos ESP32
import { useState, useEffect, useCallback } from 'react';

const useESP32Data = (pollingInterval = 3000) => {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      // IMPORTANTE: usar /data/ con barra final
      const response = await fetch('http://localhost:8000/data/');
      
      if (response.ok) {
        const esp32Data = await response.json();
        setData(esp32Data);
        setConnected(true);
        setError(null);
      } else {
        setConnected(false);
        setError(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Error fetching ESP32 data:', err);
      setConnected(false);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateParameter = useCallback(async (parameter, value) => {
    try {
      const response = await fetch('http://localhost:8000/config/parameter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parameter, value })
      });

      const result = await response.json();
      
      if (result.success) {
        // Actualizar datos locales inmediatamente
        setData(prev => ({ ...prev, [parameter]: value }));
        return { success: true, message: result.esp32_response };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, pollingInterval);
    return () => clearInterval(interval);
  }, [fetchData, pollingInterval]);

  return {
    data,
    connected,
    loading,
    error,
    refetch: fetchData,
    updateParameter
  };
};

// Uso del hook
const MyComponent = () => {
  const { data, connected, loading, error, updateParameter } = useESP32Data();

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!connected) return <div>ESP32 desconectado</div>;

  return (
    <div>
      <h3>Voltaje: {data.voltageBatterySensor2}V</h3>
      <button onClick={() => updateParameter('useFuenteDC', !data.useFuenteDC)}>
        {data.useFuenteDC ? 'Desactivar' : 'Activar'} Fuente DC
      </button>
    </div>
  );
};
```

### 5. 📱 Notificaciones y Alertas

```javascript
// Sistema de notificaciones para eventos importantes
const NotificationSystem = () => {
  const [notifications, setNotifications] = useState([]);

  const addNotification = (type, message) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, type, message, timestamp: new Date() }]);
    
    // Auto-remove después de 5 segundos
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  // Monitorear cambios críticos
  const { data, connected } = useESP32Data();
  
  useEffect(() => {
    if (data) {
      // Alertas por voltaje bajo
      if (data.voltageBatterySensor2 < 11.5) {
        addNotification('warning', `⚠️ Voltaje bajo: ${data.voltageBatterySensor2}V`);
      }
      
      // Alertas por temperatura alta
      if (data.temperature > 40) {
        addNotification('error', `🌡️ Temperatura alta: ${data.temperature}°C`);
      }
      
      // Notificar cambios en el estado de carga
      const isCharging = data.chargeState !== 'ERROR' && data.chargeState !== 'FLOAT_CHARGE';
      if (isCharging && !window.lastChargingState) {
        addNotification('success', `🔋 Estado de carga: ${data.chargeState}`);
      }
      window.lastChargingState = isCharging;
    }

    // Alerta de desconexión
    if (!connected) {
      addNotification('error', '❌ ESP32 desconectado');
    }
  }, [data, connected]);

  return (
    <div className="notification-container">
      {notifications.map(notification => (
        <div key={notification.id} className={`notification ${notification.type}`}>
          <span>{notification.message}</span>
          <small>{notification.timestamp.toLocaleTimeString()}</small>
        </div>
      ))}
    </div>
  );
};
```

### 6. 🎨 Estilos CSS Recomendados

```css
/* Estilos para componentes ESP32 */
.esp32-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.data-card {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.data-card h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.parameter-config {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.parameter-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 15px 0;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.parameter-item label {
  flex: 1;
  font-weight: bold;
}

.parameter-item input,
.parameter-item select {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.parameter-item button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.parameter-item button:hover {
  background: #0056b3;
}

.configurations-list {
  max-height: 400px;
  overflow-y: auto;
  margin: 20px 0;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin: 10px 0;
  background: white;
}

.config-info h4 {
  margin: 0 0 5px 0;
  color: #333;
}

.config-info p {
  margin: 5px 0;
  color: #666;
}

.config-actions {
  display: flex;
  gap: 10px;
}

.apply-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.delete-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  max-width: 300px;
}

.notification {
  padding: 15px;
  border-radius: 4px;
  margin: 10px 0;
  color: white;
  animation: slideIn 0.3s ease-out;
}

.notification.success { background: #28a745; }
.notification.warning { background: #ffc107; color: #333; }
.notification.error { background: #dc3545; }

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* Responsive design */
@media (max-width: 768px) {
  .data-grid {
    grid-template-columns: 1fr;
  }
  
  .config-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .config-actions {
    margin-top: 10px;
    justify-content: center;
  }
  
  .parameter-item {
    flex-direction: column;
    align-items: stretch;
  }
}
```

## 🔧 Configuraciones Predefinidas

### Configuraciones de Batería Comunes

```javascript
const BATTERY_PRESETS = {
  'LiFePO4_100Ah': {
    batteryCapacity: 100,
    isLithium: true,
    thresholdPercentage: 3.0,
    maxAllowedCurrent: 10000,
    bulkVoltage: 14.6,
    absorptionVoltage: 14.6,
    floatVoltage: 13.8,
    useFuenteDC: false,
    fuenteDC_Amps: 0,
    factorDivider: 1
  },
  'GEL_100Ah': {
    batteryCapacity: 100,
    isLithium: false,
    thresholdPercentage: 2.5,
    maxAllowedCurrent: 5000,
    bulkVoltage: 14.4,
    absorptionVoltage: 14.4,
    floatVoltage: 13.6,
    useFuenteDC: true,
    fuenteDC_Amps: 10,
    factorDivider: 2
  },
  'AGM_200Ah': {
    batteryCapacity: 200,
    isLithium: false,
    thresholdPercentage: 2.0,
    maxAllowedCurrent: 10000,
    bulkVoltage: 14.7,
    absorptionVoltage: 14.7,
    floatVoltage: 13.7,
    useFuenteDC: true,
    fuenteDC_Amps: 15,
    factorDivider: 1
  }
};
```

## 📱 Integración con Frameworks

### Next.js API Routes

```javascript
// pages/api/esp32/[...params].js
export default async function handler(req, res) {
  const { params } = req.query;
  const endpoint = params.join('/');
  
  try {
    const response = await fetch(`http://localhost:8000/${endpoint}`, {
      method: req.method,
      headers: req.headers,
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined
    });
    
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
```

### Vue.js Composable

```javascript
// composables/useESP32.js
import { ref, onMounted, onUnmounted } from 'vue'

export function useESP32() {
  const data = ref(null)
  const connected = ref(false)
  const loading = ref(true)

  let interval = null

  const fetchData = async () => {
    try {
      // IMPORTANTE: usar /data/ con barra final
      const response = await fetch('http://localhost:8000/data/')
      if (response.ok) {
        data.value = await response.json()
        connected.value = true
      }
    } catch (error) {
      connected.value = false
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchData()
    interval = setInterval(fetchData, 3000)
  })

  onUnmounted(() => {
    if (interval) clearInterval(interval)
  })

  return { data, connected, loading }
}
```

---

**🎯 Estos ejemplos proporcionan una base sólida para implementar una interfaz frontend completa y funcional con el ESP32 Solar Charger API.**
