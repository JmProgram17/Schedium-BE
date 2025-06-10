"""
Academic domain models.
Maps program, level, chain, nomenclature, and student group tables.
"""

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models import Base, TimeStampMixin


class Level(Base, TimeStampMixin):
    """Academic level model."""

    __tablename__ = "level"
    __table_args__ = {"comment": "Academic levels for programs"}
    __allow_unmapped__ = True

    level_id = Column(Integer, primary_key=True, autoincrement=True)
    study_type = Column(String(100), nullable=False, index=True)
    duration = Column(Integer, comment="Duration in months")

    # Relationships
    programs = relationship("Program", back_populates="level")

    def __repr__(self) -> str:
        return f"<Level(id={self.level_id}, type={self.study_type})>"


class Chain(Base, TimeStampMixin):
    """Program chain model."""

    __tablename__ = "chain"
    __table_args__ = {"comment": "Program chains or learning paths"}
    __allow_unmapped__ = True

    chain_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)

    # Relationships
    programs = relationship("Program", back_populates="chain")

    def __repr__(self) -> str:
        return f"<Chain(id={self.chain_id}, name={self.name})>"


class Nomenclature(Base, TimeStampMixin):
    """Program nomenclature model."""

    __tablename__ = "nomenclature"
    __table_args__ = {
        "comment": "Standardized abbreviations or codes for academic programs"
    }
    __allow_unmapped__ = True

    nomenclature_id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Abbreviation or short code",
    )
    description = Column(String(255), comment="Optional description")
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    programs = relationship("Program", back_populates="nomenclature")

    def __repr__(self) -> str:
        return f"<Nomenclature(id={self.nomenclature_id}, code={self.code})>"


class Program(Base, TimeStampMixin):
    """Academic program model."""

    __tablename__ = "program"
    __table_args__ = {"comment": "Academic programs offered by the institution"}
    __allow_unmapped__ = True

    program_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    nomenclature_id = Column(
        Integer, ForeignKey("nomenclature.nomenclature_id", ondelete="SET NULL"), index=True
    )
    chain_id = Column(Integer, ForeignKey("chain.chain_id", ondelete="SET NULL"), index=True)
    department_id = Column(
        Integer, ForeignKey("department.department_id", ondelete="SET NULL"), index=True
    )
    level_id = Column(Integer, ForeignKey("level.level_id", ondelete="SET NULL"), index=True)

    # Relationships
    nomenclature = relationship("Nomenclature", back_populates="programs")
    chain = relationship("Chain", back_populates="programs")
    department = relationship("Department", back_populates="programs")
    level = relationship("Level", back_populates="programs")
    student_groups = relationship("StudentGroup", back_populates="program")

    def __repr__(self) -> str:
        return f"<Program(id={self.program_id}, name={self.name})>"


class StudentGroup(Base, TimeStampMixin):
    """Student group (ficha) model."""

    __tablename__ = "student_group"
    __table_args__ = {"comment": "Student groups assigned to specific programs"}
    __allow_unmapped__ = True

    group_id = Column(Integer, primary_key=True, autoincrement=True)
    group_number = Column(Integer, nullable=False, unique=True, index=True)
    program_id = Column(Integer, ForeignKey("program.program_id", ondelete="RESTRICT"), index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    capacity = Column(Integer, nullable=False)
    schedule_id = Column(
        Integer, ForeignKey("schedule.schedule_id", ondelete="RESTRICT"), index=True
    )
    active = Column(Boolean, default=True, nullable=False)

    # Relationships
    program = relationship("Program", back_populates="student_groups")
    schedule = relationship("Schedule", back_populates="student_groups")
    class_schedules = relationship("ClassSchedule", back_populates="group")

    def __repr__(self) -> str:
        return f"<StudentGroup(id={self.group_id}, number={self.group_number})>"
