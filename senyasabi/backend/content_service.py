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
from pathlib import Path
import re
from typing import Protocol

from . import config
from .recognition_labels import normalize_label

MODULE_CODES = ("greeting", "survival", "number", "days", "family")
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
    "Months of the Year": "months",
    "Action Words": "actions",
}
MODULE_CODES = tuple(c for c in DATASET_MODULE_CODES.values() if c != ALPHABET)  # word modules
ALL_MODULE_CODES = (ALPHABET, *MODULE_CODES)

_NUMBER_ALIASES = dict(zip("1 2 3 4 5 6 7 8 9 10".split(),
                           "ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN".split()))
_ONES = ("ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE THIRTEEN "
         "FOURTEEN FIFTEEN SIXTEEN SEVENTEEN EIGHTEEN NINETEEN").split()
_TENS = ("", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY")


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
    modules, module, lesson = [], None, None
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
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
    def get_signs(self, module_code):
        if module_code == "alphabet":
            return [SignRecord("alphabet", char.lower(), char, char)
                    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        if module_code not in MODULE_CODES:
            raise ValueError(f"Unknown module: {module_code}")
        entries = json.loads((ROOT / "resources/data/105labels.json").read_text(encoding="utf-8-sig"))
        # Source training IDs are not database IDs. Adapters supply real DB IDs.
        return [SignRecord(module_code, entry.get("sign_code") or readable_code(entry["label"]),
                           entry["label"], normalize_label(entry.get("recognition_label", entry["label"])))
                for entry in entries if entry["category"].casefold() == module_code]


_repository: ContentRepository = BundledContentRepository()


def get_modules() -> list[ModuleRecord]:
    return _repository.get_modules()


def get_module(module_code) -> ModuleRecord:
    code = module_code.casefold()
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
    return next((sign for sign in get_signs_for_module(module_code)
                 if sign.sign_code == sign_code), None)


def get_lesson_id(module_code: str, lesson_order: int = 1) -> int | None:
    """(module_code, lesson_order) -> lesson_id from the local SQLite cache.
    IDs are server-assigned, so there is no static fallback."""
    try:
        from .database.session import SessionLocal
        from .database.models import Lesson, Module
        with SessionLocal() as db:
            mod = db.query(Module).filter(Module.module_code == module_code.casefold(),
                                          Module.is_deleted.is_(False)).first()
            if not mod:
                return None
            lesson = db.query(Lesson).filter(Lesson.parent_module == mod.module_id,
                                             Lesson.lesson_order == lesson_order,
                                             Lesson.is_deleted.is_(False)).first()
            return lesson.lesson_id if lesson else None
    except Exception:
        return None

