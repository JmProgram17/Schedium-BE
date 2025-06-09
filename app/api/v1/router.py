"""
Main API router for version 1.
Aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import academic, auth, health, hr, infrastructure, scheduling

api_router = APIRouter()

# Include all routers
api_router.include_router(health.router, prefix="/health", tags=["health"])

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

api_router.include_router(academic.router, prefix="/academic", tags=["academic"])

api_router.include_router(hr.router, prefix="/hr", tags=["human-resources"])

api_router.include_router(
    infrastructure.router, prefix="/infrastructure", tags=["infrastructure"]
)

api_router.include_router(scheduling.router, prefix="/scheduling", tags=["scheduling"])
