"""Mirror the signed-in learner's server progress into the local SQLite cache.

Server (Supabase via FastAPI ``/api/v1/progress/me/snapshot``) is the source of truth for rows
that were already synced; local rows are merged by primary key and nothing is deleted, so
attempts still waiting in the sync queue are untouched. Best effort: any failure (offline, no
session, content not cached locally) returns False and the dashboard keeps its cached data.
"""
import logging
import uuid
from datetime import date, datetime, timezone
import threading
import time

from backend import auth_service
from backend.database import models as m
from backend.database.session import session_scope

_log = logging.getLogger(__name__)
CONTENT_SYNC_INTERVAL = 600  # seconds between content checks
_last_content_sync = 0.0

# FK order
_TABLES = {
    "users": m.User,  
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
    if model is m.LessonProgress and out.get("client_updated_at") is None:
        out["client_updated_at"] = out.get("updated_at") or out.get("last_accessed") or datetime.now(timezone.utc)
    if "updated_at" in out and out["updated_at"] is None:
        out["updated_at"] = datetime.now(timezone.utc)
    return out


def fetch_snapshot(token=None):
    """Server snapshot via the shared client (offline tracking + fast offline probe).
    None means offline/unavailable: callers keep using SQLite."""
    from backend.api_client import get_api_client
    return get_api_client().get_progress_snapshot()


def apply_snapshot(snapshot):
    """Merge a snapshot dict into SQLite with conflict safeguards. Returns {table: rows_merged}."""
    counts = {}
    with session_scope() as db:
        for name, model in _TABLES.items():
            rows = snapshot.get(name) or []
            for row in rows:
                converted = _convert(model, row)
                # Safeguard: do not overwrite local Completed lesson with stale non-completed status
                if model is m.LessonProgress:
                    pk = (converted.get("user_id"), converted.get("lesson_id"))
                    existing = db.get(m.LessonProgress, pk)
                    if existing and existing.status == "Completed" and converted.get("status") != "Completed":
                        converted["status"] = "Completed"
                        converted["completed_at"] = existing.completed_at or datetime.now(timezone.utc)
                        converted["completion_percentage"] = max(
                            float(existing.completion_percentage or 0),
                            float(converted.get("completion_percentage") or 0)
                        )
                    if converted.get("status") == "Completed" and not converted.get("completed_at"):
                        converted["completed_at"] = (existing.completed_at if existing else None) or datetime.now(timezone.utc)
                db.merge(model(**converted))
            db.flush()
            counts[name] = len(rows)

        # Refresh local user_statistics from live view after applying remote snapshot
        user = auth_service.get_current_user()
        if user and user.get("user_id"):
            try:
                from backend.database.repository import rebuild_user_statistics
                uid = uuid.UUID(str(user["user_id"]))
                rebuild_user_statistics(db, uid)
            except Exception as e:
                _log.warning("Could not rebuild statistics after snapshot: %s", e)
    return counts

def sync_content_if_due(force=False):
    """Best effort content delta pull. Never raises. Returns True if content is current."""
    global _last_content_sync
    # if not _content_lock.acquire(blocking=False):
    #     return False  # another worker is already syncing
    try:
        if not force and time.monotonic() - _last_content_sync < CONTENT_SYNC_INTERVAL:
            return True
        from backend import sync_service
        result = sync_service.sync_content_from_server()
        if result.get("success"):
            _last_content_sync = time.monotonic()
            return True
        _log.warning("Content sync failed: %s", result.get("error"))
        return False
    except Exception as error:
        _log.warning("Content sync failed: %s", error)
        return False
    # finally:
    #     _content_lock.release()

def pull_user_progress():
    """Refresh local content, then progress (and the leaderboard cache). Never raises."""
    try:
        token = auth_service.get_access_token()
        _log.debug("Sync upload token available: %s", bool(token))
        if not token:
            return False
        sync_content_if_due()  # failure is fine: progress merge falls back to whatever is cached
        snapshot = fetch_snapshot(token)
        if snapshot is None:
            return False
        apply_snapshot(snapshot)
    except Exception as error:
        _log.warning("Progress sync failed: %s", error)
        return False
    try:  # keeps the dashboard rank in step with the leaderboard
        from backend import leaderboard_service
        leaderboard_service.get_leaderboard()
    except Exception as error:
        _log.warning("Leaderboard refresh failed: %s", error)
    # finally:
    #     _pull_lock.release()
    return True

