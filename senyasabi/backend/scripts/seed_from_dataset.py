"""
Rebuild module content from resources/data/expected_dataset.md (Postgres/Supabase).
Seeds under a NEW content version, then soft-deletes anything not in the dataset
(at that same version, so clients receive the deletions).

Usage (from senyasabi/):  python -m backend.scripts.seed_from_dataset [--dry-run]
"""
import json, sys
from collections import Counter

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from backend import config
from backend.recognition_labels import normalize_label
from backend.scripts.migrate_content import (
    EXPECTED_DATASET_PATH, LABELS_PATH, MEDIA_ROLE, QUIZ_PASSING_SCORE, STATIC_BADGES,
    build_media_index, find_media, parse_expected_dataset, slugify, upsert)
from backend.content_service import DATASET_MODULE_CODES as MODULE_CODES

CONTENT_VERSION_NUMBER = 2   # must be higher than what clients have

DIGITS = dict(zip(map(str, range(1, 11)),
                  "ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN".split()))


def recognition_labels():
    items = json.loads(LABELS_PATH.read_text(encoding="utf-8-sig"))
    return {slugify(normalize_label(i["label"])): normalize_label(i["label"]) for i in items}


def build_plan():
    """[(module_code, title, [(lesson_code, lesson_title, [label, ...])])]"""
    plan = []
    for mdata in parse_expected_dataset(EXPECTED_DATASET_PATH):
        code = MODULE_CODES[mdata["name"]]          # KeyError = unmapped module name
        lessons = []
        for n, ldata in enumerate(mdata["lessons"], 1):
            seen, labels = set(), []
            for label in ldata["signs"]:
                if slugify(label) not in seen:
                    seen.add(slugify(label))
                    labels.append(label)
            lessons.append((f"{code}_lesson_{n}", ldata["name"], labels))
        plan.append((code, mdata["name"], lessons))
    codes = [slugify(s) for _, _, ls in plan for _, _, ss in ls for s in ss]
    dupes = [c for c, k in Counter(codes).items() if k > 1]
    assert not dupes, f"sign_code collisions across modules: {dupes}"
    return plan


