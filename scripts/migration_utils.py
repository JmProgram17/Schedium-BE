#!/usr/bin/env python
"""
Utility scripts for database migrations.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MigrationManager:
    """Manage Alembic migrations."""

    @staticmethod
    def create_migration(message: str):
        """Create a new migration."""
        print(f"📝 Creating migration: {message}")
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", message],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Migration created successfully!")
            print(result.stdout)
        else:
            print(f"❌ Error: {result.stderr}")

        return result.returncode == 0

    @staticmethod
    def upgrade(target: str = "head"):
        """Upgrade database to target revision."""
        print(f"⬆️  Upgrading to: {target}")
        result = subprocess.run(
            ["alembic", "upgrade", target], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Upgrade successful!")
        else:
            print(f"❌ Error: {result.stderr}")

        return result.returncode == 0

    @staticmethod
    def downgrade(target: str = "-1"):
        """Downgrade database to target revision."""
        print(f"⬇️  Downgrading to: {target}")

        # Confirm
        response = input("⚠️  Are you sure? This may cause data loss! (y/N): ")
        if response.lower() != "y":
            print("Cancelled.")
            return False

        result = subprocess.run(
            ["alembic", "downgrade", target], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✅ Downgrade successful!")
        else:
            print(f"❌ Error: {result.stderr}")

        return result.returncode == 0

    @staticmethod
    def current():
        """Show current revision."""
        print("📍 Current revision:")
        subprocess.run(["alembic", "current"])

    @staticmethod
    def history():
        """Show migration history."""
        print("📜 Migration history:")
        subprocess.run(["alembic", "history", "--verbose"])

    @staticmethod
    def heads():
        """Show head revisions."""
        print("🎯 Head revisions:")
        subprocess.run(["alembic", "heads"])

    @staticmethod
    def check():
        """Check if there are pending migrations."""
        print("🔍 Checking for model changes...")
        result = subprocess.run(["alembic", "check"], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Database is up to date with models!")
        else:
            print("⚠️  Model changes detected! Create a new migration.")
            print(result.stderr)

        return result.returncode == 0


def main():
    """Main CLI for migration management."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage database migrations")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create migration
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("message", help="Migration message")

    # Upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument(
        "target", nargs="?", default="head", help="Target revision"
    )

    # Downgrade
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument(
        "target", nargs="?", default="-1", help="Target revision"
    )

    # Other commands
    subparsers.add_parser("current", help="Show current revision")
    subparsers.add_parser("history", help="Show migration history")
    subparsers.add_parser("heads", help="Show head revisions")
    subparsers.add_parser("check", help="Check for pending changes")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = MigrationManager()

    if args.command == "create":
        manager.create_migration(args.message)
    elif args.command == "upgrade":
        manager.upgrade(args.target)
    elif args.command == "downgrade":
        manager.downgrade(args.target)
    elif args.command == "current":
        manager.current()
    elif args.command == "history":
        manager.history()
    elif args.command == "heads":
        manager.heads()
    elif args.command == "check":
        manager.check()


if __name__ == "__main__":
    main()
