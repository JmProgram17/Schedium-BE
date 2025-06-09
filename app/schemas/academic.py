"""
Academic domain schemas.
Provides validation and serialization for academic entities.
"""

from datetime import date
from typing import List, Optional

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema, TimestampSchema


# Level Schemas
class LevelBase(BaseSchema):
    """Base level schema."""

    study_type: str = Field(
        ..., min_length=2, max_length=100, description="Type of study"
    )
    duration: Optional[int] = Field(
        None, gt=0, le=120, description="Duration in months"
    )


class LevelCreate(LevelBase):
    """Schema for creating a level."""

    pass


class LevelUpdate(BaseSchema):
    """Schema for updating a level."""

    study_type: Optional[str] = Field(None, min_length=2, max_length=100)
    duration: Optional[int] = Field(None, gt=0, le=120)


class Level(LevelBase, TimestampSchema):
    """Level schema for API responses."""

    level_id: int = Field(..., description="Level ID")


# Chain Schemas
class ChainBase(BaseSchema):
    """Base chain schema."""

    name: str = Field(..., min_length=2, max_length=100, description="Chain name")


class ChainCreate(ChainBase):
    """Schema for creating a chain."""

    pass


class ChainUpdate(BaseSchema):
    """Schema for updating a chain."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)


class Chain(ChainBase, TimestampSchema):
    """Chain schema for API responses."""

    chain_id: int = Field(..., description="Chain ID")


# Nomenclature Schemas
class NomenclatureBase(BaseSchema):
    """Base nomenclature schema."""

    code: str = Field(..., min_length=1, max_length=20, description="Abbreviation code")
    description: Optional[str] = Field(None, max_length=255, description="Description")
    active: bool = Field(True, description="Active status")


class NomenclatureCreate(NomenclatureBase):
    """Schema for creating a nomenclature."""

    pass


class NomenclatureUpdate(BaseSchema):
    """Schema for updating a nomenclature."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None


class Nomenclature(NomenclatureBase, TimestampSchema):
    """Nomenclature schema for API responses."""

    nomenclature_id: int = Field(..., description="Nomenclature ID")


# Program Schemas
class ProgramBase(BaseSchema):
    """Base program schema."""

    name: str = Field(..., min_length=2, max_length=255, description="Program name")
    nomenclature_id: Optional[int] = Field(None, description="Nomenclature ID")
    chain_id: Optional[int] = Field(None, description="Chain ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    level_id: Optional[int] = Field(None, description="Level ID")


class ProgramCreate(ProgramBase):
    """Schema for creating a program."""

    pass


class ProgramUpdate(BaseSchema):
    """Schema for updating a program."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    nomenclature_id: Optional[int] = None
    chain_id: Optional[int] = None
    department_id: Optional[int] = None
    level_id: Optional[int] = None


class Program(ProgramBase, TimestampSchema):
    """Program schema for API responses."""

    program_id: int = Field(..., description="Program ID")
    nomenclature: Optional[Nomenclature] = None
    chain: Optional[Chain] = None
    level: Optional[Level] = None


# Student Group Schemas
class StudentGroupBase(BaseSchema):
    """Base student group schema."""

    group_number: int = Field(..., gt=0, description="Group number (ficha)")
    program_id: int = Field(..., description="Program ID")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    capacity: int = Field(..., gt=0, le=100, description="Student capacity")
    schedule_id: int = Field(..., description="Schedule ID")
    active: bool = Field(True, description="Active status")

    @field_validator("end_date")
    def validate_dates(cls, v: date, info) -> date:
        """Validate end date is after start date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class StudentGroupCreate(StudentGroupBase):
    """Schema for creating a student group."""

    pass


class StudentGroupUpdate(BaseSchema):
    """Schema for updating a student group."""

    group_number: Optional[int] = Field(None, gt=0)
    program_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    capacity: Optional[int] = Field(None, gt=0, le=100)
    schedule_id: Optional[int] = None
    active: Optional[bool] = None


class StudentGroup(StudentGroupBase, TimestampSchema):
    """Student group schema for API responses."""

    group_id: int = Field(..., description="Group ID")
    program: Optional[Program] = None


class StudentGroupDisable(BaseSchema):
    """Schema for disabling a student group."""

    reason: Optional[str] = Field(
        None, max_length=255, description="Reason for disabling"
    )
