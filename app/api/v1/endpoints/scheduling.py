"""
Scheduling endpoints.
Handles schedules, time blocks, quarters, and class scheduling.
"""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
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
from app.schemas.scheduling import (
    ClassSchedule,
    ClassScheduleCreate,
    ClassScheduleDetailed,
    ClassScheduleUpdate,
    Day,
    DayTimeBlock,
    DayTimeBlockCreate,
    Quarter,
    QuarterCreate,
    QuarterUpdate,
    Schedule,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleValidation,
    TimeBlock,
    TimeBlockCreate,
    TimeBlockUpdate,
)
from app.services.scheduling import SchedulingService

router = APIRouter()


# Schedule (Jornada) endpoints
@router.get("/schedules", response_model=SuccessResponse[Page[Schedule]])
async def get_schedules(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Schedule]]:
    """Get paginated list of schedules (jornadas)."""
    service = SchedulingService(db)
    schedules = service.get_schedules(params)

    return SuccessResponse(
        data=schedules, message="Schedules retrieved successfully", errors=None
    )


@router.post("/schedules", response_model=CreatedResponse[Schedule])
async def create_schedule(
    schedule_in: ScheduleCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Schedule]:
    """Create a new schedule. Coordinator or Admin only."""
    service = SchedulingService(db)
    schedule = service.create_schedule(schedule_in)

    return CreatedResponse(
        data=schedule, message="Schedule created successfully", errors=None
    )


@router.get("/schedules/{schedule_id}", response_model=SuccessResponse[Schedule])
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Schedule]:
    """Get schedule by ID."""
    service = SchedulingService(db)
    schedule = service.get_schedule(schedule_id)

    return SuccessResponse(
        data=schedule, message="Schedule retrieved successfully", errors=None
    )


@router.put("/schedules/{schedule_id}", response_model=UpdatedResponse[Schedule])
async def update_schedule(
    schedule_id: int,
    schedule_in: ScheduleUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Schedule]:
    """Update schedule. Coordinator or Admin only."""
    service = SchedulingService(db)
    schedule = service.update_schedule(schedule_id, schedule_in)

    return UpdatedResponse(
        data=schedule, message="Schedule updated successfully", errors=None
    )


@router.delete("/schedules/{schedule_id}", response_model=DeletedResponse)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete schedule. Admin only."""
    service = SchedulingService(db)
    service.delete_schedule(schedule_id)

    return DeletedResponse(message="Schedule deleted successfully", errors=None)


# Time Block endpoints
@router.get("/time-blocks", response_model=SuccessResponse[Page[TimeBlock]])
async def get_time_blocks(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[TimeBlock]]:
    """Get paginated list of time blocks."""
    service = SchedulingService(db)
    blocks = service.get_time_blocks(params)

    return SuccessResponse(
        data=blocks, message="Time blocks retrieved successfully", errors=None
    )


@router.post("/time-blocks", response_model=CreatedResponse[TimeBlock])
async def create_time_block(
    block_in: TimeBlockCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[TimeBlock]:
    """Create a new time block. Coordinator or Admin only."""
    service = SchedulingService(db)
    block = service.create_time_block(block_in)

    return CreatedResponse(
        data=block, message="Time block created successfully", errors=None
    )


@router.get("/time-blocks/{time_block_id}", response_model=SuccessResponse[TimeBlock])
async def get_time_block(
    time_block_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[TimeBlock]:
    """Get time block by ID."""
    service = SchedulingService(db)
    block = service.get_time_block(time_block_id)

    return SuccessResponse(
        data=block, message="Time block retrieved successfully", errors=None
    )


@router.put("/time-blocks/{time_block_id}", response_model=UpdatedResponse[TimeBlock])
async def update_time_block(
    time_block_id: int,
    block_in: TimeBlockUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[TimeBlock]:
    """Update time block. Coordinator or Admin only."""
    service = SchedulingService(db)
    block = service.update_time_block(time_block_id, block_in)

    return UpdatedResponse(
        data=block, message="Time block updated successfully", errors=None
    )


@router.delete("/time-blocks/{time_block_id}", response_model=DeletedResponse)
async def delete_time_block(
    time_block_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete time block. Admin only."""
    service = SchedulingService(db)
    service.delete_time_block(time_block_id)

    return DeletedResponse(message="Time block deleted successfully", errors=None)


