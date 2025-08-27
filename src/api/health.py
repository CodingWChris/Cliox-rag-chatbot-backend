import logging
import time
from fastapi import APIRouter, HTTPException
from ..services.ollama_service import ollama_service
from ..services.session_service import session_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Track start time for uptime calculation
start_time = time.time()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    
    try:
        ollama_healthy = await ollama_service.health_check()
        available_models = await ollama_service.list_models()
        uptime_seconds = time.time() - start_time
        
        # Get vector service info
        from ..services.vector_service import vector_service
        vector_service_info = {
            "model": "all-MiniLM-L6-v2",
            "active_sessions": len(vector_service.session_collections),
            "collections": list(vector_service.session_collections.values()) if vector_service.session_collections else []
        }
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "ollama_connected": ollama_healthy,
            "available_models": available_models,
            "active_sessions": session_service.get_session_count(),
            "uptime_seconds": uptime_seconds,
            "vector_service": vector_service_info
        }
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unhealthy",
                "error": str(e)
            }
        ) 