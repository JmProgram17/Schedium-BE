# app/core/security/headers.py
"""
Security headers middleware.
Adds security headers to all responses.
"""

from typing import Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    def __init__(self, app):
        super().__init__(app)
        self.security_headers = self._get_security_headers()

    def _get_security_headers(self) -> Dict[str, str]:
        """Get security headers based on environment."""
        headers = {
            # Prevent XSS attacks
            "X-Content-Type-Options": "nosniff",

            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Enable XSS filter
            "X-XSS-Protection": "1; mode=block",

            # DNS prefetch control
            "X-DNS-Prefetch-Control": "off",

            # Download options
            "X-Download-Options": "noopen",

            # Permitted cross-domain policies
            "X-Permitted-Cross-Domain-Policies": "none",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        # Add HSTS for production
        if settings.IS_PRODUCTION:
            headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "img-src 'self' data: https:",
            "font-src 'self' https: data:",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # For OpenAPI
            "style-src 'self' 'unsafe-inline' https:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

        headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Permissions Policy
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
        ]

        headers["Permissions-Policy"] = ", ".join(permissions)

        return headers

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Remove sensitive headers
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)

        return response
