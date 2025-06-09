"""
Scheduling domain repositories.
Handles database operations for scheduling entities.
"""

from datetime import date, time
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.pagination import Page, PaginationParams, paginate
from app.models.scheduling import (
    ClassSchedule,
    Day,
    DayTimeBlock,
    Quarter,
    Schedule,
    TimeBlock,
)
from app.repositories.base import BaseRepository
from app.schemas.scheduling import (
    ClassScheduleCreate,
    ClassScheduleUpdate,
    DayTimeBlockCreate,
    QuarterCreate,
    QuarterUpdate,
    ScheduleCreate,
    ScheduleUpdate,
    TimeBlockCreate,
    TimeBlockUpdate,
)


class ScheduleRepository(BaseRepository[Schedule, ScheduleCreate, ScheduleUpdate]):
    """Repository for schedules (jornadas)."""

    def __init__(self, db: Session):
        super().__init__(Schedule, db)

    def get_by_name(self, name: str) -> Optional[Schedule]:
        """Get schedule by name."""
        return self.db.query(Schedule).filter(Schedule.name == name).first()

    def get_groups_count(self, schedule_id: int) -> int:
        """Get count of student groups using this schedule."""
        from app.models.academic import StudentGroup

        return (
            self.db.query(StudentGroup)
            .filter(StudentGroup.schedule_id == schedule_id)
            .count()
        )

    def get_overlapping_schedules(
        self, start_time: time, end_time: time, exclude_id: Optional[int] = None
    ) -> List[Schedule]:
        """Get schedules that overlap with given time range."""
        query = self.db.query(Schedule).filter(
            or_(
                and_(Schedule.start_time <= start_time, Schedule.end_time > start_time),
                and_(Schedule.start_time < end_time, Schedule.end_time >= end_time),
                and_(Schedule.start_time >= start_time, Schedule.end_time <= end_time),
            )
        )

        if exclude_id:
            query = query.filter(Schedule.schedule_id != exclude_id)

        return query.all()


class TimeBlockRepository(BaseRepository[TimeBlock, TimeBlockCreate, TimeBlockUpdate]):
    """Repository for time blocks."""

    def __init__(self, db: Session):
        super().__init__(TimeBlock, db)

    def get_by_times(self, start_time: time, end_time: time) -> Optional[TimeBlock]:
        """Get time block by start and end times."""
        return (
            self.db.query(TimeBlock)
            .filter(
                and_(TimeBlock.start_time == start_time, TimeBlock.end_time == end_time)
            )
            .first()
        )

    def get_day_time_blocks_count(self, time_block_id: int) -> int:
        """Get count of day-time block associations."""
        return (
            self.db.query(DayTimeBlock)
            .filter(DayTimeBlock.time_block_id == time_block_id)
            .count()
        )

    def get_overlapping_blocks(
        self, start_time: time, end_time: time, exclude_id: Optional[int] = None
    ) -> List[TimeBlock]:
        """Get time blocks that overlap with given time range."""
        query = self.db.query(TimeBlock).filter(
            or_(
                and_(
                    TimeBlock.start_time <= start_time, TimeBlock.end_time > start_time
                ),
                and_(TimeBlock.start_time < end_time, TimeBlock.end_time >= end_time),
                and_(
                    TimeBlock.start_time >= start_time, TimeBlock.end_time <= end_time
                ),
            )
        )

        if exclude_id:
            query = query.filter(TimeBlock.time_block_id != exclude_id)

        return query.all()


class DayRepository(BaseRepository[Day, None, None]):
    """Repository for days of week."""

    def __init__(self, db: Session):
        super().__init__(Day, db)

    def get_by_name(self, name: str) -> Optional[Day]:
        """Get day by name."""
        return self.db.query(Day).filter(Day.name == name).first()

    def get_all_ordered(self) -> List[Day]:
        """Get all days ordered by ID (weekday order)."""
        return self.db.query(Day).order_by(Day.day_id).all()


