"""Leaderboard data boundary.

Online: GET /api/v1/leaderboard (Supabase/PostgreSQL, computed from real attempts) and the
result is mirrored into the SQLite ``leaderboard_cache``. Offline/unreachable: the last cached
board is shown. If neither is available a ``LeaderboardUnavailable`` error is raised so the UI
can show its error state (an empty list means "no scored activity yet").
Only public display data (display name, points, streak, badge count) is ever handled here.
"""
import logging
import threading
import uuid
from datetime import datetime, timezone

from backend import auth_service

BOARD_CODES = ("all_time", "weekly", "monthly")
_log = logging.getLogger(__name__)


class LeaderboardUnavailable(Exception):
    """No server response and no cached leaderboard."""


def _entry(user_id, name, points, rank, streak=0, badges=0):
    return dict(user_id=str(user_id), username=name, total_score=int(points or 0),
                rank_position=int(rank), current_streak=int(streak or 0),
                badges_unlocked=int(badges or 0))


class SyncedLeaderboardRepository:
    """API first (refreshing the SQLite cache), cached rows when offline."""

    def get_leaderboard(self, board_code="all_time"):
        payload = self._fetch(board_code)
        if payload is not None:
            entries = [_entry(e["user_id"], e.get("display_name") or "Learner", e.get("total_score"),
                              e["rank_position"], e.get("current_streak"), e.get("badge_count"))
                       for e in payload.get("entries", [])]
            self._store(board_code, entries)
            return entries
        cached = self._load(board_code)
        if cached is None:
            raise LeaderboardUnavailable("Leaderboard server unreachable and nothing cached")
        return cached

    @staticmethod
    def _fetch(board_code):
        from backend.api_client import get_api_client
        try:
            payload = get_api_client().get_leaderboard(board_code)
        except Exception as error:  # network/serialisation problems -> cache fallback
            _log.warning("Leaderboard fetch failed: %s", error)
            return None
        return payload if isinstance(payload, dict) and "entries" in payload else None

    @staticmethod
    def _store(board_code, entries):
        """Replace this board's cache. Other learners get a minimal placeholder users row
        (no email) only because leaderboard_cache has a FK to users."""
        from backend.database.models import LeaderboardCache, User
        from backend.database.session import session_scope
        try:
            with session_scope() as db:
                db.query(LeaderboardCache).filter(LeaderboardCache.board_code == board_code).delete()
                now = datetime.now(timezone.utc)
                for e in entries:
                    uid = uuid.UUID(e["user_id"])
                    if db.get(User, uid) is None:
                        db.add(User(user_id=uid, username=f"lb-{uid.hex}",
                                    email=None, display_name=e["username"]))
                        db.flush()
                    db.add(LeaderboardCache(board_code=board_code, user_id=uid,
                                            display_name=e["username"], total_score=e["total_score"],
                                            rank_position=e["rank_position"],
                                            current_streak=e["current_streak"],
                                            badge_count=e["badges_unlocked"], fetched_at=now))
        except Exception as error:
            _log.warning("Leaderboard cache write failed: %s", error)

    @staticmethod
    def _load(board_code):
        from backend.database.repository import list_leaderboard_cache
        from backend.database.session import session_scope
        try:
            with session_scope() as db:
                rows = list_leaderboard_cache(db, board_code, 500)
                if not rows:
                    return None
                return [_entry(r.user_id, r.display_name, r.total_score, r.rank_position,
                               r.current_streak, r.badge_count) for r in rows]
        except Exception as error:
            _log.warning("Leaderboard cache read failed: %s", error)
            return None


_repository = SyncedLeaderboardRepository()
_CURRENT_USER = object()
_listeners = []
_listeners_lock = threading.Lock()


def add_scores_listener(callback):
    with _listeners_lock:
        _listeners.append(callback)


def remove_scores_listener(callback):
    with _listeners_lock:
        if callback in _listeners:
            _listeners.remove(callback)


def notify_scores_changed():
    """Call after a quiz/minigame score was saved or synced so open leaderboards refresh."""
    with _listeners_lock:
        callbacks = list(_listeners)
    for callback in callbacks:
        try:
            callback()
        except Exception:
            _log.exception("Leaderboard listener failed")


def get_leaderboard(user_id=_CURRENT_USER, board_code="all_time"):
    """Return ranked entries with session-specific highlighting, without mutation.

    Order is deterministic: rank_position, then display name (case-insensitive), then user_id.
    Equal scores share a rank_position. Raises LeaderboardUnavailable on a hard failure.
    An explicit user_id lets worker requests use the session captured by the UI.
    """
    if board_code not in BOARD_CODES:
        raise ValueError(f"Unknown leaderboard: {board_code}")
    if user_id is _CURRENT_USER:
        user = auth_service.get_current_user()
        user_id = user["user_id"] if user else None
    try:
        entries = _repository.get_leaderboard() if board_code == "all_time" \
            else _repository.get_leaderboard(board_code)
    except (OSError, ConnectionError, TimeoutError) as error:
        raise LeaderboardUnavailable(str(error)) from error
    entries = entries or []
    return [{"current_streak": 0, "badges_unlocked": 0, "total_score": 0,
             **entry, "is_current_user": user_id is not None and str(entry["user_id"]) == str(user_id)}
            for entry in sorted(entries, key=lambda e: (e["rank_position"],
                                                       str(e["username"]).casefold(), str(e["user_id"])))]
