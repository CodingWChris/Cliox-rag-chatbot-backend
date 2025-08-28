# 📊 Monitoring Guide

## Overview

The RAG Chatbot Backend includes comprehensive monitoring capabilities to track system health, performance metrics, session activity, and service status. This guide covers all monitoring features, endpoints, and dashboard usage.

## 🎯 Quick Start

### Terminal-Based Monitoring (OCI/Production)
When connected to your OCI instance via SSH, use these commands for real-time monitoring:

```bash
# Quick system overview
./scripts/quick_diagnostic.sh

# Monitor application logs in real-time (systemd service)
sudo journalctl -u cliox-rag-backend -f

# Monitor container logs in real-time
docker logs cliox-rag-chatbot-backend-backend-1 -f

# Check container status and performance
docker stats

# Monitor API endpoints
curl -s http://localhost:8001/api/v1/monitoring/metrics | jq .

# Watch system resources
htop
```

#### Container Management Commands
```bash
# List all containers
docker ps -a

# Your specific containers:
# Backend: cliox-rag-chatbot-backend-backend-1
# Ollama: cliox-rag-chatbot-backend-ollama-1

# Follow backend logs
docker logs cliox-rag-chatbot-backend-backend-1 -f --tail=100

# Follow ollama logs
docker logs cliox-rag-chatbot-backend-ollama-1 -f --tail=50

# Check container health
docker inspect cliox-rag-chatbot-backend-backend-1 | jq '.[0].State.Health'

# Restart containers if needed
docker restart cliox-rag-chatbot-backend-backend-1
docker restart cliox-rag-chatbot-backend-ollama-1
```

### Web Dashboard Access (Development)
1. **Web Dashboard**: Visit `http://localhost:8001/api/v1/monitoring/dashboard`
2. **Raw Metrics**: Access `http://localhost:8001/api/v1/monitoring/metrics`
3. **Health Check**: Check `http://localhost:8001/api/v1/monitoring/health/detailed`

### Key Monitoring URLs
```bash
# Main monitoring dashboard (web UI)
GET /api/v1/monitoring/dashboard

# Comprehensive metrics endpoint
GET /api/v1/monitoring/metrics

# Performance-focused metrics
GET /api/v1/monitoring/metrics/performance

# Session metrics with details
GET /api/v1/monitoring/metrics/sessions?limit=50

# Detailed health check
GET /api/v1/monitoring/health/detailed
```

## 📈 Available Metrics

### System Metrics
- **Uptime**: System uptime in human-readable format
- **Total Requests**: Overall request count since startup
- **Error Rate**: Percentage of failed requests
- **Average Response Time**: Mean response time across all endpoints
- **Requests Per Second**: Current request rate

### Performance Metrics
- **P95 Response Time**: 95th percentile response time
- **P99 Response Time**: 99th percentile response time
- **Endpoint Performance**: Per-endpoint response times and error rates
- **Hourly Activity**: Request patterns over the last 24 hours

### Session Metrics
- **Active Sessions**: Sessions with activity in the last hour
- **Total Sessions**: Cumulative session count
- **Session Details**: Individual session statistics including:
  - Total requests per session
  - Message count
  - Knowledge chunks uploaded
  - Last activity timestamp
  - Session duration

### Service Health Metrics
- **Ollama Service**: Connection status and available models
- **Vector Service**: Active collections and vector count
- **Session Service**: Active sessions and cleanup configuration

## 🛠️ Monitoring Endpoints

### 1. Comprehensive Metrics
```http
GET /api/v1/monitoring/metrics
```

