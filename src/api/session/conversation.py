"""
Conversation API endpoints for managing chat history and summaries
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from ...auth.security import verify_api_key
from ...services.s3_conversation_service import conversation_storage, ConversationMessage
from ...services.conversation_summarizer import conversation_summarizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversation", tags=["conversation"])

@router.get("/{session_id}/history")
async def get_conversation_history(
    session_id: str,
    limit: Optional[int] = None,
    credentials = Depends(verify_api_key)
):
    """Get conversation history for a session"""
    try:
        if limit:
            messages = await conversation_storage.load_recent_messages(session_id, limit)
        else:
            messages = await conversation_storage.load_conversation(session_id)
        
        if messages is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "session_id": session_id,
            "message_count": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get conversation history for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")

@router.get("/{session_id}/summary")
async def get_conversation_summary(
    session_id: str,
    credentials = Depends(verify_api_key)
):
    """Get conversation summary for a session"""
    try:
        summary = await conversation_storage.load_summary(session_id)
        
        if summary is None:
            raise HTTPException(status_code=404, detail="Conversation summary not found")
        
        return {
            "success": True,
            "session_id": session_id,
            "summary": {
                "version": summary.summary_version,
                "created_at": summary.created_at,
                "last_updated": summary.last_updated,
                "conversation_summary": summary.conversation_summary,
                "key_topics": summary.key_topics,
                "user_context": summary.user_context,
                "messages_summarized": summary.messages_summarized,
                "last_message_id": summary.last_message_id
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get conversation summary for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation summary")

@router.post("/{session_id}/summarize")
async def trigger_summarization(
    session_id: str,
    credentials = Depends(verify_api_key)
):
    """Manually trigger conversation summarization"""
    try:
        # Check if session exists
        if not await conversation_storage.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate summary
        summary = await conversation_summarizer.generate_summary(session_id)
        
        if summary is None:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Summary generated successfully",
            "summary_version": summary.summary_version,
            "messages_summarized": summary.messages_summarized
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate summary for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

@router.get("/{session_id}/context")
async def get_conversation_context(
    session_id: str,
    max_tokens: Optional[int] = 1000,
    credentials = Depends(verify_api_key)
):
    """Get conversation context for chat responses (summary + recent messages)"""
    try:
        context = await conversation_summarizer.get_conversation_context(session_id, max_tokens)
        
        return {
            "success": True,
            "session_id": session_id,
            "context": context,
            "estimated_tokens": len(context) // 4  # Rough estimation
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get conversation context for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation context")

@router.delete("/{session_id}")
async def delete_conversation(
    session_id: str,
    credentials = Depends(verify_api_key)
):
    """Delete conversation and all associated data"""
    try:
        success = await conversation_storage.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Conversation deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete conversation {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")

@router.get("/{session_id}/exists")
async def check_conversation_exists(
    session_id: str,
    credentials = Depends(verify_api_key)
):
    """Check if a conversation exists"""
    try:
        exists = await conversation_storage.session_exists(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "exists": exists
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to check if conversation exists for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check conversation existence")
