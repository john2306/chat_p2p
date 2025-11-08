class P2PChatClient {
    constructor() {
        this.apiUrl = '';
        this.ws = null;
        this.username = '';
        this.connectedPeers = new Set();
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Login
        document.getElementById('startBtn').addEventListener('click', () => this.startNode());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopNode());
        
        // Peers
        document.getElementById('refreshPeersBtn').addEventListener('click', () => this.loadAvailablePeers());
        
        // Mensajes
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('broadcastBtn').addEventListener('click', () => this.broadcastMessage());
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Recipient select
        document.getElementById('recipientSelect').addEventListener('change', (e) => {
            const hasRecipient = e.target.value !== '';
            document.getElementById('messageInput').disabled = !hasRecipient;
            document.getElementById('sendBtn').disabled = !hasRecipient;
        });
    }
    
    async startNode() {
        const username = document.getElementById('username').value.trim();
        const peerPort = parseInt(document.getElementById('peerPort').value);
        const apiPort = parseInt(document.getElementById('apiPort').value);
        
        if (!username) {
            this.showStatus('Por favor ingresa un username', 'error', 'loginStatus');
            return;
        }
        
        this.apiUrl = `http://localhost:${apiPort}`;
        this.username = username;
        
        try {
            this.showStatus('Iniciando nodo...', 'success', 'loginStatus');
            
            const response = await fetch(`${this.apiUrl}/start`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: username,
                    port: peerPort,
                    tracker_url: 'http://localhost:8000'
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail);
            }
            
            const data = await response.json();
            console.log('Nodo iniciado:', data);
            
            // Conectar WebSocket
            this.connectWebSocket(apiPort);
            
            // Cambiar a vista de chat
            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('chatSection').classList.remove('hidden');
            document.getElementById('statusBar').classList.remove('hidden');
            document.getElementById('currentUsername').textContent = username;
            
            // Cargar peers disponibles
            await this.loadAvailablePeers();
            await this.loadConnectedPeers();
            
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, 'error', 'loginStatus');
            console.error(error);
        }
    }
    
    connectWebSocket(apiPort) {
        this.ws = new WebSocket(`ws://localhost:${apiPort}/ws`);
        
        this.ws.onopen = () => {
            console.log('WebSocket conectado');
            document.getElementById('connectionStatus').textContent = '🟢 Conectado';
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket mensaje:', data);
            
            if (data.type === 'message') {
                this.displayMessage(data.data, false);
            } else if (data.type === 'peer_connected') {
                this.onPeerConnected(data.peer);
            } else if (data.type === 'peer_disconnected') {
                this.onPeerDisconnected(data.peer);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket desconectado');
            document.getElementById('connectionStatus').textContent = '🔴 Desconectado';
        };
    }
    
    async loadAvailablePeers() {
        try {
            const response = await fetch(`${this.apiUrl}/peers`);
            const data = await response.json();
            
            const container = document.getElementById('availablePeersList');
            container.innerHTML = '';
            
            if (data.peers.length === 0) {
                container.innerHTML = '<p style="color: #999; padding: 10px;">No hay peers disponibles</p>';
                return;
            }
            
            data.peers.forEach(peer => {
                const peerDiv = document.createElement('div');
                peerDiv.className = 'peer-item';
                peerDiv.innerHTML = `
                    <div>
                        <div class="peer-name">${peer.username}</div>
                        <div class="peer-status">${peer.host}:${peer.port}</div>
                    </div>
                    <div class="peer-actions">
                        <button class="btn btn-primary btn-small" onclick="chatClient.connectToPeer('${peer.username}')">
                            Conectar
                        </button>
                    </div>
                `;
                container.appendChild(peerDiv);
            });
            
        } catch (error) {
            console.error('Error cargando peers:', error);
        }
    }
    
    async loadConnectedPeers() {
        try {
            const response = await fetch(`${this.apiUrl}/connected-peers`);
            const data = await response.json();
            
            this.connectedPeers = new Set(data.connected_peers);
            
            const container = document.getElementById('connectedPeersList');
            const select = document.getElementById('recipientSelect');
            
            container.innerHTML = '';
            select.innerHTML = '<option value="">Selecciona destinatario</option>';
            
            if (data.connected_peers.length === 0) {
                container.innerHTML = '<p style="color: #999; padding: 10px;">Sin conexiones</p>';
                document.getElementById('broadcastBtn').disabled = true;
                return;
            }
            
            document.getElementById('broadcastBtn').disabled = false;
            
            data.connected_peers.forEach(peerUsername => {
                // Lista visual
                const peerDiv = document.createElement('div');
                peerDiv.className = 'peer-item';
                peerDiv.innerHTML = `
                    <div>
                        <div class="peer-name">🟢 ${peerUsername}</div>
                    </div>
                    <div class="peer-actions">
                        <button class="btn btn-danger btn-small" onclick="chatClient.disconnectFromPeer('${peerUsername}')">
                            Desconectar
                        </button>
                    </div>
                `;
                container.appendChild(peerDiv);
                
                // Select option
                const option = document.createElement('option');
                option.value = peerUsername;
                option.textContent = peerUsername;
                select.appendChild(option);
            });
            
            document.getElementById('peersCount').textContent = `Peers: ${data.connected_peers.length}`;
            
        } catch (error) {
            console.error('Error cargando peers conectados:', error);
        }
    }
    
    async connectToPeer(peerUsername) {
        try {
            const response = await fetch(`${this.apiUrl}/connect`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({peer_username: peerUsername})
            });
            
            if (!response.ok) {
                throw new Error('Error conectando al peer');
            }
            
            console.log(`Conectado a ${peerUsername}`);
            await this.loadConnectedPeers();
            await this.loadAvailablePeers();
            
        } catch (error) {
            alert(`Error: ${error.message}`);
            console.error(error);
        }
    }
    
    async disconnectFromPeer(peerUsername) {
        try {
            const response = await fetch(`${this.apiUrl}/disconnect/${peerUsername}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Error desconectando');
            }
            
            console.log(`Desconectado de ${peerUsername}`);
            await this.loadConnectedPeers();
            
        } catch (error) {
            alert(`Error: ${error.message}`);
            console.error(error);
        }
    }
    
    async sendMessage() {
        const recipient = document.getElementById('recipientSelect').value;
        const content = document.getElementById('messageInput').value.trim();
        
        if (!recipient || !content) return;
        
        try {
            const response = await fetch(`${this.apiUrl}/send`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    peer_username: recipient,
                    content: content
                })
            });
            
            if (!response.ok) {
                throw new Error('Error enviando mensaje');
            }
            
            // Mostrar mensaje enviado
            this.displayMessage({
                from: this.username,
                content: content,
                timestamp: new Date().toISOString()
            }, true);
            
            document.getElementById('messageInput').value = '';
            
        } catch (error) {
            alert(`Error: ${error.message}`);
            console.error(error);
        }
    }
    
    async broadcastMessage() {
        const content = document.getElementById('messageInput').value.trim();
        
        if (!content) return;
        
        try {
            const response = await fetch(`${this.apiUrl}/broadcast?content=${encodeURIComponent(content)}`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Error enviando broadcast');
            }
            
            // Mostrar mensaje broadcast
            this.displayMessage({
                from: `${this.username} (broadcast)`,
                content: content,
                timestamp: new Date().toISOString()
            }, true);
            
            document.getElementById('messageInput').value = '';
            document.getElementById('recipientSelect').value = '';
            
        } catch (error) {
            alert(`Error: ${error.message}`);
            console.error(error);
        }
    }
    
    displayMessage(message, isSent) {
        const container = document.getElementById('messagesContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isSent ? 'message-sent' : 'message-received'}`;
        
        const time = new Date(message.timestamp).toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-sender">${message.from}</div>
            <div class="message-content">${this.escapeHtml(message.content)}</div>
            <div class="message-time">${time}</div>
        `;
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }
    
    onPeerConnected(peerUsername) {
        console.log(`Peer conectado: ${peerUsername}`);
        this.loadConnectedPeers();
    }
    
    onPeerDisconnected(peerUsername) {
        console.log(`Peer desconectado: ${peerUsername}`);
        this.loadConnectedPeers();
    }
    
    async stopNode() {
        try {
            await fetch(`${this.apiUrl}/stop`, {method: 'POST'});
            
            if (this.ws) {
                this.ws.close();
            }
            
            // Volver a vista de login
            document.getElementById('chatSection').classList.add('hidden');
            document.getElementById('statusBar').classList.add('hidden');
            document.getElementById('loginSection').classList.remove('hidden');
            
            // Limpiar
            document.getElementById('messagesContainer').innerHTML = '';
            
        } catch (error) {
            console.error('Error deteniendo nodo:', error);
        }
    }
    
    showStatus(message, type, elementId) {
        const statusEl = document.getElementById(elementId);
        statusEl.textContent = message;
        statusEl.className = `status ${type}`;
        statusEl.style.display = 'block';
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Instancia global
const chatClient = new P2PChatClient();