# RAG Chatbot API Documentation

## Overview
This is a comprehensive guide for all available API endpoints in the RAG Chatbot backend. All endpoints require API key authentication unless specified otherwise.

**Base URL**: `http://localhost:8000` (development) or your production URL
**API Version**: v1.0.0

## Authentication
All endpoints (except root and health) require API key authentication:
- **Header**: `Authorization: Bearer YOUR_API_KEY`
- **Alternative Header**: `X-API-Key: YOUR_API_KEY`

## Rate Limiting
- Most endpoints have rate limiting enabled
- Limits vary by endpoint (specified in each section)
- Rate limit headers are included in responses

---

## 📊 Health & Monitoring

### GET `/api/health`
**Health check endpoint - No authentication required**

Returns the current health status of the application and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1693747200.123,
  "ollama_connected": true,
  "available_models": ["llama3.1", "mistral"],
  "active_sessions": 5,
  "uptime_seconds": 3600.45,
  "vector_service": {
    "model": "all-MiniLM-L6-v2",
    "active_sessions": 5,
    "collections": ["session1", "session2"]
  }
}
```

**Error Response (500):**
```json
{
  "status": "unhealthy",
  "error": "Ollama connection failed"
}
```

### GET `/api/v1/monitoring/metrics`
**Get comprehensive application metrics**
- **Rate Limit**: Not specified
- **Authentication**: Required

**Response:**
```json
{
  "uptime_seconds": 3600,
  "total_requests": 1250,
  "total_errors": 15,
  "error_rate": 1.2,
  "services": {
    "ollama": {
      "healthy": true,
      "available_models": ["llama3.1", "mistral"],
      "model_count": 2
    },
    "vector_service": {
      "model": "all-MiniLM-L6-v2",
      "active_collections": 5,
      "total_vectors": 1500
    },
    "session_service": {
      "active_sessions": 5,
      "cleanup_interval": 3600,
      "max_session_age": 86400
    }
  }
}
```

---

## 💬 Chat Endpoints

### POST `/api/v1/session/chat`
**Process chat messages with RAG (Retrieval-Augmented Generation)**
- **Rate Limit**: 20 requests/minute
- **Authentication**: Required
- **Session Header**: `X-Session-ID` (required)

#### Streaming Mode (Default - Recommended)
**Query Parameter**: `stream=true` (default)

Returns Server-Sent Events (SSE) for real-time response generation.

**Request:**
```json
{
  "message": "What is the main topic of the uploaded document?",
  "config": {
    "temperature": 0.7,
    "max_tokens": 500
  }
}
```

**Headers:**
```
X-Session-ID: your-session-uuid
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY
```

**Response**: Server-Sent Events stream
```
data: {"type": "status", "content": "Processing your question..."}

data: {"type": "text", "content": "Based on the uploaded document, "}

data: {"type": "text", "content": "the main topic appears to be..."}

data: {"type": "done", "content": ""}
```

#### Legacy Mode (Non-streaming)
**Query Parameter**: `stream=false`

**Response:**
```json
{
  "success": true,
  "response": "Based on the uploaded document, the main topic appears to be...",
  "session_id": "session-uuid",
  "sources": [
    {
      "content": "Relevant document chunk...",
      "score": 0.85
    }
  ],
  "metadata": {
    "model_used": "llama3.1",
    "response_time_ms": 2340,
    "tokens_used": 156
  }
}
```

**Error Responses:**
```json
// Missing session ID
{
  "success": false,
  "error": "missing_session_id"
}

// Invalid message
{
  "success": false,
  "error": "invalid_message"
}

// Processing error
{
  "success": false,
  "error": "chat_failed",
  "message": "Detailed error message"
}
```

---

## 📚 Knowledge Management

### POST `/api/v1/session/knowledge/upload`
**Upload knowledge chunks for a session**
- **Rate Limit**: 10 requests/minute
- **Authentication**: Required
- **Session Header**: `X-Session-ID` (required)

**Request:**
```json
{
  "knowledge_chunks": [
    {
      "content": "This is the first chunk of knowledge...",
      "metadata": {
        "source": "document1.pdf",
        "page": 1,
        "section": "Introduction"
      }
    },
    {
      "content": "This is the second chunk...",
      "metadata": {
        "source": "document1.pdf",
        "page": 2,
        "section": "Methodology"
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "chunks_processed": 2
}
```

**Error Responses:**
```json
// Missing session ID
{
  "success": false,
  "error": "missing_session_id"
}

// Invalid chunks
{
  "success": false,
  "error": "invalid_knowledge_chunks"
}

// Upload failed
{
  "success": false,
  "error": "upload_failed",
  "message": "Detailed error message"
}
```

### GET `/api/v1/session/knowledge/status`
**Get knowledge status for a session**
- **Rate Limit**: 30 requests/minute
- **Session Header**: `X-Session-ID` (optional)

**Response:**
```json
{
  "has_knowledge": true,
  "chunk_count": 15,
  "domains": [],
  "session_id": "session-uuid"
}
```

**Without Session ID:**
```json
{
  "has_knowledge": false,
  "chunk_count": 0,
  "domains": [],
  "session_id": null
}
```

### GET `/api/v1/session/knowledge/stats`
**Get detailed statistics for a session**
- **Rate Limit**: 30 requests/minute
- **Session Header**: `X-Session-ID` (optional)

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "stats": {
    "has_session": true,
    "chunk_count": 15,
    "vector_count": 15,
    "last_activity": "2024-01-01T12:00:00Z",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

### DELETE `/api/v1/session/knowledge/session`
**Delete a session and all its knowledge data**
- **Rate Limit**: 10 requests/minute
- **Session Header**: `X-Session-ID` (required)

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "message": "Session deleted successfully"
}
```

**Session Not Found:**
```json
{
  "success": false,
  "session_id": "session-uuid",
  "message": "Session not found"
}
```

---

## 🗨️ Conversation Management

### GET `/api/v1/conversation/{session_id}/history`
**Get conversation history for a session**
- **Authentication**: Required
- **Parameters**: 
  - `session_id` (path): Session UUID
  - `limit` (query, optional): Limit number of messages

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "message_count": 10,
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "Hello, what can you tell me about...",
      "timestamp": "2024-01-01T12:00:00Z",
      "metadata": {}
    },
    {
      "id": "msg-uuid-2",
      "role": "assistant",
      "content": "Based on the information provided...",
      "timestamp": "2024-01-01T12:00:05Z",
      "metadata": {
        "model": "llama3.1",
        "tokens": 156
      }
    }
  ]
}
```

### GET `/api/v1/conversation/{session_id}/summary`
**Get conversation summary for a session**
- **Authentication**: Required

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "summary": {
    "version": 1,
    "created_at": "2024-01-01T12:00:00Z",
    "last_updated": "2024-01-01T13:00:00Z",
    "conversation_summary": "The user asked about document analysis and received detailed explanations...",
    "key_topics": ["document analysis", "AI", "machine learning"],
    "user_context": "User is interested in AI applications for document processing",
    "messages_summarized": 8,
    "last_message_id": "msg-uuid-8"
  }
}
```

