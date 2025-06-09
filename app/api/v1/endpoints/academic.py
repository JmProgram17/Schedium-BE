"""
Academic domain endpoints.
Handles levels, chains, nomenclatures, programs, and student groups.
"""

from datetime import date
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
from app.schemas.academic import (
    Chain,
    ChainCreate,
    ChainUpdate,
    Level,
    LevelCreate,
    LevelUpdate,
    Nomenclature,
    NomenclatureCreate,
    NomenclatureUpdate,
    Program,
    ProgramCreate,
    ProgramUpdate,
    StudentGroup,
    StudentGroupCreate,
    StudentGroupDisable,
    StudentGroupUpdate,
)
from app.schemas.auth import User
from app.services.academic import AcademicService

router = APIRouter()


# Level endpoints
@router.get("/levels", response_model=SuccessResponse[Page[Level]])
async def get_levels(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Level]]:
    """Get paginated list of academic levels."""
    service = AcademicService(db)
    levels = service.get_levels(params)

    return SuccessResponse(
        data=levels, message="Levels retrieved successfully", errors=None
    )


@router.post("/levels", response_model=CreatedResponse[Level])
async def create_level(
    level_in: LevelCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Level]:
    """Create a new academic level. Coordinator or Admin only."""
    service = AcademicService(db)
    level = service.create_level(level_in)

    return CreatedResponse(
        data=level, message="Level created successfully", errors=None
    )


@router.get("/levels/{level_id}", response_model=SuccessResponse[Level])
async def get_level(
    level_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Level]:
    """Get academic level by ID."""
    service = AcademicService(db)
    level = service.get_level(level_id)

    return SuccessResponse(
        data=level, message="Level retrieved successfully", errors=None
    )


@router.put("/levels/{level_id}", response_model=UpdatedResponse[Level])
async def update_level(
    level_id: int,
    level_in: LevelUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Level]:
    """Update academic level. Coordinator or Admin only."""
    service = AcademicService(db)
    level = service.update_level(level_id, level_in)

    return UpdatedResponse(
        data=level, message="Level updated successfully", errors=None
    )