class DayTimeBlockRepository(BaseRepository[DayTimeBlock, DayTimeBlockCreate, None]):
    """Repository for day-time block associations."""

    def __init__(self, db: Session):
        super().__init__(DayTimeBlock, db)

    def get_by_day_and_block(
        self, day_id: int, time_block_id: int
    ) -> Optional[DayTimeBlock]:
        """Get day-time block by day and time block IDs."""
        return (
            self.db.query(DayTimeBlock)
            .filter(
                and_(
                    DayTimeBlock.day_id == day_id,
                    DayTimeBlock.time_block_id == time_block_id,
                )
            )
            .first()
        )

    def get_with_relations(self, day_time_block_id: int) -> Optional[DayTimeBlock]:
        """Get day-time block with relations loaded."""
        return (
            self.db.query(DayTimeBlock)
            .options(joinedload(DayTimeBlock.day), joinedload(DayTimeBlock.time_block))
            .filter(DayTimeBlock.day_time_block_id == day_time_block_id)
            .first()
        )

    def get_schedules_count(self, day_time_block_id: int) -> int:
        """Get count of class schedules for this day-time block."""
        return (
            self.db.query(ClassSchedule)
            .filter(ClassSchedule.day_time_block_id == day_time_block_id)
            .count()
        )

    def get_by_day_name_and_time(
        self, day_name: str, start_time: time, end_time: time
    ) -> Optional[DayTimeBlock]:
        """Get day-time block by day name and time range."""
        return (
            self.db.query(DayTimeBlock)
            .join(Day)
            .join(TimeBlock)
            .filter(
                and_(
                    Day.name == day_name,
                    TimeBlock.start_time == start_time,
                    TimeBlock.end_time == end_time,
                )
            )
            .first()
        )


class QuarterRepository(BaseRepository[Quarter, QuarterCreate, QuarterUpdate]):
    """Repository for academic quarters."""

    def __init__(self, db: Session):
        super().__init__(Quarter, db)

    def get_by_dates(self, start_date: date, end_date: date) -> Optional[Quarter]:
        """Get quarter by start and end dates."""
        return (
            self.db.query(Quarter)
            .filter(
                and_(Quarter.start_date == start_date, Quarter.end_date == end_date)
            )
            .first()
        )

    def get_current_quarter(self) -> Optional[Quarter]:
        """Get the current active quarter."""
        today = date.today()
        return (
            self.db.query(Quarter)
            .filter(and_(Quarter.start_date <= today, Quarter.end_date >= today))
            .first()
        )

    def get_overlapping_quarters(
        self, start_date: date, end_date: date, exclude_id: Optional[int] = None
    ) -> List[Quarter]:
        """Get quarters that overlap with given date range."""
        query = self.db.query(Quarter).filter(
            or_(
                and_(Quarter.start_date <= start_date, Quarter.end_date >= start_date),
                and_(Quarter.start_date <= end_date, Quarter.end_date >= end_date),
                and_(Quarter.start_date >= start_date, Quarter.end_date <= end_date),
            )
        )

        if exclude_id:
            query = query.filter(Quarter.quarter_id != exclude_id)

        return query.all()

    def get_schedules_count(self, quarter_id: int) -> int:
        """Get count of class schedules in this quarter."""
        return (
            self.db.query(ClassSchedule)
            .filter(ClassSchedule.quarter_id == quarter_id)
            .count()
        )


