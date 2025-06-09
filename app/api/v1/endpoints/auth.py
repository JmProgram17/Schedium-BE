"""
Authentication endpoints.
Handles login, logout, token refresh, and user management.
"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_current_user,
    get_db,
    get_pagination_params,
    require_admin,
)
from app.config import settings
from app.core.exceptions import (  # Add this import if NotFoundException is defined here
    NotFoundException,
)
from app.core.pagination import Page, PaginationParams
from app.core.responses import (
    CreatedResponse,
    DeletedResponse,
    SuccessResponse,
    UpdatedResponse,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    Role,
    RoleCreate,
    RoleUpdate,
    Token,
    User,
    UserCreate,
    UserUpdate,
    UserWithoutPassword,
)
from app.services.auth import AuthService

router = APIRouter()


# Authentication endpoints
@router.post("/login", response_model=SuccessResponse[Token])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """
    OAuth2 compatible token login.

    Use username field for email.
    Returns access and refresh tokens.
    """
    service = AuthService(db)

    # Authenticate user
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    tokens = service.create_tokens(user.user_id)

    return SuccessResponse(data=tokens, message="Login successful")


@router.post("/refresh", response_model=SuccessResponse[Token])
async def refresh_token(
    refresh_token: Annotated[str, Body(..., embed=True, description="Refresh token")],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Refresh access token using refresh token.

    Returns new access and refresh tokens.
    """
    service = AuthService(db)
    tokens = service.refresh_access_token(refresh_token)

    return SuccessResponse(data=tokens, message="Token refreshed successfully")


@router.post("/logout", response_model=SuccessResponse[dict])
async def logout(current_user: Annotated[User, Depends(get_current_active_user)]):
    """
    Logout current user.

    Note: Since we use stateless JWT, this endpoint is mainly
    for client-side token removal. In production, you might want
    to implement token blacklisting.
    """
    return SuccessResponse(
        data={
            "user_id": current_user.user_id,
            "message": "Please remove tokens from client storage",
        },
        message="Logout successful",
    )


@router.get("/me", response_model=SuccessResponse[UserWithoutPassword])
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Get current user information.
    """
    return SuccessResponse(
        data=UserWithoutPassword.model_validate(current_user),
        message="User information retrieved",
    )


@router.put("/me", response_model=UpdatedResponse[UserWithoutPassword])
async def update_current_user(
    user_update: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Update current user's own information.

    Cannot change role or active status.
    """
    # Remove fields that user cannot change themselves
    update_data = user_update.model_dump(exclude_unset=True)
    update_data.pop("role_id", None)
    update_data.pop("active", None)
    update_data.pop("password", None)  # Use change-password endpoint

    service = AuthService(db)
    user = service.update_user(current_user.user_id, UserUpdate(**update_data))

    return UpdatedResponse(data=user, message="Profile updated successfully")


@router.post("/change-password", response_model=SuccessResponse[dict])
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Change current user's password.
    """
    service = AuthService(db)

    success = service.change_password(
        current_user.user_id, password_data.current_password, password_data.new_password
    )

    return SuccessResponse(
        data={"success": success}, message="Password changed successfully"
    )


@router.post("/forgot-password", response_model=SuccessResponse[dict])
async def forgot_password(
    email: Annotated[str, Body(..., embed=True, description="User email")],
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Request password reset.

    Sends reset token to user's email (in production).
    For development, the token is returned in the response.
    """
    service = AuthService(db)

    try:
        reset_token = service.reset_password(email)

        # In production, send email with reset token
        # background_tasks.add_task(send_reset_email, email, reset_token)

        # For development, return token
        response_data = {"message": "Password reset instructions sent to email"}
        if settings.DEBUG:
            response_data["reset_token"] = reset_token

        return SuccessResponse(data=response_data, message="Password reset requested")
    except NotFoundException:
        # Don't reveal if email exists or not
        return SuccessResponse(
            data={"message": "If the email exists, reset instructions have been sent"},
            message="Password reset requested",
        )


@router.post("/reset-password", response_model=SuccessResponse[dict])
async def reset_password(
    token: Annotated[str, Body(..., description="Reset token")],
    new_password: Annotated[str, Body(..., min_length=8, description="New password")],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Reset password using reset token.
    """
    service = AuthService(db)
    success = service.confirm_reset_password(token, new_password)

    return SuccessResponse(
        data={"success": success}, message="Password reset successfully"
    )


# User management endpoints (Admin only)
@router.get("/users", response_model=SuccessResponse[Page[UserWithoutPassword]])
async def get_users(
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    params: Annotated[PaginationParams, Depends(get_pagination_params)],
    search: Optional[str] = None,
    role_id: Optional[int] = None,
    active: Optional[bool] = None,
):
    """
    Get paginated list of users.

    Admin only.
    """
    service = AuthService(db)
    users = service.get_users(params, search, role_id, active)

    return SuccessResponse(data=users, message="Users retrieved successfully")


@router.post("/users", response_model=CreatedResponse[UserWithoutPassword])
async def create_user(
    user_in: UserCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new user.

    Admin only.
    """
    service = AuthService(db)
    user = service.create_user(user_in)

    return CreatedResponse(data=user, message="User created successfully")


@router.get("/users/{user_id}", response_model=SuccessResponse[UserWithoutPassword])
async def get_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Get user by ID.

    Admin only.
    """
    service = AuthService(db)
    user = service.get_user(user_id)

    return SuccessResponse(data=user, message="User retrieved successfully")


@router.put("/users/{user_id}", response_model=UpdatedResponse[UserWithoutPassword])
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Update user.

    Admin only.
    """
    service = AuthService(db)
    user = service.update_user(user_id, user_in)

    return UpdatedResponse(data=user, message="User updated successfully")


@router.delete("/users/{user_id}", response_model=DeletedResponse)
async def delete_user(
    user_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Delete user.

    Admin only. Cannot delete the last administrator.
    """
    service = AuthService(db)
    service.delete_user(user_id)

    return DeletedResponse(message="User deleted successfully")


# Role management endpoints
@router.get("/roles", response_model=SuccessResponse[List[Role]])
async def get_roles(db: Annotated[Session, Depends(get_db)]):
    """
    Get all roles.

    Public endpoint - roles are not sensitive.
    """
    service = AuthService(db)
    roles = service.get_roles()

    return SuccessResponse(data=roles, message="Roles retrieved successfully")


@router.post("/roles", response_model=CreatedResponse[Role])
async def create_role(
    role_in: RoleCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new role.

    Admin only.
    """
    service = AuthService(db)
    role = service.create_role(role_in)

    return CreatedResponse(data=role, message="Role created successfully")


@router.put("/roles/{role_id}", response_model=UpdatedResponse[Role])
async def update_role(
    role_id: int,
    role_in: RoleUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Update role.

    Admin only. Cannot rename system roles.
    """
    service = AuthService(db)
    role = service.update_role(role_id, role_in)

    return UpdatedResponse(data=role, message="Role updated successfully")


@router.delete("/roles/{role_id}", response_model=DeletedResponse)
async def delete_role(
    role_id: int,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Delete role.

    Admin only. Cannot delete system roles or roles in use.
    """
    service = AuthService(db)
    service.delete_role(role_id)

    return DeletedResponse(message="Role deleted successfully")
