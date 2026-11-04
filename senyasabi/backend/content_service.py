"""Logical content boundary, built from resources/data/expected_dataset.md.

The dataset is the single source of truth for modules, lessons and signs.
105labels.json is consulted ONLY to find the model's recognition label for a sign.
Codes here must match backend/scripts/seed_from_dataset.py:
  module_code = DATASET_MODULE_CODES[name], lesson_code = f"{module}_lesson_{n}",
  sign_code   = readable_code(label).
"""
from dataclasses import dataclass
from functools import lru_cache
import json
import logging
from pathlib import Path
import re
from typing import Protocol

from . import config
from .recognition_labels import normalize_label

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = config.DATA_DIR / "expected_dataset.md"
LABELS_PATH = config.DATA_DIR / "105labels.json"

ALPHABET = "alphabet"
# dataset module name -> module_code (import this in the seed script too)
DATASET_MODULE_CODES = {
    "The Manual Alphabet": ALPHABET,
    "Numbers": "number",
    "Family Members": "family",
    "Basic Communication": "communication",
    "Days of the Week": "days",
    "Calendar": "calendar",
    "Action Words": "actions",
}
MODULE_CODES = tuple(c for c in DATASET_MODULE_CODES.values() if c != ALPHABET)  # word modules
ALL_MODULE_CODES = (ALPHABET, *MODULE_CODES)

_NUMBER_ALIASES = dict(zip("1 2 3 4 5 6 7 8 9 10".split(),
                           "ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN".split()))
_ONES = ("ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE THIRTEEN "
         "FOURTEEN FIFTEEN SIXTEEN SEVENTEEN EIGHTEEN NINETEEN").split()
_TENS = ("", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY")

MODEL_CATEGORY = {   # (module, lesson_number) -> model folder
    ("communication", 1): "greeting", ("communication", 2): "greeting",
    ("communication", 3): "greeting",
    ("communication", 4): "survival", ("communication", 5): "survival",
}

MODEL_TO_MODULE = {"greeting": "communication", "survival": "communication"}
def content_module(code):
    code = code.casefold()
    return MODEL_TO_MODULE.get(code, code)

def model_category(module_code, lesson_number=1):
    return MODEL_CATEGORY.get((module_code, lesson_number), module_code)


def readable_code(label):
    return re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")


def number_to_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] + (f" {_ONES[ones]}" if ones else "")
    for size, name in ((1000, "THOUSAND"), (100, "HUNDRED")):
        if n >= size:
            head, rest = divmod(n, size)
            return f"{number_to_words(head)} {name}" + (f" {number_to_words(rest)}" if rest else "")


def fingerspell_text(label: str) -> str:
    """What a learner physically fingerspells for a label: A-Z words only.
    '100' -> 'ONE HUNDRED'; "Happy Valentine's Day" -> 'HAPPY VALENTINES DAY'."""
    label = (label or "").strip()
    if label.isdigit():
        return number_to_words(int(label))
    words = ("".join(c for c in word if "A" <= c <= "Z") for word in label.upper().split())
    return " ".join(word for word in words if word)


@dataclass(frozen=True)
class SignRecord:
    module_code: str
    sign_code: str
    label: str
    recognition_label: str
    sign_id: int | None = None
    lesson_id: int | None = None
    media_id: int | None = None
    lesson_code: str | None = None


@dataclass(frozen=True)
class LessonRecord:
    module_code: str
    lesson_code: str
    title: str
    order: int
    signs: tuple[SignRecord, ...]


@dataclass(frozen=True)
class ModuleRecord:
    module_code: str
    title: str
    order: int
    lessons: tuple[LessonRecord, ...]

    @property
    def signs(self) -> tuple[SignRecord, ...]:
        return tuple(sign for lesson in self.lessons for sign in lesson.signs)


# ---- dataset parsing -------------------------------------------------------
_MODULE_RE = re.compile(r"^##\s*Module\s+\d+\s*[:.\-]?\s*(.+)$", re.IGNORECASE)


