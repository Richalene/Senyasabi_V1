"""
Idempotent sync service for client-initiated synchronization to PostgreSQL/Supabase.

This service ensures that:
1. Sync operations are idempotent - can be safely retried
2. Server-assigned content IDs are preserved
3. Client-generated UUIDs for attempts are mapped to server responses
4. Conflict resolution favors server data for content
5. Version checking prevents stale data overwrites
"""
import json
from datetime import datetime, timezone
import logging
import uuid

from .database.session import session_scope
from .database.repository import (
    enqueue_sync,
    dequeue_pending_sync,
    mark_synced,
    mark_sync_failed,
    get_sync_queue_stats,
    get_content_version_by_number,
    create_or_update_lesson_progress,
    upsert_quiz_attempt,
    upsert_minigame_attempt,
)
from .database.models import SyncQueue
from .database import models as m

from sqlalchemy import select


logger = logging.getLogger(__name__)

VALID_LESSON_STATUSES = ("Not Started", "In Progress", "Completed")


def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("Naive datetime not allowed; use timezone-aware UTC")
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

# FK-safe apply order for upserts (parents before children).
_CONTENT_TABLES = (
    ("modules", m.Module),
    ("lessons", m.Lesson),
    ("signs", m.Sign),
    ("media_files", m.MediaFile),
    ("lesson_signs", m.LessonSign),
    ("sign_media", m.SignMedia),
    ("quizzes", m.Quiz),
    ("quiz_signs", m.QuizSign),
    ("minigames", m.Minigame),
    ("minigame_signs", m.MinigameSign),
)
_SYNCED_VERSION_KEY = "content/synced_version"

