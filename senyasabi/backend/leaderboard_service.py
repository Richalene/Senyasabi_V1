"""Leaderboard data boundary.

Completed quiz and minigame attempts in SQLite are the primary local source. They are already
queued for upload by the sync service. Local results are merged with the last server leaderboard
snapshot so cached global entries remain visible. The API is queried only when neither local
source has data.
Only public display data (display name, points, streak, badge count) is ever handled here.
"""
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from backend import auth_service

BOARD_CODES = ("all_time", "weekly", "monthly")
BOARD_PERIODS = {"all_time": None, "weekly": timedelta(days=7), "monthly": timedelta(days=30)}
_log = logging.getLogger(__name__)


class LeaderboardUnavailable(Exception):
    """No server response and no cached leaderboard."""


def _entry(user_id, name, points, rank, streak=0, badges=0):
    return dict(user_id=str(user_id), username=name, total_score=int(points or 0),
                rank_position=int(rank), current_streak=int(streak or 0),
                badges_unlocked=int(badges or 0))


class SyncedLeaderboardRepository:
    """Build the board from local attempts and cached server entries."""

    def get_leaderboard(self, board_code="all_time"):
        local = self._load_local_attempts(board_code)
        cached = self._load(board_code)
        if local is not None or cached is not None:
            entries = {entry["user_id"]: entry for entry in cached or []}
            for entry in local or []:
                cached_entry = entries.get(entry["user_id"])
                if cached_entry is None:
                    entries[entry["user_id"]] = entry
                else:
                    cached_entry.update(username=entry["username"],
                                        total_score=entry["total_score"])
            return _rank_entries(list(entries.values()))

        payload = self._fetch(board_code)
        if payload is not None:
            entries = [_entry(e["user_id"], e.get("display_name") or "Learner", e.get("total_score"),
                              e["rank_position"], e.get("current_streak"), e.get("badge_count"))
                       for e in payload.get("entries", [])]
            self._store(board_code, entries)
            return entries
        raise LeaderboardUnavailable("No local leaderboard data and server is unreachable")

    @staticmethod
    def _load_local_attempts(board_code):
        from backend.database.models import MinigameAttempt, QuizAttempt, User
        from backend.database.session import session_scope

        cutoff = BOARD_PERIODS[board_code]
        completed_after = datetime.now(timezone.utc) - cutoff if cutoff is not None else None
        scores = {}
        try:
            with session_scope() as db:
                for model in (QuizAttempt, MinigameAttempt):
                    query = db.query(model.user_id, func.sum(model.score)).filter(
                        model.completed_at.is_not(None), model.score.is_not(None))
                    if completed_after is not None:
                        query = query.filter(model.completed_at >= completed_after)
                    for user_id, score in query.group_by(model.user_id).all():
                        scores[str(user_id)] = scores.get(str(user_id), 0) + int(score or 0)

                if not scores:
                    return None

                users = db.query(User).filter(User.user_id.in_(
                    [uuid.UUID(user_id) for user_id in scores])).all()
                entries = [
                    _entry(user.user_id, user.display_name or user.username, scores[str(user.user_id)], 0)
                    for user in users
                ]
                return _rank_entries(entries)
        except Exception as error:
            _log.warning("Local leaderboard read failed: %s", error)
            return None

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


def _rank_entries(entries):
    ordered = sorted(entries, key=lambda e: (-e["total_score"], str(e["username"]).casefold(),
                                            str(e["user_id"])))
    previous_score = None
    rank = 0
    for position, entry in enumerate(ordered, start=1):
        if entry["total_score"] != previous_score:
            rank = position
            previous_score = entry["total_score"]
        entry["rank_position"] = rank
    return ordered


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
        entries = _repository.get_leaderboard(board_code)
    except (OSError, ConnectionError, TimeoutError) as error:
        raise LeaderboardUnavailable(str(error)) from error
    entries = entries or []
    return [{"current_streak": 0, "badges_unlocked": 0, "total_score": 0,
             **entry, "is_current_user": user_id is not None and str(entry["user_id"]) == str(user_id)}
            for entry in sorted(entries, key=lambda e: (e["rank_position"],
                                                       str(e["username"]).casefold(), str(e["user_id"])))]
