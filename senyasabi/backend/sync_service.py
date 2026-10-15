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

logger = logging.getLogger(__name__)

VALID_LESSON_STATUSES = ("Not Started", "In Progress", "Completed")


def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ValueError("Naive datetime not allowed; use timezone-aware UTC")
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SyncService:
    """Service for idempotent client-initiated synchronization."""

    def __init__(self) -> None:
        self.client_version = "1.0.0"

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
    ) -> uuid.UUID:
        """
        Save a quiz attempt locally and queue it for synchronization.

        attempt_id is a client-generated UUID and is also the server primary
        key, so retries upsert the same row and no ID remapping is needed.
        """
        payload = {
            "attempt_id": str(attempt_id),
            "quiz_id": quiz_id,  # server-assigned content ID
            "started_at": _iso_utc(started_at),
            "completed_at": _iso_utc(completed_at),
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "passed": passed,  # server recomputes this; sent for display only
            "client_version": self.client_version,
        }

        sync_id = uuid.uuid4()

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
            )
            enqueue_sync(
                db,
                sync_id=sync_id,
                user_id=user_id,
                entity_type="quiz_attempt",
                entity_id=attempt_id,
                payload=payload,
                operation="upsert",
            )

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

        sync_id = uuid.uuid4()

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
            enqueue_sync(
                db,
                sync_id=sync_id,
                user_id=user_id,
                entity_type="minigame_attempt",
                entity_id=game_attempt_id,
                payload=payload,
                operation="upsert",
            )

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

        payload = {
            "lesson_id": lesson_id,  # server-assigned content ID
            "completion_percentage": completion_percentage,
            "status": status,
            "time_spent_seconds": time_spent_seconds,
            "client_updated_at": _iso_utc(client_updated_at),
            "client_version": self.client_version,
        }
        if status == "Completed":
            # Server CHECK requires completed_at when status is Completed
            payload["completed_at"] = _iso_utc(now)

        sync_id = uuid.uuid4()

        with session_scope() as db:
            create_or_update_lesson_progress(
                db,
                user_id=user_id,
                lesson_id=lesson_id,
                completion_percentage=completion_percentage,
                status=status,
                time_spent_seconds=time_spent_seconds,
                last_accessed=now,
            )
            enqueue_sync(
                db,
                sync_id=sync_id,
                user_id=user_id,
                entity_type="lesson_progress",
                entity_id=lesson_id,  # enqueue_sync converts to str
                payload=payload,
                operation="upsert",
            )

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

        return results

    def _send_to_server(self, item: SyncQueue) -> bool:
        """
        Placeholder for the HTTP call to the FastAPI backend.

        It must not open its own session: the caller's session is already
        in a transaction, and a second writer on SQLite can hit
        "database is locked". Replace the body with the real request.
        """
        payload = json.loads(item.payload)  # validates the stored JSON
        logger.debug("Would send %s %s: %s", item.entity_type, item.entity_id, payload)
        return True

    def get_sync_status(self, user_id: uuid.UUID) -> dict:
        """Get sync queue statistics for a user."""
        with session_scope() as db:
            return get_sync_queue_stats(db, user_id)

    def sync_content_from_server(self, content_version: int) -> dict:
        """
        Sync content from the server to the local cache (placeholder).

        In production this would fetch content from the server API and upsert
        it using server-assigned IDs (db.merge), leaving local user data
        untouched.
        """
        with session_scope() as db:
            version = get_content_version_by_number(db, content_version)
            if version is None:
                return {
                    "success": False,
                    "error": f"Content version {content_version} not found locally",
                }

        return {
            "success": True,
            "message": f"Content version {content_version} is already synced",
            "version": content_version,
        }

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
) -> uuid.UUID:
    """Save a quiz attempt locally and queue it for synchronization."""
    return _sync_service.queue_quiz_attempt(
        user_id, attempt_id, quiz_id, started_at, completed_at,
        score, max_score, percentage, passed,
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


def sync_content_from_server(content_version: int) -> dict:
    """Sync content from server to local cache."""
    return _sync_service.sync_content_from_server(content_version)