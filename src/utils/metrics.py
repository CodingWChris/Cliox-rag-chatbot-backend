import time
import json
import logging
from typing import Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import Request

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = deque(maxlen=1000)  # Keep last 1000 response times
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0, 
            'errors': 0, 
            'total_time': 0.0,
            'avg_time': 0.0
        })
        self.session_stats = defaultdict(lambda: {
            'requests': 0,
            'last_activity': None,
            'total_messages': 0,
            'knowledge_chunks': 0
        })
        self.hourly_stats = defaultdict(lambda: {
            'requests': 0,
            'errors': 0,
            'unique_sessions': set()
        })
        
    def record_request(self, endpoint: str, session_id: str, response_time: float, success: bool = True):
        """Record a request with metrics"""
        current_time = datetime.now()
        hour_key = current_time.strftime("%Y-%m-%d %H:00")
        
        # Overall stats
        self.request_count += 1
        if not success:
            self.error_count += 1
            
        # Response time tracking
        self.response_times.append(response_time)
        
        # Endpoint stats
        endpoint_stat = self.endpoint_stats[endpoint]
        endpoint_stat['count'] += 1
        if not success:
            endpoint_stat['errors'] += 1
        endpoint_stat['total_time'] += response_time
        endpoint_stat['avg_time'] = endpoint_stat['total_time'] / endpoint_stat['count']
        
        # Session stats
        if session_id:
            session_stat = self.session_stats[session_id]
            session_stat['requests'] += 1
            session_stat['last_activity'] = current_time
            if endpoint == '/api/v1/session/chat':
                session_stat['total_messages'] += 1
        
        # Hourly stats
        hourly_stat = self.hourly_stats[hour_key]
        hourly_stat['requests'] += 1
        if not success:
            hourly_stat['errors'] += 1
        if session_id:
            hourly_stat['unique_sessions'].add(session_id)
            
    def record_knowledge_upload(self, session_id: str, chunk_count: int):
        """Record knowledge upload"""
        if session_id:
            self.session_stats[session_id]['knowledge_chunks'] += chunk_count
    
    def get_metrics(self) -> Dict:
        """Get comprehensive metrics"""
        uptime = time.time() - self.start_time
        current_time = datetime.now()
        
        # Calculate average response time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        # Get recent hourly stats (last 24 hours)
        recent_hours = []
        for i in range(24):
            hour = current_time - timedelta(hours=i)
            hour_key = hour.strftime("%Y-%m-%d %H:00")
            stats = self.hourly_stats[hour_key]
            recent_hours.append({
                'hour': hour_key,
                'requests': stats['requests'],
                'errors': stats['errors'],
                'unique_sessions': len(stats['unique_sessions']),
                'error_rate': stats['errors'] / max(stats['requests'], 1) * 100
            })
        
        # Active sessions (activity in last hour)
        cutoff_time = current_time - timedelta(hours=1)
        active_sessions = [
            sid for sid, stats in self.session_stats.items()
            if stats['last_activity'] and stats['last_activity'] > cutoff_time
        ]
        
        return {
            'timestamp': current_time.isoformat(),
            'uptime_seconds': uptime,
            'uptime_human': self._format_uptime(uptime),
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': (self.error_count / max(self.request_count, 1)) * 100,
            'average_response_time_ms': avg_response_time * 1000,
            'active_sessions_last_hour': len(active_sessions),
            'total_sessions': len(self.session_stats),
            'endpoint_stats': dict(self.endpoint_stats),
            'recent_hourly_stats': recent_hours[:12],  # Last 12 hours
            'performance': {
                'requests_per_second': self.request_count / max(uptime, 1),
                'avg_response_time_ms': avg_response_time * 1000,
                'p95_response_time_ms': self._percentile(list(self.response_times), 95) * 1000 if self.response_times else 0,
                'p99_response_time_ms': self._percentile(list(self.response_times), 99) * 1000 if self.response_times else 0
            }
        }
    
    def get_session_details(self, limit: int = 50) -> List[Dict]:
        """Get detailed session information"""
        sessions = []
        for session_id, stats in list(self.session_stats.items())[:limit]:
            sessions.append({
                'session_id': session_id,
                'total_requests': stats['requests'],
                'total_messages': stats['total_messages'],
                'knowledge_chunks': stats['knowledge_chunks'],
                'last_activity': stats['last_activity'].isoformat() if stats['last_activity'] else None,
                'duration_minutes': ((datetime.now() - stats['last_activity']).total_seconds() / 60) if stats['last_activity'] else None
            })
        
        return sorted(sessions, key=lambda x: x['last_activity'] or '', reverse=True)
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{days}d {hours}h {minutes}m"
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

# Global metrics collector instance
metrics = MetricsCollector()