def _parse_dataset(path):
    """[(module_name, [(lesson_title, [label, ...])])]. Sign lines directly under a
    module (no ###) go into a default lesson named after the module."""
    try:
        content = Path(path).read_text(encoding="utf-8-sig")
    except OSError as e:
        logger.error("Failed to read dataset file %s: %s", path, e)
        raise
    except UnicodeDecodeError as e:
        logger.error("Failed to decode dataset file %s: %s", path, e)
        raise
    
    modules, module, lesson = [], None, None
    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = _MODULE_RE.match(line)
        if match:
            module, lesson = (match.group(1).strip(), []), None
            modules.append(module)
            continue
        if module is None:
            continue
        if line.startswith("###"):
            lesson = (line.lstrip("#").strip(), [])
            module[1].append(lesson)
            continue
        if line.startswith("#"):
            continue
        labels = [s.strip() for s in line.lstrip("-*• ").split(",") if s.strip()]
        if labels:
            if lesson is None:
                lesson = (module[0], [])
                module[1].append(lesson)
            lesson[1].extend(labels)
    return modules


@lru_cache(maxsize=1)
def _recognition_labels():
    try:
        items = json.loads(LABELS_PATH.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return {readable_code(normalize_label(i["label"])): normalize_label(i["label"]) for i in items}


def _recognition_label(module_code, label):
    if module_code == ALPHABET:
        return label
    key = readable_code(normalize_label(_NUMBER_ALIASES.get(label, label)))
    return _recognition_labels().get(key) or normalize_label(label)


@lru_cache(maxsize=1)
def _load_modules(path=DATASET_PATH):
    modules = []
    for order, (name, lessons) in enumerate(_parse_dataset(path), 1):
        code = DATASET_MODULE_CODES.get(name)
        if code is None:
            raise ValueError(f"Dataset module {name!r} has no code in DATASET_MODULE_CODES")
        seen, records = set(), []
        for number, (title, labels) in enumerate(lessons, 1):
            lesson_code = f"{code}_lesson_{number}"
            signs = []
            for label in labels:
                slug = readable_code(label)
                if slug in seen:          # a sign belongs to one lesson per module
                    continue
                seen.add(slug)
                signs.append(SignRecord(code, slug if code != ALPHABET else label.lower(), label,
                                        _recognition_label(code, label), lesson_code=lesson_code))
            if signs:
                records.append(LessonRecord(code, lesson_code, title, len(records) + 1, tuple(signs)))
        modules.append(ModuleRecord(code, name, order, tuple(records)))
    return tuple(modules)


def reload_content():
    """Drop parsed caches (tests, or after editing the dataset at runtime)."""
    _load_modules.cache_clear()
    _recognition_labels.cache_clear()


# ---- repository -------------------------------------------------------------
class ContentRepository(Protocol):
    def get_modules(self) -> list[ModuleRecord]: ...


class BundledContentRepository:
    def get_modules(self): 
        return list(_load_modules())

    def get_signs(self, module_code):
        if module_code == "alphabet":
            return [SignRecord("alphabet", char.lower(), char, char)
                    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        if module_code in ("basic_communication", "communication"):
            return self.get_signs("greeting") + self.get_signs("survival")
        entries = json.loads((ROOT / "resources/data/105labels.json").read_text(encoding="utf-8-sig"))
        matching = [SignRecord(module_code, entry.get("sign_code") or readable_code(entry["label"]),
                               entry["label"], normalize_label(entry.get("recognition_label", entry["label"])))
                    for entry in entries if entry["category"].casefold() == module_code]
        if not matching and module_code not in MODULE_CODES:
            raise ValueError(f"Unknown module: {module_code}")
        return matching


_repository: ContentRepository = BundledContentRepository()


def get_modules() -> list[ModuleRecord]:
    return _repository.get_modules()


def get_module(module_code) -> ModuleRecord:
    code = content_module(module_code)   # greeting/survival -> communication
    if code == "basic_communication":
        code = "communication"
    for module in get_modules():
        if module.module_code == code:
            return module
    raise ValueError(f"Unknown module: {module_code}")


def get_lessons_for_module(module_code) -> list[LessonRecord]:
    return list(get_module(module_code).lessons)


def get_signs_for_module(module_code) -> list[SignRecord]:
    return list(get_module(module_code).signs)


def get_signs_for_lesson(module_code, lesson_number) -> list[SignRecord]:
    lessons = get_module(module_code).lessons
    if not 1 <= lesson_number <= len(lessons):
        raise ValueError(f"{module_code} has no lesson {lesson_number}")
    return list(lessons[lesson_number - 1].signs)


def get_words_for_module(module_code):
    return [sign.label for sign in get_signs_for_module(module_code)]


def get_sign(module_code, sign_code):
    target = readable_code(sign_code)
    clean_target = re.sub(r"[^a-z0-9]+", "", str(sign_code).casefold())
    for sign in get_signs_for_module(module_code):
        if sign.sign_code == sign_code or readable_code(sign.sign_code) == target or readable_code(sign.label) == target:
            return sign
        if re.sub(r"[^a-z0-9]+", "", sign.sign_code.casefold()) == clean_target:
            return sign
        if re.sub(r"[^a-z0-9]+", "", sign.label.casefold()) == clean_target:
            return sign
    return None


def get_lesson_id(module_code: str, lesson_order: int = 1) -> int | None:
    """Resolve (module_code, lesson_order) to lesson_id from local SQLite cache."""
    code = module_code.casefold()
    if code in ("basic_communication", "communication"):
        if lesson_order <= 3:
            code = "greeting"
        else:
            code = "survival"
            lesson_order = lesson_order - 3
    try:
        from .database.session import SessionLocal
        from .database.models import Lesson, Module
        with SessionLocal() as db:
            mod = db.query(Module).filter(Module.module_code == code).first()
            if not mod:
                return None
            lesson = db.query(Lesson).filter(Lesson.parent_module == mod.module_id,
                                             Lesson.lesson_order == lesson_order,
                                             Lesson.is_deleted.is_(False)).first()
            return lesson.lesson_id if lesson else None
    except Exception:
        # Static fallback if database is not available
        offset = {"alphabet": 72, "greeting": 76, "survival": 79, "number": 82,
                  "calendar": 85, "days": 88, "family": 91, "relationships": 94,
                  "color": 97, "food": 100, "drink": 103}.get(code)
        if offset is not None:
            return offset + (lesson_order - 1)
        return None


def get_synced_lessons(module_code):
    """Lessons from the synced SQLite cache (Supabase content), falling back to the
    bundled dataset when the cache is empty.
    -> [{"lesson_id", "number" (1-based), "title", "words": [labels]}]"""
    code = module_code.casefold()
    try:
        from sqlalchemy import func, select
        from .database.session import SessionLocal
        from .database import models as m
        with SessionLocal() as db:
            lessons = db.scalars(
                select(m.Lesson)
                .join(m.Module, m.Module.module_id == m.Lesson.parent_module)
                .where(func.lower(m.Module.module_code) == code,
                       m.Module.is_deleted.is_(False), m.Lesson.is_deleted.is_(False),
                       m.Lesson.is_active.is_(True))
                .order_by(m.Lesson.lesson_order)).all()
            result = []
            for lesson in lessons:
                labels = db.scalars(
                    select(m.Sign.label)
                    .join(m.LessonSign, m.LessonSign.sign_id == m.Sign.sign_id)
                    .where(m.LessonSign.lesson_id == lesson.lesson_id,
                           m.LessonSign.is_deleted.is_(False), m.Sign.is_deleted.is_(False))
                    .order_by(m.LessonSign.display_order)).all()
                if labels:
                    result.append(dict(lesson_id=lesson.lesson_id, number=len(result) + 1,
                                       title=lesson.title, words=list(labels)))
            if result:
                return result
    except Exception as error:
        logger.warning("Synced lessons unavailable for %s: %s", code, error)
    return [dict(lesson_id=None, number=l.order, title=l.title,
                 words=[s.label for s in l.signs]) for l in get_lessons_for_module(code)]

MODULE_LESSONS_PATH = ROOT / "resources" / "data" / "module_lessons.json"


def _load_module_lessons() -> dict[str, list[dict]]:
    if MODULE_LESSONS_PATH.is_file():
        try:
            return json.loads(MODULE_LESSONS_PATH.read_text(encoding="utf-8-sig"))
        except OSError as e:
            logger.warning("Failed to read module lessons file %s: %s", MODULE_LESSONS_PATH, e)
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse module lessons JSON %s: %s", MODULE_LESSONS_PATH, e)
        except Exception as e:
            logger.warning("Unexpected error loading module lessons %s: %s", MODULE_LESSONS_PATH, e)
    return {
        "alphabet": [
            {"lesson_number": 1, "title": "Letters A - F", "words": list("ABCDEF")},
            {"lesson_number": 2, "title": "Letters G - L", "words": list("GHIJKL")},
            {"lesson_number": 3, "title": "Letters M - R", "words": list("MNOPQR")},
            {"lesson_number": 4, "title": "Letters S - Z", "words": list("STUVWXYZ")},
        ],
        "number": [
            {"lesson_number": 1, "title": "One to Five", "words": ["ONE", "TWO", "THREE", "FOUR", "FIVE"]},
            {"lesson_number": 2, "title": "Six to Ten", "words": ["SIX", "SEVEN", "EIGHT", "NINE", "TEN"]},
        ],
        "family": [
            {"lesson_number": 1, "title": "Immediate Family", "words": ["FATHER", "MOTHER", "PARENTS"]},
            {"lesson_number": 2, "title": "Children & Young Family", "words": ["SON", "DAUGHTER"]},
            {"lesson_number": 3, "title": "Older Generation", "words": ["GRANDFATHER", "GRANDMOTHER", "UNCLE", "AUNTIE"]},
            {"lesson_number": 4, "title": "Same / Younger Generation", "words": ["COUSIN"]},
        ],
        "greeting": [
            {"lesson_number": 1, "title": "Daily Greetings & Farewells", "words": ["GOOD MORNING", "GOOD AFTERNOON", "GOOD EVENING", "HELLO", "SEE YOU TOMORROW"]},
            {"lesson_number": 2, "title": "Courtesy", "words": ["THANK YOU", "YOURE WELCOME"]},
            {"lesson_number": 3, "title": "Introductions & Small Talk", "words": ["NICE TO MEET YOU", "HOW ARE YOU", "IM FINE"]},
            {"lesson_number": 4, "title": "Responses & Answers", "words": ["YES", "NO", "CORRECT", "WRONG"]},
            {"lesson_number": 5, "title": "Understanding & Pacing", "words": ["UNDERSTAND", "DONT UNDERSTAND", "KNOW", "DONT KNOW", "SLOW", "FAST"]},
        ],
        "days": [
            {"lesson_number": 1, "title": "Days of the Week", "words": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]},
            {"lesson_number": 2, "title": "Relative Days", "words": ["TODAY", "TOMORROW", "YESTERDAY"]},
        ],
        "calendar": [
            {"lesson_number": 1, "title": "First Six Months", "words": ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE"]},
            {"lesson_number": 2, "title": "Last Six Months", "words": ["JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]},
        ],
        "actions": [
            {"lesson_number": 1, "title": "Action Words", "words": []},
        ],
    }


MODULE_LESSONS: dict[str, list[dict]] = _load_module_lessons()

def get_lesson_model_code(module_code: str, lesson_order: int = 1) -> str:
    code = module_code.casefold()
    if code in MODEL_TO_MODULE:   # already a model folder (greeting/survival)
        return code
    for lesson in get_lessons_for_module(code):
        if lesson.order == lesson_order and lesson.module_code:
            return model_category(str(lesson.module_code).casefold(), lesson.order)
    if code in ("basic_communication", "communication"):
        return "greeting" if lesson_order <= 3 else "survival"
    return code


def get_words_for_lesson(module_code, lesson_order=1) -> list[str]:
    return [s.label for s in get_signs_for_lesson(module_code, lesson_order)]