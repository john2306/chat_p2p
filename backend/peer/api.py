from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from .node import P2PNode

# Modelos
class StartNodeRequest(BaseModel):
    username: str
    port: int
    tracker_url: Optional[str] = "http://localhost:8000"

class ConnectPeerRequest(BaseModel):
    peer_username: str

class SendMessageRequest(BaseModel):
    peer_username: str
    content: str

# FastAPI app
app = FastAPI(title="P2P Chat Peer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global del nodo (se inicializa al hacer start)
peer_node: Optional[P2PNode] = None
websocket_connections = []

# Endpoints HTTP
@app.post("/start")
async def start_node(request: StartNodeRequest):
    """Inicia el nodo P2P"""
    global peer_node
    
    if peer_node and peer_node.is_running:
        raise HTTPException(status_code=400, detail="Nodo ya está corriendo")
    
    peer_node = P2PNode(
        username=request.username,
        peer_port=request.port,
        tracker_url=request.tracker_url
    )
    
    # Configurar callbacks para notificar al frontend
    peer_node.on_message_callback = notify_message
    peer_node.on_peer_connected_callback = notify_peer_connected
    peer_node.on_peer_disconnected_callback = notify_peer_disconnected
    
    success = await peer_node.start()
    
    if success:
        return {"status": "started", "username": request.username}
    else:
        raise HTTPException(status_code=500, detail="Error iniciando nodo")

@app.post("/stop")
async def stop_node():
    """Detiene el nodo P2P"""
    global peer_node
    
    if not peer_node:
        raise HTTPException(status_code=400, detail="No hay nodo corriendo")
    
    await peer_node.stop()
    peer_node = None
    
    return {"status": "stopped"}

@app.get("/peers")
async def get_peers():
    """Obtiene lista de peers disponibles del tracker"""
    if not peer_node:
        raise HTTPException(status_code=400, detail="Nodo no iniciado")
    
    peers = await peer_node.get_peers_from_tracker()
    return {"peers": peers}

@app.get("/connected-peers")
async def get_connected_peers():
    """Obtiene lista de peers conectados directamente"""
    if not peer_node:
        raise HTTPException(status_code=400, detail="Nodo no iniciado")
    
    return {
        "connected_peers": list(peer_node.connected_peers.keys())
    }

@app.post("/connect")
async def connect_to_peer(request: ConnectPeerRequest):
    """Conecta a otro peer"""
    if not peer_node:
        raise HTTPException(status_code=400, detail="Nodo no iniciado")
    
    success = await peer_node.connect_to_peer(request.peer_username)
    
    if success:
        return {"status": "connected", "peer": request.peer_username}
    else:
        raise HTTPException(status_code=400, detail="No se pudo conectar")

@app.post("/send")
async def send_message(request: SendMessageRequest):
    """Envía un mensaje a un peer"""
    if not peer_node:
        raise HTTPException(status_code=400, detail="Nodo no iniciado")
    
    success = await peer_node.send_message(request.peer_username, request.content)
    
    if success:
        return {"status": "sent"}
    else:
        raise HTTPException(status_code=400, detail="Error enviando mensaje")

@app.post("/broadcast")
async def broadcast_message(content: str):
    """Envía un mensaje a todos los peers conectados"""
    if not peer_node:
        raise HTTPException(status_code=400, detail="Nodo no iniciado")
    
    success = await peer_node.broadcast_message(content)
    
    if success:
        return {"status": "broadcasted"}
    else:
        raise HTTPException(status_code=400, detail="Error enviando broadcast")

@app.delete("/disconnect/{peer_username}")
async def disconnect_peer(peer_username: str):
    """Desconecta de un peer"""
    if not peer_node:
        raise HTTPException(status_code=400, detail="Nodo no iniciado")
    
    success = await peer_node.disconnect_from_peer(peer_username)
    
    if success:
        return {"status": "disconnected"}
    else:
        raise HTTPException(status_code=400, detail="Peer no conectado")

# WebSocket para actualizaciones en tiempo real
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para notificaciones en tiempo real al frontend"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Mantener conexión abierta
            data = await websocket.receive_text()
            # El frontend puede enviar pings si quiere
            await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

# Funciones para notificar al frontend via WebSocket
async def notify_message(message):
    """Notifica nuevo mensaje a todos los clientes conectados"""
    for ws in websocket_connections:
        try:
            await ws.send_json({
                "type": "message",
                "data": message
            })
        except:
            pass

async def notify_peer_connected(peer_username):
    """Notifica que un peer se conectó"""
    for ws in websocket_connections:
        try:
            await ws.send_json({
                "type": "peer_connected",
                "peer": peer_username
            })
        except:
            pass

async def notify_peer_disconnected(peer_username):
    """Notifica que un peer se desconectó"""
    for ws in websocket_connections:
        try:
            await ws.send_json({
                "type": "peer_disconnected",
                "peer": peer_username
            })
        except:
            pass

@app.get("/")
async def root():
    """Página de inicio"""
    return HTMLResponse("""
    <html>
        <head><title>P2P Chat</title></head>
        <body>
            <h1>P2P Chat Peer API</h1>
            <p>API corriendo. Ve a <a href="/docs">/docs</a> para ver la documentación.</p>
        </body>
    </html>
    """)