"""
Human resources domain models.
Maps instructor, contract, and department tables.
"""

from sqlalchemy import DECIMAL, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models import Base, TimeStampMixin


class Department(Base, TimeStampMixin):
    """Department (coordination) model."""

    __tablename__ = "department"
    __table_args__ = {
        "comment": "Academic departments that manage programs and instructors"
    }

    department_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(20))
    email = Column(String(100), index=True)

    # Relationships
    programs = relationship("Program", back_populates="department")
    instructors = relationship("Instructor", back_populates="department")
    classrooms = relationship("DepartmentClassroom", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.department_id}, name={self.name})>"


class Contract(Base, TimeStampMixin):
    """Contract type model."""

    __tablename__ = "contract"
    __table_args__ = {"comment": "Instructor contract types"}

    contract_id = Column(Integer, primary_key=True, autoincrement=True)
    contract_type = Column(String(100), nullable=False, index=True)
    hour_limit = Column(Integer)

    # Relationships
    instructors = relationship("Instructor", back_populates="contract")

    def __repr__(self):
        return f"<Contract(id={self.contract_id}, type={self.contract_type})>"


class Instructor(Base, TimeStampMixin):
    """Instructor model."""

    __tablename__ = "instructor"
    __table_args__ = {"comment": "Instructors who teach courses"}

    instructor_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    phone_number = Column(String(20))
    email = Column(String(100), nullable=False, unique=True, index=True)
    hour_count = Column(DECIMAL(10, 2), default=0, comment="Total assigned hours")
    contract_id = Column(
        Integer, ForeignKey("contract.contract_id", ondelete="SET NULL")
    )
    department_id = Column(
        Integer, ForeignKey("department.department_id", ondelete="SET NULL")
    )
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    contract = relationship("Contract", back_populates="instructors")
    department = relationship("Department", back_populates="instructors")
    class_schedules = relationship("ClassSchedule", back_populates="instructor")

    @property
    def full_name(self):
        """Get instructor's full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Instructor(id={self.instructor_id}, name={self.full_name})>"
