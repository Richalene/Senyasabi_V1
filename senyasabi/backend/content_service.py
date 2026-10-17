"""Logical content boundary. A cache/DB adapter can replace the bundled repository."""
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Protocol
from .recognition_labels import normalize_label

MODULE_CODES = ("greeting", "survival", "number", "calendar", "days", "family",
                "relationships", "color", "food", "drink")
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
        if module_code not in MODULE_CODES:
            raise ValueError(f"Unknown module: {module_code}")
        entries = json.loads((ROOT / "resources/data/105labels.json").read_text(encoding="utf-8-sig"))
        # Source training IDs are not database IDs. Adapters supply real DB IDs.
        return [SignRecord(module_code, entry.get("sign_code") or readable_code(entry["label"]),
                           entry["label"], normalize_label(entry.get("recognition_label", entry["label"])))
                for entry in entries if entry["category"].casefold() == module_code]


_repository: ContentRepository = BundledContentRepository()


def get_signs_for_module(module_code):
    return _repository.get_signs(module_code.casefold())


def get_words_for_module(module_code):
    return [sign.label for sign in get_signs_for_module(module_code)]


def get_sign(module_code, sign_code):
    return next((sign for sign in get_signs_for_module(module_code)
                 if sign.sign_code == sign_code), None)
