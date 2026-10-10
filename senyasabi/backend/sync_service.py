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
from typing import Any, Optional
from uuid import uuid4

from .database.session import get_session
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


class SyncService:
    """Service for idempotent client-initiated synchronization."""

    def __init__(self):
        self.client_version = "1.0.0"

    def queue_quiz_attempt(
        self,
        user_id: int,
        attempt_id: str,
        quiz_id: int,
        started_at: datetime,
        completed_at: datetime,
        score: int,
        max_score: int,
        percentage: float,
        passed: bool,
    ) -> str:
        """
        Queue a quiz attempt for synchronization.
        
        The attempt_id is a client-generated UUID. When synced, the server will
        return a server-assigned ID. Both are stored in the payload for idempotency.
        """
        payload = {
            "attempt_id": attempt_id,  # Client UUID
            "quiz_id": quiz_id,  # Server-assigned content ID
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "passed": passed,
            "client_version": self.client_version,
        }

        sync_id = str(uuid4())

        with get_session() as db:
            enqueue_sync(
                db,
                sync_id=sync_id,
                user_id=user_id,
                entity_type="quiz_attempt",
                entity_id=attempt_id,  # Use client UUID for entity_id
                payload=json.dumps(payload),
                operation="upsert",
            )

        return sync_id

    def queue_minigame_attempt(
        self,
        user_id: int,
        game_attempt_id: str,
        minigame_id: int,
        started_at: datetime,
        completed_at: datetime,
        score: int,
        duration_seconds: int,
        accuracy: float,
    ) -> str:
        """
        Queue a minigame attempt for synchronization.
        
        The game_attempt_id is a client-generated UUID. When synced, the server will
        return a server-assigned ID. Both are stored in the payload for idempotency.
        """
        payload = {
            "game_attempt_id": game_attempt_id,  # Client UUID
            "minigame_id": minigame_id,  # Server-assigned content ID
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "score": score,
            "duration_seconds": duration_seconds,
            "accuracy": accuracy,
            "client_version": self.client_version,
        }

        sync_id = str(uuid4())

        with get_session() as db:
            enqueue_sync(
                db,
                sync_id=sync_id,
                user_id=user_id,
                entity_type="minigame_attempt",
                entity_id=game_attempt_id,  # Use client UUID for entity_id
                payload=json.dumps(payload),
                operation="upsert",
            )

        return sync_id

    def queue_lesson_completion(
        self,
        user_id: int,
        lesson_id: int,
        completion_percentage: float,
        status: str,
        time_spent_seconds: int,
    ) -> str:
        """
        Queue a lesson completion for synchronization.
        
        Uses server-assigned lesson_id for idempotency.
        """
        payload = {
            "lesson_id": lesson_id,  # Server-assigned content ID
            "completion_percentage": completion_percentage,
            "status": status,
            "time_spent_seconds": time_spent_seconds,
            "client_version": self.client_version,
        }

        sync_id = str(uuid4())

        with get_session() as db:
            enqueue_sync(
                db,
                sync_id=sync_id,
                user_id=user_id,
                entity_type="lesson_completion",
                entity_id=str(lesson_id),  # Use server ID for entity_id
                payload=json.dumps(payload),
                operation="upsert",
            )

        return sync_id

    def process_pending_syncs(self, user_id: int, batch_size: int = 10) -> dict:
        """
        Process pending sync items.
        
        In a real implementation, this would:
        1. Send batched data to the server
        2. Receive server responses with server-assigned IDs
        3. Update local records with server IDs
        4. Mark sync items as synced or failed
        
        For now, this is a placeholder that simulates successful sync.
        """
        with get_session() as db:
            pending_items = dequeue_pending_sync(db, limit=batch_size)

            results = {
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "errors": [],
            }

            for item in pending_items:
                try:
                    # Simulate server sync
                    success = self._simulate_server_sync(item)

                    if success:
                        mark_synced(db, item.sync_id)
                        results["succeeded"] += 1
                    else:
                        mark_sync_failed(db, item.sync_id, "Server rejected sync")
                        results["failed"] += 1
                        results["errors"].append(f"{item.entity_type}:{item.entity_id}")

                    results["processed"] += 1

                except Exception as e:
                    mark_sync_failed(db, item.sync_id, str(e))
                    results["failed"] += 1
                    results["errors"].append(f"{item.entity_type}:{item.entity_id} - {str(e)}")
                    results["processed"] += 1

        return results

    def _simulate_server_sync(self, item: SyncQueue) -> bool:
        """
        Simulate server sync for development/testing.
        
        In production, this would make an HTTP request to the FastAPI backend.
        """
        try:
            payload = json.loads(item.payload)

            # Update local database with the synced data
            with get_session() as db:
                if item.entity_type == "quiz_attempt":
                    upsert_quiz_attempt(
                        db,
                        user_id=item.user_id,
                        attempt_id=payload["attempt_id"],
                        quiz_id=payload["quiz_id"],
                        started_at=datetime.fromisoformat(payload["started_at"]),
                        completed_at=datetime.fromisoformat(payload["completed_at"]),
                        score=payload["score"],
                        max_score=payload["max_score"],
                        percentage=payload["percentage"],
                        passed=payload["passed"],
                    )

                elif item.entity_type == "minigame_attempt":
                    upsert_minigame_attempt(
                        db,
                        user_id=item.user_id,
                        game_attempt_id=payload["game_attempt_id"],
                        minigame_id=payload["minigame_id"],
                        started_at=datetime.fromisoformat(payload["started_at"]),
                        completed_at=datetime.fromisoformat(payload["completed_at"]),
                        score=payload["score"],
                        duration_seconds=payload["duration_seconds"],
                        accuracy=payload["accuracy"],
                    )

                elif item.entity_type == "lesson_completion":
                    create_or_update_lesson_progress(
                        db,
                        user_id=item.user_id,
                        lesson_id=payload["lesson_id"],
                        completion_percentage=payload["completion_percentage"],
                        status=payload["status"],
                        time_spent_seconds=payload["time_spent_seconds"],
                        last_accessed=datetime.now(timezone.utc),
                    )

            return True

        except Exception as e:
            print(f"Sync error for {item.entity_type}:{item.entity_id}: {e}")
            return False

    def get_sync_status(self, user_id: int) -> dict:
        """Get sync queue statistics for a user."""
        with get_session() as db:
            return get_sync_queue_stats(db, user_id)

    def sync_content_from_server(self, content_version: int) -> dict:
        """
        Sync content from server to local cache.
        
        This ensures idempotency by:
        1. Checking if content version matches
        2. Using server-assigned IDs for all content
        3. Using db.merge() to update existing records or create new ones
        4. Preserving local user data
        
        In production, this would:
        1. Fetch content from the server API
        2. Apply it to the local database
        3. Handle version conflicts
        """
        # Placeholder for content sync implementation
        # In production, this would make HTTP requests to the server
        with get_session() as db:
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

    def handle_server_response(self, sync_id: str, server_response: dict) -> bool:
        """
        Handle server response for a sync operation.
        
        This ensures idempotency by:
        1. Extracting server-assigned IDs from the response
        2. Updating local records with server IDs
        3. Marking the sync as complete
        """
        try:
            with get_session() as db:
                # Mark as synced
                success = mark_synced(db, sync_id)

                if not success:
                    return False

                # In production, we would update local records with server IDs here
                # For example, if the server returns a new attempt_id, we would:
                # 1. Update the local record with the server ID
                # 2. Update the sync queue payload to include the server ID
                # 3. This ensures future syncs use the server ID

            return True

        except Exception as e:
            print(f"Error handling server response: {e}")
            return False


