"""
Authentication and authorization models.
Maps user and role tables.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models import Base, TimeStampMixin


class Role(Base, TimeStampMixin):
    """Role model for user permissions."""

    __tablename__ = "role"
    __table_args__ = {"comment": "User roles for system access control"}

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, index=True)

    # Relationships
    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(id={self.role_id}, name={self.name})>"


class User(Base, TimeStampMixin):
    """User model for system access."""

    __tablename__ = "user"
    __table_args__ = {"comment": "System users with access credentials"}

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    document_number = Column(String(20), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True, index=True)
    role_id = Column(Integer, ForeignKey("role.role_id", ondelete="RESTRICT"))
    active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users")

    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User(id={self.user_id}, email={self.email})>"
