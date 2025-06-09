"""
Base repository providing common CRUD operations.
Implements the Repository pattern for data access.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, inspect, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.core.pagination import Page, PaginationParams, paginate
from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository with CRUD operations.

    Type Parameters:
        ModelType: SQLAlchemy model type
        CreateSchemaType: Pydantic schema for creation
        UpdateSchemaType: Pydantic schema for updates
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.

        Args:
            id: Record ID

        Returns:
            Model instance or None
        """
        # Get primary key dynamically
        mapper = inspect(self.model)
        pk_column = mapper.primary_key[0]
        return self.db.query(self.model).filter(pk_column == id).first()

    def get_or_404(self, id: Any) -> ModelType:
        """
        Get a single record by ID or raise 404.

        Args:
            id: Record ID

        Returns:
            Model instance

        Raises:
            NotFoundException: If record not found
        """
        obj = self.get(id)
        if not obj:
            raise NotFoundException(
                detail=f"{self.model.__name__} with id {id} not found"
            )
        return obj

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Get a single record by field value.

        Args:
            field: Field name
            value: Field value

        Returns:
            Model instance or None
        """
        return (
            self.db.query(self.model)
            .filter(getattr(self.model, field) == value)
            .first()
        )

    def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[ModelType]:
        """
        Get multiple records with optional filtering and sorting.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field-value pairs to filter by
            order_by: Field name to order by
            order_desc: Whether to order descending

        Returns:
            List of model instances
        """
        query = self.db.query(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field)

        return query.offset(skip).limit(limit).all()

    def get_paginated(
        self,
        params: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        search_fields: Optional[List[str]] = None,
        search_term: Optional[str] = None,
    ) -> Page[ModelType]:
        """
        Get paginated records.

        Args:
            params: Pagination parameters
            filters: Dictionary of field-value pairs to filter by
            search_fields: Fields to search in
            search_term: Term to search for

        Returns:
            Paginated results
        """
        query = self.db.query(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.filter(getattr(self.model, field) == value)

        # Apply search
        if search_term and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(
                        func.lower(getattr(self.model, field)).contains(
                            search_term.lower()
                        )
                    )
            if search_conditions:
                query = query.filter(or_(*search_conditions))

        return paginate(query, params)

    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            obj_in: Pydantic schema with creation data

        Returns:
            Created model instance
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record.

        Args:
            db_obj: Existing model instance
            obj_in: Pydantic schema or dict with update data

        Returns:
            Updated model instance
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, *, id: Any) -> ModelType:
        """
        Delete a record.

        Args:
            id: Record ID

        Returns:
            Deleted model instance

        Raises:
            NotFoundException: If record not found
        """
        obj = self.get(id)
        if not obj:
            raise NotFoundException(
                detail=f"{self.model.__name__} with id {id} not found"
            )
        self.db.delete(obj)
        self.db.commit()
        return obj

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.

        Args:
            filters: Dictionary of field-value pairs to filter by

        Returns:
            Number of records
        """
        query = self.db.query(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.count()

    def exists(self, **kwargs) -> bool:
        """
        Check if a record exists with given field values.

        Args:
            **kwargs: Field-value pairs to check

        Returns:
            True if exists, False otherwise
        """
        query = self.db.query(self.model)
        for field, value in kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        return query.first() is not None

    def bulk_create(self, *, obj_in_list: List[CreateSchemaType]) -> List[ModelType]:
        """
        Create multiple records in bulk.

        Args:
            obj_in_list: List of Pydantic schemas with creation data

        Returns:
            List of created model instances
        """
        db_objs = []
        for obj_in in obj_in_list:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)

        self.db.bulk_save_objects(db_objs)
        self.db.commit()
        return db_objs
