# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from ui_form import Ui_main


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_main()
        self.ui.setupUi(self)

        image_path = Path(__file__).resolve().parent / "resources" / "img" / "menu.png"
        self.ui.bg.setPixmap(QPixmap(str(image_path)))
        self.ui.bg.setScaledContents(True)

        # ── Alphabet button ───────────────────────────────────────────────
        self.ui.alphabetBtn.clicked.connect(self._open_alphabet_menu)

        # ── Word Lessons button (add this in Qt Designer, name: wordLessonsBtn)
        self.ui.wordLessonsBtn.clicked.connect(self._open_word_menu)

        # other buttons — wire when those modules are ready
        # self.ui.signSprint.clicked.connect(...)
        # self.ui.EIP.clicked.connect(...)
        # self.ui.signDetective.clicked.connect(...)
        # self.ui.fingerspellQuest.clicked.connect(...)

    # ══════════════════════════════════════════════════════════════════════
    # ALPHABET navigation
    # ══════════════════════════════════════════════════════════════════════

    def _open_alphabet_menu(self):
        from lessons.alphabet_menu import AlphabetMenuWidget
        self._alphabet_menu = AlphabetMenuWidget()
        self._alphabet_menu.go_back.connect(self._on_back_to_main)
        self._alphabet_menu.open_learn.connect(self._open_lesson_select)
        self._alphabet_menu.open_spell.connect(self._open_spell_category)
        self.hide()
        self._alphabet_menu.show()

    def _open_lesson_select(self):
        from lessons.lesson_select import LessonSelectWidget
        if hasattr(self, "_alphabet_menu"):
            self._alphabet_menu.hide()
        self._lesson_select = LessonSelectWidget()
        self._lesson_select.go_back.connect(self._back_to_alphabet_menu)
        self._lesson_select.lesson_chosen.connect(self._open_learn_lesson)
        self._lesson_select.show()

    def _open_learn_lesson(self, lesson_number: int):
        from lessons.alphabet_menu import LESSON_LETTERS
        from lessons.alphabet_lesson import AlphabetLessonWidget
        if hasattr(self, "_lesson_select"):
            self._lesson_select.hide()
        self._learn_window = AlphabetLessonWidget(
            letters=LESSON_LETTERS[lesson_number],
            lesson_number=lesson_number,
        )
        self._learn_window.lesson_finished.connect(self._back_to_lesson_select)
        self._learn_window.show()

    def _open_spell_category(self):
        from lessons.spell_select import SpellCategoryWidget
        if hasattr(self, "_alphabet_menu"):
            self._alphabet_menu.hide()
        self._spell_cat = SpellCategoryWidget()
        self._spell_cat.go_back.connect(self._back_to_alphabet_menu)
        self._spell_cat.category_chosen.connect(self._open_spell_words)
        self._spell_cat.show()

    def _open_spell_words(self, category: str, words: list):
        from lessons.spell_select import SpellWordWidget
        if hasattr(self, "_spell_cat"):
            self._spell_cat.hide()
        self._spell_words = SpellWordWidget(category=category, words=words)
        self._spell_words.go_back.connect(self._back_to_spell_category)
        self._spell_words.word_chosen.connect(
            lambda word: self._open_spell_lesson(word, category)
        )
        self._spell_words.show()

    def _open_spell_lesson(self, word: str, category: str):
        from lessons.spell_lesson import SpellLessonWidget
        if hasattr(self, "_spell_words"):
            self._spell_words.hide()
        self._spell_lesson = SpellLessonWidget(word=word, category=category)
        self._spell_lesson.lesson_finished.connect(self._back_to_spell_words)
        self._spell_lesson.show()

    # ══════════════════════════════════════════════════════════════════════
    # WORD LESSONS navigation
    # ══════════════════════════════════════════════════════════════════════

    def _open_word_menu(self):
        from lessons.word_menu import WordMenuWidget
        self._word_menu = WordMenuWidget()
        self._word_menu.go_back.connect(self._on_back_to_main)
        self._word_menu.category_chosen.connect(self._open_word_lesson)
        self.hide()
        self._word_menu.show()

    def _open_word_lesson(self, category: str, words: list):
        from lessons.word_lesson import WordLessonWidget
        if hasattr(self, "_word_menu"):
            self._word_menu.hide()
        self._word_lesson = WordLessonWidget(words=words, category=category)
        self._word_lesson.lesson_finished.connect(self._back_to_word_menu)
        self._word_lesson.show()

    # ══════════════════════════════════════════════════════════════════════
    # BACK navigation
    # ══════════════════════════════════════════════════════════════════════

    def _on_back_to_main(self):
        for attr in ("_alphabet_menu", "_word_menu"):
            w = getattr(self, attr, None)
            if w:
                w.close()
        self.show()

    def _back_to_alphabet_menu(self):
        for attr in ("_lesson_select", "_spell_cat"):
            w = getattr(self, attr, None)
            if w:
                w.close()
        if hasattr(self, "_alphabet_menu"):
            self._alphabet_menu.show()

    def _back_to_lesson_select(self):
        if hasattr(self, "_learn_window"):
            self._learn_window.close()
        if hasattr(self, "_lesson_select"):
            self._lesson_select.show()

    def _back_to_spell_category(self):
        if hasattr(self, "_spell_words"):
            self._spell_words.close()
        if hasattr(self, "_spell_cat"):
            self._spell_cat.show()

    def _back_to_spell_words(self):
        if hasattr(self, "_spell_lesson"):
            self._spell_lesson.close()
        if hasattr(self, "_spell_words"):
            self._spell_words.show()

    def _back_to_word_menu(self):
        if hasattr(self, "_word_lesson"):
            self._word_lesson.close()
        if hasattr(self, "_word_menu"):
            self._word_menu.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())