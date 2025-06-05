# test_config.py - Crear en la raíz del proyecto para probar
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