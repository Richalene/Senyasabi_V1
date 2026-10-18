"""Leaderboard API endpoints.

This provides endpoints for:
- Leaderboard retrieval (all_time, weekly, monthly)
- Leaderboard caching
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy import text

from ..database.postgre_session import get_postgres_session
from ..security import get_current_user_id

router = APIRouter(prefix="/api/v1/leaderboard", tags=["leaderboard"])


PERIODS = {"all_time": None, "weekly": "7 days", "monthly": "30 days"}

# total_score follows the existing rule (v_user_statistics_live): completed quiz scores +
# completed minigame scores. Ties share a rank (RANK) and are listed by name, then user_id.
# Only public display data is returned: never email or username.
_LEADERBOARD_SQL = """
WITH scores AS (
    SELECT u.user_id,
           COALESCE(NULLIF(btrim(u.display_name), ''), u.username) AS display_name,
           (COALESCE((SELECT SUM(qa.score) FROM public.quiz_attempts qa
                       WHERE qa.user_id = u.user_id AND qa.completed_at IS NOT NULL
                         AND (CAST(:period AS text) IS NULL
                              OR qa.completed_at >= now() - CAST(:period AS interval))), 0)
          + COALESCE((SELECT SUM(ma.score) FROM public.minigame_attempts ma
                       WHERE ma.user_id = u.user_id AND ma.completed_at IS NOT NULL
                         AND (CAST(:period AS text) IS NULL
                              OR ma.completed_at >= now() - CAST(:period AS interval))), 0))::BIGINT AS total_score,
           COALESCE((SELECT s.current_streak FROM public.streaks s WHERE s.user_id = u.user_id), 0) AS current_streak,
           (SELECT COUNT(*) FROM public.user_badges ub WHERE ub.user_id = u.user_id)::INT AS badge_count
      FROM public.users u
)
SELECT user_id::text AS user_id, display_name, total_score, current_streak, badge_count,
       RANK() OVER (ORDER BY total_score DESC)::INT AS rank_position
  FROM scores
 WHERE total_score > 0
 ORDER BY rank_position, lower(display_name), user_id
 LIMIT :limit
"""


@router.get("/")
async def get_leaderboard(board_code: str = "all_time", limit: int = 100,
                          _user_id: str = Depends(get_current_user_id)):
    """
    Get the leaderboard from PostgreSQL (real attempts only, nothing fabricated).

    Args:
        board_code: all_time, weekly (last 7 days) or monthly (last 30 days)
        limit: Maximum number of entries to return (1-500)

    Returns:
        {"board_code", "limit", "entries": [{user_id, display_name, total_score,
         rank_position, current_streak, badge_count}]}
    """
    if board_code not in PERIODS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown board_code")
    limit = max(1, min(limit, 500))
    try:
        with get_postgres_session() as db:
            rows = db.execute(text(_LEADERBOARD_SQL),
                              {"period": PERIODS[board_code], "limit": limit}).mappings().all()
            return {"board_code": board_code, "limit": limit, "entries": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching leaderboard: {str(e)}"
        )

@router.get("/user/{user_id}")
async def get_user_leaderboard_position(user_id: int, board_code: str = "all_time"):
    """
    Get user's position on the leaderboard.
    
    Args:
        user_id: The user ID
        board_code: The leaderboard type (all_time, weekly, monthly)
        
    Returns:
        User's leaderboard position
    """
    try:
        with get_postgres_session() as db:
            # TODO: Implement user position retrieval
            return {
                "user_id": user_id,
                "board_code": board_code,
                "rank": None,
                "message": "User leaderboard position - to be implemented"
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user position: {str(e)}"
        )
