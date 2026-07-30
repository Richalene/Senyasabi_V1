# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow

from controllers.mainwindow import MainWindow


class LegacyMainWindow(MainWindow):
    """Compatibility wrapper for the old file location."""

    def __init__(self, parent=None):
        super().__init__(parent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = LegacyMainWindow()
    widget.show()
    sys.exit(app.exec())
