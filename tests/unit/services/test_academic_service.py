"""
Unit tests for academic service.
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.schemas.academic import (
    ChainCreate,
    LevelCreate,
    NomenclatureCreate,
    ProgramCreate,
    StudentGroupCreate,
    StudentGroupDisable,
)
from app.services.academic import AcademicService


class TestAcademicService:
    """Test academic service operations."""

    @pytest.fixture
    def academic_service(self, db_session):
        """Create academic service instance."""
        return AcademicService(db_session)

    def test_create_level_success(self, academic_service):
        """Test successful level creation."""
        level_data = LevelCreate(study_type="Professional", duration=48)

        level = academic_service.create_level(level_data)

        assert level.study_type == "Professional"
        assert level.duration == 48
        assert level.level_id is not None

    def test_create_level_duplicate_type(self, academic_service, test_level):
        """Test creating level with duplicate study type."""
        level_data = LevelCreate(
            study_type=test_level.study_type, duration=36  # Duplicate
        )

        with pytest.raises(ConflictException) as exc_info:
            academic_service.create_level(level_data)

        assert "already exists" in str(exc_info.value.detail).lower()

    def test_create_program_with_all_relations(
        self, academic_service, test_level, test_department
    ):
        """Test creating program with all relationships."""
        # Create nomenclature
        nom_data = NomenclatureCreate(
            code="TEST", description="Test Program", active=True
        )
        nomenclature = academic_service.create_nomenclature(nom_data)

        # Create chain
        chain_data = ChainCreate(name="Test Chain")
        chain = academic_service.create_chain(chain_data)

        # Create program
        program_data = ProgramCreate(
            name="Complete Test Program",
            nomenclature_id=nomenclature.nomenclature_id,
            chain_id=chain.chain_id,
            department_id=test_department.department_id,
            level_id=test_level.level_id,
        )

        program = academic_service.create_program(program_data)

        assert program.name == "Complete Test Program"
        assert program.nomenclature.code == "TEST"
        assert program.chain.name == "Test Chain"
        assert program.level.level_id == test_level.level_id
        assert program.department is not None

    def test_create_student_group_validation(self, academic_service, test_program):
        """Test student group creation with validations."""
        from app.models.scheduling import Schedule

        # Create schedule
        schedule = Schedule(
            name="Test Schedule", start_time="08:00:00", end_time="14:00:00"
        )
        academic_service.db.add(schedule)
        academic_service.db.commit()

        # Test with invalid dates
        group_data = StudentGroupCreate(
            group_number=2750999,
            program_id=test_program.program_id,
            start_date=date(2024, 12, 31),
            end_date=date(2024, 1, 1),  # Before start date
            capacity=30,
            schedule_id=schedule.schedule_id,
        )

        with pytest.raises(BadRequestException) as exc_info:
            academic_service.create_student_group(group_data)

        assert "End date must be after start date" in str(exc_info.value.detail)

    def test_disable_student_group(self, academic_service, test_program):
        """Test disabling a student group."""
        from app.models.scheduling import Schedule

        # Create schedule
        schedule = Schedule(
            name="Test Schedule", start_time="08:00:00", end_time="14:00:00"
        )
        academic_service.db.add(schedule)
        academic_service.db.commit()

        # Create active group
        group_data = StudentGroupCreate(
            group_number=2750888,
            program_id=test_program.program_id,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31),
            capacity=30,
            schedule_id=schedule.schedule_id,
            active=True,
        )
        group = academic_service.create_student_group(group_data)

        # Disable it
        disable_data = StudentGroupDisable(reason="Test disable")
        disabled_group = academic_service.disable_student_group(
            group.group_id, disable_data
        )

        assert disabled_group.active is False

    def test_delete_level_with_programs_fails(
        self, academic_service, test_level, test_program
    ):
        """Test that deleting level with programs fails."""
        with pytest.raises(BadRequestException) as exc_info:
            academic_service.delete_level(test_level.level_id)

        assert "Cannot delete level" in str(exc_info.value.detail)
        assert "programs use this level" in str(exc_info.value.detail)

    def test_update_nomenclature_code_conflict(self, academic_service):
        """Test updating nomenclature with conflicting code."""
        # Create two nomenclatures
        nom1 = academic_service.create_nomenclature(
            NomenclatureCreate(code="NOM1", description="First")
        )
        nom2 = academic_service.create_nomenclature(
            NomenclatureCreate(code="NOM2", description="Second")
        )

        # Try to update nom2 with nom1's code
        from app.schemas.academic import NomenclatureUpdate

        with pytest.raises(ConflictException) as exc_info:
            academic_service.update_nomenclature(
                nom2.nomenclature_id, NomenclatureUpdate(code="NOM1")
            )

        assert "already exists" in str(exc_info.value.detail).lower()
