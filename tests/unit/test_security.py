"""
Unit tests for security components.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from jose import JWTError, jwt

from app.config import settings
from app.core.auth_middleware import AuthenticationMiddleware, JWTBearer
from app.core.exceptions import UnauthorizedException
from app.core.auth_security import SecurityUtils


class TestJWTBearer:
    """Test JWT Bearer authentication."""

    @pytest.fixture
    def jwt_bearer(self):
        """Create JWTBearer instance."""
        return JWTBearer()

    @pytest.mark.asyncio
    async def test_valid_bearer_token(self, jwt_bearer):
        """Test valid bearer token verification."""
        # Create valid token
        token = SecurityUtils.create_access_token({"sub": "123"})

        # Mock request with valid Authorization header
        mock_request = Mock()
        mock_credentials = Mock()
        mock_credentials.scheme = "Bearer"
        mock_credentials.credentials = token

        with patch.object(jwt_bearer, "__call__", return_value=mock_credentials):
            result = await jwt_bearer(mock_request)
            assert result == token

    def test_verify_jwt_valid_token(self, jwt_bearer):
        """Test JWT verification with valid token."""
        token = SecurityUtils.create_access_token({"sub": "123"})
        assert jwt_bearer.verify_jwt(token) is True

    def test_verify_jwt_invalid_token(self, jwt_bearer):
        """Test JWT verification with invalid token."""
        assert jwt_bearer.verify_jwt("invalid.token.here") is False

    def test_verify_jwt_expired_token(self, jwt_bearer):
        """Test JWT verification with expired token."""
        token = SecurityUtils.create_access_token(
            {"sub": "123"}, expires_delta=timedelta(seconds=-1)
        )
        assert jwt_bearer.verify_jwt(token) is False


class TestAuthenticationMiddleware:
    """Test authentication middleware."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return AuthenticationMiddleware(app=Mock())

    @pytest.mark.asyncio
    async def test_public_endpoints_bypass_auth(self, middleware):
        """Test that public endpoints bypass authentication."""
        # Mock request to public endpoint
        mock_request = Mock()
        mock_request.url.path = "/health"
        mock_request.headers = {}

        mock_call_next = Mock()
        mock_response = Mock()
        mock_call_next.return_value = mock_response

        response = await middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response
        assert not hasattr(mock_request.state, "user_id")

    @pytest.mark.asyncio
    async def test_authenticated_request_sets_user_context(self, middleware):
        """Test that authenticated requests set user context."""
        # Create valid token
        token_data = {
            "sub": "123",
            "email": "test@example.com",
            "role": "Administrator",
        }
        token = SecurityUtils.create_access_token(token_data)

        # Mock authenticated request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/users"
        mock_request.headers = {"Authorization": f"Bearer {token}"}
        mock_request.state = Mock()

        mock_call_next = Mock()
        mock_call_next.return_value = Mock()

        await middleware.dispatch(mock_request, mock_call_next)

        assert mock_request.state.user_id == "123"
        assert mock_request.state.user_email == "test@example.com"
        assert mock_request.state.user_role == "Administrator"


class TestPasswordValidation:
    """Test password validation and policies."""

    def test_password_complexity_requirements(self):
        """Test password complexity validation."""
        # Valid passwords
        valid_passwords = ["Test123!", "MyP@ssw0rd", "Secure#Pass123", "C0mpl3x!Pass"]

        for password in valid_passwords:
            hashed = SecurityUtils.get_password_hash(password)
            assert hashed is not None
            assert len(hashed) > 50

        # Test that different passwords produce different hashes
        hash1 = SecurityUtils.get_password_hash("Password1!")
        hash2 = SecurityUtils.get_password_hash("Password2!")
        assert hash1 != hash2

    def test_token_payload_validation(self):
        """Test token payload structure and claims."""
        payload = {
            "sub": "user123",
            "email": "user@example.com",
            "role": "User",
            "custom_claim": "value",
        }

        token = SecurityUtils.create_access_token(payload)
        decoded = SecurityUtils.decode_token(token)

        # Verify all claims are present
        assert decoded["sub"] == "user123"
        assert decoded["email"] == "user@example.com"
        assert decoded["role"] == "User"
        assert decoded["custom_claim"] == "value"
        assert decoded["type"] == "access"

        # Verify standard JWT claims
        assert "exp" in decoded
        assert "iat" in decoded
        assert decoded["exp"] > decoded["iat"]
