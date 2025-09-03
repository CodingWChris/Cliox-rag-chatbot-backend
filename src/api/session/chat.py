import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...models.knowledge import ChatRequest, ChatResponse, StreamChatRequest, StreamChatChunk
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

@router.post("/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(
    chat_request: StreamChatRequest,
    request: Request,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    auth: str = Depends(verify_api_key)
):
    """Process chat message with RAG using Server-Sent Events (SSE)"""
    
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
    
    async def generate_stream():
        """Generate SSE stream"""
        try:
            async for chunk in rag_service.process_chat_stream(
                x_session_id, 
                chat_request.message, 
                chat_request.config
            ):
                # Format as SSE
                if chunk.error:
                    yield f"data: {{\"error\": \"{chunk.error}\", \"done\": true}}\n\n"
                else:
                    # Convert chunk to JSON and send as SSE
                    import json
                    chunk_data = {
                        "content": chunk.content,
                        "done": chunk.done
                    }
                    
                    if chunk.sources:
                        chunk_data["sources"] = [
                            {
                                "source": source.source,
                                "relevance_score": source.relevance_score,
                                "content_preview": source.content_preview
                            }
                            for source in chunk.sources
                        ]
                    
                    if chunk.metadata:
                        chunk_data["metadata"] = {
                            "chunks_retrieved": chunk.metadata.chunks_retrieved,
                            "processing_time_ms": chunk.metadata.processing_time_ms,
                            "model_used": chunk.metadata.model_used
                        }
                    
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    if chunk.done:
                        break
                        
        except Exception as e:
            logger.error(f"❌ Streaming chat error: {e}")
            yield f"data: {{\"error\": \"{str(e)}\", \"done\": true}}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    ) 