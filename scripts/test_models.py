#!/usr/bin/env python
"""
Test SQLAlchemy models mapping.
Verifies all tables are correctly mapped.
"""
import sys
from pathlib import Path

from sqlalchemy import inspect

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))

from app.database import Base, engine
from app.models import academic, auth, hr, infrastructure, scheduling


def test_models_mapping():
    """Test that all models are correctly mapped to database tables."""

    print("🔍 Verificando mapeo de modelos...\n")

    # Import all models to ensure they're registered
    models = []

    # Auth models
    models.extend([auth.Role, auth.User])

    # Academic models
    models.extend(
        [
            academic.Level,
            academic.Chain,
            academic.Nomenclature,
            academic.Program,
            academic.StudentGroup,
        ]
    )

    # HR models
    models.extend([hr.Department, hr.Contract, hr.Instructor])

    # Infrastructure models
    models.extend(
        [
            infrastructure.Campus,
            infrastructure.Classroom,
            infrastructure.DepartmentClassroom,
        ]
    )

    # Scheduling models
    models.extend(
        [
            scheduling.Schedule,
            scheduling.TimeBlock,
            scheduling.Day,
            scheduling.DayTimeBlock,
            scheduling.Quarter,
            scheduling.ClassSchedule,
        ]
    )

    # Get all table names from database
    inspector = inspect(engine)
    db_tables = set(inspector.get_table_names())

    # Get all mapped tables
    mapped_tables = set()
    for model in models:
        mapped_tables.add(model.__tablename__)

    # Check mapping
    print(f"📊 Tablas en BD: {len(db_tables)}")
    print(f"📋 Modelos mapeados: {len(mapped_tables)}")

    # Find unmapped tables
    unmapped = db_tables - mapped_tables
    if unmapped:
        print(f"\n⚠️  Tablas sin mapear: {unmapped}")
    else:
        print("\n✅ Todas las tablas están mapeadas!")

    # Test relationships
    print("\n🔗 Verificando relaciones...")
    for model in models:
        relationships = inspect(model).relationships
        if relationships:
            print(f"\n{model.__name__}:")
            for rel in relationships:
                print(f"  - {rel.key} -> {rel.mapper.class_.__name__}")

    print("\n✅ Verificación completada!")


if __name__ == "__main__":
    test_models_mapping()
