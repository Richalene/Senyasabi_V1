"""
Lesson / word / VRM-sign-image content.

No UI, no PIL/Tk-specific image objects — VRM images are returned as plain
Path objects. Convert to QPixmap in the Qt layer, e.g.:

    path = content.vrm_image_path("A")
    pixmap = QPixmap(str(path)) if path else QPixmap()
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random

from . import config


class LessonContent:
    def __init__(self, lessons_path: Path = config.LESSONS_PATH,
                 vrm_dir: Path = config.VRM_SIGNS_DIR,
                 alphabet_labels: Optional[List[str]] = None):
        self.lessons: Dict[str, List[str]] = json.loads(
            Path(lessons_path).read_text(encoding="utf-8"))
        self.vrm_dir = Path(vrm_dir)

        if alphabet_labels is not None:
            self.class_names: List[str] = list(alphabet_labels)
        elif config.ALPHABET_LABELS_PATH is not None:
            self.class_names = json.loads(Path(config.ALPHABET_LABELS_PATH).read_text())
        else:
            self.class_names = list(config.ALPHABET_LABELS_FALLBACK)

    # ---- categories / words -------------------------------------------
    def categories(self) -> List[str]:
        return list(self.lessons.keys())

    def words_in(self, category: str) -> List[str]:
        return self.lessons[category]

    def all_words(self) -> List[Tuple[str, str]]:
        """(category, word) pairs across every category."""
        return [(cat, w) for cat, words in self.lessons.items() for w in words]

    @staticmethod
    def letters_of(word: str) -> List[str]:
        return [c for c in word if c != ' ']

    # ---- alphabet -------------------------------------------------------
    def alphabet(self) -> List[str]:
        return list(self.class_names)

    # ---- shuffled queue builders (mirrors the old app's menu actions) ---
    def shuffled_all_words(self) -> List[Tuple[str, str]]:
        items = self.all_words()
        random.shuffle(items)
        return items

    def shuffled_category(self, category: str) -> List[Tuple[str, str]]:
        items = [(category, w) for w in self.words_in(category)]
        random.shuffle(items)
        return items

    def megashuffle_queue(self) -> List[Tuple[Optional[str], str]]:
        """Every alphabet letter (category=None) mixed with every lesson word."""
        items: List[Tuple[Optional[str], str]] = [(None, l) for l in self.alphabet()]
        items += self.all_words()
        random.shuffle(items)
        return items

    # ---- images -----------------------------------------------------------
    def vrm_image_path(self, label: str) -> Optional[Path]:
        """Finds the reference sign image for a letter/label, if any."""
        for ext in ('.png', '.jpg', '.jpeg', '.webp'):
            p = self.vrm_dir / f"{label}{ext}"
            if p.exists():
                return p
        return None
