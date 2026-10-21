from pathlib import Path

from screens.auth.login import add_dev_button
from screens.loading import LoadingOverlay
from screens.startup import FittedForm

from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget, QLabel


_UI_FILE = Path(__file__).resolve().parents[2] / "ui" / "designer" / "register.ui"


class RegisterScreen(QWidget):
    dev_login_requested = Signal()
    sign_in_requested = Signal()
    create_account_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._ui = QUiLoader().load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")

        self.resize(self._ui.size())
        self._ui.resize(self.size())
        self.setWindowTitle("SenyaSabi — Create Account")

        # Load styling
        root = Path(__file__).resolve().parents[2]
        style = (root / "resources/styles/common.qss").read_text() + (root / "resources/styles/auth.qss").read_text()
        self.setStyleSheet(style)

        # Explicitly set background and logo pixmaps so they load reliably
        bg_label = self._ui.findChild(QLabel, "imageBg")
        if bg_label:
            bg_pixmap = QPixmap(str(root / "resources/img/login_bg.png"))
            if not bg_pixmap.isNull():
                bg_label.setPixmap(bg_pixmap)
                bg_label.setScaledContents(True)

        logo_label = self._ui.findChild(QLabel, "logoLabel")
        if logo_label:
            logo_pixmap = QPixmap(str(root / "resources/img/ui/logo_black.png"))
            if not logo_pixmap.isNull():
                logo_label.setPixmap(logo_pixmap)
                logo_label.setScaledContents(True)

        self.email_input: QLineEdit = self._ui.findChild(QLineEdit, "emailInput")
        self.password_input: QLineEdit = self._ui.findChild(QLineEdit, "passwordInput")

        # Error label positioned directly above buttons
        self.error_label = QLabel(self._ui)
        self.error_label.setObjectName('authError')
        self.error_label.setWordWrap(True)
        self.error_label.setGeometry(870, 672, 840, 36)
        self.error_label.raise_()

        self.password_input.returnPressed.connect(self.create_account_requested)

        create_btn = self._ui.findChild(QPushButton, "createAccountButton")
        if create_btn:
            create_btn.clicked.connect(self.create_account_requested)

        sign_in_btn = self._ui.findChild(QPushButton, "signInButton")
        if sign_in_btn:
            sign_in_btn.clicked.connect(self.sign_in_requested)

        back_btn = self._ui.findChild(QPushButton, "backButton")
        if back_btn:
            back_btn.clicked.connect(self.back_requested)

        add_dev_button(self)

        self.loading = LoadingOverlay(self)
        self._fitted_form = FittedForm(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_ui') and self._ui:
            self._ui.resize(self.size())
