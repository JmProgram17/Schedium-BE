#!/usr/bin/env python
"""
Complete validation script for Schedium Backend.
Checks all components and provides a health report.
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BLUE}{title}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.ENDC}")


def check_mark(condition: bool) -> str:
    """Return check mark or X based on condition."""
    return (
        f"{Colors.GREEN}✅{Colors.ENDC}" if condition else f"{Colors.RED}❌{Colors.ENDC}"
    )


def validate_environment():
    """Validate environment setup."""
    print_header("1. Environment Validation")

    checks = {
        "Python 3.11+": sys.version_info >= (3, 11),
        ".env file exists": (project_root / ".env").exists(),
        "Virtual environment active": hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix),
    }

    for check, passed in checks.items():
        print(f"{check_mark(passed)} {check}")

    return all(checks.values())


def validate_dependencies():
    """Validate required dependencies."""
    print_header("2. Dependencies Validation")

    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "alembic",
        "pymysql",
        "python-jose",
        "passlib",
        "python-multipart",
        "email-validator",
    ]

    checks = {}
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            checks[package] = True
        except ImportError:
            checks[package] = False

    for package, installed in checks.items():
        print(f"{check_mark(installed)} {package}")

    return all(checks.values())


def validate_database_connection():
    """Validate database connection."""
    print_header("3. Database Connection")

    try:
        from sqlalchemy import text

        from app.database import engine, init_db

        init_db()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        print(f"{check_mark(True)} Database connection successful")

        # Check tables
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                """
                )
            )
            table_count = result.scalar()
            print(
                f"{check_mark(table_count > 0)} Found {table_count} tables in database"
            )

        return True

    except Exception as e:
        print(f"{check_mark(False)} Database connection failed: {e}")
        return False


def validate_project_structure():
    """Validate project structure."""
    print_header("4. Project Structure")

    required_dirs = [
        "app",
        "app/api",
        "app/core",
        "app/models",
        "app/schemas",
        "app/services",
        "app/repositories",
        "alembic",
        "tests",
        "scripts",
    ]

    checks = {}
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        checks[dir_path] = full_path.exists() and full_path.is_dir()

    for dir_path, exists in checks.items():
        print(f"{check_mark(exists)} {dir_path}/")

    return all(checks.values())


def validate_models_and_schemas():
    """Validate models and schemas can be imported."""
    print_header("5. Models and Schemas")

    modules_to_check = [
        ("Models - Auth", "app.models.auth"),
        ("Models - Academic", "app.models.academic"),
        ("Models - HR", "app.models.hr"),
        ("Models - Infrastructure", "app.models.infrastructure"),
        ("Models - Scheduling", "app.models.scheduling"),
        ("Schemas - Auth", "app.schemas.auth"),
        ("Schemas - Academic", "app.schemas.academic"),
        ("Schemas - HR", "app.schemas.hr"),
        ("Schemas - Infrastructure", "app.schemas.infrastructure"),
        ("Schemas - Scheduling", "app.schemas.scheduling"),
    ]

    checks = {}
    for name, module_path in modules_to_check:
        try:
            importlib.import_module(module_path)
            checks[name] = True
        except Exception as e:
            checks[name] = False
            print(f"{check_mark(False)} {name}: {e}")
            continue

        if checks[name]:
            print(f"{check_mark(True)} {name}")

    return all(checks.values())


def validate_api_endpoints():
    """Validate API endpoints can be imported."""
    print_header("6. API Endpoints")

    endpoints = ["auth", "academic", "hr", "infrastructure", "scheduling", "health"]

    checks = {}
    for endpoint in endpoints:
        try:
            module = importlib.import_module(f"app.api.v1.endpoints.{endpoint}")
            checks[endpoint] = hasattr(module, "router")
        except Exception as e:
            checks[endpoint] = False
            print(f"{check_mark(False)} {endpoint}: {e}")
            continue

        if checks[endpoint]:
            print(f"{check_mark(True)} {endpoint}")

    return all(checks.values())


