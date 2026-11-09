"""Record finished minigames: SQLite first (instant, works offline), server second (background)."""
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from . import auth_service, sync_service
from .api_client import is_online
from .database import models as m
from .database.repository import rebuild_user_statistics
from .database.session import session_scope
from .leaderboard_service import notify_scores_changed

log = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="score_sync")
GAME_CODES = {"sprint": "sign_sprint", "quest": "fingerspell_quest", "detective": "sign_detective"}


def _user_uuid():
    user = auth_service.get_current_user()
    if not user:
        return None
    try:
        return uuid.UUID(str(user["user_id"]))
    except ValueError:            # e.g. the "dev-session" user
        return None


def _minigame_id(db, kind):
    return db.scalar(select(m.Minigame.minigame_id).where(
        m.Minigame.is_deleted.is_(False),
        (m.Minigame.minigame_code == GAME_CODES[kind]) | (m.Minigame.game_type == kind)).limit(1))


def record_minigame_result(kind, score, total, duration_seconds):
    """UI-thread safe: only local SQLite work happens here; the upload is backgrounded."""
    uid = _user_uuid()
    if uid is None:
        return None
    with session_scope() as db:
        minigame_id = _minigame_id(db, kind)
    if minigame_id is None:
        log.warning("Minigame %r is not in the local cache; score not recorded", kind)
        return None
    completed = datetime.now(timezone.utc)
    attempt_id = uuid.uuid4()
    sync_service.queue_minigame_attempt(           # SQLite row + durable sync_queue entry
        uid, attempt_id, minigame_id,
        completed - timedelta(seconds=duration_seconds), completed,
        int(score), int(duration_seconds),
        round(100.0 * score / max(1, total), 2))   # server expects 0-100
    with session_scope() as db:
        rebuild_user_statistics(db, uid)
    notify_scores_changed()
    flush_pending_async()
    return attempt_id


def flush_pending_async():
    """Upload queued items for the signed-in user. No-op offline (the queue persists)."""
    if not is_online():
        return
    uid = _user_uuid()
    if uid is not None:
        _executor.submit(_flush, uid)


def _flush(uid):
    try:
        result = sync_service.process_pending_syncs(uid, batch_size=50)
        log.info("Sync flush: %s", result)
    except Exception:
        log.exception("Sync flush failed")