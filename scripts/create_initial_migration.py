#!/usr/bin/env python
"""
Create initial Alembic migration from existing database.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set UTF-8 encoding for subprocess
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"


def create_initial_migration():
    """Create the initial migration from existing models."""
    print("=" * 60)
    print("Creating Initial Migration")
    print("=" * 60)

    # Check if database exists
    from sqlalchemy import text

    from app.database import engine

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()"
                )
            )
            table_count = result.scalar()
            print(f"✅ Database connected. Found {table_count} tables.")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # Check if alembic_version table exists
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'alembic_version'"))
            if result.fetchone():
                print("⚠️  Warning: alembic_version table already exists.")
                print("   This might not be the first migration.")

                # Ask if user wants to continue
                response = input("\nContinue anyway? (y/N): ").lower()
                if response != "y":
                    print("Aborted.")
                    return False
    except:
        pass

    # Generate migration
    print("\n📝 Generating migration...")
    try:
        # Create migration with proper encoding
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", "Initial schema"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )

        if result.returncode != 0:
            print(f"❌ Migration generation failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

        print("✅ Migration generated successfully!")

        # Try to extract the migration file path
        output = result.stdout if result.stdout else ""

        # Look for the generated file in output
        import re

        patterns = [
            r"Generating (.+\.py)",
            r"Revision ID: ([a-f0-9]+)",
            r"Path: (.+\.py)",
        ]

        migration_file = None
        revision_id = None

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                if pattern.startswith("Generating"):
                    migration_file = match.group(1)
                elif pattern.startswith("Revision ID"):
                    revision_id = match.group(1)
                break

        if migration_file:
            print(f"\n📄 Migration file: {migration_file}")
        elif revision_id:
            print(f"\n📄 Revision ID: {revision_id}")
        else:
            # If we can't find it in output, look in the versions folder
            versions_dir = project_root / "alembic" / "versions"
            if versions_dir.exists():
                py_files = list(versions_dir.glob("*.py"))
                if py_files:
                    # Get the most recent file
                    latest_file = max(py_files, key=lambda p: p.stat().st_mtime)
                    print(f"\n📄 Latest migration file: {latest_file}")

        # Ask if user wants to apply it
        response = input("\nApply this migration now? (y/N): ").lower()
        if response == "y":
            print("\n🚀 Applying migration...")
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )

            if result.returncode == 0:
                print("✅ Migration applied successfully!")
                if result.stdout:
                    print(result.stdout)
            else:
                print(f"❌ Migration failed:")
                print(f"STDERR: {result.stderr}")
                return False

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_initial_migration()
    sys.exit(0 if success else 1)
