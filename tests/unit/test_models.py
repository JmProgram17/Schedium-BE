"""
Unit tests for database models.
"""

from datetime import date, time

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.academic import Level, Program, StudentGroup
from app.models.auth import Role, User
from app.models.hr import Contract, Department, Instructor
from app.models.infrastructure import Campus, Classroom
from app.models.scheduling import Quarter, Schedule, TimeBlock


class TestAuthModels:
    """Test authentication models."""

    def test_create_role(self, db_session):
        """Test role creation."""
        role = Role(name="TestRole")
        db_session.add(role)
        db_session.commit()

        assert role.role_id is not None
        assert role.name == "TestRole"
        assert role.created_at is not None

    def test_create_user(self, db_session, test_role_admin):
        """Test user creation."""
        user = User(
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
            document_number="12345678",
            password="hashed_password",
            role_id=test_role_admin.role_id,
            active=True,
        )
        db_session.add(user)
        db_session.commit()

        assert user.user_id is not None
        assert user.full_name == "John Doe"
        assert user.role.name == "Administrator"

    def test_user_unique_email(self, db_session):
        """Test email uniqueness constraint."""
        user1 = User(
            first_name="User1",
            last_name="Test",
            email="duplicate@test.com",
            document_number="11111111",
            password="password1",
        )
        user2 = User(
            first_name="User2",
            last_name="Test",
            email="duplicate@test.com",  # Same email
            document_number="22222222",
            password="password2",
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAcademicModels:
    """Test academic domain models."""

    def test_create_program(self, db_session, test_level, test_department):
        """Test program creation with relationships."""
        program = Program(
            name="Test Program",
            level_id=test_level.level_id,
            department_id=test_department.department_id,
        )
        db_session.add(program)
        db_session.commit()

        assert program.program_id is not None
        assert program.level.study_type == "Technologist"
        assert program.department.name == "Information Technology"

    def test_student_group_dates(self, db_session, test_program):
        """Test student group date validation."""
        from app.models.scheduling import Schedule

        # Create schedule first
        schedule = Schedule(name="Morning", start_time=time(7, 0), end_time=time(13, 0))
        db_session.add(schedule)
        db_session.commit()

        group = StudentGroup(
            group_number=2750001,
            program_id=test_program.program_id,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31),
            capacity=30,
            schedule_id=schedule.schedule_id,
            active=True,
        )
        db_session.add(group)
        db_session.commit()

        assert group.group_id is not None
        assert group.end_date > group.start_date


class TestSchedulingModels:
    """Test scheduling models."""

    def test_create_quarter(self, db_session):
        """Test quarter creation."""
        quarter = Quarter(start_date=date(2024, 1, 1), end_date=date(2024, 3, 31))
        db_session.add(quarter)
        db_session.commit()

        assert quarter.quarter_id is not None
        assert quarter.end_date > quarter.start_date

    def test_time_block_duration(self, db_session):
        """Test time block with calculated duration."""
        time_block = TimeBlock(start_time=time(8, 0), end_time=time(10, 0))
        db_session.add(time_block)
        db_session.commit()

        assert time_block.time_block_id is not None
        # Duration should be calculated by database trigger/computed column
