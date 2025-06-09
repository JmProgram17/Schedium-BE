"""
Mock objects and fixtures for testing.
"""

import random
import string
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock


class MockDatabase:
    """Mock database for testing without real DB."""

    def __init__(self):
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        self._id_counters: Dict[str, int] = {}

    def add(self, table: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add a record to mock database."""
        if table not in self.data:
            self.data[table] = []
            self._id_counters[table] = 1

        # Add ID if not present
        if "id" not in record:
            record["id"] = self._id_counters[table]
            self._id_counters[table] += 1

        # Add timestamps
        now = datetime.utcnow()
        record["created_at"] = now
        record["updated_at"] = now

        self.data[table].append(record)
        return record

    def get(self, table: str, id: int) -> Optional[Dict[str, Any]]:
        """Get a record by ID."""
        if table not in self.data:
            return None

        for record in self.data[table]:
            if record.get("id") == id:
                return record
        return None

    def filter(self, table: str, **kwargs) -> List[Dict[str, Any]]:
        """Filter records by criteria."""
        if table not in self.data:
            return []

        results = []
        for record in self.data[table]:
            match = True
            for key, value in kwargs.items():
                if record.get(key) != value:
                    match = False
                    break
            if match:
                results.append(record)

        return results

    def update(self, table: str, id: int, updates: Dict[str, Any]) -> bool:
        """Update a record."""
        record = self.get(table, id)
        if not record:
            return False

        record.update(updates)
        record["updated_at"] = datetime.utcnow()
        return True

    def delete(self, table: str, id: int) -> bool:
        """Delete a record."""
        if table not in self.data:
            return False

        self.data[table] = [r for r in self.data[table] if r.get("id") != id]
        return True

    def clear(self):
        """Clear all data."""
        self.data.clear()
        self._id_counters.clear()


class MockEmailService:
    """Mock email service for testing."""

    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []

    def send_email(
        self, to: str, subject: str, body: str, html: Optional[str] = None
    ) -> bool:
        """Mock sending an email."""
        email = {
            "to": to,
            "subject": subject,
            "body": body,
            "html": html,
            "sent_at": datetime.utcnow(),
        }
        self.sent_emails.append(email)
        return True

    def get_sent_emails(self, to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sent emails, optionally filtered by recipient."""
        if to:
            return [e for e in self.sent_emails if e["to"] == to]
        return self.sent_emails

    def clear(self):
        """Clear sent emails."""
        self.sent_emails.clear()


class MockFileStorage:
    """Mock file storage for testing."""

    def __init__(self):
        self.files: Dict[str, bytes] = {}

    def save(self, filename: str, content: bytes) -> str:
        """Save a file and return its path."""
        path = f"/mock/storage/{filename}"
        self.files[path] = content
        return path

    def read(self, path: str) -> Optional[bytes]:
        """Read a file by path."""
        return self.files.get(path)

    def delete(self, path: str) -> bool:
        """Delete a file."""
        if path in self.files:
            del self.files[path]
            return True
        return False

    def exists(self, path: str) -> bool:
        """Check if file exists."""
        return path in self.files

    def clear(self):
        """Clear all files."""
        self.files.clear()


def create_mock_request(
    method: str = "GET",
    path: str = "/",
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
) -> Mock:
    """Create a mock FastAPI request."""
    request = Mock()
    request.method = method
    request.url.path = path
    request.headers = headers or {}
    request.query_params = query_params or {}
    request.json = MagicMock(return_value=json_data) if json_data else None

    # Add state for user context
    request.state = Mock()
    if user_id:
        request.state.user_id = user_id

    return request


def create_mock_user(
    user_id: int = 1,
    email: str = "test@example.com",
    role: str = "User",
    active: bool = True,
) -> Mock:
    """Create a mock user object."""
    user = Mock()
    user.user_id = user_id
    user.email = email
    user.first_name = "Test"
    user.last_name = "User"
    user.active = active
    user.created_at = datetime.utcnow()

    # Mock role
    user.role = Mock()
    user.role.role_id = 1
    user.role.name = role

    return user


def generate_test_data(model: str, count: int = 10) -> List[Dict[str, Any]]:
    """Generate test data for a given model."""
    generators = {
        "user": lambda i: {
            "first_name": f"User{i}",
            "last_name": "Test",
            "email": f"user{i}@test.com",
            "document_number": f"{10000000 + i}",
            "password": "hashed_password",
            "active": True,
        },
        "program": lambda i: {
            "name": f"Program {i}",
            "duration": random.choice([12, 24, 36, 48]),
        },
        "instructor": lambda i: {
            "first_name": f"Instructor{i}",
            "last_name": "Test",
            "email": f"instructor{i}@test.com",
            "phone_number": f"+123456789{i}",
            "hour_count": 0,
            "active": True,
        },
        "classroom": lambda i: {
            "room_number": f"{random.choice(['A', 'B', 'C'])}{100 + i}",
            "capacity": random.randint(20, 50),
            "classroom_type": random.choice(["Standard", "Laboratory", "Workshop"]),
        },
    }

    generator = generators.get(model)
    if not generator:
        raise ValueError(f"No generator for model: {model}")

    return [generator(i) for i in range(count)]
