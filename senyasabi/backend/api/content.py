"""Content sync API: published-version deltas."""
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from ..database.postgre_session import get_postgres_session

router = APIRouter(prefix="/api/v1/content", tags=["content"])

# table -> (columns sent to the client, primary-key columns)
_DELTA_TABLES = {
    "modules": (("module_id", "module_code", "title", "description",
                 "module_order", "is_active"), ("module_id",)),
    "lessons": (("lesson_id", "lesson_code", "title", "description",
                 "parent_module", "lesson_order", "is_active"), ("lesson_id",)),
    "signs": (("sign_id", "sign_code", "label", "recognition_label"), ("sign_id",)),
    # object_key is intentionally omitted; checksum lets clients invalidate caches
    "media_files": (("media_id", "file_name", "media_type", "width", "height",
                     "duration_seconds", "file_size", "checksum"), ("media_id",)),
    "lesson_signs": (("lesson_id", "sign_id", "display_order"), ("lesson_id", "sign_id")),
    "sign_media": (("sign_id", "media_id", "media_role", "display_order"),
                   ("sign_id", "media_id", "media_role")),
    "lesson_media": (("lesson_id", "media_id", "media_role", "display_order"),
                     ("lesson_id", "media_id", "media_role")),
    "quizzes": (("quiz_id", "quiz_code", "module_id", "category_code", "title",
                 "passing_score", "time_limit_seconds", "config"), ("quiz_id",)),
    "quiz_signs": (("quiz_id", "sign_id", "display_order"), ("quiz_id", "sign_id")),
    "minigames": (("minigame_id", "minigame_code", "game_name", "game_type",
                   "module_id", "description", "config"), ("minigame_id",)),
    "minigame_signs": (("minigame_id", "sign_id"), ("minigame_id", "sign_id")),
}

_CURRENT_VERSION_SQL = """
SELECT content_version_id, version_number, released_at, changelog
FROM public.content_versions
WHERE is_published AND NOT is_deleted
ORDER BY version_number DESC
LIMIT 1
"""


def _current_version(db):
    row = db.execute(text(_CURRENT_VERSION_SQL)).mappings().first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No published content version found")
    return row


def _changed_rows(db, table: str, since: int, current: int) -> dict:
    cols, keys = _DELTA_TABLES[table]
    select = ", ".join(f"t.{c}" for c in cols)
    rows = db.execute(text(f"""
        SELECT {select}, t.is_deleted, t.updated_at,
               cv.version_number AS content_version_number
        FROM public.{table} t
        JOIN public.content_versions cv
          ON cv.content_version_id = t.content_version_id
        WHERE cv.version_number > :since
          AND cv.version_number <= :current
          AND cv.is_published AND NOT cv.is_deleted
    """), {"since": since, "current": current}).mappings().all()

    upsert, delete = [], []
    for r in rows:
        r = dict(r)
        deleted = r.pop("is_deleted")
        if deleted:
            if since > 0:  # a fresh client has nothing to delete
                delete.append({k: r[k] for k in keys})
        else:
            if isinstance(r.get("checksum"), (bytes, memoryview)):
                r["checksum_sha256"] = bytes(r.pop("checksum")).hex()
            upsert.append(r)
    return {"upsert": upsert, "delete": delete}


@router.get("/version")
def get_current_version():
    with get_postgres_session() as db:
        v = _current_version(db)
    return jsonable_encoder({
        "version": v["version_number"],
        "content_version_id": v["content_version_id"],
        "released_at": v["released_at"],
        "changelog": v["changelog"],
    })


@router.get("/sync")
def sync_content(since_version: int = 0):
    if since_version < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "since_version must be >= 0")
    with get_postgres_session() as db:
        current = _current_version(db)["version_number"]
        if since_version >= current:
            return {"version": current, "since_version": since_version,
                    **{t: {"upsert": [], "delete": []} for t in _DELTA_TABLES},
                    "badges": []}
        body = {t: _changed_rows(db, t, since_version, current) for t in _DELTA_TABLES}
        badges = db.execute(text(
            "SELECT badge_id, badge_code, badge_name, description "
            "FROM public.badges WHERE NOT is_deleted ORDER BY badge_id"
        )).mappings().all()
    return jsonable_encoder({"version": current, "since_version": since_version,
                             **body, "badges": [dict(b) for b in badges]})