**Response Example:**
```json
{
  "timestamp": "2024-08-28T10:30:00.123456",
  "uptime_human": "0d 2h 15m",
  "total_requests": 1250,
  "total_errors": 15,
  "error_rate": 1.2,
  "average_response_time_ms": 245.7,
  "active_sessions_last_hour": 8,
  "total_sessions": 42,
  "services": {
    "ollama": {
      "healthy": true,
      "available_models": ["llama2", "codellama"],
      "model_count": 2
    },
    "vector_service": {
      "model": "all-MiniLM-L6-v2",
      "active_collections": 3,
      "total_vectors": 1500
    },
    "session_service": {
      "active_sessions": 5,
      "cleanup_interval": 3600,
      "max_session_age": 86400
    }
  },
  "endpoint_stats": {
    "/api/v1/session/chat": {
      "count": 450,
      "errors": 5,
      "total_time": 125.5,
      "avg_time": 0.279
    }
  },
  "performance": {
    "requests_per_second": 2.34,
    "avg_response_time_ms": 245.7,
    "p95_response_time_ms": 456.2,
    "p99_response_time_ms": 789.1
  }
}
```

### 2. Performance Metrics
```http
GET /api/v1/monitoring/metrics/performance
```

Focused on performance data with endpoint-specific timing information.

### 3. Session Metrics
```http
GET /api/v1/monitoring/metrics/sessions?limit=50
```

**Query Parameters:**
- `limit`: Number of sessions to return (1-200, default: 50)

### 4. Detailed Health Check
```http
GET /api/v1/monitoring/health/detailed
```

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2024-08-28T10:30:00.123456",
  "uptime": "0d 2h 15m",
  "services": {
    "api": {
      "status": "healthy",
      "total_requests": 1250,
      "error_rate": 1.2,
      "avg_response_time_ms": 245.7
    },
    "ollama": {
      "status": "healthy",
      "connected": true,
      "available_models": ["llama2", "codellama"],
      "model_count": 2
    },
    "sessions": {
      "status": "healthy",
      "active_count": 5,
      "total_created": 42
    }
  }
}
```

## 🖥️ Terminal Monitoring Commands (OCI Production)

### System Performance Monitoring

#### Real-time System Resources
```bash
# Monitor CPU, memory, disk, network
htop

# Alternative system monitor
top

# I/O statistics
iostat -x 1

# Network statistics
netstat -tulpn | grep :8001

