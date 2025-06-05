"""
Academic domain endpoints.
Temporary placeholder.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/placeholder")
async def placeholder():
    """Temporary endpoint."""
    return {"message": "Academic endpoints coming in Phase 6"}