# app/core/middleware/request_id.py
"""
Request ID middleware.
Adds unique request ID for tracking and debugging.
"""

import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable):
        """Add request ID to request state and response headers."""
        # Check if request already has ID (from header)
        request_id = request.headers.get("X-Request-ID")

        # Generate new ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())

        # Validate request ID format
        try:
            # Ensure it's a valid UUID
            uuid.UUID(request_id)
        except ValueError:
            # Generate new one if invalid
            request_id = str(uuid.uuid4())

        # Add to request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response