# Disk usage monitoring
df -h
du -sh /var/log/* | sort -hr

# Memory usage details
free -h
cat /proc/meminfo
```

#### Docker Container Monitoring
```bash
# Real-time container stats
docker stats

# Container resource usage with formatting
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Check container logs
docker logs cliox-rag-chatbot-backend-backend-1 -f --tail=100

# Container health status
docker ps -a
docker inspect cliox-rag-chatbot-backend-backend-1 | jq '.[0].State'
```

### Application Log Monitoring

#### System Service Logs
```bash
# Follow application logs in real-time
sudo journalctl -u cliox-rag-backend -f

# View recent logs with timestamp
sudo journalctl -u cliox-rag-backend --since "1 hour ago"

# Filter error logs only
sudo journalctl -u cliox-rag-backend -p err

# Export logs to file
sudo journalctl -u cliox-rag-backend --since "24 hours ago" > /tmp/app_logs.txt
```

#### Docker Logs
```bash
# Follow container logs
docker logs cliox-rag-chatbot-backend-backend-1 -f

# View logs with timestamps
docker logs cliox-rag-chatbot-backend-backend-1 -f -t

# Last 100 lines of logs
docker logs cliox-rag-chatbot-backend-backend-1 --tail=100

# Filter logs by time
docker logs cliox-rag-chatbot-backend-backend-1 --since="2024-08-28T10:00:00"
```

### API Monitoring via Terminal

#### Health and Metrics Endpoints
```bash
# Quick health check
curl -s http://localhost:8001/api/v1/health | jq .

# Detailed health with formatting
curl -s http://localhost:8001/api/v1/monitoring/health/detailed | jq .

# System metrics overview
curl -s http://localhost:8001/api/v1/monitoring/metrics | jq '{
  uptime: .uptime_human,
  requests: .total_requests,
  errors: .total_errors,
  error_rate: .error_rate,
  response_time: .average_response_time_ms,
  active_sessions: .active_sessions_last_hour
}'

# Performance metrics
curl -s http://localhost:8001/api/v1/monitoring/metrics/performance | jq .performance

# Session information
curl -s "http://localhost:8001/api/v1/monitoring/metrics/sessions?limit=10" | jq .
```

#### Continuous Monitoring Scripts
```bash
# Create an error-only monitoring script
cat > /tmp/error_only_monitor.sh << 'EOF'
#!/bin/bash

echo "🚨 RAG Chatbot Error Monitor"
echo "================================"
echo "Monitoring for actual errors only..."
echo "Press Ctrl+C to stop"
echo

# Function to check for errors and display them
check_errors() {
    echo "[$(date '+%H:%M:%S')] Checking for new errors..."
    
    # Check for ERROR level logs
    ERRORS=$(docker logs cliox-rag-chatbot-backend-backend-1 --since="1m" | grep " - ERROR - ")
    if [ ! -z "$ERRORS" ]; then
        echo "🔥 ERROR LEVEL LOGS:"
        echo "$ERRORS"
        echo "---"
    fi
    
    # Check for failed requests
    FAILED_REQUESTS=$(docker logs cliox-rag-chatbot-backend-backend-1 --since="1m" | grep "❌")
    if [ ! -z "$FAILED_REQUESTS" ]; then
        echo "💥 FAILED REQUESTS:"
        echo "$FAILED_REQUESTS"
        echo "---"
    fi
    
    # Check for HTTP errors
    HTTP_ERRORS=$(docker logs cliox-rag-chatbot-backend-backend-1 --since="1m" | grep -E " -> [4-5][0-9][0-9] ")
    if [ ! -z "$HTTP_ERRORS" ]; then
        echo "🌐 HTTP ERRORS:"
        echo "$HTTP_ERRORS"
        echo "---"
    fi
    
    # If no errors found
    if [ -z "$ERRORS" ] && [ -z "$FAILED_REQUESTS" ] && [ -z "$HTTP_ERRORS" ]; then
        echo "✅ No errors detected in the last minute"
    fi
    
    echo ""
}

# Run initial check for last 10 minutes
echo "📊 Checking for errors in the last 10 minutes..."
docker logs cliox-rag-chatbot-backend-backend-1 --since="10m" | grep -E "( - ERROR - |❌| -> [4-5][0-9][0-9] )" | tail -10

echo ""
echo "🔄 Now monitoring for new errors every 30 seconds..."
echo ""

# Monitor in real-time
while true; do
    check_errors
    sleep 30
done
EOF

chmod +x /tmp/error_only_monitor.sh
/tmp/error_only_monitor.sh
```
```bash
# Create a monitoring script
cat > /tmp/monitor_app.sh << 'EOF'
#!/bin/bash
while true; do
  clear
  echo "=== RAG Chatbot Backend Monitoring ==="
  echo "Timestamp: $(date)"
  echo
  
  # System resources
  echo "=== System Resources ==="
  free -h | head -2
  df -h / | tail -1
  echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
  echo
  
  # Docker stats
  echo "=== Container Status ==="
  docker stats --no-stream --format "CPU: {{.CPUPerc}} | Memory: {{.MemUsage}} | Net I/O: {{.NetIO}}"
  echo
  
  # API health
  echo "=== API Health ==="
  curl -s http://localhost:8001/api/v1/monitoring/metrics | jq -r '
    "Uptime: " + .uptime_human + 
    " | Requests: " + (.total_requests | tostring) + 
    " | Error Rate: " + (.error_rate | tostring) + "%" +
    " | Avg Response: " + (.average_response_time_ms | tostring) + "ms"
  ' 2>/dev/null || echo "API not responding"
  
  echo
  echo "Press Ctrl+C to stop monitoring..."
  sleep 5
done
EOF

chmod +x /tmp/monitor_app.sh
/tmp/monitor_app.sh
```

### Log Analysis Commands

## 🚨 Error-Only Monitoring

### Real-time Error Monitoring
```bash
# Follow only actual ERROR level logs in real-time
docker logs cliox-rag-chatbot-backend-backend-1 -f | grep " - ERROR - "

# Monitor for failed requests (❌ symbol)
docker logs cliox-rag-chatbot-backend-backend-1 -f | grep "❌"

# Watch for HTTP error codes in real-time
docker logs cliox-rag-chatbot-backend-backend-1 -f | grep -E " -> [4-5][0-9][0-9] "

# Monitor for exceptions and critical errors
docker logs cliox-rag-chatbot-backend-backend-1 -f | grep -E "(ERROR|CRITICAL|Exception|Traceback)"
```

### Error Detection Commands
```bash
# Check if there are any actual errors (returns empty if no errors)
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep " - ERROR - " | wc -l

# Get last 10 actual errors
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep " - ERROR - " | tail -10

# Find failed HTTP requests
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep " -> [4-5][0-9][0-9] "

# Look for Python exceptions
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -B 2 -A 5 "Exception"

# Check for Ollama connection issues
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -i "ollama" | grep -E "(error|failed|timeout)"
```

### Quick Error Check
```bash
# One-liner to check if there are any recent errors
echo "Checking for errors in last 1000 log lines..."
ERROR_COUNT=$(docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -E "( - ERROR - |❌| -> [4-5][0-9][0-9] )" | wc -l)
if [ $ERROR_COUNT -eq 0 ]; then
    echo "✅ No errors found in recent logs"
else
    echo "🚨 Found $ERROR_COUNT errors in recent logs:"
    docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -E "( - ERROR - |❌| -> [4-5][0-9][0-9] )" | tail -5
fi
```

### Error Breakdown Analysis
```bash
# Get detailed breakdown of errors by endpoint
curl -s http://localhost:8001/api/v1/monitoring/metrics | jq '.endpoint_stats | to_entries[] | select(.value.errors > 0) | {endpoint: .key, errors: .value.errors, total_requests: .value.count, error_rate: (.value.errors / .value.count * 100 | floor)}' 

# Create a comprehensive error analysis report
cat > /tmp/error_analysis.sh << 'EOF'
#!/bin/bash

echo "🔍 DETAILED ERROR ANALYSIS"
echo "=========================="
echo "Generated: $(date)"
echo

# Get total metrics
METRICS=$(curl -s http://localhost:8001/api/v1/monitoring/metrics)
TOTAL_ERRORS=$(echo "$METRICS" | jq -r '.total_errors')
TOTAL_REQUESTS=$(echo "$METRICS" | jq -r '.total_requests')
ERROR_RATE=$(echo "$METRICS" | jq -r '.error_rate')

echo "📊 Overall Statistics:"
echo "  Total Errors: $TOTAL_ERRORS"
echo "  Total Requests: $TOTAL_REQUESTS"
echo "  Overall Error Rate: ${ERROR_RATE}%"
echo

echo "🎯 Error Breakdown by Endpoint:"
echo "$METRICS" | jq -r '.endpoint_stats | to_entries[] | select(.value.errors > 0) | "  " + .key + ": " + (.value.errors | tostring) + " errors (" + ((.value.errors / .value.count * 100) | tostring | .[0:5]) + "% of " + (.value.count | tostring) + " requests)"'
echo

echo "🔍 Error Type Analysis:"
# Known error patterns
KNOWLEDGE_ERRORS=$(echo "$METRICS" | jq '.endpoint_stats["/api/v1/session/knowledge/upload"].errors // 0')
FAVICON_ERRORS=$(echo "$METRICS" | jq '.endpoint_stats["/favicon.ico"].errors // 0')
UNKNOWN_ENDPOINT_ERRORS=$(echo "$METRICS" | jq '.endpoint_stats | to_entries[] | select(.key | test("^/(?!api/).*")) | .value.errors' | jq -s 'add // 0')

echo "  📤 Knowledge Upload Errors: $KNOWLEDGE_ERRORS (likely file upload issues)"
echo "  🌐 Favicon/Static File Errors: $FAVICON_ERRORS (missing static files - normal)"
echo "  🔗 Unknown Endpoint Errors: $UNKNOWN_ENDPOINT_ERRORS (bots/crawlers hitting non-existent endpoints)"
echo

echo "💡 Error Interpretation:"
if [ "$KNOWLEDGE_ERRORS" -gt 0 ]; then
    echo "  ⚠️  Knowledge upload errors suggest file processing issues"
fi

if [ "$FAVICON_ERRORS" -gt 0 ]; then
    echo "  ℹ️  Favicon errors are normal - browsers requesting /favicon.ico"
fi

if [ "$UNKNOWN_ENDPOINT_ERRORS" -gt 0 ]; then
    echo "  🤖 Unknown endpoint errors are likely bots/crawlers - not user issues"
fi

echo
echo "🏥 Health Assessment:"
REAL_API_ERRORS=$(echo "$METRICS" | jq '.endpoint_stats | to_entries[] | select(.key | startswith("/api/")) | .value.errors' | jq -s 'add // 0')
if [ "$REAL_API_ERRORS" -eq 0 ]; then
    echo "  ✅ No actual API errors - system is healthy!"
    echo "  ✅ All errors are from non-API endpoints (favicon, unknown paths)"
else
    echo "  ⚠️  Found $REAL_API_ERRORS actual API errors that need attention"
fi

EOF

chmod +x /tmp/error_analysis.sh
/tmp/error_analysis.sh
```

#### Error Analysis
```bash
# Look for actual ERROR level logs (not just the word "error")
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep " - ERROR - "

# Find CRITICAL level logs
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep " - CRITICAL - "

# Look for failed requests (❌ symbol)
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep "❌"

# Find HTTP error status codes (4xx, 5xx)
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -E " -> [4-5][0-9][0-9] "

# Look for Python exceptions and tracebacks
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -A 5 "Traceback"

# Find connection errors or timeouts
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -i -E "(connection.*failed|timeout|refused|unreachable)"

# Look for specific error patterns in your app
docker logs cliox-rag-chatbot-backend-backend-1 --tail=1000 | grep -E "(Exception|Error:|Failed to|Unable to)"

# Check for specific error types based on your endpoint data
# 1. Knowledge upload errors (might be real issues)
curl -s http://localhost:8001/api/v1/monitoring/metrics | jq '.endpoint_stats["/api/v1/session/knowledge/upload"]'

# 2. Favicon errors (normal - browsers requesting missing favicon)
curl -s http://localhost:8001/api/v1/monitoring/metrics | jq '.endpoint_stats["/favicon.ico"]'

# 3. Bot/crawler errors (normal - bots hitting non-existent endpoints)
curl -s http://localhost:8001/api/v1/monitoring/metrics | jq '.endpoint_stats | to_entries[] | select(.key | test("^/(?!api/).*"))'

# 4. Find logs for knowledge upload failures specifically
docker logs cliox-rag-chatbot-backend-backend-1 --tail=2000 | grep "knowledge/upload" | grep -E "❌|ERROR|40[0-9]|50[0-9]"
```
```

#### Traffic Analysis
```bash
# Request patterns from logs
sudo journalctl -u cliox-rag-backend --since "1 hour ago" | grep -oP 'GET|POST|PUT|DELETE' | sort | uniq -c

# Session activity
docker logs cliox-rag-chatbot-backend-backend-1 2>&1 | grep "Session:" | tail -10

# Most requested endpoints
docker logs cliox-rag-chatbot-backend-backend-1 2>&1 | grep -oP '/api/[^"]*' | sort | uniq -c | sort -nr | head -10
```

### Performance Monitoring

#### Response Time Monitoring
```bash
# Monitor API response times continuously
watch -n 5 "curl -w '@/dev/stdin' -o /dev/null -s http://localhost:8001/api/v1/health <<< 'Response Time: %{time_total}s'"

# Benchmark specific endpoints
ab -n 100 -c 10 http://localhost:8001/api/v1/health

# Monitor with detailed timing
curl -w "@-" -o /dev/null -s http://localhost:8001/api/v1/monitoring/metrics <<< '
     namelookup:  %{time_namelookup}s
        connect:  %{time_connect}s
     appconnect:  %{time_appconnect}s
    pretransfer:  %{time_pretransfer}s
       redirect:  %{time_redirect}s
  starttransfer:  %{time_starttransfer}s
          total:  %{time_total}s
'
```

### Automated Monitoring Setup

#### Cron Jobs for Regular Checks
```bash
# Add to crontab (crontab -e)
# Check health every 5 minutes and log to file
*/5 * * * * curl -s http://localhost:8001/api/v1/monitoring/health/detailed | jq -r '"[" + now + "] Status: " + .status + " | Uptime: " + .uptime' >> /var/log/health_checks.log

