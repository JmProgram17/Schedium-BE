"""
Pytest configuration and fixtures.
Provides common test utilities and fixtures.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Create test database URL
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.DB_NAME, 
    f"{settings.DB_NAME}_test"
)

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

# Create test session
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="session")
def setup_test_db():
    """Create test database and tables."""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db(setup_test_db) -> Generator[Session, None, None]:
    """Get test database session."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """Get test client with overridden database."""
    
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Get authentication headers for testing."""
    # Create test user and login
    # This will be implemented when auth is ready
    return {"Authorization": "Bearer test-token"}


# Test data fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "document_number": "12345678",
        "password": "TestPass123!",
        "role_id": 1
    }


@pytest.fixture
def sample_instructor_data():
    """Sample instructor data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "+573001234567",
        "contract_id": 1,
        "department_id": 1
    }


@pytest.fixture
def sample_classroom_data():
    """Sample classroom data for testing."""
    return {
        "room_number": "A101",
        "capacity": 30,
        "campus_id": 1,
        "classroom_type": "Laboratory"
    }