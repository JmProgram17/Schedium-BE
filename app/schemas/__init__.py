"""
Schemas package initialization.
Re-exports all schemas for convenient imports.
"""

# Common schemas
from app.schemas.common import (
    BaseSchema,
    TimestampSchema,
    IDSchema,
    MessageSchema,
    StatusSchema,
    ErrorDetailSchema,
    BulkResponseSchema
)

# Auth schemas
from app.schemas.auth import (
    # Role
    RoleBase,
    RoleCreate,
    RoleUpdate,
    Role,
    
    # User
    UserBase,
    UserCreate,
    UserUpdate,
    User,
    UserWithoutPassword,
    
    # Authentication
    Token,
    TokenData,
    LoginRequest,
    ChangePasswordRequest
)

# Academic schemas
from app.schemas.academic import (
    # Level
    LevelBase,
    LevelCreate,
    LevelUpdate,
    Level,
    
    # Chain
    ChainBase,
    ChainCreate,
    ChainUpdate,
    Chain,
    
    # Nomenclature
    NomenclatureBase,
    NomenclatureCreate,
    NomenclatureUpdate,
    Nomenclature,
    
    # Program
    ProgramBase,
    ProgramCreate,
    ProgramUpdate,
    Program,
    
    # Student Group
    StudentGroupBase,
    StudentGroupCreate,
    StudentGroupUpdate,
    StudentGroup,
    StudentGroupDisable
)

# HR schemas
from app.schemas.hr import (
    # Department
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    Department,
    
    # Contract
    ContractBase,
    ContractCreate,
    ContractUpdate,
    Contract,
    
    # Instructor
    InstructorBase,
    InstructorCreate,
    InstructorUpdate,
    Instructor,
    InstructorWorkload
)

# Infrastructure schemas
from app.schemas.infrastructure import (
    # Campus
    CampusBase,
    CampusCreate,
    CampusUpdate,
    Campus,
    
    # Classroom
    ClassroomBase,
    ClassroomCreate,
    ClassroomUpdate,
    Classroom,
    
    # Department-Classroom
    DepartmentClassroomBase,
    DepartmentClassroomCreate,
    DepartmentClassroomUpdate,
    DepartmentClassroom,
    ClassroomAvailability
)

# Scheduling schemas
from app.schemas.scheduling import (
    # Schedule
    ScheduleBase,
    ScheduleCreate,
    ScheduleUpdate,
    Schedule,
    
    # Time Block
    TimeBlockBase,
    TimeBlockCreate,
    TimeBlockUpdate,
    TimeBlock,
    
    # Day
    DayBase,
    Day,
    
    # Day-Time Block
    DayTimeBlockBase,
    DayTimeBlockCreate,
    DayTimeBlock,
    
    # Quarter
    QuarterBase,
    QuarterCreate,
    QuarterUpdate,
    Quarter,
    
    # Class Schedule
    ClassScheduleBase,
    ClassScheduleCreate,
    ClassScheduleUpdate,
    ClassSchedule,
    ClassScheduleDetailed,
    ScheduleConflict,
    ScheduleValidation
)

__all__ = [
    # Common
    "BaseSchema", "TimestampSchema", "IDSchema", "MessageSchema",
    "StatusSchema", "ErrorDetailSchema", "BulkResponseSchema",
    
    # Auth
    "RoleBase", "RoleCreate", "RoleUpdate", "Role",
    "UserBase", "UserCreate", "UserUpdate", "User", "UserWithoutPassword",
    "Token", "TokenData", "LoginRequest", "ChangePasswordRequest",
    
    # Academic
    "LevelBase", "LevelCreate", "LevelUpdate", "Level",
    "ChainBase", "ChainCreate", "ChainUpdate", "Chain",
    "NomenclatureBase", "NomenclatureCreate", "NomenclatureUpdate", "Nomenclature",
    "ProgramBase", "ProgramCreate", "ProgramUpdate", "Program",
    "StudentGroupBase", "StudentGroupCreate", "StudentGroupUpdate", "StudentGroup", "StudentGroupDisable",
    
    # HR
    "DepartmentBase", "DepartmentCreate", "DepartmentUpdate", "Department",
    "ContractBase", "ContractCreate", "ContractUpdate", "Contract",
    "InstructorBase", "InstructorCreate", "InstructorUpdate", "Instructor", "InstructorWorkload",
    
    # Infrastructure
    "CampusBase", "CampusCreate", "CampusUpdate", "Campus",
    "ClassroomBase", "ClassroomCreate", "ClassroomUpdate", "Classroom",
    "DepartmentClassroomBase", "DepartmentClassroomCreate", "DepartmentClassroomUpdate",
    "DepartmentClassroom", "ClassroomAvailability",
    
    # Scheduling
    "ScheduleBase", "ScheduleCreate", "ScheduleUpdate", "Schedule",
    "TimeBlockBase", "TimeBlockCreate", "TimeBlockUpdate", "TimeBlock",
    "DayBase", "Day",
    "DayTimeBlockBase", "DayTimeBlockCreate", "DayTimeBlock",
    "QuarterBase", "QuarterCreate", "QuarterUpdate", "Quarter",
    "ClassScheduleBase", "ClassScheduleCreate", "ClassScheduleUpdate",
    "ClassSchedule", "ClassScheduleDetailed", "ScheduleConflict", "ScheduleValidation"
]