"""
Middleware for MetaApi Flask application.
Provides request/response logging, rate limiting, and error handling.
"""

import time
import json
from functools import wraps
from typing import Dict, Any, Optional
from flask import request, jsonify, g
from werkzeug.exceptions import TooManyRequests
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

from config.config_manager import config_manager
from core.exceptions import RateLimitError, MetaApiError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 300, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = defaultdict(deque)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limits."""
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old requests
        client_requests = self.requests[client_id]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        # Check if within limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True
    
    def get_reset_time(self, client_id: str) -> datetime:
        """Get time when rate limit resets for client."""
        client_requests = self.requests[client_id]
        if not client_requests:
            return datetime.now()
        
        return client_requests[0] + timedelta(minutes=self.window_minutes)


# Global rate limiter instance
rate_limiter = RateLimiter()


def init_middleware(app):
    """Initialize middleware for Flask app."""
    
    @app.before_request
    def before_request():
        """Execute before each request."""
        g.start_time = time.time()
        g.request_id = f"{int(time.time())}-{id(request)}"
        
        # Log incoming request
        logger.info(f"[{g.request_id}] {request.method} {request.path} from {request.remote_addr}")
        
        if request.is_json and request.get_json():
            # Log request data (without sensitive info)
            data = request.get_json()
            safe_data = {k: v if k not in ['password', 'token', 'secret'] else '***' for k, v in data.items()}
            logger.debug(f"[{g.request_id}] Request data: {safe_data}")
    
    @app.after_request
    def after_request(response):
        """Execute after each request."""
        duration = round((time.time() - g.start_time) * 1000, 2)
        
        logger.info(f"[{g.request_id}] Response: {response.status_code} in {duration}ms")
        
        # Add response headers
        response.headers['X-Request-ID'] = g.request_id
        response.headers['X-Response-Time'] = f"{duration}ms"
        response.headers['X-API-Version'] = "2.0"
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Global exception handler."""
        request_id = getattr(g, 'request_id', 'unknown')
        
        if isinstance(e, MetaApiError):
            logger.error(f"[{request_id}] MetaApi error: {e}")
            return jsonify(e.to_dict()), 400
        elif isinstance(e, TooManyRequests):
            logger.warning(f"[{request_id}] Rate limit exceeded")
            return jsonify({
                "error": "RateLimitError",
                "message": "Too many requests",
                "status": "NOTOK"
            }), 429
        else:
            logger.exception(f"[{request_id}] Unexpected error: {e}")
            return jsonify({
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "status": "NOTOK"
            }), 500


def rate_limit(max_requests: Optional[int] = None):
    """Rate limiting decorator."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = config_manager.get_config()
            limit = max_requests or config.rate_limit_per_minute
            
            # Use IP address as client identifier
            client_id = request.remote_addr
            
            # Check rate limit
            if not rate_limiter.is_allowed(client_id):
                reset_time = rate_limiter.get_reset_time(client_id)
                logger.warning(f"Rate limit exceeded for {client_id}")
                
                return jsonify({
                    "error": "RateLimitError",
                    "message": f"Rate limit exceeded. Max {limit} requests per minute.",
                    "status": "NOTOK",
                    "retry_after": reset_time.isoformat()
                }), 429
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_request_response(include_request_data: bool = True, include_response_data: bool = False):
    """Decorator for detailed request/response logging."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request_id = getattr(g, 'request_id', 'unknown')
            
            # Log request details
            if include_request_data and request.is_json:
                data = request.get_json()
                if data:
                    # Sanitize sensitive data
                    safe_data = {
                        k: v if k not in ['password', 'token', 'secret_key'] else '***' 
                        for k, v in data.items()
                    }
                    logger.debug(f"[{request_id}] Request payload: {json.dumps(safe_data, indent=2)}")
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log response details
                if include_response_data:
                    if hasattr(result, 'get_json'):
                        response_data = result.get_json()
                        logger.debug(f"[{request_id}] Response payload: {json.dumps(response_data, indent=2)}")
                
                return result
                
            except Exception as e:
                logger.error(f"[{request_id}] Function {func.__name__} failed: {e}")
                raise
        
        return wrapper
    return decorator


def require_content_type(content_type: str = "application/json"):
    """Decorator to require specific content type."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.content_type != content_type:
                return jsonify({
                    "error": "UnsupportedMediaType",
                    "message": f"Content-Type must be {content_type}",
                    "status": "NOTOK"
                }), 415
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def timeout_handler(timeout_seconds: Optional[int] = None):
    """Decorator to handle request timeouts."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = config_manager.get_config()
            timeout = timeout_seconds or config.request_timeout
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Check if execution time exceeded timeout
                execution_time = time.time() - start_time
                if execution_time > timeout:
                    logger.warning(f"Request took {execution_time:.2f}s (timeout: {timeout}s)")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                if execution_time > timeout:
                    logger.error(f"Request timed out after {execution_time:.2f}s")
                    return jsonify({
                        "error": "RequestTimeout",
                        "message": f"Request timed out after {timeout} seconds",
                        "status": "NOTOK"
                    }), 408
                
                raise
        
        return wrapper
    return decorator


class RequestMetrics:
    """Simple request metrics collector."""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()
    
    def record_request(self, endpoint: str, response_time: float, success: bool):
        """Record basic request metrics."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get basic metrics."""
        uptime = time.time() - self.start_time
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "uptime_seconds": round(uptime, 2)
        }


# Global metrics instance
request_metrics = RequestMetrics()


def collect_metrics():
    """Decorator to collect request metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = request.endpoint or func.__name__
            success = True
            
            try:
                result = func(*args, **kwargs)
                
                # Check if response indicates success
                if hasattr(result, 'status_code'):
                    success = result.status_code < 400
                
                return result
                
            except Exception as e:
                success = False
                raise
            
            finally:
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                request_metrics.record_request(endpoint, response_time, success)
        
        return wrapper
    return decorator
