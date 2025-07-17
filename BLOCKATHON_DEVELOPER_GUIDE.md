# RAG Chatbot Backend - Blockathon Developer Guide

This guide will help blockathon students understand what parts of the RAG chatbot backend they can modify to customize the system for their specific use case.

## 🎯 Quick Start for Blockathon Development

### What You Can Safely Modify
- **AI Prompts and Responses** - Customize how the AI behaves
- **Knowledge Processing** - Change how documents are processed
- **API Responses** - Modify response formats
- **Configuration** - Adjust system settings
- **New API Endpoints** - Add custom functionality

### What to Avoid Modifying
- Core FastAPI setup (unless you're experienced)
- Async/await patterns (can break the system)
- Session management internals
- Ollama service integration basics

## 🔧 Key Modification Points

### 1. AI Behavior & Prompts (`src/services/rag_service.py`)

**Location**: Lines 45-65 in `src/services/rag_service.py`

**What to modify**:
```python
# Customize the RAG prompt for your use case
rag_prompt = f"""You are a helpful AI assistant with access to relevant information.

Context Information:
{context}

User Question: {query}

Instructions:
- Use the context information as your primary source when relevant
- Enhance with your general knowledge when helpful
- Be conversational and helpful
- Provide sources when using context information

Response:"""
```

**Blockathon Ideas**:
- Make it domain-specific (medical, legal, gaming, etc.)
- Add personality (formal, casual, expert, beginner-friendly)
- Include specific output formats (JSON, structured data, etc.)
- Add safety guidelines for sensitive topics

### 2. Knowledge Processing (`src/services/vector_service.py`)

**Location**: `src/services/vector_service.py`

**Current Implementation**: Simple keyword matching
```python
def calculate_similarity(self, query: str, chunk: str) -> float:
    # Simple keyword-based similarity
    query_words = set(query.lower().split())
    chunk_words = set(chunk.lower().split())
    
    if not query_words:
        return 0.0
    
    intersection = query_words.intersection(chunk_words)
    return len(intersection) / len(query_words)
```

**Blockathon Improvements**:
```python
# Example: Add domain-specific keywords
def calculate_similarity(self, query: str, chunk: str) -> float:
    # Add domain-specific scoring
    domain_keywords = {
        "blockchain": ["smart contract", "cryptocurrency", "token", "defi"],
        "medical": ["treatment", "diagnosis", "patient", "therapy"],
        "legal": ["contract", "agreement", "liability", "compliance"]
    }
    
    base_score = len(query_words.intersection(chunk_words)) / len(query_words)
    
    # Boost score for domain keywords
    for domain, keywords in domain_keywords.items():
        if any(keyword in chunk.lower() for keyword in keywords):
            base_score *= 1.5
    
    return min(base_score, 1.0)
```

### 3. Response Format (`src/models/knowledge.py`)

**Location**: `src/models/knowledge.py`

**Add Custom Response Fields**:
```python
class ChatResponse(BaseModel):
    response: str
    sources: List[ChatSource] = []
    metadata: ChatMetadata
    
    # Add your custom fields here
    confidence_score: Optional[float] = None
    response_type: Optional[str] = None  # "factual", "creative", "analysis"
    suggested_followups: Optional[List[str]] = None
    domain_detected: Optional[str] = None
```

### 4. New API Endpoints (`src/api/`)

**Create Custom Endpoints**: Add new files in `src/api/` or extend existing ones

**Example - Analytics Endpoint**:
```python
# src/api/analytics.py
from fastapi import APIRouter, Depends
from ..services.session_service import SessionService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/session-stats/{session_id}")
async def get_session_stats(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    
    return {
        "total_chunks": len(session.knowledge_chunks),
        "domains": list(set(chunk.domain for chunk in session.knowledge_chunks)),
        "last_updated": session.last_accessed
    }
```

**Example - Custom Processing Endpoint**:
```python
# src/api/custom.py
@router.post("/summarize")
async def summarize_knowledge(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service)
):
    # Custom logic to summarize all knowledge in session
    summary = await rag_service.generate_summary(session_id)
    return {"summary": summary}
```

### 5. Configuration Changes (`src/config/settings.py`)

**Add Custom Settings**:
```python
class Settings(BaseSettings):
    # Existing settings...
    
    # Add your custom settings
    custom_domain: str = "general"
    max_response_length: int = 1000
    enable_analytics: bool = True
    custom_model_name: str = "llama3.2:1b"
    response_temperature: float = 0.7
    
    class Config:
        env_file = ".env"
```

## 🚀 Common Blockathon Modifications

### 1. **Domain-Specific Chatbot**
- **File**: `src/services/rag_service.py` 
- **Change**: Modify the RAG prompt to be specialized (medical, legal, finance, etc.)

### 2. **Multi-Language Support**
- **File**: `src/services/ollama_service.py`
- **Change**: Add language parameter and prepend language instruction to prompts

### 3. **Structured JSON Responses**
- **File**: `src/services/rag_service.py`
- **Change**: Force responses in JSON format with specific fields (confidence, sources, etc.)

### 4. **Real-time Data Integration**
- **File**: Create `src/services/external_data_service.py`
- **Change**: Add API calls to fetch live data (crypto prices, news, weather, etc.)

## 🧪 Testing Your Changes

### 1. Quick API Testing
```bash
# Test health endpoint
curl http://localhost:8001/api/health

# Test your new endpoint
curl -X POST http://localhost:8001/api/v1/your-endpoint \
  -H "Content-Type: application/json" \
  -d '{"your": "data"}'
```

### 2. Test with Different Queries
```python
# Create test scripts in tests/ directory
import asyncio
from src.services.rag_service import RAGService

async def test_custom_behavior():
    rag_service = RAGService()
    response = await rag_service.generate_response("test query", "test_session")
    print(f"Response: {response}")

asyncio.run(test_custom_behavior())
```

## 🔍 Debugging Tips

### 1. Add Logging
```python
import logging
logger = logging.getLogger(__name__)

# Add to your functions
logger.info(f"Processing query: {query}")
logger.debug(f"Found {len(chunks)} relevant chunks")
```

### 2. Enable Debug Mode
In `src/main.py`:
```python
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # More permissive for debugging
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

## 📚 Integration Examples

### Frontend Integration
```javascript
// Example: Custom domain detection
const response = await fetch('/api/v1/session/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        session_id: 'blockathon_session',
        query: 'What is machine learning?',
        domain: 'technology'  // Custom domain
    })
});
```

### Database Integration
```python
# Add to requirements.txt: databases[postgresql]
from databases import Database

