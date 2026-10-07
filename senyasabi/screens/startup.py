"""Thin wrappers around the existing Welcome and Landing forms."""
from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget
from ui.welcome_ui import Ui_Welcome
from ui.landing_ui import Ui_Landing


class StartupScreen(QWidget):
    def __init__(self, form, background_name):
        super().__init__()
        self.ui = form()
        self.ui.setupUi(self)
        self.background_path = Path(__file__).resolve().parents[1] / "resources" / "img" / background_name
        if self.background_path.is_file():
            pixmap = QPixmap(str(self.background_path))
            if not pixmap.isNull():
                self.ui.imgBackground.setPixmap(pixmap)
                self.ui.imgBackground.setScaledContents(True)


class WelcomeScreen(StartupScreen):
    def __init__(self):
        super().__init__(Ui_Welcome, "welcome.png")
        next_button_path = Path(__file__).resolve().parents[1] / "resources" / "img" / "ui" / "nextbtn.png"
        icon = QIcon(str(next_button_path))
        if icon.isNull():
            raise RuntimeError(f"Failed to load welcome button image: {next_button_path}")
        self.ui.btnContinue.setIcon(icon)
        self.ui.btnContinue.setIconSize(self.ui.btnContinue.size())


class LandingScreen(StartupScreen):
    def __init__(self):
        super().__init__(Ui_Landing, "landing.png")
