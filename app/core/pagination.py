"""
Pagination utilities for list endpoints.
Provides consistent pagination across the application.
"""

from math import ceil
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Query

from app.config import settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for requests."""

    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE)

    @field_validator("page_size")
    def validate_page_size(cls, v: int) -> int:
        """Ensure page size is within allowed limits."""
        if v > settings.MAX_PAGE_SIZE:
            return settings.MAX_PAGE_SIZE
        return v

    @property
    def skip(self) -> int:
        """Calculate the number of records to skip."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get the limit for the query."""
        return self.page_size


class Page(BaseModel, Generic[T]):
    """Paginated response model."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True


def paginate(
    query: Query,
    params: PaginationParams,
    response_model: Optional[Type[BaseModel]] = None,
) -> Page:
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query object
        params: Pagination parameters
        response_model: Optional Pydantic model for serialization

    Returns:
        Page object with paginated results
    """
    # Get total count
    total = query.count()

    # Calculate total pages
    total_pages = ceil(total / params.page_size) if total > 0 else 0

    # Apply pagination
    items = query.offset(params.skip).limit(params.limit).all()

    # Serialize if response model provided
    if response_model:
        items = [response_model.model_validate(item) for item in items]

    return Page(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )


def paginate_list(
    items: List[Any], params: PaginationParams, total: Optional[int] = None
) -> Page:
    """
    Paginate a list of items.

    Args:
        items: List of items to paginate
        params: Pagination parameters
        total: Optional total count (if different from len(items))

    Returns:
        Page object with paginated results
    """
    if total is None:
        total = len(items)

    # Calculate total pages
    total_pages = ceil(total / params.page_size) if total > 0 else 0

    # Apply pagination to list
    start = params.skip
    end = start + params.page_size
    paginated_items = items[start:end]

    return Page(
        items=paginated_items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )


class SortParams(BaseModel):
    """Sorting parameters for requests."""

    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

    @property
    def is_desc(self) -> bool:
        """Check if sort order is descending."""
        return self.sort_order.lower() == "desc"


class FilterParams(BaseModel):
    """Base class for filter parameters."""

    search: Optional[str] = Field(None, description="Search term")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
