from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from datetime import datetime, timedelta
from typing import List
import asyncio

from .models import Base, Peer
from .schemas import PeerRegister, PeerResponse, HeartbeatRequest
from ..shared.config import settings

# Database setup
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# FastAPI app
app = FastAPI(
    title="P2P Chat Tracker",
    description="Servidor de descubrimiento para peers P2P",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Función auxiliar
async def cleanup_inactive_peers(db: AsyncSession, threshold_minutes: int = 2):
    """Marca como inactivos los peers sin heartbeat reciente"""
    threshold = datetime.utcnow() - timedelta(minutes=threshold_minutes)
    result = await db.execute(
        select(Peer).where(
            Peer.last_heartbeat < threshold,
            Peer.is_active == True
        )
    )
    inactive_peers = result.scalars().all()
    
    for peer in inactive_peers:
        peer.is_active = False
    
    await db.commit()
    return len(inactive_peers)

# Tarea periódica
async def periodic_cleanup():
    """Ejecuta limpieza cada 30 segundos"""
    while True:
        await asyncio.sleep(30)
        async with AsyncSessionLocal() as db:
            try:
                cleaned = await cleanup_inactive_peers(db)
                if cleaned > 0:
                    print(f"🧹 Limpiados {cleaned} peers inactivos")
            except Exception as e:
                print(f"❌ Error en limpieza: {e}")

# Endpoints
@app.post("/register", response_model=PeerResponse)
async def register_peer(peer_data: PeerRegister, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo peer o actualiza uno existente"""
    result = await db.execute(select(Peer).where(Peer.username == peer_data.username))
    peer = result.scalar_one_or_none()
    
    if peer:
        peer.host = peer_data.host
        peer.port = peer_data.port
        peer.is_active = True
        peer.last_heartbeat = datetime.utcnow()
    else:
        peer = Peer(
            username=peer_data.username,
            host=peer_data.host,
            port=peer_data.port,
            is_active=True,
            last_heartbeat=datetime.utcnow()
        )
        db.add(peer)
    
    await db.commit()
    await db.refresh(peer)
    return peer

@app.post("/heartbeat")
async def heartbeat(heartbeat_data: HeartbeatRequest, db: AsyncSession = Depends(get_db)):
    """Actualiza el último latido del peer"""
    result = await db.execute(select(Peer).where(Peer.username == heartbeat_data.username))
    peer = result.scalar_one_or_none()
    
    if not peer:
        raise HTTPException(status_code=404, detail="Peer not found")
    
    peer.last_heartbeat = datetime.utcnow()
    peer.is_active = True
    await db.commit()
    return {"message": "Heartbeat actualizado", "username": peer.username}

@app.get("/peers", response_model=List[PeerResponse])
async def get_active_peers(db: AsyncSession = Depends(get_db)):
    """Obtiene lista de peers activos"""
    result = await db.execute(select(Peer).where(Peer.is_active == True))
    return result.scalars().all()

@app.delete("/unregister/{username}")
async def unregister_peer(username: str, db: AsyncSession = Depends(get_db)):
    """Marca un peer como inactivo"""
    result = await db.execute(select(Peer).where(Peer.username == username))
    peer = result.scalar_one_or_none()
    
    if not peer:
        raise HTTPException(status_code=404, detail="Peer not found")
    
    peer.is_active = False
    await db.commit()
    return {"message": f"Peer {username} desconectado"}

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check del tracker"""
    total_result = await db.execute(select(Peer))
    total_peers = len(total_result.scalars().all())
    
    active_result = await db.execute(select(Peer).where(Peer.is_active == True))
    active_peers = len(active_result.scalars().all())
    
    return {
        "status": "healthy",
        "total_peers": total_peers,
        "active_peers": active_peers,
        "timestamp": datetime.utcnow()
    }

@app.on_event("startup")
async def startup_event():
    """Inicia limpieza automática al arrancar"""
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Iniciar tarea de limpieza
    asyncio.create_task(periodic_cleanup())
    print("✅ Tracker iniciado - Limpieza automática activada")