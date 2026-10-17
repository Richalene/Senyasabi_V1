from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGridLayout, QScrollArea
from .common import AnswerGame, SignImage, label


class SignDetective(AnswerGame):
    def __init__(self, parent=None, module_code=None, *, scope=None):
        super().__init__("detective", parent, module_code=module_code, scope=scope)
        self.content.addWidget(label("Decode the alphabet signs. Gaps separate words; apostrophes need no sign.", "instructionCard"))
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content.addWidget(self.scroll, 1)
        self.start()

    def render_round(self):
        self.round_header()
        old = self.scroll.takeWidget()
        if old:
            old.deleteLater()
        canvas = QWidget()
        grid = QGridLayout(canvas)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        # Each source word occupies its own line; long words wrap to five cards.
        row, col = 0, 0
        for word in self.session.word.split():
            for char in word:
                if not "A" <= char <= "Z":
                    continue
                grid.addWidget(SignImage(char, 105), row, col)
                col += 1
                if col == 5:
                    row, col = row + 1, 0
            row, col = row + 1, 0
        self.scroll.setWidget(canvas)
