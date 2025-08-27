#!/bin/bash

echo "🔧 Starting RAG Chatbot development environment..."

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️  Ollama is not running. Please start Ollama first:"
    echo "   brew install ollama"
    echo "   ollama serve"
    echo ""
    echo "Then pull a model:"
    echo "   ollama pull llama2:7b"
    exit 1
fi

echo "🦙 Ollama is running. Checking models..."
ollama list

echo "🚀 Starting FastAPI development server..."
echo "📚 API docs will be available at: http://localhost:8001/docs"
echo "🔍 Health check: http://localhost:8001/api/health"
echo ""

# Start development server with reload
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload 