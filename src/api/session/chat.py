import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...models.knowledge import ChatRequest, ChatResponse
from ...services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Import auth dependency
from ...auth.security import verify_api_key

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    chat_request: ChatRequest,
    request: Request,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    auth: str = Depends(verify_api_key)
):
    """Process chat message with RAG"""
    
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "missing_session_id"
            }
        )
    
    if not chat_request.message or not isinstance(chat_request.message, str):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "invalid_message"
            }
        )
    
    try:
        # Process chat with RAG
        result = await rag_service.process_chat(
            x_session_id, 
            chat_request.message, 
            chat_request.config
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Chat processing error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "chat_failed",
                "message": str(e)
            }
        ) 