def validate_migrations():
    """Validate Alembic migrations."""
    print_header("7. Database Migrations")

    try:
        # Check if alembic is configured
        alembic_ini = project_root / "alembic.ini"
        checks = {
            "alembic.ini exists": alembic_ini.exists(),
            "migrations directory": (project_root / "alembic" / "versions").exists(),
        }

        for check, passed in checks.items():
            print(f"{check_mark(passed)} {check}")

        # Try to get current revision
        if all(checks.values()):
            result = subprocess.run(
                ["alembic", "current"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"{check_mark(True)} Alembic is properly configured")
                if result.stdout.strip():
                    print(f"   Current revision: {result.stdout.strip()}")
                return True
            else:
                print(f"{check_mark(False)} Alembic configuration error")
                return False

        return False

    except Exception as e:
        print(f"{check_mark(False)} Migration check failed: {e}")
        return False


def validate_security():
    """Validate security configurations."""
    print_header("8. Security Configuration")

    try:
        from app.config import settings

        checks = {
            "SECRET_KEY configured": len(settings.SECRET_KEY) >= 32,
            "SECRET_KEY not default": settings.SECRET_KEY
            not in ["CHANGE-THIS-SECRET-KEY", "secret"],
            "CORS configured": bool(settings.BACKEND_CORS_ORIGINS),
            "JWT algorithm set": settings.ALGORITHM == "HS256",
        }

        for check, passed in checks.items():
            print(f"{check_mark(passed)} {check}")

        return all(checks.values())

    except Exception as e:
        print(f"{check_mark(False)} Security check failed: {e}")
        return False


def run_basic_import_test():
    """Test basic FastAPI app import."""
    print_header("9. FastAPI Application")

    try:
        from app.main import app

        print(f"{check_mark(True)} FastAPI app imports successfully")

        # Check if routes are included
        route_count = len(app.routes)
        print(f"{check_mark(route_count > 10)} Found {route_count} routes")

        return True

    except Exception as e:
        print(f"{check_mark(False)} FastAPI app import failed: {e}")
        return False


def generate_report(results: dict):
    """Generate final validation report."""
    print_header("Validation Report")

    total_checks = len(results)
    passed_checks = sum(results.values())
    percentage = (passed_checks / total_checks) * 100

    print(f"\nTotal checks: {total_checks}")
    print(f"Passed: {Colors.GREEN}{passed_checks}{Colors.ENDC}")
    print(f"Failed: {Colors.RED}{total_checks - passed_checks}{Colors.ENDC}")
    print(f"Score: {Colors.YELLOW}{percentage:.1f}%{Colors.ENDC}")

    if percentage == 100:
        print(
            f"\n{Colors.GREEN}🎉 All validations passed! Your Schedium Backend is ready.{Colors.ENDC}"
        )
    elif percentage >= 80:
        print(
            f"\n{Colors.YELLOW}⚠️  Most validations passed, but some issues need attention.{Colors.ENDC}"
        )
    else:
        print(
            f"\n{Colors.RED}❌ Several validations failed. Please fix the issues above.{Colors.ENDC}"
        )

    print("\n📋 Next steps:")
    if results.get("environment", False) and results.get("dependencies", False):
        print("1. Run migrations: alembic upgrade head")
        print("2. Create admin user: python scripts/create_admin_user.py")
        print("3. Start server: uvicorn app.main:app --reload")
    else:
        print("1. Fix the failed validations above")
        print("2. Re-run this validation script")


def main():
    """Run all validations."""
    print(f"{Colors.BLUE}Schedium Backend - Installation Validation{Colors.ENDC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.ENDC}")

    results = {
        "environment": validate_environment(),
        "dependencies": validate_dependencies(),
        "structure": validate_project_structure(),
        "database": validate_database_connection(),
        "models": validate_models_and_schemas(),
        "endpoints": validate_api_endpoints(),
        "migrations": validate_migrations(),
        "security": validate_security(),
        "fastapi": run_basic_import_test(),
    }

    generate_report(results)


if __name__ == "__main__":
    main()
