"""
Human resources endpoints.
Handles departments, contracts, and instructors.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    get_db, get_current_active_user, require_coordinator,
    require_admin, get_pagination_params
)
from app.core.responses import (
    SuccessResponse, CreatedResponse, UpdatedResponse, DeletedResponse
)
from app.core.pagination import PaginationParams, Page
from app.schemas.auth import User
from app.schemas.hr import (
    Department, DepartmentCreate, DepartmentUpdate,
    Contract, ContractCreate, ContractUpdate,
    Instructor, InstructorCreate, InstructorUpdate, InstructorWorkload
)
from app.services.hr import HRService

router = APIRouter()


# Department endpoints
@router.get("/departments", response_model=SuccessResponse[Page[Department]])
async def get_departments(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in name, email, or phone"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of departments."""
    service = HRService(db)
    departments = service.get_departments(params, search)
    
    return SuccessResponse(
        data=departments,
        message="Departments retrieved successfully"
    )


@router.post("/departments", response_model=CreatedResponse[Department])
async def create_department(
    department_in: DepartmentCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Create a new department. Coordinator or Admin only."""
    service = HRService(db)
    department = service.create_department(department_in)
    
    return CreatedResponse(
        data=department,
        message="Department created successfully"
    )


@router.get("/departments/{department_id}", response_model=SuccessResponse[Department])
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get department by ID."""
    service = HRService(db)
    department = service.get_department(department_id)
    
    return SuccessResponse(
        data=department,
        message="Department retrieved successfully"
    )


@router.put("/departments/{department_id}", response_model=UpdatedResponse[Department])
async def update_department(
    department_id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Update department. Coordinator or Admin only."""
    service = HRService(db)
    department = service.update_department(department_id, department_in)
    
    return UpdatedResponse(
        data=department,
        message="Department updated successfully"
    )


@router.delete("/departments/{department_id}", response_model=DeletedResponse)
async def delete_department(
    department_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete department. Admin only."""
    service = HRService(db)
    service.delete_department(department_id)
    
    return DeletedResponse(
        message="Department deleted successfully"
    )


# Contract endpoints
@router.get("/contracts", response_model=SuccessResponse[Page[Contract]])
async def get_contracts(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of contract types."""
    service = HRService(db)
    contracts = service.get_contracts(params)
    
    return SuccessResponse(
        data=contracts,
        message="Contracts retrieved successfully"
    )


@router.post("/contracts", response_model=CreatedResponse[Contract])
async def create_contract(
    contract_in: ContractCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Create a new contract type. Coordinator or Admin only."""
    service = HRService(db)
    contract = service.create_contract(contract_in)
    
    return CreatedResponse(
        data=contract,
        message="Contract created successfully"
    )


@router.get("/contracts/{contract_id}", response_model=SuccessResponse[Contract])
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get contract type by ID."""
    service = HRService(db)
    contract = service.get_contract(contract_id)
    
    return SuccessResponse(
        data=contract,
        message="Contract retrieved successfully"
    )


@router.put("/contracts/{contract_id}", response_model=UpdatedResponse[Contract])
async def update_contract(
    contract_id: int,
    contract_in: ContractUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Update contract type. Coordinator or Admin only."""
    service = HRService(db)
    contract = service.update_contract(contract_id, contract_in)
    
    return UpdatedResponse(
        data=contract,
        message="Contract updated successfully"
    )


@router.delete("/contracts/{contract_id}", response_model=DeletedResponse)
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete contract type. Admin only."""
    service = HRService(db)
    service.delete_contract(contract_id)
    
    return DeletedResponse(
        message="Contract deleted successfully"
    )


# Instructor endpoints
@router.get("/instructors", response_model=SuccessResponse[Page[Instructor]])
async def get_instructors(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in name, email, or phone"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    contract_id: Optional[int] = Query(None, description="Filter by contract type"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of instructors."""
    service = HRService(db)
    instructors = service.get_instructors(
        params, search, department_id, contract_id, active
    )
    
    return SuccessResponse(
        data=instructors,
        message="Instructors retrieved successfully"
    )


@router.post("/instructors", response_model=CreatedResponse[Instructor])
async def create_instructor(
    instructor_in: InstructorCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Create a new instructor. Coordinator or Admin only."""
    service = HRService(db)
    instructor = service.create_instructor(instructor_in)
    
    return CreatedResponse(
        data=instructor,
        message="Instructor created successfully"
    )


@router.get("/instructors/{instructor_id}", response_model=SuccessResponse[Instructor])
async def get_instructor(
    instructor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get instructor by ID."""
    service = HRService(db)
    instructor = service.get_instructor(instructor_id)
    
    return SuccessResponse(
        data=instructor,
        message="Instructor retrieved successfully"
    )


@router.put("/instructors/{instructor_id}", response_model=UpdatedResponse[Instructor])
async def update_instructor(
    instructor_id: int,
    instructor_in: InstructorUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Update instructor. Coordinator or Admin only."""
    service = HRService(db)
    instructor = service.update_instructor(instructor_id, instructor_in)
    
    return UpdatedResponse(
        data=instructor,
        message="Instructor updated successfully"
    )


@router.delete("/instructors/{instructor_id}", response_model=DeletedResponse)
async def delete_instructor(
    instructor_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete instructor. Admin only."""
    service = HRService(db)
    service.delete_instructor(instructor_id)
    
    return DeletedResponse(
        message="Instructor deleted successfully"
    )


@router.get("/instructors/{instructor_id}/workload", response_model=SuccessResponse[InstructorWorkload])
async def get_instructor_workload(
    instructor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get instructor workload summary."""
    service = HRService(db)
    workload = service.get_instructor_workload(instructor_id)
    
    return SuccessResponse(
        data=workload,
        message="Instructor workload retrieved successfully"
    )


@router.get("/instructors/{instructor_id}/schedule", response_model=SuccessResponse[list])
async def get_instructor_schedule(
    instructor_id: int,
    quarter_id: int = Query(..., description="Quarter ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get instructor's class schedule for a specific quarter."""
    from app.services.scheduling import SchedulingService
    
    service = SchedulingService(db)
    schedules = service.get_instructor_schedule(instructor_id, quarter_id)
    
    return SuccessResponse(
        data=schedules,
        message="Instructor schedule retrieved successfully"
    )