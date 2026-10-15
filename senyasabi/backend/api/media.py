"""Media API endpoints for presigned URLs.

This uses Supabase Storage to generate presigned URLs for media files,
following the pattern from test_fetch.py.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from config import SUPABASE_URL, SUPABASE_KEY
from security import get_current_user_id

router = APIRouter(prefix="/api/v1/media", tags=["media"])

# Supabase Storage client
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    STORAGE_AVAILABLE = True
except Exception as e:
    print(f"Supabase Storage not available: {e}")
    STORAGE_AVAILABLE = False


@router.get("/presign/{media_id}")
async def get_presigned_url(
    media_id: int,
    auth_user_id: str = Depends(get_current_user_id)
):
    """
    Get a presigned URL for media file from Supabase Object Storage.
    
    This follows the pattern from test_fetch.py:
    - Generate presigned URL using Supabase Storage
    - Set expiration time (default 5 minutes)
    - Validate user has access (via JWT)
    
    Args:
        media_id: The media file ID
        auth_user_id: The authenticated user's UUID (from JWT)
        
    Returns:
        Presigned URL with expiration
        
    Raises:
        HTTPException: If media not found or storage unavailable
    """
    if not STORAGE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Storage is not configured"
        )
    
    # TODO: Query PostgreSQL to get object_key for this media_id
    # For now, return a placeholder
    # In production:
    # 1. Query media_files table to get object_key
    # 2. Use storage3 to generate presigned URL
    # 3. Return URL with expiration
    
    return {
        "media_id": media_id,
        "url": None,
        "expires_in": 300,
        "message": "Presigned URL generation - needs PostgreSQL query to get object_key"
    }


@router.get("/info/{media_id}")
async def get_media_info(media_id: int):
    """
    Get media file information from PostgreSQL.
    
    Args:
        media_id: The media file ID
        
    Returns:
        Media file metadata
    """
    # TODO: Implement media info retrieval from PostgreSQL
    return {
        "media_id": media_id,
        "message": "Media info endpoint - to be implemented"
    }
