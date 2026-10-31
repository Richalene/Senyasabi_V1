from pathlib import Path

from screens.loading import LoadingOverlay
from screens.startup import FittedForm

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QLineEdit, QPushButton, QWidget, QLabel


_UI_FILE = Path(__file__).resolve().parents[2] / "ui" / "designer" / "register.ui"


class RegisterScreen(QWidget):
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
        from PySide6.QtWidgets import QScrollArea
        class _AuthScrollCompat(QScrollArea):
            def geometry(self):
                p = self.parentWidget()
                return p.rect() if p else super().geometry()
        self._auth_form = QWidget(self)
        self._auth_form.scroll = _AuthScrollCompat(self)
        self._auth_form.scroll.setStyleSheet("background: transparent; border: none;")
        self._auth_form.scroll.viewport().setStyleSheet("background: transparent; border: none;")
        self._auth_form.scroll.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._auth_form.scroll.lower()
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
        self.username_input: QLineEdit = self._ui.findChild(QLineEdit, "usernameInput") or QLineEdit(self)
        self.name_input: QLineEdit = self._ui.findChild(QLineEdit, "nameInput") or QLineEdit(self)
        self.confirm_password_input: QLineEdit = self._ui.findChild(QLineEdit, "confirmPasswordInput") or QLineEdit(self)

        # Error label positioned directly above buttons
        self.error_label = QLabel(self._ui)
        self.error_label.setObjectName('authError')
        self.error_label.setWordWrap(True)
        self.error_label.setGeometry(870, 684, 840, 26)
        self.error_label.raise_()

        self.name_input.returnPressed.connect(self.create_account_requested)
        self.username_input.returnPressed.connect(self.create_account_requested)
        self.email_input.returnPressed.connect(self.create_account_requested)
        self.password_input.returnPressed.connect(self.create_account_requested)
        if hasattr(self, "confirm_password_input") and self.confirm_password_input:
            self.confirm_password_input.returnPressed.connect(self.create_account_requested)

        create_btn = self._ui.findChild(QPushButton, "createAccountButton")
        if create_btn:
            create_btn.clicked.connect(self.create_account_requested)

        sign_in_btn = self._ui.findChild(QPushButton, "signInButton")
        if sign_in_btn:
            sign_in_btn.clicked.connect(self.sign_in_requested)

        back_btn = self._ui.findChild(QPushButton, "backButton")
        if back_btn:
            back_btn.clicked.connect(self.back_requested)

        self.loading = LoadingOverlay(self)
        self._fitted_form = FittedForm(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_ui') and self._ui:
            self._ui.resize(self.size())
