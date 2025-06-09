# check_tables.py
"""
Script para verificar todas las tablas y vistas en la base de datos.
"""
import sys
from pathlib import Path

from sqlalchemy import text
from tabulate import tabulate

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))

from app.config import settings
from app.database import engine


def check_database_structure():
    """Verificar estructura completa de la base de datos."""
    print("🔍 Analizando estructura de la base de datos...\n")

    with engine.connect() as conn:
        # Obtener todas las tablas
        result = conn.execute(
            text(
                """
                SELECT
                    table_name,
                    table_type,
                    COALESCE(table_comment, '') as comment
                FROM information_schema.tables
                WHERE table_schema = :schema
                ORDER BY table_type DESC, table_name
            """
            ),
            {"schema": settings.DB_NAME},
        )

        tables_data = []
        views_data = []

        for row in result:
            table_info = [row[0], row[2] if row[2] else "-"]
            if row[1] == "BASE TABLE":
                tables_data.append(table_info)
            else:
                views_data.append(table_info)

        # Mostrar tablas
        print(f"📊 TABLAS BASE ({len(tables_data)} tablas):")
        print(tabulate(tables_data, headers=["Tabla", "Descripción"], tablefmt="grid"))

        # Mostrar vistas
        if views_data:
            print(f"\n👁️ VISTAS ({len(views_data)} vistas):")
            print(
                tabulate(views_data, headers=["Vista", "Descripción"], tablefmt="grid")
            )

        # Verificar triggers
        result = conn.execute(
            text(
                """
                SELECT trigger_name, event_manipulation, event_object_table
                FROM information_schema.triggers
                WHERE trigger_schema = :schema
            """
            ),
            {"schema": settings.DB_NAME},
        )

        triggers = list(result)
        if triggers:
            print(f"\n⚡ TRIGGERS ({len(triggers)} triggers):")
            trigger_data = [[t[0], t[1], t[2]] for t in triggers]
            print(
                tabulate(
                    trigger_data,
                    headers=["Trigger", "Evento", "Tabla"],
                    tablefmt="grid",
                )
            )

        # Resumen
        print(f"\n📈 RESUMEN:")
        print(f"   - Tablas: {len(tables_data)}")
        print(f"   - Vistas: {len(views_data)}")
        print(f"   - Triggers: {len(triggers)}")
        print(
            f"   - Total objetos: {len(tables_data) + len(views_data) + len(triggers)}"
        )


if __name__ == "__main__":
    # Instalar tabulate si no lo tienes
    # pip install tabulate
    check_database_structure()
