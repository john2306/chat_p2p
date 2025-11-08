from pydantic import BaseModel
from datetime import datetime

class PeerRegister(BaseModel):
    """Schema for registering a new peer."""
    username: str
    host: str
    port: int

class PeerResponse(BaseModel):
    """Schema for responding with peer information."""
    id: int
    username: str
    host: str
    port: int
    is_active: bool
    last_heartbeat: datetime

    class Config:
        from_attributes = True

class HeartbeatRequest(BaseModel):
    """Schema for heartbeat requests."""
    username: str