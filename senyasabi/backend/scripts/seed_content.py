"""
Idempotent content seed (Postgres / Supabase) from the bundled content files.

Sources (no vocabulary is duplicated here):
  resources/data/105labels.json      -> 105 canonical word signs + categories
  backend/content_service.MODULE_CODES -> word module order
  resources/data/quizzes/quizzes.json  -> one quiz per module
  backend/minigame_service.CONFIG      -> Sign Sprint / FingerSpell Quest / Sign Detective

Lessons: Alphabet = 4 (A-F, G-L, M-R, S-Z); each word module = 3 contiguous
chunks of its labels in 105labels.json order. No media/progress/scores are created.

Usage (from senyasabi/):  python -m backend.scripts.seed_content [--dry-run]
"""
import json
import sys
from collections import Counter

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from backend import config
from backend.content_service import MODULE_CODES, readable_code
from backend.minigame_service import CONFIG as MINIGAME_CONFIG
from backend.recognition_labels import normalize_label
from backend.scripts.migrate_content import (CONTENT_VERSION_NUMBER, STATIC_BADGES, upsert)

LABELS_PATH = config.DATA_DIR / "105labels.json"
QUIZZES_PATH = config.DATA_DIR / "quizzes" / "quizzes.json"
ALPHABET_LESSONS = [("A-F", "ABCDEF"), ("G-L", "GHIJKL"), ("M-R", "MNOPQR"), ("S-Z", "STUVWXYZ")]
MINIGAMES = [("sign_sprint", "sprint"), ("fingerspell_quest", "quest"), ("sign_detective", "detective")]


def split3(items):
    base, extra = divmod(len(items), 3)
    out, i = [], 0
    for n in range(3):
        size = base + (1 if n < extra else 0)
        out.append(items[i:i + size])
        i += size
    return out


def build_plan():
    """[(module_code, title, [(lesson_title, [(sign_code, label, recognition)])])]"""
    entries = json.loads(LABELS_PATH.read_text(encoding="utf-8-sig"))
    plan = [("alphabet", "Alphabet", [
        (f"Letters {name}", [(c.lower(), c, c) for c in letters]) for name, letters in ALPHABET_LESSONS])]
    for code in MODULE_CODES:
        signs = [(e.get("sign_code") or readable_code(e["label"]), e["label"],
                  normalize_label(e.get("recognition_label", e["label"])))
                 for e in entries if e["category"].casefold() == code]
        plan.append((code, code.title(),
                     [(f"{code.title()} Part {n}", chunk) for n, chunk in enumerate(split3(signs), 1)]))
    codes = [s[0] for _, _, ls in plan for _, ss in ls for s in ss]
    assert len(codes) == len(set(codes)), "duplicate sign_code in content"
    assert sum(len(ss) for c, _, ls in plan if c != "alphabet" for _, ss in ls) == 105
    return plan


def seed(dry_run=False):
    if not config.POSTGRESQL_URL:
        sys.exit("ERROR: DATABASE_URL not set")
    plan = build_plan()
    quizzes = {q["module_code"]: q for q in json.loads(QUIZZES_PATH.read_text(encoding="utf-8"))["quizzes"]}
    stats = Counter()

    def tally(kind, created):
        stats[f"{kind} {'created' if created else 'existing/unchanged'}"] += 1

    engine = create_engine(config.POSTGRESQL_URL, poolclass=NullPool, connect_args={"prepare_threshold": None})
    with engine.connect() as conn:
        cv_id, _ = upsert(conn, "content_versions", "content_version_id", ["version_number"],
                          {"version_number": CONTENT_VERSION_NUMBER, "changelog": "Initial content version",
                           "is_published": True, "is_deleted": False})
        module_ids = {}
        for m_idx, (mcode, title, lessons) in enumerate(plan, 1):
            module_id, c = upsert(conn, "modules", "module_id", ["module_code"],
                                  {"module_code": mcode, "title": title, "module_order": m_idx,
                                   "is_active": True, "is_deleted": False, "content_version_id": cv_id})
            tally("module", c)
            module_ids[mcode] = module_id
            all_sign_ids = []
            for l_idx, (ltitle, signs) in enumerate(lessons, 1):
                lesson_id, c = upsert(conn, "lessons", "lesson_id", ["lesson_code"],
                                      {"lesson_code": f"{mcode}_lesson_{l_idx}", "title": ltitle,
                                       "parent_module": module_id, "lesson_order": l_idx,
                                       "is_active": True, "is_deleted": False, "content_version_id": cv_id})
                tally("lesson", c)
                for order, (scode, label, rec) in enumerate(signs, 1):
                    sign_id, c = upsert(conn, "signs", "sign_id", ["sign_code"],
                                        {"sign_code": scode, "label": label, "recognition_label": rec,
                                         "is_deleted": False, "content_version_id": cv_id})
                    tally("sign", c)
                    _, c = upsert(conn, "lesson_signs", None, ["lesson_id", "sign_id"],
                                  {"lesson_id": lesson_id, "sign_id": sign_id, "display_order": order,
                                   "is_deleted": False, "content_version_id": cv_id})
                    tally("lesson_sign", c)
                    all_sign_ids.append(sign_id)
            q = quizzes[mcode]
            quiz_id, c = upsert(conn, "quizzes", "quiz_id", ["quiz_code"],
                                {"quiz_code": q["quiz_code"], "module_id": module_id, "category_code": None,
                                 "title": q["title"], "passing_score": q["passing_score"],
                                 "config": json.dumps({"shuffle": q.get("shuffle", True),
                                                       "question_types": q["question_types"]}),
                                 "is_deleted": False, "content_version_id": cv_id},
                                casts={"config": "jsonb"})
            tally("quiz", c)
            for order, sid in enumerate(all_sign_ids, 1):
                _, c = upsert(conn, "quiz_signs", None, ["quiz_id", "sign_id"],
                              {"quiz_id": quiz_id, "sign_id": sid, "display_order": order,
                               "is_deleted": False, "content_version_id": cv_id})
                tally("quiz_sign", c)

        badges = list(STATIC_BADGES) + [(f"{c}_master".upper(), f"{t} Master",
                                         f"Complete every lesson and pass the quiz in {t}.") for c, t, _ in plan]
        for code, name, desc in badges:
            _, c = upsert(conn, "badges", "badge_id", ["badge_code"],
                          {"badge_code": code, "badge_name": name, "description": desc, "is_deleted": False})
            tally("badge", c)

        # minigames.module_id is NOT NULL; games are global, so anchor them to the Alphabet module.
        for code, kind in MINIGAMES:
            name, difficulty, seconds = MINIGAME_CONFIG[kind]
            _, c = upsert(conn, "minigames", "minigame_id", ["minigame_code"],
                          {"minigame_code": code, "game_name": name, "game_type": kind,
                           "module_id": module_ids["alphabet"], "description": difficulty,
                           "config": json.dumps({"scope": "global", "time_limit_seconds": seconds}),
                           "is_deleted": False, "content_version_id": cv_id},
                          casts={"config": "jsonb"})
            tally("minigame", c)

        if dry_run:
            conn.rollback()
            print("DRY RUN: rolled back")
        else:
            conn.commit()
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")


if __name__ == "__main__":
    seed("--dry-run" in sys.argv)

