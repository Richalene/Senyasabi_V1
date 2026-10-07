"""Dashboard data boundary. No persistence until the V4 repository is ready."""


class DefaultDashboardRepository:
    """Replace this adapter with a SQLAlchemy repository using the same method.

    module_progress entries will contain completion_percentage, status,
    last_accessed and completed_at; user_badges entries badge_id and unlocked_at.
    Empty collections mean the user has no recorded progress or badges.
    """

    def get_dashboard_stats(self, user_id):
        return {
            "user_statistics": {
                "lessons_completed": 0, "quizzes_completed": 0,
                "minigames_completed": 0, "total_quiz_score": 0,
                "total_minigame_score": 0, "average_accuracy": 0.0,
                "total_time_spent": 0,
            },
            "streaks": {
                "current_streak": 0, "longest_streak": 0,
                "last_activity_date": None,
            },
            "module_progress": [],
            "user_badges": [],
            "leaderboard": {
                "total_score": 0, "average_accuracy": 0.0,
                "lessons_completed": 0, "current_streak": 0,
                "rank_position": None,
            },
        }


_repository = DefaultDashboardRepository()


def get_dashboard_stats(user_id):
    """Return fresh V4-shaped data; anonymous previews also use safe defaults."""
    if user_id is None:
        return DefaultDashboardRepository().get_dashboard_stats(None)
    return _repository.get_dashboard_stats(user_id)
