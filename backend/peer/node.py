import socket
import asyncio
import json
import httpx
from typing import Dict, Optional, Callable
from datetime import datetime

class P2PNode:
    """
    Nodo P2P asíncrono que maneja conexiones directas con otros peers.
    """
    
    def __init__(
        self,
        username: str,
        peer_port: int,
        tracker_url: str = "http://localhost:8000"
    ):
        self.username = username
        self.peer_port = peer_port
        self.tracker_url = tracker_url
        
        # Estado del nodo
        self.is_running = False
        
        # Peers conectados: {username: (reader, writer)}
        self.connected_peers: Dict[str, tuple] = {}
        
        # Cliente HTTP async
        self.http_client: Optional[httpx.AsyncClient] = None
        
        # Callbacks para el frontend
        self.on_message_callback: Optional[Callable] = None
        self.on_peer_connected_callback: Optional[Callable] = None
        self.on_peer_disconnected_callback: Optional[Callable] = None
        
        # Tasks
        self.server_task = None
        self.heartbeat_task = None
    
    async def start(self):
        """Inicia el nodo P2P"""
        try:
            # Crear cliente HTTP
            self.http_client = httpx.AsyncClient(timeout=10.0)
            self.is_running = True
            
            # Iniciar servidor TCP
            self.server_task = asyncio.create_task(self._start_server())
            
            # Registrarse en el tracker
            registered = await self.register_to_tracker()
            if not registered:
                print("⚠️ No se pudo registrar en el tracker")
                return False
            
            # Iniciar heartbeat
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            
            print(f"✅ Nodo '{self.username}' iniciado en puerto {self.peer_port}")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando nodo: {e}")
            await self.stop()
            return False
    
    async def _start_server(self):
        """Inicia el servidor TCP para aceptar conexiones P2P"""
        try:
            server = await asyncio.start_server(
                self._handle_peer_connection,
                '0.0.0.0',
                self.peer_port
            )
            
            addr = server.sockets[0].getsockname()
            print(f"🔊 Servidor P2P escuchando en {addr}")
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            print(f"❌ Error en servidor P2P: {e}")
    
    async def _handle_peer_connection(self, reader, writer):
        """Maneja una conexión entrante de otro peer"""
        peer_addr = writer.get_extra_info('peername')
        print(f"📥 Conexión entrante desde {peer_addr}")
        
        try:
            # Primer mensaje debe ser el handshake con el username
            data = await reader.read(1024)
            handshake = json.loads(data.decode())
            
            if handshake.get('type') == 'handshake':
                peer_username = handshake.get('username')
                
                # Guardar conexión
                self.connected_peers[peer_username] = (reader, writer)
                print(f"✅ Peer '{peer_username}' conectado")
                
                # Notificar al frontend
                if self.on_peer_connected_callback:
                    await self.on_peer_connected_callback(peer_username)
                
                # Enviar confirmación
                response = json.dumps({
                    'type': 'handshake_ack',
                    'username': self.username
                })
                writer.write(response.encode())
                await writer.drain()
                
                # Escuchar mensajes de este peer
                await self._listen_peer_messages(peer_username, reader, writer)
            
        except Exception as e:
            print(f"❌ Error manejando peer: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _listen_peer_messages(self, peer_username, reader, writer):
        """Escucha mensajes de un peer específico"""
        try:
            while self.is_running:
                data = await reader.read(4096)
                if not data:
                    break
                
                message = json.loads(data.decode())
                print(f"💬 Mensaje de {peer_username}: {message.get('content')}")
                
                # Notificar al frontend
                if self.on_message_callback:
                    await self.on_message_callback({
                        'from': peer_username,
                        'content': message.get('content'),
                        'timestamp': message.get('timestamp')
                    })
        
        except Exception as e:
            print(f"⚠️ Error leyendo mensajes de {peer_username}: {e}")
        finally:
            # Remover peer desconectado
            if peer_username in self.connected_peers:
                del self.connected_peers[peer_username]
                print(f"❌ Peer '{peer_username}' desconectado")
                
                if self.on_peer_disconnected_callback:
                    await self.on_peer_disconnected_callback(peer_username)
    
    async def register_to_tracker(self):
        """Registra el peer en el tracker"""
        try:
            # Obtener IP local
            local_ip = socket.gethostbyname(socket.gethostname())
            
            response = await self.http_client.post(
                f"{self.tracker_url}/register",
                json={
                    "username": self.username,
                    "host": local_ip,
                    "port": self.peer_port
                }
            )
            
            if response.status_code == 200:
                print(f"✅ Registrado en tracker: {local_ip}:{self.peer_port}")
                return True
            else:
                print(f"❌ Error registrando: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando al tracker: {e}")
            return False
    
    async def heartbeat_loop(self):
        """Envía heartbeat periódico al tracker"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Cada 30 segundos
                
                response = await self.http_client.post(
                    f"{self.tracker_url}/heartbeat",
                    json={"username": self.username}
                )
                
                if response.status_code == 200:
                    print("💓 Heartbeat enviado")
                else:
                    print(f"⚠️ Heartbeat fallido: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Error en heartbeat: {e}")
                await asyncio.sleep(30)
    
    async def get_peers_from_tracker(self):
        """Obtiene lista de peers activos del tracker"""
        try:
            response = await self.http_client.get(f"{self.tracker_url}/peers")
            
            if response.status_code == 200:
                peers = response.json()
                # Filtrar para no incluirse a sí mismo
                return [p for p in peers if p['username'] != self.username]
            else:
                print(f"❌ Error obteniendo peers: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error obteniendo peers: {e}")
            return []
    
    async def connect_to_peer(self, peer_username: str):
        """Conecta a otro peer por username"""
        try:
            # Obtener info del peer del tracker
            peers = await self.get_peers_from_tracker()
            peer_info = next((p for p in peers if p['username'] == peer_username), None)
            
            if not peer_info:
                print(f"❌ Peer '{peer_username}' no encontrado")
                return False
            
            # Conectar via TCP
            reader, writer = await asyncio.open_connection(
                peer_info['host'],
                peer_info['port']
            )
            
            # Enviar handshake
            handshake = json.dumps({
                'type': 'handshake',
                'username': self.username
            })
            writer.write(handshake.encode())
            await writer.drain()
            
            # Esperar confirmación
            data = await reader.read(1024)
            response = json.loads(data.decode())
            
            if response.get('type') == 'handshake_ack':
                # Guardar conexión
                self.connected_peers[peer_username] = (reader, writer)
                print(f"✅ Conectado a peer '{peer_username}'")
                
                # Notificar al frontend
                if self.on_peer_connected_callback:
                    await self.on_peer_connected_callback(peer_username)
                
                # Escuchar mensajes de este peer
                asyncio.create_task(self._listen_peer_messages(peer_username, reader, writer))
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error conectando a {peer_username}: {e}")
            return False
    
    async def send_message(self, peer_username: str, content: str):
        """Envía un mensaje a un peer específico"""
        if peer_username not in self.connected_peers:
            print(f"❌ No estás conectado a '{peer_username}'")
            return False
        
        try:
            reader, writer = self.connected_peers[peer_username]
            
            message = json.dumps({
                'type': 'message',
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            writer.write(message.encode())
            await writer.drain()
            
            print(f"📤 Mensaje enviado a {peer_username}")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return False
    
    async def broadcast_message(self, content: str):
        """Envía un mensaje a todos los peers conectados"""
        if not self.connected_peers:
            print("❌ No hay peers conectados")
            return False
        
        results = []
        for peer_username in list(self.connected_peers.keys()):
            result = await self.send_message(peer_username, content)
            results.append(result)
        
        return all(results)
    
    async def disconnect_from_peer(self, peer_username: str):
        """Desconecta de un peer específico"""
        if peer_username not in self.connected_peers:
            return False
        
        try:
            reader, writer = self.connected_peers[peer_username]
            writer.close()
            await writer.wait_closed()
            del self.connected_peers[peer_username]
            
            print(f"🔌 Desconectado de '{peer_username}'")
            
            if self.on_peer_disconnected_callback:
                await self.on_peer_disconnected_callback(peer_username)
            
            return True
            
        except Exception as e:
            print(f"❌ Error desconectando: {e}")
            return False
    
    async def stop(self):
        """Detiene el nodo limpiamente"""
        print("🛑 Deteniendo nodo...")
        self.is_running = False
        
        # Desregistrar del tracker
        try:
            if self.http_client:
                await self.http_client.delete(
                    f"{self.tracker_url}/unregister/{self.username}"
                )
        except:
            pass
        
        # Cerrar todas las conexiones de peers
        for peer_username, (reader, writer) in list(self.connected_peers.items()):
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
        
        self.connected_peers.clear()
        
        # Cerrar cliente HTTP
        if self.http_client:
            await self.http_client.aclose()
        
        # Cancelar tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        print("✅ Nodo detenido")