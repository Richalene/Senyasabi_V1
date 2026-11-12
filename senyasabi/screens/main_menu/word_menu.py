"""
Word Lessons Menu — scrollable list of category rows.
Each row opens a WordLessonWidget for that category's words.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from backend.content_service import MODULE_CODES, get_words_for_module
from screens.main_menu.alphabet_menu import LESSON_LETTERS
from screens.navigation import BackButton, install_page_menu

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea
)

_ROOT        = Path(__file__).resolve().parents[2]
_LABELS_PATH = _ROOT / "resources" / "data" / "105labels.json"
_UI_FILE     = _ROOT / "ui" / "designer" / "word_menu.ui"

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_BG       = "#0f1117"
_CARD_BG  = "#1a1f2e"
_CARD_HOV = "#212840"
_BORDER   = "#2a3150"
_ACCENT   = "#5ecf8a"   # green for word lessons
_TEXT_W   = "#ffffff"
_TEXT_MID = "#5a6080"

_ROW_STYLE = (
    f"background-color:{_CARD_BG}; border:2px solid {_BORDER};"
    "border-radius:14px;"
)
_ROW_HOV = (
    f"background-color:{_CARD_HOV}; border:2px solid {_ACCENT};"
    "border-radius:14px;"
)
_ROW_DISABLED = (
    f"background-color:{_CARD_BG}; border:2px solid {_BORDER};"
    "border-radius:14px; opacity:0.65;"
)


def _load_categories() -> dict[str, list[str]]:
    return {code.upper(): get_words_for_module(code) for code in MODULE_CODES}


def _menu_entries() -> list[dict]:
    alphabet_words = [ch for letters in LESSON_LETTERS.values() for ch in letters]
    return [
        {"number": 1, "code": "alphabet", "title": "FSL Alphabet", "words": alphabet_words, "coming_soon": False},
        {"number": 2, "code": "number", "title": "Numbers", "words": get_words_for_module("number"), "coming_soon": False},
        {"number": 3, "code": "family", "title": "Family Members", "words": get_words_for_module("family"), "coming_soon": False},
        {"number": 4, "code": "greeting", "title": "Basic Communication", "words": get_words_for_module("basic_communication"), "coming_soon": False},
        {"number": 5, "code": "days", "title": "Days of the Week", "words": get_words_for_module("days"), "coming_soon": False},
        {"number": 6, "code": "months", "title": "Months of the Year", "words": [], "coming_soon": True},
        {"number": 7, "code": "actions", "title": "Action Words", "words": [], "coming_soon": True},
    ]


class WordMenuWidget(QWidget):
    """
    Signals
    -------
    go_back
    category_chosen(category, words)
    """
    go_back         = Signal()
    category_chosen = Signal(str, list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        loader   = QUiLoader()
        self._ui = loader.load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")
        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle("SenyaSabi — Word Lessons")
        install_page_menu(self, canvas_size=QSize(1306, 753))

        self.back_button = BackButton.replace(self._ui.findChild(QPushButton, "backBtn"))
        self.back_button.setGeometry(40,24,52,52)
        self.back_button.clicked.connect(self.go_back)

        self._categories = _load_categories()
        self._entries = _menu_entries()
        self._populate_scroll()

    def _populate_scroll(self):
        scroll: QScrollArea = self._ui.findChild(QScrollArea, "scrollArea")

        container = QWidget()
        container.setStyleSheet(f"background:{_BG};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(60, 16, 60, 24)
        layout.setSpacing(12)

        for entry in self._entries:
            row = self._make_row(
                entry["number"],
                entry["title"],
                entry["words"],
                code=entry["code"],
                coming_soon=entry["coming_soon"],
            )
            layout.addWidget(row)

        layout.addStretch()
        scroll.setWidget(container)

    def _make_row(
        self,
        number: int,
        cat: str,
        words: list[str],
        *,
        code: str | None = None,
        coming_soon: bool = False,
    ) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet(_ROW_DISABLED if coming_soon else _ROW_STYLE)
        frame.setCursor(Qt.CursorShape.ArrowCursor if coming_soon else Qt.CursorShape.PointingHandCursor)

        h = QHBoxLayout(frame)
        h.setContentsMargins(28, 0, 28, 0)
        h.setSpacing(16)

        # lesson number badge
        badge = QLabel(f"{number:02d}")
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:{_TEXT_MID if coming_soon else _ACCENT}; color:#0f1117; font-size:13px;"
            "font-weight:800; border-radius:8px;"
        )

        name = QLabel(cat)
        name.setStyleSheet(
            f"color:{_TEXT_W}; font-size:16px; font-weight:700; background:transparent;"
        )

        detail_text = "Lesson coming soon" if coming_soon else f"{len(words)} signs"
        count = QLabel(detail_text)
        count.setStyleSheet(
            f"color:{_TEXT_MID}; font-size:13px; background:transparent;"
        )

        arrow = QLabel("" if coming_soon else "→")
        arrow.setStyleSheet(
            f"color:{_ACCENT}; font-size:18px; font-weight:700; background:transparent;"
        )

        h.addWidget(badge)
        h.addWidget(name)
        h.addStretch()
        h.addWidget(count)
        h.addWidget(arrow)

        if not coming_soon:
            emit_code = (code or cat).upper()
            frame.enterEvent = lambda e, f=frame: f.setStyleSheet(_ROW_HOV)
            frame.leaveEvent = lambda e, f=frame: f.setStyleSheet(_ROW_STYLE)
            frame.mousePressEvent = (
                lambda e, c=emit_code, w=words: self.category_chosen.emit(c, w)
            )
        return frame

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
