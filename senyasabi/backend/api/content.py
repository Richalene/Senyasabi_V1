"""Content sync API endpoints.

This provides content synchronization endpoints for:
- Fetching content delta (new/updated/deleted items)
- Version checking for conflict resolution
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime
from sqlalchemy import text

from ..database.postgre_session import get_postgres_session
from ..security import get_current_user_id

router = APIRouter(prefix="/api/v1/content", tags=["content"])


@router.get("/sync")
async def sync_content(since_version: int = 0):
    """
    Get content delta for synchronization.
    
    Args:
        since_version: Only return changes since this version
        
    Returns:
        Content delta with new/updated/deleted items
    """
    try:
        with get_postgres_session() as db:
            # Get current content version
            result = db.execute(text(
                "SELECT version_number " \
                "FROM content_versions " \
                "WHERE is_published = true " \
                "ORDER BY version_number DESC" \
                "LIMIT 1"
            ))
            current_version_row = result.fetchone()
            
            if not current_version_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No published content version found"
                )
            
            current_version = current_version_row[0]
            
            # TODO: Implement delta generation
            # For now, return empty delta
            return {
                "version": current_version,
                "since_version": since_version,
                "modules": {"upsert": [], "delete": []},
                "lessons": {"upsert": [], "delete": []},
                "signs": {"upsert": [], "delete": []},
                "media_files": {"upsert": [], "delete": []},
                "message": "Content sync endpoint - delta generation to be implemented"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching content sync: {str(e)}"
        )


@router.get("/version")
async def get_current_version():
    """
    Get the current published content version.
    
    Returns:
        Current content version information
    """
    try:
        with get_postgres_session() as db:
            result = db.execute(text(
                "SELECT version_number, content_version_id " \
                "FROM content_versions " \
                "WHERE is_published = true " \
                "ORDER BY version_number DESC" \
                "LIMIT 1"
            ))
            version_row = result.fetchone()
            
            if not version_row:
                return {
                    "version": None,
                    "message": "No published content version found"
                }
            
            return {
                "version": version_row[0],
                "released_at": version_row[1].isoformat() if version_row[1] else None,
                "changelog": version_row[2]
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching content version: {str(e)}"
        )

@router.get("/version/modules")
async def get_changed_modules():
    """
    Get the current published content version.
    
    Returns:
        Current content version information
    """