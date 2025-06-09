"""
Authentication middleware.
Handles request authentication and user context.
"""

from typing import Callable, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.core.security import SecurityUtils


class JWTBearer(HTTPBearer):
    """
    Custom JWT Bearer authentication.
    """

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                )
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token.",
                )
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code.",
            )

    def verify_jwt(self, token: str) -> bool:
        """
        Verify JWT token validity.

        Args:
            token: JWT token

        Returns:
            True if valid, False otherwise
        """
        try:
            payload = SecurityUtils.decode_token(token)
            return SecurityUtils.verify_token_type(payload, "access")
        except:
            return False


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication state.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add user context if authenticated.
        """
        # Skip authentication for public endpoints
        public_paths = [
            "/",
            "/health",
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/docs",
            "/api/v1/redoc",
            "/api/v1/openapi.json",
        ]

        if any(request.url.path.startswith(path) for path in public_paths):
            response = await call_next(request)
            return response

        # Try to get user from token
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                payload = SecurityUtils.decode_token(token)
                if SecurityUtils.verify_token_type(payload, "access"):
                    # Add user info to request state
                    request.state.user_id = payload.get("sub")
                    request.state.user_email = payload.get("email")
                    request.state.user_role = payload.get("role")
            except:
                # Invalid token, but continue without user context
                pass

        response = await call_next(request)
        return response
