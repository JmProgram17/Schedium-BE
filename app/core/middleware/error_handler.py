# app/core/middleware/error_handler.py
"""
Global error handler middleware.
Catches and formats all exceptions consistently.
"""

import sys
import traceback
from typing import Any, Callable, Dict, List

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.config import settings
from app.core.exceptions import (
    BaseAppException,
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.logging import get_logger
from app.core.security.validators import SecurityValidator

logger = get_logger(__name__)


class ErrorHandlerMiddleware:
    """Global error handler for consistent error responses."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.validator = SecurityValidator()

        # Register exception handlers
        app.add_exception_handler(BaseAppException, self.handle_app_exception)  # type: ignore
        app.add_exception_handler(RequestValidationError, self.handle_validation_error)  # type: ignore
        app.add_exception_handler(ValidationError, self.handle_pydantic_error)  # type: ignore
        app.add_exception_handler(StarletteHTTPException, self.handle_http_exception)  # type: ignore
        app.add_exception_handler(IntegrityError, self.handle_db_integrity_error)  # type: ignore
        app.add_exception_handler(OperationalError, self.handle_db_operational_error)  # type: ignore
        app.add_exception_handler(Exception, self.handle_unexpected_error)  # type: ignore

    async def __call__(self, request: Request, call_next: Callable[..., Any]) -> Response:
        """Process request with error handling."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # This catches any exceptions not handled by specific handlers
            return await self.handle_unexpected_error(request, exc)

    async def handle_app_exception(self, request: Request, exc: BaseAppException) -> JSONResponse:
        """Handle custom application exceptions."""
        log_data: Dict[str, Any] = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "error_code": getattr(exc, "error_code", "UNKNOWN"),
            "user_id": getattr(request.state, "user_id", None),
        }

        # Log based on exception type
        if isinstance(exc, UnauthorizedException):
            logger.warning(f"Authentication error: {exc.detail}", extra=log_data)
        elif isinstance(exc, NotFoundException):
            logger.info(f"Resource not found: {exc.detail}", extra=log_data)
        elif isinstance(exc, ConflictException):
            logger.warning(f"Conflict error: {exc.detail}", extra=log_data)
        else:
            logger.error(f"Application error: {exc.detail}", extra=log_data)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": getattr(exc, "error_code", "APP_ERROR"),
                    "message": exc.detail,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
            headers=getattr(exc, "headers", None),
        )

    async def handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors."""
        errors: List[Dict[str, Any]] = []

        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
            })

        log_data: Dict[str, Any] = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "errors": errors,
            "user_id": getattr(request.state, "user_id", None),
        }

        logger.warning("Validation error", extra=log_data)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": errors,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    async def handle_pydantic_error(self, request: Request, exc: ValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors: List[Dict[str, Any]] = []

        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Data validation failed",
                    "details": errors,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    async def handle_http_exception(self, request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
            headers=getattr(exc, "headers", None),
        )

    async def handle_db_integrity_error(self, request: Request, exc: IntegrityError) -> JSONResponse:
        """Handle database integrity errors."""
        # Sanitize error message to not expose DB structure
        sanitized_message = self.validator.sanitize_log_message(str(exc))

        log_data: Dict[str, Any] = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "error": sanitized_message,
            "user_id": getattr(request.state, "user_id", None),
        }

        logger.error("Database integrity error", extra=log_data)

        # Parse common integrity errors
        error_str = str(exc.orig) if hasattr(exc, "orig") else str(exc)

        if "duplicate" in error_str.lower() or "unique" in error_str.lower():
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": {
                        "code": "DUPLICATE_RESOURCE",
                        "message": "Resource already exists",
                        "request_id": getattr(request.state, "request_id", None),
                    }
                },
            )
        elif "foreign key" in error_str.lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "INVALID_REFERENCE",
                        "message": "Referenced resource does not exist",
                        "request_id": getattr(request.state, "request_id", None),
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "DATA_INTEGRITY_ERROR",
                        "message": "Data integrity constraint violated",
                        "request_id": getattr(request.state, "request_id", None),
                    }
                },
            )

    async def handle_db_operational_error(self, request: Request, exc: OperationalError) -> JSONResponse:
        """Handle database operational errors."""
        log_data: Dict[str, Any] = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "error": str(exc),
            "user_id": getattr(request.state, "user_id", None),
        }

        logger.critical("Database operational error", extra=log_data)

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database service is temporarily unavailable",
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    async def handle_unexpected_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors."""
        # Get exception details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)

        log_data: Dict[str, Any] = {
            "request_id": getattr(request.state, "request_id", None),
            "method": request.method,
            "path": request.url.path,
            "error_type": exc_type.__name__ if exc_type else "Unknown",
            "error_message": str(exc),
            "traceback": "".join(tb_lines) if settings.DEBUG else "[REDACTED]",
            "user_id": getattr(request.state, "user_id", None),
        }

        logger.critical("Unexpected error occurred", extra=log_data, exc_info=True)

        # Response based on environment
        if settings.DEBUG:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": str(exc),
                        "type": exc_type.__name__ if exc_type else "Unknown",
                        "traceback": tb_lines[-5:],  # Last 5 lines
                        "request_id": getattr(request.state, "request_id", None),
                    }
                },
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred. Please try again later.",
                        "request_id": getattr(request.state, "request_id", None),
                    }
                },
            )
