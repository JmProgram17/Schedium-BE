"""
Services package.
Provides business logic layer for all domains.
"""

# Auth services
from app.services.auth import AuthService

# Academic services
from app.services.academic import AcademicService

# HR services
from app.services.hr import HRService

# Infrastructure services
from app.services.infrastructure import InfrastructureService

# Scheduling services
from app.services.scheduling import SchedulingService

__all__ = [
    "AuthService",
    "AcademicService", 
    "HRService",
    "InfrastructureService",
    "SchedulingService"
]