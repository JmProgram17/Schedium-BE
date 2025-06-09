"""
Common dependencies used across the application.
Provides reusable dependencies for dependency injection.
"""

from datetime import datetime
from typing import Annotated, Generator, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import SecurityUtils
from app.database import SessionLocal
from app.models.auth import User
from app.repositories.auth import UserRepository

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", scheme_name="JWT"
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Ensures proper cleanup after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Solo la función corregida:


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        Current user object

    Raises:
        UnauthorizedException: If token is invalid or user not found
    """
    credentials_exception = UnauthorizedException(
        detail="Could not validate credentials", error_code="INVALID_CREDENTIALS"
    )

    try:
        # Decode JWT token
        payload = SecurityUtils.decode_token(token)

        # Verify token type
        if not SecurityUtils.verify_token_type(payload, "access"):
            raise credentials_exception

        # Get user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Check token expiration (already checked in decode, but double-check)
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise UnauthorizedException(
                detail="Token has expired", error_code="TOKEN_EXPIRED"
            )

    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception

    # Get user from database
    user_repo = UserRepository(db)
    user = user_repo.get(int(user_id))

    if user is None:
        raise credentials_exception

    # Ensure role is loaded
    if user.role:
        _ = user.role.name  # Force load the relationship

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Active user object

    Raises:
        UnauthorizedException: If user is inactive
    """
    if not current_user.active:
        raise UnauthorizedException(detail="Inactive user", error_code="INACTIVE_USER")
    return current_user


def require_role(allowed_roles: list[str]):
    """
    Dependency to check if user has required role.

    Args:
        allowed_roles: List of allowed role names

    Returns:
        Dependency function that validates user role
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if not current_user.role:
            raise ForbiddenException(
                detail="User has no role assigned", error_code="NO_ROLE"
            )

        if current_user.role.name not in allowed_roles:
            raise ForbiddenException(
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
                error_code="INSUFFICIENT_PERMISSIONS",
            )
        return current_user

    return role_checker


# Pre-defined role dependencies
require_admin = require_role(["Administrator"])
require_coordinator = require_role(["Administrator", "Coordinator"])
require_any_role = require_role(["Administrator", "Coordinator", "Secretary"])


async def get_current_user_optional(
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except (UnauthorizedException, JWTError):
        return None


async def get_request_id(
    x_request_id: Annotated[Optional[str], Header(alias="X-Request-ID")] = None
) -> Optional[str]:
    """
    Get request ID from header.

    Args:
        x_request_id: Request ID from header

    Returns:
        Request ID or None
    """
    return x_request_id


class CommonQueryParams:
    """Common query parameters for list endpoints."""

    def __init__(
        self,
        skip: int = 0,
        limit: int = settings.DEFAULT_PAGE_SIZE,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ):
        self.skip = skip
        self.limit = min(limit, settings.MAX_PAGE_SIZE)
        self.search = search
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order in ["asc", "desc"] else "asc"


def verify_token_dependency(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    Verify token and return payload.

    Args:
        token: JWT token

    Returns:
        Token payload

    Raises:
        UnauthorizedException: If token is invalid
    """
    try:
        payload = SecurityUtils.decode_token(token)
        if not SecurityUtils.verify_token_type(payload, "access"):
            raise UnauthorizedException(
                detail="Invalid token type", error_code="INVALID_TOKEN_TYPE"
            )
        return payload
    except JWTError:
        raise UnauthorizedException(
            detail="Could not validate token", error_code="INVALID_TOKEN"
        )
