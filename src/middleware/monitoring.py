import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.metrics import metrics

logger = logging.getLogger(__name__)

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to track request metrics and performance"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        
        # Extract session ID
        session_id = request.headers.get("X-Session-ID")
        endpoint = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(f"📥 {method} {endpoint} from {client_ip} (Session: {session_id or 'None'})")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            success = response.status_code < 400
            
            # Record metrics
            metrics.record_request(
                endpoint=endpoint,
                session_id=session_id,
                response_time=response_time,
                success=success
            )
            
            # Log response
            status_icon = "✅" if success else "❌"
            logger.info(f"{status_icon} {method} {endpoint} -> {response.status_code} ({response_time*1000:.1f}ms)")
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time*1000:.1f}ms"
            response.headers["X-Request-ID"] = str(hash(f"{client_ip}-{start_time}"))
            
            return response
            
        except Exception as e:
            # Record error
            response_time = time.time() - start_time
            metrics.record_request(
                endpoint=endpoint,
                session_id=session_id,
                response_time=response_time,
                success=False
            )
            
            logger.error(f"❌ {method} {endpoint} failed: {str(e)} ({response_time*1000:.1f}ms)")
            raise
