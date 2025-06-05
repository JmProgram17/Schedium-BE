"""
Human resources services.
Handles business logic for HR entities.
"""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.hr import Department, Contract, Instructor
from app.schemas.hr import (
    DepartmentCreate, DepartmentUpdate, Department as DepartmentSchema,
    ContractCreate, ContractUpdate, Contract as ContractSchema,
    InstructorCreate, InstructorUpdate, Instructor as InstructorSchema,
    InstructorWorkload
)
from app.repositories.hr import (
    DepartmentRepository, ContractRepository, InstructorRepository
)
from app.core.exceptions import (
    NotFoundException, ConflictException, BadRequestException
)
from app.core.pagination import PaginationParams, Page


class HRService:
    """Service for human resources operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.department_repo = DepartmentRepository(db)
        self.contract_repo = ContractRepository(db)
        self.instructor_repo = InstructorRepository(db)
    
    # Department operations
    def create_department(self, dept_in: DepartmentCreate) -> DepartmentSchema:
        """Create a new department."""
        # Check if name already exists
        existing = self.department_repo.get_by_name(dept_in.name)
        if existing:
            raise ConflictException(
                detail=f"Department '{dept_in.name}' already exists",
                error_code="DEPARTMENT_EXISTS"
            )
        
        department = self.department_repo.create(obj_in=dept_in)
        return DepartmentSchema.model_validate(department)
    
    def get_department(self, department_id: int) -> DepartmentSchema:
        """Get department by ID."""
        department = self.department_repo.get_or_404(department_id)
        return DepartmentSchema.model_validate(department)
    
    def get_departments(
        self,
        params: PaginationParams,
        search: Optional[str] = None
    ) -> Page[DepartmentSchema]:
        """Get paginated list of departments."""
        page = self.department_repo.search_departments(params, search)
        page.items = [DepartmentSchema.model_validate(item) for item in page.items]
        return page
    
    def update_department(
        self,
        department_id: int,
        dept_in: DepartmentUpdate
    ) -> DepartmentSchema:
        """Update department."""
        department = self.department_repo.get_or_404(department_id)
        
        # Check uniqueness if name changed
        if dept_in.name and dept_in.name != department.name:
            existing = self.department_repo.get_by_name(dept_in.name)
            if existing:
                raise ConflictException(
                    detail=f"Department '{dept_in.name}' already exists",
                    error_code="DEPARTMENT_EXISTS"
                )
        
        department = self.department_repo.update(db_obj=department, obj_in=dept_in)
        return DepartmentSchema.model_validate(department)
    
    def delete_department(self, department_id: int) -> None:
        """Delete department."""
        department = self.department_repo.get_or_404(department_id)
        
        # Check if department has programs
        programs_count = self.department_repo.get_programs_count(department_id)
        if programs_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete department. {programs_count} programs belong to it",
                error_code="DEPARTMENT_HAS_PROGRAMS"
            )
        
        # Check if department has instructors
        instructors_count = self.department_repo.get_instructors_count(department_id)
        if instructors_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete department. {instructors_count} instructors belong to it",
                error_code="DEPARTMENT_HAS_INSTRUCTORS"
            )
        
        self.department_repo.delete(id=department_id)
    
    # Contract operations
    def create_contract(self, contract_in: ContractCreate) -> ContractSchema:
        """Create a new contract type."""
        # Check if type already exists
        existing = self.contract_repo.get_by_type(contract_in.contract_type)
        if existing:
            raise ConflictException(
                detail=f"Contract type '{contract_in.contract_type}' already exists",
                error_code="CONTRACT_EXISTS"
            )
        
        contract = self.contract_repo.create(obj_in=contract_in)
        return ContractSchema.model_validate(contract)
    
    def get_contract(self, contract_id: int) -> ContractSchema:
        """Get contract by ID."""
        contract = self.contract_repo.get_or_404(contract_id)
        return ContractSchema.model_validate(contract)
    
    def get_contracts(self, params: PaginationParams) -> Page[ContractSchema]:
        """Get paginated list of contracts."""
        page = self.contract_repo.get_paginated(params)
        page.items = [ContractSchema.model_validate(item) for item in page.items]
        return page
    
    def update_contract(
        self,
        contract_id: int,
        contract_in: ContractUpdate
    ) -> ContractSchema:
        """Update contract."""
        contract = self.contract_repo.get_or_404(contract_id)
        
        # Check uniqueness if type changed
        if contract_in.contract_type and contract_in.contract_type != contract.contract_type:
            existing = self.contract_repo.get_by_type(contract_in.contract_type)
            if existing:
                raise ConflictException(
                    detail=f"Contract type '{contract_in.contract_type}' already exists",
                    error_code="CONTRACT_EXISTS"
                )
        
        contract = self.contract_repo.update(db_obj=contract, obj_in=contract_in)
        return ContractSchema.model_validate(contract)
    
    def delete_contract(self, contract_id: int) -> None:
        """Delete contract."""
        contract = self.contract_repo.get_or_404(contract_id)
        
        # Check if contract is in use
        instructors_count = self.contract_repo.get_instructors_count(contract_id)
        if instructors_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete contract. {instructors_count} instructors have this contract",
                error_code="CONTRACT_IN_USE"
            )
        
        self.contract_repo.delete(id=contract_id)
    
    # Instructor operations
    def create_instructor(self, instructor_in: InstructorCreate) -> InstructorSchema:
        """Create a new instructor."""
        # Check if email already exists
        if self.instructor_repo.is_email_taken(instructor_in.email):
            raise ConflictException(
                detail=f"Email {instructor_in.email} is already registered",
                error_code="EMAIL_TAKEN"
            )
        
        # Validate foreign keys
        if instructor_in.contract_id:
            self.contract_repo.get_or_404(instructor_in.contract_id)
        
        if instructor_in.department_id:
            self.department_repo.get_or_404(instructor_in.department_id)
        
        instructor = self.instructor_repo.create(obj_in=instructor_in)
        instructor = self.instructor_repo.get_with_relations(instructor.instructor_id)
        return InstructorSchema.model_validate(instructor)
    
    def get_instructor(self, instructor_id: int) -> InstructorSchema:
        """Get instructor by ID."""
        instructor = self.instructor_repo.get_with_relations(instructor_id)
        if not instructor:
            raise NotFoundException(f"Instructor with id {instructor_id} not found")
        return InstructorSchema.model_validate(instructor)
    
    def get_instructors(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        active: Optional[bool] = None
    ) -> Page[InstructorSchema]:
        """Get paginated list of instructors."""
        page = self.instructor_repo.search_instructors(
            params, search, department_id, contract_id, active
        )
        page.items = [InstructorSchema.model_validate(item) for item in page.items]
        return page
    
    def update_instructor(
        self,
        instructor_id: int,
        instructor_in: InstructorUpdate
    ) -> InstructorSchema:
        """Update instructor."""
        instructor = self.instructor_repo.get_or_404(instructor_id)
        
        # Check email uniqueness if changed
        if instructor_in.email and instructor_in.email != instructor.email:
            if self.instructor_repo.is_email_taken(instructor_in.email, instructor_id):
                raise ConflictException(
                    detail=f"Email {instructor_in.email} is already taken",
                    error_code="EMAIL_TAKEN"
                )
        
        # Validate foreign keys if changed
        if instructor_in.contract_id is not None:
            if instructor_in.contract_id:
                self.contract_repo.get_or_404(instructor_in.contract_id)
        
        if instructor_in.department_id is not None:
            if instructor_in.department_id:
                self.department_repo.get_or_404(instructor_in.department_id)
        
        instructor = self.instructor_repo.update(db_obj=instructor, obj_in=instructor_in)
        instructor = self.instructor_repo.get_with_relations(instructor_id)
        return InstructorSchema.model_validate(instructor)
    
    def delete_instructor(self, instructor_id: int) -> None:
        """Delete instructor."""
        instructor = self.instructor_repo.get_or_404(instructor_id)
        
        # Check if instructor has schedules
        schedules_count = self.instructor_repo.get_schedules_count(instructor_id)
        if schedules_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete instructor. {schedules_count} class schedules assigned",
                error_code="INSTRUCTOR_HAS_SCHEDULES"
            )
        
        self.instructor_repo.delete(id=instructor_id)
    
    def get_instructor_workload(self, instructor_id: int) -> InstructorWorkload:
        """Get instructor workload summary."""
        workload_data = self.instructor_repo.get_workload_summary(instructor_id)
        if not workload_data:
            raise NotFoundException(f"Instructor with id {instructor_id} not found")
        
        # Determine status based on utilization
        if workload_data.get("utilization_percentage") is None:
            status = "NO_LIMIT"
        elif workload_data["utilization_percentage"] >= 100:
            status = "OVERLOADED"
        elif workload_data["utilization_percentage"] >= 90:
            status = "NEAR_LIMIT"
        elif workload_data["utilization_percentage"] >= 70:
            status = "HIGH_LOAD"
        elif workload_data["utilization_percentage"] >= 50:
            status = "MEDIUM_LOAD"
        else:
            status = "LOW_LOAD"
        
        workload_data["status"] = status
        
        return InstructorWorkload(**workload_data)