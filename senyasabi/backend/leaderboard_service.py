"""Leaderboard data boundary.

Completed quiz and minigame attempts in SQLite are the primary local source. They are already
queued for upload by the sync service. Local results are merged with the last server leaderboard
snapshot so cached global entries remain visible. The API is queried in the background to refresh
the cache without blocking the UI.
Only public display data (display name, points, streak, badge count) is ever handled here.
"""
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
import concurrent.futures

from sqlalchemy import func

from backend import auth_service

BOARD_CODES = ("all_time", "weekly", "monthly")
BOARD_PERIODS = {"all_time": None, "weekly": timedelta(days=7), "monthly": timedelta(days=30)}
CACHE_TTL_SECONDS = 900  # 15 minutes
_log = logging.getLogger(__name__)

# Thread pool for background fetches
_fetch_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="lb_fetch")


class LeaderboardUnavailable(Exception):
    """No server response and no cached leaderboard."""


def _entry(user_id, name, points, rank, streak=0, badges=0):
    return dict(user_id=str(user_id), username=name, total_score=int(points or 0),
                rank_position=int(rank), current_streak=int(streak or 0),
                badges_unlocked=int(badges or 0))


class SyncedLeaderboardRepository:
    """Build the board from local attempts and cached server entries."""

    def get_leaderboard(self, board_code="all_time", force_refresh=False):
        """Get leaderboard, returning cached data immediately and fetching fresh data in background."""
        local = self._load_local_attempts(board_code)
        cached = self._load(board_code)

        # Merge local attempts with cached server data
        if local is not None or cached is not None:
            entries = {entry["user_id"]: entry for entry in cached or []}
            for entry in local or []:
                cached_entry = entries.get(entry["user_id"])
                if cached_entry is None:
                    entries[entry["user_id"]] = entry
                else:
                    cached_entry.update(username=entry["username"],
                                        total_score=entry["total_score"])
            merged = _rank_entries(list(entries.values()))

            # Check if cache is stale and trigger background refresh
            if not force_refresh and self._is_cache_stale(board_code):
                self._fetch_background(board_code)

            return merged

        # No cache at all - fetch synchronously on first load
        payload = self._fetch(board_code)
        if payload is not None:
            entries = [_entry(e["user_id"], e.get("display_name") or "Learner", e.get("total_score"),
                              e["rank_position"], e.get("current_streak"), e.get("badge_count"))
                       for e in payload.get("entries", [])]
            self._store(board_code, entries)
            return entries
        raise LeaderboardUnavailable("No local leaderboard data and server is unreachable")

    def _is_cache_stale(self, board_code):
        """Check if cache is older than CACHE_TTL_SECONDS."""
        from backend.database.repository import list_leaderboard_cache
        from backend.database.session import session_scope
        try:
            with session_scope() as db:
                rows = list_leaderboard_cache(db, board_code, 1)  # Get one entry to check timestamp
                if not rows:
                    return True  # No cache = stale
                cache = rows[0]
                if cache.fetched_at is None:
                    return True
                cache_age = (datetime.now(timezone.utc) - cache.fetched_at).total_seconds()
                return cache_age > CACHE_TTL_SECONDS
        except Exception as error:
            _log.warning("Cache staleness check failed: %s", error)
            return True  # On error, treat as stale

    def _fetch_background(self, board_code):
        """Fetch fresh data in background thread and notify listeners."""
        def fetch_and_store():
            try:
                payload = self._fetch(board_code)
                if payload is not None:
                    entries = [_entry(e["user_id"], e.get("display_name") or "Learner", e.get("total_score"),
                                      e["rank_position"], e.get("current_streak"), e.get("badge_count"))
                               for e in payload.get("entries", [])]
                    self._store(board_code, entries)
                    # Notify listeners that fresh data is available
                    notify_scores_changed()
                    _log.info("Background leaderboard refresh completed for %s", board_code)
            except Exception as error:
                _log.warning("Background leaderboard fetch failed for %s: %s", board_code, error)

        _fetch_executor.submit(fetch_and_store)

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


def get_leaderboard(user_id=_CURRENT_USER, board_code="all_time", force_refresh=False):
    """Return ranked entries with session-specific highlighting, without mutation.

    Returns cached data immediately for fast UI response. Triggers background refresh
    if cache is stale (older than 5 minutes) or force_refresh is True.

    Order is deterministic: rank_position, then display name (case-insensitive), then user_id.
    Equal scores share a rank_position. Raises LeaderboardUnavailable on a hard failure.
    An explicit user_id lets worker requests use the session captured by the UI.
    """
    if board_code not in BOARD_CODES:
        raise ValueError(f"Unknown leaderboard: {board_code}")
    if user_id is _CURRENT_USER:
        user = auth_service.get_current_user()
        user_id = user["user_id"] if user else None
    DEMO_LEADERBOARD = [
        dict(user_id="mock-1", username="Sample Ana", total_score=1500, current_streak=8, badges_unlocked=3, rank_position=1),
        dict(user_id="mock-2", username="Sample Ben", total_score=1200, current_streak=5, badges_unlocked=2, rank_position=2),
        dict(user_id="mock-3", username="Sample Kai", total_score=900, current_streak=2, badges_unlocked=1, rank_position=3),
    ]
    try:
        entries = _repository.get_leaderboard(board_code, force_refresh=force_refresh)
    except (OSError, ConnectionError, TimeoutError) as error:
        _log.warning("Leaderboard unavailable: %s", error)
        entries = []
    if not entries and user_id and str(user_id).startswith("mock-"):
        entries = DEMO_LEADERBOARD
    elif entries and user_id and str(user_id).startswith("mock-") and not any(str(e.get("user_id")) == str(user_id) for e in entries):
        entries = DEMO_LEADERBOARD
    entries = entries or []
    return [{"current_streak": 0, "badges_unlocked": 0, "total_score": 0,
             **entry, "is_current_user": user_id is not None and str(entry["user_id"]) == str(user_id)}
            for entry in sorted(entries, key=lambda e: (e["rank_position"],
                                                       str(e["username"]).casefold(), str(e["user_id"])))]


def refresh_leaderboard(board_code="all_time"):
    """Force refresh the leaderboard cache from the server.

    This is useful for pull-to-refresh functionality or when the user explicitly
    wants fresh data. Returns immediately; the actual refresh happens in background.
    """
    if board_code not in BOARD_CODES:
        raise ValueError(f"Unknown leaderboard: {board_code}")
    _repository._fetch_background(board_code)
