# app/core/middleware/security.py
"""
Enhanced security middleware.
Combines multiple security features.
"""

import hashlib
import hmac
import json
import time
from typing import Callable, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.core.security.rate_limiter import get_rate_limiter
from app.core.security.sanitizer import InputSanitizer
from app.core.security.validators import SecurityValidator


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""

    def __init__(self, app):
        super().__init__(app)
        # Skip rate limiter initialization in testing
        if settings.APP_ENV == "testing" or not settings.RATE_LIMIT_ENABLED:
            self.rate_limiter = None
        else:
            self.rate_limiter = get_rate_limiter()
        self.sanitizer = InputSanitizer()
        self.validator = SecurityValidator()

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with security checks."""
        # Run pre-request security checks
        error_response = await self._run_security_checks(request)
        if error_response:
            return error_response

        # Process request
        start_time = time.time()
        response = await call_next(request)

        # Add response headers
        self._add_response_headers(request, response, start_time)

        return response

    async def _run_security_checks(self, request: Request) -> Optional[JSONResponse]:
        """Run all security checks. Return error response if any check fails."""
        # Check request size
        size_check = self._check_request_size(request)
        if size_check:
            return size_check

        # Rate limiting
        rate_check = await self._check_rate_limit(request)
        if rate_check:
            return rate_check

        # Validate content type
        content_check = self._check_content_type(request)
        if content_check:
            return content_check

        # Check URL patterns
        if self._check_suspicious_url(str(request.url)):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request"},
            )

        # Validate API key
        api_key_check = self._check_api_key(request)
        if api_key_check:
            return api_key_check

        return None

    def _check_request_size(self, request: Request) -> Optional[JSONResponse]:
        """Check if request size is within limits."""
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > settings.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request too large"},
                )
        return None

    async def _check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """Check rate limiting."""
        # Skip rate limiting in testing environment
        if settings.APP_ENV == "testing" or not settings.RATE_LIMIT_ENABLED:
            return None
            
        if self.rate_limiter and settings.RATE_LIMIT_ENABLED:
            try:
                await self.rate_limiter.check_rate_limit(request)
            except Exception as e:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": str(e)},
                    headers=getattr(e, "headers", {}),
                )
        return None

    def _check_content_type(self, request: Request) -> Optional[JSONResponse]:
        """Validate content type for modification requests."""
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not any(ct in content_type for ct in ["application/json", "multipart/form-data", "application/x-www-form-urlencoded"]):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "Unsupported media type"},
                )
        return None

    def _check_api_key(self, request: Request) -> Optional[JSONResponse]:
        """Validate API key if provided."""
        api_key = request.headers.get("X-API-Key")
        if api_key and not self._validate_api_key(api_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid API key"},
            )
        return None

    def _add_response_headers(self, request: Request, response, start_time: float):
        """Add security and performance headers to response."""
        # Add security headers from rate limiter
        if hasattr(request.state, "rate_limit_headers"):
            for header, value in request.state.rate_limit_headers.items():
                response.headers[header] = value

        # Add processing time
        response.headers["X-Process-Time"] = str(time.time() - start_time)

    def _check_suspicious_url(self, url: str) -> bool:
        """Check URL for suspicious patterns."""
        suspicious_patterns = [
            r"\.\./",  # Directory traversal
            r"<script",  # XSS attempt
            r"javascript:",  # XSS attempt
            r"\x00",  # Null byte
            r"%00",  # Encoded null byte
            r"\.\.\\",  # Windows directory traversal
        ]

        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if pattern in url_lower:
                return True

        return False

    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and signature."""
        if not api_key or len(api_key) < 32:
            return False

        # API key format: "sched_" + 32 hex chars + "_" + timestamp + "_" + signature
        # Example: sched_a1b2c3d4e5f6789012345678901234567890_1640995200_abc123def456
        
        try:
            # Check prefix
            if not api_key.startswith("sched_"):
                return False
                
            # Remove prefix and split parts
            key_without_prefix = api_key[6:]  # Remove "sched_"
            parts = key_without_prefix.split("_")
            
            if len(parts) != 3:
                return False
                
            key_id, timestamp_str, signature = parts
            
            # Validate key ID (should be 32 hex chars)
            if len(key_id) != 32 or not all(c in "0123456789abcdef" for c in key_id.lower()):
                return False
                
            # Validate timestamp (should be valid unix timestamp)
            try:
                timestamp = int(timestamp_str)
                current_timestamp = int(time.time())
                
                # API key should not be older than 1 year
                if current_timestamp - timestamp > 365 * 24 * 60 * 60:
                    return False
                    
            except ValueError:
                return False
                
            # Validate signature (should be at least 12 chars)
            if len(signature) < 12:
                return False
                
            # In a real implementation, you would:
            # 1. Look up the API key in your database
            # 2. Verify the signature using HMAC
            # 3. Check if the key is active and not revoked
            # 4. Check rate limits specific to this API key
            
            # For now, we'll validate the format and accept well-formed keys
            return True
            
        except Exception:
            return False
