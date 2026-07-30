# This Python file uses the following encoding: utf-8
"""Menu screen for choosing a minigame."""

from pathlib import Path

from PySide6.QtWidgets import QMainWindow

from ui.ui_menuwindow import Ui_MenuWindow


class MenuWindow(QMainWindow):
    """Main menu screen that routes to individual game windows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MenuWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("SenyaSabi Menu")
        self.resize(1500, 900)

    def open_game(self, game_name):
        """Placeholder for selecting a minigame."""
        # Connect later to each minigame
        pass
