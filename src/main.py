import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config.settings import settings
from .api.session.knowledge import router as knowledge_router
from .api.session.chat import router as chat_router
from .api.health import router as health_router
from .services.session_service import session_service
from .services.ollama_service import ollama_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting RAG Chatbot API")
    session_service.start_cleanup_task()
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down RAG Chatbot API")
    await ollama_service.close()

# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="Session-based RAG chatbot with Ocean Protocol integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include routers
app.include_router(knowledge_router, prefix="/api/v1/session", tags=["knowledge"])
app.include_router(chat_router, prefix="/api/v1/session", tags=["chat"])
app.include_router(health_router, prefix="/api", tags=["health"])

@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "status": "healthy"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development"
    ) 