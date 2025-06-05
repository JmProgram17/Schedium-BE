"""
Infrastructure endpoints.
Temporary placeholder.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/placeholder")
async def placeholder():
    """Temporary endpoint."""
    return {"message": "Infrastructure endpoints coming in Phase 6"}