#!/usr/bin/env python
"""
Verify complete setup.
"""

import os
import platform
import sys
from pathlib import Path

project_root = Path(__file__).parent
if (project_root / "app").exists():
    sys.path.insert(0, str(project_root))
elif (project_root.parent / "app").exists():
    sys.path.insert(0, str(project_root.parent))


def main():
    print("=" * 60)
    print("Schedium Backend - Setup Verification")
    print("=" * 60)

    # System info
    print(f"\n📋 System Information:")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    print(f"Working Dir: {os.getcwd()}")
    print(f"Shell: {os.environ.get('SHELL', 'Unknown')}")

    # Check if running in Git Bash
    if "MINGW" in platform.system() or "MSYS" in os.environ.get("MSYSTEM", ""):
        print("\n⚠️  WARNING: Running in Git Bash detected!")
        print("   Git Bash can cause issues with paths starting with '/'")
        print("   Consider using PowerShell or CMD instead.")

    # Try importing settings
    print(f"\n📋 Checking Configuration:")
    try:
        from app.config import settings

        print(f"✅ Settings imported successfully")
        print(f"API_V1_STR: '{settings.API_V1_STR}'")
        print(f"Is valid path: {settings.API_V1_STR.startswith('/')}")

        # Test FastAPI creation
        print(f"\n📋 Testing FastAPI Creation:")
        from fastapi import FastAPI

        app = FastAPI(
            openapi_url=f"{settings.API_V1_STR}/openapi.json",
            docs_url=f"{settings.API_V1_STR}/docs",
            redoc_url=f"{settings.API_V1_STR}/redoc",
        )
        print("✅ FastAPI app created successfully")

        # Test server startup
        print(f"\n🚀 Ready to start server!")
        print(f"Run: python -m uvicorn app.main:app --reload")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
