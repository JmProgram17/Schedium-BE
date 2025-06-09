"""
Integration tests for repositories.
"""

from datetime import date

import pytest

from app.core.pagination import PaginationParams
from app.repositories.academic import ProgramRepository, StudentGroupRepository
from app.repositories.auth import RoleRepository, UserRepository
from app.repositories.hr import DepartmentRepository, InstructorRepository
from app.schemas.academic import ProgramCreate, StudentGroupCreate
from app.schemas.auth import UserCreate


class TestUserRepository:
    """Test user repository operations."""

    def test_create_user(self, db_session, test_role_admin):
        """Test creating user through repository."""
        user_repo = UserRepository(db_session)

        user_data = UserCreate(
            first_name="Repo",
            last_name="Test",
            email="repo@test.com",
            document_number="99999999",
            password="RepoTest123!",
            role_id=test_role_admin.role_id,
        )

        user = user_repo.create(obj_in=user_data)

        assert user.user_id is not None
        assert user.email == "repo@test.com"
        assert user.role_id == test_role_admin.role_id

    def test_search_users(self, db_session, test_user_admin, test_user_coordinator):
        """Test searching users with filters."""
        user_repo = UserRepository(db_session)

        # Search by email
        params = PaginationParams(page=1, page_size=10)
        result = user_repo.search_users(params, search="admin")

        assert result.total >= 1
        assert any(u.email == "admin@test.com" for u in result.items)

    def test_update_last_login(self, db_session, test_user_admin):
        """Test updating user's last login."""
        user_repo = UserRepository(db_session)

        # Initial last login should be None
        assert test_user_admin.last_login is None

        # Update last login
        success = user_repo.update_last_login(test_user_admin.user_id)
        assert success is True

        # Verify update
        updated_user = user_repo.get(test_user_admin.user_id)
        assert updated_user.last_login is not None


class TestProgramRepository:
    """Test program repository operations."""

    def test_search_programs_with_relations(self, db_session, test_program):
        """Test searching programs with loaded relationships."""
        program_repo = ProgramRepository(db_session)

        params = PaginationParams(page=1, page_size=10)
        result = program_repo.search_programs(params, search="Software")

        assert result.total >= 1
        assert result.items[0].nomenclature is not None
        assert result.items[0].department is not None
        assert result.items[0].level is not None

    def test_filter_programs_by_department(self, db_session, test_program):
        """Test filtering programs by department."""
        program_repo = ProgramRepository(db_session)

        params = PaginationParams(page=1, page_size=10)
        result = program_repo.search_programs(
            params, department_id=test_program.department_id
        )

        assert result.total >= 1
        assert all(p.department_id == test_program.department_id for p in result.items)


class TestTransactionRollback:
    """Test transaction rollback behavior."""

    def test_rollback_on_error(self, db_session):
        """Test that transactions rollback on error."""
        user_repo = UserRepository(db_session)

        # Count initial users
        initial_count = user_repo.count()

        try:
            # Create user with invalid data
            _ = user_repo.create(
                obj_in=UserCreate(
                    first_name="Test",
                    last_name="User",
                    email="invalid",  # Invalid email
                    document_number="12345678",
                    password="Test123!",
                )
            )
            db_session.commit()
        except Exception:
            db_session.rollback()

        # Count should remain the same
        final_count = user_repo.count()
        assert final_count == initial_count
