"""
Alphabet Menu — hub between Learn mode and Spell mode.

Learn  → AlphabetLessonSelectWidget (picks lesson 1-5)
Spell  → SpellCategoryWidget (picks category → word → SpellLessonWidget)
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_UI_FILE = _HERE / "alphabet_menu.ui"

# Lesson definitions (shared across the alphabet module)
LESSON_LETTERS: dict[int, list[str]] = {
    1: list("ABCDEF"),
    2: list("GHIJKL"),
    3: list("MNOPQR"),
    4: list("STUVWX"),
    5: list("YZ"),
}


class AlphabetMenuWidget(QWidget):
    """
    Hub screen: Learn or Spell.

    Signals
    -------
    go_back        — user hit Back, caller should reshow main menu
    open_learn     — user chose Learn, caller opens lesson select
    open_spell     — user chose Spell, caller opens category select
    """
    go_back    = Signal()
    open_learn = Signal()
    open_spell = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        loader = QUiLoader()
        self._ui = loader.load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")

        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle("SenyaSabi — Alphabet")

        # wire buttons
        self._ui.findChild(QPushButton, "backBtn").clicked.connect(self.go_back)
        self._ui.findChild(QPushButton, "learnBtn").clicked.connect(self.open_learn)
        self._ui.findChild(QPushButton, "spellBtn").clicked.connect(self.open_spell)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
