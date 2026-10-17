from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout
from backend.minigame_service import CONFIG, MinigameContext
from screens.navigation import BackButton, install_page_menu
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
        self.context = MinigameContext()
        self.game = None
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        self.menu = QWidget()
        choices = QVBoxLayout(self.menu)
        choices.setContentsMargins(60, 30, 60, 30)
        self.back_button = BackButton()
        self.back_button.clicked.connect(self.back_requested.emit)
        navigation_row = QHBoxLayout()
        navigation_row.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignLeft)
        navigation_row.addStretch()
        navigation_row.addSpacing(76)
        choices.addLayout(navigation_row)
        choices.addWidget(label("Global Minigames", "gameTitle"))
        choices.addWidget(label("Practice words and phrases from all word modules.", "gameSubtitle"))
        self.game_buttons = {}
        for kind in CONFIG:
            title, difficulty, _ = CONFIG[kind]
            choice = button(f"{title}\n{difficulty}",
                            lambda checked=False, selected=kind: self.open_game(
                                selected, scope="global", module_code=None), "primaryButton")
            self.game_buttons[kind] = choice
            choices.addWidget(choice)
        choices.addStretch()
        self.stack.addWidget(self.menu)
        # Each stacked activity owns its header; the hub header belongs only to this page.
        self.navigation_header = install_page_menu(self.menu)

    @property
    def scope(self):
        return self.context.scope

    @property
    def module_code(self):
        return self.context.module_code

    def show_global_hub(self):
        self.return_menu()
        self.context = MinigameContext(scope="global", module_code=None)

    def open_game(self, kind, module_code=None, *, scope="global"):
        context = MinigameContext(scope=scope, module_code=module_code)
        factory = {"sprint": SignSprint, "quest": FingerSpellQuest, "detective": SignDetective}[kind]
        self.return_menu()
        self.context = context
        self.game = factory(self.stack, scope=context.scope, module_code=context.module_code)
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
        if self.scope == "module":
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
