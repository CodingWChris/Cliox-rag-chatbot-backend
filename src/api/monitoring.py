import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import HTMLResponse
from ..utils.metrics import metrics
from ..services.ollama_service import ollama_service
from ..services.session_service import session_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """Get comprehensive application metrics"""
    try:
        app_metrics = metrics.get_metrics()
        
        # Add service-specific metrics
        ollama_healthy = await ollama_service.health_check()
        available_models = await ollama_service.list_models()
        
        # Get vector service info
        from ..services.vector_service import vector_service
        vector_service_info = {
            "model": "all-MiniLM-L6-v2",
            "active_collections": len(vector_service.session_collections),
            "total_vectors": sum(
                len(collection) if hasattr(collection, '__len__') else 0 
                for collection in vector_service.session_collections.values()
            ) if vector_service.session_collections else 0
        }
        
        return {
            **app_metrics,
            "services": {
                "ollama": {
                    "healthy": ollama_healthy,
                    "available_models": available_models,
                    "model_count": len(available_models)
                },
                "vector_service": vector_service_info,
                "session_service": {
                    "active_sessions": session_service.get_session_count(),
                    "cleanup_interval": session_service.cleanup_interval,
                    "max_session_age": session_service.max_session_age
                }
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Metrics collection error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to collect metrics", "message": str(e)}
        )

@router.get("/metrics/sessions")
async def get_session_metrics(limit: int = Query(50, ge=1, le=200)):
    """Get detailed session metrics"""
    try:
        return {
            "sessions": metrics.get_session_details(limit=limit),
            "summary": {
                "total_sessions": len(metrics.session_stats),
                "active_sessions": session_service.get_session_count()
            }
        }
    except Exception as e:
        logger.error(f"❌ Session metrics error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to collect session metrics", "message": str(e)}
        )

@router.get("/metrics/performance")
async def get_performance_metrics():
    """Get performance-focused metrics"""
    try:
        app_metrics = metrics.get_metrics()
        
        return {
            "timestamp": app_metrics["timestamp"],
            "uptime": app_metrics["uptime_human"],
            "performance": app_metrics["performance"],
            "error_rate": app_metrics["error_rate"],
            "endpoint_performance": {
                endpoint: {
                    "avg_response_time_ms": stats["avg_time"] * 1000,
                    "total_requests": stats["count"],
                    "error_rate": (stats["errors"] / max(stats["count"], 1)) * 100,
                    "requests_per_second": stats["count"] / max(app_metrics["uptime_seconds"], 1)
                }
                for endpoint, stats in app_metrics["endpoint_stats"].items()
            },
            "recent_activity": app_metrics["recent_hourly_stats"][:6]  # Last 6 hours
        }
    except Exception as e:
        logger.error(f"❌ Performance metrics error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to collect performance metrics", "message": str(e)}
        )

