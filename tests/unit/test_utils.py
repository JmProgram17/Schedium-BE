"""
Unit tests for utility functions.
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.core.pagination import PaginationParams, paginate, paginate_list
from app.utils.formatters import (
    format_currency,
    format_date,
    format_percentage,
    format_phone_number,
    format_time,
)
from app.utils.validators import (
    sanitize_string,
    validate_capacity,
    validate_date_range,
    validate_document_number,
    validate_email,
    validate_hour_limit,
    validate_phone,
    validate_time_slot,
)


class TestValidators:
    """Test validator functions."""

    def test_validate_email(self):
        """Test email validation."""
        # Valid emails
        assert validate_email("user@example.com") is True
        assert validate_email("test.user+tag@sub.domain.com") is True

        # Invalid emails
        assert validate_email("invalid") is False
        assert validate_email("@example.com") is False
        assert validate_email("user@") is False
        assert validate_email("user..double@example.com") is False

    def test_validate_phone(self):
        """Test phone number validation."""
        # Valid phones
        assert validate_phone("+1234567890") is True
        assert validate_phone("123-456-7890") is True
        assert validate_phone("(123) 456-7890") is True
        assert validate_phone("1234567890") is True

        # Invalid phones
        assert validate_phone("123") is False  # Too short
        assert validate_phone("abcdefghij") is False  # Letters
        assert validate_phone("") is False

    def test_validate_document_number(self):
        """Test document number validation."""
        # Valid documents
        assert validate_document_number("12345678") is True
        assert validate_document_number("CC12345678") is True
        assert validate_document_number("TI-98765432") is True

        # Invalid documents
        assert validate_document_number("123") is False  # Too short
        assert validate_document_number("") is False
        assert validate_document_number("a" * 30) is False  # Too long

    def test_validate_date_range(self):
        """Test date range validation."""
        # Valid ranges
        assert validate_date_range(date(2024, 1, 1), date(2024, 12, 31)) is True

        # Same date is valid
        assert validate_date_range(date(2024, 1, 1), date(2024, 1, 1)) is True

        # Invalid range
        assert validate_date_range(date(2024, 12, 31), date(2024, 1, 1)) is False

    def test_sanitize_string(self):
        """Test string sanitization."""
        # Remove extra spaces
        assert sanitize_string("  hello   world  ") == "hello world"

        # Replace multiple spaces
        assert sanitize_string("hello    world") == "hello world"

        # Truncate long strings
        assert len(sanitize_string("a" * 100, max_length=50)) == 50

        # Handle empty strings
        assert sanitize_string("   ") == ""


class TestPagination:
    """Test pagination utilities."""

    def test_pagination_params(self):
        """Test pagination parameters."""
        # Default values
        params = PaginationParams()
        assert params.page == 1
        assert params.skip == 0
        assert params.limit == params.page_size

        # Custom values
        params = PaginationParams(page=3, page_size=20)
        assert params.page == 3
        assert params.page_size == 20
        assert params.skip == 40  # (3-1) * 20

        # Max page size limit
        params = PaginationParams(page_size=1000)
        assert params.page_size <= 100  # Should be capped

    def test_paginate_list(self):
        """Test list pagination."""
        items = list(range(1, 101))  # 100 items

        # First page
        params = PaginationParams(page=1, page_size=10)
        page = paginate_list(items, params)

        assert page.total == 100
        assert page.page == 1
        assert page.page_size == 10
        assert page.total_pages == 10
        assert page.has_next is True
        assert page.has_prev is False
        assert len(page.items) == 10
        assert page.items[0] == 1

        # Last page
        params = PaginationParams(page=10, page_size=10)
        page = paginate_list(items, params)

        assert page.has_next is False
        assert page.has_prev is True
        assert page.items[-1] == 100

    def test_paginate_empty_list(self):
        """Test pagination with empty list."""
        items = []
        params = PaginationParams()
        page = paginate_list(items, params)

        assert page.total == 0
        assert page.total_pages == 0
        assert page.has_next is False
        assert page.has_prev is False
        assert len(page.items) == 0
