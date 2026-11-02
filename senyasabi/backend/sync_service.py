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
from typing import Any, cast

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
    ("lesson_media", m.LessonMedia),
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

    def queue_user_update(
        self,
        user_id: uuid.UUID,
        display_name: str | None = None,
        notifications_enabled: bool | None = None,
        dark_mode: bool | None = None,
    ) -> uuid.UUID:
        """Queue user metadata update for synchronization."""
        sync_id = uuid.uuid4()
        payload = {
            "display_name": display_name,
            "notifications_enabled": notifications_enabled,
            "dark_mode": dark_mode,
        }
        with session_scope() as db:
            enqueue_sync(db, sync_id, user_id, cast(Any, "user"), str(user_id), payload, "upsert")
        return sync_id

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
            pending_items = dequeue_pending_sync(db, limit=batch_size, user_id=user_id)

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
        Send sync item to the server (FastAPI or Supabase).
        Must not open its own SQLite session to avoid lock contention.
        """
        from .config import CLIENT_MODE
        
        # In distributed mode: try FastAPI first, fall back to Supabase
        if CLIENT_MODE == "distributed":
            result = self._send_to_fastapi(item)
            if result:
                return True
            # FastAPI failed, try Supabase as fallback
            logger.info("FastAPI sync failed, trying Supabase fallback")
            return self._send_to_supabase(item)
        
        # In direct mode: use Supabase directly
        if CLIENT_MODE == "direct":
            return self._send_to_supabase(item)
        
        # In fastapi mode: use FastAPI backend
        return self._send_to_fastapi(item)
    

    def _send_to_fastapi(self, item: SyncQueue) -> bool:
        """Send one sync item to FastAPI using the current access token."""
        import json
        import requests

        from .config import FASTAPI_HOST, FASTAPI_PORT, API_BASE_URL
        from . import auth_service

        token = auth_service.get_access_token()
        logger.debug("Sync upload token available: %s", bool(token))

        if not token:
            logger.debug(
                "Skipping sync upload: no access token available "
                "(entity_type=%s, entity_id=%s). Item remains queued.",
                item.entity_type,
                item.entity_id,
            )
            return False

        payload = json.loads(item.payload)

        url = (
            f"{API_BASE_URL.rstrip('/')}/api/v1/sync/upload"
            if API_BASE_URL
            else f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/api/v1/sync/upload"
        )

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
        logger.info(
            "Sync request: token_present=%s, endpoint=%s",
            bool(token),
            url,
        )
        try:
            resp = requests.post(
                url,
                json=req_body,
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )

            if resp.status_code == 200:
                data = resp.json()
                succeeded = data.get("succeeded", 0)
                logger.info("FastAPI sync response: %s", data)
                return succeeded > 0

            if resp.status_code in (401, 403):
                logger.warning(
                    "Sync authentication rejected: HTTP %s. "
                    "Check token validity and FastAPI authentication. "
                    "Response: %s",
                    resp.status_code,
                    resp.text[:500],
                )
                return False

            logger.warning(
                "Sync upload failed: HTTP %s: %s",
                resp.status_code,
                resp.text[:500],
            )
            return False

        except requests.exceptions.RequestException as exc:
            logger.warning("Sync upload request failed: %s", exc)
            return False
    
    def _send_to_supabase(self, item: SyncQueue) -> bool:
        """Send sync item directly to Supabase."""
        from .sync_supabase import upload_sync
        
        payload = json.loads(item.payload)
        sync_items = [{
            "entity_type": item.entity_type,
            "client_id": str(item.entity_id),
            "data": payload,
            "operation": item.operation or "upsert",
        }]
        
        try:
            result = upload_sync(str(item.user_id), sync_items)
            if result and isinstance(result, dict):
                succeeded = result.get("succeeded", 0)
                logger.info("Supabase sync succeeded: %s items, response: %s", succeeded, result)
                return succeeded > 0
            logger.debug("Supabase sync skipped or returned no response (likely unauthenticated)")
            return False
        except Exception as exc:
            logger.debug("Supabase sync upload error: %s", exc)
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
            return max(0, int(str(self._settings().value(_SYNCED_VERSION_KEY, 0))))
        except (TypeError, ValueError):
            return 0


    def sync_content_from_server(self, since_version: int | None = None) -> dict:
        """
        Pull published content delta and merge it into SQLite.

        FastAPI and distributed modes use the FastAPI backend.
        Direct mode uses Supabase directly.
        """

        if since_version is None:
            since_version = self._local_synced_version()

        from .config import CLIENT_MODE

        try:
            # Select the correct backend
            if CLIENT_MODE == "direct":
                from .sync_supabase import sync_content
                delta = sync_content(since_version)

            elif CLIENT_MODE in ("fastapi", "distributed"):
                from .api_client import get_api_client
                delta = get_api_client().sync_content(since_version)

            else:
                logger.error("Unsupported CLIENT_MODE: %s", CLIENT_MODE)
                return {
                    "success": False,
                    "error": f"Unsupported CLIENT_MODE: {CLIENT_MODE}"
                }

            # Validate response
            if not isinstance(delta, dict):
                return {
                    "success": False,
                    "error": "Content backend returned no valid response"
                }

            version = delta.get("version")

            if not isinstance(version, int) or isinstance(version, bool):
                logger.error("Invalid content delta response: %s", delta)
                return {
                    "success": False,
                    "error": "Content server returned invalid version data"
                }

            # Apply content delta to SQLite
            logger.info(
                "Received content delta: version=%s, modules=%s, lessons=%s, signs=%s",
                delta.get("version"),
                len(delta.get("modules", {}).get("upsert", [])),
                len(delta.get("lessons", {}).get("upsert", [])),
                len(delta.get("signs", {}).get("upsert", []))
            )
            
            try:
                applied = self.apply_content_delta(delta)
                logger.info("Content successfully applied to SQLite: %s", applied)
            except Exception:
                logger.exception("Content delta could not be applied")
                return {
                    "success": False,
                    "error": "Failed to apply content delta to SQLite"
                }
            

            # Save successfully synced version
            settings = self._settings()
            settings.setValue(_SYNCED_VERSION_KEY, version)
            settings.sync()

            return {
                "success": True,
                "version": version,
                "since_version": since_version,
                "applied": applied
            }

        except Exception:
            logger.exception(
                "Content synchronization failed (mode=%s)",
                CLIENT_MODE
            )
            return {
                "success": False,
                "error": "Content synchronization failed"
            }

    def apply_content_delta(self, delta: dict) -> dict:
        """Merge one /api/v1/content/sync response in a single transaction."""
        logger.info(
            "Applying content delta: version=%s, since_version=%s",
            delta.get("version"),
            delta.get("since_version")
        )

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
            version = delta.get("version")

            if not isinstance(version, int) or isinstance(version, bool) or version < 0:
                raise ValueError(f"Invalid content version: {version}")

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

                if name == "signs":
                    sign_586 = db.get(m.Sign, 586)

                    print("\n===== SIGN SYNC DEBUG =====")
                    print("Sign 586 found:", sign_586 is not None)

                    if sign_586 is not None:
                        print("Sign ID:", sign_586.sign_id)
                        print("Sign code:", sign_586.sign_code)
                        print("Content version ID:", sign_586.content_version_id)

                    print("Sign count in transaction:",
                        db.query(m.Sign).filter(
                            m.Sign.sign_id == 586
                        ).count())

                    print("===========================\n")
                    if name == "signs":
                        sign_586 = db.get(m.Sign, 586)

                        print("\n===== SIGN SYNC DEBUG =====")
                        print("Sign 586 found:", sign_586 is not None)

                        if sign_586 is not None:
                            print("Sign ID:", sign_586.sign_id)
                            print("Sign code:", sign_586.sign_code)
                            print("Content version ID:", sign_586.content_version_id)

                        print("Sign count in transaction:",
                            db.query(m.Sign).filter(
                                m.Sign.sign_id == 586
                            ).count())

                    print("===========================\n")

                logger.info(
                    "Content sync: %s - %s records upserted",
                    name,
                    len(rows)
                )

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

            logger.info("Content delta successfully applied: %s", counts)
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

def queue_user_update(
    user_id: uuid.UUID,
    display_name: str | None = None,
    notifications_enabled: bool | None = None,
    dark_mode: bool | None = None,
) -> uuid.UUID:
    """Queue user metadata update for synchronization."""
    return _sync_service.queue_user_update(
        user_id, display_name, notifications_enabled, dark_mode
    )

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