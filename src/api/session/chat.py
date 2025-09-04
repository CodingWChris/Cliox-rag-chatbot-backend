import logging
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Header, Request, Depends, Query
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import json

from ...models.knowledge import ChatRequest, ChatResponse, StreamChunk
from ...services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Import auth dependency
from ...auth.security import verify_api_key

@router.post("/chat")
@limiter.limit("20/minute")
async def chat(
    chat_request: ChatRequest,
    request: Request,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    stream: bool = Query(True, description="Enable streaming response"),
    auth: str = Depends(verify_api_key)
):
    """
    Process chat message with RAG - streaming by default
    
    STREAMING MODE (default, stream=true):
    - Returns Server-Sent Events (SSE) with real-time response generation
    - Provides status updates during processing
    - Text appears progressively like ChatGPT
    - Use EventSource or fetch with stream handling on frontend
    
    LEGACY MODE (stream=false):
    - Returns complete response as JSON (backward compatibility)
    - Traditional request-response pattern
    - Use for existing clients that don't support streaming
    
    Query Parameters:
    - stream=true (default): Enable streaming response
    - stream=false: Use legacy non-streaming response
    """
    
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
    
    if stream:
        # ==============================================
        # STREAMING RESPONSE (PREFERRED, DEFAULT)
        # ==============================================
        # Returns Server-Sent Events for real-time response generation
        
        async def generate_stream():
            try:
                async for chunk in rag_service.process_chat_stream(
                    x_session_id, 
                    chat_request.message, 
                    chat_request.config
                ):
                    # Convert StreamChunk to SSE format
                    chunk_data = chunk.model_dump()
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
            except Exception as e:
                logger.error(f"❌ Streaming chat error: {e}")
                error_chunk = StreamChunk(type="error", content=str(e))
                yield f"data: {json.dumps(error_chunk.model_dump())}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    else:
        # ==============================================
        # LEGACY NON-STREAMING RESPONSE
        # ==============================================
        # Returns complete response as JSON for backward compatibility
        # Use ?stream=false to access this mode
        
        try:
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