@router.delete("/levels/{level_id}", response_model=DeletedResponse)
async def delete_level(
    level_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete academic level. Admin only."""
    service = AcademicService(db)
    service.delete_level(level_id)

    return DeletedResponse(message="Level deleted successfully", errors=None)


# Chain endpoints
@router.get("/chains", response_model=SuccessResponse[Page[Chain]])
async def get_chains(
    params: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Chain]]:
    """Get paginated list of program chains."""
    service = AcademicService(db)
    chains = service.get_chains(params)

    return SuccessResponse(
        data=chains, message="Chains retrieved successfully", errors=None
    )


@router.post("/chains", response_model=CreatedResponse[Chain])
async def create_chain(
    chain_in: ChainCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Chain]:
    """Create a new program chain. Coordinator or Admin only."""
    service = AcademicService(db)
    chain = service.create_chain(chain_in)

    return CreatedResponse(
        data=chain, message="Chain created successfully", errors=None
    )


@router.get("/chains/{chain_id}", response_model=SuccessResponse[Chain])
async def get_chain(
    chain_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Chain]:
    """Get program chain by ID."""
    service = AcademicService(db)
    chain = service.get_chain(chain_id)

    return SuccessResponse(
        data=chain, message="Chain retrieved successfully", errors=None
    )


@router.put("/chains/{chain_id}", response_model=UpdatedResponse[Chain])
async def update_chain(
    chain_id: int,
    chain_in: ChainUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Chain]:
    """Update program chain. Coordinator or Admin only."""
    service = AcademicService(db)
    chain = service.update_chain(chain_id, chain_in)

    return UpdatedResponse(
        data=chain, message="Chain updated successfully", errors=None
    )


@router.delete("/chains/{chain_id}", response_model=DeletedResponse)
async def delete_chain(
    chain_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete program chain. Admin only."""
    service = AcademicService(db)
    service.delete_chain(chain_id)

    return DeletedResponse(message="Chain deleted successfully", errors=None)


# Nomenclature endpoints
@router.get("/nomenclatures", response_model=SuccessResponse[Page[Nomenclature]])
async def get_nomenclatures(
    params: PaginationParams = Depends(get_pagination_params),
    active_only: bool = Query(False, description="Return only active nomenclatures"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Nomenclature]]:
    """Get paginated list of nomenclatures."""
    service = AcademicService(db)
    nomenclatures = service.get_nomenclatures(params, active_only)

    return SuccessResponse(
        data=nomenclatures, message="Nomenclatures retrieved successfully", errors=None
    )


@router.post("/nomenclatures", response_model=CreatedResponse[Nomenclature])
async def create_nomenclature(
    nomenclature_in: NomenclatureCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Nomenclature]:
    """Create a new nomenclature. Coordinator or Admin only."""
    service = AcademicService(db)
    nomenclature = service.create_nomenclature(nomenclature_in)

    return CreatedResponse(
        data=nomenclature, message="Nomenclature created successfully", errors=None
    )


@router.get(
    "/nomenclatures/{nomenclature_id}", response_model=SuccessResponse[Nomenclature]
)
async def get_nomenclature(
    nomenclature_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Nomenclature]:
    """Get nomenclature by ID."""
    service = AcademicService(db)
    nomenclature = service.get_nomenclature(nomenclature_id)

    return SuccessResponse(
        data=nomenclature, message="Nomenclature retrieved successfully", errors=None
    )


@router.put(
    "/nomenclatures/{nomenclature_id}", response_model=UpdatedResponse[Nomenclature]
)
async def update_nomenclature(
    nomenclature_id: int,
    nomenclature_in: NomenclatureUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Nomenclature]:
    """Update nomenclature. Coordinator or Admin only."""
    service = AcademicService(db)
    nomenclature = service.update_nomenclature(nomenclature_id, nomenclature_in)

    return UpdatedResponse(
        data=nomenclature, message="Nomenclature updated successfully", errors=None
    )


@router.delete("/nomenclatures/{nomenclature_id}", response_model=DeletedResponse)
async def delete_nomenclature(
    nomenclature_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete nomenclature. Admin only."""
    service = AcademicService(db)
    service.delete_nomenclature(nomenclature_id)

    return DeletedResponse(message="Nomenclature deleted successfully", errors=None)


# Program endpoints
@router.get("/programs", response_model=SuccessResponse[Page[Program]])
async def get_programs(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(
        None, description="Search in program name or nomenclature"
    ),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    level_id: Optional[int] = Query(None, description="Filter by level"),
    chain_id: Optional[int] = Query(None, description="Filter by chain"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[Program]]:
    """Get paginated list of academic programs."""
    service = AcademicService(db)
    programs = service.get_programs(params, search, department_id, level_id, chain_id)

    return SuccessResponse(
        data=programs, message="Programs retrieved successfully", errors=None
    )


@router.post("/programs", response_model=CreatedResponse[Program])
async def create_program(
    program_in: ProgramCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[Program]:
    """Create a new academic program. Coordinator or Admin only."""
    service = AcademicService(db)
    program = service.create_program(program_in)

    return CreatedResponse(
        data=program, message="Program created successfully", errors=None
    )


@router.get("/programs/{program_id}", response_model=SuccessResponse[Program])
async def get_program(
    program_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Program]:
    """Get academic program by ID."""
    service = AcademicService(db)
    program = service.get_program(program_id)

    return SuccessResponse(
        data=program, message="Program retrieved successfully", errors=None
    )


@router.put("/programs/{program_id}", response_model=UpdatedResponse[Program])
async def update_program(
    program_id: int,
    program_in: ProgramUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[Program]:
    """Update academic program. Coordinator or Admin only."""
    service = AcademicService(db)
    program = service.update_program(program_id, program_in)

    return UpdatedResponse(
        data=program, message="Program updated successfully", errors=None
    )


@router.delete("/programs/{program_id}", response_model=DeletedResponse)
async def delete_program(
    program_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete academic program. Admin only."""
    service = AcademicService(db)
    service.delete_program(program_id)

    return DeletedResponse(message="Program deleted successfully", errors=None)


# Student Group endpoints
@router.get("/groups", response_model=SuccessResponse[Page[StudentGroup]])
async def get_student_groups(
    params: PaginationParams = Depends(get_pagination_params),
    search: Optional[str] = Query(
        None, description="Search by group number or program"
    ),
    program_id: Optional[int] = Query(None, description="Filter by program"),
    schedule_id: Optional[int] = Query(None, description="Filter by schedule"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    start_date_from: Optional[date] = Query(
        None, description="Filter by start date from"
    ),
    start_date_to: Optional[date] = Query(None, description="Filter by start date to"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[Page[StudentGroup]]:
    """Get paginated list of student groups (fichas)."""
    service = AcademicService(db)
    groups = service.get_student_groups(
        params, search, program_id, schedule_id, active, start_date_from, start_date_to
    )

    return SuccessResponse(
        data=groups, message="Student groups retrieved successfully", errors=None
    )


@router.post("/groups", response_model=CreatedResponse[StudentGroup])
async def create_student_group(
    group_in: StudentGroupCreate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> CreatedResponse[StudentGroup]:
    """Create a new student group. Coordinator or Admin only."""
    service = AcademicService(db)
    group = service.create_student_group(group_in)

    return CreatedResponse(
        data=group, message="Student group created successfully", errors=None
    )


@router.get("/groups/{group_id}", response_model=SuccessResponse[StudentGroup])
async def get_student_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SuccessResponse[StudentGroup]:
    """Get student group by ID."""
    service = AcademicService(db)
    group = service.get_student_group(group_id)

    return SuccessResponse(
        data=group, message="Student group retrieved successfully", errors=None
    )


@router.put("/groups/{group_id}", response_model=UpdatedResponse[StudentGroup])
async def update_student_group(
    group_id: int,
    group_in: StudentGroupUpdate,
    current_user: User = Depends(require_coordinator),
    db: Session = Depends(get_db),
) -> UpdatedResponse[StudentGroup]:
    """Update student group. Coordinator or Admin only."""
    service = AcademicService(db)
    group = service.update_student_group(group_id, group_in)

    return UpdatedResponse(
        data=group, message="Student group updated successfully", errors=None
    )


@router.patch(
    "/groups/{group_id}/disable", response_model=UpdatedResponse[StudentGroup]
)
async def disable_student_group(
    group_id: int,
    disable_data: StudentGroupDisable,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UpdatedResponse[StudentGroup]:
    """
    Disable a student group (soft delete).

    Available to all authenticated users as per requirements.
    """
    service = AcademicService(db)
    group = service.disable_student_group(group_id, disable_data)

    return UpdatedResponse(
        data=group, message="Student group disabled successfully", errors=None
    )


@router.delete("/groups/{group_id}", response_model=DeletedResponse)
async def delete_student_group(
    group_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> DeletedResponse:
    """Delete student group. Admin only."""
    service = AcademicService(db)
    service.delete_student_group(group_id)

    return DeletedResponse(message="Student group deleted successfully", errors=None)
