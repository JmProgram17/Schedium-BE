"""
Configuration module for Schedium API.
Handles all environment variables and application settings.
"""

import locale
import os
import platform
import secrets
import sys
from typing import Any, List, Optional, TextIO, Union

from pydantic import ConfigDict, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure UTF-8 output for Windows
if platform.system() == "Windows":
    # Set console encoding to UTF-8
    if sys.stdout.encoding != "utf-8" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8" and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Schedium API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Schedium - Sistema de Programación Académica"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Redis for rate limiting
    REDIS_URL: str = "redis://localhost:6379/0"

    # Request limits
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024   # 50MB

    # Session security
    SESSION_SECRET_KEY: str = secrets.token_urlsafe(32)
    SESSION_EXPIRE_MINUTES: int = 60

    # CSRF protection
    CSRF_SECRET_KEY: str = secrets.token_urlsafe(32)
    CSRF_TOKEN_EXPIRE_MINUTES: int = 60

    # Password policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # API Key settings (if using)
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY_SALT: str = secrets.token_urlsafe(32)

    # Security headers
    HSTS_MAX_AGE: int = 31536000  # 1 year

    # Allowed file extensions for uploads
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        "jpg", "jpeg", "png", "gif", "pdf",
        "doc", "docx", "xls", "xlsx", "csv"
    ]

    # IP whitelist/blacklist (optional)
    IP_WHITELIST: List[str] = []
    IP_BLACKLIST: List[str] = []

    # Database
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = []

    @field_validator("API_V1_STR", mode="before")
    @classmethod
    def fix_api_path(cls, v: str) -> str:
        """Fix API path for Windows Git Bash issue."""
        if isinstance(v, str):
            # Si Git Bash convirtió la ruta, arreglarla
            if v.startswith("C:/") or v.startswith("/c/") or "Program Files/Git" in v:
                return "/api/v1"
            # Asegurar que empiece con /
            if not v.startswith("/"):
                return f"/{v}"
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str):
            # Si es una cadena, dividir por comas
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            # Si ya es una lista, devolverla
            return v
        # Si es cualquier otra cosa, devolver lista vacía
        return []

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def IS_DEVELOPMENT(self) -> bool:
        """Check if running in development mode."""
        return self.APP_ENV == "development"

    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production mode."""
        return self.APP_ENV == "production"

    @property
    def IS_TESTING(self) -> bool:
        """Check if running in testing mode."""
        return self.APP_ENV == "testing"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Importante: NO parsear campos complejos como JSON automáticamente
        json_encoders={list: lambda v: v},
    )


# Create global settings instance
settings = Settings()


# Validate critical settings at startup
def validate_settings() -> None:
    """Validate critical settings at application startup."""
    errors = []
    warnings = []

    # Check database settings
    if not all([settings.DB_HOST, settings.DB_USER, settings.DB_NAME]):
        errors.append("Database configuration incomplete")

    # Check security settings - solo error en producción
    insecure_keys = [
        "your-super-secret-key-change-this-in-production",
        "CHANGE-THIS-SECRET-KEY",
        "secret",
        "password",
        "12345678",
    ]

    if settings.SECRET_KEY in insecure_keys:
        if settings.IS_PRODUCTION:
            errors.append("SECRET_KEY must be changed from default value in production")
        else:
            warnings.append(
                "⚠️  WARNING: Using insecure SECRET_KEY - change before production!"
            )

    # Check CORS in production
    if settings.IS_PRODUCTION and not settings.BACKEND_CORS_ORIGINS:
        errors.append("CORS origins must be configured for production")

    # Verificar que API_V1_STR es correcto
    if not settings.API_V1_STR.startswith("/"):
        errors.append(f"API_V1_STR must start with '/', got: {settings.API_V1_STR}")

    # Print warnings
    for warning in warnings:
        print(warning)

    # Only raise if there are errors
    if errors:
        error_msg = "Configuration errors:\n" + "\n".join(f"- {e}" for e in errors)
        raise ValueError(error_msg)


# Run validation when module is imported
if settings.APP_ENV != "testing":
    validate_settings()

# Log environment info for debugging
if settings.DEBUG:
    print(f"🖥️  System: {platform.system()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🔧 API Path: {settings.API_V1_STR}")
