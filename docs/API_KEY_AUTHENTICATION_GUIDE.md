# API Key Authentication Guide

## Overview
The RAG Chatbot API supports API key authentication for production environments. Authentication is **optional in development** and **required in production** when an API key is set.

## Configuration

### 1. Set API Key (Production)

**Option A: Environment Variable**
```bash
export API_KEY="your-secure-api-key-here"
export ENV="production"
```

**Option B: Docker Compose**
```yaml
environment:
  - API_KEY=your-secure-api-key-here
  - ENV=production
```

**Option C: .env File**
```env
API_KEY=your-secure-api-key-here
ENV=production
```

### 2. Generate Secure API Key
```bash
# Generate a secure random API key
openssl rand -hex 32
# Output: f4e9c8b7a6d5e4f3c2b1a9e8d7c6b5a4f3e2d1c9b8a7f6e5d4c3b2a1f9e8d7c6

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Authentication Behavior

### Development Mode (ENV=development)
- ✅ **No API key required**
- ✅ All endpoints accessible without authentication
- 🔓 Perfect for local testing and development

### Production Mode (ENV=production)
- 🔐 **API key required** for protected endpoints
- ❌ Requests without valid API key are rejected with 401
- ✅ Health endpoint remains public (no auth required)

## Protected Endpoints

### Endpoints that REQUIRE authentication in production:
- `POST /api/v1/session/knowledge/upload`
- `POST /api/v1/session/chat`

### Endpoints that are ALWAYS public:
- `GET /api/health`
- `GET /` (root endpoint)
- `GET /docs` (API documentation)

## Usage Examples

### 1. cURL Examples

**Without Authentication (Development):**
```bash
# Chat request - works in development
curl -X POST http://localhost:8001/api/v1/session/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session" \
  -d '{
    "message": "Hello, what can you help me with?",
    "config": {"temperature": 0.7}
  }'
```

**With Authentication (Production):**
```bash
# Set your API key
API_KEY="your-secure-api-key-here"

# Chat request with authentication
curl -X POST http://YOUR_OCI_IP:8001/api/v1/session/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -H "X-Session-ID: test-session" \
  -d '{
    "message": "Hello, what can you help me with?",
    "config": {"temperature": 0.7}
  }'

# Knowledge upload with authentication
curl -X POST http://YOUR_OCI_IP:8001/api/v1/session/knowledge/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -H "X-Session-ID: test-session" \
  -d '{
    "knowledge_chunks": [
      {
        "id": "doc-1",
        "content": "Ocean Protocol enables data sharing...",
        "metadata": {"source": "documentation"}
      }
    ]
  }'

# Health check (always public, no auth needed)
curl http://YOUR_OCI_IP:8001/api/health
```

### 2. Python Examples

```python
import requests
import os

# Configuration
BASE_URL = "http://YOUR_OCI_IP:8001"
API_KEY = os.getenv("API_KEY", "your-api-key")
SESSION_ID = "python-session-123"

# Headers for authenticated requests
auth_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "X-Session-ID": SESSION_ID
}

# Headers for public endpoints
public_headers = {
    "Content-Type": "application/json"
}

def check_health():
    """Health check - no authentication required"""
    response = requests.get(f"{BASE_URL}/api/health", headers=public_headers)
    print("Health Check:", response.json())
    return response.status_code == 200

