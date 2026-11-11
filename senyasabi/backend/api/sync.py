"""Sync API endpoints for progress synchronization.

This provides endpoints for:
- Uploading client progress and attempts
- Server ID mapping for new records
- Batch processing with idempotency
- Smart merge logic with conflict resolution

NOTE: Lesson reordering requires a temporary order value to swap two lessons,
because the partial unique index on (parent_module, lesson_order) is not deferrable.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy import text
from datetime import date, datetime, timedelta, timezone
from fastapi.encoders import jsonable_encoder

from ..database.postgre_session import get_postgres_session
from ..security import get_current_user_id

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


class SyncItem(BaseModel):
    """Single sync item."""
    entity_type: str  # quiz_attempt, minigame_attempt, lesson_progress
    client_id: str  # Client-generated UUID (for attempts) or server ID (for progress)
    data: Dict[str, Any]
    operation: str  # upsert, delete


class SyncRequest(BaseModel):
    """Sync upload request."""
    user_id: str  # UUID string from JWT
    sync_items: List[SyncItem]

class SyncResponse(BaseModel):
    processed: int
    succeeded: int
    failed: int
    mappings: Dict[str, Dict[str, str]]
    streak: Optional[Dict[str, Any]] = None          # authoritative

QUALIFYING = ("quiz_attempt", "minigame_attempt", "lesson_progress")

def _valid(item) -> bool:
    """Reject impossible timestamps; a small clock skew is tolerated."""
    raw = item.data.get("completed_at")
    if not raw:
        return item.entity_type == "lesson_progress" and item.data.get("status") != "Completed"
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return False
    return ts <= datetime.now(timezone.utc) + timedelta(days=1)

@router.post("/upload")
async def upload_sync(request: SyncRequest, user_id: str = Depends(get_current_user_id)):
    """
    Upload client progress and attempts for synchronization.
    
    Accepts batch of progress/attempts and stores in PostgreSQL.
    Returns server-assigned IDs for new records.
    
    Implements smart merge logic:
    - lesson_progress: ON CONFLICT ... WHERE EXCLUDED.client_updated_at > ...
    - Takes GREATEST() of time and percentage
    - Never regresses Completed status
    - Recomputes passed server-side from percentage and quizzes.passing_score
    
    Args:
        request: Sync request with user_id (UUID) and sync_items
        
    Returns:
        Sync response with processing results and ID mappings
    """
    try:
        with get_postgres_session() as db:
            processed = 0
            succeeded = 0
            failed = 0
            mappings = {}
            activity, tz_name = False, None
            
            for item in request.sync_items:
                processed += 1
                try:
                    handler = {"quiz_attempt": upsert_quiz_attempt,
                               "minigame_attempt": upsert_minigame_attempt,
                               "lesson_progress": upsert_lesson_progress,
                               "user": upsert_user}.get(item.entity_type)
                    with db.begin_nested():       # savepoint: one bad item can't abort the batch
                        success = bool(handler and handler(db, user_id, item))
                    if success and item.entity_type in QUALIFYING and (
                            item.entity_type != "lesson_progress"
                            or item.data.get("status") == "Completed"):
                        activity = True
                        tz_name = tz_name or item.data.get("timezone")
                    succeeded += success
                    failed += not success
                except Exception as e:
                    failed += 1
                    print(f"Error processing sync item: {e}")

            streak = None
            if activity:      # steps 3-4: recalc, update streaks, trigger refreshes the cache
                row = db.execute(text("SELECT * FROM public.recalculate_streak(:u, :tz)"),
                                 {"u": user_id, "tz": tz_name}).mappings().first()
                streak = jsonable_encoder(dict(row)) if row else None


            db.execute(text("SELECT public.refresh_user_statistics(:u)"), {"u": user_id})
            db.commit()

            return SyncResponse(processed=processed, succeeded=succeeded, failed=failed,
                                mappings=mappings, streak=streak)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during sync upload: {str(e)}"
        )

def upsert_user(db, user_id: str, item: SyncItem) -> bool:
    """Upsert user metadata."""
    data = item.data
    display_name = data.get("display_name")
    notifications_enabled = data.get("notifications_enabled")
    dark_mode = data.get("dark_mode")
    
    result = db.execute(text("""
        INSERT INTO public.users (user_id, display_name, notifications_enabled, dark_mode, updated_at)
        VALUES (:user_id, :display_name, :notifications_enabled, :dark_mode, now())
        ON CONFLICT (user_id) DO UPDATE SET
            display_name = COALESCE(EXCLUDED.display_name, users.display_name),
            notifications_enabled = COALESCE(EXCLUDED.notifications_enabled, users.notifications_enabled),
            dark_mode = COALESCE(EXCLUDED.dark_mode, users.dark_mode),
            updated_at = now()
        RETURNING user_id
    """), {
        "user_id": user_id,
        "display_name": display_name,
        "notifications_enabled": notifications_enabled,
        "dark_mode": dark_mode
    })
    
    return result.rowcount > 0


def upsert_lesson_progress(db, user_id: str, item: SyncItem) -> bool:
    """
    Upsert lesson progress with smart merge logic.
    
    Uses ON CONFLICT with WHERE clause to only merge if client has newer data.
    Takes GREATEST() of time and percentage.
    Never regresses Completed status.
    Recomputes passed server-side from percentage and passing_score.
    """
    data = item.data
    lesson_id = data.get("lesson_id")
    completion_percentage = data.get("completion_percentage", 0)
    status = data.get("status", "In Progress")
    time_spent_seconds = data.get("time_spent_seconds", 0)
    client_updated_at = data.get("client_updated_at") or data.get("updated_at")
    
    # First, get the quiz passing score for this lesson's module
    quiz_passing_score = get_quiz_passing_score(db, lesson_id)
    
    # Recompute passed status
    passed = completion_percentage >= quiz_passing_score if quiz_passing_score else False
    
    if status == "Completed":
        passed = True  # Always pass if marked completed
    
    completed_at = data.get("completed_at") if status == "Completed" else None
    client_updated_at = client_updated_at or datetime.now(timezone.utc).isoformat()
    result = db.execute(text("""
        INSERT INTO public.lesson_progress AS lp (
            user_id, lesson_id, completion_percentage, status,
            completed_at, time_spent_seconds, client_updated_at, updated_at)
        VALUES (:user_id, :lesson_id, :completion_percentage, :status,
            CASE WHEN :status = 'Completed'
                 THEN COALESCE(CAST(:completed_at AS timestamptz), now()) END,
            :time_spent_seconds, CAST(:client_updated_at AS timestamptz), now())
        ON CONFLICT (user_id, lesson_id) DO UPDATE SET
            completion_percentage = GREATEST(lp.completion_percentage, EXCLUDED.completion_percentage),
            time_spent_seconds    = GREATEST(lp.time_spent_seconds, EXCLUDED.time_spent_seconds),
            status = CASE WHEN EXCLUDED.status = 'Completed' OR lp.status = 'Completed'
                          THEN 'Completed' ELSE EXCLUDED.status END,
            completed_at = LEAST(lp.completed_at, EXCLUDED.completed_at),   -- earliest wins, NULLs ignored
            client_updated_at = GREATEST(lp.client_updated_at, EXCLUDED.client_updated_at),
            updated_at = now()
        RETURNING user_id
    """), {
        "user_id": user_id,
        "lesson_id": lesson_id,
        "completion_percentage": completion_percentage,
        "status": status,
        "time_spent_seconds": time_spent_seconds,
        "completed_at": completed_at,
        "client_updated_at": client_updated_at,
    })
    
    return result.rowcount > 0


def upsert_quiz_attempt(db, user_id: str, item: SyncItem) -> bool:
    """Upsert quiz attempt with server-side validation."""
    data = item.data
    quiz_id = data.get("quiz_id")
    started_at = data.get("started_at")
    completed_at = data.get("completed_at")
    score = data.get("score", 0)
    max_score = data.get("max_score", 100)
    camera_accuracy = data.get("camera_accuracy")
    mc_accuracy = data.get("mc_accuracy")
    duration_seconds = data.get("duration_seconds")
    
    # Recompute percentage
    percentage = (score / max_score * 100) if max_score > 0 else 0
    
    # Recompute passed from percentage and quiz passing score
    quiz_passing_score = get_quiz_passing_score_for_quiz(db, quiz_id)
    passed = percentage >= quiz_passing_score if quiz_passing_score else False
    attempt_id = data.get("attempt_id") or item.client_id
    
    result = db.execute(text("""
        INSERT INTO public.quiz_attempts (
            attempt_id, user_id, quiz_id, started_at, completed_at,
            score, max_score, percentage, passed, duration_seconds
            camera_accuracy, mc_accuracy
        )
        VALUES (
            :id, :user_id, :quiz_id, :started_at, :completed_at,
            :score, :max_score, :percentage, :passed, ;duration_seconds
            :camera_accuracy, :mc_accuracy
        )
        ON CONFLICT (user_id, quiz_id, started_at) DO UPDATE SET
            completed_at = EXCLUDED.completed_at,
            score = EXCLUDED.score,
            max_score = EXCLUDED.max_score,
            percentage = EXCLUDED.percentage,
            passed = EXCLUDED.passed,
            duration_seconds = EXCLUDED.duration_seconds,
            camera_accuracy = EXCLUDED.camera_accuracy,
            mc_accuracy = EXCLUDED.mc_accuracy
        RETURNING attempt_id
    """), {
        "id": attempt_id,
        "user_id": user_id,
        "quiz_id": quiz_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "passed": passed,
        "duration_seconds": duration_seconds,
        "camera_accuracy": camera_accuracy,
        "mc_accuracy": mc_accuracy
    })
    
    return result.rowcount > 0


def upsert_minigame_attempt(db, user_id: str, item: SyncItem) -> bool:
    """Upsert minigame attempt."""
    data = item.data
    minigame_id = data.get("minigame_id")
    started_at = data.get("started_at")
    completed_at = data.get("completed_at")
    score = data.get("score", 0)
    duration_seconds = data.get("duration_seconds")
    accuracy = data.get("accuracy")
    attempt_id = data.get("game_attempt_id") or item.client_id

    result = db.execute(text("""
        INSERT INTO public.minigame_attempts AS ma (
            game_attempt_id, user_id, minigame_id, started_at, completed_at,
            score, duration_seconds, accuracy)
        VALUES (:id, :user_id, :minigame_id, :started_at, :completed_at,
                :score, :duration_seconds, :accuracy)
        ON CONFLICT (game_attempt_id) DO UPDATE SET
            completed_at = EXCLUDED.completed_at, score = EXCLUDED.score,
            duration_seconds = EXCLUDED.duration_seconds, accuracy = EXCLUDED.accuracy,
            synced_at = now()
        WHERE ma.user_id = EXCLUDED.user_id
        RETURNING game_attempt_id
    """), {"id": attempt_id, "user_id": user_id, "minigame_id": minigame_id,
           "started_at": started_at, "completed_at": completed_at, "score": score,
           "duration_seconds": duration_seconds, "accuracy": accuracy})
        
    return result.rowcount > 0


def get_quiz_passing_score(db, lesson_id: int) -> Optional[int]:
    """Get the passing score for the quiz associated with this lesson's module."""
    result = db.execute(text("""
        SELECT q.passing_score
        FROM quizzes q
        JOIN lessons l ON l.parent_module = q.module_id
        WHERE l.lesson_id = :lesson_id
    """), {"lesson_id": lesson_id})
    
    row = result.fetchone()
    return row[0] if row else None


