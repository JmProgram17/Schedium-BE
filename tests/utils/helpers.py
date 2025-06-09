"""
Test helper functions.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


def generate_random_email() -> str:
    """Generate a random email address."""
    username = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@test.com"


def generate_random_document() -> str:
    """Generate a random document number."""
    return "".join(random.choices(string.digits, k=8))


def future_date(days: int = 30) -> str:
    """Get a future date string."""
    future = datetime.utcnow() + timedelta(days=days)
    return future.date().isoformat()


def past_date(days: int = 30) -> str:
    """Get a past date string."""
    past = datetime.utcnow() - timedelta(days=days)
    return past.date().isoformat()


def create_test_user_data(
    email: Optional[str] = None, document: Optional[str] = None, **kwargs
) -> Dict[str, Any]:
    """Create test user data with defaults."""
    data = {
        "first_name": "Test",
        "last_name": "User",
        "email": email or generate_random_email(),
        "document_number": document or generate_random_document(),
        "password": "TestPass123!",
        "active": True,
    }
    data.update(kwargs)
    return data


def extract_token_from_response(response) -> str:
    """Extract access token from login response."""
    data = response.json()
    return data["data"]["access_token"]


def create_auth_headers(token: str) -> Dict[str, str]:
    """Create authorization headers with token."""
    return {"Authorization": f"Bearer {token}"}
