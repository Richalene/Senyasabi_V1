import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, text

from .config import POSTGRESQL_URL
from .database.postgre_session import get_postgres_session
from .database.session import session_scope
from .database import models as m

logger = logging.getLogger(__name__)


# This is the same dependency order used by the existing desktop delta applier.
UPSERT_ORDER = (
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

# Reverse dependency order is important when soft-deleting the old snapshot.
DELETE_ORDER = tuple(reversed(UPSERT_ORDER))

# The public PostgreSQL columns intentionally match the existing delta API.
# object_key is omitted to preserve the existing local media-key convention.
TABLE_COLUMNS = {
    "modules": (
        "module_id", "module_code", "title", "description",
        "module_order", "is_active",
    ),
    "lessons": (
        "lesson_id", "lesson_code", "title", "description",
        "parent_module", "lesson_order", "is_active",
    ),
    "signs": (
        "sign_id", "sign_code", "label", "recognition_label",
    ),
    "media_files": (
        "media_id", "file_name", "media_type", "width", "height",
        "duration_seconds", "file_size", "checksum",
    ),
    "lesson_signs": ("lesson_id", "sign_id", "display_order"),
    "sign_media": (
        "sign_id", "media_id", "media_role", "display_order",
    ),
    "lesson_media": (
        "lesson_id", "media_id", "media_role", "display_order",
    ),
    "quizzes": (
        "quiz_id", "quiz_code", "module_id", "category_code", "title",
        "passing_score", "time_limit_seconds", "config",
    ),
    "quiz_signs": ("quiz_id", "sign_id", "display_order"),
    "minigames": (
        "minigame_id", "minigame_code", "game_name", "game_type",
        "module_id", "description", "config",
    ),
    "minigame_signs": ("minigame_id", "sign_id"),
}

# Content-versioned tables in the provided PostgreSQL schema.
VERSIONED_TABLES = frozenset(TABLE_COLUMNS)

def _remove_orphaned_snapshot_rows(tables: dict) -> None:
    """Remove associations whose required parent is absent from the snapshot."""

    module_ids = {r["module_id"] for r in tables["modules"]}
    lesson_ids = {r["lesson_id"] for r in tables["lessons"]}
    sign_ids = {r["sign_id"] for r in tables["signs"]}
    media_ids = {r["media_id"] for r in tables["media_files"]}
    quiz_ids = {r["quiz_id"] for r in tables["quizzes"]}
    minigame_ids = {r["minigame_id"] for r in tables["minigames"]}

    # First, remove children whose parent modules are not in the snapshot.
    tables["lessons"] = [
        r for r in tables["lessons"]
        if r["parent_module"] in module_ids
    ]

    tables["quizzes"] = [
        r for r in tables["quizzes"]
        if r["module_id"] in module_ids
    ]

    tables["minigames"] = [
        r for r in tables["minigames"]
        if r["module_id"] in module_ids
    ]

    # Recalculate lesson IDs after filtering.
    lesson_ids = {r["lesson_id"] for r in tables["lessons"]}

    # Filter every association table against all its required parents.
    tables["lesson_signs"] = [
        r for r in tables["lesson_signs"]
        if r["lesson_id"] in lesson_ids
        and r["sign_id"] in sign_ids
    ]

    tables["sign_media"] = [
        r for r in tables["sign_media"]
        if r["sign_id"] in sign_ids
        and r["media_id"] in media_ids
    ]

    tables["lesson_media"] = [
        r for r in tables["lesson_media"]
        if r["lesson_id"] in lesson_ids
        and r["media_id"] in media_ids
    ]

    tables["quiz_signs"] = [
        r for r in tables["quiz_signs"]
        if r["quiz_id"] in quiz_ids
        and r["sign_id"] in sign_ids
    ]

    tables["minigame_signs"] = [
        r for r in tables["minigame_signs"]
        if r["minigame_id"] in minigame_ids
        and r["sign_id"] in sign_ids
    ]

def _fetch_snapshot() -> dict:
    """Read one consistent published snapshot from PostgreSQL."""
    if not POSTGRESQL_URL:
        raise RuntimeError(
            "Cannot synchronize initial content: POSTGRESQL_URL is not configured."
        )

    with get_postgres_session() as db:
        # Keep the version and all table reads in one PostgreSQL transaction.
        # REPEATABLE READ ensures they see the same committed database snapshot.
        db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))

        version = db.execute(text("""
            SELECT content_version_id, version_number, released_at, changelog
            FROM public.content_versions
            WHERE is_published = TRUE
              AND is_deleted = FALSE
            ORDER BY version_number DESC
            LIMIT 1
        """)).mappings().first()

        if version is None:
            raise RuntimeError(
                "PostgreSQL is reachable, but no published, non-deleted "
                "content version exists."
            )

        current_version = int(version["version_number"])
        tables = {}

        for table, columns in TABLE_COLUMNS.items():
            selected = ", ".join(f"t.{column}" for column in columns)

            active_clause = (
                "AND t.is_active = TRUE"
                if table in ("modules", "lessons")
                else ""
            )

            rows = db.execute(text(f"""
                SELECT {selected},
                       cv.version_number AS content_version_number
                FROM public.{table} AS t
                JOIN public.content_versions AS cv
                  ON cv.content_version_id = t.content_version_id
                WHERE cv.is_published = TRUE
                  AND cv.is_deleted = FALSE
                  AND cv.version_number <= :current_version
                  AND t.is_deleted = FALSE
                  {active_clause}
                ORDER BY {", ".join("t." + c for c in columns
                                    if c.endswith("_id"))}
            """), {"current_version": current_version}).mappings().all()

            records = [dict(row) for row in rows]

            # Match the checksum format accepted by the existing sync applier.
            if table == "media_files":
                for record in records:
                    checksum = record.pop("checksum", None)
                    record["checksum_sha256"] = (
                        bytes(checksum).hex() if checksum is not None else None
                    )

            tables[table] = records

        _remove_orphaned_snapshot_rows(tables)

        badges = db.execute(text("""
            SELECT badge_id, badge_code, badge_name, description
            FROM public.badges
            WHERE is_deleted = FALSE
            ORDER BY badge_id
        """)).mappings().all()

        snapshot = {
            "version": current_version,
            "server_content_version_id": int(version["content_version_id"]),
            "released_at": version["released_at"],
            "changelog": version["changelog"],
            "tables": tables,
            "badges": [dict(row) for row in badges],
        }

    logger.info(
        "Fetched PostgreSQL content version %s; row counts: %s",
        snapshot["version"],
        {name: len(rows) for name, rows in tables.items()},
    )
    return snapshot


