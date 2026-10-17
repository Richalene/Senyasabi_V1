from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget, QLabel
from screens.auth.common import AuthForm
from screens.navigation import BackButton


# TEMPORARY: disable before distributing a production build.
DEV_MODE = True


def add_dev_button(screen):
    if not DEV_MODE:
        return
    button = QPushButton("DEV \u2192", screen)
    button.setObjectName("devLoginButton")
    button.setToolTip("Development session only")
    button.setGeometry(12, 12, 66, 28)
    button.setStyleSheet("font-size: 11px; padding: 3px 8px;")
    button.clicked.connect(lambda: screen.dev_login_requested.emit() if DEV_MODE else None)
    button.raise_()
    screen.dev_button = button


_UI_FILE = Path(__file__).resolve().parents[2] / "ui" / "designer" / "login.ui"


class LoginScreen(QWidget):
    dev_login_requested = Signal()
    continue_requested = Signal()
    register_requested = Signal()
    back_requested = Signal()

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
        self.error_label.setObjectName('authError')
        self.error_label.setWordWrap(True)
        self._ui.layout().insertWidget(8, self.error_label)
        self.password_input.returnPressed.connect(self.continue_requested)
        self._ui.findChild(QPushButton, "continueButton").clicked.connect(
            self.continue_requested
        )
        self._ui.findChild(QPushButton, "registerButton").clicked.connect(
            self.register_requested
        )

        add_dev_button(self)
        self.back_button = BackButton(self._ui)
        self.back_button.clicked.connect(self.back_requested.emit)
        self._ui.layout().insertWidget(0, self.back_button, 0, Qt.AlignmentFlag.AlignLeft)
        self._auth_form = AuthForm(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_auth_form'):
            self._auth_form.fit()
