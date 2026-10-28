"""Logical content boundary. A cache/DB adapter can replace the bundled repository."""
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Protocol
from .recognition_labels import normalize_label

MODULE_CODES = ("greeting", "survival", "number", "days", "family")
ROOT = Path(__file__).resolve().parents[1]


def readable_code(label):
    return re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")


@dataclass(frozen=True)
class SignRecord:
    module_code: str
    sign_code: str
    label: str
    recognition_label: str
    sign_id: int | None = None
    lesson_id: int | None = None
    media_id: int | None = None


class ContentRepository(Protocol):
    def get_signs(self, module_code: str) -> list[SignRecord]: ...


class BundledContentRepository:
    def get_signs(self, module_code):
        if module_code == "alphabet":
            return [SignRecord("alphabet", char.lower(), char, char)
                    for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        entries = json.loads((ROOT / "resources/data/105labels.json").read_text(encoding="utf-8-sig"))
        matching = [SignRecord(module_code, entry.get("sign_code") or readable_code(entry["label"]),
                               entry["label"], normalize_label(entry.get("recognition_label", entry["label"])))
                    for entry in entries if entry["category"].casefold() == module_code]
        if not matching and module_code not in MODULE_CODES:
            raise ValueError(f"Unknown module: {module_code}")
        return matching


_repository: ContentRepository = BundledContentRepository()


def get_signs_for_module(module_code):
    return _repository.get_signs(module_code.casefold())


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
    try:
        from .database.session import SessionLocal
        from .database.models import Lesson, Module
        with SessionLocal() as db:
            mod = db.query(Module).filter(Module.module_code == module_code.casefold()).first()
            if not mod:
                return None
            lesson = db.query(Lesson).filter(
                Lesson.parent_module == mod.module_id,
                Lesson.lesson_order == lesson_order
            ).first()
            return lesson.lesson_id if lesson else None
    except Exception:
        # Static fallback if database is not available
        offset = {"alphabet": 72, "greeting": 76, "survival": 79, "number": 82,
                  "calendar": 85, "days": 88, "family": 91, "relationships": 94,
                  "color": 97, "food": 100, "drink": 103}.get(module_code.casefold())
        if offset is not None:
            return offset + (lesson_order - 1)
        return None




MODULE_LESSONS_PATH = ROOT / "resources" / "data" / "module_lessons.json"


def _load_module_lessons() -> dict[str, list[dict]]:
    if MODULE_LESSONS_PATH.is_file():
        try:
            return json.loads(MODULE_LESSONS_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
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
        ],
        "days": [
            {"lesson_number": 1, "title": "Days of the Week", "words": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]},
            {"lesson_number": 2, "title": "Relative Days", "words": ["TODAY", "TOMORROW", "YESTERDAY"]},
        ],
        "survival": [
            {"lesson_number": 1, "title": "Responses & Answers", "words": ["YES", "NO", "CORRECT", "WRONG"]},
            {"lesson_number": 2, "title": "Understanding & Pacing", "words": ["UNDERSTAND", "DONT UNDERSTAND", "KNOW", "DONT KNOW", "SLOW", "FAST"]},
        ],
    }


MODULE_LESSONS: dict[str, list[dict]] = _load_module_lessons()


def get_lessons_for_module(module_code: str) -> list[dict]:
    return MODULE_LESSONS.get(module_code.casefold(), [])


def get_words_for_lesson(module_code: str, lesson_order: int = 1) -> list[str]:
    lessons = get_lessons_for_module(module_code)
    for lesson in lessons:
        if lesson["lesson_number"] == lesson_order:
            return list(lesson["words"])
    return []
