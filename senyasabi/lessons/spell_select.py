"""
Spell Mode selectors — category screen then word screen.
Both load their layout from .ui files; Python only populates
the QScrollArea contents dynamically (unavoidable for variable-length lists).
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
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QSizePolicy
)

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_LABELS_PATH      = _ROOT / "resources" / "data" / "105labels.json"
_CAT_UI_FILE      = _HERE / "spell_category.ui"
_WORD_UI_FILE     = _HERE / "spell_word.ui"

# ── colours ───────────────────────────────────────────────────────────────────
_BG        = "#0f1117"
_CARD_BG   = "#1a1f2e"
_CARD_HOV  = "#212840"
_BORDER    = "#2a3150"
_ACCENT    = "#a87eed"
_TEXT_W    = "#ffffff"
_TEXT_MID  = "#5a6080"

_ROW_STYLE = (
    f"background-color:{_CARD_BG}; border:2px solid {_BORDER};"
    "border-radius:14px;"
)
_ROW_HOV   = (
    f"background-color:{_CARD_HOV}; border:2px solid {_ACCENT};"
    "border-radius:14px;"
)
_CHIP_STYLE = (
    f"background-color:{_CARD_BG}; border:2px solid {_BORDER};"
    "border-radius:10px;"
)
_CHIP_HOV  = (
    f"background-color:{_CARD_HOV}; border:2px solid {_ACCENT};"
    "border-radius:10px;"
)


def _load_categories() -> dict[str, list[str]]:
    data = json.loads(_LABELS_PATH.read_text(encoding="utf-8"))
    cats: dict[str, list[str]] = defaultdict(list)
    for entry in data:
        cats[entry["category"]].append(entry["label"])
    return dict(cats)


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY SELECT
# ══════════════════════════════════════════════════════════════════════════════

class SpellCategoryWidget(QWidget):
    """
    Scrollable list of category rows loaded from spell_category.ui.

    Signals
    -------
    go_back
    category_chosen(category_name, words_list)
    """
    go_back         = Signal()
    category_chosen = Signal(str, list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        loader    = QUiLoader()
        self._ui  = loader.load(str(_CAT_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_CAT_UI_FILE}")
        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle("SenyaSabi — Spell: Choose Category")

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

        for cat, words in self._categories.items():
            row = self._make_row(cat, words)
            layout.addWidget(row)

        layout.addStretch()
        scroll.setWidget(container)

    def _make_row(self, cat: str, words: list[str]) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(80)
        frame.setStyleSheet(_ROW_STYLE)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)

        h = QHBoxLayout(frame)
        h.setContentsMargins(28, 0, 28, 0)
        h.setSpacing(0)

        name = QLabel(cat)
        name.setStyleSheet(
            f"color:{_TEXT_W}; font-size:16px; font-weight:700; background:transparent;"
        )

        count = QLabel(f"{len(words)} words")
        count.setStyleSheet(
            f"color:{_TEXT_MID}; font-size:13px; background:transparent;"
        )
        count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        arrow = QLabel("→")
        arrow.setStyleSheet(
            f"color:{_ACCENT}; font-size:18px; font-weight:700;"
            "background:transparent; margin-left:16px;"
        )

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


# ══════════════════════════════════════════════════════════════════════════════
# WORD SELECT
# ══════════════════════════════════════════════════════════════════════════════

class SpellWordWidget(QWidget):
    """
    Scrollable grid of word chips loaded from spell_word.ui.

    Signals
    -------
    go_back
    word_chosen(word)
    """
    go_back     = Signal()
    word_chosen = Signal(str)

    def __init__(self, category: str, words: list[str],
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._category = category
        self._words    = words

        loader   = QUiLoader()
        self._ui = loader.load(str(_WORD_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_WORD_UI_FILE}")
        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle(f"SenyaSabi — Spell: {category}")

        self._ui.findChild(QPushButton, "backBtn").clicked.connect(self.go_back)
        self._ui.findChild(QLabel, "categoryLabel").setText(category)
        self._ui.findChild(QLabel, "titleLabel").setText("Choose a Word")

        self._populate_scroll()

    def _populate_scroll(self):
        scroll: QScrollArea = self._ui.findChild(QScrollArea, "scrollArea")

        container = QWidget()
        container.setStyleSheet(f"background:{_BG};")

        # wrap chips into rows of 4
        outer = QVBoxLayout(container)
        outer.setContentsMargins(60, 16, 60, 24)
        outer.setSpacing(12)

        COLS   = 4
        row_w  = None
        row_l  = None

        for i, word in enumerate(self._words):
            if i % COLS == 0:
                row_w = QWidget()
                row_w.setStyleSheet(f"background:{_BG};")
                row_l = QHBoxLayout(row_w)
                row_l.setContentsMargins(0, 0, 0, 0)
                row_l.setSpacing(12)
                outer.addWidget(row_w)

            chip = self._make_chip(word)
            row_l.addWidget(chip)

        # pad last row if needed
        remainder = len(self._words) % COLS
        if remainder and row_l:
            for _ in range(COLS - remainder):
                spacer = QWidget()
                spacer.setStyleSheet("background:transparent;")
                spacer.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )
                row_l.addWidget(spacer)

        outer.addStretch()
        scroll.setWidget(container)

    def _make_chip(self, word: str) -> QFrame:
        letters = [c for c in word if c != " "]
        frame   = QFrame()
        frame.setFixedHeight(80)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        frame.setStyleSheet(_CHIP_STYLE)
        frame.setCursor(Qt.CursorShape.PointingHandCursor)

        v = QVBoxLayout(frame)
        v.setContentsMargins(18, 12, 18, 12)
        v.setSpacing(4)

        name = QLabel(word)
        name.setStyleSheet(
            f"color:{_TEXT_W}; font-size:14px; font-weight:700; background:transparent;"
        )
        count = QLabel(f"{len(letters)} letters")
        count.setStyleSheet(
            f"color:{_TEXT_MID}; font-size:11px; background:transparent;"
        )

        v.addWidget(name)
        v.addWidget(count)

        frame.enterEvent = lambda e, f=frame: f.setStyleSheet(_CHIP_HOV)
        frame.leaveEvent = lambda e, f=frame: f.setStyleSheet(_CHIP_STYLE)
        frame.mousePressEvent = lambda e, w=word: self.word_chosen.emit(w)

        return frame

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
