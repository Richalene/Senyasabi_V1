"""Supabase sync operations for distributed mode.

This module provides sync operations using the Supabase client directly,
bypassing the FastAPI proxy when in distributed mode.
"""
import json
import logging
from typing import Dict, Any, Optional

from .supabase_client import get_supabase_client
from .config import CLIENT_MODE

logger = logging.getLogger(__name__)


def sync_content(since_version: int = 0) -> Optional[Dict]:
    """
    Fetch content delta from Supabase.
    
    Args:
        since_version: Only fetch changes since this version
        
    Returns:
        Content delta dict or None on failure
    """
    if CLIENT_MODE == "fastapi":
        return None  # Use FastAPI in fastapi mode
    
    try:
        supabase = get_supabase_client()
        
        # Get current version
        version_response = supabase.table('content_versions') \
            .select('content_version_id, version_number, released_at, changelog') \
            .eq('is_published', True) \
            .eq('is_deleted', False) \
            .order('version_number', desc=True) \
            .limit(1) \
            .execute()
        
        if not version_response.data:
            return None
        
        current = version_response.data[0]
        current_version = current['version_number']
        
        if since_version >= current_version:
            # No changes
            return {
                "version": current_version,
                "since_version": since_version,
                "modules": {"upsert": [], "delete": []},
                "lessons": {"upsert": [], "delete": []},
                "signs": {"upsert": [], "delete": []},
                "media_files": {"upsert": [], "delete": []},
                "lesson_signs": {"upsert": [], "delete": []},
                "sign_media": {"upsert": [], "delete": []},
                "lesson_media": {"upsert": [], "delete": []},
                "quizzes": {"upsert": [], "delete": []},
                "quiz_signs": {"upsert": [], "delete": []},
                "minigames": {"upsert": [], "delete": []},
                "minigame_signs": {"upsert": [], "delete": []},
                "badges": []
            }
        
        # Fetch changed data for each table
        delta = {
            "version": current_version,
            "since_version": since_version,
            "modules": _fetch_table_delta(supabase, 'modules', since_version, current_version),
            "lessons": _fetch_table_delta(supabase, 'lessons', since_version, current_version),
            "signs": _fetch_table_delta(supabase, 'signs', since_version, current_version),
            "media_files": _fetch_table_delta(supabase, 'media_files', since_version, current_version, 
                                          exclude_columns=['object_key']),
            "lesson_signs": _fetch_table_delta(supabase, 'lesson_signs', since_version, current_version),
            "sign_media": _fetch_table_delta(supabase, 'sign_media', since_version, current_version),
            "lesson_media": _fetch_table_delta(supabase, 'lesson_media', since_version, current_version),
            "quizzes": _fetch_table_delta(supabase, 'quizzes', since_version, current_version),
            "quiz_signs": _fetch_table_delta(supabase, 'quiz_signs', since_version, current_version),
            "minigames": _fetch_table_delta(supabase, 'minigames', since_version, current_version),
            "minigame_signs": _fetch_table_delta(supabase, 'minigame_signs', since_version, current_version),
            "badges": _fetch_badges(supabase)
        }
        
        return delta
        
    except Exception as e:
        logger.exception("Failed to sync content from Supabase")
        return None


def _fetch_table_delta(supabase, table: str, since_version: int, current_version: int, 
                      exclude_columns: list = None) -> Dict:
    """
    Fetch delta for a specific table.
    
    Args:
        supabase: Supabase client
        table: Table name
        since_version: Starting version
        current_version: Current version
        exclude_columns: Columns to exclude from response
        
    Returns:
        Dict with 'upsert' and 'delete' lists
    """
    try:
        # Join with content_versions to filter by version range
        # This is a simplified version - the actual query would need proper joins
        # For now, we'll fetch all and filter client-side
        
        response = supabase.table(table).select('*').execute()
        
        upsert = []
        delete = []
        
        for row in response.data:
            # Check version number (would need proper join in production)
            # For now, skip version filtering
            if row.get('is_deleted', False):
                delete.append(row)
            else:
                # Exclude specified columns
                if exclude_columns:
                    row_filtered = {k: v for k, v in row.items() if k not in exclude_columns}
                    upsert.append(row_filtered)
                else:
                    upsert.append(row)
        
        return {"upsert": upsert, "delete": delete}
        
    except Exception as e:
        logger.warning(f"Failed to fetch delta for {table}: {e}")
        return {"upsert": [], "delete": []}


