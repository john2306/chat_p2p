# 💬 Chat P2P Descentralizado

Sistema de chat peer-to-peer (P2P) descentralizado con arquitectura cliente-servidor híbrida. Los usuarios pueden comunicarse directamente entre ellos usando WebSockets, mientras que un servidor tracker central facilita el descubrimiento de peers.

## 🎯 Características

- **Arquitectura P2P real**: Comunicación directa entre peers sin pasar mensajes por servidor central
- **Servidor Tracker**: Descubrimiento de peers y gestión de conexiones
- **WebSocket**: Comunicación en tiempo real bidireccional
- **Async/Await**: Implementación completamente asíncrona con FastAPI y SQLAlchemy
- **Auto-limpieza**: Detección y eliminación automática de peers inactivos
- **API REST**: Endpoints documentados con OpenAPI/Swagger
- **Frontend web**: Interfaz de usuario simple y funcional

## 🏗️ Arquitectura

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Peer A    │◄────────┤   Tracker   ├────────►│   Peer B    │
│  (Puerto    │  Registro│  (Puerto    │ Registro│  (Puerto    │
│   3000)     │  /Descub.│   8000)     │/Descub. │   3001)     │
└──────┬──────┘         └─────────────┘         └──────┬──────┘
       │                                                │
       │          ┌──────────────────┐                 │
       └──────────┤  WebSocket P2P   ├─────────────────┘
                  │  Conexión Directa│
                  └──────────────────┘
```

### Componentes

1. **Tracker Server** (`backend/tracker/`)
   - Registro de peers activos
   - Descubrimiento de peers
   - Sistema de heartbeat
   - Auto-limpieza de peers inactivos

2. **Peer Node** (`backend/peer/`)
   - Cliente/servidor P2P
   - Gestión de conexiones WebSocket
   - Envío/recepción de mensajes
   - Comunicación con tracker

3. **Frontend** (`frontend/`)
   - Interfaz web HTML/CSS/JS
   - Interacción con API peer
   - Chat en tiempo real

## 📋 Requisitos

- Python 3.9+
- pip (gestor de paquetes de Python)

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/john2306/chat_p2p.git
cd chat_p2p
```

### 2. Crear entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 🎮 Uso

### Paso 1: Iniciar el Tracker Server

El tracker debe estar corriendo antes que los peers.

```bash
# Desde la raíz del proyecto
uvicorn backend.tracker.main:app --reload
```

El tracker estará disponible en:
- API: `http://localhost:8000`
- Documentación: `http://localhost:8000/docs`

### Paso 2: Iniciar Peers

Abre **dos o más terminales** y ejecuta un peer en cada una:

**Terminal 1 - Peer 1:**
```bash
uvicorn backend.peer.api:app --port 3000
```

**Terminal 2 - Peer 2:**
```bash
uvicorn backend.peer.api:app --port 3001
```

**Terminal 3 - Peer 3 (opcional):**
```bash
uvicorn backend.peer.api:app --port 3002
```

Cada peer estará disponible en:
- API: `http://localhost:PORT`
- Documentación: `http://localhost:PORT/docs`

### Paso 3: Iniciar Frontend

En una nueva terminal:

```bash
cd frontend
python serve.py
```

El frontend estará disponible en: `http://localhost:8080`

## 🔧 API Endpoints

### Tracker API (`http://localhost:8000`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/register` | Registrar un nuevo peer |
| POST | `/heartbeat` | Enviar latido de vida |
| GET | `/peers` | Obtener lista de peers activos |
| DELETE | `/unregister/{username}` | Desconectar peer |
| GET | `/health` | Estado del tracker |

### Peer API (`http://localhost:3000`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/start` | Iniciar nodo P2P |
| POST | `/connect` | Conectar con otro peer |
| POST | `/send` | Enviar mensaje a peer |
| GET | `/peers` | Obtener peers conectados |
| GET | `/messages` | Obtener historial de mensajes |
| WebSocket | `/ws` | Conexión WebSocket para mensajes en tiempo real |

## 📝 Ejemplos de Uso

### Registrar un Peer en el Tracker

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "host": "localhost",
    "port": 3000
  }'
