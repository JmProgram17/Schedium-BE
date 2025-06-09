"""
Integration tests for database connectivity and operations.
"""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal, engine
from app.models import Base


class TestDatabaseConnectivity:
    """Test database connection and basic operations."""

    def test_database_connection(self):
        """Test basic database connectivity."""
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_all_tables_created(self):
        """Test that all expected tables are created."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "user",
            "role",
            "level",
            "chain",
            "nomenclature",
            "program",
            "student_group",
            "department",
            "contract",
            "instructor",
            "campus",
            "classroom",
            "department_classroom",
            "schedule",
            "time_block",
            "day",
            "day_time_block",
            "quarter",
            "class_schedule",
        ]

        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found in database"

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        db = SessionLocal()

        try:
            from app.models.auth import User

            # Try to create user with non-existent role
            invalid_user = User(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                document_number="12345678",
                password="hashed",
                role_id=9999,  # Non-existent role
            )

            db.add(invalid_user)
            with pytest.raises(IntegrityError):
                db.commit()

        finally:
            db.rollback()
            db.close()

    def test_unique_constraints(self):
        """Test that unique constraints are enforced."""
        db = SessionLocal()

        try:
            from app.models.auth import Role

            # Create first role
            role1 = Role(name="UniqueRole")
            db.add(role1)
            db.commit()

            # Try to create duplicate role
            role2 = Role(name="UniqueRole")
            db.add(role2)

            with pytest.raises(IntegrityError):
                db.commit()

        finally:
            db.rollback()
            db.close()


class TestDatabaseTransactions:
    """Test database transaction behavior."""

    def test_transaction_rollback(self, db_session):
        """Test that transactions properly rollback on error."""
        from app.models.auth import Role, User

        # Create a role
        role = Role(name="TestRole")
        db_session.add(role)
        db_session.commit()

        initial_user_count = db_session.query(User).count()

        try:
            # Start transaction
            user1 = User(
                first_name="User1",
                last_name="Test",
                email="user1@test.com",
                document_number="11111111",
                password="password",
                role_id=role.role_id,
            )
            db_session.add(user1)

            # This should fail due to duplicate email
            user2 = User(
                first_name="User2",
                last_name="Test",
                email="user1@test.com",  # Duplicate
                document_number="22222222",
                password="password",
                role_id=role.role_id,
            )
            db_session.add(user2)
            db_session.commit()

        except IntegrityError:
            db_session.rollback()

        # Verify no users were added
        final_user_count = db_session.query(User).count()
        assert final_user_count == initial_user_count

    def test_cascade_delete_behavior(self, db_session):
        """Test cascade delete configuration."""
        from app.models.academic import Program, StudentGroup
        from app.models.scheduling import Schedule

        # Create program
        program = Program(name="Test Program")
        db_session.add(program)
        db_session.commit()

        # Create schedule
        schedule = Schedule(
            name="Test Schedule", start_time="08:00:00", end_time="14:00:00"
        )
        db_session.add(schedule)
        db_session.commit()

        # Create student group
        group = StudentGroup(
            group_number=999999,
            program_id=program.program_id,
            start_date="2024-01-01",
            end_date="2025-12-31",
            capacity=30,
            schedule_id=schedule.schedule_id,
        )
        db_session.add(group)
        db_session.commit()

        # Delete program should fail due to RESTRICT
        db_session.delete(program)
        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()

        # Verify program and group still exist
        assert db_session.query(Program).get(program.program_id) is not None
        assert db_session.query(StudentGroup).get(group.group_id) is not None