@router.get("/health/detailed")
async def detailed_health_check():
    """Enhanced health check with detailed service status"""
    try:
        # Basic health info
        base_metrics = metrics.get_metrics()
        
        # Service health checks
        ollama_healthy = await ollama_service.health_check()
        available_models = await ollama_service.list_models()
        
        # Determine overall health
        is_healthy = (
            ollama_healthy and
            len(available_models) > 0 and
            base_metrics["error_rate"] < 50  # Less than 50% error rate
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": base_metrics["timestamp"],
            "uptime": base_metrics["uptime_human"],
            "services": {
                "api": {
                    "status": "healthy" if base_metrics["error_rate"] < 20 else "degraded",
                    "total_requests": base_metrics["total_requests"],
                    "error_rate": base_metrics["error_rate"],
                    "avg_response_time_ms": base_metrics["average_response_time_ms"]
                },
                "ollama": {
                    "status": "healthy" if ollama_healthy else "unhealthy",
                    "connected": ollama_healthy,
                    "available_models": available_models,
                    "model_count": len(available_models)
                },
                "sessions": {
                    "status": "healthy",
                    "active_count": session_service.get_session_count(),
                    "total_created": len(metrics.session_stats)
                }
            },
            "performance": {
                "requests_per_second": base_metrics["performance"]["requests_per_second"],
                "avg_response_time_ms": base_metrics["performance"]["avg_response_time_ms"],
                "p95_response_time_ms": base_metrics["performance"]["p95_response_time_ms"]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Detailed health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": base_metrics.get("timestamp", "unknown"),
            "error": str(e)
        }

@router.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard():
    """Serve the monitoring dashboard HTML"""
    try:
        # Inline dashboard HTML with auto-configuration
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Chatbot Backend - Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            color: #666;
            margin-bottom: 5px;
        }
        .status-healthy { color: #28a745; }
        .status-degraded { color: #ffc107; }
        .status-unhealthy { color: #dc3545; }
        .refresh-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .refresh-btn:hover {
            background: #0056b3;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 RAG Chatbot Backend Monitoring</h1>
            <p>Real-time monitoring dashboard for your RAG chatbot backend service</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
            <span id="lastUpdate" style="margin-left: 20px; color: #666;"></span>
        </div>

        <div id="loading" class="loading">
            <h3>Loading metrics...</h3>
        </div>

        <div id="dashboard" style="display: none;">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">System Status</div>
                    <div class="metric-value" id="systemStatus">-</div>
                    <div id="uptime">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Requests</div>
                    <div class="metric-value" id="totalRequests">-</div>
                    <div id="requestsPerSecond">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Error Rate</div>
                    <div class="metric-value" id="errorRate">-</div>
                    <div id="totalErrors">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Active Sessions</div>
                    <div class="metric-value" id="activeSessions">-</div>
                    <div id="totalSessions">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value" id="avgResponseTime">-</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Ollama Status</div>
                    <div class="metric-value" id="ollamaStatus">-</div>
                    <div id="ollamaModels">-</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Automatically use the current host as API base
        const API_BASE = window.location.origin;
        console.log('Using API Base:', API_BASE);

        async function fetchMetrics() {
            try {
                const response = await fetch(`${API_BASE}/api/v1/monitoring/metrics`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return await response.json();
            } catch (error) {
                console.error('Failed to fetch metrics:', error);
                return null;
            }
        }

        function updateMetrics(data) {
            if (!data) return;

            // System Status
            const status = data.services?.ollama?.healthy ? 'healthy' : 'degraded';
            document.getElementById('systemStatus').textContent = status.toUpperCase();
            document.getElementById('systemStatus').className = `metric-value status-${status}`;
            document.getElementById('uptime').textContent = `Uptime: ${data.uptime_human}`;

            // Request Stats
            document.getElementById('totalRequests').textContent = data.total_requests.toLocaleString();
            document.getElementById('requestsPerSecond').textContent = `${data.performance.requests_per_second.toFixed(2)} req/s`;

            // Error Rate
            document.getElementById('errorRate').textContent = `${data.error_rate.toFixed(1)}%`;
            document.getElementById('totalErrors').textContent = `${data.total_errors} total errors`;

            // Sessions
            document.getElementById('activeSessions').textContent = data.active_sessions_last_hour;
            document.getElementById('totalSessions').textContent = `${data.total_sessions} total sessions`;

            // Performance
            document.getElementById('avgResponseTime').textContent = `${data.performance.avg_response_time_ms.toFixed(0)}ms`;

            // Services
            const ollamaHealthy = data.services?.ollama?.healthy;
            document.getElementById('ollamaStatus').textContent = ollamaHealthy ? 'HEALTHY' : 'UNHEALTHY';
            document.getElementById('ollamaStatus').className = `metric-value status-${ollamaHealthy ? 'healthy' : 'unhealthy'}`;
            document.getElementById('ollamaModels').textContent = `${data.services?.ollama?.model_count || 0} models available`;

            // Update timestamp
            document.getElementById('lastUpdate').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
        }

        async function refreshData() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('dashboard').style.display = 'none';
            
            const data = await fetchMetrics();
            if (data) {
                updateMetrics(data);
                document.getElementById('loading').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
            } else {
                document.getElementById('loading').innerHTML = '<h3 style="color: red;">❌ Failed to load metrics</h3>';
            }
        }

        // Initial load
        refreshData();

        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
            
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return HTMLResponse(content=f"<h1>Error loading dashboard: {str(e)}</h1>", status_code=500)
