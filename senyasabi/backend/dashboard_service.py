"""Dashboard data boundary using SQLite persistence."""
import logging
import uuid

from .database.session import session_scope
from .database.repository import (
    get_user_statistics, list_lesson_progress, list_user_badges,
    get_leaderboard_cache, get_streak,
    get_latest_badge, get_current_module, get_module_performance,
    list_modules,
)


def _coerce_uuid(user_id) -> uuid.UUID | None:
    if isinstance(user_id, uuid.UUID):
        return user_id
    if isinstance(user_id, str):
        try:
            return uuid.UUID(user_id)
        except ValueError:
            return None
    return None


class DefaultDashboardRepository:
    """Default/fallback dashboard stats repository with full schema compatibility."""

    def get_dashboard_stats(self, user_id):
        return {
            "user_statistics": {
                "lessons_completed": 0,
                "quizzes_completed": 0,
                "minigames_completed": 0,
                "total_quiz_score": 0,
                "total_minigame_score": 0,
                "average_accuracy": 0.0,
                "total_time_spent": 0,
                "total_time_spent_seconds": 0,
            },
            "streaks": {
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity_date": None,
            },
            "module_count": 0,
            "module_progress": [],
            "lesson_progress": [],
            "user_badges": [],
            "leaderboard": {
                "total_score": 0,
                "average_accuracy": 0.0,
                "lessons_completed": 0,
                "current_streak": 0,
                "rank_position": None,
                "fetched_at": None,
            },
            "latest_badge": None,
            "current_module": None,
            "module_performance": [],
        }


class SQLiteDashboardRepository(DefaultDashboardRepository):
    """SQLite-based repository for dashboard statistics."""

    def get_dashboard_stats(self, user_id):
        uid = _coerce_uuid(user_id)
        if uid is None:
            return self._get_default_stats()

        with session_scope() as db:
            # Get user statistics
            stats = get_user_statistics(db, uid)
            if stats is None:
                stats_data = {
                    "lessons_completed": 0,
                    "quizzes_completed": 0,
                    "minigames_completed": 0,
                    "total_quiz_score": 0,
                    "total_minigame_score": 0,
                    "average_accuracy": 0.0,
                    "total_time_spent": 0,
                    "total_time_spent_seconds": 0,
                }
            else:
                stats_data = {
                    "lessons_completed": stats.lessons_completed,
                    "quizzes_completed": stats.quizzes_completed,
                    "minigames_completed": stats.minigames_completed,
                    "total_quiz_score": stats.total_quiz_score,
                    "total_minigame_score": stats.total_minigame_score,
                    "average_accuracy": float(stats.average_accuracy) if stats.average_accuracy else 0.0,
                    "total_time_spent": stats.total_time_spent_seconds,
                    "total_time_spent_seconds": stats.total_time_spent_seconds,
                }

            # Get streaks
            streak = get_streak(db, uid)
            if streak is None:
                streaks_data = {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "last_activity_date": None,
                }
            else:
                streaks_data = {
                    "current_streak": streak.current_streak or 0,
                    "longest_streak": streak.longest_streak or 0,
                    "last_activity_date": streak.last_activity_date.isoformat() if streak.last_activity_date else None,
                }

            # Get lesson progress
            lesson_progress_list = list_lesson_progress(db, uid)
            lesson_progress_data = [
                {
                    "lesson_id": lp.lesson_id,
                    "completion_percentage": float(lp.completion_percentage) if lp.completion_percentage else 0.0,
                    "status": lp.status,
                    "last_accessed": lp.last_accessed.isoformat() if lp.last_accessed else None,
                    "completed_at": lp.completed_at.isoformat() if lp.completed_at else None,
                    "time_spent_seconds": lp.time_spent_seconds,
                }
                for lp in lesson_progress_list
            ]

            # Get user badges
            user_badges_list = list_user_badges(db, uid)
            user_badges_data = [
                {
                    "badge_id": ub.badge_id,
                    "unlocked_at": ub.unlocked_at.isoformat(),
                }
                for ub in user_badges_list
            ]

            # Get leaderboard cache
            leaderboard_entry = get_leaderboard_cache(db, "all_time", uid)
            if leaderboard_entry is None:
                leaderboard_data = {
                    "rank_position": None,
                    "total_score": 0,
                    "average_accuracy": stats_data["average_accuracy"],
                    "lessons_completed": stats_data["lessons_completed"],
                    "current_streak": streaks_data["current_streak"],
                    "fetched_at": None,
                }
            else:
                leaderboard_data = {
                    "rank_position": leaderboard_entry.rank_position,
                    "total_score": leaderboard_entry.total_score,
                    "average_accuracy": stats_data["average_accuracy"],
                    "lessons_completed": stats_data["lessons_completed"],
                    "current_streak": streaks_data["current_streak"],
                    "fetched_at": leaderboard_entry.fetched_at.isoformat() if leaderboard_entry.fetched_at else None,
                }

            latest = get_latest_badge(db, uid)
            latest_badge_data = (
                {
                    "badge_id": latest[0].badge_id,
                    "badge_name": latest[0].badge_name,
                    "description": latest[0].description,
                    "unlocked_at": latest[1].unlocked_at.isoformat(),
                }
                if latest else None
            )

            current = get_current_module(db, uid)
            current_module_data = (
                {
                    "module_id": current.module_id,
                    "module_code": current.module_code,
                    "title": current.title,
                }
                if current else None
            )

            modules = list_modules(db)
            module_progress_data = [
                {
                    "module_id": m.module_id,
                    "module_code": m.module_code,
                    "title": m.title,
                }
                for m in modules
            ]

            return {
                "user_statistics": stats_data,
                "streaks": streaks_data,
                "module_count": len(modules),
                "module_progress": module_progress_data,
                "lesson_progress": lesson_progress_data,
                "user_badges": user_badges_data,
                "leaderboard": leaderboard_data,
                "latest_badge": latest_badge_data,
                "current_module": current_module_data,
                "module_performance": get_module_performance(db, uid),
            }

    def _get_default_stats(self):
        """Return default stats for anonymous or non-UUID users."""
        return super().get_dashboard_stats(None)


