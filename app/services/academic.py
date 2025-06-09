"""
Academic domain services.
Handles business logic for academic entities.
"""

from datetime import date
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.core.pagination import Page, PaginationParams
from app.models.academic import Chain, Level, Nomenclature, Program, StudentGroup
from app.repositories.academic import (
    ChainRepository,
    LevelRepository,
    NomenclatureRepository,
    ProgramRepository,
    StudentGroupRepository,
)
from app.schemas.academic import Chain as ChainSchema
from app.schemas.academic import ChainCreate, ChainUpdate
from app.schemas.academic import Level as LevelSchema
from app.schemas.academic import LevelCreate, LevelUpdate
from app.schemas.academic import Nomenclature as NomenclatureSchema
from app.schemas.academic import NomenclatureCreate, NomenclatureUpdate
from app.schemas.academic import Program as ProgramSchema
from app.schemas.academic import ProgramCreate, ProgramUpdate
from app.schemas.academic import StudentGroup as StudentGroupSchema
from app.schemas.academic import (
    StudentGroupCreate,
    StudentGroupDisable,
    StudentGroupUpdate,
)


class AcademicService:
    """Service for academic domain operations."""

    def __init__(self, db: Session):
        self.db = db
        self.level_repo = LevelRepository(db)
        self.chain_repo = ChainRepository(db)
        self.nomenclature_repo = NomenclatureRepository(db)
        self.program_repo = ProgramRepository(db)
        self.group_repo = StudentGroupRepository(db)

    # Level operations
    def create_level(self, level_in: LevelCreate) -> LevelSchema:
        """Create a new level."""
        # Check if study type already exists
        existing = self.level_repo.get_by_study_type(level_in.study_type)
        if existing:
            raise ConflictException(
                detail=f"Level with study type '{level_in.study_type}' already exists",
                error_code="LEVEL_EXISTS",
            )

        level = self.level_repo.create(obj_in=level_in)
        return LevelSchema.model_validate(level)

    def get_level(self, level_id: int) -> LevelSchema:
        """Get level by ID."""
        level = self.level_repo.get_or_404(level_id)
        return LevelSchema.model_validate(level)

    def get_levels(self, params: PaginationParams) -> Page[LevelSchema]:
        """Get paginated list of levels."""
        page = self.level_repo.get_paginated(params)
        page.items = [LevelSchema.model_validate(item) for item in page.items]
        return page

    def update_level(self, level_id: int, level_in: LevelUpdate) -> LevelSchema:
        """Update level."""
        level = self.level_repo.get_or_404(level_id)
        updated_level = self.level_repo.update(db_obj=level, obj_in=level_in)
        return LevelSchema.model_validate(updated_level)

    def delete_level(self, level_id: int) -> None:
        """Delete level."""
        _ = self.level_repo.get_or_404(level_id)

        # Check if level is in use
        programs_count = self.level_repo.get_programs_count(level_id)
        if programs_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete level. {programs_count} programs use this level",
                error_code="LEVEL_IN_USE",
            )

        self.level_repo.delete(id=level_id)

    # Chain operations
    def create_chain(self, chain_in: ChainCreate) -> ChainSchema:
        """Create a new chain."""
        # Check if name already exists
        existing = self.chain_repo.get_by_name(chain_in.name)
        if existing:
            raise ConflictException(
                detail=f"Chain '{chain_in.name}' already exists",
                error_code="CHAIN_EXISTS",
            )

        chain = self.chain_repo.create(obj_in=chain_in)
        return ChainSchema.model_validate(chain)

    def get_chain(self, chain_id: int) -> ChainSchema:
        """Get chain by ID."""
        chain = self.chain_repo.get_or_404(chain_id)
        return ChainSchema.model_validate(chain)

    def get_chains(self, params: PaginationParams) -> Page[ChainSchema]:
        """Get paginated list of chains."""
        page = self.chain_repo.get_paginated(params)
        page.items = [ChainSchema.model_validate(item) for item in page.items]
        return page

    def update_chain(self, chain_id: int, chain_in: ChainUpdate) -> ChainSchema:
        """Update chain."""
        chain = self.chain_repo.get_or_404(chain_id)

        # Check uniqueness if name changed
        if chain_in.name and chain_in.name != chain.name:
            existing = self.chain_repo.get_by_name(chain_in.name)
            if existing:
                raise ConflictException(
                    detail=f"Chain '{chain_in.name}' already exists",
                    error_code="CHAIN_EXISTS",
                )

        updated_chain = self.chain_repo.update(db_obj=chain, obj_in=chain_in)
        return ChainSchema.model_validate(updated_chain)

    def delete_chain(self, chain_id: int) -> None:
        """Delete chain."""
        _ = self.chain_repo.get_or_404(chain_id)

        # Check if chain is in use
        programs_count = self.chain_repo.get_programs_count(chain_id)
        if programs_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete chain. {programs_count} programs use this chain",
                error_code="CHAIN_IN_USE",
            )

        self.chain_repo.delete(id=chain_id)

    # Nomenclature operations
    def create_nomenclature(self, nom_in: NomenclatureCreate) -> NomenclatureSchema:
        """Create a new nomenclature."""
        # Check if code already exists
        existing = self.nomenclature_repo.get_by_code(nom_in.code)
        if existing:
            raise ConflictException(
                detail=f"Nomenclature with code '{nom_in.code}' already exists",
                error_code="NOMENCLATURE_EXISTS",
            )

        nomenclature = self.nomenclature_repo.create(obj_in=nom_in)
        return NomenclatureSchema.model_validate(nomenclature)

    def get_nomenclature(self, nomenclature_id: int) -> NomenclatureSchema:
        """Get nomenclature by ID."""
        nomenclature = self.nomenclature_repo.get_or_404(nomenclature_id)
        return NomenclatureSchema.model_validate(nomenclature)

    def get_nomenclatures(
        self, params: PaginationParams, active_only: bool = False
    ) -> Page[NomenclatureSchema]:
        """Get paginated list of nomenclatures."""
        filters = {"active": True} if active_only else None
        page = self.nomenclature_repo.get_paginated(params, filters=filters)
        page.items = [NomenclatureSchema.model_validate(item) for item in page.items]
        return page

    def update_nomenclature(
        self, nomenclature_id: int, nom_in: NomenclatureUpdate
    ) -> NomenclatureSchema:
        """Update nomenclature."""
        nomenclature = self.nomenclature_repo.get_or_404(nomenclature_id)

        # Check uniqueness if code changed
        if nom_in.code and nom_in.code != nomenclature.code:
            existing = self.nomenclature_repo.get_by_code(nom_in.code)
            if existing:
                raise ConflictException(
                    detail=f"Nomenclature with code '{nom_in.code}' already exists",
                    error_code="NOMENCLATURE_EXISTS",
                )

        updated_nomenclature = self.nomenclature_repo.update(
            db_obj=nomenclature, obj_in=nom_in
        )
        return NomenclatureSchema.model_validate(updated_nomenclature)

    def delete_nomenclature(self, nomenclature_id: int) -> None:
        """Delete nomenclature."""
        _ = self.nomenclature_repo.get_or_404(nomenclature_id)

        # Check if nomenclature is in use
        programs_count = self.nomenclature_repo.get_programs_count(nomenclature_id)
        if programs_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete nomenclature. {programs_count} programs use this code",
                error_code="NOMENCLATURE_IN_USE",
            )

        self.nomenclature_repo.delete(id=nomenclature_id)

    # Program operations
    def create_program(self, program_in: ProgramCreate) -> ProgramSchema:
        """Create a new program."""
        # Validate foreign keys
        if program_in.nomenclature_id:
            self.nomenclature_repo.get_or_404(program_in.nomenclature_id)

        if program_in.chain_id:
            self.chain_repo.get_or_404(program_in.chain_id)

        if program_in.department_id:
            from app.repositories.hr import DepartmentRepository

            dept_repo = DepartmentRepository(self.db)
            dept_repo.get_or_404(program_in.department_id)

        if program_in.level_id:
            self.level_repo.get_or_404(program_in.level_id)

        program = self.program_repo.create(obj_in=program_in)
        program = self.program_repo.get_with_relations(program.program_id)
        return ProgramSchema.model_validate(program)

    def get_program(self, program_id: int) -> ProgramSchema:
        """Get program by ID."""
        program = self.program_repo.get_with_relations(program_id)
        if not program:
            raise NotFoundException(f"Program with id {program_id} not found")
        return ProgramSchema.model_validate(program)

    def get_programs(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        level_id: Optional[int] = None,
        chain_id: Optional[int] = None,
    ) -> Page[ProgramSchema]:
        """Get paginated list of programs."""
        page = self.program_repo.search_programs(
            params, search, department_id, level_id, chain_id
        )
        page.items = [ProgramSchema.model_validate(item) for item in page.items]
        return page

    def update_program(
        self, program_id: int, program_in: ProgramUpdate
    ) -> ProgramSchema:
        """Update program."""
        program = self.program_repo.get_or_404(program_id)

        # Validate foreign keys if changed
        if program_in.nomenclature_id is not None:
            if program_in.nomenclature_id:
                self.nomenclature_repo.get_or_404(program_in.nomenclature_id)

        if program_in.chain_id is not None:
            if program_in.chain_id:
                self.chain_repo.get_or_404(program_in.chain_id)

        if program_in.department_id is not None:
            if program_in.department_id:
                from app.repositories.hr import DepartmentRepository

                dept_repo = DepartmentRepository(self.db)
                dept_repo.get_or_404(program_in.department_id)

        if program_in.level_id is not None:
            if program_in.level_id:
                self.level_repo.get_or_404(program_in.level_id)

        self.program_repo.update(db_obj=program, obj_in=program_in)
        updated_program = self.program_repo.get_with_relations(program_id)
        return ProgramSchema.model_validate(updated_program)

    def delete_program(self, program_id: int) -> None:
        """Delete program."""
        _ = self.program_repo.get_or_404(program_id)

        # Check if program has student groups
        groups_count = self.program_repo.get_student_groups_count(program_id)
        if groups_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete program. {groups_count} student groups are assigned",
                error_code="PROGRAM_HAS_GROUPS",
            )

        self.program_repo.delete(id=program_id)

    # Student Group operations
    def create_student_group(self, group_in: StudentGroupCreate) -> StudentGroupSchema:
        """Create a new student group."""
        # Check if group number already exists
        existing = self.group_repo.get_by_number(group_in.group_number)
        if existing:
            raise ConflictException(
                detail=f"Group number {group_in.group_number} already exists",
                error_code="GROUP_NUMBER_EXISTS",
            )

        # Validate dates
        if group_in.end_date <= group_in.start_date:
            raise BadRequestException(
                detail="End date must be after start date",
                error_code="INVALID_DATE_RANGE",
            )

        # Validate foreign keys
        self.program_repo.get_or_404(group_in.program_id)

        from app.repositories.scheduling import ScheduleRepository

        schedule_repo = ScheduleRepository(self.db)
        schedule_repo.get_or_404(group_in.schedule_id)

        group = self.group_repo.create(obj_in=group_in)
        group = self.group_repo.get_with_relations(group.group_id)
        return StudentGroupSchema.model_validate(group)

    def get_student_group(self, group_id: int) -> StudentGroupSchema:
        """Get student group by ID."""
        group = self.group_repo.get_with_relations(group_id)
        if not group:
            raise NotFoundException(f"Student group with id {group_id} not found")
        return StudentGroupSchema.model_validate(group)

    def get_student_groups(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        program_id: Optional[int] = None,
        schedule_id: Optional[int] = None,
        active: Optional[bool] = None,
        start_date_from: Optional[date] = None,
        start_date_to: Optional[date] = None,
    ) -> Page[StudentGroupSchema]:
        """Get paginated list of student groups."""
        page = self.group_repo.search_groups(
            params,
            search,
            program_id,
            schedule_id,
            active,
            start_date_from,
            start_date_to,
        )
        page.items = [StudentGroupSchema.model_validate(item) for item in page.items]
        return page

    def update_student_group(
        self, group_id: int, group_in: StudentGroupUpdate
    ) -> StudentGroupSchema:
        """Update student group."""
        group = self.group_repo.get_or_404(group_id)

        # Check uniqueness if group number changed
        if group_in.group_number and group_in.group_number != group.group_number:
            existing = self.group_repo.get_by_number(group_in.group_number)
            if existing:
                raise ConflictException(
                    detail=f"Group number {group_in.group_number} already exists",
                    error_code="GROUP_NUMBER_EXISTS",
                )

        # Validate dates if provided
        update_data = group_in.model_dump(exclude_unset=True)
        start_date = update_data.get("start_date", group.start_date)
        end_date = update_data.get("end_date", group.end_date)

        if end_date <= start_date:
            raise BadRequestException(
                detail="End date must be after start date",
                error_code="INVALID_DATE_RANGE",
            )

        # Validate foreign keys if changed
        if group_in.program_id is not None:
            self.program_repo.get_or_404(group_in.program_id)

        if group_in.schedule_id is not None:
            from app.repositories.scheduling import ScheduleRepository

            schedule_repo = ScheduleRepository(self.db)
            schedule_repo.get_or_404(group_in.schedule_id)

        group = self.group_repo.update(db_obj=group, obj_in=group_in)
        group = self.group_repo.get_with_relations(group_id)
        return StudentGroupSchema.model_validate(group)

    def disable_student_group(
        self, group_id: int, disable_data: StudentGroupDisable
    ) -> StudentGroupSchema:
        """Disable a student group (soft delete)."""
        group = self.group_repo.get_or_404(group_id)

        if not group.active:
            raise BadRequestException(
                detail="Group is already disabled", error_code="GROUP_ALREADY_DISABLED"
            )

        # Check if group has active schedules
        schedules_count = self.group_repo.get_schedules_count(group_id)
        if schedules_count > 0:
            raise BadRequestException(
                detail=f"Cannot disable group. {schedules_count} class schedules exist",
                error_code="GROUP_HAS_SCHEDULES",
            )

        group = self.group_repo.disable_group(group_id)
        return StudentGroupSchema.model_validate(group)

    def delete_student_group(self, group_id: int) -> None:
        """Delete student group (admin only)."""
        _ = self.group_repo.get_or_404(group_id)

        # Check if group has schedules
        schedules_count = self.group_repo.get_schedules_count(group_id)
        if schedules_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete group. {schedules_count} class schedules exist",
                error_code="GROUP_HAS_SCHEDULES",
            )

        self.group_repo.delete(id=group_id)
