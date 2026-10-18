"""Mirror the signed-in learner's server progress into the local SQLite cache.

Server (Supabase via FastAPI ``/api/v1/progress/me/snapshot``) is the source of truth for rows
that were already synced; local rows are merged by primary key and nothing is deleted, so
attempts still waiting in the sync queue are untouched. Best effort: any failure (offline, no
session, content not cached locally) returns False and the dashboard keeps its cached data.
"""
import logging
import uuid
from datetime import date, datetime

import requests

from backend import auth_service, config
from backend.database import models as m
from backend.database.session import session_scope

_log = logging.getLogger(__name__)
TIMEOUT = 8  # seconds; single attempt so an offline app stays responsive

# FK order
_TABLES = {
    "lesson_progress": m.LessonProgress,
    "quiz_attempts": m.QuizAttempt,
    "minigame_attempts": m.MinigameAttempt,
    "user_badges": m.UserBadges,
    "streaks": m.Streak,
    "user_statistics": m.UserStatistics,
}


def _convert(model, row):
    out = {}
    for attr in model.__mapper__.column_attrs:
        value = row.get(attr.key)
        if isinstance(value, str):
            try:
                py = attr.columns[0].type.python_type
            except NotImplementedError:
                py = None
            if py is uuid.UUID:
                value = uuid.UUID(value)
            elif py is datetime or attr.key.endswith(("_at", "accessed")):
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            elif py is date:
                value = date.fromisoformat(value)
        out[attr.key] = value
    return out


def fetch_snapshot(token):
    try:
        resp = requests.get(f"{config.API_BASE_URL}/api/v1/progress/me/snapshot",
                            headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except (requests.exceptions.RequestException, ValueError) as error:
        _log.warning("Progress snapshot unavailable: %s", error)
        return None


def apply_snapshot(snapshot):
    """Merge a snapshot dict into SQLite. Returns {table: rows_merged}."""
    counts = {}
    with session_scope() as db:
        for name, model in _TABLES.items():
            rows = snapshot.get(name) or []
            for row in rows:
                db.merge(model(**_convert(model, row)))
            db.flush()
            counts[name] = len(rows)
    return counts


def pull_user_progress():
    """Refresh local progress (and the leaderboard cache) for the current session. Never raises."""
    try:
        token = auth_service.get_access_token()
        if not token:
            return False
        snapshot = fetch_snapshot(token)
        if snapshot is None:
            return False
        apply_snapshot(snapshot)
    except Exception as error:  # missing local content (FK), bad data, etc.
        _log.warning("Progress sync failed: %s", error)
        return False
    try:  # keeps the dashboard rank in step with the leaderboard
        from backend import leaderboard_service
        leaderboard_service.get_leaderboard()
    except Exception as error:
        _log.warning("Leaderboard refresh failed: %s", error)
    return True

