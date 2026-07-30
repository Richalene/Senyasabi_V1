# This Python file uses the following encoding: utf-8
"""Main application window."""

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

from menuwindow import MenuWindow
from ui.ui_mainwindow import Ui_SenyaSabi


def get_resource_path(relative_path):
    """Get absolute path to resource using pathlib."""
    base_path = Path(__file__).resolve().parents[2]
    return str(base_path / relative_path)


class MainWindow(QMainWindow):
    """Main application window with menu and game buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_SenyaSabi()
        self.ui.setupUi(self)
        self.setWindowTitle("SenyaSabi")
        self.showMaximized()

        icon_path = get_resource_path("senyasabi/resources/img/logo_white.png")
        self.setWindowIcon(QIcon(icon_path))

        self.ui.startButton.clicked.connect(self.open_menu_window)

    def open_menu_window(self):
        """Open the menu screen from the landing page."""
        self.menu_window = MenuWindow(self)
        self.menu_window.show()
        self.hide()

    def on_start_clicked(self):
        """Handle start button click."""
        self.open_menu_window()
