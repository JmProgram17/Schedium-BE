# app/core/security/validators.py
"""
Security-focused validators.
Additional validation for security-sensitive operations.
"""

import re
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import HTTPException, status


class SecurityValidator:
    """Security-focused validation utilities."""

    # Password requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 128
    PASSWORD_PATTERNS = [
        (r"[A-Z]", "at least one uppercase letter"),
        (r"[a-z]", "at least one lowercase letter"),
        (r"\d", "at least one digit"),
        (r"[!@#$%^&*(),.?\":{}|<>]", "at least one special character"),
    ]

    # Common weak passwords
    WEAK_PASSWORDS = {
        "password", "12345678", "123456789", "qwerty", "abc123",
        "password123", "admin", "letmein", "welcome", "monkey",
        "dragon", "1234567890", "password1", "123123", "admin123",
    }

    @classmethod
    def validate_password_strength(cls, password: str) -> List[str]:
        """
        Validate password strength and return list of issues.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check length
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long")

        if len(password) > cls.PASSWORD_MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.PASSWORD_MAX_LENGTH} characters")

        # Check patterns
        for pattern, description in cls.PASSWORD_PATTERNS:
            if not re.search(pattern, password):
                errors.append(f"Password must contain {description}")

        # Check weak passwords
        if password.lower() in cls.WEAK_PASSWORDS:
            errors.append("Password is too common. Please choose a stronger password")

        # Check for repeated characters
        if re.search(r"(.)\1{2,}", password):
            errors.append("Password should not contain repeated characters")

        return errors

    @classmethod
    def validate_url(cls, url: str, allowed_schemes: List[str] = None) -> bool:
        """Validate URL for security."""
        if not url:
            return False

        allowed_schemes = allowed_schemes or ["http", "https"]

        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in allowed_schemes:
                return False

            # Check for localhost/internal IPs in production
            if parsed.hostname:
                if parsed.hostname in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    return False

                # Check for internal IP ranges
                if re.match(r"^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)", parsed.hostname):
                    return False

            return True
        except Exception:
            return False

    @classmethod
    def validate_file_upload(
        cls,
        filename: str,
        content_type: str,
        file_size: int,
        allowed_extensions: List[str] = None,
        allowed_content_types: List[str] = None,
        max_size_bytes: int = 10 * 1024 * 1024,  # 10MB default
    ) -> List[str]:
        """Validate file upload for security."""
        errors = []

        # Check file size
        if file_size > max_size_bytes:
            errors.append(f"File size exceeds maximum allowed size of {max_size_bytes / 1024 / 1024}MB")

        # Check extension
        if allowed_extensions:
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            if ext not in allowed_extensions:
                errors.append(f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")

        # Check content type
        if allowed_content_types and content_type not in allowed_content_types:
            errors.append(f"Content type not allowed: {content_type}")

        # Check for double extensions
        if filename.count('.') > 1:
            errors.append("Filename contains multiple extensions")

        # Check for null bytes
        if '\x00' in filename:
            errors.append("Filename contains invalid characters")

        return errors

    @classmethod
    def validate_jwt_claims(cls, claims: dict) -> bool:
        """Validate JWT token claims."""
        required_claims = ["sub", "exp", "iat", "type"]

        for claim in required_claims:
            if claim not in claims:
                return False

        # Check token type
        if claims.get("type") not in ["access", "refresh"]:
            return False

        # Additional checks can be added here

        return True

    @classmethod
    def sanitize_log_message(cls, message: str) -> str:
        """Sanitize log messages to prevent log injection."""
        if not message:
            return message

        # Remove line breaks and carriage returns
        message = message.replace('\n', ' ').replace('\r', ' ')

        # Remove control characters
        message = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', message)

        # Limit length
        if len(message) > 1000:
            message = message[:1000] + '...'

        return message