def seed(dry_run=False):
    if not config.POSTGRESQL_URL:
        sys.exit("ERROR: DATABASE_URL not set")
    plan, rec_map = build_plan(), recognition_labels()
    stats, no_label, no_media = Counter(), [], []
    tally = lambda k, c: stats.update([f"{k} {'created' if c else 'existing/unchanged'}"])

    engine = create_engine(config.POSTGRESQL_URL, poolclass=NullPool,
                           connect_args={"prepare_threshold": None})
    with engine.connect() as conn:
        cv, _ = upsert(conn, "content_versions", "content_version_id", ["version_number"],
                       {"version_number": CONTENT_VERSION_NUMBER,
                        "changelog": "Modules rebuilt from expected_dataset.md",
                        "is_published": True, "is_deleted": False})

        # Free lesson_order slots before inserting (partial unique index).
        keep_lessons = [l[0] for _, _, ls in plan for l in ls]
        conn.execute(text("""UPDATE public.lessons SET is_deleted = true, content_version_id = :cv
                             WHERE NOT is_deleted AND lesson_code <> ALL(CAST(:k AS text[]))"""),
                     {"cv": cv, "k": keep_lessons})

        media_index, used = build_media_index(conn), set()

        for m_idx, (mcode, title, lessons) in enumerate(plan, 1):
            module_id, c = upsert(conn, "modules", "module_id", ["module_code"],
                {"module_code": mcode, "title": title[:100], "module_order": m_idx,
                 "is_active": True, "is_deleted": False, "content_version_id": cv})
            tally("module", c)
            module_sign_ids = []
            for l_idx, (lcode, ltitle, labels) in enumerate(lessons, 1):
                lesson_id, c = upsert(conn, "lessons", "lesson_id", ["lesson_code"],
                    {"lesson_code": lcode, "title": ltitle[:100], "parent_module": module_id,
                     "lesson_order": l_idx, "is_active": True, "is_deleted": False,
                     "content_version_id": cv})
                tally("lesson", c)
                for order, label in enumerate(labels, 1):
                    scode = slugify(label)
                    key = slugify(normalize_label(DIGITS.get(label, label)))
                    rec = rec_map.get(key)
                    if rec is None:
                        no_label.append(label)
                        rec = normalize_label(label)
                    sign_id, c = upsert(conn, "signs", "sign_id", ["sign_code"],
                        {"sign_code": scode, "label": label[:100], "recognition_label": rec[:100],
                         "is_deleted": False, "content_version_id": cv})
                    tally("sign", c)
                    _, c = upsert(conn, "lesson_signs", None, ["lesson_id", "sign_id"],
                        {"lesson_id": lesson_id, "sign_id": sign_id, "display_order": order,
                         "is_deleted": False, "content_version_id": cv})
                    tally("lesson_sign", c)
                    module_sign_ids.append(sign_id)

                    media = find_media(media_index, label, [ltitle, title], used)
                    if media is None:
                        no_media.append(f"{title} / {label}")   # sign still created
                    else:
                        used.add(media["media_id"])
                        _, c = upsert(conn, "sign_media", None, ["sign_id", "media_id", "media_role"],
                            {"sign_id": sign_id, "media_id": media["media_id"],
                             "media_role": MEDIA_ROLE, "display_order": 1,
                             "is_deleted": False, "content_version_id": cv})
                        tally("sign_media", c)

            quiz_id, c = upsert(conn, "quizzes", "quiz_id", ["quiz_code"],
                {"quiz_code": f"{mcode}_quiz", "module_id": module_id, "category_code": None,
                 "title": f"{title} Quiz"[:100], "passing_score": QUIZ_PASSING_SCORE,
                 "config": json.dumps({"shuffle": True,
                                       "question_types": ["camera", "identification"]}),
                 "is_deleted": False, "content_version_id": cv}, casts={"config": "jsonb"})
            tally("quiz", c)
            for order, sid in enumerate(module_sign_ids, 1):
                _, c = upsert(conn, "quiz_signs", None, ["quiz_id", "sign_id"],
                    {"quiz_id": quiz_id, "sign_id": sid, "display_order": order,
                     "is_deleted": False, "content_version_id": cv})
                tally("quiz_sign", c)

        # Every planned row now has content_version_id = cv. Any live row still on an
        # older version is stale: soft-delete it AT the new version so deltas carry it.
        for table in ("sign_media", "quiz_signs", "lesson_signs", "quizzes",
                      "signs", "lessons", "modules"):
            r = conn.execute(text(f"""UPDATE public.{table}
                SET is_deleted = true, content_version_id = :cv
                WHERE NOT is_deleted AND content_version_id <> :cv"""), {"cv": cv})
            stats[f"{table} retired"] += r.rowcount

        # Badges (no content_version column; the API always sends the full list).
        badges = list(STATIC_BADGES) + [(f"{c}_master".upper(), f"{t} Master",
                 f"Complete every lesson and pass the quiz in {t}.") for c, t, _ in plan]
        for code, name, desc in badges:
            _, c = upsert(conn, "badges", "badge_id", ["badge_code"],
                {"badge_code": code, "badge_name": name[:100],
                 "description": desc, "is_deleted": False})
            tally("badge", c)
        conn.execute(text("""UPDATE public.badges SET is_deleted = true
            WHERE NOT is_deleted AND badge_code LIKE '%\\_MASTER'
              AND badge_code <> ALL(CAST(:k AS text[]))"""), {"k": [b[0] for b in badges]})

        if dry_run:
            conn.rollback(); print("DRY RUN: rolled back")
        else:
            conn.commit(); print("Committed")

    for k in sorted(stats): print(f"  {k}: {stats[k]}")
    if no_label:
        print(f"\n{len(no_label)} signs have no model label (recognition_label derived): "
              + ", ".join(no_label))
    if no_media:
        print(f"\n{len(no_media)} signs have no media yet (created anyway)")


if __name__ == "__main__":
    seed("--dry-run" in sys.argv)