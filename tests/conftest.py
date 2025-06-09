"""
Global pytest configuration and fixtures.
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["APP_ENV"] = "testing"

from app.config import settings
from app.core.security import SecurityUtils
from app.database import Base, get_db
from app.main import app
from app.models import *  # Import all models

# Test database URL - use in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables for testing."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)

    session = TestSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def authorized_client(client: TestClient, test_user_admin) -> TestClient:
    """Create an authorized test client with admin token."""
    from app.services.auth import AuthService

    # Create token for admin user
    auth_service = AuthService(db_session)
    tokens = auth_service.create_tokens(test_user_admin.user_id)

    client.headers = {"Authorization": f"Bearer {tokens.access_token}"}

    return client


# User fixtures
@pytest.fixture
def test_role_admin(db_session: Session):
    """Create admin role."""
    from app.models.auth import Role

    role = Role(name="Administrator")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def test_role_coordinator(db_session: Session):
    """Create coordinator role."""
    from app.models.auth import Role

    role = Role(name="Coordinator")
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def test_user_admin(db_session: Session, test_role_admin):
    """Create test admin user."""
    from app.models.auth import User

    user = User(
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
        document_number="12345678",
        password=SecurityUtils.get_password_hash("Admin123!"),
        role_id=test_role_admin.role_id,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_coordinator(db_session: Session, test_role_coordinator):
    """Create test coordinator user."""
    from app.models.auth import User

    user = User(
        first_name="Coordinator",
        last_name="User",
        email="coordinator@test.com",
        document_number="87654321",
        password=SecurityUtils.get_password_hash("Coord123!"),
        role_id=test_role_coordinator.role_id,
        active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# Academic fixtures
@pytest.fixture
def test_level(db_session: Session):
    """Create test level."""
    from app.models.academic import Level

    level = Level(study_type="Technologist", duration=24)
    db_session.add(level)
    db_session.commit()
    db_session.refresh(level)
    return level


@pytest.fixture
def test_department(db_session: Session):
    """Create test department."""
    from app.models.hr import Department

    department = Department(
        name="Information Technology", email="it@test.com", phone_number="+1234567890"
    )
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


@pytest.fixture
def test_program(db_session: Session, test_level, test_department):
    """Create test program."""
    from app.models.academic import Nomenclature, Program

    # Create nomenclature first
    nomenclature = Nomenclature(
        code="ADSO", description="Software Development", active=True
    )
    db_session.add(nomenclature)
    db_session.commit()

    program = Program(
        name="Software Development Analysis",
        nomenclature_id=nomenclature.nomenclature_id,
        level_id=test_level.level_id,
        department_id=test_department.department_id,
    )
    db_session.add(program)
    db_session.commit()
    db_session.refresh(program)
    return program


# Helper fixtures
@pytest.fixture
def auth_headers(test_user_admin, db_session):
    """Get authorization headers for requests."""
    from app.services.auth import AuthService

    auth_service = AuthService(db_session)
    tokens = auth_service.create_tokens(test_user_admin.user_id)

    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing."""

    class MockDatetime:
        @staticmethod
        def utcnow():
            return datetime(2024, 1, 1, 12, 0, 0)

    monkeypatch.setattr("app.core.security.datetime", MockDatetime)
    return MockDatetime
