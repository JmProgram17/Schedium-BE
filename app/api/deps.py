"""
API-specific dependencies.
Extends core dependencies with API-specific functionality.
"""

from typing import Optional

from fastapi import Depends, Query

from app.core.dependencies import *  # Re-export core dependencies
from app.core.pagination import PaginationParams, SortParams


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
) -> PaginationParams:
    """
    Get pagination parameters from query params.

    Args:
        page: Page number
        page_size: Items per page

    Returns:
        PaginationParams instance
    """
    return PaginationParams(page=page, page_size=page_size)


def get_sort_params(
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
) -> SortParams:
    """
    Get sorting parameters from query params.

    Args:
        sort_by: Field name to sort by
        sort_order: Sort order (asc/desc)

    Returns:
        SortParams instance
    """
    return SortParams(sort_by=sort_by, sort_order=sort_order)


class SearchParams:
    """Common search parameters."""

    def __init__(
        self,
        q: Optional[str] = Query(None, description="Search query"),
        fields: Optional[str] = Query(
            None, description="Fields to search in (comma-separated)"
        ),
    ):
        self.query = q
        self.fields = fields.split(",") if fields else None
