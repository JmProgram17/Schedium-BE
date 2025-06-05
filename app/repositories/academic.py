"""
Academic domain repositories.
Handles database operations for academic entities.
"""

from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from app.models.academic import (
    Level, Chain, Nomenclature, Program, StudentGroup
)
from app.repositories.base import BaseRepository
from app.schemas.academic import (
    LevelCreate, LevelUpdate,
    ChainCreate, ChainUpdate,
    NomenclatureCreate, NomenclatureUpdate,
    ProgramCreate, ProgramUpdate,
    StudentGroupCreate, StudentGroupUpdate
)
from app.core.pagination import PaginationParams, Page, paginate


class LevelRepository(BaseRepository[Level, LevelCreate, LevelUpdate]):
    """Repository for academic levels."""
    
    def __init__(self, db: Session):
        super().__init__(Level, db)
    
    def get_by_study_type(self, study_type: str) -> Optional[Level]:
        """Get level by study type."""
        return self.db.query(Level).filter(
            Level.study_type == study_type
        ).first()
    
    def get_programs_count(self, level_id: int) -> int:
        """Get count of programs for this level."""
        from app.models.academic import Program
        return self.db.query(Program).filter(
            Program.level_id == level_id
        ).count()


class ChainRepository(BaseRepository[Chain, ChainCreate, ChainUpdate]):
    """Repository for program chains."""
    
    def __init__(self, db: Session):
        super().__init__(Chain, db)
    
    def get_by_name(self, name: str) -> Optional[Chain]:
        """Get chain by name."""
        return self.db.query(Chain).filter(Chain.name == name).first()
    
    def get_programs_count(self, chain_id: int) -> int:
        """Get count of programs in this chain."""
        from app.models.academic import Program
        return self.db.query(Program).filter(
            Program.chain_id == chain_id
        ).count()


class NomenclatureRepository(BaseRepository[Nomenclature, NomenclatureCreate, NomenclatureUpdate]):
    """Repository for nomenclatures."""
    
    def __init__(self, db: Session):
        super().__init__(Nomenclature, db)
    
    def get_by_code(self, code: str) -> Optional[Nomenclature]:
        """Get nomenclature by code."""
        return self.db.query(Nomenclature).filter(
            Nomenclature.code == code
        ).first()
    
    def get_active(self) -> List[Nomenclature]:
        """Get all active nomenclatures."""
        return self.db.query(Nomenclature).filter(
            Nomenclature.active == True
        ).all()
    
    def get_programs_count(self, nomenclature_id: int) -> int:
        """Get count of programs using this nomenclature."""
        from app.models.academic import Program
        return self.db.query(Program).filter(
            Program.nomenclature_id == nomenclature_id
        ).count()


class ProgramRepository(BaseRepository[Program, ProgramCreate, ProgramUpdate]):
    """Repository for academic programs."""
    
    def __init__(self, db: Session):
        super().__init__(Program, db)
    
    def get_with_relations(self, program_id: int) -> Optional[Program]:
        """Get program with all relations loaded."""
        return self.db.query(Program).options(
            joinedload(Program.nomenclature),
            joinedload(Program.chain),
            joinedload(Program.department),
            joinedload(Program.level)
        ).filter(Program.program_id == program_id).first()
    
    def search_programs(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        level_id: Optional[int] = None,
        chain_id: Optional[int] = None
    ) -> Page[Program]:
        """Search programs with filters."""
        query = self.db.query(Program).options(
            joinedload(Program.nomenclature),
            joinedload(Program.chain),
            joinedload(Program.department),
            joinedload(Program.level)
        )
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Program.name.ilike(f"%{search}%"),
                    Nomenclature.code.ilike(f"%{search}%")
                )
            ).join(Nomenclature, isouter=True)
        
        if department_id:
            query = query.filter(Program.department_id == department_id)
        
        if level_id:
            query = query.filter(Program.level_id == level_id)
        
        if chain_id:
            query = query.filter(Program.chain_id == chain_id)
        
        return paginate(query, params)
    
    def get_student_groups_count(self, program_id: int) -> int:
        """Get count of student groups for this program."""
        return self.db.query(StudentGroup).filter(
            StudentGroup.program_id == program_id
        ).count()


class StudentGroupRepository(BaseRepository[StudentGroup, StudentGroupCreate, StudentGroupUpdate]):
    """Repository for student groups (fichas)."""
    
    def __init__(self, db: Session):
        super().__init__(StudentGroup, db)
    
    def get_by_number(self, group_number: int) -> Optional[StudentGroup]:
        """Get group by number."""
        return self.db.query(StudentGroup).filter(
            StudentGroup.group_number == group_number
        ).first()
    
    def get_with_relations(self, group_id: int) -> Optional[StudentGroup]:
        """Get group with all relations loaded."""
        return self.db.query(StudentGroup).options(
            joinedload(StudentGroup.program).joinedload(Program.nomenclature),
            joinedload(StudentGroup.schedule)
        ).filter(StudentGroup.group_id == group_id).first()
    
    def search_groups(
        self,
        params: PaginationParams,
        search: Optional[str] = None,
        program_id: Optional[int] = None,
        schedule_id: Optional[int] = None,
        active: Optional[bool] = None,
        start_date_from: Optional[str] = None,
        start_date_to: Optional[str] = None
    ) -> Page[StudentGroup]:
        """Search student groups with filters."""
        query = self.db.query(StudentGroup).options(
            joinedload(StudentGroup.program).joinedload(Program.nomenclature),
            joinedload(StudentGroup.schedule)
        )
        
        # Apply filters
        if search:
            # Convert search to int if possible for group number search
            try:
                group_num = int(search)
                query = query.filter(
                    or_(
                        StudentGroup.group_number == group_num,
                        Program.name.ilike(f"%{search}%")
                    )
                ).join(Program, isouter=True)
            except ValueError:
                query = query.join(Program).filter(
                    Program.name.ilike(f"%{search}%")
                )
        
        if program_id:
            query = query.filter(StudentGroup.program_id == program_id)
        
        if schedule_id:
            query = query.filter(StudentGroup.schedule_id == schedule_id)
        
        if active is not None:
            query = query.filter(StudentGroup.active == active)
        
        if start_date_from:
            query = query.filter(StudentGroup.start_date >= start_date_from)
        
        if start_date_to:
            query = query.filter(StudentGroup.start_date <= start_date_to)
        
        return paginate(query, params)
    
    def get_active_groups(self) -> List[StudentGroup]:
        """Get all active student groups."""
        return self.db.query(StudentGroup).filter(
            StudentGroup.active == True
        ).all()
    
    def get_schedules_count(self, group_id: int) -> int:
        """Get count of class schedules for this group."""
        from app.models.scheduling import ClassSchedule
        return self.db.query(ClassSchedule).filter(
            ClassSchedule.group_id == group_id
        ).count()
    
    def disable_group(self, group_id: int) -> StudentGroup:
        """Disable a student group (soft delete)."""
        group = self.get_or_404(group_id)
        group.active = False
        self.db.commit()
        self.db.refresh(group)
        return group