#!/bin/bash

echo "🔍 Quick OCI Backend Diagnostic"
echo "==============================="
echo ""

# Check Docker containers
echo "🐳 Docker Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "❌ Docker command failed"
echo ""

# Check what's listening on port 8001
echo "🔌 Port 8001 Listeners:"
sudo netstat -tlnp | grep :8001 2>/dev/null || sudo ss -tlnp | grep :8001 2>/dev/null || echo "❌ Nothing listening on port 8001"
echo ""

# Test internal connectivity
echo "🏠 Internal API Test:"
echo "Testing localhost:8001/api/health..."
if curl -s -m 5 http://localhost:8001/api/health; then
    echo ""
    echo "✅ Internal API is working"
else
    echo "❌ Internal API failed"
fi
echo ""

# Get instance IPs
echo "📍 Instance IP Information:"
PRIVATE_IP=$(hostname -I | awk '{print $1}' 2>/dev/null)
PUBLIC_IP=$(curl -s -m 5 http://169.254.169.254/opc/v1/instance/ 2>/dev/null | grep -o '"publicIp":"[^"]*' | cut -d'"' -f4)

echo "Private IP: ${PRIVATE_IP:-Not found}"
echo "Public IP: ${PUBLIC_IP:-Not found}"
echo ""

# Test private IP access
if [ -n "$PRIVATE_IP" ]; then
    echo "🔗 Testing Private IP Access:"
    echo "Testing ${PRIVATE_IP}:8001/api/health..."
    if curl -s -m 5 http://${PRIVATE_IP}:8001/api/health; then
        echo ""
        echo "✅ Private IP access works"
    else
        echo "❌ Private IP access failed"
    fi
    echo ""
fi

# Check firewall
echo "🛡️  Firewall Check:"
if command -v ufw >/dev/null && sudo ufw status 2>/dev/null | grep -q "Status: active"; then
    echo "UFW is active:"
    sudo ufw status | grep 8001 || echo "❌ Port 8001 not found in UFW rules"
elif command -v firewall-cmd >/dev/null && sudo firewall-cmd --state 2>/dev/null | grep -q running; then
    echo "Firewalld is running:"
    sudo firewall-cmd --list-ports | grep 8001 || echo "❌ Port 8001 not found in firewalld"
else
    echo "✅ No active firewall detected"
fi
echo ""

echo "🎯 Next Steps:"
echo "1. If containers aren't running: docker-compose up -d"
echo "2. If port not listening: check application logs"
echo "3. If internal test fails: application issue"
echo "4. If internal works but external fails: OCI Security List issue"