# Day endpoints
@router.get("/days", response_model=SuccessResponse[List[Day]])
async def get_days(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> SuccessResponse[List[Day]]:
    """Get all days of the week."""
    service = SchedulingService(db)
    days = service.get_days()

    return SuccessResponse(
        data=days, message="Days retrieved successfully", errors=None
    )


# Day-Time Block endpoints
@router.get("/day-time-blocks", response_model=SuccessResponse[Page[DayTimeBlock]])
async def get_day_time_blocks(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[DayTimeBlock]]:
    """Get paginated list of day-time block associations."""
    service = SchedulingService(db)
    dtbs = service.get_day_time_blocks(params)

    return SuccessResponse(
        data=dtbs, message="Day-time blocks retrieved successfully", errors=None
    )


@router.post("/day-time-blocks", response_model=CreatedResponse[DayTimeBlock])
async def create_day_time_block(
    dtb_in: DayTimeBlockCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[DayTimeBlock]:
    """Create day-time block association. Coordinator or Admin only."""
    service = SchedulingService(db)
    dtb = service.create_day_time_block(dtb_in)

    return CreatedResponse(
        data=dtb, message="Day-time block created successfully", errors=None
    )


@router.delete("/day-time-blocks/{day_time_block_id}", response_model=DeletedResponse)
async def delete_day_time_block(
    day_time_block_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete day-time block. Admin only."""
    service = SchedulingService(db)
    service.delete_day_time_block(day_time_block_id)

    return DeletedResponse(message="Day-time block deleted successfully", errors=None)


# Quarter endpoints
@router.get("/quarters", response_model=SuccessResponse[Page[Quarter]])
async def get_quarters(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Quarter]]:
    """Get paginated list of academic quarters."""
    service = SchedulingService(db)
    quarters = service.get_quarters(params)

    return SuccessResponse(
        data=quarters, message="Quarters retrieved successfully", errors=None
    )


@router.get("/quarters/current", response_model=SuccessResponse[Optional[Quarter]])
async def get_current_quarter(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
) -> SuccessResponse[Optional[Quarter]]:
    """Get the current active quarter."""
    service = SchedulingService(db)
    quarter = service.get_current_quarter()

    return SuccessResponse(
        data=quarter,
        message="Current quarter retrieved" if quarter else "No current quarter found",
        errors=None,
    )


@router.post("/quarters", response_model=CreatedResponse[Quarter])
async def create_quarter(
    quarter_in: QuarterCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Quarter]:
    """Create a new quarter. Coordinator or Admin only."""
    service = SchedulingService(db)
    quarter = service.create_quarter(quarter_in)

    return CreatedResponse(
        data=quarter, message="Quarter created successfully", errors=None
    )


@router.get("/quarters/{quarter_id}", response_model=SuccessResponse[Quarter])
async def get_quarter(
    quarter_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Quarter]:
    """Get quarter by ID."""
    service = SchedulingService(db)
    quarter = service.get_quarter(quarter_id)

    return SuccessResponse(
        data=quarter, message="Quarter retrieved successfully", errors=None
    )


@router.put("/quarters/{quarter_id}", response_model=UpdatedResponse[Quarter])
async def update_quarter(
    quarter_id: int,
    quarter_in: QuarterUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Quarter]:
    """Update quarter. Coordinator or Admin only."""
    service = SchedulingService(db)
    quarter = service.update_quarter(quarter_id, quarter_in)

    return UpdatedResponse(
        data=quarter, message="Quarter updated successfully", errors=None
    )


@router.delete("/quarters/{quarter_id}", response_model=DeletedResponse)
async def delete_quarter(
    quarter_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete quarter. Admin only."""
    service = SchedulingService(db)
    service.delete_quarter(quarter_id)

    return DeletedResponse(message="Quarter deleted successfully", errors=None)


# Class Schedule endpoints
@router.post(
    "/class-schedules/validate", response_model=SuccessResponse[ScheduleValidation]
)
async def validate_class_schedule(
    schedule_in: ClassScheduleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[ScheduleValidation]:
    """
    Validate a class schedule for conflicts.

    Returns validation result with any conflicts or warnings.
    """
    service = SchedulingService(db)
    validation = service.validate_schedule(schedule_in)

    return SuccessResponse(
        data=validation, message="Schedule validation completed", errors=None
    )


@router.get(
    "/class-schedules", response_model=SuccessResponse[Page[ClassScheduleDetailed]]
)
async def get_class_schedules(
    params: PaginationParams = Depends(get_pagination_params),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    instructor_id: Optional[int] = Query(None, description="Filter by instructor"),
    group_id: Optional[int] = Query(None, description="Filter by student group"),
    classroom_id: Optional[int] = Query(None, description="Filter by classroom"),
    quarter_id: Optional[int] = Query(None, description="Filter by quarter"),
    day_id: Optional[int] = Query(None, description="Filter by day"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[ClassScheduleDetailed]]:
    """Get paginated list of class schedules."""
    service = SchedulingService(db)
    schedules = service.get_class_schedules(
        params, subject, instructor_id, group_id, classroom_id, quarter_id, day_id
    )

    return SuccessResponse(
        data=schedules, message="Class schedules retrieved successfully", errors=None
    )


@router.post("/class-schedules", response_model=CreatedResponse[ClassScheduleDetailed])
async def create_class_schedule(
    schedule_in: ClassScheduleCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[ClassScheduleDetailed]:
    """
    Create a new class schedule.

    Coordinator or Admin only.
    Validates for conflicts before creating.
    """
    service = SchedulingService(db)
    schedule = service.create_class_schedule(schedule_in)

    return CreatedResponse(
        data=schedule, message="Class schedule created successfully", errors=None
    )


@router.get(
    "/class-schedules/{class_schedule_id}",
    response_model=SuccessResponse[ClassScheduleDetailed],
)
async def get_class_schedule(
    class_schedule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[ClassScheduleDetailed]:
    """Get class schedule by ID."""
    service = SchedulingService(db)
    schedule = service.get_class_schedule(class_schedule_id)

    return SuccessResponse(
        data=schedule, message="Class schedule retrieved successfully", errors=None
    )


@router.put(
    "/class-schedules/{class_schedule_id}",
    response_model=UpdatedResponse[ClassScheduleDetailed],
)
async def update_class_schedule(
    class_schedule_id: int,
    schedule_in: ClassScheduleUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[ClassScheduleDetailed]:
    """
    Update class schedule.

    Coordinator or Admin only.
    Validates for conflicts before updating.
    """
    service = SchedulingService(db)
    schedule = service.update_class_schedule(class_schedule_id, schedule_in)

    return UpdatedResponse(
        data=schedule, message="Class schedule updated successfully", errors=None
    )


@router.delete("/class-schedules/{class_schedule_id}", response_model=DeletedResponse)
async def delete_class_schedule(
    class_schedule_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete class schedule. Admin only."""
    service = SchedulingService(db)
    service.delete_class_schedule(class_schedule_id)

    return DeletedResponse(message="Class schedule deleted successfully", errors=None)


# Schedule queries
@router.get("/reports/schedule-matrix", response_model=SuccessResponse[dict])
async def get_schedule_matrix(
    quarter_id: int = Query(..., description="Quarter ID"),
    campus_id: Optional[int] = Query(None, description="Filter by campus"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[dict]:
    """
    Get schedule matrix showing all classes by day and time block.

    TODO: Implement using the view_schedule_matrix from database.
    """
    return SuccessResponse(
        data={"message": "To be implemented"},
        message="Feature coming soon",
        errors=None,
    )


@router.get("/reports/instructor-workload", response_model=SuccessResponse[list])
async def get_instructor_workload_report(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[list]:
    """
    Get instructor workload report.

    TODO: Implement using the view_instructor_workload from database.
    """
    return SuccessResponse(data=[], message="Feature coming soon", errors=None)
