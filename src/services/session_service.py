import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..models.knowledge import SessionKnowledge, KnowledgeChunk

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self.sessions: Dict[str, SessionKnowledge] = {}
        self.cleanup_task = None
        self._started = False
    
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
                await asyncio.sleep(1800)  # 30 minutes
                await self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def store_knowledge(
        self, 
        session_id: str, 
        chunks: List[KnowledgeChunk], 
        domains: List[str]
    ) -> None:
        """Store knowledge chunks for a session"""
        now = datetime.now()
        
        self.sessions[session_id] = SessionKnowledge(
            chunks=chunks,
            domains=domains,
            created_at=now,
            last_accessed=now
        )
        
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
        max_age = timedelta(hours=2)  # 2 hours
        
        expired_sessions = []
        for session_id, knowledge in self.sessions.items():
            if now - knowledge.last_accessed > max_age:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)

# Global session service instance
session_service = SessionService() 