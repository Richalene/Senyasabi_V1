"""
Content structure migration (Postgres / Supabase).

Parses expected_dataset.md and populates:
  content_versions, modules, lessons, signs, lesson_signs, sign_media,
  quizzes (one per module; questions are generated client-side),
  badges, minigames (from minigames.json, if present)

Run after:
  1. DATABASE_URL is set in .env
  2. media_files is populated (tests/import_media.py import)

Usage:
    python migrate_content.py            # write to DB
    python migrate_content.py --dry-run  # run everything, then roll back

Safe to re-run: rows are matched on their unique codes and only changed rows
are updated (so updated_at, which drives delta sync, is not bumped needlessly).
Rows that disappear from the dataset are NOT soft-deleted by this script.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from backend.config import POSTGRESQL_URL
from backend.database.models import (
    Badge,
    ContentVersion,
    Lesson,
    LessonSign,
    MediaFile,
    Minigame,
    Module,
    Quiz,
    QuizSign,
    Sign,
    SignMedia
)

from backend import config  # loads .env

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EXPECTED_DATASET_PATH = config.DATA_DIR / "expected_dataset.md"
LABELS_PATH = config.DATA_DIR / "105labels.json"
MINIGAMES_PATH = config.DATA_DIR / "minigames.json"

CONTENT_VERSION_NUMBER = 1
EXPECTED_MODULE_COUNT = 7
QUIZ_PASSING_SCORE = 70
MEDIA_ROLE = "demonstration"

# module name as written in expected_dataset.md -> module_code.
# Anything not listed falls back to UPPER_SNAKE of the name,
# e.g. {"Words": "WORD", "Alphabet": "ALPHABET"}
MODULE_CODE_OVERRIDES: dict[str, str] = {}

# (badge_code, badge_name, description)
STATIC_BADGES = [
    ("FIRST_STEPS", "First Steps", "Complete your first lesson."),
    ("QUIZ_TAKER", "Quiz Taker", "Complete your first quiz."),
    ("GAME_ON", "Game On", "Complete your first minigame."),
    ("ON_A_ROLL", "On a Roll", "Reach a 7-day streak."),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def slugify(value: str) -> str:
    """'Good Morning' / 'GOOD_MORNING' / 'good-morning' -> 'good_morning'"""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def to_code(value: str) -> str:
    return slugify(value).upper()


def upsert(conn, table: str, pk: str | None, conflict: list[str],
           values: dict, casts: dict[str, str] | None = None):
    """
    INSERT ... ON CONFLICT (conflict) DO UPDATE, touching the row only if a
    value actually changed. Returns (pk_value_or_None, created).

    `table`, column names and `casts` are internal constants, never user input.
    """
    casts = casts or {}
    cols = list(values)
    placeholders = [
        f"CAST(:{c} AS {casts[c]})" if c in casts else f":{c}" for c in cols
    ]
    update_cols = [c for c in cols if c not in conflict]
    set_sql = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
    changed_sql = " OR ".join(
        f"t.{c} IS DISTINCT FROM EXCLUDED.{c}" for c in update_cols
    )
    returning = ", ".join(x for x in (pk, "(xmax = 0) AS created") if x)

    row = conn.execute(text(f"""
        INSERT INTO public.{table} AS t ({", ".join(cols)})
        VALUES ({", ".join(placeholders)})
        ON CONFLICT ({", ".join(conflict)}) DO UPDATE SET {set_sql}
        WHERE {changed_sql}
        RETURNING {returning}
    """), values).mappings().first()

    if row is not None:
        return (row[pk] if pk else None), bool(row["created"])

    # Row exists and nothing changed: the guarded UPDATE returned no row.
    pk_value = None
    if pk:
        where = " AND ".join(f"{c} = :{c}" for c in conflict)
        pk_value = conn.execute(
            text(f"SELECT {pk} FROM public.{table} WHERE {where}"),
            {c: values[c] for c in conflict},
        ).scalar_one()
    return pk_value, False


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------
MODULE_RE = re.compile(r"^##\s*Module\s+(.+)$", re.IGNORECASE)

def parse_expected_dataset(file_path: Path) -> list[dict]:
    """
    Expected format:

        ## Lesson Alphabet
        ### Letters A-M            <- becomes a lesson
        A, B, C, D, ...            <- signs (comma-separated; "- A, B" bullets ok)

    Sign lines directly under a module header (no ###) go into a default
    lesson named after the module.

    Returns: [{"name": str, "lessons": [{"name": str, "signs": [str, ...]}]}]
    """
    modules: list[dict] = []
    module = None
    lesson = None

    for raw in file_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue

        m = MODULE_RE.match(line)
        if m:
            module = {"name": m.group(1).strip(), "lessons": []}
            modules.append(module)
            lesson = None
            continue

        if line.startswith("###"):
            if module is None:
                continue
            lesson = {"name": line.lstrip("#").strip(), "signs": []}
            module["lessons"].append(lesson)
            continue

        if line.startswith("#") or module is None:
            continue

        signs = [s.strip() for s in line.lstrip("-*• ").split(",") if s.strip()]
        if not signs:
            continue
        if lesson is None:
            lesson = {"name": module["name"], "signs": []}
            module["lessons"].append(lesson)
        lesson["signs"].extend(signs)

    return modules


def load_labels(file_path: Path) -> dict[str, str]:
    """105labels.json: list of {"label": ..., "category": ...}.
    Returns {slugified_label: original_label}."""
    if not file_path.exists():
        print(f"WARNING: {file_path} not found; recognition_label will be derived")
        return {}
    items = json.loads(file_path.read_text(encoding="utf-8"))
    return {slugify(i["label"]): i["label"] for i in items}


def load_minigames(file_path: Path) -> list[dict]:
    """Accepts a top-level list or {"minigames": [...]}."""
    if not file_path.exists():
        print(f"WARNING: {file_path} not found; skipping minigames")
        return []
    data = json.loads(file_path.read_text(encoding="utf-8"))
    return data.get("minigames", []) if isinstance(data, dict) else data


# ---------------------------------------------------------------------------
# Media matching
# ---------------------------------------------------------------------------
def build_media_index(conn) -> dict[str, list]:
    """slug of file stem -> [row, ...] (by file_name and object_key)."""
    index: dict[str, list] = defaultdict(list)
    rows = conn.execute(text("""
        SELECT media_id, file_name, object_key
        FROM public.media_files
        WHERE NOT is_deleted
        ORDER BY media_id
    """)).mappings().all()
    for mf in rows:
        stems = {slugify(Path(mf["file_name"] or "").stem),
                 slugify(Path(mf["object_key"]).stem)}
        for key in stems:
            index[key].append(mf)
    return index


def find_media(index, label: str, hints: list[str], used_ids: set[int]):
    """Unused media whose filename stem matches the label. If several match,
    prefer the one whose object_key path contains the lesson/module name."""
    candidates = [m for m in index.get(slugify(label), [])
                  if m["media_id"] not in used_ids]
    if not candidates:
        return None
    if len(candidates) > 1:
        hint_slugs = [slugify(h) for h in hints if h]
        for m in candidates:
            key = slugify(m["object_key"])
            if any(h in key for h in hint_slugs):
                return m
    return candidates[0]


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------
def migrate_content(dry_run: bool = False) -> None:
    if not config.POSTGRESQL_URL:
        sys.exit("ERROR: DATABASE_URL not set in environment")

    print("Starting content migration..." + (" (DRY RUN)" if dry_run else ""))

    modules_data = parse_expected_dataset(EXPECTED_DATASET_PATH)
    if not modules_data:
        sys.exit(f"ERROR: no modules parsed from {EXPECTED_DATASET_PATH}")
    print(f"Parsed {len(modules_data)} modules from {EXPECTED_DATASET_PATH.name}")
    if len(modules_data) != EXPECTED_MODULE_COUNT:
        print(f"WARNING: expected {EXPECTED_MODULE_COUNT} modules, got {len(modules_data)}")

    labels_map = load_labels(LABELS_PATH)
    print(f"Loaded {len(labels_map)} labels from {LABELS_PATH.name}")
    minigames_data = load_minigames(MINIGAMES_PATH)

    stats: Counter = Counter()
    missing_media: list[str] = []
    unlabeled: list[str] = []

    def tally(kind: str, created: bool) -> None:
        stats[f"{kind} {'created' if created else 'existing/unchanged'}"] += 1

    # NullPool + no prepared statements: works with both Supabase poolers.
    engine = create_engine(
        config.POSTGRESQL_URL,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )

    with engine.connect() as conn:  # exiting on error rolls back
        # --- Content version ------------------------------------------------
        cv_id, created = upsert(
            conn, "content_versions", "content_version_id", ["version_number"],
            {"version_number": CONTENT_VERSION_NUMBER,
             "changelog": "Initial content version",
             "is_published": True,
             "is_deleted": False},
        )
        print(f"{'Created' if created else 'Using existing'} content version "
              f"v{CONTENT_VERSION_NUMBER} (ID: {cv_id})")

        media_index = build_media_index(conn)
        used_media_ids: set[int] = set(conn.scalars(
            text("SELECT media_id FROM public.sign_media WHERE NOT is_deleted")))
        modules_by_key: dict[str, int] = {}
        module_rows: list[tuple[str, str]] = []  # (module_code, title)

        # --- Modules / lessons / signs / quizzes ----------------------------
        for m_idx, mdata in enumerate(modules_data, 1):
            module_code = MODULE_CODE_OVERRIDES.get(mdata["name"]) or to_code(mdata["name"])
            title = mdata["name"][:100]
            module_id, created = upsert(
                conn, "modules", "module_id", ["module_code"],
                {"module_code": module_code,
                 "title": title,
                 "module_order": m_idx,
                 "is_active": True,
                 "is_deleted": False,
                 "content_version_id": cv_id},
            )
            tally("module", created)
            modules_by_key[module_code.lower()] = module_id
            modules_by_key[slugify(mdata["name"])] = module_id
            module_rows.append((module_code, title))

            module_sign_count = 0
            module_sign_ids: list[int] = []

            for l_idx, ldata in enumerate(mdata["lessons"], 1):
                lesson_code = f"{module_code}_{to_code(ldata['name'])}"[:100]
                lesson_id, created = upsert(
                    conn, "lessons", "lesson_id", ["lesson_code"],
                    {"lesson_code": lesson_code,
                     "title": ldata["name"][:100],
                     "parent_module": module_id,
                     "lesson_order": l_idx,
                     "is_active": True,
                     "is_deleted": False,
                     "content_version_id": cv_id},
                )
                tally("lesson", created)

                seen_in_lesson: set[str] = set()
                for label in ldata["signs"]:
                    sign_slug = slugify(label)
                    if sign_slug in seen_in_lesson:
                        continue
                    seen_in_lesson.add(sign_slug)

                    sign_code = f"{lesson_code}_{to_code(label)}"[:100]
                    
                    # Media already linked to this sign (re-run), if any
                    media_id = conn.execute(text("""
                        SELECT sm.media_id
                        FROM public.signs s
                        JOIN public.sign_media sm
                          ON sm.sign_id = s.sign_id
                         AND sm.media_role = :role
                         AND NOT sm.is_deleted
                        WHERE s.sign_code = :code
                    """), {"role": MEDIA_ROLE, "code": sign_code}).scalar()

                    if media_id is None:
                        media = find_media(
                            media_index, label, [ldata["name"], mdata["name"]],
                            used_media_ids)
                        if media is None:
                            missing_media.append(
                                f"{mdata['name']} / {ldata['name']} / {label}")
                            continue
                        media_id = media["media_id"]
                        used_media_ids.add(media_id)

                    recognition = labels_map.get(sign_slug)
                    if recognition is None:
                        unlabeled.append(label)
                        recognition = to_code(label)

                    sign_id, created = upsert(
                        conn, "signs", "sign_id", ["sign_code"],
                        {"sign_code": sign_code,
                         "label": label[:100],
                         "recognition_label": recognition[:100],
                         "is_deleted": False,
                         "content_version_id": cv_id},
                    )
                    tally("sign", created)

                    _, created = upsert(
                        conn, "lesson_signs", None, ["lesson_id", "sign_id"],
                        {"lesson_id": lesson_id,
                         "sign_id": sign_id,
                         "display_order": len(seen_in_lesson),
                         "is_deleted": False,
                         "content_version_id": cv_id},
                    )
                    tally("lesson_sign", created)

                    _, created = upsert(
                        conn, "sign_media", None,
                        ["sign_id", "media_id", "media_role"],
                        {"sign_id": sign_id,
                         "media_id": media_id,
                         "media_role": MEDIA_ROLE,
                         "display_order": 1,
                         "is_deleted": False,
                         "content_version_id": cv_id},
                    )
                    tally("sign_media", created)
                    module_sign_count += 1
                    module_sign_ids.append(sign_id)

            # One quiz per module (skip modules where no signs resolved).
            if module_sign_count:
                quiz_id, created = upsert(
                    conn, "quizzes", "quiz_id", ["quiz_code"],
                    {"quiz_code": f"{module_code}_QUIZ"[:100],
                     "module_id": module_id,
                     "category_code": None,
                     "title": f"{title} Quiz"[:100],
                     "passing_score": QUIZ_PASSING_SCORE,
                     "config": json.dumps(
                         {"shuffle": True,
                          "question_types": ["camera", "identification"]}),
                     "is_deleted": False,
                     "content_version_id": cv_id},
                    casts={"config": "jsonb"},
                )
                tally("quiz", created)

                for order, sid in enumerate(module_sign_ids, 1):
                    _, created = upsert(
                        conn, "quiz_signs", None, ["quiz_id", "sign_id"],
                        {"quiz_id": quiz_id,
                         "sign_id": sid,
                         "display_order": order,
                         "is_deleted": False,
                         "content_version_id": cv_id},
                    )
                    tally("quiz_sign", created)
                    
            print(f"  {m_idx}. {mdata['name']}: {len(mdata['lessons'])} lessons, "
                  f"{module_sign_count} signs, quiz covers {module_sign_count * 2} "
                  f"generated questions (camera + MC)")

        # --- Badges -----------------------------------------------------------
        badge_defs = list(STATIC_BADGES) + [
            (f"{code}_MASTER", f"{title} Master",
             f"Complete every lesson and pass the quiz in {title}.")
            for code, title in module_rows
        ]
        for code, name, desc in badge_defs:
            _, created = upsert(
                conn, "badges", "badge_id", ["badge_code"],
                {"badge_code": code[:100],
                 "badge_name": name[:100],
                 "description": desc,
                 "is_deleted": False},
            )
            tally("badge", created)

        # --- Minigames --------------------------------------------------------
        for mg in minigames_data:
            code = mg.get("minigame_id") or mg.get("minigame_code")
            module_id = modules_by_key.get(slugify(str(mg.get("module_id", ""))))
            if not code or module_id is None:
                print(f"WARNING: skipping minigame {code!r}: "
                      f"unknown module {mg.get('module_id')!r}")
                continue
            if not mg.get("game_name") or not mg.get("game_type"):
                print(f"WARNING: skipping minigame {code!r}: "
                      f"game_name and game_type are required")
                continue
            _, created = upsert(
                conn, "minigames", "minigame_id", ["minigame_code"],
                {"minigame_code": code[:100],
                 "game_name": mg["game_name"][:100],
                 "game_type": mg["game_type"][:50],
                 "module_id": module_id,
                 "description": mg.get("description"),
                 "config": json.dumps(mg.get("config", {}), ensure_ascii=False),
                 "is_deleted": False,
                 "content_version_id": cv_id},
                casts={"config": "jsonb"},
            )
            tally("minigame", created)

        if dry_run:
            conn.rollback()
            print("\nDRY RUN: rolled back, nothing written.")
        else:
            conn.commit()
            print("\nCommitted.")

    print("\nSummary:")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    if missing_media:
        print(f"\n{len(missing_media)} signs skipped (no unused matching media_files row):")
        for item in missing_media:
            print(f"  - {item}")
    if unlabeled:
        print(f"\n{len(unlabeled)} signs not found in 105labels.json "
              f"(recognition_label was derived):")
        print("  " + ", ".join(unlabeled))


if __name__ == "__main__":
    migrate_content(dry_run="--dry-run" in sys.argv)