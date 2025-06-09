"""
Unit tests for authentication service.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.schemas.auth import RoleCreate, UserCreate, UserUpdate
from app.services.auth import AuthService


class TestAuthService:
    """Test authentication service."""

    @pytest.fixture
    def auth_service(self, db_session):
        """Create auth service instance."""
        return AuthService(db_session)

    @pytest.fixture
    def mock_user_repo(self):
        """Create mock user repository."""
        with patch("app.services.auth.UserRepository") as mock:
            yield mock.return_value

    @pytest.fixture
    def mock_role_repo(self):
        """Create mock role repository."""
        with patch("app.services.auth.RoleRepository") as mock:
            yield mock.return_value

    def test_authenticate_user_success(self, auth_service, test_user_admin):
        """Test successful user authentication."""
        user = auth_service.authenticate_user(
            email="admin@test.com", password="Admin123!"
        )

        assert user is not None
        assert user.email == "admin@test.com"
        assert user.user_id == test_user_admin.user_id

    def test_authenticate_user_wrong_password(self, auth_service, test_user_admin):
        """Test authentication with wrong password."""
        user = auth_service.authenticate_user(
            email="admin@test.com", password="WrongPassword"
        )

        assert user is None

    def test_authenticate_user_not_found(self, auth_service):
        """Test authentication with non-existent user."""
        user = auth_service.authenticate_user(
            email="nonexistent@test.com", password="Password123!"
        )

        assert user is None

    def test_authenticate_inactive_user(
        self, auth_service, db_session, test_role_admin
    ):
        """Test authentication with inactive user."""
        from app.core.security import SecurityUtils
        from app.models.auth import User

        # Create inactive user
        inactive_user = User(
            first_name="Inactive",
            last_name="User",
            email="inactive@test.com",
            document_number="99999999",
            password=SecurityUtils.get_password_hash("Test123!"),
            role_id=test_role_admin.role_id,
            active=False,
        )
        db_session.add(inactive_user)
        db_session.commit()

        # Try to authenticate
        with pytest.raises(UnauthorizedException) as exc_info:
            auth_service.authenticate_user(
                email="inactive@test.com", password="Test123!"
            )

        assert "inactive" in str(exc_info.value.detail).lower()

    def test_create_user_email_conflict(self, auth_service, test_user_admin):
        """Test creating user with existing email."""
        user_data = UserCreate(
            first_name="New",
            last_name="User",
            email="admin@test.com",  # Already exists
            document_number="88888888",
            password="NewUser123!",
            role_id=test_user_admin.role_id,
        )

        with pytest.raises(ConflictException) as exc_info:
            auth_service.create_user(user_data)

        assert "email" in str(exc_info.value.detail).lower()

    def test_create_tokens(self, auth_service, test_user_admin):
        """Test token creation for user."""
        tokens = auth_service.create_tokens(test_user_admin.user_id)

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

        # Tokens should be different
        assert tokens.access_token != tokens.refresh_token

    def test_refresh_access_token_valid(self, auth_service, test_user_admin):
        """Test refreshing access token with valid refresh token."""
        # Get initial tokens
        initial_tokens = auth_service.create_tokens(test_user_admin.user_id)

        # Refresh token
        new_tokens = auth_service.refresh_access_token(initial_tokens.refresh_token)

        assert new_tokens.access_token is not None
        assert new_tokens.access_token != initial_tokens.access_token

    def test_refresh_access_token_invalid(self, auth_service):
        """Test refreshing with invalid refresh token."""
        with pytest.raises(UnauthorizedException):
            auth_service.refresh_access_token("invalid.refresh.token")

    def test_change_password_success(self, auth_service, test_user_admin):
        """Test successful password change."""
        success = auth_service.change_password(
            user_id=test_user_admin.user_id,
            current_password="Admin123!",
            new_password="NewAdmin123!",
        )

        assert success is True

        # Verify can login with new password
        user = auth_service.authenticate_user(
            email="admin@test.com", password="NewAdmin123!"
        )
        assert user is not None

    def test_change_password_wrong_current(self, auth_service, test_user_admin):
        """Test password change with wrong current password."""
        with pytest.raises(BadRequestException) as exc_info:
            auth_service.change_password(
                user_id=test_user_admin.user_id,
                current_password="WrongPassword",
                new_password="NewAdmin123!",
            )

        assert "incorrect" in str(exc_info.value.detail).lower()

    def test_delete_last_admin_fails(self, auth_service, test_user_admin):
        """Test that deleting the last admin fails."""
        with pytest.raises(BadRequestException) as exc_info:
            auth_service.delete_user(test_user_admin.user_id)

        assert "last administrator" in str(exc_info.value.detail).lower()

    def test_create_role_duplicate_name(self, auth_service, test_role_admin):
        """Test creating role with duplicate name."""
        role_data = RoleCreate(name="Administrator")  # Already exists

        with pytest.raises(ConflictException) as exc_info:
            auth_service.create_role(role_data)

        assert "already exists" in str(exc_info.value.detail).lower()
