import logging

from sqlalchemy import text

from ..database.postgre_session import get_postgres_session

logger = logging.getLogger(__name__)


# Use only fixed, application-controlled table and column names here.
# The primary keys must match the PostgreSQL schema.
SNAPSHOT_TABLES = {
    "modules": {
        "columns": (
            "module_id", "module_code", "title", "description",
            "module_order", "is_active",
        ),
        "primary_key": ("module_id",),
        "active_column": "is_active",
    },
    "lessons": {
        "columns": (
            "lesson_id", "lesson_code", "title", "description",
            "parent_module", "lesson_order", "is_active",
        ),
        "primary_key": ("lesson_id",),
        "active_column": "is_active",
    },
    "signs": {
        "columns": (
            "sign_id", "sign_code", "label", "recognition_label",
        ),
        "primary_key": ("sign_id",),
    },
    "media_files": {
        "columns": (
            "media_id", "file_name", "media_type", "width", "height",
            "duration_seconds", "file_size", "checksum",
        ),
        "primary_key": ("media_id",),
    },
    "lesson_signs": {
        "columns": ("lesson_id", "sign_id", "display_order"),
        "primary_key": ("lesson_id", "sign_id"),
    },
    "sign_media": {
        "columns": ("sign_id", "media_id", "media_role", "display_order"),
        "primary_key": ("sign_id", "media_id", "media_role"),
    },
    "lesson_media": {
        "columns": ("lesson_id", "media_id", "media_role", "display_order"),
        "primary_key": ("lesson_id", "media_id", "media_role"),
    },
    "quizzes": {
        "columns": (
            "quiz_id", "quiz_code", "module_id", "category_code", "title",
            "passing_score", "time_limit_seconds", "config",
        ),
        "primary_key": ("quiz_id",),
    },
    "quiz_signs": {
        "columns": ("quiz_id", "sign_id", "display_order"),
        "primary_key": ("quiz_id", "sign_id"),
    },
    "minigames": {
        "columns": (
            "minigame_id", "minigame_code", "game_name", "game_type",
            "module_id", "description", "config",
        ),
        "primary_key": ("minigame_id",),
    },
    "minigame_signs": {
        "columns": ("minigame_id", "sign_id"),
        "primary_key": ("minigame_id", "sign_id"),
    },
}


def _latest_published_rows(db, table_name: str, spec: dict) -> list[dict]:
    """Return the latest published revision of each record, if still active."""
    columns = spec["columns"]
    primary_key = spec["primary_key"]
    active_column = spec.get("active_column")

    selected_columns = ", ".join(f"t.{c}" for c in columns)
    partition_columns = ", ".join(f"t.{c}" for c in primary_key)

    # Both identifiers are sourced from the fixed SNAPSHOT_TABLES constant.
    active_filter = (
        f"AND COALESCE(is_active, FALSE) = TRUE"
        if active_column
        else ""
    )

    query = text(f"""
        WITH ranked AS (
            SELECT
                {selected_columns},
                t.is_deleted,
                {"t.is_active," if active_column else ""}
                cv.version_number AS content_version_number,
                ROW_NUMBER() OVER (
                    PARTITION BY {partition_columns}
                    ORDER BY cv.version_number DESC,
                             t.updated_at DESC
                ) AS revision_rank
            FROM public.{table_name} AS t
            JOIN public.content_versions AS cv
              ON cv.content_version_id = t.content_version_id
            WHERE cv.is_published = TRUE
              AND cv.is_deleted = FALSE
        )
        SELECT *
        FROM ranked
        WHERE revision_rank = 1
          AND COALESCE(is_deleted, FALSE) = FALSE
          {active_filter}
        ORDER BY {", ".join(primary_key)}
    """)

    return [dict(row) for row in db.execute(query).mappings().all()]


def fetch_published_content_snapshot() -> dict:
    """Fetch the published release and its latest active content records."""
    try:
        with get_postgres_session() as db:
            version = db.execute(text("""
                SELECT content_version_id, version_number,
                       released_at, changelog
                FROM public.content_versions
                WHERE is_published = TRUE
                  AND is_deleted = FALSE
                ORDER BY version_number DESC
                LIMIT 1
            """)).mappings().first()

            if version is None:
                raise RuntimeError(
                    "PostgreSQL has no published, non-deleted content version."
                )

            tables = {
                name: _latest_published_rows(db, name, spec)
                for name, spec in SNAPSHOT_TABLES.items()
            }

            # The existing Badge model has no content_version_id. Its
            # historical revision-selection rules are not shown in scripts.md.
            badges = [
                dict(row)
                for row in db.execute(text("""
                    SELECT badge_id, badge_code, badge_name, description
                    FROM public.badges
                    WHERE is_deleted = FALSE
                    ORDER BY badge_id
                """)).mappings().all()
            ]

            snapshot = {
                "version": int(version["version_number"]),
                "server_content_version_id": int(version["content_version_id"]),
                "released_at": version["released_at"],
                "changelog": version["changelog"],
                "tables": tables,
                "badges": badges,
            }

        logger.info(
            "Fetched published content snapshot: version=%s, counts=%s",
            snapshot["version"],
            {name: len(rows) for name, rows in tables.items()},
        )
        return snapshot

    except Exception as exc:
        logger.exception("Could not fetch the published PostgreSQL content snapshot")
        raise RuntimeError(
            "Content snapshot fetch failed. Check DATABASE_URL, PostgreSQL "
            "connectivity, published content versions, and the content schema."
        ) from exc