"""
Scheduling domain services.
Handles business logic for scheduling entities.
"""

from typing import Optional, List, Dict, Any
from datetime import date, time, timedelta
from sqlalchemy.orm import Session

from app.models.scheduling import (
    Schedule, TimeBlock, Day, DayTimeBlock, Quarter, ClassSchedule
)
from app.schemas.scheduling import (
    ScheduleCreate, ScheduleUpdate, Schedule as ScheduleSchema,
    TimeBlockCreate, TimeBlockUpdate, TimeBlock as TimeBlockSchema,
    Day as DaySchema,
    DayTimeBlockCreate, DayTimeBlock as DayTimeBlockSchema,
    QuarterCreate, QuarterUpdate, Quarter as QuarterSchema,
    ClassScheduleCreate, ClassScheduleUpdate, ClassSchedule as ClassScheduleSchema,
    ClassScheduleDetailed, ScheduleConflict, ScheduleValidation
)
from app.repositories.scheduling import (
    ScheduleRepository, TimeBlockRepository, DayRepository,
    DayTimeBlockRepository, QuarterRepository, ClassScheduleRepository
)
from app.repositories.academic import StudentGroupRepository
from app.repositories.hr import InstructorRepository
from app.repositories.infrastructure import ClassroomRepository
from app.core.exceptions import (
    NotFoundException, ConflictException, BadRequestException,
    ScheduleConflictException, InstructorOverloadException
)
from app.core.pagination import PaginationParams, Page


