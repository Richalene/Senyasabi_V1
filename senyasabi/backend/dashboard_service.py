"""Dashboard data boundary using SQLite persistence."""

from .database.session import get_session
from .database.repository import (
    get_user_statistics,
    list_lesson_progress,
    list_user_badges,
    get_leaderboard_cache,
    get_streak,
)
from .database.models import Streak


class SQLiteDashboardRepository:
    """SQLite-based repository for dashboard statistics."""

    def get_dashboard_stats(self, user_id):
        if user_id is None:
            return self._get_default_stats()

        with get_session() as db:
            # Get user statistics
            stats = get_user_statistics(db, user_id)
            if stats is None:
                stats_data = {
                    "lessons_completed": 0,
                    "quizzes_completed": 0,
                    "minigames_completed": 0,
                    "total_quiz_score": 0,
                    "total_minigame_score": 0,
                    "average_accuracy": 0.0,
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
                    "total_time_spent_seconds": stats.total_time_spent_seconds,
                }

            # Get streaks
            streak = get_streak(db, user_id)
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

            # Get lesson progress (replaces module_progress)
            lesson_progress_list = list_lesson_progress(db, user_id)
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
            user_badges_list = list_user_badges(db, user_id)
            user_badges_data = [
                {
                    "badge_id": ub.badge_id,
                    "unlocked_at": ub.unlocked_at.isoformat(),
                }
                for ub in user_badges_list
            ]

            # Get leaderboard cache (replaces leaderboard_entry)
            leaderboard_entry = get_leaderboard_cache(db, "all_time", user_id)
            if leaderboard_entry is None:
                leaderboard_data = {
                    "rank_position": None,
                    "total_score": 0,
                    "fetched_at": None,
                }
            else:
                leaderboard_data = {
                    "rank_position": leaderboard_entry.rank_position,
                    "total_score": leaderboard_entry.total_score,
                    "fetched_at": leaderboard_entry.fetched_at.isoformat() if leaderboard_entry.fetched_at else None,
                }

            return {
                "user_statistics": stats_data,
                "streaks": streaks_data,
                "lesson_progress": lesson_progress_data,
                "user_badges": user_badges_data,
                "leaderboard": leaderboard_data,
            }

    def _get_default_stats(self):
        """Return default stats for anonymous users."""
        return {
            "user_statistics": {
                "lessons_completed": 0,
                "quizzes_completed": 0,
                "minigames_completed": 0,
                "total_quiz_score": 0,
                "total_minigame_score": 0,
                "average_accuracy": 0.0,
                "total_time_spent_seconds": 0,
            },
            "streaks": {
                "current_streak": 0,
                "longest_streak": 0,
                "last_activity_date": None,
            },
            "lesson_progress": [],
            "user_badges": [],
            "leaderboard": {
                "rank_position": None,
                "total_score": 0,
                "fetched_at": None,
            },
        }


_repository = SQLiteDashboardRepository()


def get_dashboard_stats(user_id):
    """Return fresh dashboard data from SQLite; anonymous previews use safe defaults."""
    return _repository.get_dashboard_stats(user_id)