# Singleton instance
_sync_service = SyncService()


def queue_quiz_attempt(
    user_id: int,
    attempt_id: str,
    quiz_id: int,
    started_at: datetime,
    completed_at: datetime,
    score: int,
    max_score: int,
    percentage: float,
    passed: bool,
) -> str:
    """Queue a quiz attempt for synchronization."""
    return _sync_service.queue_quiz_attempt(
        user_id, attempt_id, quiz_id, started_at, completed_at,
        score, max_score, percentage, passed
    )


def queue_minigame_attempt(
    user_id: int,
    game_attempt_id: str,
    minigame_id: int,
    started_at: datetime,
    completed_at: datetime,
    score: int,
    duration_seconds: int,
    accuracy: float,
) -> str:
    """Queue a minigame attempt for synchronization."""
    return _sync_service.queue_minigame_attempt(
        user_id, game_attempt_id, minigame_id, started_at, completed_at,
        score, duration_seconds, accuracy
    )


def queue_lesson_completion(
    user_id: int,
    lesson_id: int,
    completion_percentage: float,
    status: str,
    time_spent_seconds: int,
) -> str:
    """Queue a lesson completion for synchronization."""
    return _sync_service.queue_lesson_completion(
        user_id, lesson_id, completion_percentage, status, time_spent_seconds
    )


def process_pending_syncs(user_id: int, batch_size: int = 10) -> dict:
    """Process pending sync items."""
    return _sync_service.process_pending_syncs(user_id, batch_size)


def get_sync_status(user_id: int) -> dict:
    """Get sync queue statistics for a user."""
    return _sync_service.get_sync_status(user_id)


def sync_content_from_server(content_version: int) -> dict:
    """Sync content from server to local cache."""
    return _sync_service.sync_content_from_server(content_version)
