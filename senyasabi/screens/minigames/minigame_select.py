from pathlib import Path
from PySide6.QtCore import Signal, QTimer, Qt, QSize
from PySide6.QtGui import QFontDatabase, QPixmap
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from backend.minigame_service import ROOT, CONFIG, MinigameContext
from screens.navigation import BackButton, SenyaSabiHeader, install_page_menu
from screens.dialogs import HelpCalloutDialog
from screens.startup import FittedForm
from ui.generated.minigame_select_ui import Ui_MinigameSelect
from .common import GameCanvas
from .sign_sprint import SignSprint
from .sign_detective import SignDetective
from .fingerspell_quest import FingerSpellQuest
from backend.media_service import warm_alphabet_stills

class MinigameMenuWidget(QWidget):
    """The hub screen displaying the 3 minigame buttons based on Figma mockup."""
    sprint_requested = Signal()
    quest_requested = Signal()
    detective_requested = Signal()
    back_requested = Signal()
    logout_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.ui = Ui_MinigameSelect()
        self.ui.setupUi(self)

        # Ensure Cherry Bomb One font is loaded
        font_path = ROOT / "resources/font/CherryBombOne-Regular.ttf"
        if font_path.exists():
            QFontDatabase.addApplicationFont(str(font_path))

        # Runtime absolute asset resolution
        self.ui.imageBg.setPixmap(QPixmap(str(ROOT / "resources/img/gen_bg.png")))

        b16 = str(ROOT / "resources/img/ui/button_16.png").replace("\\", "/")
        b17 = str(ROOT / "resources/img/ui/button_17.png").replace("\\", "/")

        self.ui.btnSprint.setStyleSheet(
            f"QPushButton#btnSprint {{ background: transparent; border: none; color: transparent; font-size: 1px; border-image: url({b16}) 0 0 0 0 stretch stretch; }}"
        )
        self.ui.btnQuest.setStyleSheet(
            f"QPushButton#btnQuest {{ background: transparent; border: none; color: transparent; font-size: 1px; border-image: url({b17}) 0 0 0 0 stretch stretch; }}"
        )
        self.ui.btnDetective.setStyleSheet(
            f"QPushButton#btnDetective {{ background: transparent; border: none; color: transparent; font-size: 1px; border-image: url({b16}) 0 0 0 0 stretch stretch; }}"
        )
        self.ui.btnSprint.setText(f"{CONFIG['sprint'][0]}\n{CONFIG['sprint'][1]}")
        self.ui.btnQuest.setText(f"{CONFIG['quest'][0]}\n{CONFIG['quest'][1]}")
        self.ui.btnDetective.setText(f"{CONFIG['detective'][0]}\n{CONFIG['detective'][1]}")
        self.ui.btnSprint.setToolTip("Sign Sprint: Fast-paced live camera sign recognition game")
        self.ui.btnQuest.setToolTip("FingerSpell Quest: Decode and fingerspell words with your camera")
        self.ui.btnDetective.setToolTip("Sign Detective: Guess mystery words from demonstration clues")

        self.ui.lblSprintText.setText(
            f"<b>{CONFIG['sprint'][0]}</b><br><span style='font-size:18px; color:#8F8C78; font-weight:normal;'>{CONFIG['sprint'][1]}</span>"
        )
        self.ui.lblQuestText.setText(
            f"<b>{CONFIG['quest'][0]}</b><br><span style='font-size:18px; color:#8F8C78; font-weight:normal;'>{CONFIG['quest'][1]}</span>"
        )
        self.ui.lblDetectiveText.setText(
            f"<b>{CONFIG['detective'][0]}</b><br><span style='font-size:18px; color:#8F8C78; font-weight:normal;'>{CONFIG['detective'][1]}</span>"
        )
        self.ui.lblSprintText.setTextFormat(Qt.TextFormat.RichText)
        self.ui.lblQuestText.setTextFormat(Qt.TextFormat.RichText)
        self.ui.lblDetectiveText.setTextFormat(Qt.TextFormat.RichText)

        star_pix = QPixmap(str(ROOT / "resources/img/ui/star.png"))
        for star in (self.ui.starSprint1, self.ui.starQuest1, self.ui.starQuest2,
                     self.ui.starDet1, self.ui.starDet2, self.ui.starDet3):
            star.setPixmap(star_pix)
            star.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.ui.lblSprintText.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.ui.lblQuestText.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.ui.lblDetectiveText.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # Replace btnBack with stylized circular BackButton
        self.back_button = BackButton.replace(self.ui.btnBack)
        self.back_button.clicked.connect(self.back_requested.emit)

        # Header with streak and menu
        self.header = SenyaSabiHeader(self, show_help=True)
        self.header.anchor_to_canvas(QSize(1920, 1080))
        self.header.help_requested.connect(self._show_help)
        install_page_menu(self, header=self.header)
        if self.header.menu_button is not None and hasattr(self.header.menu_button, "menu"):
            menu = self.header.menu_button.menu()
            if hasattr(menu, "sign_out_action"):
                menu.sign_out_action.triggered.connect(self.logout_requested.emit)

        # FittedForm for proportional scaling to any resolution
        self._fitted_form = FittedForm(self)

        # Button signals
        self.ui.btnSprint.clicked.connect(self.sprint_requested.emit)
        self.ui.btnQuest.clicked.connect(self.quest_requested.emit)
        self.ui.btnDetective.clicked.connect(self.detective_requested.emit)

    def _show_help(self):
        HelpCalloutDialog.show_help(
            self,
            title="Minigames Guide",
            bullets=[
                "Sign Sprint: A fast-paced time-attack game! Form the requested signs as quickly as you can before the clock expires.",
                "Fingerspell Quest: An RPG-style spelling adventure! Spell the letters of given target words using hand signs to defeat obstacles.",
                "Sign Detective: Solve sign mysteries! Watch clues and deduce the secret word.",
                "Stars: Score points to earn up to 3 stars per minigame and climb the leaderboard.",
                "Lighting & Camera: Ensure your hand is clearly visible and well-lit for optimal sign recognition."
            ]
        )