class SchedulingService:
    """Service for scheduling operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.schedule_repo = ScheduleRepository(db)
        self.time_block_repo = TimeBlockRepository(db)
        self.day_repo = DayRepository(db)
        self.day_time_block_repo = DayTimeBlockRepository(db)
        self.quarter_repo = QuarterRepository(db)
        self.class_schedule_repo = ClassScheduleRepository(db)
        
        # Related repositories
        self.group_repo = StudentGroupRepository(db)
        self.instructor_repo = InstructorRepository(db)
        self.classroom_repo = ClassroomRepository(db)
    
    # Schedule (Jornada) operations
    def create_schedule(self, schedule_in: ScheduleCreate) -> ScheduleSchema:
        """Create a new schedule."""
        # Check name uniqueness
        existing = self.schedule_repo.get_by_name(schedule_in.name)
        if existing:
            raise ConflictException(
                detail=f"Schedule '{schedule_in.name}' already exists",
                error_code="SCHEDULE_EXISTS"
            )
        
        # Check time validity
        if schedule_in.end_time <= schedule_in.start_time:
            raise BadRequestException(
                detail="End time must be after start time",
                error_code="INVALID_TIME_RANGE"
            )
        
        # Check for overlapping schedules
        overlapping = self.schedule_repo.get_overlapping_schedules(
            schedule_in.start_time,
            schedule_in.end_time
        )
        if overlapping:
            raise ConflictException(
                detail=f"Schedule overlaps with: {', '.join([s.name for s in overlapping])}",
                error_code="SCHEDULE_OVERLAP"
            )
        
        schedule = self.schedule_repo.create(obj_in=schedule_in)
        return ScheduleSchema.model_validate(schedule)
    
    def get_schedule(self, schedule_id: int) -> ScheduleSchema:
        """Get schedule by ID."""
        schedule = self.schedule_repo.get_or_404(schedule_id)
        return ScheduleSchema.model_validate(schedule)
    
    def get_schedules(self, params: PaginationParams) -> Page[ScheduleSchema]:
        """Get paginated list of schedules."""
        page = self.schedule_repo.get_paginated(params)
        page.items = [ScheduleSchema.model_validate(item) for item in page.items]
        return page
    
    def update_schedule(
        self,
        schedule_id: int,
        schedule_in: ScheduleUpdate
    ) -> ScheduleSchema:
        """Update schedule."""
        schedule = self.schedule_repo.get_or_404(schedule_id)
        
        # Check name uniqueness if changed
        if schedule_in.name and schedule_in.name != schedule.name:
            existing = self.schedule_repo.get_by_name(schedule_in.name)
            if existing:
                raise ConflictException(
                    detail=f"Schedule '{schedule_in.name}' already exists",
                    error_code="SCHEDULE_EXISTS"
                )
        
        # Validate times if changed
        update_data = schedule_in.model_dump(exclude_unset=True)
        start_time = update_data.get("start_time", schedule.start_time)
        end_time = update_data.get("end_time", schedule.end_time)
        
        if end_time <= start_time:
            raise BadRequestException(
                detail="End time must be after start time",
                error_code="INVALID_TIME_RANGE"
            )
        
        # Check for overlapping schedules
        if "start_time" in update_data or "end_time" in update_data:
            overlapping = self.schedule_repo.get_overlapping_schedules(
                start_time, end_time, exclude_id=schedule_id
            )
            if overlapping:
                raise ConflictException(
                    detail=f"Schedule overlaps with: {', '.join([s.name for s in overlapping])}",
                    error_code="SCHEDULE_OVERLAP"
                )
        
        schedule = self.schedule_repo.update(db_obj=schedule, obj_in=schedule_in)
        return ScheduleSchema.model_validate(schedule)
    
    def delete_schedule(self, schedule_id: int) -> None:
        """Delete schedule."""
        schedule = self.schedule_repo.get_or_404(schedule_id)
        
        # Check if schedule is in use
        groups_count = self.schedule_repo.get_groups_count(schedule_id)
        if groups_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete schedule. {groups_count} student groups use it",
                error_code="SCHEDULE_IN_USE"
            )
        
        self.schedule_repo.delete(id=schedule_id)
    
    # Time Block operations
    def create_time_block(self, block_in: TimeBlockCreate) -> TimeBlockSchema:
        """Create a new time block."""
        # Check if times already exist
        existing = self.time_block_repo.get_by_times(
            block_in.start_time,
            block_in.end_time
        )
        if existing:
            raise ConflictException(
                detail="Time block with these times already exists",
                error_code="TIME_BLOCK_EXISTS"
            )
        
        # Validate times
        if block_in.end_time <= block_in.start_time:
            raise BadRequestException(
                detail="End time must be after start time",
                error_code="INVALID_TIME_RANGE"
            )
        
        block = self.time_block_repo.create(obj_in=block_in)
        return TimeBlockSchema.model_validate(block)
    
    def get_time_block(self, time_block_id: int) -> TimeBlockSchema:
        """Get time block by ID."""
        block = self.time_block_repo.get_or_404(time_block_id)
        return TimeBlockSchema.model_validate(block)
    
    def get_time_blocks(self, params: PaginationParams) -> Page[TimeBlockSchema]:
        """Get paginated list of time blocks."""
        page = self.time_block_repo.get_paginated(
            params,
            order_by="start_time"
        )
        page.items = [TimeBlockSchema.model_validate(item) for item in page.items]
        return page
    
    def update_time_block(
        self,
        time_block_id: int,
        block_in: TimeBlockUpdate
    ) -> TimeBlockSchema:
        """Update time block."""
        block = self.time_block_repo.get_or_404(time_block_id)
        
        # Check if block is in use
        usage_count = self.time_block_repo.get_day_time_blocks_count(time_block_id)
        if usage_count > 0:
            raise BadRequestException(
                detail="Cannot modify time block that is in use",
                error_code="TIME_BLOCK_IN_USE"
            )
        
        # Validate times if changed
        update_data = block_in.model_dump(exclude_unset=True)
        start_time = update_data.get("start_time", block.start_time)
        end_time = update_data.get("end_time", block.end_time)
        
        if end_time <= start_time:
            raise BadRequestException(
                detail="End time must be after start time",
                error_code="INVALID_TIME_RANGE"
            )
        
        # Check uniqueness if times changed
        if "start_time" in update_data or "end_time" in update_data:
            existing = self.time_block_repo.get_by_times(start_time, end_time)
            if existing and existing.time_block_id != time_block_id:
                raise ConflictException(
                    detail="Time block with these times already exists",
                    error_code="TIME_BLOCK_EXISTS"
                )
        
        block = self.time_block_repo.update(db_obj=block, obj_in=block_in)
        return TimeBlockSchema.model_validate(block)
    
    def delete_time_block(self, time_block_id: int) -> None:
        """Delete time block."""
        block = self.time_block_repo.get_or_404(time_block_id)
        
        # Check if block is in use
        usage_count = self.time_block_repo.get_day_time_blocks_count(time_block_id)
        if usage_count > 0:
            raise BadRequestException(
                detail="Cannot delete time block that is in use",
                error_code="TIME_BLOCK_IN_USE"
            )
        
        self.time_block_repo.delete(id=time_block_id)
    
    # Day operations
    def get_days(self) -> List[DaySchema]:
        """Get all days of the week."""
        days = self.day_repo.get_all_ordered()
        return [DaySchema.model_validate(day) for day in days]
    
    # Day-Time Block operations
    def create_day_time_block(self, dtb_in: DayTimeBlockCreate) -> DayTimeBlockSchema:
        """Create day-time block association."""
        # Validate day and time block exist
        self.day_repo.get_or_404(dtb_in.day_id)
        self.time_block_repo.get_or_404(dtb_in.time_block_id)
        
        # Check if association already exists
        existing = self.day_time_block_repo.get_by_day_and_block(
            dtb_in.day_id,
            dtb_in.time_block_id
        )
        if existing:
            raise ConflictException(
                detail="This day-time block combination already exists",
                error_code="DAY_TIME_BLOCK_EXISTS"
            )
        
        dtb = self.day_time_block_repo.create(obj_in=dtb_in)
        dtb = self.day_time_block_repo.get_with_relations(dtb.day_time_block_id)
        return DayTimeBlockSchema.model_validate(dtb)
    
    def get_day_time_blocks(self, params: PaginationParams) -> Page[DayTimeBlockSchema]:
        """Get paginated list of day-time blocks."""
        page = self.day_time_block_repo.get_paginated(params)
        page.items = [DayTimeBlockSchema.model_validate(item) for item in page.items]
        return page
    
    def delete_day_time_block(self, day_time_block_id: int) -> None:
        """Delete day-time block."""
        dtb = self.day_time_block_repo.get_or_404(day_time_block_id)
        
        # Check if in use
        schedules_count = self.day_time_block_repo.get_schedules_count(day_time_block_id)
        if schedules_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete. {schedules_count} schedules use this time slot",
                error_code="DAY_TIME_BLOCK_IN_USE"
            )
        
        self.day_time_block_repo.delete(id=day_time_block_id)
    
    # Quarter operations
    def create_quarter(self, quarter_in: QuarterCreate) -> QuarterSchema:
        """Create a new quarter."""
        # Check date validity
        if quarter_in.end_date <= quarter_in.start_date:
            raise BadRequestException(
                detail="End date must be after start date",
                error_code="INVALID_DATE_RANGE"
            )
        
        # Check if dates already exist
        existing = self.quarter_repo.get_by_dates(
            quarter_in.start_date,
            quarter_in.end_date
        )
        if existing:
            raise ConflictException(
                detail="Quarter with these dates already exists",
                error_code="QUARTER_EXISTS"
            )
        
        # Check for overlapping quarters
        overlapping = self.quarter_repo.get_overlapping_quarters(
            quarter_in.start_date,
            quarter_in.end_date
        )
        if overlapping:
            raise ConflictException(
                detail=f"Quarter overlaps with: {', '.join([q.name for q in overlapping])}",
                error_code="QUARTER_OVERLAP"
            )
        
        quarter = self.quarter_repo.create(obj_in=quarter_in)
        return QuarterSchema.model_validate(quarter)
    
    def get_quarter(self, quarter_id: int) -> QuarterSchema:
        """Get quarter by ID."""
        quarter = self.quarter_repo.get_or_404(quarter_id)
        return QuarterSchema.model_validate(quarter)
    
    def get_quarters(self, params: PaginationParams) -> Page[QuarterSchema]:
        """Get paginated list of quarters."""
        page = self.quarter_repo.get_paginated(
            params,
            order_by="start_date",
            order_desc=True
        )
        page.items = [QuarterSchema.model_validate(item) for item in page.items]
        return page
    
    def get_current_quarter(self) -> Optional[QuarterSchema]:
        """Get the current active quarter."""
        quarter = self.quarter_repo.get_current_quarter()
        return QuarterSchema.model_validate(quarter) if quarter else None
    
    def update_quarter(
        self,
        quarter_id: int,
        quarter_in: QuarterUpdate
    ) -> QuarterSchema:
        """Update quarter."""
        quarter = self.quarter_repo.get_or_404(quarter_id)
        
        # Validate dates if changed
        update_data = quarter_in.model_dump(exclude_unset=True)
        start_date = update_data.get("start_date", quarter.start_date)
        end_date = update_data.get("end_date", quarter.end_date)
        
        if end_date <= start_date:
            raise BadRequestException(
                detail="End date must be after start date",
                error_code="INVALID_DATE_RANGE"
            )
        
        # Check for overlapping quarters
        if "start_date" in update_data or "end_date" in update_data:
            overlapping = self.quarter_repo.get_overlapping_quarters(
                start_date, end_date, exclude_id=quarter_id
            )
            if overlapping:
                raise ConflictException(
                    detail=f"Quarter overlaps with: {', '.join([q.name for q in overlapping])}",
                    error_code="QUARTER_OVERLAP"
                )
        
        quarter = self.quarter_repo.update(db_obj=quarter, obj_in=quarter_in)
        return QuarterSchema.model_validate(quarter)
    
    def delete_quarter(self, quarter_id: int) -> None:
        """Delete quarter."""
        quarter = self.quarter_repo.get_or_404(quarter_id)
        
        # Check if quarter has schedules
        schedules_count = self.quarter_repo.get_schedules_count(quarter_id)
        if schedules_count > 0:
            raise BadRequestException(
                detail=f"Cannot delete quarter. {schedules_count} schedules exist",
                error_code="QUARTER_HAS_SCHEDULES"
            )
        
        self.quarter_repo.delete(id=quarter_id)
    
    # Class Schedule operations
    def validate_schedule(self, schedule_in: ClassScheduleCreate) -> ScheduleValidation:
        """Validate a class schedule for conflicts."""
        conflicts = []
        warnings = []
        
        # Check instructor conflict
        instructor_conflict = self.class_schedule_repo.check_instructor_conflict(
            schedule_in.instructor_id,
            schedule_in.day_time_block_id,
            schedule_in.quarter_id
        )
        if instructor_conflict:
            instructor = self.instructor_repo.get(schedule_in.instructor_id)
            conflicts.append(ScheduleConflict(
                conflict_type="instructor",
                resource_id=schedule_in.instructor_id,
                resource_name=instructor.full_name if instructor else "Unknown",
                existing_schedule_id=instructor_conflict.class_schedule_id,
                existing_subject=instructor_conflict.subject,
                day=instructor_conflict.day_time_block.day.name,
                time_block=f"{instructor_conflict.day_time_block.time_block.start_time}-{instructor_conflict.day_time_block.time_block.end_time}"
            ))
        
        # Check classroom conflict
        classroom_conflict = self.class_schedule_repo.check_classroom_conflict(
            schedule_in.classroom_id,
            schedule_in.day_time_block_id,
            schedule_in.quarter_id
        )
        if classroom_conflict:
            classroom = self.classroom_repo.get(schedule_in.classroom_id)
            conflicts.append(ScheduleConflict(
                conflict_type="classroom",
                resource_id=schedule_in.classroom_id,
                resource_name=f"Room {classroom.room_number}" if classroom else "Unknown",
                existing_schedule_id=classroom_conflict.class_schedule_id,
                existing_subject=classroom_conflict.subject,
                day=classroom_conflict.day_time_block.day.name,
                time_block=f"{classroom_conflict.day_time_block.time_block.start_time}-{classroom_conflict.day_time_block.time_block.end_time}"
            ))
        
        # Check group conflict
        group_conflict = self.class_schedule_repo.check_group_conflict(
            schedule_in.group_id,
            schedule_in.day_time_block_id,
            schedule_in.quarter_id
        )
        if group_conflict:
            group = self.group_repo.get(schedule_in.group_id)
            conflicts.append(ScheduleConflict(
                conflict_type="group",
                resource_id=schedule_in.group_id,
                resource_name=f"Group {group.group_number}" if group else "Unknown",
                existing_schedule_id=group_conflict.class_schedule_id,
                existing_subject=group_conflict.subject,
                day=group_conflict.day_time_block.day.name,
                time_block=f"{group_conflict.day_time_block.time_block.start_time}-{group_conflict.day_time_block.time_block.end_time}"
            ))
        
        # Check instructor workload
        instructor = self.instructor_repo.get(schedule_in.instructor_id)
        if instructor and instructor.contract and instructor.contract.hour_limit:
            dtb = self.day_time_block_repo.get_with_relations(schedule_in.day_time_block_id)
            if dtb:
                hours_to_add = dtb.time_block.duration_minutes / 60
                total_hours = float(instructor.hour_count) + hours_to_add
                
                if total_hours > instructor.contract.hour_limit:
                    warnings.append(
                        f"Instructor {instructor.full_name} will exceed hour limit "
                        f"({total_hours:.1f}/{instructor.contract.hour_limit} hours)"
                    )
        
        # Check classroom capacity
        classroom = self.classroom_repo.get(schedule_in.classroom_id)
        group = self.group_repo.get(schedule_in.group_id)
        if classroom and group and classroom.capacity < group.capacity:
            warnings.append(
                f"Classroom capacity ({classroom.capacity}) is less than "
                f"group size ({group.capacity})"
            )
        
        return ScheduleValidation(
            is_valid=len(conflicts) == 0,
            conflicts=conflicts,
            warnings=warnings
        )
    
    def create_class_schedule(self, schedule_in: ClassScheduleCreate) -> ClassScheduleDetailed:
        """Create a new class schedule."""
        # Validate all foreign keys
        self.quarter_repo.get_or_404(schedule_in.quarter_id)
        self.day_time_block_repo.get_or_404(schedule_in.day_time_block_id)
        self.group_repo.get_or_404(schedule_in.group_id)
        self.instructor_repo.get_or_404(schedule_in.instructor_id)
        self.classroom_repo.get_or_404(schedule_in.classroom_id)
        
        # Validate for conflicts
        validation = self.validate_schedule(schedule_in)
        if not validation.is_valid:
            conflict = validation.conflicts[0]
            raise ScheduleConflictException(
                detail=f"{conflict.conflict_type.title()} conflict: {conflict.resource_name} "
                       f"already has '{conflict.existing_subject}' at this time",
                conflict_type=conflict.conflict_type
            )
        
        # Create schedule
        schedule = self.class_schedule_repo.create(obj_in=schedule_in)
        
        # The database trigger will handle updating instructor hours
        
        # Get with relations and return
        schedule = self.class_schedule_repo.get_with_relations(schedule.class_schedule_id)
        return ClassScheduleDetailed.model_validate(schedule)
    
    def get_class_schedule(self, class_schedule_id: int) -> ClassScheduleDetailed:
        """Get class schedule by ID."""
        schedule = self.class_schedule_repo.get_with_relations(class_schedule_id)
        if not schedule:
            raise NotFoundException(f"Class schedule with id {class_schedule_id} not found")
        return ClassScheduleDetailed.model_validate(schedule)
    
    def get_class_schedules(
        self,
        params: PaginationParams,
        subject: Optional[str] = None,
        instructor_id: Optional[int] = None,
        group_id: Optional[int] = None,
        classroom_id: Optional[int] = None,
        quarter_id: Optional[int] = None,
        day_id: Optional[int] = None
    ) -> Page[ClassScheduleDetailed]:
        """Get paginated list of class schedules."""
        page = self.class_schedule_repo.search_schedules(
            params, subject, instructor_id, group_id,
            classroom_id, quarter_id, day_id
        )
        page.items = [ClassScheduleDetailed.model_validate(item) for item in page.items]
        return page
    
    def update_class_schedule(
        self,
        class_schedule_id: int,
        schedule_in: ClassScheduleUpdate
    ) -> ClassScheduleDetailed:
        """Update class schedule."""
        schedule = self.class_schedule_repo.get_or_404(class_schedule_id)
        
        # If critical fields are changing, validate for conflicts
        if any([
            schedule_in.instructor_id is not None,
            schedule_in.classroom_id is not None,
            schedule_in.group_id is not None,
            schedule_in.day_time_block_id is not None,
            schedule_in.quarter_id is not None
        ]):
            # Create a validation object with current + new values
            validation_data = ClassScheduleCreate(
                subject=schedule_in.subject or schedule.subject,
                quarter_id=schedule_in.quarter_id or schedule.quarter_id,
                day_time_block_id=schedule_in.day_time_block_id or schedule.day_time_block_id,
                group_id=schedule_in.group_id or schedule.group_id,
                instructor_id=schedule_in.instructor_id or schedule.instructor_id,
                classroom_id=schedule_in.classroom_id or schedule.classroom_id
            )
            
            # Check conflicts excluding current schedule
            validation = self.validate_schedule(validation_data)
            
            # Filter out conflicts from the current schedule
            validation.conflicts = [
                c for c in validation.conflicts 
                if c.existing_schedule_id != class_schedule_id
            ]
            
            if validation.conflicts:
                conflict = validation.conflicts[0]
                raise ScheduleConflictException(
                    detail=f"{conflict.conflict_type.title()} conflict: {conflict.resource_name} "
                           f"already has '{conflict.existing_subject}' at this time",
                    conflict_type=conflict.conflict_type
                )
        
        # Update schedule
        schedule = self.class_schedule_repo.update(db_obj=schedule, obj_in=schedule_in)
        
        # The database trigger will handle updating instructor hours
        
        # Get with relations and return
        schedule = self.class_schedule_repo.get_with_relations(class_schedule_id)
        return ClassScheduleDetailed.model_validate(schedule)
    
    def delete_class_schedule(self, class_schedule_id: int) -> None:
        """Delete class schedule."""
        # The database trigger will handle updating instructor hours
        self.class_schedule_repo.delete(id=class_schedule_id)
    
    # Schedule queries
    def get_instructor_schedule(
        self,
        instructor_id: int,
        quarter_id: int
    ) -> List[ClassScheduleDetailed]:
        """Get all schedules for an instructor in a quarter."""
        self.instructor_repo.get_or_404(instructor_id)
        self.quarter_repo.get_or_404(quarter_id)
        
        schedules = self.class_schedule_repo.get_instructor_schedule(
            instructor_id, quarter_id
        )
        return [ClassScheduleDetailed.model_validate(s) for s in schedules]
    
    def get_classroom_schedule(
        self,
        classroom_id: int,
        quarter_id: int
    ) -> List[ClassScheduleDetailed]:
        """Get all schedules for a classroom in a quarter."""
        self.classroom_repo.get_or_404(classroom_id)
        self.quarter_repo.get_or_404(quarter_id)
        
        schedules = self.class_schedule_repo.get_classroom_schedule(
            classroom_id, quarter_id
        )
        return [ClassScheduleDetailed.model_validate(s) for s in schedules]
    
    def get_group_schedule(
        self,
        group_id: int,
        quarter_id: int
    ) -> List[ClassScheduleDetailed]:
        """Get all schedules for a student group in a quarter."""
        self.group_repo.get_or_404(group_id)
        self.quarter_repo.get_or_404(quarter_id)
        
        schedules = self.class_schedule_repo.get_group_schedule(
            group_id, quarter_id
        )
        return [ClassScheduleDetailed.model_validate(s) for s in schedules]