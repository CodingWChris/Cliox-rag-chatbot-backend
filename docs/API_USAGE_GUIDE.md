# RAG Chatbot API Usage Guide

## Base URL
```
Production: http://YOUR_OCI_PUBLIC_IP:8001
Development: http://localhost:8001
```

## Authentication (Production)
```bash
# Add API key header for production environments
Authorization: Bearer YOUR_API_KEY
```

**📚 For detailed authentication setup and examples, see: [API_KEY_AUTHENTICATION_GUIDE.md](./API_KEY_AUTHENTICATION_GUIDE.md)**

## API Endpoints

### 1. Health Check
```bash
GET /api/health

curl http://YOUR_OCI_PUBLIC_IP:8001/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1724600000,
  "ollama_connected": true,
  "available_models": ["llama3.1:8b"],
  "active_sessions": 2,
  "uptime_seconds": 3600,
  "vector_service": {
    "model": "all-MiniLM-L6-v2",
    "active_sessions": 2
  }
}
```

### 2. Upload Knowledge (Session-based)
```bash
POST /api/v1/session/knowledge/upload
Headers:
  Content-Type: application/json
  X-Session-ID: your-unique-session-id
  Authorization: Bearer YOUR_API_KEY (production only)

curl -X POST http://YOUR_OCI_PUBLIC_IP:8001/api/v1/session/knowledge/upload \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: session-123" \
  -d '{
    "knowledge_chunks": [
      {
        "id": "chunk-1",
        "content": "Ocean Protocol is a decentralized data exchange protocol...",
        "metadata": {"source": "documentation", "category": "protocol"}
      }
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "session_id": "session-123",
  "chunks_processed": 1,
  "message": "Knowledge uploaded successfully"
}
```

### 3. Chat with RAG
```bash
POST /api/v1/session/chat
Headers:
  Content-Type: application/json
  X-Session-ID: your-unique-session-id
  Authorization: Bearer YOUR_API_KEY (production only)

curl -X POST http://YOUR_OCI_PUBLIC_IP:8001/api/v1/session/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: session-123" \
  -d '{
    "message": "What is Ocean Protocol?",
    "config": {
      "model": "llama3.1:8b",
      "temperature": 0.7,
      "max_tokens": 500
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "Ocean Protocol is a decentralized data exchange protocol that enables...",
  "session_id": "session-123",
  "model_used": "llama3.1:8b",
  "processing_time": 2.5,
  "sources_used": ["chunk-1"]
}
```

## Rate Limits
- Knowledge Upload: 10 requests/minute
- Chat: 20 requests/minute
- Health Check: No limit

## Error Responses
```json
{
  "success": false,
  "error": "missing_session_id|invalid_message|chat_failed",
  "message": "Detailed error description"
}
```

## Session Management
- Sessions are automatically cleaned up after 2 hours of inactivity
- Use consistent X-Session-ID headers to maintain context
- Each session maintains its own knowledge base

## Examples for Different Clients

### Python
```python
import requests

# Configuration
BASE_URL = "http://YOUR_OCI_PUBLIC_IP:8001"
SESSION_ID = "my-session-123"
API_KEY = "your-api-key"  # For production

headers = {
    "Content-Type": "application/json",
    "X-Session-ID": SESSION_ID,
    # "Authorization": f"Bearer {API_KEY}"  # Uncomment for production
}

# Upload knowledge
knowledge_data = {
    "knowledge_chunks": [
        {
            "id": "doc-1",
            "content": "Your document content here...",
            "metadata": {"source": "manual"}
        }
    ]
}

response = requests.post(
    f"{BASE_URL}/api/v1/session/knowledge/upload",
    json=knowledge_data,
    headers=headers
)
print(response.json())

# Chat
chat_data = {
    "message": "Tell me about the uploaded content",
    "config": {"temperature": 0.7}
}

response = requests.post(
    f"{BASE_URL}/api/v1/session/chat",
    json=chat_data,
    headers=headers
)
print(response.json())
```

### Node.js
```javascript
const axios = require('axios');

const BASE_URL = 'http://YOUR_OCI_PUBLIC_IP:8001';
const SESSION_ID = 'my-session-123';
// const API_KEY = 'your-api-key'; // For production

const headers = {
    'Content-Type': 'application/json',
    'X-Session-ID': SESSION_ID,
    // 'Authorization': `Bearer ${API_KEY}` // Uncomment for production
};

// Upload knowledge
const uploadKnowledge = async () => {
    try {
        const response = await axios.post(`${BASE_URL}/api/v1/session/knowledge/upload`, {
            knowledge_chunks: [{
                id: 'doc-1',
                content: 'Your document content here...',
                metadata: { source: 'manual' }
            }]
        }, { headers });
        
        console.log(response.data);
    } catch (error) {
        console.error(error.response.data);
    }
};

// Chat
const chat = async () => {
    try {
        const response = await axios.post(`${BASE_URL}/api/v1/session/chat`, {
            message: 'Tell me about the uploaded content',
            config: { temperature: 0.7 }
        }, { headers });
        
        console.log(response.data);
    } catch (error) {
        console.error(error.response.data);
    }
};
```

### Mobile App (React Native)
```javascript
const API_CONFIG = {
    baseURL: 'http://YOUR_OCI_PUBLIC_IP:8001',
    sessionId: 'mobile-session-456',
    // apiKey: 'your-api-key' // For production
};

const uploadKnowledge = async (chunks) => {
    const response = await fetch(`${API_CONFIG.baseURL}/api/v1/session/knowledge/upload`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Session-ID': API_CONFIG.sessionId,
            // 'Authorization': `Bearer ${API_CONFIG.apiKey}` // For production
        },
        body: JSON.stringify({ knowledge_chunks: chunks })
    });
    
    return response.json();
};

const sendMessage = async (message) => {
    const response = await fetch(`${API_CONFIG.baseURL}/api/v1/session/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Session-ID': API_CONFIG.sessionId,
            // 'Authorization': `Bearer ${API_CONFIG.apiKey}` // For production
        },
        body: JSON.stringify({ 
            message,
            config: { temperature: 0.7 }
        })
    });
    
    return response.json();
};
```