def get_quiz_passing_score_for_quiz(db, quiz_id: int) -> Optional[int]:
    """Get the passing score for a specific quiz."""
    result = db.execute(text("""
        SELECT passing_score FROM quizzes WHERE quiz_id = :quiz_id
    """), {"quiz_id": quiz_id})
    
    row = result.fetchone()
    return row[0] if row else None


@router.get("/queue/{user_id}")
async def get_sync_queue(user_id: str):
    """
    Get pending sync queue items for a user.

    Returns recent quiz attempts, minigame attempts, and lesson progress
    that might need to be synced to the client.

    Args:
        user_id: The user ID (UUID)

    Returns:
        Pending sync items organized by entity type
    """
    try:
        with get_postgres_session() as db:
            # Get recent quiz attempts
            quiz_attempts = db.execute(text("""
                SELECT qa.attempt_id::text, qa.quiz_id, qa.started_at, qa.completed_at,
                       qa.score, qa.max_score, qa.percentage, qa.passed
                FROM quiz_attempts qa
                WHERE qa.user_id = :user_id
                ORDER BY qa.started_at DESC
                LIMIT 50
            """), {"user_id": user_id}).mappings().all()

            # Get recent minigame attempts
            minigame_attempts = db.execute(text("""
                SELECT ma.game_attempt_id::text, ma.minigame_id, ma.started_at, ma.completed_at,
                       ma.score, ma.duration_seconds, ma.accuracy
                FROM minigame_attempts ma
                WHERE ma.user_id = :user_id
                ORDER BY ma.started_at DESC
                LIMIT 50
            """), {"user_id": user_id}).mappings().all()

            # Get lesson progress
            lesson_progress = db.execute(text("""
                SELECT lp.lesson_id, lp.completion_percentage, lp.status,
                       lp.completed_at, lp.time_spent_seconds, lp.updated_at
                FROM lesson_progress lp
                WHERE lp.user_id = :user_id
                ORDER BY lp.updated_at DESC
                LIMIT 50
            """), {"user_id": user_id}).mappings().all()

            return {
                "user_id": user_id,
                "quiz_attempts": [dict(r) for r in quiz_attempts],
                "minigame_attempts": [dict(r) for r in minigame_attempts],
                "lesson_progress": [dict(r) for r in lesson_progress]
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching sync queue: {str(e)}"
        )


