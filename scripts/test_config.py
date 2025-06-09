# test_config.py - Crear en la raíz del proyecto para probar
import sys
from pathlib import Path

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))

from app.config import settings


def test_database_url():
    """Test database URL construction."""
    assert settings.DATABASE_URL.startswith("mysql+pymysql://")
    assert settings.DB_NAME in settings.DATABASE_URL


def test_environment_checks():
    """Test environment detection."""
    assert settings.IS_DEVELOPMENT or settings.IS_PRODUCTION or settings.IS_TESTING


if __name__ == "__main__":
    test_database_url()
    test_environment_checks()
    print("✅ Configuration tests passed!")
