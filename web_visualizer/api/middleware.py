"""Middleware configuration for the web visualizer API."""

import time
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ..config import config

log = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application."""
    
    # Trusted Host Middleware (security)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.local"]
    )
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Rate Limiting Middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # Security Headers Middleware
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next: Callable) -> Response:
        """Add security headers to all responses."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # CSP for additional security
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://d3js.org https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:; "
            "worker-src 'self' blob:;"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response
    
    # Request Logging Middleware
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next: Callable) -> Response:
        """Log requests and response times."""
        start_time = time.time()
        
        # Log request
        log.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            log.info(
                f"Response: {response.status_code} "
                f"({process_time:.3f}s) "
                f"for {request.method} {request.url.path}"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            log.error(
                f"Error: {str(e)} "
                f"({process_time:.3f}s) "
                f"for {request.method} {request.url.path}"
            )
            raise
    
    # Request Size Limiting Middleware
    @app.middleware("http")
    async def request_size_middleware(request: Request, call_next: Callable) -> Response:
        """Limit request body size."""
        MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50MB
        
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Request too large. Maximum size: {MAX_REQUEST_SIZE} bytes"
            )
        
        return await call_next(request)
    
    # Health Check Endpoint (bypass middleware)
    @app.middleware("http")
    async def health_check_middleware(request: Request, call_next: Callable) -> Response:
        """Fast path for health checks."""
        if request.url.path == "/health":
            return Response(
                content='{"status":"healthy"}',
                media_type="application/json",
                status_code=200
            )
        
        return await call_next(request)