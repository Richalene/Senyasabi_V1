from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from backend.minigame_service import CONFIG
from .common import GameCanvas, button, label
from .sign_sprint import SignSprint
from .sign_detective import SignDetective
from .fingerspell_quest import FingerSpellQuest


class MinigameSelect(GameCanvas):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("minigameSelect")
        self.setWindowTitle("SenyaSabi Minigames")
        self.module_code = None
        self.game = None
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        self.menu = QWidget()
        choices = QVBoxLayout(self.menu)
        choices.setContentsMargins(60, 30, 60, 30)
        choices.addWidget(button("Back", self.back_requested.emit, "secondaryButton"))
        choices.addWidget(label("Minigames", "gameTitle"))
        for kind in CONFIG:
            title, difficulty, _ = CONFIG[kind]
            choices.addWidget(button(f"{title} ? {difficulty}", lambda checked=False, selected=kind: self.open_game(selected), "primaryButton"))
        choices.addStretch()
        self.stack.addWidget(self.menu)

    def open_game(self, kind, module_code=None):
        self.return_menu()
        factory = {"sprint": SignSprint, "quest": FingerSpellQuest, "detective": SignDetective}[kind]
        self.module_code = module_code
        self.game = factory(self.stack, module_code=module_code)
        self.game.back_requested.connect(self.game_back)
        self.stack.addWidget(self.game)
        self.stack.setCurrentWidget(self.game)
        # Stacking a new page can hide it once during insertion. Start after
        # navigation has made the selector visible, not during that hide cycle.
        game = self.game
        QTimer.singleShot(0, lambda: self.start_game(game))

    def start_game(self, game):
        if self.game is not game or not self.isVisible():
            return
        if isinstance(game, FingerSpellQuest):
            if game.engine is None and not game.loading.busy:
                game.open_camera()
        elif not game.countdown.isActive():
            game.start()

    def game_back(self):
        self.return_menu()
        if self.module_code is not None:
            self.back_requested.emit()

    def return_menu(self):
        if self.game is not None:
            self.game.stop()
            self.stack.removeWidget(self.game)
            self.game.deleteLater()
            self.game = None
        self.stack.setCurrentWidget(self.menu)

    def hideEvent(self, event):
        self.return_menu()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.return_menu()
        super().closeEvent(event)
