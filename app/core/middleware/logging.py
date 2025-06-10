# app/core/middleware/logging.py
"""
Request logging middleware.
Logs all requests with security context.
"""

import json
import time
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.security.validators import SecurityValidator

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with security context."""

    # Sensitive headers to redact
    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "x-api-key",
        "x-csrf-token",
    }

    # Sensitive fields in body
    SENSITIVE_FIELDS = {
        "password",
        "current_password",
        "new_password",
        "token",
        "refresh_token",
        "secret",
        "api_key",
    }

    async def dispatch(self, request: Request, call_next: Callable):
        """Log request and response details."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Log request
        await self._log_request(request, request_id)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        self._log_response(request, response, duration, request_id)

        # Add request ID to response
        response.headers["X-Request-ID"] = request_id

        return response

    async def _log_request(self, request: Request, request_id: str):
        """Log incoming request details."""
        # Redact sensitive headers
        headers = {}
        for header, value in request.headers.items():
            if header.lower() in self.SENSITIVE_HEADERS:
                headers[header] = "[REDACTED]"
            else:
                headers[header] = value

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": headers,
            "client": request.client.host if request.client else None,
            "user_id": getattr(request.state, "user_id", None),
        }

        # Log body for POST/PUT/PATCH (with sensitive data redacted)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    content_type = request.headers.get("content-type", "")
                    if "application/json" in content_type:
                        try:
                            body_json = json.loads(body)
                            log_data["body"] = self._redact_sensitive_data(body_json)
                        except json.JSONDecodeError:
                            log_data["body"] = "[Invalid JSON]"
                    else:
                        log_data["body"] = f"[{content_type}]"
            except Exception as e:
                log_data["body_error"] = str(e)

        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra=log_data,
        )

    def _log_response(self, request: Request, response, duration: float, request_id: str):
        """Log response details."""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": round(duration, 3),
            "user_id": getattr(request.state, "user_id", None),
        }

        # Log at appropriate level based on status code
        if response.status_code >= 500:
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {response.status_code}",
                extra=log_data,
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Request error: {request.method} {request.url.path} - {response.status_code}",
                extra=log_data,
            )
        else:
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra=log_data,
            )

    def _redact_sensitive_data(self, data):
        """Redact sensitive fields from data."""
        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                if key.lower() in self.SENSITIVE_FIELDS:
                    redacted[key] = "[REDACTED]"
                elif isinstance(value, dict):
                    redacted[key] = self._redact_sensitive_data(value)
                elif isinstance(value, list):
                    redacted[key] = [self._redact_sensitive_data(item) for item in value]
                else:
                    redacted[key] = value
            return redacted
        elif isinstance(data, list):
            return [self._redact_sensitive_data(item) for item in data]
        else:
            return data
