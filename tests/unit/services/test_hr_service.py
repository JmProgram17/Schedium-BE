"""
Unit tests for HR service.
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import BadRequestException, ConflictException
from app.schemas.hr import (
    ContractCreate,
    DepartmentCreate,
    InstructorCreate,
    InstructorUpdate,
)
from app.services.hr import HRService


class TestHRService:
    """Test HR service operations."""

    @pytest.fixture
    def hr_service(self, db_session):
        """Create HR service instance."""
        return HRService(db_session)

    def test_create_department_success(self, hr_service):
        """Test successful department creation."""
        dept_data = DepartmentCreate(
            name="Engineering Department",
            email="engineering@test.com",
            phone_number="+1234567890",
        )

        department = hr_service.create_department(dept_data)

        assert department.name == "Engineering Department"
        assert department.email == "engineering@test.com"
        assert department.department_id is not None

    def test_create_contract_with_hour_limit(self, hr_service):
        """Test creating contract with hour limit."""
        contract_data = ContractCreate(contract_type="Part Time", hour_limit=20)

        contract = hr_service.create_contract(contract_data)

        assert contract.contract_type == "Part Time"
        assert contract.hour_limit == 20

    def test_create_instructor_email_validation(self, hr_service):
        """Test instructor creation with email validation."""
        instructor_data = InstructorCreate(
            first_name="Invalid",
            last_name="Email",
            email="not-an-email",  # Invalid
            phone_number="+1234567890",
        )

        # Should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            hr_service.create_instructor(instructor_data)

    def test_instructor_workload_calculation(self, hr_service, test_department):
        """Test instructor workload calculation."""
        # Create contract with hour limit
        contract_data = ContractCreate(contract_type="Full Time", hour_limit=40)
        contract = hr_service.create_contract(contract_data)

        # Create instructor
        instructor_data = InstructorCreate(
            first_name="Test",
            last_name="Instructor",
            email="instructor@test.com",
            phone_number="+1234567890",
            contract_id=contract.contract_id,
            department_id=test_department.department_id,
        )
        instructor = hr_service.create_instructor(instructor_data)

        # Get workload
        workload = hr_service.get_instructor_workload(instructor.instructor_id)

        assert workload.instructor_id == instructor.instructor_id
        assert workload.total_hours == 0  # No classes assigned yet
        assert workload.contract_limit == 40
        assert workload.available_hours == 40
        assert workload.utilization_percentage == 0
        assert workload.status == "LOW_LOAD"

    def test_update_instructor_email_conflict(self, hr_service, test_department):
        """Test updating instructor with conflicting email."""
        # Create two instructors
        inst1_data = InstructorCreate(
            first_name="First",
            last_name="Instructor",
            email="first@test.com",
            department_id=test_department.department_id,
        )
        _ = hr_service.create_instructor(inst1_data)

        inst2_data = InstructorCreate(
            first_name="Second",
            last_name="Instructor",
            email="second@test.com",
            department_id=test_department.department_id,
        )
        inst2 = hr_service.create_instructor(inst2_data)

        # Try to update inst2 with inst1's email
        with pytest.raises(ConflictException) as exc_info:
            hr_service.update_instructor(
                inst2.instructor_id, InstructorUpdate(email="first@test.com")
            )

        assert "already taken" in str(exc_info.value.detail).lower()

    def test_delete_department_with_instructors_fails(
        self, hr_service, test_department
    ):
        """Test that deleting department with instructors fails."""
        # Create instructor in department
        instructor_data = InstructorCreate(
            first_name="Dept",
            last_name="Instructor",
            email="dept.instructor@test.com",
            department_id=test_department.department_id,
        )
        hr_service.create_instructor(instructor_data)

        # Try to delete department
        with pytest.raises(BadRequestException) as exc_info:
            hr_service.delete_department(test_department.department_id)

        assert "Cannot delete department" in str(exc_info.value.detail)
        assert "instructors belong to it" in str(exc_info.value.detail)

    def test_instructor_workload_status_levels(self, hr_service):
        """Test different workload status levels."""
        from app.repositories.hr import InstructorRepository

        # Mock workload data for different scenarios
        scenarios = [
            (0, 40, "LOW_LOAD"),
            (20, 40, "MEDIUM_LOAD"),
            (30, 40, "HIGH_LOAD"),
            (38, 40, "NEAR_LIMIT"),
            (42, 40, "OVERLOADED"),
            (20, None, "NO_LIMIT"),
        ]

        for hours, limit, expected_status in scenarios:
            # Mock the repository method
            with patch.object(
                InstructorRepository,
                "get_workload_summary",
                return_value={
                    "instructor_id": 1,
                    "full_name": "Test Instructor",
                    "total_hours": float(hours),
                    "contract_limit": limit,
                    "available_hours": float(limit - hours) if limit else None,
                    "utilization_percentage": (
                        float(hours / limit * 100) if limit else None
                    ),
                },
            ):
                workload = hr_service.get_instructor_workload(1)
                assert workload.status == expected_status
