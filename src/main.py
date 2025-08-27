import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config.settings import settings
from .api.session.knowledge import router as knowledge_router
from .api.session.chat import router as chat_router
from .api.health import router as health_router
from .api.monitoring import router as monitoring_router
from .middleware.monitoring import MonitoringMiddleware
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

# Add CORS middleware only if origins are configured
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"🌐 CORS enabled for origins: {settings.cors_origins}")
else:
    logger.info("🚫 CORS disabled - API-only mode")

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Include routers
app.include_router(knowledge_router, prefix="/api/v1/session", tags=["knowledge"])
app.include_router(chat_router, prefix="/api/v1/session", tags=["chat"])
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["monitoring"])

# Mount static files directory (only if it exists)
static_dir = "static"
if os.path.exists(static_dir) and os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Mounted static files directory: {static_dir}")
else:
    logger.warning(f"Static directory '{static_dir}' not found - skipping static file mounting")

@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot API",
        "version": "1.0.0",
        "status": "healthy"
    }

# Note: Server is started via Docker CMD, so comment out 
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "src.main:app",
#         host="0.0.0.0",
#         port=settings.port,
#         reload=settings.environment == "development"
#     )