from pathlib import Path

from screens.auth.login import add_dev_button
from screens.auth.common import AuthForm

from PySide6.QtCore import Signal
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget, QLabel


_UI_FILE = Path(__file__).resolve().parents[2] / "ui" / "designer" / "register.ui"


class RegisterScreen(QWidget):
    dev_login_requested = Signal()
    sign_in_requested = Signal()
    create_account_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._ui = QUiLoader().load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")

        self.resize(self._ui.size())
        self._ui.resize(self.size())
        self.setWindowTitle("SenyaSabi — Create Account")

        self.username_input = self._ui.findChild(QLineEdit, "usernameInput")
        self.name_input: QLineEdit = self._ui.findChild(QLineEdit, "nameInput")
        self.email_input: QLineEdit = self._ui.findChild(QLineEdit, "emailInput")
        self.password_input: QLineEdit = self._ui.findChild(
            QLineEdit, "passwordInput"
        )
        self.confirm_password_input: QLineEdit = self._ui.findChild(
            QLineEdit, "confirmPasswordInput"
        )
        self.error_label = QLabel(self._ui)
        self.error_label.setObjectName('authError')
        self.error_label.setWordWrap(True)
        self._ui.layout().insertWidget(14, self.error_label)
        self.confirm_password_input.returnPressed.connect(self.create_account_requested)
        self._ui.findChild(QPushButton, "createAccountButton").clicked.connect(
            self.create_account_requested
        )
        self._ui.findChild(QPushButton, "signInButton").clicked.connect(
            self.sign_in_requested
        )

        add_dev_button(self)
        self._auth_form = AuthForm(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_auth_form'):
            self._auth_form.fit()
