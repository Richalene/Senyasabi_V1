"""
Word Lessons Menu — scrollable list of category rows.
Each row opens a WordLessonWidget for that category's words.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea
)

_HERE        = Path(__file__).resolve().parent
_ROOT        = _HERE.parent
_LABELS_PATH = _ROOT / "resources" / "data" / "105labels.json"
_UI_FILE     = _HERE / "word_menu.ui"

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


def _load_categories() -> dict[str, list[str]]:
    data = json.loads(_LABELS_PATH.read_text(encoding="utf-8"))
    cats: dict[str, list[str]] = defaultdict(list)
    for entry in data:
        cats[entry["category"]].append(entry["label"])
    return dict(cats)


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

        self._ui.findChild(QPushButton, "backBtn").clicked.connect(self.go_back)

        self._categories = _load_categories()
        self._populate_scroll()

    def _populate_scroll(self):
        scroll: QScrollArea = self._ui.findChild(QScrollArea, "scrollArea")

        container = QWidget()
        container.setStyleSheet(f"background:{_BG};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(60, 16, 60, 24)
        layout.setSpacing(12)

        for i, (cat, words) in enumerate(self._categories.items(), start=1):
            row = self._make_row(i, cat, words)
            layout.addWidget(row)

        layout.addStretch()
        scroll.setWidget(container)

    def _make_row(self, number: int, cat: str, words: list[str]) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet(_ROW_STYLE)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)

        h = QHBoxLayout(frame)
        h.setContentsMargins(28, 0, 28, 0)
        h.setSpacing(16)

        # lesson number badge
        badge = QLabel(f"{number:02d}")
        badge.setFixedSize(36, 36)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background:{_ACCENT}; color:#0f1117; font-size:13px;"
            "font-weight:800; border-radius:8px;"
        )

        name = QLabel(cat.title())
        name.setStyleSheet(
            f"color:{_TEXT_W}; font-size:16px; font-weight:700; background:transparent;"
        )

        count = QLabel(f"{len(words)} words")
        count.setStyleSheet(
            f"color:{_TEXT_MID}; font-size:13px; background:transparent;"
        )

        arrow = QLabel("→")
        arrow.setStyleSheet(
            f"color:{_ACCENT}; font-size:18px; font-weight:700; background:transparent;"
        )

        h.addWidget(badge)
        h.addWidget(name)
        h.addStretch()
        h.addWidget(count)
        h.addWidget(arrow)

        frame.enterEvent = lambda e, f=frame: f.setStyleSheet(_ROW_HOV)
        frame.leaveEvent = lambda e, f=frame: f.setStyleSheet(_ROW_STYLE)
        frame.mousePressEvent = (
            lambda e, c=cat, w=words: self.category_chosen.emit(c, w)
        )
        return frame

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
