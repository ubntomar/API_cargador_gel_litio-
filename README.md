# ESP32 Solar Charger API

API REST para control y monitoreo del cargador solar ESP32.

## 🚀 Instalación Rápida

```bash
# Clonar/crear el proyecto
git clone https://github.com/ubntomar/API_cargador_gel_litio-.git
cd API_cargador_gel_litio-

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# Ejecutar servidor
python main.py
```

## Dentro de la carpeta crontab hay un script para controlar arranque automático 
```bash
mv ./setup_api_crontab.sh ..
chmod +x setup_api_crontab.sh
./setup_api_crontab.sh

```
## 📡 Uso de la API

### Obtener todos los datos
```bash
curl http://localhost:8000/data/
```

### Configurar parámetro
```bash
curl -X PUT http://localhost:8000/config/bulkVoltage \
  -H "Content-Type: application/json" \
  -d '{"value": 14.5}'
```

### Apagar carga temporalmente
```bash
curl -X POST http://localhost:8000/actions/toggle_load \
  -H "Content-Type: application/json" \
  -d '{"hours": 0, "minutes": 5, "seconds": 0}'
```

## 📊 Documentación Interactiva

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Tests

```bash
pytest tests/
```

## 📁 Estructura del Proyecto

```
esp32_api/
├── main.py              # FastAPI app principal
├── models/              # Modelos Pydantic
├── services/            # Lógica de negocio
├── api/                 # Endpoints REST
├── core/                # Configuración
├── tests/               # Tests
└── logs/                # Archivos de log
```

## ⚙️ Configuración

Edita el archivo `.env`:

```bash
SERIAL_PORT=/dev/ttyS5
SERIAL_BAUDRATE=9600
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## 🔗 Endpoints Principales

- `GET /data/` - Todos los datos del ESP32
- `PUT /config/{parameter}` - Configurar parámetro
- `POST /actions/toggle_load` - Control de carga
- `GET /health` - Estado de la API

## 📞 Soporte

Para más información, consulta la documentación en `/docs`.
