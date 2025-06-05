"""
Repositories package.
Provides data access layer for all domains.
"""

from app.repositories.base import BaseRepository

# Auth repositories
from app.repositories.auth import UserRepository, RoleRepository

# Academic repositories
from app.repositories.academic import (
    LevelRepository, ChainRepository, NomenclatureRepository,
    ProgramRepository, StudentGroupRepository
)

# HR repositories
from app.repositories.hr import (
    DepartmentRepository, ContractRepository, InstructorRepository
)

# Infrastructure repositories
from app.repositories.infrastructure import (
    CampusRepository, ClassroomRepository, DepartmentClassroomRepository
)

# Scheduling repositories
from app.repositories.scheduling import (
    ScheduleRepository, TimeBlockRepository, DayRepository,
    DayTimeBlockRepository, QuarterRepository, ClassScheduleRepository
)

__all__ = [
    # Base
    "BaseRepository",
    
    # Auth
    "UserRepository", "RoleRepository",
    
    # Academic
    "LevelRepository", "ChainRepository", "NomenclatureRepository",
    "ProgramRepository", "StudentGroupRepository",
    
    # HR
    "DepartmentRepository", "ContractRepository", "InstructorRepository",
    
    # Infrastructure
    "CampusRepository", "ClassroomRepository", "DepartmentClassroomRepository",
    
    # Scheduling
    "ScheduleRepository", "TimeBlockRepository", "DayRepository",
    "DayTimeBlockRepository", "QuarterRepository", "ClassScheduleRepository"
]