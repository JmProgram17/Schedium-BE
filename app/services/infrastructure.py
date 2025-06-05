"""
Infrastructure domain services.
Handles business logic for infrastructure entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.infrastructure import Campus, Classroom, DepartmentClassroom
from app.schemas.infrastructure import (
    CampusCreate, CampusUpdate, Campus as CampusSchema,
    ClassroomCreate, ClassroomUpdate, Classroom as ClassroomSchema,
    DepartmentClassroomCreate, DepartmentClassroomUpdate,
    DepartmentClassroom as DepartmentClassroomSchema,
    ClassroomAvailability
)
from app.repositories.infrastructure import (
    CampusRepository, ClassroomRepository, DepartmentClassroomRepository
)
from app.repositories.hr import DepartmentRepository
from app.core.exceptions import (
    NotFoundException, ConflictException, BadRequestException
)
from app.core.pagination import PaginationParams, Page


class InfrastructureService:
    """Service for infrastructure operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.campus_repo = CampusRepository(db)
        self.classroom_repo = ClassroomRepository(db)
        self.dept_classroom_repo = DepartmentClassroomRepository(db)
        self.department_repo = DepartmentRepository(db)
    
    # Campus operations
    def create_campus(self, campus_in: CampusCreate) -> CampusSchema:
        """Create a new campus."""
        # Check if address already exists
        existing = self.campus_repo.get_by_address(campus_in.address)
        if existing:
            raise ConflictException(
                detail=f"Campus at '{campus_in.address}' already exists",
                error_code="CAMPUS_EXISTS"
            )
        
        campus = self.campus_repo.create(obj_in=campus_in)
        return CampusSchema.model_validate(campus)
    
    def get_campus(self, campus_id: int) -> CampusSchema:
        """Get campus by ID."""
        campus = self.campus_repo.get_or_404(campus_id)
        return CampusSchema.model_validate(campus)
    
    def get_campuses(
        self,
        params: PaginationParams,
        search: Optional[str] = None
    ) -> Page[CampusSchema]:
        """Get paginated list of campuses."""
        page = self.campus_repo.search_campuses(params, search)
        page.items = [CampusSchema.model_validate(item) for item in page.items]
        return page
    
    def update_campus(self, campus_id: int, campus_in: CampusUpdate) -> CampusSchema:
        """Update campus."""
        campus = self.campus_repo.get_or_404(campus_id)
        
        # Check uniqueness if address changed
        if campus_in.address and campus_in.address != campus.address:
            existing = self.campus_repo.get_by_address(campus_in.address)
            if existing:
                raise ConflictException(
                    detail=f"Campus at '{campus_in.address}' already exists",
                    error_code="CAMPUS_EXISTS"
                )
        
        campus = self.campus_repo.update(db_obj=campus, obj_in=campus_in)
        return CampusSchema.model_validate(campus)
    
    def delete_campus(self, campus_id: int) -> None:
        """Delete campus."""
        campus = self.campus_repo.get_or_404(campus_id)
        
        # Check if campus has classrooms
        classrooms_count = self.campus_repo.get_classrooms_count(campus_id)
        if classrooms_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete campus. {classrooms_count} classrooms exist",
                error_code="CAMPUS_HAS_CLASSROOMS"
            )
        
        self.campus_repo.delete(id=campus_id)
    
    # Classroom operations
    def create_classroom(self, classroom_in: ClassroomCreate) -> ClassroomSchema:
        """Create a new classroom."""
        # Validate campus exists
        self.campus_repo.get_or_404(classroom_in.campus_id)
        
        # Check if room number already exists in campus
        existing = self.classroom_repo.get_by_room_and_campus(
            classroom_in.room_number,
            classroom_in.campus_id
        )
        if existing:
            raise ConflictException(
                detail=f"Room {classroom_in.room_number} already exists in this campus",
                error_code="ROOM_EXISTS"
            )
        
        classroom = self.classroom_repo.create(obj_in=classroom_in)
        classroom = self.classroom_repo.get_with_relations(classroom.classroom_id)
        return ClassroomSchema.model_validate(classroom)
    
    def get_classroom(self, classroom_id: int) -> ClassroomSchema:
        """Get classroom by ID."""
        classroom = self.classroom_repo.get_with_relations(classroom_id)
        if not classroom:
            raise NotFoundException(f"Classroom with id {classroom_id} not found")
        return ClassroomSchema.model_validate(classroom)
    
    def get_classrooms(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        campus_id: Optional[int] = None,
        classroom_type: Optional[str] = None,
        min_capacity: Optional[int] = None,
        max_capacity: Optional[int] = None
    ) -> Page[ClassroomSchema]:
        """Get paginated list of classrooms."""
        page = self.classroom_repo.search_classrooms(
            params, search, campus_id, classroom_type, min_capacity, max_capacity
        )
        page.items = [ClassroomSchema.model_validate(item) for item in page.items]
        return page
    
    def update_classroom(
        self,
        classroom_id: int,
        classroom_in: ClassroomUpdate
    ) -> ClassroomSchema:
        """Update classroom."""
        classroom = self.classroom_repo.get_or_404(classroom_id)
        
        # Validate campus if changed
        if classroom_in.campus_id and classroom_in.campus_id != classroom.campus_id:
            self.campus_repo.get_or_404(classroom_in.campus_id)
        
        # Check room uniqueness if changed
        if (classroom_in.room_number and 
            (classroom_in.room_number != classroom.room_number or
             classroom_in.campus_id != classroom.campus_id)):
            
            campus_id = classroom_in.campus_id or classroom.campus_id
            existing = self.classroom_repo.get_by_room_and_campus(
                classroom_in.room_number,
                campus_id
            )
            if existing and existing.classroom_id != classroom_id:
                raise ConflictException(
                    detail=f"Room {classroom_in.room_number} already exists in campus",
                    error_code="ROOM_EXISTS"
                )
        
        classroom = self.classroom_repo.update(db_obj=classroom, obj_in=classroom_in)
        classroom = self.classroom_repo.get_with_relations(classroom_id)
        return ClassroomSchema.model_validate(classroom)
    
    def delete_classroom(self, classroom_id: int) -> None:
        """Delete classroom."""
        classroom = self.classroom_repo.get_or_404(classroom_id)
        
        # Check if classroom has schedules
        schedules_count = self.classroom_repo.get_schedules_count(classroom_id)
        if schedules_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete classroom. {schedules_count} schedules exist",
                error_code="CLASSROOM_HAS_SCHEDULES"
            )
        
        self.classroom_repo.delete(id=classroom_id)
    
    def get_classroom_availability(
        self,
        day_time_block_id: int,
        quarter_id: int,
        min_capacity: Optional[int] = None
    ) -> List[ClassroomAvailability]:
        """Get available classrooms for a time slot."""
        from app.repositories.scheduling import DayTimeBlockRepository, QuarterRepository
        
        # Validate inputs
        dtb_repo = DayTimeBlockRepository(self.db)
        quarter_repo = QuarterRepository(self.db)
        
        day_time_block = dtb_repo.get_with_relations(day_time_block_id)
        if not day_time_block:
            raise NotFoundException("Day time block not found")
        
        quarter = quarter_repo.get_or_404(quarter_id)
        
        # Get available classrooms
        available = self.classroom_repo.get_available_classrooms(
            day_time_block_id,
            quarter_id,
            min_capacity
        )
        
        # Convert to availability schema
        result = []
        for classroom in available:
            availability = ClassroomAvailability(
                classroom_id=classroom.classroom_id,
                room_number=classroom.room_number,
                campus=classroom.campus.address,
                capacity=classroom.capacity,
                is_available=True,
                day=day_time_block.day.name,
                time_block=f"{day_time_block.time_block.start_time}-{day_time_block.time_block.end_time}",
                current_class=None,
                instructor=None
            )
            result.append(availability)
        
        return result
    
    # Department-Classroom operations
    def assign_classroom_to_department(
        self,
        assignment: DepartmentClassroomCreate
    ) -> DepartmentClassroomSchema:
        """Assign classroom to department."""
        # Validate department and classroom exist
        self.department_repo.get_or_404(assignment.department_id)
        self.classroom_repo.get_or_404(assignment.classroom_id)
        
        # Check if relationship already exists
        existing = self.dept_classroom_repo.get_by_ids(
            assignment.department_id,
            assignment.classroom_id
        )
        if existing:
            raise ConflictException(
                detail="Department already has access to this classroom",
                error_code="ASSIGNMENT_EXISTS"
            )
        
        # If marking as primary, unmark others
        if assignment.is_primary:
            current_assignments = self.dept_classroom_repo.get_department_classrooms(
                assignment.department_id
            )
            for ca in current_assignments:
                if ca.is_primary:
                    ca.is_primary = False
            self.db.commit()
        
        dept_classroom = self.dept_classroom_repo.create(obj_in=assignment)
        return DepartmentClassroomSchema.model_validate(dept_classroom)
    
    def update_classroom_assignment(
        self,
        department_id: int,
        classroom_id: int,
        update_data: DepartmentClassroomUpdate
    ) -> DepartmentClassroomSchema:
        """Update department-classroom assignment."""
        assignment = self.dept_classroom_repo.get_by_ids(department_id, classroom_id)
        if not assignment:
            raise NotFoundException("Assignment not found")
        
        # If marking as primary, unmark others
        if update_data.is_primary is True:
            current_assignments = self.dept_classroom_repo.get_department_classrooms(
                department_id
            )
            for ca in current_assignments:
                if ca.classroom_id != classroom_id and ca.is_primary:
                    ca.is_primary = False
            self.db.commit()
        
        assignment = self.dept_classroom_repo.update(
            db_obj=assignment,
            obj_in=update_data
        )
        return DepartmentClassroomSchema.model_validate(assignment)
    
    def remove_classroom_assignment(
        self,
        department_id: int,
        classroom_id: int
    ) -> None:
        """Remove classroom assignment from department."""
        assignment = self.dept_classroom_repo.get_by_ids(department_id, classroom_id)
        if not assignment:
            raise NotFoundException("Assignment not found")
        
        self.db.delete(assignment)
        self.db.commit()
    
    def get_department_classrooms(
        self,
        department_id: int
    ) -> List[DepartmentClassroomSchema]:
        """Get all classrooms assigned to a department."""
        self.department_repo.get_or_404(department_id)
        
        assignments = self.dept_classroom_repo.get_department_classrooms(department_id)
        return [
            DepartmentClassroomSchema.model_validate(a) 
            for a in assignments
        ]