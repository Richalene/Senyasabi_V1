"""Module-scoped lesson and minigame choices loaded from Qt Designer (.ui)."""
from pathlib import Path
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QFontDatabase, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton, QLabel
from screens.main_menu.alphabet_menu import LESSON_LETTERS
from screens.main_menu.word_menu import _load_categories
from screens.navigation import BackButton, SenyaSabiHeader, install_page_menu
from screens.startup import FittedForm

ROOT = Path(__file__).resolve().parents[2]
_UI_FILE = ROOT / "ui/designer/lesson_select.ui"


class LessonSelectWidget(QWidget):
    go_back = Signal()
    menu_requested = Signal()
    lesson_chosen = Signal(int)
    game_chosen = Signal(str)
    quiz_requested = Signal()

    def __init__(self, parent=None, module_code="alphabet"):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.setWindowTitle("SenyaSabi — Lessons + MiniGames")

        font_path = ROOT / "resources/font/CherryBombOne-Regular.ttf"
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))

        # Load the Qt Designer UI file directly so all visual elements can be edited in Qt Designer
        self._ui = QUiLoader().load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Unable to load {_UI_FILE}")

        # Header with streak and hamburger menu
        self.header = SenyaSabiHeader(self._ui)
        self.header.anchor_to_canvas(QSize(1920, 1080))
        install_page_menu(self, header=self.header)

        # Connect Back Button
        self.btn_back = self._ui.findChild(QPushButton, "btnBack") or self._ui.findChild(QPushButton, "backBtn")
        if self.btn_back is not None:
            self.back_button = BackButton.replace(self.btn_back)
            self.back_button.setObjectName("backBtn")
            self.back_button.clicked.connect(self.go_back)

        # Connect Quiz Button
        self.btn_quiz = self._ui.findChild(QPushButton, "btnQuiz")
        if self.btn_quiz is not None:
            self.btn_quiz.clicked.connect(self.quiz_requested.emit)
        self.quiz_button = self.btn_quiz

        # Connect Minigame Buttons
        self.btn_sprint = self._ui.findChild(QPushButton, "btnSprint")
        if self.btn_sprint is not None:
            self.btn_sprint.clicked.connect(lambda: self.game_chosen.emit("sprint"))

        self.btn_quest = self._ui.findChild(QPushButton, "btnQuest")
        if self.btn_quest is not None:
            self.btn_quest.clicked.connect(lambda: self.game_chosen.emit("quest"))

        self.btn_detective = self._ui.findChild(QPushButton, "btnDetective")
        if self.btn_detective is not None:
            self.btn_detective.clicked.connect(lambda: self.game_chosen.emit("detective"))

        self.btn_expression = self._ui.findChild(QPushButton, "btnExpression")
        self.game_buttons = {
            "sprint": self.btn_sprint,
            "quest": self.btn_quest,
            "detective": self.btn_detective,
        }

        # Explicitly apply star pixmaps so they load in all execution environments
        star_pix = QPixmap(str(ROOT / "resources/img/ui/star.png"))
        for star_name in ("starSprint", "starQuest1", "starQuest2", "starExpr1", "starExpr2", "starDet1", "starDet2", "starDet3"):
            lbl = self._ui.findChild(QLabel, star_name)
            if lbl is not None:
                lbl.setPixmap(star_pix)
                lbl.setScaledContents(True)
                lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        if self.btn_expression is not None:
            self.btn_expression.clicked.connect(self._on_expression_clicked)

        # Gather lesson buttons
        self.lesson_buttons = []
        for i in range(1, 6):
            btn = self._ui.findChild(QPushButton, f"btnLesson{i}")
            if btn is not None:
                btn.clicked.connect(lambda checked=False, num=i: self.lesson_chosen.emit(num))
                self.lesson_buttons.append(btn)

        self.set_module(module_code)
        self._fitted_form = FittedForm(self)

    def _on_expression_clicked(self):
        from screens.dialogs import ComingSoonDialog
        d = ComingSoonDialog(self)
        d.exec()

    def set_module(self, code: str):
        self.module_code = code.lower()
        if self.module_code == "alphabet":
            for btn in self.lesson_buttons:
                btn.show()
        else:
            from backend.content_service import get_lessons_for_module
            lessons = get_lessons_for_module(self.module_code)
            count = len(lessons) if lessons else 1
            for idx, btn in enumerate(self.lesson_buttons):
                is_visible = idx < count
                btn.setVisible(is_visible)
                if is_visible and idx < len(lessons):
                    btn.setToolTip(lessons[idx]["title"])

    def set_streak(self, text):
        self.header.set_streak_text(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui is not None:
            self._ui.resize(self.size())
