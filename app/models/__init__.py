"""
Base model configuration and common mixins.
Provides reusable components for all models.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy.ext.declarative import declared_attr

from app.database import Base


class TimeStampMixin:
    """Mixin for created_at and updated_at timestamps."""

    @declared_attr
    def created_at(cls) -> Column[DateTime]:
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
            comment="Record creation timestamp",
        )

    @declared_attr
    def updated_at(cls) -> Column[DateTime]:
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
            comment="Record last update timestamp",
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    @declared_attr
    def is_deleted(cls) -> Column[Boolean]:
        return Column(
            Boolean, default=False, nullable=False, comment="Soft delete flag"
        )

    @declared_attr
    def deleted_at(cls) -> Column[DateTime]:
        return Column(DateTime, nullable=True, comment="Deletion timestamp")


# Re-export Base for convenience
__all__ = ["Base", "TimeStampMixin", "SoftDeleteMixin"]
