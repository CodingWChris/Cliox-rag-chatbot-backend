from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2:1b"  # Changed to faster 1B model
    
    # Server Configuration
    environment: str = "development"
    port: int = 8001
    # Empty CORS origins if no browser frontend makes direct calls
    cors_origins: List[str] = []
    
    # Session Management
    session_cleanup_interval: int = 1800  # 30 minutes in seconds -> do the idle check scan every 30 min
    max_session_age: int = 3600  # 1 hours in seconds -> sesson idle for 1h, then delete session to free memory
    
    # Security
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings() 