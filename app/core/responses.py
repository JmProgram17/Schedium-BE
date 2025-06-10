"""
Standardized response models for the API.
Ensures consistent response format across all endpoints.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseMeta(BaseModel):
    """Metadata for API responses."""

    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    version: str = Field(default="1.0", description="API version")


class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all API responses."""

    success: bool = Field(..., description="Indicates if the request was successful")
    message: str = Field(..., description="Human-readable message")
    data: Optional[T] = Field(None, description="Response data")
    meta: ResponseMeta = Field(
        default_factory=lambda: ResponseMeta(), description="Response metadata"
    )
    errors: Optional[Dict[str, Any]] = Field(None, description="Error details if any")


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Response model for paginated data."""

    success: bool = Field(default=True)
    message: str = Field(default="Data retrieved successfully")
    data: List[T] = Field(..., description="List of items")
    pagination: PaginationMeta = Field(..., description="Pagination information")
    meta: ResponseMeta = Field(default_factory=lambda: ResponseMeta())


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = Field(default=False)
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")
    errors: Optional[Dict[str, Any]] = Field(
        None, description="Detailed error information"
    )
    meta: ResponseMeta = Field(default_factory=lambda: ResponseMeta())


class SuccessResponse(BaseResponse[T]):
    """Standard success response."""

    success: bool = Field(default=True)


class CreatedResponse(BaseResponse[T]):
    """Response for successful resource creation."""

    success: bool = Field(default=True)
    message: str = Field(default="Resource created successfully")


class UpdatedResponse(BaseResponse[T]):
    """Response for successful resource update."""

    success: bool = Field(default=True)
    message: str = Field(default="Resource updated successfully")


class DeletedResponse(BaseResponse[None]):
    """Response for successful resource deletion."""

    success: bool = Field(default=True)
    message: str = Field(default="Resource deleted successfully")
    data: None = None


# Helper functions for creating responses
def create_success_response(
    data: Any,
    message: str = "Request successful",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {
        "success": True,
        "message": message,
        "data": data,
        "meta": {"timestamp": datetime.utcnow().isoformat(), "version": "1.0"},
    }
    if meta:
        meta_dict = response["meta"]
        assert isinstance(meta_dict, dict)
        meta_dict.update(meta)
    return response


def create_error_response(
    message: str,
    error_code: str,
    errors: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a standardized error response."""
    response = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "errors": errors,
        "meta": {"timestamp": datetime.utcnow().isoformat(), "version": "1.0"},
    }
    if meta:
        meta_dict = response["meta"]
        assert isinstance(meta_dict, dict)
        meta_dict.update(meta)
    return response
