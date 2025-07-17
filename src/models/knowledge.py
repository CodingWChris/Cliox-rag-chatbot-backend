from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class KnowledgeChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]

class SessionKnowledge(BaseModel):
    chunks: List[KnowledgeChunk]
    domains: List[str]
    created_at: datetime
    last_accessed: datetime

class UploadRequest(BaseModel):
    session_id: str
    knowledge_chunks: List[KnowledgeChunk]
    domains: List[str] = []

class UploadResponse(BaseModel):
    success: bool
    session_id: str
    chunks_processed: int
    domains: List[str]
    message: Optional[str] = None

class KnowledgeStatus(BaseModel):
    has_knowledge: bool
    chunk_count: int
    domains: List[str]
    session_id: Optional[str]

class ChatRequest(BaseModel):
    session_id: str
    message: str
    config: Dict[str, Any] = {}

class ChatSource(BaseModel):
    source: str
    relevance_score: float
    content_preview: str

class ChatMetadata(BaseModel):
    chunks_retrieved: int
    processing_time_ms: int
    model_used: str
    
    model_config = {"protected_namespaces": ()}

class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    sources: Optional[List[ChatSource]] = None
    metadata: Optional[ChatMetadata] = None
    error: Optional[str] = None
    message: Optional[str] = None 