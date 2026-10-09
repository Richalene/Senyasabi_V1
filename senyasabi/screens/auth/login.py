from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget, QLabel


_UI_FILE = Path(__file__).resolve().parents[2] / "ui" / "designer" / "login.ui"


class LoginScreen(QWidget):
    continue_requested = Signal()
    register_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._ui = QUiLoader().load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")

        self.resize(self._ui.size())
        self._ui.resize(self.size())
        self.setWindowTitle("SenyaSabi — Sign In")

        self.email_input: QLineEdit = self._ui.findChild(QLineEdit, "emailInput")
        self.password_input: QLineEdit = self._ui.findChild(QLineEdit, "passwordInput")
        self.error_label = QLabel(self._ui)
        self.error_label.setWordWrap(True)
        self._ui.layout().insertWidget(8, self.error_label)
        self.password_input.returnPressed.connect(self.continue_requested)
        self._ui.findChild(QPushButton, "continueButton").clicked.connect(
            self.continue_requested
        )
        self._ui.findChild(QPushButton, "registerButton").clicked.connect(
            self.register_requested
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
