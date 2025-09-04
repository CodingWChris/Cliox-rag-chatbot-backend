# 🚀 SSE (Server-Sent Events) Guide

Complete guide for using the new Server-Sent Events functionality in your RAG Chatbot Backend.

## 📋 Overview

The backend now supports **real-time streaming responses** using Server-Sent Events (SSE), allowing users to see AI responses as they're being generated, similar to ChatGPT's streaming interface.

## 🔗 New Endpoints

### Streaming Chat Endpoint
- **URL**: `POST /api/v1/session/chat/stream`
- **Content-Type**: `text/event-stream`
- **Headers**: Same as regular chat endpoint
- **Response**: Real-time streaming SSE data

### Regular Chat Endpoint (Still Available)
- **URL**: `POST /api/v1/session/chat`
- **Content-Type**: `application/json`
- **Response**: Complete response in one request

## 🚀 How to Use SSE

### 1. Frontend JavaScript Example

```javascript
// Create EventSource for SSE connection
const eventSource = new EventSource('/api/v1/session/chat/stream');

// Listen for messages
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.error) {
        console.error('Error:', data.error);
        return;
    }
    
    if (data.content) {
        // Append content to UI
        appendToChat(data.content);
    }
    
    if (data.done) {
        // Stream completed
        console.log('Sources:', data.sources);
        console.log('Metadata:', data.metadata);
        eventSource.close();
    }
};

// Handle errors
eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
};
```

### 2. Python Client Example

```python
import aiohttp
import json

async def stream_chat():
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'http://localhost:8001/api/v1/session/chat/stream',
            json={
                "message": "Hello! Tell me about AI.",
                "config": {
                    "model": "llama3.2:1b",
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            },
            headers={
                "X-Session-ID": "your_session_id",
                "Authorization": "Bearer your_api_key"
            }
        ) as response:
            
            async for line in response.content:
                if line:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith('data: '):
                        try:
                            data = json.loads(line_text[6:])
                            if data.get('content'):
                                print(data['content'], end='', flush=True)
                            if data.get('done'):
                                break
                        except json.JSONDecodeError:
                            continue
```

## 📊 Response Format

### SSE Data Structure

Each SSE message contains a JSON object with the following fields:

```json
{
    "content": "Generated text chunk",
    "done": false,
    "sources": null,
    "metadata": null,
    "error": null
}
```

### Final Message (when done=true)

```json
{
    "content": "Final text chunk",
    "done": true,
    "sources": [
        {
            "source": "document_name.pdf",
            "relevance_score": 0.85,
            "content_preview": "This document contains..."
        }
    ],
    "metadata": {
        "chunks_retrieved": 3,
        "processing_time_ms": 1250,
        "model_used": "llama3.2:1b"
    },
    "error": null
}
```

## ⚙️ Configuration Options

### Chat Configuration

```json
{
    "message": "Your question here",
    "config": {
        "model": "llama3.2:1b",
        "temperature": 0.7,
        "max_tokens": 500,
        "top_k": 3
    }
}
```

- **model**: Ollama model to use
- **temperature**: Creativity level (0.0 - 2.0)
- **max_tokens**: Maximum response length
- **top_k**: Number of knowledge chunks to retrieve

## 🔧 Backend Implementation Details

### 1. Ollama Service Updates

- Added `generate_stream()` method
- Supports `"stream": true` parameter
- Parses Ollama's streaming response format

### 2. RAG Service Updates

- Added `process_chat_stream()` method
- Maintains same RAG pipeline logic
- Yields streaming chunks instead of single response

### 3. API Endpoint

- New `/chat/stream` endpoint
- Uses FastAPI's `StreamingResponse`
- Proper SSE headers and formatting

## 🧪 Testing

### 1. Python Test Script

Run the included test script:

```bash
cd testing
python test_sse.py
```

**Note**: Update the API key in the script before running.

### 2. Frontend Demo

Open `testing/sse_frontend_example.html` in your browser:

```bash
# Start your backend
python -m src.main

# Open the HTML file in your browser
open testing/sse_frontend_example.html
```

## 🚨 Important Notes

### 1. Ollama Requirements

- Ollama must support streaming responses
- Ensure your Ollama version is up to date
- Some models may not support streaming

### 2. Error Handling

- Always check for `error` field in SSE messages
- Handle connection errors gracefully
- Implement retry logic for production use

### 3. Performance

- Streaming reduces perceived latency
- May increase total processing time slightly
- Better user experience for long responses

## 🔄 Migration from Regular Chat

### Before (Regular Chat)

```python
response = await rag_service.process_chat(session_id, message, config)
# Wait for complete response
print(response.response)
```

### After (Streaming Chat)

```python
async for chunk in rag_service.process_chat_stream(session_id, message, config):
    if chunk.content:
        print(chunk.content, end='', flush=True)
    if chunk.done:
        break
```

## 🌟 Benefits of SSE

✅ **Real-time Feedback**: Users see responses as they're generated  
✅ **Better UX**: No more waiting for complete responses  
✅ **Progress Indication**: Users know the system is working  
✅ **Lower Perceived Latency**: Faster perceived response times  
✅ **Interactive Feel**: More engaging chat experience  

## 🐛 Troubleshooting

### Common Issues

1. **SSE Connection Fails**
   - Check CORS settings
   - Verify API key and session ID
   - Ensure backend is running

2. **No Streaming Response**
   - Verify Ollama supports streaming
   - Check model configuration
   - Review backend logs

3. **Partial Responses**
   - Check network stability
   - Verify SSE parsing logic
   - Review error handling

### Debug Mode

Enable debug logging in your backend:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Additional Resources

- [Server-Sent Events MDN Guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)

---

🎉 **Congratulations!** Your RAG backend now supports real-time streaming responses with SSE! 