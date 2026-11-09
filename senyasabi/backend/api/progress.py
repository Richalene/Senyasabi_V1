"""Progress API endpoints for user statistics and leaderboard.

This provides endpoints for:
- User progress retrieval
- User statistics
- Leaderboard (all_time, weekly, monthly)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from ..database.postgre_session import get_postgres_session
from ..security import get_current_user_id
from .leaderboard import _LEADERBOARD_SQL, PERIODS

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


def _own(user_id_in_path: str, token_user_id: str) -> str:
    if user_id_in_path != token_user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your data")
    return token_user_id

_SNAPSHOT_QUERIES = {
    "lesson_progress": "SELECT user_id, lesson_id, completion_percentage, status, last_accessed, completed_at, "
                       "time_spent_seconds, client_updated_at, updated_at FROM public.lesson_progress WHERE user_id = :u",
    "quiz_attempts": "SELECT attempt_id, user_id, quiz_id, started_at, completed_at, score, max_score, percentage, "
                     "passed, duration_seconds, camera_accuracy, mc_accuracy FROM public.quiz_attempts WHERE user_id = :u",
    "minigame_attempts": "SELECT game_attempt_id, user_id, minigame_id, started_at, completed_at, score, "
                         "duration_seconds, accuracy FROM public.minigame_attempts WHERE user_id = :u",
    "user_badges": "SELECT user_id, badge_id, unlocked_at FROM public.user_badges WHERE user_id = :u",
    "streaks": "SELECT user_id, current_streak, longest_streak, last_activity_date, updated_at "
               "FROM public.streaks WHERE user_id = :u",
    # live view = same scoring rule the leaderboard uses, never a stale cache
    "user_statistics": "SELECT user_id, lessons_completed, quizzes_completed, minigames_completed, total_quiz_score, "
                       "total_minigame_score, average_accuracy, total_time_spent_seconds, now() AS updated_at "
                       "FROM public.v_user_statistics_live WHERE user_id = :u",
}

_LATEST_BADGE_SQL = """
SELECT b.badge_id, b.badge_code, b.badge_name, b.description, ub.unlocked_at
FROM public.user_badges ub
JOIN public.badges b ON b.badge_id = ub.badge_id AND NOT b.is_deleted
WHERE ub.user_id = :u
ORDER BY ub.unlocked_at DESC
LIMIT 1
"""

# Mirrors repository.get_current_module: most recent in-progress lesson first,
# otherwise the first module with an incomplete lesson.
_CURRENT_MODULE_SQL = """
SELECT module_id, module_code, title FROM (
    SELECT m.module_id, m.module_code, m.title, 0 AS pri,
           lp.last_accessed AS sort_key, m.module_order
    FROM public.lesson_progress lp
    JOIN public.lessons l ON l.lesson_id = lp.lesson_id
         AND NOT l.is_deleted AND l.is_active
    JOIN public.modules m ON m.module_id = l.parent_module
         AND NOT m.is_deleted AND m.is_active
    WHERE lp.user_id = :u AND lp.status = 'In Progress'
    UNION ALL
    SELECT m.module_id, m.module_code, m.title, 1, NULL, m.module_order
    FROM public.modules m
    WHERE NOT m.is_deleted AND m.is_active
      AND EXISTS (
        SELECT 1 FROM public.lessons l
        WHERE l.parent_module = m.module_id AND NOT l.is_deleted AND l.is_active
          AND NOT EXISTS (
            SELECT 1 FROM public.lesson_progress lp
            WHERE lp.lesson_id = l.lesson_id AND lp.user_id = :u
              AND lp.status = 'Completed'))
) t
ORDER BY pri, sort_key DESC NULLS LAST, module_order
LIMIT 1
"""

# Q = avg quiz percentage, R = avg camera accuracy (same as get_module_performance)
_RADAR_SQL = """
WITH stats AS (
    SELECT q.module_id,
           AVG(qa.percentage) AS q_avg,
           AVG(qa.camera_accuracy) AS r_avg
    FROM public.quiz_attempts qa
    JOIN public.quizzes q ON q.quiz_id = qa.quiz_id AND NOT q.is_deleted
    WHERE qa.user_id = :u AND qa.completed_at IS NOT NULL
    GROUP BY q.module_id
)
SELECT m.module_id, m.module_code, m.title,
       COALESCE(s.q_avg, 0) AS q,
       COALESCE(s.r_avg, 0) AS r,
       ROUND((0.5 * COALESCE(s.q_avg, 0) + 0.5 * COALESCE(s.r_avg, 0))::numeric, 1) AS radar_score
