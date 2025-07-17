#!/bin/bash

echo "🚀 Starting RAG Chatbot deployment with Docker..."

# Stop existing services
echo "🛑 Stopping existing services..."
docker-compose down

# Build and start services
echo "🏗️  Building services..."
docker-compose build --no-cache

echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Health check
echo "🩺 Performing health check..."
if curl -f http://localhost:8001/api/health; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 API available at: http://localhost:8001"
    echo "📚 API docs at: http://localhost:8001/docs"
    echo "🦙 Ollama available at: http://localhost:11434"
    echo ""
    echo "📊 Service status:"
    docker-compose ps
    echo ""
    echo "📝 To see logs:"
    echo "   docker-compose logs -f chatbot-api"
    echo "   docker-compose logs -f ollama"
    echo ""
    echo "🔧 To pull Ollama models:"
    echo "   docker-compose exec ollama ollama pull llama2:7b"
else
    echo ""
    echo "❌ Deployment failed!"
    echo "📝 Check logs:"
    echo "   docker-compose logs chatbot-api"
    echo "   docker-compose logs ollama"
    exit 1
fi 