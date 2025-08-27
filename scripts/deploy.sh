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
    echo "📖 API usage guide: ./API_USAGE_GUIDE.md"
    echo ""
    echo "🔑 For production, set API_KEY environment variable"
    echo "🔧 Test API endpoints:"
    echo "   curl http://localhost:8001/api/health"
    echo "   curl http://localhost:8001/docs"
    echo ""
    echo "📊 Service status:"
    docker-compose ps
    echo ""
    echo "📝 To see logs:"
    echo "   docker-compose logs -f backend"
    echo "   docker-compose logs -f ollama"
else
    echo ""
    echo "❌ Deployment failed!"
    echo "📝 Check logs:"
    echo "   docker-compose logs chatbot-api"
    echo "   docker-compose logs ollama"
    exit 1
fi 