def upload_knowledge(content):
    """Upload knowledge - requires authentication in production"""
    knowledge_data = {
        "knowledge_chunks": [
            {
                "id": "python-doc-1",
                "content": content,
                "metadata": {"source": "python-client", "type": "text"}
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/session/knowledge/upload",
        json=knowledge_data,
        headers=auth_headers
    )
    
    if response.status_code == 401:
        print("❌ Authentication failed - check your API key")
        return None
    elif response.status_code == 200:
        print("✅ Knowledge uploaded successfully")
        return response.json()
    else:
        print(f"❌ Upload failed: {response.status_code}")
        return None

def send_message(message):
    """Send chat message - requires authentication in production"""
    chat_data = {
        "message": message,
        "config": {"temperature": 0.7, "max_tokens": 500}
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/session/chat",
        json=chat_data,
        headers=auth_headers
    )
    
    if response.status_code == 401:
        print("❌ Authentication failed - check your API key")
        return None
    elif response.status_code == 200:
        result = response.json()
        print("🤖 Bot Response:", result.get("response"))
        return result
    else:
        print(f"❌ Chat failed: {response.status_code}")
        return None

# Example usage
if __name__ == "__main__":
    # Check if API is healthy
    if check_health():
        # Upload some knowledge
        upload_knowledge("Ocean Protocol is a decentralized data exchange...")
        
        # Send a chat message
        send_message("Tell me about Ocean Protocol")
```

### 3. Node.js Examples

```javascript
const axios = require('axios');

class RagChatbotClient {
    constructor(baseUrl, apiKey, sessionId) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.sessionId = sessionId;
        
        // Headers for authenticated requests
        this.authHeaders = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'X-Session-ID': sessionId
        };
        
        // Headers for public endpoints
        this.publicHeaders = {
            'Content-Type': 'application/json'
        };
    }
    
    async checkHealth() {
        try {
            const response = await axios.get(`${this.baseUrl}/api/health`, {
                headers: this.publicHeaders
            });
            console.log('✅ API is healthy:', response.data);
            return true;
        } catch (error) {
            console.error('❌ Health check failed:', error.response?.data);
            return false;
        }
    }
    
    async uploadKnowledge(chunks) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/api/v1/session/knowledge/upload`,
                { knowledge_chunks: chunks },
                { headers: this.authHeaders }
            );
            
            console.log('✅ Knowledge uploaded:', response.data);
            return response.data;
        } catch (error) {
            if (error.response?.status === 401) {
                console.error('❌ Authentication failed - check your API key');
            } else {
                console.error('❌ Upload failed:', error.response?.data);
            }
            return null;
        }
    }
    
    async sendMessage(message, config = {}) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/api/v1/session/chat`,
                { 
                    message,
                    config: { temperature: 0.7, max_tokens: 500, ...config }
                },
                { headers: this.authHeaders }
            );
            
            console.log('🤖 Bot Response:', response.data.response);
            return response.data;
        } catch (error) {
            if (error.response?.status === 401) {
                console.error('❌ Authentication failed - check your API key');
            } else {
                console.error('❌ Chat failed:', error.response?.data);
            }
            return null;
        }
    }
}

// Example usage
const client = new RagChatbotClient(
    'http://YOUR_OCI_IP:8001',
    'your-api-key-here',
    'nodejs-session-456'
);

async function demo() {
    // Check health
    if (await client.checkHealth()) {
        // Upload knowledge
        await client.uploadKnowledge([
            {
                id: 'node-doc-1',
                content: 'Ocean Protocol enables secure data sharing and monetization...',
                metadata: { source: 'nodejs-client' }
            }
        ]);
        
        // Send message
        await client.sendMessage('What is Ocean Protocol?');
    }
}

demo();
```

### 4. React/Frontend Example (if CORS enabled)

```javascript
// React component example
import React, { useState } from 'react';

const ChatComponent = () => {
    const [message, setMessage] = useState('');
    const [response, setResponse] = useState('');
    const [apiKey, setApiKey] = useState('');
    
    const API_BASE = 'http://YOUR_OCI_IP:8001';
    const SESSION_ID = 'react-session-789';
    
    const sendMessage = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/session/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`,
                    'X-Session-ID': SESSION_ID
                },
                body: JSON.stringify({
                    message,
                    config: { temperature: 0.7 }
                })
            });
            
            if (response.status === 401) {
                setResponse('❌ Authentication failed - check your API key');
                return;
            }
            
            const data = await response.json();
            setResponse(data.response);
            
        } catch (error) {
            setResponse('❌ Error: ' + error.message);
        }
    };
    
    return (
        <div>
            <input
                type="password"
                placeholder="API Key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
            />
            <input
                type="text"
                placeholder="Your message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
            />
            <button onClick={sendMessage}>Send</button>
            <div>Response: {response}</div>
        </div>
    );
};
```

## Error Responses

### Authentication Errors
```json
{
  "success": false,
  "error": "invalid_api_key",
  "message": "Invalid or missing API key"
}
```

### Missing Session ID
```json
{
  "success": false,
  "error": "missing_session_id"
}
```

## Security Best Practices

1. **Keep API Keys Secret**
   - Never commit API keys to version control
   - Use environment variables or secure key management
   - Rotate keys regularly

2. **Use HTTPS in Production**
   - Set up SSL/TLS certificates
   - Never send API keys over HTTP

3. **Monitor Usage**
   - Check API logs for unauthorized access attempts
   - Implement rate limiting (already included)

4. **Development vs Production**
   - Use different API keys for different environments
   - Disable authentication in development for easier testing

## Testing Authentication

### Test Development Mode (No Auth)
```bash
# Should work without API key
curl -X POST http://localhost:8001/api/v1/session/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test" \
  -d '{"message": "test"}'
```

### Test Production Mode (With Auth)
```bash
# Should fail without API key
curl -X POST http://YOUR_OCI_IP:8001/api/v1/session/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test" \
  -d '{"message": "test"}'

# Should succeed with valid API key
curl -X POST http://YOUR_OCI_IP:8001/api/v1/session/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -H "X-Session-ID: test" \
  -d '{"message": "test"}'
```
