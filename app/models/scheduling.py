"""
Scheduling domain models.
Maps schedule, time blocks, days, quarters, and class schedules.
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models import Base, TimeStampMixin


class Schedule(Base, TimeStampMixin):
    """Schedule (jornada) model."""

    __tablename__ = "schedule"
    __table_args__ = {
        "comment": "Daily schedules for classes (morning, afternoon, evening, etc.)"
    }

    schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Relationships
    student_groups = relationship("StudentGroup", back_populates="schedule")

    def __repr__(self):
        return f"<Schedule(id={self.schedule_id}, name={self.name})>"


class TimeBlock(Base, TimeStampMixin):
    """Time block model."""

    __tablename__ = "time_block"
    __table_args__ = {"comment": "Time blocks for class scheduling"}

    time_block_id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer)  # Computed column in DB

    # Relationships
    day_time_blocks = relationship("DayTimeBlock", back_populates="time_block")

    __table_args__ = (
        UniqueConstraint("start_time", "end_time", name="uq_time_block_times"),
        {"comment": "Time blocks for class scheduling"},
    )

    def __repr__(self):
        return (
            f"<TimeBlock(id={self.time_block_id}, {self.start_time}-{self.end_time})>"
        )


class Day(Base, TimeStampMixin):
    """Day of week model."""

    __tablename__ = "day"
    __table_args__ = {"comment": "Days of the week"}

    day_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False, unique=True, index=True)

    # Relationships
    day_time_blocks = relationship("DayTimeBlock", back_populates="day")

    def __repr__(self):
        return f"<Day(id={self.day_id}, name={self.name})>"


class DayTimeBlock(Base, TimeStampMixin):
    """Day-TimeBlock relationship model."""

    __tablename__ = "day_time_block"
    __table_args__ = {
        "comment": "Association between days and time blocks for scheduling"
    }

    day_time_block_id = Column(Integer, primary_key=True, autoincrement=True)
    time_block_id = Column(
        Integer,
        ForeignKey("time_block.time_block_id", ondelete="CASCADE"),
        nullable=False,
    )
    day_id = Column(
        Integer, ForeignKey("day.day_id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    time_block = relationship("TimeBlock", back_populates="day_time_blocks")
    day = relationship("Day", back_populates="day_time_blocks")
    class_schedules = relationship("ClassSchedule", back_populates="day_time_block")

    __table_args__ = (
        UniqueConstraint("day_id", "time_block_id", name="uq_day_time_block"),
        {"comment": "Association between days and time blocks for scheduling"},
    )

    def __repr__(self):
        return f"<DayTimeBlock(id={self.day_time_block_id}, day={self.day_id}, block={self.time_block_id})>"


class Quarter(Base, TimeStampMixin):
    """Academic quarter model."""

    __tablename__ = "quarter"
    __table_args__ = {"comment": "Academic quarters for scheduling"}

    quarter_id = Column(Integer, primary_key=True, autoincrement=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    name = Column(String(50))  # Generated column in DB

    # Relationships
    class_schedules = relationship("ClassSchedule", back_populates="quarter")

    __table_args__ = (
        UniqueConstraint("start_date", "end_date", name="uq_quarter_dates"),
        {"comment": "Academic quarters for scheduling"},
    )

    def __repr__(self):
        return f"<Quarter(id={self.quarter_id}, name={self.name})>"


class ClassSchedule(Base, TimeStampMixin):
    """Class schedule (cronograma) model - Central entity."""

    __tablename__ = "class_schedule"
    __table_args__ = {
        "comment": "Class schedules linking instructors, groups, classrooms, and time slots"
    }

    class_schedule_id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String(255), nullable=False)
    quarter_id = Column(
        Integer, ForeignKey("quarter.quarter_id", ondelete="CASCADE"), nullable=False
    )
    day_time_block_id = Column(
        Integer,
        ForeignKey("day_time_block.day_time_block_id", ondelete="RESTRICT"),
        nullable=False,
    )
    group_id = Column(
        Integer,
        ForeignKey("student_group.group_id", ondelete="CASCADE"),
        nullable=False,
    )
    instructor_id = Column(
        Integer,
        ForeignKey("instructor.instructor_id", ondelete="RESTRICT"),
        nullable=False,
    )
    classroom_id = Column(
        Integer,
        ForeignKey("classroom.classroom_id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relationships
    quarter = relationship("Quarter", back_populates="class_schedules")
    day_time_block = relationship("DayTimeBlock", back_populates="class_schedules")
    group = relationship("StudentGroup", back_populates="class_schedules")
    instructor = relationship("Instructor", back_populates="class_schedules")
    classroom = relationship("Classroom", back_populates="class_schedules")

    __table_args__ = (
        UniqueConstraint(
            "day_time_block_id",
            "instructor_id",
            "quarter_id",
            name="uq_schedule_conflict_instructor",
        ),
        UniqueConstraint(
            "day_time_block_id",
            "classroom_id",
            "quarter_id",
            name="uq_schedule_conflict_classroom",
        ),
        UniqueConstraint(
            "day_time_block_id",
            "group_id",
            "quarter_id",
            name="uq_schedule_conflict_group",
        ),
        {
            "comment": "Class schedules linking instructors, groups, classrooms, and time slots"
        },
    )

    def __repr__(self):
        return f"<ClassSchedule(id={self.class_schedule_id}, subject={self.subject})>"
