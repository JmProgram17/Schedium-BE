"""
Infrastructure endpoints.
Handles campuses, classrooms, and department-classroom assignments.
"""

from typing import Optional, List
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
from app.schemas.infrastructure import (
    Campus, CampusCreate, CampusUpdate,
    Classroom, ClassroomCreate, ClassroomUpdate,
    DepartmentClassroom, DepartmentClassroomCreate, DepartmentClassroomUpdate,
    ClassroomAvailability
)
from app.services.infrastructure import InfrastructureService

router = APIRouter()


# Campus endpoints
@router.get("/campuses", response_model=SuccessResponse[Page[Campus]])
async def get_campuses(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in address, email, or phone"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of campuses."""
    service = InfrastructureService(db)
    campuses = service.get_campuses(params, search)
    
    return SuccessResponse(
        data=campuses,
        message="Campuses retrieved successfully"
    )


@router.post("/campuses", response_model=CreatedResponse[Campus])
async def create_campus(
    campus_in: CampusCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Create a new campus. Coordinator or Admin only."""
    service = InfrastructureService(db)
    campus = service.create_campus(campus_in)
    
    return CreatedResponse(
        data=campus,
        message="Campus created successfully"
    )


@router.get("/campuses/{campus_id}", response_model=SuccessResponse[Campus])
async def get_campus(
    campus_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get campus by ID."""
    service = InfrastructureService(db)
    campus = service.get_campus(campus_id)
    
    return SuccessResponse(
        data=campus,
        message="Campus retrieved successfully"
    )


@router.put("/campuses/{campus_id}", response_model=UpdatedResponse[Campus])
async def update_campus(
    campus_id: int,
    campus_in: CampusUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Update campus. Coordinator or Admin only."""
    service = InfrastructureService(db)
    campus = service.update_campus(campus_id, campus_in)
    
    return UpdatedResponse(
        data=campus,
        message="Campus updated successfully"
    )


@router.delete("/campuses/{campus_id}", response_model=DeletedResponse)
async def delete_campus(
    campus_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete campus. Admin only."""
    service = InfrastructureService(db)
    service.delete_campus(campus_id)
    
    return DeletedResponse(
        message="Campus deleted successfully"
    )


# Classroom endpoints
@router.get("/classrooms", response_model=SuccessResponse[Page[Classroom]])
async def get_classrooms(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(None, description="Search in room number or type"),
    campus_id: Optional[int] = Query(None, description="Filter by campus"),
    classroom_type: Optional[str] = Query(None, description="Filter by classroom type"),
    min_capacity: Optional[int] = Query(None, description="Minimum capacity"),
    max_capacity: Optional[int] = Query(None, description="Maximum capacity"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of classrooms."""
    service = InfrastructureService(db)
    classrooms = service.get_classrooms(
        params, search, campus_id, classroom_type, min_capacity, max_capacity
    )
    
    return SuccessResponse(
        data=classrooms,
        message="Classrooms retrieved successfully"
    )


@router.post("/classrooms", response_model=CreatedResponse[Classroom])
async def create_classroom(
    classroom_in: ClassroomCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Create a new classroom. Coordinator or Admin only."""
    service = InfrastructureService(db)
    classroom = service.create_classroom(classroom_in)
    
    return CreatedResponse(
        data=classroom,
        message="Classroom created successfully"
    )


@router.get("/classrooms/{classroom_id}", response_model=SuccessResponse[Classroom])
async def get_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get classroom by ID."""
    service = InfrastructureService(db)
    classroom = service.get_classroom(classroom_id)
    
    return SuccessResponse(
        data=classroom,
        message="Classroom retrieved successfully"
    )


@router.put("/classrooms/{classroom_id}", response_model=UpdatedResponse[Classroom])
async def update_classroom(
    classroom_id: int,
    classroom_in: ClassroomUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """Update classroom. Coordinator or Admin only."""
    service = InfrastructureService(db)
    classroom = service.update_classroom(classroom_id, classroom_in)
    
    return UpdatedResponse(
        data=classroom,
        message="Classroom updated successfully"
    )


@router.delete("/classrooms/{classroom_id}", response_model=DeletedResponse)
async def delete_classroom(
    classroom_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete classroom. Admin only."""
    service = InfrastructureService(db)
    service.delete_classroom(classroom_id)
    
    return DeletedResponse(
        message="Classroom deleted successfully"
    )


@router.get("/classrooms/availability", response_model=SuccessResponse[List[ClassroomAvailability]])
async def get_classroom_availability(
    day_time_block_id: int = Query(..., description="Day-time block ID"),
    quarter_id: int = Query(..., description="Quarter ID"),
    min_capacity: Optional[int] = Query(None, description="Minimum required capacity"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get available classrooms for a specific time slot."""
    service = InfrastructureService(db)
    availability = service.get_classroom_availability(
        day_time_block_id, quarter_id, min_capacity
    )
    
    return SuccessResponse(
        data=availability,
        message="Classroom availability retrieved successfully"
    )


# Department-Classroom assignment endpoints
@router.post("/classrooms/{classroom_id}/departments", response_model=CreatedResponse[DepartmentClassroom])
async def assign_classroom_to_department(
    classroom_id: int,
    assignment: DepartmentClassroomCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """
    Assign classroom to department.
    
    Coordinator or Admin only.
    """
    # Ensure classroom_id matches
    assignment.classroom_id = classroom_id
    
    service = InfrastructureService(db)
    dept_classroom = service.assign_classroom_to_department(assignment)
    
    return CreatedResponse(
        data=dept_classroom,
        message="Classroom assigned to department successfully"
    )


@router.put(
    "/departments/{department_id}/classrooms/{classroom_id}",
    response_model=UpdatedResponse[DepartmentClassroom]
)
async def update_classroom_assignment(
    department_id: int,
    classroom_id: int,
    update_data: DepartmentClassroomUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """
    Update department-classroom assignment.
    
    Coordinator or Admin only.
    """
    service = InfrastructureService(db)
    assignment = service.update_classroom_assignment(
        department_id, classroom_id, update_data
    )
    
    return UpdatedResponse(
        data=assignment,
        message="Assignment updated successfully"
    )


@router.delete("/departments/{department_id}/classrooms/{classroom_id}", response_model=DeletedResponse)
async def remove_classroom_assignment(
    department_id: int,
    classroom_id: int,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db)
):
    """
    Remove classroom assignment from department.
    
    Coordinator or Admin only.
    """
    service = InfrastructureService(db)
    service.remove_classroom_assignment(department_id, classroom_id)
    
    return DeletedResponse(
        message="Assignment removed successfully"
    )


@router.get("/departments/{department_id}/classrooms", response_model=SuccessResponse[List[DepartmentClassroom]])
async def get_department_classrooms(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all classrooms assigned to a department."""
    service = InfrastructureService(db)
    assignments = service.get_department_classrooms(department_id)
    
    return SuccessResponse(
        data=assignments,
        message="Department classrooms retrieved successfully"
    )