#!/usr/bin/env python
"""
Development environment setup script.
Installs dependencies and configures pre-commit hooks.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_file_exists(filepath: str, content: str = None) -> bool:
    """Check if file exists, create if not and content provided."""
    path = Path(filepath)

    if not path.exists():
        print(f"⚠️  {filepath} not found.")
        if content:
            print(f"📝 Creating {filepath}...")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"✅ {filepath} created!")
            return True
        return False
    return True


def run_command(
    cmd: list[str], description: str, check_files: list[str] = None
) -> bool:
    """Run a command and return success status."""
    # Check required files first
    if check_files:
        for file in check_files:
            if not Path(file).exists():
                print(f"❌ Required file missing: {file}")
                return False

    print(f"\n🔧 {description}...")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ {description} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def create_config_files():
    """Create necessary configuration files if they don't exist."""
    configs = {
        ".pre-commit-config.yaml": """repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile=black']

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
""",
        "pyproject.toml": """[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
""",
        ".flake8": """[flake8]
max-line-length = 88
extend-ignore = E203, E266, E501, W503
max-complexity = 10
exclude = .git,__pycache__,venv,.venv,migrations,.tox,build,dist
""",
        "mypy.ini": """[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

[mypy-sqlalchemy.*]
ignore_missing_imports = True

[mypy-alembic.*]
ignore_missing_imports = True
""",
        ".env.example": """# Application
APP_NAME="Schedium API"
APP_VERSION="1.0.0"
APP_ENV="development"
DEBUG=True

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=schedium_database

# Security (IMPORTANT: Generate a secure key with: python scripts/generate_secret_key.py)
SECRET_KEY="CHANGE_THIS_IN_PRODUCTION_USE_GENERATOR_SCRIPT"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
""",
    }

    print("\n📋 Checking configuration files...")
    for filename, content in configs.items():
        check_file_exists(filename, content)


def main():
    """Set up development environment."""
    print("=" * 60)
    print("🚀 Schedium Backend - Development Setup")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required!")
        sys.exit(1)

    print(f"✅ Python {sys.version.split()[0]} detected")

    # Create configuration files if needed
    create_config_files()

    # Commands to run
    commands = [
        (["pip", "install", "--upgrade", "pip"], "Upgrading pip", None),
        (
            ["pip", "install", "-r", "requirements.txt"],
            "Installing dependencies",
            ["requirements.txt"],
        ),
        (
            ["pip", "install", "-r", "requirements-dev.txt"],
            "Installing dev dependencies",
            ["requirements-dev.txt"],
        ),
        (
            ["pre-commit", "install"],
            "Setting up pre-commit hooks",
            [".pre-commit-config.yaml"],
        ),
    ]

    # Run commands
    for cmd, desc, required_files in commands:
        if not run_command(cmd, desc, required_files):
            print("\n⚠️  Setup incomplete. Please fix errors and try again.")
            print("\n💡 Troubleshooting tips:")
            print("  - Make sure all required files exist")
            print("  - Check that you're in the project root directory")
            print("  - Ensure virtual environment is activated")
            sys.exit(1)

    # Try to run pre-commit on all files (optional, may fail on first run)
    print("\n🔍 Running initial code checks (this may take a while)...")
    try:
        subprocess.run(["pre-commit", "run", "--all-files"], check=False)
    except Exception:
        print("⚠️  Initial pre-commit run skipped (this is normal)")

    print("\n✅ Development environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Copy .env.example to .env and configure")
    print("2. Run migrations: alembic upgrade head")
    print("3. Start development: uvicorn app.main:app --reload")
    print("\n💡 Useful commands:")
    print("  - make format    # Format code")
    print("  - make lint      # Run linters")
    print("  - make test      # Run tests")
    print("  - make validate  # Run all checks")


if __name__ == "__main__":
    main()
