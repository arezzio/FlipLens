from flask import request, jsonify, current_app
from functools import wraps
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.limits = {
            '/api/search': {'requests': 100, 'window': 3600},  # 100 requests per hour
            '/api/saved-items': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
            'default': {'requests': 500, 'window': 3600}  # 500 requests per hour
        }
    
    def is_allowed(self, endpoint, client_ip):
        """Check if request is allowed based on rate limits"""
        now = time.time()
        key = f"{client_ip}:{endpoint}"
        
        # Clean old requests outside the window
        window = self.limits.get(endpoint, self.limits['default'])['window']
        while self.requests[key] and self.requests[key][0] < now - window:
            self.requests[key].popleft()
        
        # Check if limit exceeded
        limit = self.limits.get(endpoint, self.limits['default'])['requests']
        if len(self.requests[key]) >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining_requests(self, endpoint, client_ip):
        """Get remaining requests for a client on an endpoint"""
        now = time.time()
        key = f"{client_ip}:{endpoint}"
        
        # Clean old requests
        window = self.limits.get(endpoint, self.limits['default'])['window']
        while self.requests[key] and self.requests[key][0] < now - window:
            self.requests[key].popleft()
        
        limit = self.limits.get(endpoint, self.limits['default'])['requests']
        remaining = max(0, limit - len(self.requests[key]))
        return remaining

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(endpoint=None):
    """Decorator to apply rate limiting to endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get endpoint path
            endpoint_path = endpoint or request.endpoint
            
            # Get client IP
            client_ip = request.remote_addr
            
            # Check rate limit
            if not rate_limiter.is_allowed(endpoint_path, client_ip):
                remaining_time = rate_limiter.limits.get(endpoint_path, rate_limiter.limits['default'])['window']
                return jsonify({
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": remaining_time,
                    "status": "error"
                }), 429
            
            # Add rate limit headers to response
            response = f(*args, **kwargs)
            
            # If response is a tuple (response, status_code), extract the response
            if isinstance(response, tuple):
                response_obj, status_code = response
            else:
                response_obj = response
                status_code = 200
            
            # Add rate limit headers
            remaining = rate_limiter.get_remaining_requests(endpoint_path, client_ip)
            limit = rate_limiter.limits.get(endpoint_path, rate_limiter.limits['default'])['requests']
            
            if hasattr(response_obj, 'headers'):
                response_obj.headers['X-RateLimit-Limit'] = str(limit)
                response_obj.headers['X-RateLimit-Remaining'] = str(remaining)
                response_obj.headers['X-RateLimit-Reset'] = str(int(time.time() + rate_limiter.limits.get(endpoint_path, rate_limiter.limits['default'])['window']))
            
            return response_obj, status_code if isinstance(response, tuple) else response_obj
        
        return decorated_function
    return decorator 