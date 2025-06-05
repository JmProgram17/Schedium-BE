"""
Authentication repository.
Handles database operations for users and roles.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.auth import User, Role
from app.repositories.base import BaseRepository
from app.schemas.auth import UserCreate, UserUpdate, RoleCreate, RoleUpdate
from app.core.pagination import PaginationParams, Page, paginate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """User repository for database operations."""
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_document(self, document_number: str) -> Optional[User]:
        """Get user by document number."""
        return self.db.query(User).filter(User.document_number == document_number).first()
    
    def search_users(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        active: Optional[bool] = None
    ) -> Page[User]:
        """Search users with filters."""
        query = self.db.query(User)
        
        # Apply filters
        if search:
            search_filter = or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.document_number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if role_id is not None:
            query = query.filter(User.role_id == role_id)
        
        if active is not None:
            query = query.filter(User.active == active)
        
        return paginate(query, params)
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        from datetime import datetime
        
        user = self.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def is_email_taken(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Check if email is already taken."""
        query = self.db.query(User).filter(User.email == email)
        if exclude_id:
            query = query.filter(User.user_id != exclude_id)
        return query.first() is not None
    
    def is_document_taken(self, document: str, exclude_id: Optional[int] = None) -> bool:
        """Check if document number is already taken."""
        query = self.db.query(User).filter(User.document_number == document)
        if exclude_id:
            query = query.filter(User.user_id != exclude_id)
        return query.first() is not None


class RoleRepository(BaseRepository[Role, RoleCreate, RoleUpdate]):
    """Role repository for database operations."""
    
    def __init__(self, db: Session):
        super().__init__(Role, db)
    
    def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def get_users_count(self, role_id: int) -> int:
        """Get count of users with this role."""
        return self.db.query(User).filter(User.role_id == role_id).count()
    
    def is_name_taken(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if role name is already taken."""
        query = self.db.query(Role).filter(Role.name == name)
        if exclude_id:
            query = query.filter(Role.role_id != exclude_id)
        return query.first() is not None