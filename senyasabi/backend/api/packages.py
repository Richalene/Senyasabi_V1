"""Content package API: nested module/lesson/sign/media packages and minigame config."""
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from ..database.postgre_session import get_postgres_session

router = APIRouter(prefix="/api/v1/packages", tags=["packages"])

_MODULE_SQL = """
SELECT module_id, module_code, title, description, module_order
FROM public.modules
WHERE lower(module_code) = lower(:module_code) AND is_active AND NOT is_deleted
"""

_LESSONS_SQL = """
SELECT lesson_id, lesson_code, title, description, lesson_order
FROM public.lessons
WHERE parent_module = :module_id AND is_active AND NOT is_deleted
ORDER BY lesson_order
"""

_SIGNS_SQL = """
SELECT s.sign_id, s.sign_code, s.label, s.recognition_label,
       ls.lesson_id, ls.display_order
FROM public.lessons l
JOIN public.lesson_signs ls ON ls.lesson_id = l.lesson_id
JOIN public.signs s ON s.sign_id = ls.sign_id
WHERE l.parent_module = :module_id AND l.is_active AND NOT l.is_deleted
  AND NOT ls.is_deleted AND NOT s.is_deleted
ORDER BY l.lesson_order, ls.display_order
"""

# object_key deliberately NOT selected: clients fetch files via /media/presign/{media_id}
_MEDIA_SQL = """
SELECT s.sign_id, sm.media_role, sm.display_order,
       mf.media_id, mf.file_name, mf.media_type
FROM public.signs s
JOIN public.sign_media sm ON sm.sign_id = s.sign_id
JOIN public.media_files mf ON mf.media_id = sm.media_id
WHERE NOT s.is_deleted AND NOT sm.is_deleted AND NOT mf.is_deleted
  AND EXISTS (
      SELECT 1
      FROM public.lesson_signs ls
      JOIN public.lessons l ON l.lesson_id = ls.lesson_id
      WHERE ls.sign_id = s.sign_id
        AND l.parent_module = :module_id
        AND l.is_active AND NOT l.is_deleted AND NOT ls.is_deleted)
ORDER BY s.sign_id, sm.display_order
"""

_MINIGAME_SQL = """
SELECT g.minigame_id, g.minigame_code, g.game_name, g.game_type,
       m.module_code, g.description, g.config
FROM public.minigames g
JOIN public.modules m ON m.module_id = g.module_id
WHERE lower(g.minigame_code) = lower(:minigame_code) AND NOT g.is_deleted
"""

_MODULES_SQL = """
SELECT module_id, module_code, title, description, module_order
FROM public.modules
WHERE is_active AND NOT is_deleted
ORDER BY module_order
"""


@router.get("/modules")
def get_module_list():
    """All active modules, in order."""
    with get_postgres_session() as db:
        rows = db.execute(text(_MODULES_SQL)).mappings().all()
    return {"modules": [dict(r) for r in rows]}


@router.get("/modules/{module_code}")
def get_module_package(module_code: str):
    """
    A module with its lessons, each lesson's signs, and each sign's media:
    {
      "module": {...},
      "lessons": [
        {"lesson_id", "lesson_code", "title", "description", "lesson_order",
         "signs": [{"sign_id", "sign_code", "label", "recognition_label",
                    "display_order",
                    "media": [{"media_id", "media_role", "media_type",
                               "file_name", "display_order"}]}]}
      ]
    }
    """
    with get_postgres_session() as db:
        module = db.execute(text(_MODULE_SQL), {"module_code": module_code}).mappings().first()
        if module is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Module not found")
        p = {"module_id": module["module_id"]}
        lessons = [dict(r) | {"signs": []} for r in db.execute(text(_LESSONS_SQL), p).mappings()]
        signs = db.execute(text(_SIGNS_SQL), p).mappings().all()
        media = db.execute(text(_MEDIA_SQL), p).mappings().all()

    media_by_sign: dict[int, list] = {}
    for r in media:
        media_by_sign.setdefault(r["sign_id"], []).append(
            {k: r[k] for k in ("media_id", "media_role", "media_type",
                               "file_name", "display_order")})

    by_lesson = {lesson["lesson_id"]: lesson for lesson in lessons}
    for r in signs:
        lesson = by_lesson.get(r["lesson_id"])
        if lesson is None:
            continue
        lesson["signs"].append({
            "sign_id": r["sign_id"], "sign_code": r["sign_code"],
            "label": r["label"], "recognition_label": r["recognition_label"],
            "display_order": r["display_order"],
            "media": media_by_sign.get(r["sign_id"], []),
        })
    return jsonable_encoder({"module": dict(module), "lessons": lessons})


@router.get("/minigames/{minigame_code}")
def get_minigame_package(minigame_code: str):
    with get_postgres_session() as db:
        row = db.execute(text(_MINIGAME_SQL), {"minigame_code": minigame_code}).mappings().first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Minigame not found")
    return jsonable_encoder({
        "minigame_id": row["minigame_code"],   
        "game_name": row["game_name"],
        "game_type": row["game_type"],
        "module_id": row["module_code"],      
        "description": row["description"],
        "config": row["config"] or {},
    })