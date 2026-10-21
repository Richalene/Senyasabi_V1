"""Module-scoped lesson and minigame choices matching Wireframe Page 1."""
from pathlib import Path
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QFontDatabase, QPixmap
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QSizePolicy
)
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
        self.resize(1920, 1080)
        self.setWindowTitle("SenyaSabi — Lessons + Minigames")

        font_path = ROOT / "resources/font/CherryBombOne-Regular.ttf"
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))

        # Background foliage
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setPixmap(QPixmap(str(ROOT / "resources/img/gen_bg.png")))
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()

        # Header with streak and hamburger menu
        self.header = SenyaSabiHeader(self)
        self.header.anchor_to_canvas(QSize(1920, 1080))
        install_page_menu(self, header=self.header)

        # Circular Back Button at top right under the header
        self.btn_back = BackButton(self)
        self.btn_back.setGeometry(1810, 160, 68, 68)
        self.btn_back.clicked.connect(self.go_back)

        # Module Quiz Button under Lessons if requested
        self.btn_quiz = QPushButton("Module Quiz", self)
        self.btn_quiz.setGeometry(260, 960, 460, 74)
        self.btn_quiz.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quiz.setStyleSheet(
            "QPushButton { "
            "  background-color: #BFD379; "
            "  border: 4px solid #FFFFFF; "
            "  border-radius: 37px; "
            "  color: #4F3222; "
            "  font-family: 'Segoe UI', sans-serif; "
            "  font-size: 26px; "
            "  font-weight: 700; "
            "} "
            "QPushButton:hover { "
            "  background-color: #ADC362; "
            "}"
        )
        self.btn_quiz.clicked.connect(self.quiz_requested.emit)

        # Central canvas (two columns divided by dashed vertical line)
        # Left: My Lessons
        self.lbl_my_lessons = QLabel("My Lessons", self)
        self.lbl_my_lessons.setGeometry(280, 180, 380, 70)
        self.lbl_my_lessons.setStyleSheet(
            "font-family: 'Cherry Bomb One', cursive, sans-serif; "
            "font-size: 46px; "
            "color: #4F3222; "
            "background: transparent;"
        )

        # Right: MiniGames
        self.lbl_minigames = QLabel("MiniGames", self)
        self.lbl_minigames.setGeometry(1260, 180, 380, 70)
        self.lbl_minigames.setStyleSheet(
            "font-family: 'Cherry Bomb One', cursive, sans-serif; "
            "font-size: 46px; "
            "color: #4F3222; "
            "background: transparent;"
        )

        # Center dashed divider line
        self.divider = QFrame(self)
        self.divider.setGeometry(956, 240, 8, 720)
        self.divider.setFrameShape(QFrame.Shape.VLine)
        self.divider.setStyleSheet("QFrame { border: 2px dashed #C8DA86; }")

        # Lesson buttons container
        self.lesson_container = QWidget(self)
        self.lesson_container.setGeometry(180, 270, 620, 750)
        self.lesson_container.setStyleSheet("background: transparent;")
        self.lesson_layout = QVBoxLayout(self.lesson_container)
        self.lesson_layout.setContentsMargins(0, 0, 0, 0)
        self.lesson_layout.setSpacing(22)

        # Minigame buttons (2x2 grid matching Page 1)
        self.game_buttons = {}
        mg_configs = [
            ("sprint", "Sign\nSprint", 1, 1020, 340),
            ("quest", "FingerSpell\nQuest", 2, 1460, 340),
            ("expression", "Expression\nin Motion", 2, 1020, 560),
            ("detective", "Sign\nDetective", 3, 1460, 560),
        ]

        star_pix = QPixmap(str(ROOT / "resources/img/ui/star.png"))
        for kind, title, stars, gx, gy in mg_configs:
            btn = QPushButton(self)
            btn.setGeometry(gx, gy, 380, 150)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "QPushButton { "
                "  background-color: #FFFDF0; "
                "  border: 4px solid #FFFFFF; "
                "  border-radius: 46px; "
                "  color: #4F3222; "
                "  font-family: 'Segoe UI', sans-serif; "
                "  font-size: 26px; "
                "  font-weight: 600; "
                "  text-align: center; "
                "  padding-left: 50px; "
                "} "
                "QPushButton:hover { "
                "  background-color: #FFF3BD; "
                "}"
            )
            btn.setText(title)
            btn.clicked.connect(lambda checked=False, k=kind: self._on_game_clicked(k))
            self.game_buttons[kind] = btn

            # Stars on left of each minigame button
            for s in range(stars):
                star_lbl = QLabel(btn)
                if stars == 1:
                    star_lbl.setGeometry(45, 52, 42, 42)
                elif stars == 2:
                    star_lbl.setGeometry(45, 34 + s * 44, 40, 40)
                else:
                    star_lbl.setGeometry(38 + (s % 2) * 36, 30 + (s // 2) * 44, 38, 38)
                star_lbl.setPixmap(star_pix)
                star_lbl.setScaledContents(True)
                star_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.set_module(module_code)

    def _on_game_clicked(self, kind: str):
        if kind == "expression":
            from screens.dialogs import ComingSoonDialog
            d = ComingSoonDialog(self)
            d.exec()
        else:
            self.game_chosen.emit(kind)

    def set_module(self, code: str):
        self.module_code = code.lower()
        while self.lesson_layout.count():
            item = self.lesson_layout.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.deleteLater()

        if self.module_code == "alphabet":
            lesson_items = [
                (1, "Lesson 1"),
                (2, "Lesson 2"),
                (3, "Lesson 3"),
                (4, "Lesson 4"),
                (5, "Lesson 5"),
            ]
        else:
            categories = _load_categories()
            key = self.module_code.upper()
            lesson_items = [(1, "Lesson 1")]

        self.lesson_buttons = []
        for idx, (number, label_text) in enumerate(lesson_items):
            btn = QPushButton(label_text, self.lesson_container)
            btn.setFixedHeight(92)
            # Alternate horizontal margin offsets to create the exact staggered organic rhythm from Page 1
            h_offset = 0 if idx % 2 == 0 else 120
            btn.setStyleSheet(
                f"QPushButton {{ "
                f"  background-color: #FFFDF0; "
                f"  border: 4px solid #FFFFFF; "
                f"  border-radius: 46px; "
                f"  color: #4F3222; "
                f"  font-family: 'Segoe UI', sans-serif; "
                f"  font-size: 28px; "
                f"  font-weight: 600; "
                f"  margin-left: {h_offset}px; "
                f"}} "
                f"QPushButton:hover {{ "
                f"  background-color: #FFF3BD; "
                f"}}"
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, num=number: self.lesson_chosen.emit(num))
            self.lesson_layout.addWidget(btn)
            self.lesson_buttons.append(btn)

        self.lesson_layout.addStretch()

    def set_streak(self, text):
        self.header.set_streak_text(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "bg_label"):
            self.bg_label.setGeometry(self.rect())