@router.post("/reorder-lessons")
async def reorder_lessons(
    module_id: int,
    lesson_id_1: int,
    lesson_id_2: int,
    user_id: str = Depends(get_current_user_id)
):
    """
    Reorder two lessons within a module.
    
    Because the partial unique index (parent_module, lesson_order) is not deferrable,
    we use a temporary order value (e.g., -1) to avoid conflicts during the swap.
    
    Args:
        module_id: The module ID
        lesson_id_1: First lesson to swap
        lesson_id_2: Second lesson to swap
        user_id: The user ID (UUID) from JWT
        
    Returns:
        Success/failure status
    """
    try:
        with get_postgres_session() as db:
            # Get current lesson orders
            result = db.execute(text("""
                SELECT lesson_id, lesson_order FROM lessons
                WHERE lesson_id IN (:lesson_id_1, :lesson_id_2)
            """), {"lesson_id_1": lesson_id_1, "lesson_id_2": lesson_id_2})
            
            lessons = {row[0]: row[1] for row in result}
            
            if len(lessons) != 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Both lessons must exist in the same module"
                )
            
            order_1 = lessons[lesson_id_1]
            order_2 = lessons[lesson_id_2]
            
            # Swap orders using temporary value to avoid unique index conflict
            db.execute(text("""
                UPDATE lessons SET lesson_order = -1 WHERE lesson_id = :lesson_id_1
            """), {"lesson_id_1": lesson_id_1})
            
            db.execute(text("""
                UPDATE lessons SET lesson_order = :order_1 WHERE lesson_id = :lesson_id_2
            """), {"order_1": order_1, "lesson_id_2": lesson_id_2})
            
            db.execute(text("""
                UPDATE lessons SET lesson_order = :order_2 WHERE lesson_id = :lesson_id_1
            """), {"order_2": order_2, "lesson_id_1": lesson_id_1})
            
            return {
                "success": True,
                "message": "Lessons reordered successfully"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reordering lessons: {str(e)}"
        )