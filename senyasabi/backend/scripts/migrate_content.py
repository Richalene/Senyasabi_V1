"""
Content structure migration script.

Parses expected_dataset.md and creates the content structure in PostgreSQL:
- ContentVersion (v1)
- Modules
- Lessons
- Signs (linked to existing media_files)
- Quizzes (one per module; questions are generated client-side, see notes)
- Badges
- Minigames (from minigames.json, if present)

Run after:
1. POSTGRESQL_URL is configured in .env
2. media_files is populated (import_media)

Usage:
    python migrate_content.py            # write to DB
    python migrate_content.py --dry-run  # run everything, then roll back

Safe to re-run: rows are matched on their unique codes and updated in place.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Must happen BEFORE importing config, in case config reads os.environ at import time
load_dotenv()

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from config import POSTGRESQL_URL
from ..database.models import (  # adjust import path to wherever your models live
    Badge,
    ContentVersion,
    Lesson,
    MediaFile,
    Minigame,
    Module,
    Quiz,
    Sign,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = BACKEND_DIR.parent
DATA_DIR = BASE_DIR / "resources" / "data"
EXPECTED_DATASET_PATH = DATA_DIR / "expected_dataset.md"
LABELS_PATH = DATA_DIR / "105labels.json"
MINIGAMES_PATH = DATA_DIR / "minigames.json"  # adjust/create; see notes

CONTENT_VERSION_NUMBER = 1
EXPECTED_MODULE_COUNT = 7
QUIZ_PASSING_SCORE = 70

# Map the module name as written in expected_dataset.md -> module_code.
# Anything not listed falls back to UPPER_SNAKE of the name.
# e.g. {"Words": "WORD", "Alphabet": "ALPHABET"}
MODULE_CODE_OVERRIDES: dict[str, str] = {}

# Placeholder badges - edit to match your app's badge-awarding logic.
STATIC_BADGES = [
    ("First Steps", "Complete your first lesson."),
    ("Quiz Taker", "Complete your first quiz."),
    ("Game On", "Complete your first minigame."),
    ("On a Roll", "Reach a 7-day streak."),
]

if not POSTGRESQL_URL:
    print("ERROR: POSTGRESQL_URL not set in environment")
    sys.exit(1)

# Supabase Session Pooler: the pooler manages connections, so keep local pooling minimal
engine = create_engine(
    POSTGRESQL_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    """'Good Morning' / 'GOOD_MORNING' / 'good-morning' -> 'good_morning'"""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def to_code(text: str) -> str:
    return slugify(text).upper()


def upsert(db, model, lookup: dict, values: dict, update: bool = True):
    """
    Get-or-create by `lookup`. On create, sets lookup+values. On existing rows,
    updates changed fields (and bumps updated_at if the model has one).
    autoflush is off, so we flush here to get server-assigned IDs immediately.
    Returns (obj, created).
    """
    obj = db.execute(select(model).filter_by(**lookup)).scalar_one_or_none()
    if obj is None:
        extra = {}
        if hasattr(model, "updated_at") and "updated_at" not in values:
            extra["updated_at"] = utcnow()
        obj = model(**lookup, **values, **extra)
        db.add(obj)
        created = True
    else:
        created = False
        if update:
            changed = False
            for key, val in values.items():
                if getattr(obj, key) != val:
                    setattr(obj, key, val)
                    changed = True
            if changed and hasattr(obj, "updated_at"):
                obj.updated_at = utcnow()
    db.flush()
    return obj, created


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------
MODULE_RE = re.compile(r"^##\s*Lesson\s*\d*\s*[:\-–]?\s*(.+)$", re.IGNORECASE)


def parse_expected_dataset(file_path: Path) -> list[dict]:
    """
    Expected format (adjust if yours differs):

        ## Lesson Alphabet
        ### Letters A-M            <- becomes a lesson
        A, B, C, D, ...            <- signs (one or more lines, comma-separated)

    Sign lines directly under a module header (no ###) go into a default
    lesson named after the module.

    Returns: [{"name": str, "lessons": [{"name": str, "signs": [str, ...]}]}]
    """
    modules: list[dict] = []
    module = None
    lesson = None

    with open(file_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        m = MODULE_RE.match(line)
        if m:
            module = {"name": m.group(1).strip(), "lessons": []}
            modules.append(module)
            lesson = None  # don't leak the previous module's subsection
            continue

        if line.startswith("###"):
            if module is None:
                continue
            lesson = {"name": line.lstrip("#").strip(), "signs": []}
            module["lessons"].append(lesson)
            continue

        if line.startswith("#") or module is None:
            continue

        # Sign line (also tolerate "- A, B, C" bullets)
        signs = [s.strip() for s in line.lstrip("-*• ").split(",") if s.strip()]
        if not signs:
            continue
        if lesson is None:
            lesson = {"name": module["name"], "signs": []}
            module["lessons"].append(lesson)
        lesson["signs"].extend(signs)

    return modules


def load_labels(file_path: Path) -> dict[str, str]:
    """
    Load 105labels.json (expects a list of {"label": ..., "id": ...}).
    Returns {slugified_label: original_label} so we can reuse the exact label
    string the recognition model emits.
    """
    if not file_path.exists():
        print(f"WARNING: {file_path} not found; recognition_label will be derived from sign names")
        return {}
    with open(file_path, encoding="utf-8") as f:
        labels = json.load(f)
    return {slugify(item["label"]): item["label"] for item in labels}


def load_minigames(file_path: Path) -> list[dict]:
    """Accepts either a top-level list or {"minigames": [...]}."""
    if not file_path.exists():
        print(f"WARNING: {file_path} not found; skipping minigames")
        return []
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("minigames", [])
    return data


# ---------------------------------------------------------------------------
# Media matching
# ---------------------------------------------------------------------------
def build_media_index(db) -> dict[str, list]:
    """slug of file stem -> [MediaFile, ...] (by file_name and object_key)."""
    index: dict[str, list] = defaultdict(list)
    rows = db.execute(
        select(MediaFile).where(MediaFile.is_deleted.is_(False)).order_by(MediaFile.media_id)
    ).scalars()
    for mf in rows:
        for key in {slugify(Path(mf.file_name).stem), slugify(Path(mf.object_key).stem)}:
            index[key].append(mf)
    return index


def find_media(index, label: str, hints: list[str], used_ids: set[int]):
    """
    Find an unused MediaFile whose filename stem matches the sign label.
    If several match (e.g. same word in different folders), prefer the one whose
    object_key path contains the lesson/module name.
    """
    candidates = [m for m in index.get(slugify(label), []) if m.media_id not in used_ids]
    if not candidates:
        return None
    if len(candidates) > 1:
        hint_slugs = [slugify(h) for h in hints if h]
        for m in candidates:
            key = slugify(m.object_key)
            if any(h in key for h in hint_slugs):
                return m
    return candidates[0]


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------
def migrate_content(dry_run: bool = False) -> None:
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
        stats[f"{kind} {'created' if created else 'existing'}"] += 1

    with SessionLocal() as db:
        try:
            # --- Content version --------------------------------------------
            cv, created = upsert(
                db,
                ContentVersion,
                {"version_number": CONTENT_VERSION_NUMBER},
                {"changelog": "Initial content version", "is_published": True, "is_deleted": False},
                update=False,
            )
            cv_id = cv.content_version_id
            print(f"{'Created' if created else 'Using existing'} content version "
                  f"v{CONTENT_VERSION_NUMBER} (ID: {cv_id})")

            media_index = build_media_index(db)
            used_media_ids: set[int] = set(db.scalars(select(Sign.media_id)))
            modules_by_key: dict[str, Module] = {}

            # --- Modules / lessons / signs / quizzes -------------------------
            for m_idx, mdata in enumerate(modules_data, 1):
                module_code = MODULE_CODE_OVERRIDES.get(mdata["name"]) or to_code(mdata["name"])
                module, created = upsert(
                    db,
                    Module,
                    {"module_code": module_code},
                    {
                        "title": mdata["name"][:100],
                        "module_order": m_idx,
                        "is_active": True,
                        "is_deleted": False,
                        "content_version_id": cv_id,
                    },
                )
                tally("module", created)
                modules_by_key[module_code.lower()] = module
                modules_by_key[slugify(mdata["name"])] = module

                module_sign_count = 0

                for l_idx, ldata in enumerate(mdata["lessons"], 1):
                    lesson_code = f"{module_code}_{to_code(ldata['name'])}"[:100]
                    lesson, created = upsert(
                        db,
                        Lesson,
                        {"lesson_code": lesson_code},
                        {
                            "title": ldata["name"][:100],
                            "parent_module": module.module_id,
                            "lesson_order": l_idx,
                            "is_active": True,
                            "is_deleted": False,
                            "content_version_id": cv_id,
                        },
                    )
                    tally("lesson", created)

                    seen_in_lesson: set[str] = set()
                    for label in ldata["signs"]:
                        sign_slug = slugify(label)
                        if sign_slug in seen_in_lesson:
                            continue
                        seen_in_lesson.add(sign_slug)

                        sign_code = f"{lesson_code}_{to_code(label)}"[:100]
                        existing = db.execute(
                            select(Sign).where(Sign.sign_code == sign_code)
                        ).scalar_one_or_none()

                        if existing is not None:
                            media_id = existing.media_id
                        else:
                            media = find_media(
                                media_index, label, [ldata["name"], mdata["name"]], used_media_ids
                            )
                            if media is None:
                                missing_media.append(f"{mdata['name']} / {ldata['name']} / {label}")
                                continue
                            media_id = media.media_id
                            used_media_ids.add(media_id)  # Sign.media_id is UNIQUE

                        recognition = labels_map.get(sign_slug)
                        if recognition is None:
                            unlabeled.append(label)
                            recognition = to_code(label)

                        _, created = upsert(
                            db,
                            Sign,
                            {"sign_code": sign_code},
                            {
                                "lesson_id": lesson.lesson_id,
                                "media_id": media_id,
                                "label": label[:100],
                                "recognition_label": recognition[:100],
                                "is_deleted": False,
                                "content_version_id": cv_id,
                            },
                        )
                        tally("sign", created)
                        module_sign_count += 1

                # One quiz per module (skip modules where no signs resolved)
                if module_sign_count:
                    _, created = upsert(
                        db,
                        Quiz,
                        {"module_id": module.module_id, "content_version_id": cv_id},
                        {
                            "title": f"{module.title} Quiz"[:100],
                            "passing_score": QUIZ_PASSING_SCORE,
                            "time_limit_seconds": None,
                            "is_deleted": False,
                        },
                    )
                    tally("quiz", created)

                print(f"  {m_idx}. {mdata['name']}: {len(mdata['lessons'])} lessons, "
                      f"{module_sign_count} signs, quiz covers {module_sign_count * 2} "
                      f"generated questions (camera + MC)")

            # --- Badges ------------------------------------------------------
            badge_defs = list(STATIC_BADGES)
            badge_defs += [
                (f"{m.title} Master", f"Complete every lesson and pass the quiz in {m.title}.")
                for m in {id(v): v for v in modules_by_key.values()}.values()
            ]
            for name, desc in badge_defs:
                _, created = upsert(
                    db, Badge, {"badge_name": name}, {"description": desc, "is_deleted": False}
                )
                tally("badge", created)

            # --- Minigames ---------------------------------------------------
            for mg in minigames_data:
                code = mg.get("minigame_id") or mg.get("minigame_code")
                module = modules_by_key.get(slugify(str(mg.get("module_id", ""))))
                if not code or module is None:
                    print(f"WARNING: skipping minigame {code!r}: unknown module {mg.get('module_id')!r}")
                    continue
                _, created = upsert(
                    db,
                    Minigame,
                    {"minigame_code": code},
                    {
                        "game_name": mg.get("game_name"),
                        "game_type": mg.get("game_type"),
                        "module_id": module.module_id,
                        "description": mg.get("description"),
                        "config": json.dumps(mg.get("config", {}), ensure_ascii=False),
                        "is_deleted": False,
                        "content_version_id": cv_id,
                    },
                )
                tally("minigame", created)

            if dry_run:
                db.rollback()
                print("\nDRY RUN: rolled back, nothing written.")
            else:
                db.commit()
                print("\nCommitted.")

        except Exception:
            db.rollback()
            raise

    print("\nSummary:")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    if missing_media:
        print(f"\n{len(missing_media)} signs skipped (no unused matching media_files row):")
        for item in missing_media:
            print(f"  - {item}")
    if unlabeled:
        print(f"\n{len(unlabeled)} signs not found in 105labels.json (recognition_label was derived):")
        print("  " + ", ".join(unlabeled))


if __name__ == "__main__":
    migrate_content(dry_run="--dry-run" in sys.argv)