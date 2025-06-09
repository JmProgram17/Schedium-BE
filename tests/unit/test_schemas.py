"""
Unit tests for Pydantic schemas.
"""

from datetime import date, time

import pytest
from pydantic import ValidationError

from app.schemas.academic import LevelCreate, ProgramCreate, StudentGroupCreate
from app.schemas.auth import LoginRequest, UserCreate, UserUpdate
from app.schemas.hr import DepartmentCreate, InstructorCreate
from app.schemas.scheduling import QuarterCreate, ScheduleCreate, TimeBlockCreate


class TestAuthSchemas:
    """Test authentication schemas."""

    def test_user_create_valid(self):
        """Test valid user creation schema."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "document_number": "12345678",
            "password": "SecurePass123!",
            "role_id": 1,
        }

        user = UserCreate(**data)
        assert user.email == "john.doe@example.com"
        assert user.password == "SecurePass123!"

    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "document_number": "12345678",
            "password": "SecurePass123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("email",) for e in errors)

    def test_user_create_weak_password(self):
        """Test user creation with weak password."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "document_number": "12345678",
            "password": "weak",  # Too short, no uppercase, no digit
        }

        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_user_update_partial(self):
        """Test partial user update schema."""
        update = UserUpdate(first_name="Jane", active=False)

        assert update.first_name == "Jane"
        assert update.active is False
        assert update.last_name is None
        assert update.email is None


class TestAcademicSchemas:
    """Test academic domain schemas."""

    def test_student_group_date_validation(self):
        """Test student group date validation."""
        # Valid dates
        valid_data = {
            "group_number": 2750001,
            "program_id": 1,
            "start_date": date(2024, 1, 1),
            "end_date": date(2025, 12, 31),
            "capacity": 30,
            "schedule_id": 1,
        }

        group = StudentGroupCreate(**valid_data)
        assert group.end_date > group.start_date

        # Invalid dates (end before start)
        invalid_data = valid_data.copy()
        invalid_data["end_date"] = date(2023, 12, 31)

        with pytest.raises(ValidationError) as exc_info:
            StudentGroupCreate(**invalid_data)

        errors = exc_info.value.errors()
        assert any(e["msg"] == "End date must be after start date" for e in errors)

    def test_program_create_optional_fields(self):
        """Test program creation with optional fields."""
        data = {
            "name": "Test Program"
            # All other fields are optional
        }

        program = ProgramCreate(**data)
        assert program.name == "Test Program"
        assert program.nomenclature_id is None
        assert program.chain_id is None
        assert program.department_id is None
        assert program.level_id is None


class TestSchedulingSchemas:
    """Test scheduling domain schemas."""

    def test_schedule_time_validation(self):
        """Test schedule time validation."""
        # Valid times
        valid_data = {
            "name": "Morning",
            "start_time": time(7, 0),
            "end_time": time(13, 0),
        }

        schedule = ScheduleCreate(**valid_data)
        assert schedule.end_time > schedule.start_time

        # Invalid times (end before start)
        invalid_data = valid_data.copy()
        invalid_data["end_time"] = time(6, 0)

        with pytest.raises(ValidationError) as exc_info:
            ScheduleCreate(**invalid_data)

        errors = exc_info.value.errors()
        assert any("End time must be after start time" in str(e) for e in errors)

    def test_quarter_date_validation(self):
        """Test quarter date validation."""
        # Valid quarter
        valid_data = {"start_date": date(2024, 1, 1), "end_date": date(2024, 3, 31)}

        quarter = QuarterCreate(**valid_data)
        assert quarter.end_date > quarter.start_date

        # Invalid quarter (same dates)
        invalid_data = valid_data.copy()
        invalid_data["end_date"] = date(2024, 1, 1)

        with pytest.raises(ValidationError) as exc_info:
            QuarterCreate(**invalid_data)

        errors = exc_info.value.errors()
        assert any("End date must be after start date" in str(e) for e in errors)


class TestSchemaInheritance:
    """Test schema inheritance and base configurations."""

    def test_schema_from_orm_mode(self):
        """Test that schemas can be created from ORM objects."""
        from app.schemas.common import BaseSchema

        # Mock ORM object
        class MockORMObject:
            id = 1
            name = "Test"
            created_at = "2024-01-01T00:00:00"

        class TestSchema(BaseSchema):
            id: int
            name: str
            created_at: str

        # Should be able to create from ORM object
        schema = TestSchema.model_validate(MockORMObject())
        assert schema.id == 1
        assert schema.name == "Test"