def _fetch_badges(supabase) -> list:
    """Fetch all badges."""
    try:
        response = supabase.table('badges').select('*').eq('is_deleted', False).execute()
        return response.data
    except Exception as e:
        logger.warning(f"Failed to fetch badges: {e}")
        return []


def upload_sync(user_id: str, sync_items: list) -> Optional[Dict]:
    """
    Upload sync items to Supabase.
    
    Args:
        user_id: User ID
        sync_items: List of sync items
        
    Returns:
        Sync response dict or None on failure
    """
    if CLIENT_MODE == "fastapi":
        return None  # Use FastAPI in fastapi mode
    
    try:
        supabase = get_supabase_client()
        
        processed = 0
        succeeded = 0
        failed = 0
        
        for item in sync_items:
            processed += 1
            try:
                entity_type = item.get("entity_type")
                data = item.get("data", {})
                
                if entity_type == "lesson_progress":
                    if _upsert_lesson_progress(supabase, user_id, data):
                        succeeded += 1
                    else:
                        failed += 1
                elif entity_type == "quiz_attempt":
                    if _upsert_quiz_attempt(supabase, user_id, data):
                        succeeded += 1
                    else:
                        failed += 1
                elif entity_type == "minigame_attempt":
                    if _upsert_minigame_attempt(supabase, user_id, data):
                        succeeded += 1
                    else:
                        failed += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.warning(f"Error processing sync item: {e}")
                failed += 1
        
        return {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "mappings": {}
        }
        
    except Exception as e:
        logger.exception("Failed to upload sync to Supabase")
        return None


def _upsert_lesson_progress(supabase, user_id: str, data: Dict) -> bool:
    """Upsert lesson progress to Supabase."""
    try:
        lesson_id = data.get("lesson_id")
        completion_percentage = data.get("completion_percentage", 0)
        status = data.get("status", "in_progress")
        time_spent_seconds = data.get("time_spent_seconds", 0)
        client_updated_at = data.get("client_updated_at")
        
        # This is a simplified version - would need proper conflict resolution
        # For now, just upsert
        response = supabase.table('lesson_progress').upsert({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "completion_percentage": completion_percentage,
            "status": status,
            "time_spent_seconds": time_spent_seconds,
            "client_updated_at": client_updated_at
        }).execute()
        
        return len(response.data) > 0
        
    except Exception as e:
        logger.warning(f"Failed to upsert lesson progress: {e}")
        return False


def _upsert_quiz_attempt(supabase, user_id: str, data: Dict) -> bool:
    """Upsert quiz attempt to Supabase."""
    try:
        quiz_id = data.get("quiz_id")
        started_at = data.get("started_at")
        completed_at = data.get("completed_at")
        score = data.get("score", 0)
        max_score = data.get("max_score", 100)
        
        response = supabase.table('quiz_attempts').upsert({
            "user_id": user_id,
            "quiz_id": quiz_id,
            "started_at": started_at,
            "completed_at": completed_at,
            "score": score,
            "max_score": max_score
        }).execute()
        
        return len(response.data) > 0
        
    except Exception as e:
        logger.warning(f"Failed to upsert quiz attempt: {e}")
        return False


def _upsert_minigame_attempt(supabase, user_id: str, data: Dict) -> bool:
    """Upsert minigame attempt to Supabase."""
    try:
        minigame_id = data.get("minigame_id")
        started_at = data.get("started_at")
        completed_at = data.get("completed_at")
        score = data.get("score", 0)
        duration_seconds = data.get("duration_seconds")
        accuracy = data.get("accuracy")
        
        response = supabase.table('minigame_attempts').upsert({
            "user_id": user_id,
            "minigame_id": minigame_id,
            "started_at": started_at,
            "completed_at": completed_at,
            "score": score,
            "duration_seconds": duration_seconds,
            "accuracy": accuracy
        }).execute()
        
        return len(response.data) > 0
        
    except Exception as e:
        logger.warning(f"Failed to upsert minigame attempt: {e}")
        return False