### POST `/api/v1/conversation/{session_id}/summarize`
**Manually trigger conversation summarization**
- **Authentication**: Required

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "message": "Summary generated successfully",
  "summary_version": 2,
  "messages_summarized": 12
}
```

### GET `/api/v1/conversation/{session_id}/context`
**Get conversation context for chat responses**
- **Authentication**: Required
- **Parameters**: 
  - `max_tokens` (query, optional): Maximum tokens for context (default: 1000)

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "context": "Previous conversation summary and recent messages context...",
  "estimated_tokens": 250
}
```

### GET `/api/v1/conversation/{session_id}/exists`
**Check if a conversation exists**
- **Authentication**: Required

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "exists": true
}
```

### DELETE `/api/v1/conversation/{session_id}`
**Delete conversation and all associated data**
- **Authentication**: Required

**Response:**
```json
{
  "success": true,
  "session_id": "session-uuid",
  "message": "Conversation deleted successfully"
}
```

---

## 🏠 Root Endpoint

### GET `/`
**Root endpoint - No authentication required**

**Response:**
```json
{
  "message": "RAG Chatbot API",
  "version": "1.0.0",
  "status": "healthy"
}
```

---

## 🔗 Frontend Integration Examples

### JavaScript/TypeScript Examples

#### Health Check
```typescript
async function healthCheck(): Promise<{ status: string; ollama_connected?: boolean }> {
  const response = await fetch('/api/health');
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return await response.json();
}
```

#### Upload Knowledge
```typescript
async function uploadKnowledge(sessionId: string, chunks: KnowledgeChunk[]): Promise<UploadResponse> {
  const response = await fetch('/api/v1/session/knowledge/upload', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Session-ID': sessionId,
      'Authorization': `Bearer ${API_KEY}`
    },
    body: JSON.stringify({ knowledge_chunks: chunks })
  });
  
  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }
  
  return await response.json();
}
```

#### Streaming Chat
```typescript
async function streamingChat(sessionId: string, message: string): Promise<void> {
  const response = await fetch('/api/v1/session/chat?stream=true', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Session-ID': sessionId,
      'Authorization': `Bearer ${API_KEY}`
    },
    body: JSON.stringify({ message })
  });

  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        // Handle streaming data
        console.log('Stream chunk:', data);
      }
    }
  }
}
```

#### Get Conversation History
```typescript
async function getConversationHistory(sessionId: string, limit?: number): Promise<ConversationHistory> {
  const url = new URL('/api/v1/conversation/' + sessionId + '/history', window.location.origin);
  if (limit) {
    url.searchParams.set('limit', limit.toString());
  }

  const response = await fetch(url.toString(), {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to get history: ${response.status}`);
  }

  return await response.json();
}
```

---

## 🚨 Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (missing parameters, invalid data)
- **401**: Unauthorized (missing or invalid API key)
- **404**: Not Found (session/conversation not found)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error (server-side error)

### Common Error Response Format
```json
{
  "success": false,
  "error": "error_code",
  "message": "Detailed error description"
}
```

### Rate Limit Headers
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1693747260
```

---

## 📝 Notes

1. **Session Management**: Always include the `X-Session-ID` header for session-specific operations
2. **Streaming**: Use streaming mode for chat responses for better user experience
3. **Rate Limits**: Respect rate limits to avoid 429 errors
4. **Error Handling**: Always check response status and handle errors appropriately
5. **CORS**: CORS is configured for cross-origin requests if enabled in settings

---

## 🔄 API Changelog

### Version 1.0.0
- Initial API release
- Session-based knowledge management
- Streaming chat responses
- Conversation history and summarization
- Health monitoring and metrics
