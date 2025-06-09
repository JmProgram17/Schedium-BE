"""
Human resources endpoints.
Handles departments, contracts, and instructors.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_pagination_params,
    require_admin,
    require_coordinator,
)
from app.core.pagination import Page, PaginationParams
from app.core.responses import (
    CreatedResponse,
    DeletedResponse,
    SuccessResponse,
    UpdatedResponse,
)
from app.schemas.auth import User
from app.schemas.hr import (
    Contract,
    ContractCreate,
    ContractUpdate,
    Department,
    DepartmentCreate,
    DepartmentUpdate,
    Instructor,
    InstructorCreate,
    InstructorUpdate,
    InstructorWorkload,
)
from app.services.hr import HRService

router = APIRouter()


# Department endpoints
@router.get("/departments", response_model=SuccessResponse[Page[Department]])
async def get_departments(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in name, email, or phone"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Department]]:
    """Get paginated list of departments."""
    service = HRService(db)
    departments = service.get_departments(params, search)

    return SuccessResponse(
        data=departments, message="Departments retrieved successfully", errors=None
    )


@router.post("/departments", response_model=CreatedResponse[Department])
async def create_department(
    department_in: DepartmentCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Department]:
    """Create a new department. Coordinator or Admin only."""
    service = HRService(db)
    department = service.create_department(department_in)

    return CreatedResponse(
        data=department, message="Department created successfully", errors=None
    )


@router.get("/departments/{department_id}", response_model=SuccessResponse[Department])
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Department]:
    """Get department by ID."""
    service = HRService(db)
    department = service.get_department(department_id)

    return SuccessResponse(
        data=department, message="Department retrieved successfully", errors=None
    )


@router.put("/departments/{department_id}", response_model=UpdatedResponse[Department])
async def update_department(
    department_id: int,
    department_in: DepartmentUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Department]:
    """Update department. Coordinator or Admin only."""
    service = HRService(db)
    department = service.update_department(department_id, department_in)

    return UpdatedResponse(
        data=department, message="Department updated successfully", errors=None
    )


@router.delete("/departments/{department_id}", response_model=DeletedResponse)
async def delete_department(
    department_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete department. Admin only."""
    service = HRService(db)
    service.delete_department(department_id)

    return DeletedResponse(message="Department deleted successfully", errors=None)


# Contract endpoints
@router.get("/contracts", response_model=SuccessResponse[Page[Contract]])
async def get_contracts(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Contract]]:
    """Get paginated list of contract types."""
    service = HRService(db)
    contracts = service.get_contracts(params)

    return SuccessResponse(
        data=contracts, message="Contracts retrieved successfully", errors=None
    )


@router.post("/contracts", response_model=CreatedResponse[Contract])
async def create_contract(
    contract_in: ContractCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Contract]:
    """Create a new contract type. Coordinator or Admin only."""
    service = HRService(db)
    contract = service.create_contract(contract_in)

    return CreatedResponse(
        data=contract, message="Contract created successfully", errors=None
    )


@router.get("/contracts/{contract_id}", response_model=SuccessResponse[Contract])
async def get_contract(
    contract_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Contract]:
    """Get contract type by ID."""
    service = HRService(db)
    contract = service.get_contract(contract_id)

    return SuccessResponse(
        data=contract, message="Contract retrieved successfully", errors=None
    )


@router.put("/contracts/{contract_id}", response_model=UpdatedResponse[Contract])
async def update_contract(
    contract_id: int,
    contract_in: ContractUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Contract]:
    """Update contract type. Coordinator or Admin only."""
    service = HRService(db)
    contract = service.update_contract(contract_id, contract_in)

    return UpdatedResponse(
        data=contract, message="Contract updated successfully", errors=None
    )


@router.delete("/contracts/{contract_id}", response_model=DeletedResponse)
async def delete_contract(
    contract_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete contract type. Admin only."""
    service = HRService(db)
    service.delete_contract(contract_id)

    return DeletedResponse(message="Contract deleted successfully", errors=None)


# Instructor endpoints
@router.get("/instructors", response_model=SuccessResponse[Page[Instructor]])
async def get_instructors(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in name, email, or phone"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    contract_id: Optional[int] = Query(None, description="Filter by contract type"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Instructor]]:
    """Get paginated list of instructors."""
    service = HRService(db)
    instructors = service.get_instructors(
        params, search, department_id, contract_id, active
    )

    return SuccessResponse(
        data=instructors, message="Instructors retrieved successfully", errors=None
    )


@router.post("/instructors", response_model=CreatedResponse[Instructor])
async def create_instructor(
    instructor_in: InstructorCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Instructor]:
    """Create a new instructor. Coordinator or Admin only."""
    service = HRService(db)
    instructor = service.create_instructor(instructor_in)

    return CreatedResponse(
        data=instructor, message="Instructor created successfully", errors=None
    )


@router.get("/instructors/{instructor_id}", response_model=SuccessResponse[Instructor])
async def get_instructor(
    instructor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Instructor]:
    """Get instructor by ID."""
    service = HRService(db)
    instructor = service.get_instructor(instructor_id)

    return SuccessResponse(
        data=instructor, message="Instructor retrieved successfully", errors=None
    )


@router.put("/instructors/{instructor_id}", response_model=UpdatedResponse[Instructor])
async def update_instructor(
    instructor_id: int,
    instructor_in: InstructorUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Instructor]:
    """Update instructor. Coordinator or Admin only."""
    service = HRService(db)
    instructor = service.update_instructor(instructor_id, instructor_in)

    return UpdatedResponse(
        data=instructor, message="Instructor updated successfully", errors=None
    )


@router.delete("/instructors/{instructor_id}", response_model=DeletedResponse)
async def delete_instructor(
    instructor_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete instructor. Admin only."""
    service = HRService(db)
    service.delete_instructor(instructor_id)

    return DeletedResponse(message="Instructor deleted successfully", errors=None)


@router.get(
    "/instructors/{instructor_id}/workload",
    response_model=SuccessResponse[InstructorWorkload],
)
async def get_instructor_workload(
    instructor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[InstructorWorkload]:
    """Get instructor workload summary."""
    service = HRService(db)
    workload = service.get_instructor_workload(instructor_id)

    return SuccessResponse(
        data=workload, message="Instructor workload retrieved successfully", errors=None
    )


@router.get(
    "/instructors/{instructor_id}/schedule", response_model=SuccessResponse[list]
)
async def get_instructor_schedule(
    instructor_id: int,
    quarter_id: int = Query(..., description="Quarter ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[list]:
    """Get instructor's class schedule for a specific quarter."""
    from app.services.scheduling import SchedulingService

    service = SchedulingService(db)
    schedules = service.get_instructor_schedule(instructor_id, quarter_id)

    return SuccessResponse(
        data=schedules,
        message="Instructor schedule retrieved successfully",
        errors=None,
    )