```

### Iniciar Nodo P2P

```bash
curl -X POST "http://localhost:3000/start" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "port": 3000,
    "tracker_url": "http://localhost:8000"
  }'
```

### Conectar con Otro Peer

```bash
curl -X POST "http://localhost:3000/connect" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_username": "bob"
  }'
```

### Enviar Mensaje

```bash
curl -X POST "http://localhost:3000/send" \
  -H "Content-Type: application/json" \
  -d '{
    "peer_username": "bob",
    "content": "¡Hola Bob!"
  }'
```

## 🗂️ Estructura del Proyecto

```
chat_p2p/
├── backend/
│   ├── __init__.py
│   ├── peer/
│   │   ├── __init__.py
│   │   ├── api.py          # API REST del peer
│   │   ├── node.py         # Lógica del nodo P2P
│   │   └── websocket.py    # Gestión de WebSockets
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── config.py       # Configuración global
│   │   └── utils.py        # Utilidades compartidas
│   └── tracker/
│       ├── __init__.py
│       ├── main.py         # API del tracker
│       ├── models.py       # Modelos de base de datos
│       └── schemas.py      # Esquemas Pydantic
├── frontend/
│   ├── index.html          # Interfaz de usuario
│   ├── app.js              # Lógica del frontend
│   ├── style.css           # Estilos
│   └── serve.py            # Servidor HTTP simple
├── requirements.txt        # Dependencias Python
├── README.md              # Este archivo
└── LICENSE
```

## 🛠️ Tecnologías Utilizadas

- **[FastAPI](https://fastapi.tiangolo.com/)**: Framework web moderno y rápido
- **[Uvicorn](https://www.uvicorn.org/)**: Servidor ASGI de alto rendimiento
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: ORM para Python con soporte async
- **[Pydantic](https://pydantic-docs.helpmanual.io/)**: Validación de datos
- **[WebSockets](https://websockets.readthedocs.io/)**: Protocolo de comunicación en tiempo real
- **[aiosqlite](https://aiosqlite.omnilib.dev/)**: Driver async para SQLite

## 🔍 Características Técnicas

### Async/Await Completo
Todo el código backend está implementado con async/await para máximo rendimiento:
- `create_async_engine` para conexiones de BD
- `AsyncSession` para operaciones de base de datos
- Endpoints async en FastAPI
- WebSockets async para comunicación P2P

### Sistema de Heartbeat
Los peers envían señales de vida cada 30 segundos al tracker. El tracker ejecuta una tarea de limpieza automática cada 30 segundos que marca como inactivos los peers sin heartbeat reciente.

### WebSocket Bidireccional
Cada peer puede actuar como cliente y servidor WebSocket simultáneamente, permitiendo comunicación P2P verdadera.

## 🧪 Testing

Puedes probar los endpoints usando la documentación interactiva de Swagger:

- Tracker: `http://localhost:8000/docs`
- Peer 1: `http://localhost:3000/docs`
- Peer 2: `http://localhost:3001/docs`

## 🐛 Troubleshooting

### Error: "Address already in use"
Otro proceso está usando el puerto. Usa un puerto diferente:
```bash
uvicorn backend.peer.api:app --port 3005
```

### Error: "No module named 'backend'"
Asegúrate de ejecutar uvicorn desde la raíz del proyecto:
```bash
cd d:\Github\Cashea\chat_p2p
uvicorn backend.tracker.main:app
```

### Peers no se conectan
1. Verifica que el tracker esté corriendo
2. Revisa que los peers estén registrados: `http://localhost:8000/peers`
3. Asegúrate de que los puertos no estén bloqueados por firewall

## 📄 Licencia

Este proyecto está bajo la licencia especificada en el archivo [LICENSE](LICENSE).

## 👥 Autor

- GitHub: [@john2306](https://github.com/john2306)

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 🔮 Mejoras Futuras

- [ ] Cifrado end-to-end de mensajes
- [ ] Transferencia de archivos P2P
- [ ] Chat grupal
- [ ] Persistencia de mensajes
- [ ] Autenticación de usuarios
- [ ] UI mejorada con React/Vue
- [ ] Notificaciones push
- [ ] Estado "escribiendo..."
- [ ] Emojis y multimedia

---

⭐ Si te gusta este proyecto, dale una estrella en GitHub!