FROM public.modules m
LEFT JOIN stats s ON s.module_id = m.module_id
WHERE m.is_active AND NOT m.is_deleted
ORDER BY m.module_order
"""

_RANK_SQL = f"SELECT * FROM ({_LEADERBOARD_SQL.replace('LIMIT :limit', '')}) r WHERE user_id = :u"

def _radar(db, user_id):
    rows = db.execute(text(_RADAR_SQL), {"u": user_id}).mappings().all()
    return {"modules": [r["title"] for r in rows],
            "scores": [float(r["radar_score"]) for r in rows]}

@router.get("/me/snapshot")
async def get_my_progress_snapshot(user_id: str = Depends(get_current_user_id)):
    """The caller's own progress rows, for mirroring into the local SQLite cache.

    The user comes from the verified token only, so one learner can never read another's data.
    """
    try:
        with get_postgres_session() as db:

            data = {name: [dict(r) for r in db.execute(text(sql), {"u": user_id}).mappings()]
                    for name, sql in _SNAPSHOT_QUERIES.items()}
            db.commit()
        return jsonable_encoder(data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching progress: {str(e)}"
        )

@router.get("/{user_id}")
async def get_user_progress(user_id: str, me: str = Depends(get_current_user_id)):
    """
    Get user progress from PostgreSQL.
    
    Args:
        user_id: The user ID (UUID)
        
    Returns:
        User progress statistics
    """
    try:
        uid = _own(user_id, me)
        with get_postgres_session() as db:
            data = {name: [dict(r) for r in db.execute(text(sql), {"u": uid}).mappings()]
                    for name, sql in _SNAPSHOT_QUERIES.items()}
        return jsonable_encoder({"user_id": uid, **data})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching statistics: {str(e)}"
        )

@router.get("/{user_id}/statistics")
async def get_user_statistics(user_id: str, force_refresh: bool = False,
                              me: str = Depends(get_current_user_id)):
    """
    Get user statistics from PostgreSQL.
    
    Args:
        user_id: The user ID (UUID)
        force_refresh: Force refresh statistics via trigger
        
    Returns:
        User statistics including dashboard metrics:
        - leaderboard_position
        - latest_badge
        current_module
        - lessons_completed
        - minigames_completed
        - radar_chart (7-point performance visualization)
    """
    try:
        uid = _own(user_id, me)
        p = {"u": uid}
        with get_postgres_session() as db:
            if force_refresh:
                db.execute(text("SELECT public.refresh_user_statistics(:u)"), p)
                db.commit()
            stats = db.execute(text(_SNAPSHOT_QUERIES["user_statistics"]), p).mappings().first() or {}
            badge = db.execute(text(_LATEST_BADGE_SQL), p).mappings().first()
            module = db.execute(text(_CURRENT_MODULE_SQL), p).mappings().first()
            rank = db.execute(text(_RANK_SQL), p).mappings().first()
            radar = _radar(db, uid)
        return jsonable_encoder({
            "user_id": uid,
            "leaderboard_position": rank["rank_position"] if rank else None,
            "latest_badge": dict(badge) if badge else None,
            "current_module": dict(module) if module else None,
            "lessons_completed": stats.get("lessons_completed", 0),
            "minigames_completed": stats.get("minigames_completed", 0),
            "radar_chart": radar,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching statistics: {str(e)}"
        )


@router.get("/{user_id}/streak")
async def get_user_streak(user_id: str, me: str = Depends(get_current_user_id)):
    """
    Get user streak information.
    
    Args:
        user_id: The user ID (UUID)
        
    Returns:
        User streak information
    """
    uid = _own(user_id, me)
    with get_postgres_session() as db:
        row = db.execute(text(_SNAPSHOT_QUERIES["streaks"]), {"u": uid}).mappings().first()
    return jsonable_encoder({"user_id": uid, **(row or
        {"current_streak": 0, "longest_streak": 0, "last_activity_date": None})})



@router.get("/{user_id}/radar-chart")
async def get_radar_chart(user_id: str, me: str = Depends(get_current_user_id)):
    """
    Get user's radar chart data for module performance.
    
    Radar chart calculation: 0.5Q + 0.5R
    - Q = Quiz performance percentage (average score on module quizzes)
    - R = Camera-based sign recognition accuracy percentage
    
    Returns 7 points, one for each module.
    
    Args:
        user_id: The user ID (UUID)
        
    Returns:
        Radar chart data with module names and scores
    """
    try:
        uid = _own(user_id, me)
        with get_postgres_session() as db:
            return {"user_id": uid, **_radar(db, uid)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching statistics: {str(e)}"
        )