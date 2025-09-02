import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..models.knowledge import SessionKnowledge, KnowledgeChunk
from .vector_service import vector_service
from ..config.settings import settings

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self.sessions: Dict[str, SessionKnowledge] = {}
        self.cleanup_task = None
        self._started = False
        # Add monitoring properties
        self.cleanup_interval = settings.session_cleanup_interval
        self.max_session_age = settings.max_session_age
    
    def start_cleanup_task(self):
        """Start the background cleanup task"""
        if not self._started and (self.cleanup_task is None or self.cleanup_task.done()):
            try:
                self.cleanup_task = asyncio.create_task(self._cleanup_loop())
                self._started = True
            except RuntimeError:
                # No event loop running yet, will start later when FastAPI starts
                pass
    
    async def _cleanup_loop(self):
        """Background task to clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def store_knowledge(
        self, 
        session_id: str, 
        chunks: List[KnowledgeChunk]
    ) -> None:
        """Store knowledge chunks for a session"""
        now = datetime.now()
        
        # Store in session memory
        self.sessions[session_id] = SessionKnowledge(
            chunks=chunks,
            created_at=now,
            last_accessed=now
        )
        
        # Add to vector store for semantic search
        await vector_service.add_chunks(session_id, chunks)
        
        logger.info(f"📚 Stored knowledge for session {session_id}: {len(chunks)} chunks")
    
    async def get_knowledge(self, session_id: str) -> Optional[SessionKnowledge]:
        """Get knowledge for a session and update last accessed time"""
        if session_id in self.sessions:
            knowledge = self.sessions[session_id]
            knowledge.last_accessed = datetime.now()
            return knowledge
        return None
    
    async def has_knowledge(self, session_id: str) -> bool:
        """Check if session has knowledge stored"""
        return session_id in self.sessions
    
    def get_session_count(self) -> int:
        """Get current number of active sessions"""
        return len(self.sessions)
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count of cleaned sessions"""
        now = datetime.now()
        max_age = timedelta(seconds=self.max_session_age)
        
        expired_sessions = []
        for session_id, knowledge in self.sessions.items():
            if now - knowledge.last_accessed > max_age:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            # Remove from session memory
            del self.sessions[session_id]
            # Remove from vector store
            await vector_service.remove_session(session_id)
            
            # Also clean up conversation data from S3
            try:
                from .s3_conversation_service import conversation_storage
                await conversation_storage.delete_session(session_id)
                logger.debug(f"🗑️ Cleaned up S3 conversation data for session {session_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean up S3 data for session {session_id}: {e}")
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions (including S3 data)")
        
        return len(expired_sessions)
    
    async def remove_session(self, session_id: str) -> bool:
        """Manually remove a specific session and return success status"""
        if session_id in self.sessions:
            # Remove from session memory
            del self.sessions[session_id]
            # Remove from vector store (ChromaDB collection)
            await vector_service.remove_session(session_id)
            
            # Also clean up conversation data from S3
            try:
                from .s3_conversation_service import conversation_storage
                await conversation_storage.delete_session(session_id)
                logger.info(f"🗑️ Manually removed session {session_id} (including S3 data)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean up S3 data for session {session_id}: {e}")
                logger.info(f"🗑️ Manually removed session {session_id} (S3 cleanup failed)")
            
            return True
        else:
            logger.info(f"ℹ️ Session {session_id} not found for removal")
            return False
    
    def get_session_stats(self, session_id: str) -> Dict[str, any]:
        """Get detailed statistics for a session"""
        stats = {
            "has_session": False,
            "chunk_count": 0,
            "created_at": None,
            "last_accessed": None,
            "vector_stats": {}
        }
        
        if session_id in self.sessions:
            knowledge = self.sessions[session_id]
            stats.update({
                "has_session": True,
                "chunk_count": len(knowledge.chunks),
                "created_at": knowledge.created_at.isoformat(),
                "last_accessed": knowledge.last_accessed.isoformat(),
                "vector_stats": vector_service.get_session_stats(session_id)
            })
        
        return stats

# Global session service instance
session_service = SessionService() 