from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Tracker
    TRACKER_HOST: str = "0.0.0.0"
    TRACKER_PORT: int = 8000

    # Peer
    PEER_HOST: str = "0.0.0.0"
    PEER_PORT: int = 5000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./chat_p2p.db"

    # Security
    SECRET_KEY: str = "your_secret_key_here"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()