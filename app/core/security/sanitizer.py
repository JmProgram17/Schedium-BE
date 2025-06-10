# app/core/security/sanitizer.py
"""
Input sanitization utilities.
Prevents XSS and SQL injection attacks.
"""

import html
import re
from typing import Any, Dict, List, Optional, Union

import bleach
from pydantic import BaseModel


class InputSanitizer:
    """Sanitize user inputs to prevent security vulnerabilities."""

    # Allowed HTML tags for rich text fields
    ALLOWED_TAGS = [
        'a', 'abbr', 'b', 'blockquote', 'code', 'em',
        'i', 'li', 'ol', 'strong', 'ul', 'p', 'br',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    ]

    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title', 'target'],
        'abbr': ['title'],
    }

    # SQL injection patterns
    SQL_PATTERNS = [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
        r"(--|#|\/\*|\*\/)",
        r"(\bor\b\s*\d+\s*=\s*\d+)",
        r"(\band\b\s*\d+\s*=\s*\d+)",
        r"(;|\||&&)",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
    ]

    @classmethod
    def sanitize_html(cls, text: str, allow_rich_text: bool = False) -> str:
        """Sanitize HTML content."""
        if not text:
            return text

        if allow_rich_text:
            # Clean HTML with allowed tags
            cleaned = bleach.clean(
                text,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True,
            )
            return str(cleaned)
        else:
            # Escape all HTML
            return html.escape(text)

    @classmethod
    def sanitize_string(cls, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize plain text input."""
        if not text:
            return text

        # Remove control characters
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)

        # Trim whitespace
        text = text.strip()

        # Limit length
        if max_length:
            text = text[:max_length]

        return text

    @classmethod
    def check_sql_injection(cls, text: str) -> bool:
        """Check for potential SQL injection patterns."""
        if not text:
            return False

        text_lower = text.lower()

        for pattern in cls.SQL_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    @classmethod
    def check_xss(cls, text: str) -> bool:
        """Check for potential XSS patterns."""
        if not text:
            return False

        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        if not filename:
            return filename

        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')

        # Remove special characters
        filename = re.sub(r'[^\w\s.-]', '', filename)

        # Remove multiple dots
        filename = re.sub(r'\.+', '.', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]

        return filename

    @classmethod
    def sanitize_dict(
        cls,
        data: Dict[str, Any],
        string_fields: Optional[List[str]] = None,
        html_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Sanitize dictionary data."""
        if not data:
            return data

        sanitized = {}
        for key, value in data.items():
            sanitized[key] = cls._sanitize_value(value, key, string_fields, html_fields)
        return sanitized

    @classmethod
    def _sanitize_value(
        cls,
        value: Any,
        key: str,
        string_fields: Optional[List[str]] = None,
        html_fields: Optional[List[str]] = None,
    ) -> Any:
        """Sanitize a single value based on its type."""
        if isinstance(value, str):
            return cls._sanitize_string_value(value, key, string_fields, html_fields)
        elif isinstance(value, dict):
            return cls.sanitize_dict(value, string_fields, html_fields)
        elif isinstance(value, list):
            return cls._sanitize_list_value(value, string_fields, html_fields)
        else:
            return value

    @classmethod
    def _sanitize_string_value(
        cls,
        value: str,
        key: str,
        string_fields: Optional[List[str]] = None,
        html_fields: Optional[List[str]] = None,
    ) -> str:
        """Sanitize a string value."""
        if html_fields and key in html_fields:
            return cls.sanitize_html(value, allow_rich_text=True)
        else:
            return cls.sanitize_string(value)

    @classmethod
    def _sanitize_list_value(
        cls,
        value: list,
        string_fields: Optional[List[str]] = None,
        html_fields: Optional[List[str]] = None,
    ) -> list:
        """Sanitize a list value."""
        sanitized_list = []
        for item in value:
            if isinstance(item, dict):
                sanitized_list.append(cls.sanitize_dict(item, string_fields, html_fields))
            elif isinstance(item, str):
                sanitized_list.append(cls.sanitize_string(item))
            else:
                sanitized_list.append(item)
        return sanitized_list

    @classmethod
    def validate_and_sanitize_model(
        cls,
        model: BaseModel,
        string_fields: Optional[List[str]] = None,
        html_fields: Optional[List[str]] = None,
    ) -> BaseModel:
        """Validate and sanitize Pydantic model."""
        data = model.model_dump()
        sanitized_data = cls.sanitize_dict(data, string_fields, html_fields)
        return model.__class__(**sanitized_data)
