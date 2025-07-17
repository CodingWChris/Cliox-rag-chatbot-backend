from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2:1b"
    
    # Server Configuration
    environment: str = "development"
    port: int = 8001
    cors_origins: List[str] = ["http://localhost:8000", "http://localhost:3000"]
    
    # Session Management
    session_cleanup_interval: int = 1800  # 30 minutes in seconds
    max_session_age: int = 7200  # 2 hours in seconds
    
    # Security
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"

settings = Settings() 