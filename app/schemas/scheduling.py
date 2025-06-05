"""
Scheduling domain schemas.
Provides validation and serialization for scheduling entities.
"""

from typing import Optional, List
from datetime import date, time
from pydantic import Field, field_validator, model_validator
from app.schemas.common import BaseSchema, TimestampSchema


# Schedule (Jornada) Schemas
class ScheduleBase(BaseSchema):
    """Base schedule schema."""
    
    name: str = Field(..., min_length=2, max_length=50, description="Schedule name")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    
    @model_validator(mode='after')
    def validate_times(self) -> 'ScheduleBase':
        """Validate end time is after start time."""
        if self.end_time <= self.start_time:
            raise ValueError('End time must be after start time')
        return self


class ScheduleCreate(ScheduleBase):
    """Schema for creating a schedule."""
    pass


class ScheduleUpdate(BaseSchema):
    """Schema for updating a schedule."""
    
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class Schedule(ScheduleBase, TimestampSchema):
    """Schedule schema for API responses."""
    
    schedule_id: int = Field(..., description="Schedule ID")


# Time Block Schemas
class TimeBlockBase(BaseSchema):
    """Base time block schema."""
    
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    
    @model_validator(mode='after')
    def validate_times(self) -> 'TimeBlockBase':
        """Validate end time is after start time."""
        if self.end_time <= self.start_time:
            raise ValueError('End time must be after start time')
        return self


class TimeBlockCreate(TimeBlockBase):
    """Schema for creating a time block."""
    pass


class TimeBlockUpdate(BaseSchema):
    """Schema for updating a time block."""
    
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class TimeBlock(TimeBlockBase, TimestampSchema):
    """Time block schema for API responses."""
    
    time_block_id: int = Field(..., description="Time block ID")
    duration_minutes: int = Field(..., description="Duration in minutes")


# Day Schemas
class DayBase(BaseSchema):
    """Base day schema."""
    
    name: str = Field(..., min_length=2, max_length=20, description="Day name")


class Day(DayBase, TimestampSchema):
    """Day schema for API responses."""
    
    day_id: int = Field(..., description="Day ID")


# Day-Time Block Schemas
class DayTimeBlockBase(BaseSchema):
    """Base day-time block schema."""
    
    day_id: int = Field(..., description="Day ID")
    time_block_id: int = Field(..., description="Time block ID")


class DayTimeBlockCreate(DayTimeBlockBase):
    """Schema for creating a day-time block."""
    pass


class DayTimeBlock(DayTimeBlockBase, TimestampSchema):
    """Day-time block schema for API responses."""
    
    day_time_block_id: int = Field(..., description="Day-time block ID")
    day: Optional[Day] = None
    time_block: Optional[TimeBlock] = None


# Quarter Schemas
class QuarterBase(BaseSchema):
    """Base quarter schema."""
    
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    
    @model_validator(mode='after')
    def validate_dates(self) -> 'QuarterBase':
        """Validate end date is after start date."""
        if self.end_date <= self.start_date:
            raise ValueError('End date must be after start date')
        return self


class QuarterCreate(QuarterBase):
    """Schema for creating a quarter."""
    pass


class QuarterUpdate(BaseSchema):
    """Schema for updating a quarter."""
    
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class Quarter(QuarterBase, TimestampSchema):
    """Quarter schema for API responses."""
    
    quarter_id: int = Field(..., description="Quarter ID")
    name: str = Field(..., description="Quarter name")


# Class Schedule Schemas
class ClassScheduleBase(BaseSchema):
    """Base class schedule schema."""
    
    subject: str = Field(..., min_length=2, max_length=255, description="Subject name")
    quarter_id: int = Field(..., description="Quarter ID")
    day_time_block_id: int = Field(..., description="Day-time block ID")
    group_id: int = Field(..., description="Student group ID")
    instructor_id: int = Field(..., description="Instructor ID")
    classroom_id: int = Field(..., description="Classroom ID")


class ClassScheduleCreate(ClassScheduleBase):
    """Schema for creating a class schedule."""
    pass


class ClassScheduleUpdate(BaseSchema):
    """Schema for updating a class schedule."""
    
    subject: Optional[str] = Field(None, min_length=2, max_length=255)
    quarter_id: Optional[int] = None
    day_time_block_id: Optional[int] = None
    group_id: Optional[int] = None
    instructor_id: Optional[int] = None
    classroom_id: Optional[int] = None


class ClassSchedule(ClassScheduleBase, TimestampSchema):
    """Class schedule schema for API responses."""
    
    class_schedule_id: int = Field(..., description="Class schedule ID")
    quarter: Optional[Quarter] = None
    day_time_block: Optional[DayTimeBlock] = None


class ClassScheduleDetailed(ClassSchedule):
    """Detailed class schedule schema with all relationships."""
    
    group: Optional['StudentGroup'] = None
    instructor: Optional['Instructor'] = None
    classroom: Optional['Classroom'] = None


class ScheduleConflict(BaseSchema):
    """Schedule conflict information schema."""
    
    conflict_type: str = Field(..., description="Type of conflict (instructor/classroom/group)")
    resource_id: int = Field(..., description="ID of conflicting resource")
    resource_name: str = Field(..., description="Name of conflicting resource")
    existing_schedule_id: int = Field(..., description="ID of existing schedule")
    existing_subject: str = Field(..., description="Subject of existing schedule")
    day: str = Field(..., description="Day of conflict")
    time_block: str = Field(..., description="Time block of conflict")


class ScheduleValidation(BaseSchema):
    """Schedule validation result schema."""
    
    is_valid: bool = Field(..., description="Whether the schedule is valid")
    conflicts: List[ScheduleConflict] = Field(default_factory=list, description="List of conflicts")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")


# Update forward references
from app.schemas.academic import StudentGroup
from app.schemas.hr import Instructor
from app.schemas.infrastructure import Classroom

ClassScheduleDetailed.model_rebuild()