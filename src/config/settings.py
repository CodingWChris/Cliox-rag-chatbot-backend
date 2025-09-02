from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import field_validator

class Settings(BaseSettings):
    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2:1b"  # Changed to faster 1B model
    
    # Server Configuration
    environment: str = "development"
    port: int = 8001
    # CORS origins
    cors_origins: List[str] = ["http://localhost:8000"]
    
    
    # Session Management
    session_cleanup_interval: int = 1800  # 30 minutes in seconds -> do the idle check scan every 30 min
    max_session_age: int = 3600  # 1 hours in seconds -> sesson idle for 1h, then delete session to free memory
    
    # Security
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 60
    
    # AWS S3 Configuration for Conversation Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    aws_default_region: str = "us-west-2"
    s3_conversation_bucket: str = "cliox-chatbot-conversations"
    
    # Conversation Management Settings
    conversation_summary_threshold: int = 10  # Summarize after N messages
    max_conversation_history_messages: int = 50  # Max messages to keep in full history
    conversation_context_max_tokens: int = 1000  # Max tokens for conversation context
    
    class Config:
        env_file = ".env"

settings = Settings()