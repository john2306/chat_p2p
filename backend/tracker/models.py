from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Peer(AsyncAttrs, Base):
    __tablename__ = 'peers'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    host = Column(String)
    port = Column(Integer)
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    

    def __repr__(self):
        return f"<Peer(username={self.username}, host={self.host}, port={self.port}, is_active={self.is_active})>"