"""
Human resources domain schemas.
Provides validation and serialization for HR entities.
"""

from decimal import Decimal
from typing import Optional

from pydantic import EmailStr, Field, field_validator, model_validator

from app.schemas.common import BaseSchema, TimestampSchema
from app.utils.validators import validate_phone


# Department Schemas
class DepartmentBase(BaseSchema):
    """Base department schema."""

    name: str = Field(..., min_length=2, max_length=100, description="Department name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[EmailStr] = Field(None, description="Email address")

    @field_validator("phone_number")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v and not validate_phone(v):
            raise ValueError("Invalid phone number format")
        return v


class DepartmentCreate(DepartmentBase):
    """Schema for creating a department."""

    pass


class DepartmentUpdate(BaseSchema):
    """Schema for updating a department."""

    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None


class Department(DepartmentBase, TimestampSchema):
    """Department schema for API responses."""

    department_id: int = Field(..., description="Department ID")


# Contract Schemas
class ContractBase(BaseSchema):
    """Base contract schema."""

    contract_type: str = Field(
        ..., min_length=2, max_length=100, description="Contract type"
    )
    hour_limit: Optional[int] = Field(
        None, gt=0, le=200, description="Hour limit per period"
    )


class ContractCreate(ContractBase):
    """Schema for creating a contract."""

    pass


class ContractUpdate(BaseSchema):
    """Schema for updating a contract."""

    contract_type: Optional[str] = Field(None, min_length=2, max_length=100)
    hour_limit: Optional[int] = Field(None, gt=0, le=200)


class Contract(ContractBase, TimestampSchema):
    """Contract schema for API responses."""

    contract_id: int = Field(..., description="Contract ID")


# Instructor Schemas
class InstructorBase(BaseSchema):
    """Base instructor schema."""

    first_name: str = Field(..., min_length=2, max_length=100, description="First name")
    last_name: str = Field(..., min_length=2, max_length=100, description="Last name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: EmailStr = Field(..., description="Email address")
    contract_id: Optional[int] = Field(None, description="Contract ID")
    department_id: Optional[int] = Field(None, description="Department ID")
    active: bool = Field(True, description="Active status")

    @field_validator("phone_number")
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v and not validate_phone(v):
            raise ValueError("Invalid phone number format")
        return v


class InstructorCreate(InstructorBase):
    """Schema for creating an instructor."""

    pass


class InstructorUpdate(BaseSchema):
    """Schema for updating an instructor."""

    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    contract_id: Optional[int] = None
    department_id: Optional[int] = None
    active: Optional[bool] = None


class Instructor(InstructorBase, TimestampSchema):
    """Instructor schema for API responses."""

    instructor_id: int = Field(..., description="Instructor ID")
    hour_count: Decimal = Field(..., description="Total assigned hours")
    contract: Optional[Contract] = None
    department: Optional[Department] = None
    full_name: str = Field(..., description="Full name")

    @model_validator(mode="after")
    def add_full_name(self) -> "Instructor":
        """Add computed full name."""
        self.full_name = f"{self.first_name} {self.last_name}"
        return self


class InstructorWorkload(BaseSchema):
    """Instructor workload schema."""

    instructor_id: int = Field(..., description="Instructor ID")
    full_name: str = Field(..., description="Instructor full name")
    total_hours: Decimal = Field(..., description="Total assigned hours")
    contract_limit: Optional[int] = Field(None, description="Contract hour limit")
    available_hours: Optional[Decimal] = Field(None, description="Available hours")
    utilization_percentage: Optional[float] = Field(
        None, description="Utilization percentage"
    )
    status: str = Field(..., description="Workload status")
