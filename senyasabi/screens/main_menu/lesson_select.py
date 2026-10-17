"""Module-scoped lesson and minigame choices, using existing content definitions."""
from pathlib import Path
from PySide6.QtCore import Signal, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout
from screens.main_menu.alphabet_menu import LESSON_LETTERS
from screens.main_menu.word_menu import _load_categories

ROOT = Path(__file__).resolve().parents[2]


class LessonSelectWidget(QWidget):
    go_back = Signal()
    menu_requested = Signal()
    lesson_chosen = Signal(int)
    game_chosen = Signal(str)

    def __init__(self, parent=None, module_code="alphabet"):
        super().__init__(parent)
        self._ui = QUiLoader().load(str(ROOT / "ui/designer/lesson_select.ui"),self)
        if self._ui is None:
            raise RuntimeError("Unable to load lesson_select.ui")
        self._fitted_form = self
        self.resize(1306,735)
        self.setWindowTitle("SenyaSabi ? Lessons + Minigames")
        self._ui.findChild(QPushButton,"backBtn").clicked.connect(self.go_back)
        self._ui.findChild(QPushButton,"menuBtn").clicked.connect(self.menu_requested)
        self.lesson_layout = self._ui.findChild(QVBoxLayout,"lessonLayout")
        games = self._ui.findChild(QVBoxLayout,"gameLayout")
        games.addWidget(self.heading("MiniGames"))
        self.game_buttons = {}
        for stars,kind,title in ((1,"sprint","Sign Sprint"),(2,"quest","FingerSpell Quest"),(3,"detective","Sign Detective")):
            button = QPushButton("\u2b50"*stars+"  "+title)
            button.setProperty("class","minigameButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False,kind=kind:self.game_chosen.emit(kind))
            self.game_buttons[kind] = button
            games.addWidget(button)
        games.addStretch()
        self.set_module(module_code)
        self.fit()

    def heading(self,text):
        heading = QLabel(text)
        heading.setProperty("class","sectionTitle")
        return heading

    def set_module(self,code):
        self.module_code = code.lower()
        if self.module_code=="alphabet":
            self.module_title = "FSL Alphabet"
            lessons = [(number,f"Lesson {number} ? {chars[0]}?{chars[-1]}") for number,chars in LESSON_LETTERS.items()]
        else:
            categories = _load_categories()
            key = self.module_code.upper()
            if key not in categories:
                raise ValueError(f"Unknown module: {code}")
            self.module_title = key.title()
            # The existing word lesson exposes one complete category lesson.
            lessons = [(1,f"Lesson 1 ? {len(categories[key])} Signs")]
        self._ui.findChild(QLabel,"moduleTitle").setText(self.module_title)
        while self.lesson_layout.count():
            item = self.lesson_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.deleteLater()
        self.lesson_layout.addWidget(self.heading("My Lessons"))
        self.lesson_buttons = []
        for number,title in lessons:
            button = QPushButton(title)
            button.setProperty("class","lessonButton")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False,number=number:self.lesson_chosen.emit(number))
            self.lesson_layout.addWidget(button)
            self.lesson_buttons.append(button)
        self.lesson_layout.addStretch()

    def set_streak(self,text):
        self._ui.findChild(QLabel,"streakLabel").setText(text)

    def fit(self):
        if not hasattr(self,"_ui"):
            return
        scale = min(self.width()/1306,self.height()/735)
        width,height = round(1306*scale),round(735*scale)
        self._ui.setGeometry((self.width()-width)//2,(self.height()-height)//2,width,height)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.fit()
