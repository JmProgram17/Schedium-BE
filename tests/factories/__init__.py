"""Test data factories."""

from .academic import LevelFactory, ProgramFactory, StudentGroupFactory
from .auth import RoleFactory, UserFactory
from .hr import DepartmentFactory, InstructorFactory
from .infrastructure import CampusFactory, ClassroomFactory
from .scheduling import QuarterFactory, ScheduleFactory

__all__ = [
    "UserFactory",
    "RoleFactory",
    "LevelFactory",
    "ProgramFactory",
    "StudentGroupFactory",
    "DepartmentFactory",
    "InstructorFactory",
    "CampusFactory",
    "ClassroomFactory",
    "ScheduleFactory",
    "QuarterFactory",
]