# Daily metrics summary
0 0 * * * curl -s http://localhost:8001/api/v1/monitoring/metrics | jq . > /var/log/daily_metrics_$(date +\%Y\%m\%d).json
```

#### Alert Scripts
```bash
# Create alert script for high error rates
cat > /tmp/alert_check.sh << 'EOF'
#!/bin/bash
ERROR_THRESHOLD=10

# Get current error rate
ERROR_RATE=$(curl -s http://localhost:8001/api/v1/monitoring/metrics | jq -r '.error_rate // 0')

if (( $(echo "$ERROR_RATE > $ERROR_THRESHOLD" | bc -l) )); then
    echo "[ALERT] High error rate detected: ${ERROR_RATE}%" | logger -t rag-chatbot-alert
    # Add notification logic here (email, slack, etc.)
fi
EOF

chmod +x /tmp/alert_check.sh
```

### Resource Monitoring

#### Memory and CPU Tracking
```bash
# Track application memory usage
ps aux | grep python | grep -v grep

# Monitor file descriptors
lsof -p $(pgrep -f "python.*main.py") | wc -l

# Track network connections
ss -tuln | grep :8001

# Monitor disk I/O for the application
iotop -p $(pgrep -f "python.*main.py")
```

#### Database/Vector Store Monitoring
```bash
# Check vector database files
find . -name "*.db" -o -name "*.index" | xargs ls -lh

# Monitor embeddings directory size
du -sh ./embeddings/ 2>/dev/null || echo "No embeddings directory found"
```

## 🖥️ Monitoring Dashboard

### Features
- **Real-time Metrics**: Auto-refreshes every 30 seconds
- **System Overview**: Quick status indicators for all services
- **Performance Charts**: Visual representation of response times and request rates
- **Service Health**: Status indicators for Ollama, Vector Service, and Sessions
- **Historical Data**: Hourly request patterns and trends

### Dashboard Sections

#### Status Cards
- **System Status**: Overall health (healthy/degraded/unhealthy)
- **Request Volume**: Total requests and current rate
- **Error Monitoring**: Error count and percentage
- **Session Activity**: Active and total sessions
- **Response Performance**: Average response times
- **Service Status**: Individual service health

#### Interactive Features
- **Manual Refresh**: Click "🔄 Refresh Data" button
- **Auto-refresh**: Updates every 30 seconds automatically
- **Responsive Design**: Works on desktop and mobile devices

## 🔧 Monitoring Configuration

### Middleware Setup
The monitoring system uses `MonitoringMiddleware` that automatically:
- Tracks all HTTP requests
- Measures response times
- Records success/failure rates
- Associates requests with sessions
- Logs detailed request information

### Metrics Collection
The `MetricsCollector` class provides:
- **Request Tracking**: Per-endpoint statistics
- **Session Management**: User session activity
- **Performance Monitoring**: Response time percentiles
- **Historical Data**: Hourly request patterns
- **Memory Efficiency**: Uses rotating deques for recent data

### Automatic Features
- **Session Association**: Links requests to sessions via `X-Session-ID` header
- **Performance Headers**: Adds `X-Response-Time` and `X-Request-ID` to responses
- **Error Tracking**: Automatically records failed requests
- **Activity Patterns**: Tracks hourly usage patterns

## 🚨 Health Check Integration

### Service Health Checks
The system monitors:
1. **Ollama Service**: Connection and model availability
2. **Vector Service**: Collection status and vector counts
3. **Session Service**: Active session management
4. **API Performance**: Overall request success rates

### Health Status Levels
- **Healthy**: All services operational, low error rate (<20%)
- **Degraded**: Some issues detected, moderate error rate (20-50%)
- **Unhealthy**: Critical issues, high error rate (>50%) or service failures

## 📊 Using the Metrics

### For Operations
- Monitor the dashboard for real-time system health
- Set up alerts based on error rates or response times
- Track session activity patterns
- Monitor Ollama model availability

### For Development
- Use performance metrics to optimize endpoints
- Analyze session patterns for user experience improvements
- Monitor memory usage through vector service metrics
- Track error patterns for debugging

### For Scaling
- Monitor requests per second for capacity planning
- Track session counts for resource allocation
- Analyze hourly patterns for infrastructure scaling
- Use response time percentiles for SLA monitoring

## 🔍 Troubleshooting

### Common Issues

#### Dashboard Not Loading
1. Check if the backend is running on the expected port
2. Verify network connectivity to the monitoring endpoints
3. Check browser console for JavaScript errors

#### Missing Metrics
1. Ensure the monitoring middleware is properly configured
2. Check if requests are being made with proper headers
3. Verify the metrics collector is recording data

#### Service Health Issues
1. **Ollama Unhealthy**: Check Ollama service connectivity and model availability
2. **High Error Rate**: Review application logs for error patterns
3. **Slow Response Times**: Analyze endpoint performance metrics

### Debug Commands
```bash
# Test metrics endpoint
curl http://localhost:8001/api/v1/monitoring/metrics

# Check health status
curl http://localhost:8001/api/v1/monitoring/health/detailed

# Monitor specific session
curl "http://localhost:8001/api/v1/monitoring/metrics/sessions?limit=10"

# SSH into OCI and monitor
ssh your-oci-instance
sudo systemctl status cliox-rag-backend
docker logs cliox-rag-chatbot-backend-backend-1 -f
```

### OCI-Specific Troubleshooting
```bash
# Check if service is running
sudo systemctl status cliox-rag-backend

# Restart the service
sudo systemctl restart cliox-rag-backend

# Check docker container status
docker ps -a | grep cliox

# View system resources
free -h && df -h

# Check network connectivity
curl -I http://localhost:8001/api/v1/health

# Monitor real-time logs
tail -f /var/log/syslog | grep cliox
```

## 🔧 OCI Production Monitoring Setup

### Initial Setup Commands
```bash
# Install monitoring tools if not present
sudo apt update
sudo apt install htop iotop jq curl apache2-utils -y

# Create monitoring directories
sudo mkdir -p /var/log/monitoring
sudo chown $(whoami):$(whoami) /var/log/monitoring

# Set up log rotation
sudo tee /etc/logrotate.d/rag-chatbot << EOF
/var/log/monitoring/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $(whoami) $(whoami)
}
EOF
```

### Production Monitoring Script
Create a comprehensive monitoring script:
```bash
cat > ~/monitor_production.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/monitoring/production_monitor.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEM=85
ALERT_THRESHOLD_ERROR_RATE=15

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_system_resources() {
    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    
    # Memory usage
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    # Disk usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    log_message "SYSTEM: CPU=${CPU_USAGE}% MEM=${MEM_USAGE}% DISK=${DISK_USAGE}%"
    
    # Check thresholds
    if (( $(echo "$CPU_USAGE > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        log_message "ALERT: High CPU usage: ${CPU_USAGE}%"
    fi
    
    if [ "$MEM_USAGE" -gt "$ALERT_THRESHOLD_MEM" ]; then
        log_message "ALERT: High memory usage: ${MEM_USAGE}%"
    fi
}

check_application_health() {
    # Check if API is responding
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health)
    
    if [ "$HTTP_CODE" = "200" ]; then
        # Get detailed metrics
        METRICS=$(curl -s http://localhost:8001/api/v1/monitoring/metrics)
        ERROR_RATE=$(echo "$METRICS" | jq -r '.error_rate // 0')
        UPTIME=$(echo "$METRICS" | jq -r '.uptime_human // "unknown"')
        TOTAL_REQUESTS=$(echo "$METRICS" | jq -r '.total_requests // 0')
        
        log_message "APP: Status=OK ErrorRate=${ERROR_RATE}% Uptime=${UPTIME} Requests=${TOTAL_REQUESTS}"
        
        # Check error rate threshold
        if (( $(echo "$ERROR_RATE > $ALERT_THRESHOLD_ERROR_RATE" | bc -l) )); then
            log_message "ALERT: High error rate: ${ERROR_RATE}%"
        fi
    else
        log_message "ALERT: API not responding (HTTP: $HTTP_CODE)"
    fi
}

check_docker_containers() {
    CONTAINER_STATUS=$(docker ps --format "{{.Names}}: {{.Status}}" | grep cliox-rag-chatbot-backend)
    log_message "DOCKER: $CONTAINER_STATUS"
}

# Main monitoring loop
main() {
    log_message "=== Starting Production Monitor ==="
    
    while true; do
        check_system_resources
        check_application_health
        check_docker_containers
        
        sleep 60  # Check every minute
    done
}

# Handle script termination
trap 'log_message "=== Monitor Stopped ==="; exit 0' INT TERM

main
EOF

chmod +x ~/monitor_production.sh
```

### Service Monitoring Commands
```bash
# Create systemd service for monitoring
sudo tee /etc/systemd/system/rag-monitor.service << EOF
[Unit]
Description=RAG Chatbot Production Monitor
After=docker.service

[Service]
Type=simple
User=$(whoami)
ExecStart=/home/$(whoami)/monitor_production.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start monitoring service
sudo systemctl daemon-reload
sudo systemctl enable rag-monitor.service
sudo systemctl start rag-monitor.service
```

## 📋 Best Practices

### Monitoring Strategy
1. **Regular Monitoring**: Check dashboard daily for trends
2. **Alert Thresholds**: Set alerts for error rates >10% and response times >1s
3. **Capacity Planning**: Monitor request patterns for scaling decisions
4. **Performance Optimization**: Use P95/P99 metrics for optimization targets

### Data Retention
- Response times: Last 1000 requests in memory
- Hourly stats: Last 24 hours
- Session data: Until cleanup (configurable)
- Endpoint stats: Cumulative since startup

### Integration Tips
- Include `X-Session-ID` header in requests for session tracking
- Monitor both individual endpoint performance and overall system health
- Use the JSON endpoints for integration with external monitoring tools
- Set up automated health checks using the `/health/detailed` endpoint

## 🔗 Related Documentation
- [API Usage Guide](API_USAGE_GUIDE.md) - For API endpoint details
- [Frontend API Guide](FRONTEND_API_GUIDE.md) - For client integration
- [OCI Dashboard Access](OCI_DASHBOARD_ACCESS.md) - For cloud monitoring

---

*Last updated: August 28, 2025*