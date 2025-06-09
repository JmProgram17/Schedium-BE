"""
Repositories package.
Provides data access layer for all domains.
"""

# Academic repositories
from app.repositories.academic import (
    ChainRepository,
    LevelRepository,
    NomenclatureRepository,
    ProgramRepository,
    StudentGroupRepository,
)

# Auth repositories
from app.repositories.auth import RoleRepository, UserRepository
from app.repositories.base import BaseRepository

# HR repositories
from app.repositories.hr import (
    ContractRepository,
    DepartmentRepository,
    InstructorRepository,
)

# Infrastructure repositories
from app.repositories.infrastructure import (
    CampusRepository,
    ClassroomRepository,
    DepartmentClassroomRepository,
)

# Scheduling repositories
from app.repositories.scheduling import (
    ClassScheduleRepository,
    DayRepository,
    DayTimeBlockRepository,
    QuarterRepository,
    ScheduleRepository,
    TimeBlockRepository,
)

__all__ = [
    # Base
    "BaseRepository",
    # Auth
    "UserRepository",
    "RoleRepository",
    # Academic
    "LevelRepository",
    "ChainRepository",
    "NomenclatureRepository",
    "ProgramRepository",
    "StudentGroupRepository",
    # HR
    "DepartmentRepository",
    "ContractRepository",
    "InstructorRepository",
    # Infrastructure
    "CampusRepository",
    "ClassroomRepository",
    "DepartmentClassroomRepository",
    # Scheduling
    "ScheduleRepository",
    "TimeBlockRepository",
    "DayRepository",
    "DayTimeBlockRepository",
    "QuarterRepository",
    "ClassScheduleRepository",
]
