#!/usr/bin/env python
"""
Debug configuration issues.
Helps identify problems with environment variables and settings.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))


def debug_env_file():
    """Debug .env file parsing."""
    print("🔍 Debugging .env file...")
    env_path = project_root.parent / ".env"

    if not env_path.exists():
        print("❌ .env file not found!")
        return False

    print(f"✅ .env file found at: {env_path}")

    # Read and display problematic lines
    print("\n📋 Checking .env contents:")
    with open(env_path, "r") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Check for problematic values
                    if key == "BACKEND_CORS_ORIGINS":
                        print(f"Line {i}: {key} = {value[:50]}...")
                        if "[" in value or "]" in value:
                            print(
                                "  ⚠️  WARNING: Contains brackets - should be comma-separated!"
                            )
                        if '"' in value and value.count('"') > 2:
                            print(
                                "  ⚠️  WARNING: Too many quotes - remove internal quotes!"
                            )

    return True


def debug_settings():
    """Debug settings module."""
    print("\n🔍 Debugging settings module...")

    try:
        from app.config import settings

        print("✅ Settings imported successfully")

        # Check specific settings
        print(f"\n📋 Key settings:")
        print(f"API_V1_STR: {settings.API_V1_STR}")
        print(f"IS_PRODUCTION: {settings.IS_PRODUCTION}")
        print(f"DEBUG: {settings.DEBUG}")

        # Check CORS origins
        print(f"\n📋 CORS Origins:")
        print(f"Type: {type(settings.BACKEND_CORS_ORIGINS)}")
        print(f"Value: {settings.BACKEND_CORS_ORIGINS}")

        if isinstance(settings.BACKEND_CORS_ORIGINS, list):
            print(f"Count: {len(settings.BACKEND_CORS_ORIGINS)}")
            for i, origin in enumerate(settings.BACKEND_CORS_ORIGINS):
                print(f"  [{i}]: {origin}")

        # Check computed URLs
        print(f"\n📋 Computed URLs:")
        openapi_url = f"{settings.API_V1_STR}/openapi.json"
        docs_url = f"{settings.API_V1_STR}/docs"
        redoc_url = f"{settings.API_V1_STR}/redoc"

        print(f"OpenAPI URL: {openapi_url}")
        print(f"Docs URL: {docs_url}")
        print(f"ReDoc URL: {redoc_url}")

        # Verify they start with /
        for url_name, url in [
            ("OpenAPI", openapi_url),
            ("Docs", docs_url),
            ("ReDoc", redoc_url),
        ]:
            if not url.startswith("/"):
                print(f"  ❌ ERROR: {url_name} URL doesn't start with '/'")
            else:
                print(f"  ✅ {url_name} URL is correct")

        return True

    except Exception as e:
        print(f"❌ Error importing settings: {e}")
        import traceback

        traceback.print_exc()
        return False


def debug_fastapi():
    """Debug FastAPI application creation."""
    print("\n🔍 Debugging FastAPI application...")

    try:
        # Test creating FastAPI with explicit values
        from fastapi import FastAPI

        test_app = FastAPI(
            openapi_url="/api/v1/openapi.json",
            docs_url="/api/v1/docs",
            redoc_url="/api/v1/redoc",
        )
        print("✅ FastAPI creation with hardcoded values works")

        # Now test with settings
        from app.config import settings

        openapi_url = f"{settings.API_V1_STR}/openapi.json"
        print(f"\n📋 Testing dynamic URL creation:")
        print(f"settings.API_V1_STR = '{settings.API_V1_STR}'")
        print(f"openapi_url = '{openapi_url}'")
        print(f"URL starts with '/': {openapi_url.startswith('/')}")

        test_app2 = FastAPI(
            openapi_url=openapi_url if not settings.IS_PRODUCTION else None
        )
        print("✅ FastAPI creation with settings works")

        return True

    except Exception as e:
        print(f"❌ Error creating FastAPI: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all debug checks."""
    print("=" * 60)
    print("Schedium Backend - Configuration Debug")
    print("=" * 60)

    # Check environment
    print(f"\n📁 Working directory: {os.getcwd()}")
    print(f"📁 Project root: {project_root}")

    # Run checks
    env_ok = debug_env_file()
    settings_ok = debug_settings()
    fastapi_ok = debug_fastapi()

    print("\n" + "=" * 60)
    if all([env_ok, settings_ok, fastapi_ok]):
        print("✅ All debug checks passed!")

        print("\n🚀 Try running the server with:")
        print("uvicorn app.main:app --reload")
    else:
        print("❌ Some checks failed. Fix the issues above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
