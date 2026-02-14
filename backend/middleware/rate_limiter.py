"""
Rate Limiting Middleware for LearnLoop
Provides API Gateway-like rate limiting functionality
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import asyncio
import time

class RateLimiter:
    """
    In-memory rate limiter with sliding window algorithm
    For production, use Redis or similar distributed cache
    """
    
    def __init__(self):
        # Storage: {key: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        # Cleanup task
        self._cleanup_task = None
    
    def _get_key(self, request: Request, identifier: str = None) -> str:
        """Generate rate limit key from request with session context"""
        # Try to get session context from headers to separate different chat sessions
        session_context = request.headers.get("X-Session-Context", "")
        
        if identifier:
            # Include session context in key to separate rate limits per session
            if session_context:
                return f"user:{identifier}:session:{session_context}"
            return f"user:{identifier}"
        
        # Fallback to IP-based limiting with session context
        client_ip = request.client.host if request.client else "unknown"
        if session_context:
            return f"ip:{client_ip}:session:{session_context}"
        return f"ip:{client_ip}"
    
    def _cleanup_old_requests(self, key: str, window_seconds: int):
        """Remove requests outside the time window"""
        cutoff_time = time.time() - window_seconds
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key] 
            if ts > cutoff_time
        ]
    
    async def check_rate_limit(
        self, 
        request: Request, 
        max_requests: int, 
        window_seconds: int,
        identifier: str = None
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit
        
        Args:
            request: FastAPI request object
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            identifier: Optional user identifier (user_id, username)
        
        Returns:
            (is_allowed, limit_info)
        """
        key = self._get_key(request, identifier)
        
        # Cleanup old requests
        self._cleanup_old_requests(key, window_seconds)
        
        # Count requests in current window
        current_count = sum(count for _, count in self.requests[key])
        
        # Check limit
        is_allowed = current_count < max_requests
        
        if is_allowed:
            # Add new request
            self.requests[key].append((time.time(), 1))
        
        # Calculate limit info
        remaining = max(0, max_requests - current_count - (1 if is_allowed else 0))
        reset_time = int(time.time() + window_seconds)
        
        limit_info = {
            "limit": max_requests,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": window_seconds if not is_allowed else None
        }
        
        return is_allowed, limit_info
    
    async def start_cleanup_task(self):
        """Start background task to cleanup old entries"""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                current_time = time.time()
                keys_to_delete = []
                
                for key in list(self.requests.keys()):
                    # Remove entries older than 1 hour
                    self.requests[key] = [
                        (ts, count) for ts, count in self.requests[key]
                        if current_time - ts < 3600
                    ]
                    # Delete empty keys
                    if not self.requests[key]:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    del self.requests[key]
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())

# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limit configurations for different endpoints
RATE_LIMITS = {
    # Endpoint pattern: (max_requests, window_seconds)
    "/api/buddy/chat": (200, 60),  # 200 requests per minute (increased for smooth chat experience)
    "/api/material/upload": (20, 60),  # 20 uploads per minute
    "/api/auth/login": (50, 60),  # 50 login attempts per minute
    "/api/auth/register": (50, 60),  # 50 registrations per minute
    "/api/graph": (100, 60),  # 100 requests per minute
    "default": (300, 60)  # Default: 300 requests per minute
}

async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware for rate limiting
    Add this to your FastAPI app
    """
    # Skip rate limiting for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Skip rate limiting for certain paths
    skip_paths = [
        "/", 
        "/docs", 
        "/redoc", 
        "/openapi.json", 
        "/api/health",
        "/api/health/check",
        "/favicon.ico"
    ]
    if request.url.path in skip_paths:
        return await call_next(request)
    
    # Get rate limit config for this endpoint
    path = request.url.path
    max_requests, window_seconds = RATE_LIMITS.get(path, RATE_LIMITS["default"])
    
    # Try to get user identifier from headers or query params
    identifier = None
    if "X-User-ID" in request.headers:
        identifier = request.headers["X-User-ID"]
    elif "user_id" in request.query_params:
        identifier = request.query_params["user_id"]
    
    # Check rate limit
    is_allowed, limit_info = await rate_limiter.check_rate_limit(
        request, max_requests, window_seconds, identifier
    )
    
    if not is_allowed:
        # Rate limit exceeded
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please try again in {limit_info['retry_after']} seconds.",
                "limit": limit_info["limit"],
                "reset": limit_info["reset"]
            },
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(limit_info["reset"]),
                "Retry-After": str(limit_info["retry_after"])
            }
        )
    
    # Process request and add rate limit headers to response
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
    
    return response
