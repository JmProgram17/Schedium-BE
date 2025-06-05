"""
Common dependencies used across the application.
Provides reusable dependencies for dependency injection.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime

from app.database import SessionLocal
from app.config import settings
from app.core.exceptions import UnauthorizedException
from app.models.auth import User
from app.repositories.auth import UserRepository


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scheme_name="JWT"
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


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
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
        detail="Could not validate credentials",
        error_code="INVALID_CREDENTIALS"
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            raise UnauthorizedException(
                detail="Token has expired",
                error_code="TOKEN_EXPIRED"
            )
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)
    
    if user is None:
        raise credentials_exception
        
    if not user.active:
        raise UnauthorizedException(
            detail="User account is inactive",
            error_code="INACTIVE_USER"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
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
        raise UnauthorizedException(
            detail="Inactive user",
            error_code="INACTIVE_USER"
        )
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
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not current_user.role:
            raise UnauthorizedException(
                detail="User has no role assigned",
                error_code="NO_ROLE"
            )
            
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.name}' not allowed. Required roles: {', '.join(allowed_roles)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return current_user
    
    return role_checker


# Pre-defined role dependencies
require_admin = require_role(["Administrator"])
require_coordinator = require_role(["Administrator", "Coordinator"])
require_any_role = require_role(["Administrator", "Coordinator", "Secretary"])


async def get_request_id(
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID")
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
        sort_order: str = "asc"
    ):
        self.skip = skip
        self.limit = min(limit, settings.MAX_PAGE_SIZE)
        self.search = search
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order in ["asc", "desc"] else "asc"