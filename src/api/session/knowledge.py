import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...models.knowledge import UploadRequest, UploadResponse, KnowledgeStatus
from ...services.session_service import session_service

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Import auth dependency
from ...auth.security import verify_api_key

@router.post("/knowledge/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_knowledge(
    upload_request: UploadRequest,
    request: Request,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    auth: str = Depends(verify_api_key)
):
    """Upload knowledge chunks for a session"""
    
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "missing_session_id"
            }
        )
    
    try:
        if not upload_request.knowledge_chunks:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": "invalid_knowledge_chunks"
                }
            )
        
        # Store knowledge in session
        await session_service.store_knowledge(
            x_session_id, 
            upload_request.knowledge_chunks
        )
        
        # Track metrics for knowledge upload
        from ...utils.metrics import metrics
        metrics.record_knowledge_upload(x_session_id, len(upload_request.knowledge_chunks))
        
        return UploadResponse(
            success=True,
            session_id=x_session_id,
            chunks_processed=len(upload_request.knowledge_chunks)
        )
        
    except Exception as e:
        logger.error(f"❌ Knowledge upload error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "upload_failed",
                "message": str(e)
            }
        )

@router.get("/knowledge/status", response_model=KnowledgeStatus)
@limiter.limit("30/minute")
async def get_knowledge_status(
    request: Request,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Get knowledge status for a session"""
    
    if not x_session_id:
        return KnowledgeStatus(
            has_knowledge=False,
            chunk_count=0,
            domains=[],
            session_id=None
        )
    
    # Get detailed session stats including vector search info
    stats = session_service.get_session_stats(x_session_id)
    
    return KnowledgeStatus(
        has_knowledge=stats["has_session"],
        chunk_count=stats["chunk_count"],
        session_id=x_session_id
    )

@router.get("/knowledge/stats")
@limiter.limit("30/minute")
async def get_detailed_stats(
    request: Request,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Get detailed statistics for a session including vector search info"""
    
    if not x_session_id:
        return {
            "success": False,
            "error": "missing_session_id"
        }
    
    stats = session_service.get_session_stats(x_session_id)
    return {
        "success": True,
        "session_id": x_session_id,
        "stats": stats
    } 

@router.delete("/knowledge/session")
@limiter.limit("10/minute") 
async def delete_session(
    request: Request,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """Delete a session and all its knowledge data"""
    
    if not x_session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "missing_session_id"
            }
        )
    
    try:
        # Remove the session
        removed = await session_service.remove_session(x_session_id)
        
        if removed:
            return {
                "success": True,
                "session_id": x_session_id,
                "message": "Session deleted successfully"
            }
        else:
            return {
                "success": False,
                "session_id": x_session_id,
                "message": "Session not found"
            }
        
    except Exception as e:
        logger.error(f"❌ Session deletion error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "deletion_failed",
                "message": str(e)
            }
        )