class ClassScheduleRepository(
    BaseRepository[ClassSchedule, ClassScheduleCreate, ClassScheduleUpdate]
):
    """Repository for class schedules."""

    def __init__(self, db: Session):
        super().__init__(ClassSchedule, db)

    def get_with_relations(self, class_schedule_id: int) -> Optional[ClassSchedule]:
        """Get class schedule with all relations loaded."""
        return (
            self.db.query(ClassSchedule)
            .options(
                joinedload(ClassSchedule.quarter),
                joinedload(ClassSchedule.day_time_block).joinedload(DayTimeBlock.day),
                joinedload(ClassSchedule.day_time_block).joinedload(
                    DayTimeBlock.time_block
                ),
                joinedload(ClassSchedule.group).joinedload("program"),
                joinedload(ClassSchedule.instructor),
                joinedload(ClassSchedule.classroom).joinedload("campus"),
            )
            .filter(ClassSchedule.class_schedule_id == class_schedule_id)
            .first()
        )

    def check_instructor_conflict(
        self,
        instructor_id: int,
        day_time_block_id: int,
        quarter_id: int,
        exclude_id: Optional[int] = None,
    ) -> Optional[ClassSchedule]:
        """Check if instructor has a conflict at this time."""
        query = self.db.query(ClassSchedule).filter(
            and_(
                ClassSchedule.instructor_id == instructor_id,
                ClassSchedule.day_time_block_id == day_time_block_id,
                ClassSchedule.quarter_id == quarter_id,
            )
        )

        if exclude_id:
            query = query.filter(ClassSchedule.class_schedule_id != exclude_id)

        return query.first()

    def check_classroom_conflict(
        self,
        classroom_id: int,
        day_time_block_id: int,
        quarter_id: int,
        exclude_id: Optional[int] = None,
    ) -> Optional[ClassSchedule]:
        """Check if classroom has a conflict at this time."""
        query = self.db.query(ClassSchedule).filter(
            and_(
                ClassSchedule.classroom_id == classroom_id,
                ClassSchedule.day_time_block_id == day_time_block_id,
                ClassSchedule.quarter_id == quarter_id,
            )
        )

        if exclude_id:
            query = query.filter(ClassSchedule.class_schedule_id != exclude_id)

        return query.first()

    def check_group_conflict(
        self,
        group_id: int,
        day_time_block_id: int,
        quarter_id: int,
        exclude_id: Optional[int] = None,
    ) -> Optional[ClassSchedule]:
        """Check if student group has a conflict at this time."""
        query = self.db.query(ClassSchedule).filter(
            and_(
                ClassSchedule.group_id == group_id,
                ClassSchedule.day_time_block_id == day_time_block_id,
                ClassSchedule.quarter_id == quarter_id,
            )
        )

        if exclude_id:
            query = query.filter(ClassSchedule.class_schedule_id != exclude_id)

        return query.first()

    def search_schedules(
        self,
        params: PaginationParams,
        subject: Optional[str] = None,
        instructor_id: Optional[int] = None,
        group_id: Optional[int] = None,
        classroom_id: Optional[int] = None,
        quarter_id: Optional[int] = None,
        day_id: Optional[int] = None,
    ) -> Page[ClassSchedule]:
        """Search class schedules with filters."""
        query = self.db.query(ClassSchedule).options(
            joinedload(ClassSchedule.quarter),
            joinedload(ClassSchedule.day_time_block).joinedload(DayTimeBlock.day),
            joinedload(ClassSchedule.day_time_block).joinedload(
                DayTimeBlock.time_block
            ),
            joinedload(ClassSchedule.group),
            joinedload(ClassSchedule.instructor),
            joinedload(ClassSchedule.classroom),
        )

        # Apply filters
        if subject:
            query = query.filter(ClassSchedule.subject.ilike(f"%{subject}%"))

        if instructor_id:
            query = query.filter(ClassSchedule.instructor_id == instructor_id)

        if group_id:
            query = query.filter(ClassSchedule.group_id == group_id)

        if classroom_id:
            query = query.filter(ClassSchedule.classroom_id == classroom_id)

        if quarter_id:
            query = query.filter(ClassSchedule.quarter_id == quarter_id)

        if day_id:
            query = query.join(DayTimeBlock).filter(DayTimeBlock.day_id == day_id)

        return paginate(query, params)

    def get_instructor_schedule(
        self, instructor_id: int, quarter_id: int
    ) -> List[ClassSchedule]:
        """Get all schedules for an instructor in a quarter."""
        return (
            self.db.query(ClassSchedule)
            .options(
                joinedload(ClassSchedule.day_time_block).joinedload(DayTimeBlock.day),
                joinedload(ClassSchedule.day_time_block).joinedload(
                    DayTimeBlock.time_block
                ),
                joinedload(ClassSchedule.group),
                joinedload(ClassSchedule.classroom),
            )
            .filter(
                and_(
                    ClassSchedule.instructor_id == instructor_id,
                    ClassSchedule.quarter_id == quarter_id,
                )
            )
            .all()
        )

    def get_classroom_schedule(
        self, classroom_id: int, quarter_id: int
    ) -> List[ClassSchedule]:
        """Get all schedules for a classroom in a quarter."""
        return (
            self.db.query(ClassSchedule)
            .options(
                joinedload(ClassSchedule.day_time_block).joinedload(DayTimeBlock.day),
                joinedload(ClassSchedule.day_time_block).joinedload(
                    DayTimeBlock.time_block
                ),
                joinedload(ClassSchedule.instructor),
                joinedload(ClassSchedule.group),
            )
            .filter(
                and_(
                    ClassSchedule.classroom_id == classroom_id,
                    ClassSchedule.quarter_id == quarter_id,
                )
            )
            .all()
        )

    def get_group_schedule(self, group_id: int, quarter_id: int) -> List[ClassSchedule]:
        """Get all schedules for a student group in a quarter."""
        return (
            self.db.query(ClassSchedule)
            .options(
                joinedload(ClassSchedule.day_time_block).joinedload(DayTimeBlock.day),
                joinedload(ClassSchedule.day_time_block).joinedload(
                    DayTimeBlock.time_block
                ),
                joinedload(ClassSchedule.instructor),
                joinedload(ClassSchedule.classroom),
            )
            .filter(
                and_(
                    ClassSchedule.group_id == group_id,
                    ClassSchedule.quarter_id == quarter_id,
                )
            )
            .all()
        )