class MinigameSelect(GameCanvas):
    back_requested = Signal()
    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("minigameSelect")
        self.setWindowTitle("SenyaSabi Minigames")
        self.resize(1920, 1080)
        self.context = MinigameContext()
        self.game = None
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.stack)

        self.menu = MinigameMenuWidget()
        self.menu.sprint_requested.connect(lambda: self.open_game("sprint"))
        self.menu.quest_requested.connect(lambda: self.open_game("quest"))
        self.menu.detective_requested.connect(lambda: self.open_game("detective"))
        self.menu.back_requested.connect(self.back_requested.emit)
        self.menu.logout_requested.connect(self.logout_requested.emit)

        # Expose legacy attributes for backwards-compatibility
        self.back_button = self.menu.back_button
        self.game_buttons = {
            "sprint": self.menu.ui.btnSprint,
            "quest": self.menu.ui.btnQuest,
            "detective": self.menu.ui.btnDetective,
        }
        self.navigation_header = self.menu.header

        self.stack.addWidget(self.menu)

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
        warm_alphabet_stills()
        context = MinigameContext(scope=scope, module_code=module_code)
        factory = {"sprint": SignSprint, "quest": FingerSpellQuest, "detective": SignDetective}[kind]
        self.return_menu()
        self.context = context
        self.game = factory(self.stack, scope=context.scope, module_code=context.module_code)
        self.game.back_requested.connect(self.game_back)
        self.stack.addWidget(self.game)
        self.stack.setCurrentWidget(self.game)

    def start_game(self, game):
        if self.game is not game:
            return
        if hasattr(game, "start_game"):
            game.start_game()
        elif hasattr(game, "start"):
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
