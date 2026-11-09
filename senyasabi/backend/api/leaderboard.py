"""Leaderboard API endpoints.

This provides endpoints for:
- Leaderboard retrieval (all_time, weekly, monthly)
- Leaderboard caching with immediate response from cache
- Background cache refresh
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy import text
import asyncio

from ..database.postgre_session import get_postgres_session
from ..security import get_current_user_id

router = APIRouter(prefix="/api/v1/leaderboard", tags=["leaderboard"])


PERIODS = {"all_time": None, "weekly": "7 days", "monthly": "30 days"}
CACHE_TTL_SECONDS = 300  # 5 minutes

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


def _should_refresh_cache(fetched_at) -> bool:
    """Check if cache is stale and needs refresh."""
    if fetched_at is None:
        return True
    from datetime import datetime, timedelta
    cache_age = (datetime.utcnow() - fetched_at).total_seconds()
    return cache_age > CACHE_TTL_SECONDS


async def _refresh_cache_background(board_code: str):
    """Background task to refresh leaderboard cache."""
    try:
        with get_postgres_session() as db:
            db.execute(text("SELECT public.refresh_leaderboard_cache(:board_code)"),
                      {"board_code": board_code})
            db.commit()
    except Exception as e:
        print(f"Background cache refresh failed for {board_code}: {e}")


@router.get("/")
async def get_leaderboard(board_code: str = "all_time", limit: int = 100,
                          _user_id: str = Depends(get_current_user_id)):
    """
    Get the leaderboard from cache immediately, with background refresh if stale.

    Returns cached data immediately for fast response. If cache is stale or missing,
    triggers a background refresh for the next request.

    Args:
        board_code: all_time, weekly (last 7 days) or monthly (last 30 days)
        limit: Maximum number of entries to return (1-500)

    Returns:
        {"board_code", "limit", "entries": [{user_id, display_name, total_score,
         rank_position, current_streak, badge_count}], "cached": bool}
    """
    if board_code not in PERIODS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown board_code")
    limit = max(1, min(limit, 500))

    try:
        with get_postgres_session() as db:
            # Try to get cached data first
            cache_rows = db.execute(text("""
                SELECT user_id::text AS user_id, display_name, total_score,
                       current_streak, badge_count, rank_position, fetched_at
                FROM public.leaderboard_cache
                WHERE board_code = :board_code
                ORDER BY rank_position, lower(display_name), user_id
                LIMIT :limit
            """), {"board_code": board_code, "limit": limit}).mappings().all()

            # Check if cache exists and is fresh
            cache_stale = False
            if cache_rows:
                fetched_at = cache_rows[0].get("fetched_at")
                cache_stale = _should_refresh_cache(fetched_at)
            else:
                cache_stale = True

            # If cache is stale or missing, trigger background refresh
            if cache_stale:
                asyncio.create_task(_refresh_cache_background(board_code))

            # If we have cache data, return it immediately
            if cache_rows:
                entries = [{k: v for k, v in dict(r).items() if k != "fetched_at"}
                          for r in cache_rows]
                return {
                    "board_code": board_code,
                    "limit": limit,
                    "entries": entries,
                    "cached": True,
                    "cache_stale": cache_stale
                }

            # No cache - fallback to live query
            rows = db.execute(text(_LEADERBOARD_SQL),
                              {"period": PERIODS[board_code], "limit": limit}).mappings().all()
            return {
                "board_code": board_code,
                "limit": limit,
                "entries": [dict(r) for r in rows],
                "cached": False
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching leaderboard: {str(e)}"
        )


@router.post("/refresh")
async def refresh_leaderboard(board_code: str = "all_time",
                               _user_id: str = Depends(get_current_user_id)):
    """
    Manually trigger leaderboard cache refresh.

    Args:
        board_code: all_time, weekly, or monthly

    Returns:
        Success status
    """
    if board_code not in PERIODS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown board_code")

    try:
        with get_postgres_session() as db:
            db.execute(text("SELECT public.refresh_leaderboard_cache(:board_code)"),
                      {"board_code": board_code})
            db.commit()
        return {"success": True, "board_code": board_code, "message": "Leaderboard cache refreshed"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing leaderboard: {str(e)}"
        )

@router.get("/user/{user_id}")
async def get_user_leaderboard_position(user_id: str, board_code: str = "all_time"):
    """
    Get user's position on the leaderboard.

    Args:
        user_id: The user ID (UUID)
        board_code: The leaderboard type (all_time, weekly, monthly)

    Returns:
        User's leaderboard position with display_name, total_score, and rank
    """
    if board_code not in PERIODS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown board_code")

    try:
        with get_postgres_session() as db:
            result = db.execute(text("""
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
                 WHERE user_id = :user_id
            """), {"user_id": user_id, "period": PERIODS[board_code]}).mappings().first()

            if not result:
                return {
                    "user_id": user_id,
                    "board_code": board_code,
                    "rank": None,
                    "message": "User not found or no score recorded"
                }

            return {
                "user_id": user_id,
                "board_code": board_code,
                "rank": result["rank_position"],
                "display_name": result["display_name"],
                "total_score": result["total_score"],
                "current_streak": result["current_streak"],
                "badge_count": result["badge_count"]
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user position: {str(e)}"
        )