_repository = SQLiteDashboardRepository()

RADAR_MAX = 100.0


def get_dashboard_stats(user_id):
    """Raw data from SQLite; anonymous previews use safe defaults."""
    if user_id is None:
        return DefaultDashboardRepository().get_dashboard_stats(None)
    from backend import progress_sync
    progress_sync.pull_user_progress()  # best effort; falls back to the local cache
    defaults = DefaultDashboardRepository().get_dashboard_stats(user_id)
    try:
        data = _repository.get_dashboard_stats(user_id) or {}
    except (OSError, ConnectionError, TimeoutError) as error:
        logging.getLogger(__name__).warning("Statistics unavailable: %s", error)
        return defaults
    for key, value in data.items():
        if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
            defaults[key].update({name: item for name, item in value.items() if item is not None})
        elif key in defaults and value is not None:
            defaults[key] = value
    return defaults


def get_dashboard(user_id):
    """What the dashboard screen should render."""
    return build_dashboard(get_dashboard_stats(user_id))


def build_dashboard(raw: dict) -> dict:
    """Pure function (no DB access), so it's easy to unit test."""
    return {
        # 1. Current leaderboard position (None = unranked / never synced)
        "leaderboard_rank": raw["leaderboard"]["rank_position"],
        # 2. Latest badge (None = no badges yet)
        "latest_badge": raw["latest_badge"],
        # 3. Current ongoing module (None = nothing in progress, or all done)
        "current_module": raw["current_module"],
        # 4. Lessons completed, counted live so it can't drift like the cache
        "lessons_completed": sum(
            1 for lp in raw["lesson_progress"] if lp["status"] == "Completed"
        ),
        # 5. Minigames completed
        "minigames_completed": raw["user_statistics"]["minigames_completed"],
        # 6. Seven-point radar chart
        "radar": {
            "max": RADAR_MAX,
            "axes": [
                {
                    "module_id": m["module_id"],
                    "label": m["title"],
                    "score": m["score"],
                    "quiz_performance": m["quiz_performance"],
                    "camera_accuracy": m["camera_accuracy"],
                }
                for m in raw["module_performance"]
            ],
        },
    }