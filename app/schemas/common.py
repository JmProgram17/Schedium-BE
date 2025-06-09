"""
Common schemas used across domains.
Provides base schemas and shared models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class IDSchema(BaseSchema):
    """Schema with ID field."""

    id: int = Field(..., description="Unique identifier", gt=0)


class MessageSchema(BaseSchema):
    """Simple message response schema."""

    message: str = Field(..., description="Response message")


class StatusSchema(BaseSchema):
    """Status response schema."""

    status: str = Field(..., description="Status message")
    success: bool = Field(True, description="Operation success flag")


class ErrorDetailSchema(BaseSchema):
    """Error detail schema."""

    field: Optional[str] = Field(None, description="Field with error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class BulkResponseSchema(BaseSchema):
    """Response schema for bulk operations."""

    total: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successfully processed items")
    failed: int = Field(..., description="Failed items")
    errors: Optional[list[Dict[str, Any]]] = Field(None, description="Error details")
