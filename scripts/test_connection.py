#!/usr/bin/env python
"""
Test database connection and configuration.
Run this script to verify your setup is working correctly.
"""
import logging
import sys
from pathlib import Path

from sqlalchemy import text

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test database connection and basic operations."""
    try:
        from app.config import settings
        from app.database import engine, init_db

        print("🔍 Testing Database Connection...")
        print(
            f"📌 Database URL: mysql+pymysql://{settings.DB_USER}:****@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )

        # Initialize database
        init_db()
        print("✅ Database initialized successfully")

        # Test basic query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            print(f"✅ MySQL Version: {version}")

            # Test database exists
            result = conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            print(f"✅ Current Database: {db_name}")

            # Test tables exist
            result = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                """
                ),
                {"schema": settings.DB_NAME},
            )
            table_count = result.scalar()
            print(f"✅ Tables in database: {table_count}")

            # List some tables
            if table_count > 0:
                result = conn.execute(
                    text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = :schema
                        LIMIT 5
                    """
                    ),
                    {"schema": settings.DB_NAME},
                )
                print("📋 Sample tables:")
                for row in result:
                    print(f"   - {row[0]}")

        print("\n✅ All database tests passed!")
        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(
            "Make sure you're in the project directory and virtual environment is activated"
        )
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        logger.exception("Database connection test failed")
        return False


def test_configuration():
    """Test application configuration."""
    try:
        from app.config import settings

        print("\n🔍 Testing Configuration...")
        print(f"✅ APP_NAME: {settings.APP_NAME}")
        print(f"✅ APP_ENV: {settings.APP_ENV}")
        print(f"✅ DEBUG: {settings.DEBUG}")
        print(f"✅ API_V1_STR: {settings.API_V1_STR}")

        # Check critical settings
        if settings.SECRET_KEY == "CHANGE-THIS-SECRET-KEY":
            print("⚠️  WARNING: Using default SECRET_KEY - change for production!")
        else:
            print("✅ SECRET_KEY: Configured (hidden)")

        return True

    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Schedium Backend - Connection Test")
    print("=" * 50)

    config_ok = test_configuration()
    db_ok = test_database_connection()

    if config_ok and db_ok:
        print("\n🎉 All tests passed! Your setup is ready.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
