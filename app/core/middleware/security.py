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
            if not any(ct in content_type for ct in ["application/json", "multipart/form-data"]):
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

        # Add your API key validation logic here
        # This is a placeholder implementation
        return True
