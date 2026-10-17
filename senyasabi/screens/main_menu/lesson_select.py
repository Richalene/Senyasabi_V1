"""Module-scoped lesson and minigame choices, using existing content definitions."""
from pathlib import Path
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout
from screens.main_menu.alphabet_menu import LESSON_LETTERS
from screens.main_menu.word_menu import _load_categories
from screens.navigation import BackButton, SenyaSabiHeader, install_page_menu

ROOT = Path(__file__).resolve().parents[2]


class LessonSelectWidget(QWidget):
    go_back = Signal()
    menu_requested = Signal()
    lesson_chosen = Signal(int)
    game_chosen = Signal(str)
    quiz_requested = Signal()

    def __init__(self, parent=None, module_code="alphabet"):
        super().__init__(parent)
        self._ui = QUiLoader().load(str(ROOT / "ui/designer/lesson_select.ui"),self)
        if self._ui is None:
            raise RuntimeError("Unable to load lesson_select.ui")
        self._fitted_form = self
        self.resize(1306,735)
        self.setWindowTitle("SenyaSabi — Lessons + Minigames")
        header_row = self._ui.findChild(QHBoxLayout,"headerLayout")
        self.back_button = BackButton.replace(self._ui.findChild(QPushButton,"backBtn"))
        header_row.removeWidget(self.back_button)
        header_row.insertWidget(0,self.back_button)
        self.back_button.clicked.connect(self.go_back)
        # Keep the artwork together in design-canvas coordinates; the layout
        # reserves its space while the shared component owns its placement.
        for old in (self._ui.findChild(QLabel,"streakLabel"),
                    self._ui.findChild(QPushButton,"menuBtn")):
            header_row.removeWidget(old)
            old.setObjectName(f"retired_{old.objectName()}")
            old.hide()
            old.deleteLater()
        self.header = SenyaSabiHeader(self._ui)
        self.header.streak_label.setObjectName("streakLabel")
        self.header.menu_button.setObjectName("menuBtn")
        self.header.anchor_to_canvas(QSize(1306,735))
        install_page_menu(self, header=self.header)
        self._header_space = QWidget(self._ui)
        header_row.addWidget(self._header_space)
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
            lessons = [(number,f"Lesson {number} - {chars[0]} to {chars[-1]}") for number,chars in LESSON_LETTERS.items()]
        else:
            categories = _load_categories()
            key = self.module_code.upper()
            if key not in categories:
                raise ValueError(f"Unknown module: {code}")
            self.module_title = key.title()
            # The existing word lesson exposes one complete category lesson.
            lessons = [(1,f"Lesson 1 - {len(categories[key])} Signs")]
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
        self.quiz_button = QPushButton(f"{self.module_title} Quiz")
        self.quiz_button.setProperty("class", "lessonButton")
        self.quiz_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.quiz_button.clicked.connect(self.quiz_requested.emit)
        self.lesson_layout.insertWidget(self.lesson_layout.count()-1, self.quiz_button)

    def set_streak(self,text):
        self.header.set_streak_text(text)

    def fit(self):
        if not hasattr(self,"_ui"):
            return
        scale = min(self.width()/1306,self.height()/735)
        width,height = round(1306*scale),round(735*scale)
        self._ui.setGeometry((self.width()-width)//2,(self.height()-height)//2,width,height)
        if hasattr(self,"header"):
            self._header_space.setFixedSize(max(1,round(width*.28)),
                                           max(44,round(width*130/1920)))
            self.header.raise_()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.fit()
