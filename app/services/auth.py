"""
Authentication service.
Handles business logic for authentication and authorization.
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth import User, Role
from app.schemas.auth import (
    UserCreate, UserUpdate, User as UserSchema,
    RoleCreate, RoleUpdate, Role as RoleSchema,
    Token
)
from app.repositories.auth import UserRepository, RoleRepository
from app.core.exceptions import (
    NotFoundException, BadRequestException,
    UnauthorizedException, ConflictException
)
from app.core.security import SecurityUtils
from app.core.pagination import PaginationParams, Page


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
    
    # Authentication methods
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        
        if not SecurityUtils.verify_password(password, user.password):
            return None
        
        if not user.active:
            raise UnauthorizedException(
                detail="User account is inactive",
                error_code="INACTIVE_USER"
            )
        
        # Update last login
        self.user_repo.update_last_login(user.user_id)
        
        return user
    
    def create_tokens(self, user_id: int) -> Token:
        """
        Create access and refresh tokens for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Token object with access and refresh tokens
        """
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Token payload
        token_data = {
            "sub": str(user.user_id),
            "email": user.email,
            "role": user.role.name if user.role else None,
            "full_name": user.full_name
        }
        
        # Create tokens
        access_token = SecurityUtils.create_access_token(data=token_data)
        refresh_token = SecurityUtils.create_refresh_token(data={"sub": str(user.user_id)})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token pair
            
        Raises:
            UnauthorizedException: If refresh token is invalid
        """
        try:
            # Decode refresh token
            payload = SecurityUtils.decode_token(refresh_token)
            
            # Verify it's a refresh token
            if not SecurityUtils.verify_token_type(payload, "refresh"):
                raise UnauthorizedException(
                    detail="Invalid token type",
                    error_code="INVALID_TOKEN_TYPE"
                )
            
            # Get user ID
            user_id = int(payload.get("sub"))
            
            # Create new tokens
            return self.create_tokens(user_id)
            
        except Exception as e:
            raise UnauthorizedException(
                detail="Invalid refresh token",
                error_code="INVALID_REFRESH_TOKEN"
            )
    
    # User operations
    def create_user(self, user_in: UserCreate) -> UserSchema:
        """Create a new user."""
        # Check if email is taken
        if self.user_repo.is_email_taken(user_in.email):
            raise ConflictException(
                detail=f"Email {user_in.email} is already registered",
                error_code="EMAIL_TAKEN"
            )
        
        # Check if document is taken
        if self.user_repo.is_document_taken(user_in.document_number):
            raise ConflictException(
                detail=f"Document number {user_in.document_number} is already registered",
                error_code="DOCUMENT_TAKEN"
            )
        
        # Check if role exists
        if user_in.role_id:
            role = self.role_repo.get(user_in.role_id)
            if not role:
                raise NotFoundException(f"Role with id {user_in.role_id} not found")
        
        # Hash password
        user_data = user_in.model_dump()
        user_data["password"] = SecurityUtils.get_password_hash(user_data["password"])
        
        # Create user
        user = self.user_repo.create(obj_in=UserCreate(**user_data))
        return UserSchema.model_validate(user)
    
    def get_user(self, user_id: int) -> UserSchema:
        """Get user by ID."""
        user = self.user_repo.get_or_404(user_id)
        return UserSchema.model_validate(user)
    
    def get_users(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        active: Optional[bool] = None
    ) -> Page[UserSchema]:
        """Get paginated list of users."""
        page = self.user_repo.search_users(params, search, role_id, active)
        
        # Convert to schemas
        page.items = [UserSchema.model_validate(user) for user in page.items]
        return page
    
    # Solo el método corregido:

    def update_user(self, user_id: int, user_in: UserUpdate) -> UserSchema:
        """Update user."""
        user = self.user_repo.get_or_404(user_id)
        
        # Check email uniqueness if changed
        if user_in.email and user_in.email != user.email:
            if self.user_repo.is_email_taken(user_in.email, user_id):
                raise ConflictException(
                    detail=f"Email {user_in.email} is already taken",
                    error_code="EMAIL_TAKEN"
                )
        
        # Check document uniqueness if changed
        if user_in.document_number and user_in.document_number != user.document_number:
            if self.user_repo.is_document_taken(user_in.document_number, user_id):
                raise ConflictException(
                    detail=f"Document {user_in.document_number} is already taken",
                    error_code="DOCUMENT_TAKEN"
                )
        
        # Hash password if provided
        update_data = user_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = SecurityUtils.get_password_hash(update_data["password"])
        
        # Update user
        user = self.user_repo.update(db_obj=user, obj_in=update_data)
        return UserSchema.model_validate(user)
    
    def delete_user(self, user_id: int) -> None:
        """Delete user."""
        user = self.user_repo.get_or_404(user_id)
        
        # Don't delete users with admin role if they're the last admin
        if user.role and user.role.name == "Administrator":
            admin_count = self.db.query(User).join(Role).filter(
                Role.name == "Administrator",
                User.active == True,
                User.user_id != user_id
            ).count()
            
            if admin_count == 0:
                raise BadRequestException(
                    detail="Cannot delete the last administrator",
                    error_code="LAST_ADMIN"
                )
        
        self.user_repo.delete(id=user_id)
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        user = self.user_repo.get_or_404(user_id)
        
        # Verify current password
        if not SecurityUtils.verify_password(current_password, user.password):
            raise BadRequestException(
                detail="Current password is incorrect",
                error_code="INVALID_PASSWORD"
            )
        
        # Update password
        user.password = SecurityUtils.get_password_hash(new_password)
        self.db.commit()
        
        return True
    
    def reset_password(self, email: str) -> str:
        """
        Generate password reset token.
        
        Args:
            email: User email
            
        Returns:
            Reset token
            
        Raises:
            NotFoundException: If user not found
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundException(
                detail="User with this email not found",
                error_code="USER_NOT_FOUND"
            )
        
        return SecurityUtils.generate_password_reset_token(email)
    
    def confirm_reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token.
        
        Args:
            token: Reset token
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            BadRequestException: If token is invalid
        """
        email = SecurityUtils.verify_password_reset_token(token)
        if not email:
            raise BadRequestException(
                detail="Invalid or expired reset token",
                error_code="INVALID_RESET_TOKEN"
            )
        
        user = self.user_repo.get_by_email(email)
        if not user:
            raise NotFoundException(
                detail="User not found",
                error_code="USER_NOT_FOUND"
            )
        
        # Update password
        user.password = SecurityUtils.get_password_hash(new_password)
        self.db.commit()
        
        return True
    
    # Role operations
    def create_role(self, role_in: RoleCreate) -> RoleSchema:
        """Create a new role."""
        if self.role_repo.is_name_taken(role_in.name):
            raise ConflictException(
                detail=f"Role {role_in.name} already exists",
                error_code="ROLE_EXISTS"
            )
        
        role = self.role_repo.create(obj_in=role_in)
        return RoleSchema.model_validate(role)
    
    def get_roles(self) -> list[RoleSchema]:
        """Get all roles."""
        roles = self.role_repo.get_multi(limit=100)
        return [RoleSchema.model_validate(role) for role in roles]
    
    def update_role(self, role_id: int, role_in: RoleUpdate) -> RoleSchema:
        """Update role."""
        role = self.role_repo.get_or_404(role_id)
        
        # Check name uniqueness if changed
        if role_in.name and role_in.name != role.name:
            if self.role_repo.is_name_taken(role_in.name, role_id):
                raise ConflictException(
                    detail=f"Role {role_in.name} already exists",
                    error_code="ROLE_EXISTS"
                )
        
        # Don't allow renaming system roles
        system_roles = ["Administrator", "Coordinator", "Secretary"]
        if role.name in system_roles and role_in.name and role_in.name != role.name:
            raise BadRequestException(
                detail="Cannot rename system roles",
                error_code="SYSTEM_ROLE_RENAME"
            )
        
        role = self.role_repo.update(db_obj=role, obj_in=role_in)
        return RoleSchema.model_validate(role)
    
    def delete_role(self, role_id: int) -> None:
        """Delete role."""
        role = self.role_repo.get_or_404(role_id)
        
        # Check if role is in use
        users_count = self.role_repo.get_users_count(role_id)
        if users_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete role. {users_count} users have this role",
                error_code="ROLE_IN_USE"
            )
        
        # Don't delete system roles
        system_roles = ["Administrator", "Coordinator", "Secretary"]
        if role.name in system_roles:
            raise BadRequestException(
                detail="Cannot delete system roles",
                error_code="SYSTEM_ROLE"
            )
        
        self.role_repo.delete(id=role_id)