class DatabaseService:
    def __init__(self):
        self.database = Database("postgresql://user:pass@localhost/db")
    
    async def store_conversation(self, session_id: str, query: str, response: str):
        await self.database.execute(
            "INSERT INTO conversations (session_id, query, response) VALUES (:session_id, :query, :response)",
            values={"session_id": session_id, "query": query, "response": response}
        )
```

## 🎖️ Blockathon Success Tips

1. **Start Small**: Make one change at a time and test it
2. **Use Version Control**: Commit working versions frequently
3. **Document Changes**: Comment your modifications clearly
4. **Test Edge Cases**: What happens with empty queries, long texts, etc.?
5. **Performance**: Monitor response times with large knowledge bases
6. **Error Handling**: Add proper error messages for user experience

## 🚨 Common Pitfalls

1. **Breaking Async Code**: Don't remove `async`/`await` keywords
2. **Session Management**: Don't modify session internals without understanding them
3. **Memory Leaks**: Large knowledge bases can consume memory quickly
4. **Port Conflicts**: Stick to port 8001 unless you update all configs
5. **CORS Issues**: Update CORS settings if adding new frontend features

## 🔧 Useful Commands

```bash
# Restart development server
./dev.sh

# Check Ollama status
ollama list

# Monitor logs
tail -f logs/app.log  # if you add logging

# Install new dependencies
conda activate rag-chatbot
pip install new-package
pip freeze > requirements.txt
```

## 🏆 Good Luck!

Remember: The best blockathon projects solve real problems creatively. Focus on making the chatbot genuinely useful for your target users, whether that's students, professionals, or specific domain experts.

**Questions?** Check the main README.md or examine the existing code - it's well-documented and modular for easy modification. 