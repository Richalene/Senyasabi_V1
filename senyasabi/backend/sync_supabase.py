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
    Fetch delta for a specific table with proper version filtering.
    
    Uses raw SQL query to join with content_versions and filter by version range.
    
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
        # Use raw SQL query to properly join with content_versions
        # Supabase Python client supports RPC for custom SQL
        # For now, we'll fetch the content_version first, then filter
        
        # Get content_version_id for the current version
        cv_response = supabase.table('content_versions') \
            .select('content_version_id') \
            .eq('version_number', current_version) \
            .eq('is_published', True) \
            .eq('is_deleted', False) \
            .execute()
        
        if not cv_response.data:
            logger.warning(f"No content version found for {current_version}")
            return {"upsert": [], "delete": []}
        
        cv_id = cv_response.data[0]['content_version_id']
        
        # Fetch all rows for this content_version
        response = supabase.table(table) \
            .select('*') \
            .eq('content_version_id', cv_id) \
            .execute()
        
        upsert = []
        delete = []
        
        for row in response.data:
            # Add content_version_number to the row for apply_content_delta
            row['content_version_number'] = current_version
            
            if row.get('is_deleted', False):
                # For deletes, we need the primary key columns
                delete.append(row)
            else:
                # Exclude specified columns
                if exclude_columns:
                    row_filtered = {k: v for k, v in row.items() if k not in exclude_columns}
                    # Still include content_version_number
                    row_filtered['content_version_number'] = current_version
                    upsert.append(row_filtered)
                else:
                    upsert.append(row)
        
        return {"upsert": upsert, "delete": delete}
        
    except Exception as e:
        logger.warning(f"Failed to fetch delta for {table}: {e}")
        return {"upsert": [], "delete": []}


def _fetch_badges(supabase) -> Dict:
    """Fetch all badges with the same structure as table deltas."""
    try:
        response = supabase.table('badges').select('*').eq('is_deleted', False).execute()
        # Return in the same format as _fetch_table_delta
        return {"upsert": response.data, "delete": []}
    except Exception as e:
        logger.warning(f"Failed to fetch badges: {e}")
        return {"upsert": [], "delete": []}


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
        status = data.get("status", "In Progress")
        time_spent_seconds = data.get("time_spent_seconds", 0)
        client_updated_at = data.get("client_updated_at")
        completed_at = data.get("completed_at")
        
        # Build upsert data
        upsert_data = {
            "user_id": user_id,
            "lesson_id": lesson_id,
            "completion_percentage": completion_percentage,
            "status": status,
            "time_spent_seconds": time_spent_seconds,
            "client_updated_at": client_updated_at
        }
        
        # Only include completed_at if status is "Completed"
        if status == "Completed" and completed_at:
            upsert_data["completed_at"] = completed_at
        
        response = supabase.table('lesson_progress').upsert(upsert_data).execute()
        
        return len(response.data) > 0
        
    except Exception as e:
        logger.warning(f"Failed to upsert lesson progress: {e}")
        return False


def _upsert_quiz_attempt(supabase, user_id: str, data: Dict) -> bool:
    """Upsert quiz attempt to Supabase."""
    try:
        attempt_id = data.get("attempt_id")  # Client-generated UUID (primary key)
        quiz_id = data.get("quiz_id")
        started_at = data.get("started_at")
        completed_at = data.get("completed_at")
        score = data.get("score", 0)
        max_score = data.get("max_score", 100)
        
        if not attempt_id:
            logger.warning("Quiz attempt missing attempt_id (primary key)")
            return False
        
        response = supabase.table('quiz_attempts').upsert({
            "attempt_id": attempt_id,
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
        game_attempt_id = data.get("game_attempt_id")  # Client-generated UUID (primary key)
        minigame_id = data.get("minigame_id")
        started_at = data.get("started_at")
        completed_at = data.get("completed_at")
        score = data.get("score", 0)
        duration_seconds = data.get("duration_seconds")
        accuracy = data.get("accuracy")
        
        if not game_attempt_id:
            logger.warning("Minigame attempt missing game_attempt_id (primary key)")
            return False
        
        response = supabase.table('minigame_attempts').upsert({
            "game_attempt_id": game_attempt_id,
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
