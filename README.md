### 2. Install Ollama

```bash
# macOS
brew install ollama

# Start Ollama service
ollama serve &

# Pull the required model
ollama pull llama3.1:8b
```

### 3. Set Up Python Environment

```bash
# Create conda environment
conda create -n rag-chatbot python=3.11 -y
conda activate rag-chatbot

# Install dependencies
pip install -r requirements.txt
```

### 4. Start the Server

```bash
# Development mode with auto-reload
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Or use the dev script
./dev.sh
```

🎉 **Your RAG chatbot is now running!**

- **API Server**: http://localhost:8001
- **Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/api/health

## 🚀 Usage

### Step 1: Upload Knowledge

Upload documents to create your knowledge base:

```bash
curl -X POST http://localhost:8001/api/v1/session/knowledge/upload \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: my_session_123" \
  -d '{
    "session_id": "my_session_123",
    "knowledge_chunks": [
      {
        "id": "doc_001",
        "content": "Your document content here...",
        "metadata": {
          "source": "document.pdf",
          "category": "technical",
          "tags": ["ai", "chatbot"]
        }
      }
    ],
    "domains": ["technology", "ai"]
  }'
```

### Step 2: Chat with Your Knowledge

Ask questions and get contextual responses:

```bash
curl -X POST http://localhost:8001/api/v1/session/chat \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: my_session_123" \
  -d '{
    "session_id": "my_session_123",
    "message": "What can you tell me about the uploaded documents?",
    "config": {"max_tokens": 500, "temperature": 0.7}
  }'
```

**Example Response:**
```json
{
  "success": true,
  "response": "Based on your uploaded documents, I can provide information about...",
  "sources": [
    {
      "source": "document.pdf",
      "relevance_score": 3.58,
      "content_preview": "Preview of relevant content..."
    }
  ],
  "metadata": {
    "chunks_retrieved": 3,
    "processing_time_ms": 2639,
    "model_used": "llama3.2:1b"
  }
}
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with API info |
| `/api/health` | GET | Health check and system status |
| `/api/v1/session/knowledge/upload` | POST | Upload knowledge chunks |
| `/api/v1/session/knowledge/status` | GET | Get knowledge base status |
| `/api/v1/session/chat` | POST | Chat with RAG (main endpoint) |

### Required Headers

- `X-Session-ID`: Unique identifier for your session
- `Content-Type: application/json`

## ⚙️ Configuration

Edit `src/config/settings.py` or use environment variables:

```python
# Ollama Configuration
OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:1b"

# Server Configuration
PORT = 8001
CORS_ORIGINS = ["http://localhost:8000", "http://localhost:3000"]

# Session Management
SESSION_CLEANUP_INTERVAL = 1800  # 30 minutes
MAX_SESSION_AGE = 7200  # 2 hours
```

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 2: Manual Docker

```bash
# Build the image
docker build -t rag-chatbot-backend .

# Run the container
docker run -d \
  --name rag-chatbot \
  -p 8001:8001 \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  rag-chatbot-backend
```

## 🔧 Development

### Project Structure

```
src/
├── api/           # API route handlers
│   ├── health.py  # Health check endpoint
│   └── session/   # Session-based endpoints
├── config/        # Configuration management
├── models/        # Pydantic data models
├── services/      # Business logic
│   ├── rag_service.py      # RAG pipeline
│   ├── ollama_service.py   # LLM integration
│   ├── session_service.py  # Session management
│   └── vector_service.py   # Vector search
└── utils/         # Utility functions
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Quality

```bash
# Format code
black src/
isort src/

# Type checking
mypy src/
```

## 📊 Performance

- **Response Time**: ~2-3 seconds for chat requests
- **Throughput**: 20 requests/minute per session (configurable)
- **Model**: llama3.2:1b (1.24B parameters, ~1.3GB)
- **Memory**: ~2GB RAM for the model + API overhead
- **GPU**: Supports Apple Metal acceleration

## 🔍 Monitoring

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": 1752708798.29,
  "ollama_connected": true,
  "available_models": ["llama3.2:1b"],
  "active_sessions": 1,
  "uptime_seconds": 1252.08
}
```

### Logging

The application provides structured logging:

```
2025-07-16 16:33:59 - INFO - 🔍 Processing chat for session demo_session
2025-07-16 16:33:59 - INFO - 📄 Found 3 relevant chunks
2025-07-16 16:33:59 - INFO - 🦙 Calling Ollama with model: llama3.2:1b
2025-07-16 16:34:02 - INFO - 🤖 Generated response in 2639ms
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Cannot connect to Ollama"
```bash
# Check if Ollama is running
ollama list

# Start Ollama if not running
ollama serve &
```

#### 2. "Model not found"
```bash
# Pull the required model
ollama pull llama3.2:1b

# Verify installation
ollama list
```

#### 3. "uvicorn: command not found"
```bash
# Activate the correct environment
conda activate rag-chatbot

# Reinstall dependencies
pip install -r requirements.txt
```

#### 4. Port already in use
```bash
# Check what's using port 8001
lsof -i :8001

# Use a different port
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

### Environment Issues

If you see package import errors:
```bash
# Ensure you're in the correct environment
conda activate rag-chatbot

# Verify Python path
which python
python -c "import fastapi; print('FastAPI installed')"
```