def _apply_snapshot(snapshot: dict) -> dict:
    """Replace local content in one SQLite transaction; preserve server IDs."""
    version_number = snapshot["version"]
    counts = {}

    with session_scope() as db:
        # Map logical release number to the local SQLite FK.
        # Never copy server_content_version_id into local foreign keys.
        local_version = db.scalar(
            select(m.ContentVersion).where(
                m.ContentVersion.version_number == version_number
            )
        )

        if local_version is None:
            local_version = m.ContentVersion(
                version_number=version_number,
                released_at=snapshot["released_at"],
                changelog=snapshot["changelog"],
                is_published=True,
                is_deleted=False,
            )
            db.add(local_version)
            db.flush()
        else:
            local_version.released_at = snapshot["released_at"]
            local_version.changelog = snapshot["changelog"]
            local_version.is_published = True
            local_version.is_deleted = False
            db.flush()

        local_version_id = local_version.content_version_id

        # Mark all existing content as deleted first. This preserves rows
        # referenced by progress/attempts and frees lesson-order slots.
        for table, model in DELETE_ORDER:
            result = db.execute(
                model.__table__.update().values(is_deleted=True)
            )
            counts[f"{table}_retired"] = result.rowcount or 0

        db.flush()

        # Upsert in parent-before-child order.
        for table, model in UPSERT_ORDER:
            records = snapshot["tables"][table]
            mapped_columns = {
                attr.key for attr in model.__mapper__.column_attrs
            }
            primary_key_columns = {
                col.key for col in model.__mapper__.primary_key
            }

            for record in records:
                data = {
                    key: value
                    for key, value in record.items()
                    if key in mapped_columns
                    and key not in ("updated_at", "content_version_id")
                }

                data["content_version_id"] = local_version_id
                data["is_deleted"] = False

                if table == "media_files":
                    checksum_hex = record.get("checksum_sha256")
                    data["checksum"] = (
                        bytes.fromhex(checksum_hex) if checksum_hex else None
                    )
                    # Keep the same local key convention as the existing
                    # desktop delta applier. This is not the storage object key.
                    data["object_key"] = f"media/{record['media_id']}"

                if "config" in mapped_columns:
                    data["config"] = record.get("config") or {}

                identity = tuple(data[col] for col in primary_key_columns)
                identity = identity[0] if len(identity) == 1 else identity
                existing = db.get(model, identity)

                if existing is None:
                    db.add(model(**data))
                else:
                    for key, value in data.items():
                        setattr(existing, key, value)

            # Flush after each table so its parent records exist before
            # dependent records are written.
            local_version_id = local_version.content_version_id
            db.flush()
            counts[f"{table}_upserted"] = len(records)

        # Badges have no content_version_id in the provided schema.
        db.execute(m.Badge.__table__.update().values(is_deleted=True))
        for record in snapshot["badges"]:
            badge = db.get(m.Badge, record["badge_id"])
            if badge is None:
                badge = m.Badge(**record, is_deleted=False)
                db.add(badge)
            else:
                badge.badge_code = record["badge_code"]
                badge.badge_name = record["badge_name"]
                badge.description = record.get("description")
                badge.is_deleted = False
        db.flush()
        counts["badges_upserted"] = len(snapshot["badges"])

    # session_scope has committed successfully when execution reaches here.
    return counts


