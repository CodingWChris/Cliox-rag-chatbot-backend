#!/bin/bash

echo "🔍 CORS Requirements Test"
echo "=========================="
echo ""
echo "This script will help you determine if you need CORS for your setup."
echo ""

# Test basic API connectivity
echo "1️⃣  Testing basic API connectivity..."
OCI_IP=${1:-"YOUR_OCI_PUBLIC_IP"}
API_URL="http://${OCI_IP}:8001"

echo "   Testing: ${API_URL}/api/health"

if curl -s -f "${API_URL}/api/health" > /dev/null; then
    echo "   ✅ API is accessible from external clients"
else
    echo "   ❌ API is not accessible - check your OCI setup and replace YOUR_OCI_PUBLIC_IP"
    echo ""
    echo "Usage: ./test_cors_requirements.sh YOUR_ACTUAL_OCI_IP"
    exit 1
fi

echo ""
echo "2️⃣  Determining CORS requirements..."
echo ""
echo "❓ What type of application will call your API?"
echo ""
echo "A) 🖥️  Server/Backend Application (Node.js, Python, Java, etc.)"
echo "B) 📱 Mobile Application (iOS, Android, React Native, etc.)"
echo "C) 🔧 CLI Tools/Scripts (curl, Python scripts, etc.)"
echo "D) 🌐 Web Browser Frontend (React, Vue, Angular running in browser)"
echo "E) 🤖 Other Services/APIs (microservices, webhooks, etc.)"
echo ""

read -p "Enter your choice (A/B/C/D/E): " choice

case $choice in
    [Aa]* )
        echo ""
        echo "🎯 RESULT: NO CORS needed"
        echo "Server-to-server calls don't require CORS."
        echo ""
        echo "✅ Keep your current Docker Compose setup (CORS disabled)"
        echo ""
        echo "📝 Example API call:"
        echo "curl -X POST ${API_URL}/api/v1/session/chat \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -H 'Authorization: Bearer your-api-key' \\"
        echo "  -H 'X-Session-ID: test-session' \\"
        echo "  -d '{\"message\": \"Hello from server\"}'"
        ;;
    [Bb]* )
        echo ""
        echo "🎯 RESULT: NO CORS needed"
        echo "Mobile apps don't require CORS."
        echo ""
        echo "✅ Keep your current Docker Compose setup (CORS disabled)"
        echo ""
        echo "📝 Example mobile API call:"
        echo "fetch('${API_URL}/api/v1/session/chat', {"
        echo "  method: 'POST',"
        echo "  headers: {"
        echo "    'Content-Type': 'application/json',"
        echo "    'Authorization': 'Bearer your-api-key',"
        echo "    'X-Session-ID': 'mobile-session'"
        echo "  },"
        echo "  body: JSON.stringify({message: 'Hello from mobile'})"
        echo "})"
        ;;
    [Cc]* )
        echo ""
        echo "🎯 RESULT: NO CORS needed"
        echo "CLI tools and scripts don't require CORS."
        echo ""
        echo "✅ Keep your current Docker Compose setup (CORS disabled)"
        echo ""
        echo "📝 Test your API now:"
        echo "curl ${API_URL}/api/health"
        ;;
    [Dd]* )
        echo ""
        echo "🎯 RESULT: YES, CORS needed!"
        echo "Browser frontends require CORS configuration."
        echo ""
        echo "❗ You need to enable CORS in your Docker Compose"
        echo ""
        echo "📝 Add this to your docker-compose.yml environment:"
        echo "- CORS_ORIGINS=[\"https://your-frontend-domain.com\",\"http://localhost:3000\"]"
        echo ""
        echo "🌐 Common frontend scenarios:"
        echo "  • React app on Vercel: https://your-app.vercel.app"
        echo "  • Local development: http://localhost:3000"
        echo "  • Static site on GitHub Pages: https://username.github.io"
        ;;
    [Ee]* )
        echo ""
        echo "🎯 RESULT: NO CORS needed"
        echo "Service-to-service calls don't require CORS."
        echo ""
        echo "✅ Keep your current Docker Compose setup (CORS disabled)"
        echo ""
        echo "📝 Example service integration:"
        echo "POST ${API_URL}/api/v1/session/chat"
        echo "Headers: Authorization, Content-Type, X-Session-ID"
        ;;
    * )
        echo ""
        echo "❓ Invalid choice. Please run the script again and choose A, B, C, D, or E."
        ;;
esac

echo ""
echo "📚 For more details, check:"
echo "  • API_USAGE_GUIDE.md"
echo "  • API_KEY_AUTHENTICATION_GUIDE.md"
