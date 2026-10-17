"""Thin wrappers around the existing Welcome and Landing forms."""
from pathlib import Path
import re

from PySide6.QtCore import QEvent, QObject, QRect, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget
from ui.generated.welcome_ui import Ui_Welcome
from ui.generated.landing_ui import Ui_Landing


class FittedForm(QObject):
    """Fit an existing absolute-positioned form without cropping its canvas."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.canvas = window.size()
        self.widgets = [
            (widget, window.rect() if widget.objectName() == "imgBackground"
             else widget.geometry(), widget.styleSheet())
            for widget in window.findChildren(QWidget)
        ]
        window.setMinimumSize(0, 0)
        window.setMaximumSize(16777215, 16777215)
        window.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self.fit()
        return super().eventFilter(watched, event)

    def fit(self):
        scale = min(self.window.width() / self.canvas.width(),
                    self.window.height() / self.canvas.height())
        left = (self.window.width() - self.canvas.width() * scale) / 2
        top = (self.window.height() - self.canvas.height() * scale) / 2
        for widget, rect, style in self.widgets:
            direct = widget.parentWidget() is self.window
            widget.setGeometry(QRect(
                round(rect.x() * scale + (left if direct else 0)),
                round(rect.y() * scale + (top if direct else 0)),
                round(rect.width() * scale), round(rect.height() * scale)))
            if style:
                widget.setStyleSheet(re.sub(
                    r"(\d+(?:\.\d+)?)px",
                    lambda match: f"{float(match[1]) * scale:.2f}px", style))


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

        self._fitted_form = FittedForm(self)


class WelcomeScreen(StartupScreen):
    def __init__(self):
        super().__init__(Ui_Welcome, "welcome.png")
        next_button_path = Path(__file__).resolve().parents[1] / "resources" / "img" / "ui" / "nextbtn.png"
        icon = QIcon(str(next_button_path))
        if icon.isNull():
            raise RuntimeError(f"Failed to load welcome button image: {next_button_path}")
        self.ui.btnContinue.setIcon(icon)
        self.ui.btnContinue.setIconSize(self.ui.btnContinue.size())
        self.ui.nextButton.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )


class LandingScreen(StartupScreen):
    def __init__(self):
        super().__init__(Ui_Landing, "landing.png")
