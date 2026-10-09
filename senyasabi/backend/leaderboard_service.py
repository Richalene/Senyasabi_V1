"""Leaderboard data boundary for future leaderboard/users/user_badges queries."""
from backend import auth_service


class MockLeaderboardRepository:
    def get_leaderboard(self):
        # Temporary demonstration users; no persistence or real activity.
        return [
            dict(user_id="mock-2", username="Sample Ben", current_streak=5,
                 badges_unlocked=2, rank_position=2),
            dict(user_id="mock-1", username="Sample Ana", current_streak=8,
                 badges_unlocked=3, rank_position=1),
            dict(user_id="mock-3", username="Sample Kai", current_streak=2,
                 badges_unlocked=1, rank_position=3),
        ]


_repository = MockLeaderboardRepository()


def get_leaderboard():
    """Return ranked entries with session-specific highlighting, without mutation.

    Replace _repository with a SQLAlchemy adapter returning these same fields.
    badges_unlocked is the count of user_badges for each user_id.
    """
    user = auth_service.get_current_user()
    user_id = user["user_id"] if user else None
    return [dict(entry, is_current_user=user_id is not None and entry["user_id"] == user_id)
            for entry in sorted(_repository.get_leaderboard(), key=lambda entry: entry["rank_position"])]