class SyncService:
    """Service for idempotent client-initiated synchronization."""

    def __init__(self, settings=None) -> None:
        self.client_version = "1.0.0"
        self._qsettings = settings   # QSettings; created lazily so tests can inject one

    def queue_quiz_attempt(
        self,
        user_id: uuid.UUID,
        attempt_id: uuid.UUID,
        quiz_id: int,
        started_at: datetime,
        completed_at: datetime,
        score: int,
        max_score: int,
        percentage: float,
        passed: bool,
        duration_seconds: int | None = None,
        camera_accuracy: float | None = None,
        mc_accuracy: float | None = None,
    ) -> uuid.UUID:
        payload = {
            "attempt_id": str(attempt_id),
            "quiz_id": quiz_id,
            "started_at": _iso_utc(started_at),
            "completed_at": _iso_utc(completed_at),
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "passed": passed,  # server recomputes this; sent for display only
            "duration_seconds": duration_seconds,
            "camera_accuracy": camera_accuracy,
            "mc_accuracy": mc_accuracy,
            "client_version": self.client_version,
        }

        with session_scope() as db:
            upsert_quiz_attempt(
                db,
                user_id=user_id,
                attempt_id=attempt_id,
                quiz_id=quiz_id,
                started_at=started_at,
                completed_at=completed_at,
                score=score,
                max_score=max_score,
                percentage=percentage,
                passed=passed,
                duration_seconds=duration_seconds,
                camera_accuracy=camera_accuracy,
                mc_accuracy=mc_accuracy,
            )
            item = enqueue_sync(
                db,
                sync_id=uuid.uuid4(),
                user_id=user_id,
                entity_type="quiz_attempt",
                entity_id=attempt_id,
                payload=payload,
                operation="upsert",
            )
            sync_id = item.sync_id

        return sync_id
    
    def queue_minigame_attempt(
        self,
        user_id: uuid.UUID,
        game_attempt_id: uuid.UUID,
        minigame_id: int,
        started_at: datetime,
        completed_at: datetime,
        score: int,
        duration_seconds: int,
        accuracy: float,
    ) -> uuid.UUID:
        """
        Save a minigame attempt locally and queue it for synchronization.

        game_attempt_id is a client-generated UUID and is also the server
        primary key, so retries are idempotent.
        """
        payload = {
            "game_attempt_id": str(game_attempt_id),
            "minigame_id": minigame_id,  # server-assigned content ID
            "started_at": _iso_utc(started_at),
            "completed_at": _iso_utc(completed_at),
            "score": score,
            "duration_seconds": duration_seconds,
            "accuracy": accuracy,
            "client_version": self.client_version,
        }

        with session_scope() as db:
            upsert_minigame_attempt(
                db,
                user_id=user_id,
                game_attempt_id=game_attempt_id,
                minigame_id=minigame_id,
                started_at=started_at,
                completed_at=completed_at,
                score=score,
                duration_seconds=duration_seconds,
                accuracy=accuracy,
            )
            item = enqueue_sync(
                db,
                sync_id=uuid.uuid4(),
                user_id=user_id,
                entity_type="minigame_attempt",
                entity_id=game_attempt_id,
                payload=payload,
                operation="upsert",
            )
            sync_id = item.sync_id
        return sync_id

    def queue_lesson_progress(
        self,
        user_id: uuid.UUID,
        lesson_id: int,
        completion_percentage: float,
        status: str,
        time_spent_seconds: int,
        client_updated_at: datetime | None = None,
    ) -> uuid.UUID:
        """
        Save lesson progress locally and queue it for synchronization.

        The key is (user_id, lesson_id). client_updated_at lets the server
        apply its merge rules (GREATEST on time/percentage, never regress
        from Completed).
        """
        if status not in VALID_LESSON_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        now = _utcnow()
        client_updated_at = client_updated_at or now

        with session_scope() as db:
            progress = create_or_update_lesson_progress(
                db, user_id=user_id, lesson_id=lesson_id,
                completion_percentage=completion_percentage, status=status,
                time_spent_seconds=time_spent_seconds,   # delta
                last_accessed=now, client_updated_at=client_updated_at,
            )
            # send absolute totals from the stored row, not this call's delta
            payload = {
                "lesson_id": lesson_id,
                "completion_percentage": progress.completion_percentage,
                "status": progress.status,
                "time_spent_seconds": progress.time_spent_seconds,
                "client_updated_at": _iso_utc(client_updated_at),
                "client_version": self.client_version,
            }
            if progress.completed_at is not None:
                payload["completed_at"] = _iso_utc(progress.completed_at)
            item = enqueue_sync(
                db, sync_id=uuid.uuid4(), user_id=user_id,
                entity_type="lesson_progress", entity_id=lesson_id,
                payload=payload, operation="upsert",
            )
            sync_id = item.sync_id
        return sync_id
    
    # Backward-compatible alias for the old name
    queue_lesson_completion = queue_lesson_progress

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_pending_syncs(self, user_id: uuid.UUID, batch_size: int = 10) -> dict:
        """
        Process pending sync items.

        In a real implementation, this would send each item (or a batch) to
        the FastAPI backend and mark it synced or failed based on the response.
        Local rows are already saved at queue time, so this step only talks
        to the server and updates queue status.
        """
        results = {"processed": 0, "succeeded": 0, "failed": 0, "errors": []}

        with session_scope() as db:
            pending_items = dequeue_pending_sync(db, limit=batch_size)

            for item in pending_items:
                results["processed"] += 1
                try:
                    if self._send_to_server(item):
                        mark_synced(db, item.sync_id)
                        results["succeeded"] += 1
                    else:
                        mark_sync_failed(db, item.sync_id, "Server rejected sync")
                        results["failed"] += 1
                        results["errors"].append(f"{item.entity_type}:{item.entity_id}")
                except Exception as e:
                    logger.exception("Sync error for %s:%s", item.entity_type, item.entity_id)
                    mark_sync_failed(db, item.sync_id, str(e))
                    results["failed"] += 1
                    results["errors"].append(f"{item.entity_type}:{item.entity_id} - {e}")

        if results["succeeded"]:
            from . import leaderboard_service  # lazy: refresh open leaderboards
            leaderboard_service.notify_scores_changed()
        return results

    def _send_to_server(self, item: SyncQueue) -> bool:
        """
        Send sync item to the FastAPI backend.
        Must not open its own SQLite session to avoid lock contention.
        """
        payload = json.loads(item.payload)
        from .config import FASTAPI_HOST, FASTAPI_PORT
        from . import auth_service
        
        token = auth_service.get_access_token()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        url = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/api/v1/sync/upload"
        req_body = {
            "user_id": str(item.user_id),
            "sync_items": [
                {
                    "entity_type": item.entity_type,
                    "client_id": str(item.entity_id),
                    "data": payload,
                    "operation": item.operation or "upsert",
                }
            ],
        }
        try:
            import requests
            resp = requests.post(url, json=req_body, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("succeeded", 0) > 0
            logger.warning("Sync upload returned status %s: %s", resp.status_code, resp.text)
            return False
        except Exception as exc:
            logger.warning("Sync upload network error: %s", exc)
            return False

    def get_sync_status(self, user_id: uuid.UUID) -> dict:
        """Get sync queue statistics for a user."""
        with session_scope() as db:
            return get_sync_queue_stats(db, user_id)

    # ------------------------------------------------------------------
    # Content sync (server -> local cache)
    # ------------------------------------------------------------------

    def _settings(self):
        if self._qsettings is None:
            from PySide6.QtCore import QSettings
            self._qsettings = QSettings("SenyaSabi", "SenyaSabi")
        return self._qsettings

    def _local_synced_version(self) -> int:
        with session_scope() as db:
            if db.scalar(select(m.Module.module_id).limit(1)) is None:
                return 0   # empty/rebuilt DB: ignore a stale marker
        try:
            return max(0, int(self._settings().value(_SYNCED_VERSION_KEY, 0)))
        except (TypeError, ValueError):
            return 0

    def sync_content_from_server(self, since_version: int | None = None) -> dict:
        """
        Pull the published content delta and merge it into SQLite.

        Blocking (network + DB): call from a worker thread, e.g. LoadingOverlay.run.
        Local user data, progress and the sync queue are never touched.
        """
        if since_version is None:
            since_version = self._local_synced_version()

        from .api_client import get_api_client
        delta = get_api_client().sync_content(since_version)
        if not isinstance(delta, dict) or not isinstance(delta.get("version"), int):
            return {"success": False, "error": "Content server unreachable or returned bad data"}

        try:
            applied = self.apply_content_delta(delta)
        except Exception as exc:
            logger.exception("Content delta could not be applied")
            return {"success": False, "error": str(exc)}

        settings = self._settings()
        settings.setValue(_SYNCED_VERSION_KEY, delta["version"])
        settings.sync()
        return {"success": True, "version": delta["version"],
                "since_version": since_version, "applied": applied}

    def apply_content_delta(self, delta: dict) -> dict:
        """Merge one /api/v1/content/sync response in a single transaction."""
        counts: dict[str, int] = {}
        version_ids: dict[int, int] = {}   # server version_number -> local content_version_id

        def local_version_id(db, number: int) -> int:
            if number not in version_ids:
                cv = db.scalar(select(m.ContentVersion)
                               .where(m.ContentVersion.version_number == number))
                if cv is None:
                    cv = m.ContentVersion(version_number=number, changelog="Synced from server",
                                          is_published=True, is_deleted=False)
                    db.add(cv)
                    db.flush()
                version_ids[number] = cv.content_version_id
            return version_ids[number]

        with session_scope() as db:
            local_version_id(db, delta["version"])

            # 1. Soft deletes first (never violate FKs; frees lesson_order slots).
            for name, model in _CONTENT_TABLES:
                for key in (delta.get(name) or {}).get("delete", []):
                    pk = tuple(key[col.key] for col in model.__mapper__.primary_key)
                    row = db.get(model, pk if len(pk) > 1 else pk[0])
                    if row is not None and not row.is_deleted:
                        row.is_deleted = True
                        counts[f"{name}_deleted"] = counts.get(f"{name}_deleted", 0) + 1
                db.flush()

            # 2. Upserts, parents before children.
            for name, model in _CONTENT_TABLES:
                rows = (delta.get(name) or {}).get("upsert", [])
                if not rows:
                    continue
                if model is m.Lesson:
                    # Park existing lessons so a reorder can't trip the partial unique index.
                    ids = [r["lesson_id"] for r in rows]
                    for lesson in db.scalars(select(m.Lesson).where(m.Lesson.lesson_id.in_(ids))):
                        lesson.lesson_order = -lesson.lesson_id
                    db.flush()
                columns = {a.key for a in model.__mapper__.column_attrs}
                for row in rows:
                    data = {k: v for k, v in row.items()
                            if k in columns and k not in ("updated_at", "content_version_id")}
                    data["content_version_id"] = local_version_id(db, row["content_version_number"])
                    data["is_deleted"] = False
                    if model is m.MediaFile:
                        sha = row.get("checksum_sha256")
                        data["checksum"] = bytes.fromhex(sha) if sha else None
                        data["object_key"] = f"media/{row['media_id']}"  # real key stays server-side
                    if "config" in columns:
                        data["config"] = row.get("config") or {}
                    db.merge(model(**data))
                db.flush()
                counts[f"{name}_upserted"] = len(rows)

            # 3. Badges: the server sends the full list every time.
            badges = delta.get("badges") or []
            for b in badges:
                db.merge(m.Badge(badge_id=b["badge_id"], badge_code=b["badge_code"],
                                 badge_name=b["badge_name"], description=b.get("description"),
                                 is_deleted=False))
            if badges:  # an empty list is more likely a server bug than "delete everything"
                keep = {b["badge_id"] for b in badges}
                for badge in db.scalars(select(m.Badge).where(m.Badge.is_deleted.is_(False))):
                    if badge.badge_id not in keep:
                        badge.is_deleted = True
            counts["badges_upserted"] = len(badges)
        return counts
    
    def handle_server_response(self, sync_id: uuid.UUID, server_response: dict) -> bool:
        """
        Handle the server's response for a sync operation.

        Records and queue rows use client-generated UUIDs that the server
        keeps, so there is no server ID to write back. This only marks the
        queue entry as synced.
        """
        try:
            with session_scope() as db:
                return bool(mark_synced(db, sync_id))
        except Exception:
            logger.exception("Error handling server response for %s", sync_id)
            return False


# Singleton instance
_sync_service = SyncService()


def queue_quiz_attempt(
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
    quiz_id: int,
    started_at: datetime,
    completed_at: datetime,
    score: int,
    max_score: int,
    percentage: float,
    passed: bool,
    duration_seconds: int | None = None,
    camera_accuracy: float | None = None,
    mc_accuracy: float | None = None,
) -> uuid.UUID:
    """Save a quiz attempt locally and queue it for synchronization."""
    return _sync_service.queue_quiz_attempt(
        user_id, attempt_id, quiz_id, started_at, completed_at,
        score, max_score, percentage, passed,
        duration_seconds=duration_seconds,
        camera_accuracy=camera_accuracy,
        mc_accuracy=mc_accuracy,
    )


def queue_minigame_attempt(
    user_id: uuid.UUID,
    game_attempt_id: uuid.UUID,
    minigame_id: int,
    started_at: datetime,
    completed_at: datetime,
    score: int,
    duration_seconds: int,
    accuracy: float,
) -> uuid.UUID:
    """Save a minigame attempt locally and queue it for synchronization."""
    return _sync_service.queue_minigame_attempt(
        user_id, game_attempt_id, minigame_id, started_at, completed_at,
        score, duration_seconds, accuracy,
    )


def queue_lesson_progress(
    user_id: uuid.UUID,
    lesson_id: int,
    completion_percentage: float,
    status: str,
    time_spent_seconds: int,
    client_updated_at: datetime | None = None,
) -> uuid.UUID:
    """Save lesson progress locally and queue it for synchronization."""
    return _sync_service.queue_lesson_progress(
        user_id, lesson_id, completion_percentage, status,
        time_spent_seconds, client_updated_at,
    )


# Backward-compatible alias for the old name
queue_lesson_completion = queue_lesson_progress


def process_pending_syncs(user_id: uuid.UUID, batch_size: int = 10) -> dict:
    """Process pending sync items."""
    return _sync_service.process_pending_syncs(user_id, batch_size)


def get_sync_status(user_id: uuid.UUID) -> dict:
    """Get sync queue statistics for a user."""
    return _sync_service.get_sync_status(user_id)


def sync_content_from_server(since_version: int | None = None) -> dict:
    """Sync content from server to local cache (blocking; use a worker thread)."""
    return _sync_service.sync_content_from_server(since_version)