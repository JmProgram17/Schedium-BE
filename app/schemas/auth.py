"""
Authentication and authorization schemas.
Provides validation and serialization for auth domain.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import (
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
    validator,
)

from app.schemas.common import BaseSchema, TimestampSchema


# Role Schemas
class RoleBase(BaseSchema):
    """Base role schema."""

    name: str = Field(..., min_length=2, max_length=50, description="Role name")


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    pass


class RoleUpdate(BaseSchema):
    """Schema for updating a role."""

    name: Optional[str] = Field(None, min_length=2, max_length=50)


class RoleInDB(RoleBase, TimestampSchema):
    """Role schema for database representation."""

    role_id: int = Field(..., description="Role ID")


class Role(RoleInDB):
    """Role schema for API responses."""

    pass


# User Schemas
class UserBase(BaseSchema):
    """Base user schema."""

    first_name: str = Field(..., min_length=2, max_length=100, description="First name")
    last_name: str = Field(..., min_length=2, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    document_number: str = Field(
        ..., min_length=6, max_length=20, description="Document number"
    )
    role_id: Optional[int] = Field(None, description="Role ID")
    active: bool = Field(True, description="Active status")


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, description="User password")

    @field_validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    document_number: Optional[str] = Field(None, min_length=6, max_length=20)
    role_id: Optional[int] = None
    active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserInDB(UserBase, TimestampSchema):
    """User schema for database representation."""

    user_id: int = Field(..., description="User ID")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class User(UserInDB):
    """User schema for API responses."""

    role: Optional[Role] = Field(None, description="User role")

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"

    model_config = ConfigDict(from_attributes=True)


class UserWithoutPassword(User):
    """User schema without password field."""

    pass


# Authentication Schemas
class Token(BaseSchema):
    """JWT token response schema."""

    access_token: str = Field(..., description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: str = Field("bearer", description="Token type")


class TokenData(BaseSchema):
    """Token payload data schema."""

    user_id: int = Field(..., description="User ID from token")
    email: Optional[str] = Field(None, description="User email")
    role: Optional[str] = Field(None, description="User role")


class LoginRequest(BaseSchema):
    """Login request schema."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class ChangePasswordRequest(BaseSchema):
    """Change password request schema."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    def validate_new_password(cls, v: str, info: Any) -> str:
        """Validate new password is different from current."""
        if "current_password" in info.data and v == info.data["current_password"]:
            raise ValueError("New password must be different from current password")
        return v
