"""
Custom exceptions for the application.
Provides a centralized way to handle business logic errors.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    """Base exception class for application-specific errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class NotFoundException(BaseAppException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        detail: str = "Resource not found",
        headers: Optional[Dict[str, str]] = None,
        error_code: str = "NOT_FOUND",
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class BadRequestException(BaseAppException):
    """Exception raised for invalid requests."""

    def __init__(
        self,
        detail: str = "Bad request",
        headers: Optional[Dict[str, str]] = None,
        error_code: str = "BAD_REQUEST",
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class UnauthorizedException(BaseAppException):
    """Exception raised when authentication fails."""

    def __init__(
        self,
        detail: str = "Unauthorized",
        headers: Optional[Dict[str, str]] = None,
        error_code: str = "UNAUTHORIZED",
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class ForbiddenException(BaseAppException):
    """Exception raised when user lacks permission."""

    def __init__(
        self,
        detail: str = "Forbidden",
        headers: Optional[Dict[str, str]] = None,
        error_code: str = "FORBIDDEN",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class ConflictException(BaseAppException):
    """Exception raised when there's a conflict with current state."""

    def __init__(
        self,
        detail: str = "Conflict",
        headers: Optional[Dict[str, str]] = None,
        error_code: str = "CONFLICT",
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


class ValidationException(BaseAppException):
    """Exception raised when validation fails."""

    def __init__(
        self,
        detail: str = "Validation error",
        headers: Optional[Dict[str, str]] = None,
        error_code: str = "VALIDATION_ERROR",
        errors: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )
        self.errors = errors or {}


class BusinessLogicException(BaseAppException):
    """Exception raised when business rules are violated."""

    def __init__(
        self,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        error_code: str = "BUSINESS_LOGIC_ERROR",
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
            error_code=error_code,
        )


# Specific business exceptions
class ScheduleConflictException(ConflictException):
    """Exception raised when there's a scheduling conflict."""

    def __init__(self, detail: str, conflict_type: str):
        super().__init__(
            detail=detail, error_code=f"SCHEDULE_CONFLICT_{conflict_type.upper()}"
        )


class InstructorOverloadException(BusinessLogicException):
    """Exception raised when instructor exceeds hour limit."""

    def __init__(self, instructor_name: str, current_hours: float, limit: float):
        super().__init__(
            detail=f"Instructor {instructor_name} would exceed hour limit. Current: {current_hours}h, Limit: {limit}h",
            error_code="INSTRUCTOR_OVERLOAD",
        )


class InsufficientCapacityException(BusinessLogicException):
    """Exception raised when classroom capacity is insufficient."""

    def __init__(self, classroom: str, required: int, available: int):
        super().__init__(
            detail=f"Classroom {classroom} has insufficient capacity. Required: {required}, Available: {available}",
            error_code="INSUFFICIENT_CAPACITY",
        )
