"""
Security utilities for the application.
Handles password hashing, JWT tokens, and authentication.
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utilities for authentication and authorization."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Generate password hash.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            data: Token payload data
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.

        Args:
            data: Token payload data
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "refresh",
                "jti": secrets.token_urlsafe(32),  # JWT ID for refresh token
            }
        )

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Decoded token payload

        Raises:
            JWTError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            raise

    @staticmethod
    def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
        """
        Verify token type matches expected type.

        Args:
            payload: Decoded token payload
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            True if type matches, False otherwise
        """
        return payload.get("type") == expected_type

    @staticmethod
    def generate_password_reset_token(email: str) -> str:
        """
        Generate password reset token.

        Args:
            email: User email

        Returns:
            Password reset token
        """
        delta = timedelta(hours=24)
        data = {"sub": email, "type": "password_reset"}
        return SecurityUtils.create_access_token(data=data, expires_delta=delta)

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """
        Verify password reset token.

        Args:
            token: Reset token

        Returns:
            Email if valid, None otherwise
        """
        try:
            payload = SecurityUtils.decode_token(token)
            if payload.get("type") != "password_reset":
                return None
            email = payload.get("sub")
            return email
        except JWTError:
            return None
