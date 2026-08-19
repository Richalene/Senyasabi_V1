"""
Lesson Select — shows 5 lesson cards for the Learn mode.
User picks one, caller opens AlphabetLessonWidget with that lesson's letters.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton, QLabel

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lessons.alphabet_menu import LESSON_LETTERS

_UI_FILE = _HERE / "lesson_select.ui"

_CARD_STYLE = """
    color: #ffffff;
    font-size: {size}px;
    font-weight: 700;
    background: transparent;
    letter-spacing: {spacing}px;
"""


class LessonSelectWidget(QWidget):
    """
    Signals
    -------
    go_back          — back to alphabet menu
    lesson_chosen(n) — lesson number 1-5 selected
    """
    go_back       = Signal()
    lesson_chosen = Signal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        loader = QUiLoader()
        self._ui = loader.load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")

        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle("SenyaSabi — Choose a Lesson")

        self._ui.findChild(QPushButton, "backBtn").clicked.connect(self.go_back)

        # wire each lesson button + overlay labels
        for n in range(1, 6):
            btn: QPushButton = self._ui.findChild(QPushButton, f"lesson{n}Btn")
            letters = LESSON_LETTERS[n]
            letter_range = f"{letters[0]}–{letters[-1]}"

            # number label
            num_lbl = QLabel(f"Lesson {n}", btn)
            num_lbl.setStyleSheet(_CARD_STYLE.format(size=13, spacing=2) +
                                  "color: #7ecfed;")
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            num_lbl.setGeometry(0, 60, btn.width(), 24)

            # letter range label
            range_lbl = QLabel(letter_range, btn)
            range_lbl.setStyleSheet(_CARD_STYLE.format(size=42, spacing=0))
            range_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            range_lbl.setGeometry(0, 96, btn.width(), 60)

            # letter count label
            count_lbl = QLabel(f"{len(letters)} letters", btn)
            count_lbl.setStyleSheet(_CARD_STYLE.format(size=12, spacing=1) +
                                    "color: #5a6080;")
            count_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            count_lbl.setGeometry(0, 168, btn.width(), 24)

            # all letters preview
            preview_lbl = QLabel("  ".join(letters), btn)
            preview_lbl.setStyleSheet(_CARD_STYLE.format(size=13, spacing=3) +
                                      "color: #3a4060;")
            preview_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            preview_lbl.setGeometry(0, 200, btn.width(), 30)

            btn.clicked.connect(lambda checked=False, num=n: self.lesson_chosen.emit(num))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
