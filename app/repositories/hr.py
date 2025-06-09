"""
Human resources repositories.
Handles database operations for HR entities.
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.pagination import Page, PaginationParams, paginate
from app.models.hr import Contract, Department, Instructor
from app.repositories.base import BaseRepository
from app.schemas.hr import (
    ContractCreate,
    ContractUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    InstructorCreate,
    InstructorUpdate,
)


class DepartmentRepository(
    BaseRepository[Department, DepartmentCreate, DepartmentUpdate]
):
    """Repository for departments."""

    def __init__(self, db: Session):
        super().__init__(Department, db)

    def get_by_name(self, name: str) -> Optional[Department]:
        """Get department by name."""
        return self.db.query(Department).filter(Department.name == name).first()

    def get_programs_count(self, department_id: int) -> int:
        """Get count of programs in this department."""
        from app.models.academic import Program

        return (
            self.db.query(Program)
            .filter(Program.department_id == department_id)
            .count()
        )

    def get_instructors_count(self, department_id: int) -> int:
        """Get count of instructors in this department."""
        return (
            self.db.query(Instructor)
            .filter(Instructor.department_id == department_id)
            .count()
        )

    def search_departments(
        self, params: PaginationParams, search: Optional[str] = None
    ) -> Page[Department]:
        """Search departments with filters."""
        query = self.db.query(Department)

        if search:
            search_filter = or_(
                Department.name.ilike(f"%{search}%"),
                Department.email.ilike(f"%{search}%"),
                Department.phone_number.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)

        return paginate(query, params)


class ContractRepository(BaseRepository[Contract, ContractCreate, ContractUpdate]):
    """Repository for contracts."""

    def __init__(self, db: Session):
        super().__init__(Contract, db)

    def get_by_type(self, contract_type: str) -> Optional[Contract]:
        """Get contract by type."""
        return (
            self.db.query(Contract)
            .filter(Contract.contract_type == contract_type)
            .first()
        )

    def get_instructors_count(self, contract_id: int) -> int:
        """Get count of instructors with this contract."""
        return (
            self.db.query(Instructor)
            .filter(Instructor.contract_id == contract_id)
            .count()
        )

    def get_active_contracts(self) -> List[Contract]:
        """Get all contracts ordered by type."""
        return self.db.query(Contract).order_by(Contract.contract_type).all()


class InstructorRepository(
    BaseRepository[Instructor, InstructorCreate, InstructorUpdate]
):
    """Repository for instructors."""

    def __init__(self, db: Session):
        super().__init__(Instructor, db)

    def get_by_email(self, email: str) -> Optional[Instructor]:
        """Get instructor by email."""
        return self.db.query(Instructor).filter(Instructor.email == email).first()

    def get_with_relations(self, instructor_id: int) -> Optional[Instructor]:
        """Get instructor with all relations loaded."""
        return (
            self.db.query(Instructor)
            .options(joinedload(Instructor.contract), joinedload(Instructor.department))
            .filter(Instructor.instructor_id == instructor_id)
            .first()
        )

    def search_instructors(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        active: Optional[bool] = None,
    ) -> Page[Instructor]:
        """Search instructors with filters."""
        query = self.db.query(Instructor).options(
            joinedload(Instructor.contract), joinedload(Instructor.department)
        )

        # Apply filters
        if search:
            search_filter = or_(
                Instructor.first_name.ilike(f"%{search}%"),
                Instructor.last_name.ilike(f"%{search}%"),
                Instructor.email.ilike(f"%{search}%"),
                Instructor.phone_number.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)

        if department_id:
            query = query.filter(Instructor.department_id == department_id)

        if contract_id:
            query = query.filter(Instructor.contract_id == contract_id)

        if active is not None:
            query = query.filter(Instructor.active == active)

        return paginate(query, params)

    def get_active_instructors(self) -> List[Instructor]:
        """Get all active instructors."""
        return self.db.query(Instructor).filter(Instructor.active == True).all()

    def get_schedules_count(self, instructor_id: int) -> int:
        """Get count of class schedules for this instructor."""
        from app.models.scheduling import ClassSchedule

        return (
            self.db.query(ClassSchedule)
            .filter(ClassSchedule.instructor_id == instructor_id)
            .count()
        )

    def get_workload_summary(self, instructor_id: int) -> dict:
        """Get instructor workload summary."""
        instructor = self.get_with_relations(instructor_id)
        if not instructor:
            return {}

        return {
            "instructor_id": instructor.instructor_id,
            "full_name": instructor.full_name,
            "total_hours": float(instructor.hour_count),
            "contract_limit": instructor.contract.hour_limit
            if instructor.contract
            else None,
            "available_hours": (
                float(instructor.contract.hour_limit - instructor.hour_count)
                if instructor.contract and instructor.contract.hour_limit
                else None
            ),
            "utilization_percentage": (
                float(instructor.hour_count / instructor.contract.hour_limit * 100)
                if instructor.contract and instructor.contract.hour_limit
                else None
            ),
        }

    def update_hour_count(self, instructor_id: int, hours: Decimal) -> bool:
        """Update instructor's hour count."""
        instructor = self.get(instructor_id)
        if instructor:
            instructor.hour_count = hours
            self.db.commit()
            return True
        return False

    def is_email_taken(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email is already taken."""
        query = self.db.query(Instructor).filter(Instructor.email == email)
        if exclude_id:
            query = query.filter(Instructor.instructor_id != exclude_id)
        return query.first() is not None
