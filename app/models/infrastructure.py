"""
Infrastructure domain models.
Maps campus, classroom, and department-classroom relationship tables.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models import Base, TimeStampMixin


class Campus(Base, TimeStampMixin):
    """Campus (sede) model."""

    __tablename__ = "campus"
    __table_args__ = {"comment": "Physical locations where classes are held"}
    __allow_unmapped__ = True

    campus_id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    email = Column(String(100), index=True)

    # Relationships
    classrooms = relationship("Classroom", back_populates="campus")

    def __repr__(self) -> str:
        return f"<Campus(id={self.campus_id}, address={self.address})>"


class Classroom(Base, TimeStampMixin):
    """Classroom (ambiente) model."""

    __tablename__ = "classroom"
    __table_args__ = {"comment": "Physical classrooms where classes are held"}
    __allow_unmapped__ = True

    classroom_id = Column(Integer, primary_key=True, autoincrement=True)
    room_number = Column(String(20), nullable=False)
    capacity = Column(Integer, nullable=False)
    campus_id = Column(
        Integer, ForeignKey("campus.campus_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    classroom_type = Column(String(50), default="Standard")

    # Relationships
    campus = relationship("Campus", back_populates="classrooms")
    departments = relationship("DepartmentClassroom", back_populates="classroom")
    class_schedules = relationship("ClassSchedule", back_populates="classroom")

    def __repr__(self) -> str:
        return f"<Classroom(id={self.classroom_id}, room={self.room_number})>"


class DepartmentClassroom(Base, TimeStampMixin):
    """Department-Classroom relationship model."""

    __tablename__ = "department_classroom"
    __table_args__ = {
        "comment": "Many-to-many relationship between departments and classrooms"
    }
    __allow_unmapped__ = True

    department_id = Column(
        Integer,
        ForeignKey("department.department_id", ondelete="CASCADE"),
        primary_key=True,
    )
    classroom_id = Column(
        Integer,
        ForeignKey("classroom.classroom_id", ondelete="CASCADE"),
        primary_key=True,
    )
    priority = Column(Integer, default=0, comment="Booking priority level")
    is_primary = Column(
        Boolean, default=False, comment="Is primary classroom for department"
    )

    # Relationships
    department = relationship("Department", back_populates="classrooms")
    classroom = relationship("Classroom", back_populates="departments")

    def __repr__(self) -> str:
        return f"<DepartmentClassroom(dept={self.department_id}, class={self.classroom_id})>"
