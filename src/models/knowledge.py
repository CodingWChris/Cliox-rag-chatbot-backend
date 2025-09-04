from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class KnowledgeChunk(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}

class SessionKnowledge(BaseModel):
    chunks: List[KnowledgeChunk]
    created_at: datetime
    last_accessed: datetime

class UploadRequest(BaseModel):
    knowledge_chunks: List[KnowledgeChunk]

class UploadResponse(BaseModel):
    success: bool
    session_id: str
    chunks_processed: int
    message: Optional[str] = None

class KnowledgeStatus(BaseModel):
    has_knowledge: bool
    chunk_count: int
    session_id: Optional[str]

class ChatRequest(BaseModel):
    message: str
    config: Optional[Dict[str, Any]] = {}

class ChatSource(BaseModel):
    source: str
    relevance_score: float
    content_preview: str

class ChatMetadata(BaseModel):
    chunks_retrieved: int
    processing_time_ms: int
    model_used: str
    
    model_config = {"protected_namespaces": ()}

# ==============================================
# LEGACY RESPONSE MODELS
# ==============================================
# These models are used for backward compatibility with non-streaming responses

class ChatResponse(BaseModel):
    """LEGACY: Complete chat response model for non-streaming responses"""
    success: bool
    response: Optional[str] = None
    sources: Optional[List[ChatSource]] = None
    metadata: Optional[ChatMetadata] = None
    error: Optional[str] = None

# ==============================================
# STREAMING RESPONSE MODELS
# ==============================================
# These models are used for real-time streaming responses

# Streaming models for SSE
class StreamChunk(BaseModel):
    """
    Streaming chunk model for Server-Sent Events
    
    Types:
    - 'status': Processing status updates (e.g., "Searching knowledge base...")
    - 'chunk': Text content chunks as they're generated
    - 'complete': Signal that response generation is finished
    - 'error': Error information if something goes wrong
    """
    type: str  # 'status', 'chunk', 'complete', 'error'
    content: Optional[str] = None
    sources: Optional[List[ChatSource]] = None
    metadata: Optional[Dict[str, Any]] = None
    message: Optional[str] = None 