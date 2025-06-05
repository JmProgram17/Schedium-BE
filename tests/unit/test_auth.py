"""
Unit tests for authentication.
"""

import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.security import SecurityUtils
from app.config import settings


class TestSecurityUtils:
    """Test security utilities."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        
        # Hash password
        hashed = SecurityUtils.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 20
        
        # Verify correct password
        assert SecurityUtils.verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert SecurityUtils.verify_password("WrongPassword", hashed) is False
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "123", "email": "test@example.com"}
        token = SecurityUtils.create_access_token(data)
        
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "123"}
        token = SecurityUtils.create_refresh_token(data)
        
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == "123"
        assert payload["type"] == "refresh"
        assert "jti" in payload  # JWT ID
        assert "exp" in payload
    
    def test_decode_token(self):
        """Test token decoding."""
        data = {"sub": "123", "test": "value"}
        token = SecurityUtils.create_access_token(data)
        
        # Decode token
        payload = SecurityUtils.decode_token(token)
        
        assert payload["sub"] == "123"
        assert payload["test"] == "value"
        assert payload["type"] == "access"
    
    def test_verify_token_type(self):
        """Test token type verification."""
        # Create access token
        access_token = SecurityUtils.create_access_token({"sub": "123"})
        access_payload = SecurityUtils.decode_token(access_token)
        
        assert SecurityUtils.verify_token_type(access_payload, "access") is True
        assert SecurityUtils.verify_token_type(access_payload, "refresh") is False
        
        # Create refresh token
        refresh_token = SecurityUtils.create_refresh_token({"sub": "123"})
        refresh_payload = SecurityUtils.decode_token(refresh_token)
        
        assert SecurityUtils.verify_token_type(refresh_payload, "refresh") is True
        assert SecurityUtils.verify_token_type(refresh_payload, "access") is False
    
    def test_expired_token(self):
        """Test expired token handling."""
        # Create token that expires immediately
        data = {"sub": "123"}
        token = SecurityUtils.create_access_token(
            data,
            expires_delta=timedelta(seconds=-1)
        )
        
        # Should raise exception when decoding
        with pytest.raises(Exception):
            SecurityUtils.decode_token(token)
    
    def test_password_reset_token(self):
        """Test password reset token."""
        email = "test@example.com"
        
        # Generate reset token
        token = SecurityUtils.generate_password_reset_token(email)
        assert token is not None
        
        # Verify reset token
        verified_email = SecurityUtils.verify_password_reset_token(token)
        assert verified_email == email
        
        # Test invalid token
        invalid_email = SecurityUtils.verify_password_reset_token("invalid_token")
        assert invalid_email is None