# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from ui_form import Ui_main

# ── Lesson letter sets ─────────────────────────────────────────────────────
LESSON_LETTERS = {
    1: list("ABCDEF"),
    2: list("GHIJKL"),
    3: list("MNOPQR"),
    4: list("STUVWX"),
    5: list("YZ"),
}


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_main()
        self.ui.setupUi(self)

        # Background image
        image_path = Path(__file__).resolve().parent / "resources" / "img" / "menu.png"
        self.ui.bg.setPixmap(QPixmap(str(image_path)))
        self.ui.bg.setScaledContents(True)

        # ── Wire up alphabet button ────────────────────────────────────────
        # The new button added to form.ui is named "alphabetBtn"
        self.ui.alphabetBtn.clicked.connect(
            lambda: self._open_alphabet_lesson(lesson_number=1)
        )

        # ── Placeholder connections for other buttons ──────────────────────
        # Uncomment and wire when those modules exist
        # self.ui.signSprint.clicked.connect(...)
        # self.ui.EIP.clicked.connect(...)
        # self.ui.signDetective.clicked.connect(...)
        # self.ui.fingerspellQuest.clicked.connect(...)

    def _open_alphabet_lesson(self, lesson_number: int = 1):
        from lessons.alphabet_lesson import AlphabetLessonWidget

        letters = LESSON_LETTERS.get(lesson_number, list("ABCDEF"))
        self._alphabet_window = AlphabetLessonWidget(
            letters=letters,
            lesson_number=lesson_number,
            parent=None,          # top-level window, not a child
        )
        self._alphabet_window.lesson_finished.connect(self.show)
        self.hide()
        self._alphabet_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