def _save_sync_marker(version_number: int) -> None:
    """
    Persist the last successfully applied startup snapshot.

    This marker is intentionally written only after the content transaction
    commits. It is not SQLite PRAGMA user_version, which tracks schema version.
    """
    with session_scope() as db:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS content_sync_state (
                state_key TEXT PRIMARY KEY,
                version_number INTEGER NOT NULL,
                synced_at TEXT NOT NULL
            )
        """))
        db.execute(text("""
            INSERT INTO content_sync_state (state_key, version_number, synced_at)
            VALUES ('published_content', :version, :synced_at)
            ON CONFLICT(state_key) DO UPDATE SET
                version_number = excluded.version_number,
                synced_at = excluded.synced_at
        """), {
            "version": version_number,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        })


def _verify_snapshot(snapshot: dict, counts: dict) -> None:
    """Check basic post-commit invariants and report actionable failures."""
    with session_scope() as db:
        local_version = db.scalar(
            select(m.ContentVersion).where(
                m.ContentVersion.version_number == snapshot["version"]
            )
        )
        if local_version is None:
            raise RuntimeError(
                f"SQLite verification failed: content version "
                f"{snapshot['version']} was not committed."
            )

        for table, model in UPSERT_ORDER:
            expected = len(snapshot["tables"][table])
            actual = db.scalar(
                select(text("COUNT(*)")).select_from(model.__table__).where(
                    model.is_deleted.is_(False)
                )
            )
            if actual != expected:
                raise RuntimeError(
                    f"SQLite verification failed for {table}: "
                    f"expected {expected} active rows, found {actual}."
                )

        fk_errors = db.execute(text("PRAGMA foreign_key_check")).all()
        if fk_errors:
            raise RuntimeError(
                "SQLite foreign-key verification failed; "
                f"first violations: {fk_errors[:5]}"
            )


def _sync_startup_content() -> int:
    """Fetch, apply, verify, and then record the published release."""
    snapshot = _fetch_snapshot()

    try:
        counts = _apply_snapshot(snapshot)
    except Exception as exc:
        logger.exception(
            "SQLite full-snapshot transaction failed for content version %s",
            snapshot["version"],
        )
        raise RuntimeError(
            f"Could not apply PostgreSQL content version {snapshot['version']} "
            "to SQLite. The content transaction was rolled back."
        ) from exc

    _verify_snapshot(snapshot, counts)

    # Only save the marker after the content transaction and verification pass.
    _save_sync_marker(snapshot["version"])

    logger.info(
        "Startup content sync succeeded: version=%s counts=%s",
        snapshot["version"],
        counts,
    )
    return snapshot["version"]


async def ensure_initial_content() -> None:
    """
    Async entry point used by main.py's FastAPI lifespan.

    SQLAlchemy here is synchronous, so keep blocking database work off the
    event loop.
    """
    try:
        version = await asyncio.to_thread(_sync_startup_content)
    except Exception as exc:
        logger.exception("Initial PostgreSQL-to-SQLite content sync failed")
        raise RuntimeError(
            "Initial content synchronization failed. Verify PostgreSQL "
            "configuration/connectivity, the published content release, "
            "and SQLite schema/migrations. See the preceding exception "
            "for the exact database error."
        ) from exc

    logger.info("Initial content sync completed at version %s", version)
