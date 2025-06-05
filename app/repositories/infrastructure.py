"""
Infrastructure domain repositories.
Handles database operations for infrastructure entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from app.models.infrastructure import Campus, Classroom, DepartmentClassroom
from app.repositories.base import BaseRepository
from app.schemas.infrastructure import (
    CampusCreate, CampusUpdate,
    ClassroomCreate, ClassroomUpdate,
    DepartmentClassroomCreate, DepartmentClassroomUpdate
)
from app.core.pagination import PaginationParams, Page, paginate


class CampusRepository(BaseRepository[Campus, CampusCreate, CampusUpdate]):
    """Repository for campus locations."""
    
    def __init__(self, db: Session):
        super().__init__(Campus, db)
    
    def get_by_address(self, address: str) -> Optional[Campus]:
        """Get campus by address."""
        return self.db.query(Campus).filter(
            Campus.address == address
        ).first()
    
    def get_classrooms_count(self, campus_id: int) -> int:
        """Get count of classrooms in this campus."""
        return self.db.query(Classroom).filter(
            Classroom.campus_id == campus_id
        ).count()
    
    def search_campuses(
        self,
        params: PaginationParams,
        search: Optional[str] = None
    ) -> Page[Campus]:
        """Search campuses with filters."""
        query = self.db.query(Campus)
        
        if search:
            search_filter = or_(
                Campus.address.ilike(f"%{search}%"),
                Campus.email.ilike(f"%{search}%"),
                Campus.phone_number.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return paginate(query, params)


class ClassroomRepository(BaseRepository[Classroom, ClassroomCreate, ClassroomUpdate]):
    """Repository for classrooms."""
    
    def __init__(self, db: Session):
        super().__init__(Classroom, db)
    
    def get_by_room_and_campus(self, room_number: str, campus_id: int) -> Optional[Classroom]:
        """Get classroom by room number and campus."""
        return self.db.query(Classroom).filter(
            and_(
                Classroom.room_number == room_number,
                Classroom.campus_id == campus_id
            )
        ).first()
    
    def get_with_relations(self, classroom_id: int) -> Optional[Classroom]:
        """Get classroom with all relations loaded."""
        return self.db.query(Classroom).options(
            joinedload(Classroom.campus),
            joinedload(Classroom.departments)
        ).filter(Classroom.classroom_id == classroom_id).first()
    
    def search_classrooms(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        campus_id: Optional[int] = None,
        classroom_type: Optional[str] = None,
        min_capacity: Optional[int] = None,
        max_capacity: Optional[int] = None
    ) -> Page[Classroom]:
        """Search classrooms with filters."""
        query = self.db.query(Classroom).options(
            joinedload(Classroom.campus)
        )
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Classroom.room_number.ilike(f"%{search}%"),
                    Classroom.classroom_type.ilike(f"%{search}%")
                )
            )
        
        if campus_id:
            query = query.filter(Classroom.campus_id == campus_id)
        
        if classroom_type:
            query = query.filter(Classroom.classroom_type == classroom_type)
        
        if min_capacity:
            query = query.filter(Classroom.capacity >= min_capacity)
        
        if max_capacity:
            query = query.filter(Classroom.capacity <= max_capacity)
        
        return paginate(query, params)
    
    def get_schedules_count(self, classroom_id: int) -> int:
        """Get count of class schedules for this classroom."""
        from app.models.scheduling import ClassSchedule
        return self.db.query(ClassSchedule).filter(
            ClassSchedule.classroom_id == classroom_id
        ).count()
    
    def get_available_classrooms(
        self,
        day_time_block_id: int,
        quarter_id: int,
        min_capacity: Optional[int] = None
    ) -> List[Classroom]:
        """Get classrooms available for a specific time slot."""
        from app.models.scheduling import ClassSchedule
        
        # Subquery to get occupied classrooms
        occupied = self.db.query(ClassSchedule.classroom_id).filter(
            and_(
                ClassSchedule.day_time_block_id == day_time_block_id,
                ClassSchedule.quarter_id == quarter_id
            )
        ).subquery()
        
        query = self.db.query(Classroom).filter(
            ~Classroom.classroom_id.in_(occupied)
        )
        
        if min_capacity:
            query = query.filter(Classroom.capacity >= min_capacity)
        
        return query.all()


class DepartmentClassroomRepository(
    BaseRepository[DepartmentClassroom, DepartmentClassroomCreate, DepartmentClassroomUpdate]
):
    """Repository for department-classroom relationships."""
    
    def __init__(self, db: Session):
        super().__init__(DepartmentClassroom, db)
    
    def get_by_ids(self, department_id: int, classroom_id: int) -> Optional[DepartmentClassroom]:
        """Get relationship by department and classroom IDs."""
        return self.db.query(DepartmentClassroom).filter(
            and_(
                DepartmentClassroom.department_id == department_id,
                DepartmentClassroom.classroom_id == classroom_id
            )
        ).first()
    
    def get_department_classrooms(self, department_id: int) -> List[DepartmentClassroom]:
        """Get all classrooms for a department."""
        return self.db.query(DepartmentClassroom).options(
            joinedload(DepartmentClassroom.classroom).joinedload(Classroom.campus)
        ).filter(
            DepartmentClassroom.department_id == department_id
        ).order_by(DepartmentClassroom.priority.desc()).all()
    
    def get_classroom_departments(self, classroom_id: int) -> List[DepartmentClassroom]:
        """Get all departments for a classroom."""
        return self.db.query(DepartmentClassroom).options(
            joinedload(DepartmentClassroom.department)
        ).filter(
            DepartmentClassroom.classroom_id == classroom_id
        ).order_by(DepartmentClassroom.priority.desc()).all()
    
    def update_priority(
        self,
        department_id: int,
        classroom_id: int,
        priority: int
    ) -> Optional[DepartmentClassroom]:
        """Update priority for department-classroom relationship."""
        rel = self.get_by_ids(department_id, classroom_id)
        if rel:
            rel.priority = priority
            self.db.commit()
            self.db.refresh(rel)
        return rel