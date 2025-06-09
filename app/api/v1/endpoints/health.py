"""
Health check endpoints.
Provides system status information.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import settings
from app.core.responses import SuccessResponse

router = APIRouter()


@router.get("/", response_model=SuccessResponse[Dict[str, Any]])
async def health_check(db: Session = Depends(get_db)):
    """
    Check system health status.

    Returns system status including:
    - Application info
    - Database connectivity
    - System resources
    """
    health_data = {
        "status": "healthy",
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        },
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_data["database"] = {"status": "connected", "type": "MySQL"}
    except Exception as e:
        health_data["status"] = "degraded"
        health_data["database"] = {
            "status": "disconnected",
            "error": str(e) if settings.DEBUG else "Connection failed",
        }

    return SuccessResponse(data=health_data, message="System health check completed")


@router.get("/ready", response_model=SuccessResponse[Dict[str, bool]])
async def readiness_check(db: Session = Depends(get_db)):
    """
    Check if the system is ready to handle requests.

    Used for Kubernetes readiness probes.
    """
    checks = {
        "database": False,
        "cache": True,  # Placeholder for future Redis check
        "external_services": True,  # Placeholder
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except:
        pass

    all_ready = all(checks.values())

    return SuccessResponse(
        data={"ready": all_ready, "checks": checks}, message="Readiness check completed"
    )


@router.get("/live", response_model=SuccessResponse[Dict[str, bool]])
async def liveness_check():
    """
    Check if the application is alive.

    Used for Kubernetes liveness probes.
    """
    return SuccessResponse(data={"alive": True}, message="Application is alive")
