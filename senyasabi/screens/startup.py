"""Thin wrappers around the existing Welcome and Landing forms."""
from pathlib import Path
import re

from PySide6.QtCore import QEvent, QObject, QRect, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QAbstractScrollArea, QLayout, QMessageBox, QAbstractButton
from shiboken6 import isValid
from ui.generated.welcome_ui import Ui_Welcome
from ui.generated.landing_ui import Ui_Landing


class FittedForm(QObject):
    """Fit an existing absolute-positioned form without cropping its canvas."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.base_style = window.styleSheet()
        self.base_font = window.font()
        self.layout_canvas = getattr(window, "_ui", None)
        if self.layout_canvas is not None and self.layout_canvas.layout() is not None:
            self.canvas = self.layout_canvas.size()
            self.widgets = None
            window.setMinimumSize(0, 0)
            window.installEventFilter(self)
            return
        self.canvas = window.size()
        self.widgets = []
        self.layouts = []
        self.icons = []

        def collect(parent, managed=False):
            layout = parent.layout()
            if layout is not None:
                for child_layout in [layout, *layout.findChildren(QLayout)]:
                    self.layouts.append((child_layout, child_layout.contentsMargins(), child_layout.spacing()))
            for widget in parent.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly):
                # Overlays track their parent's rect independently of the form canvas.
                if widget.property("ownsGeometry"):
                    continue
                self.widgets.append((widget, window.rect() if widget.objectName() == "imgBackground"
                                     else widget.geometry(), widget.styleSheet(), widget.minimumSize(),
                                     widget.maximumSize(), managed or layout is not None))
                if isinstance(widget, QAbstractButton) and not widget.icon().isNull():
                    self.icons.append((widget, widget.iconSize()))
                # Scroll contents are dynamic and owned by Qt's layouts, not this fitter.
                if not isinstance(widget, QAbstractScrollArea):
                    collect(widget, managed or layout is not None)
        collect(window)
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
        def scaled_style(style, target_h=0):
            def repl(match):
                raw = float(match[1]) * scale
                prefix = style[:match.start()]
                last_prop = prefix.split(";")[-1] if ";" in prefix else prefix
                if "border-radius" in last_prop:
                    int_r = round(raw)
                    if target_h > 0:
                        int_r = min(int_r, max(1, (target_h // 2) - 1))
                    return f"{int_r}px"
                return f"{round(raw)}px"
            return re.sub(r"(\d+(?:\.\d+)?)px", repl, style)
        if self.base_style:
            self.window.setStyleSheet(scaled_style(self.base_style))
        font = type(self.base_font)(self.base_font)
        if font.pointSizeF() > 0:
            font.setPointSizeF(max(1, self.base_font.pointSizeF()*scale))
        elif font.pixelSize() > 0:
            font.setPixelSize(max(1, round(self.base_font.pixelSize()*scale)))
        self.window.setFont(font)
        if self.widgets is None:
            self.layout_canvas.setGeometry(round(left), round(top), round(self.canvas.width()*scale), round(self.canvas.height()*scale))
            return
        for widget, rect, style, minimum, maximum, managed in self.widgets:
            if not isValid(widget):
                continue
            direct = widget.parentWidget() is self.window
            widget.setMinimumSize(round(minimum.width()*scale), round(minimum.height()*scale))
            widget.setMaximumSize(round(maximum.width()*scale) if maximum.width()<16777215 else 16777215,
                                  round(maximum.height()*scale) if maximum.height()<16777215 else 16777215)
            if not managed:
                widget.setGeometry(QRect(
                    round(rect.x() * scale + (left if direct else 0)),
                    round(rect.y() * scale + (top if direct else 0)),
                    round(rect.width() * scale), round(rect.height() * scale)))
            if style:
                widget.setStyleSheet(scaled_style(style, target_h=round(rect.height() * scale)))
        for layout, margins, spacing in self.layouts:
            if isValid(layout):
                layout.setContentsMargins(*(round(value*scale) for value in
                    (margins.left(), margins.top(), margins.right(), margins.bottom())))
                if spacing >= 0:
                    layout.setSpacing(round(spacing*scale))
        for button, size in self.icons:
            if isValid(button):
                button.setIconSize(QSize(max(1, round(size.width()*scale)), max(1, round(size.height()*scale))))


class StartupScreen(QWidget):
    def __init__(self, form, background_name):
        super().__init__()
        self.ui = form()
        self.ui.setupUi(self)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)
        self.resize(1920, 1080)
        self.ui.imgBackground.setGeometry(self.rect())
        self.ui.imgBackground.setText('Welcome to SenyaSabi')
        self.ui.imgBackground.setStyleSheet('background: #c5d27b; color: #704833; border: none; font-size: 42px;')
        self.background_path = Path(__file__).resolve().parents[1] / "resources" / "img" / background_name
        if self.background_path.is_file():
            pixmap = QPixmap(str(self.background_path))
            if not pixmap.isNull():
                self.setMinimumSize(0, 0)
                self.setMaximumSize(16777215, 16777215)
                self.resize(pixmap.size())
                self.ui.imgBackground.setGeometry(self.rect())
                self.ui.imgBackground.setStyleSheet('background: #c5d27b; border: none;')
                self.ui.imgBackground.setPixmap(pixmap)
                self.ui.imgBackground.setScaledContents(True)



class WelcomeScreen(StartupScreen):
    def __init__(self):
        super().__init__(Ui_Welcome, "welcome.png")
        next_button_path = Path(__file__).resolve().parents[1] / "resources" / "img" / "ui" / "nextbtn.png"
        icon = QIcon(str(next_button_path))
        if icon.isNull():
            self.ui.btnContinue.setText("Continue")
        self.ui.btnContinue.setGeometry(904, 870, 112, 112)
        self.ui.btnContinue.setStyleSheet('QPushButton { background: transparent; border: none; padding: 0; } QPushButton:hover { background: rgba(255,255,255,35); border-radius: 56px; }')
        self.ui.btnContinue.setIcon(icon)
        self.ui.btnContinue.setIconSize(self.ui.btnContinue.size())
        self.ui.nextButton.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.ui.nextButton.hide()
        self._fitted_form = FittedForm(self)


class LandingScreen(StartupScreen):
    def __init__(self):
        super().__init__(Ui_Landing, "landing.png")
        # Hit regions match the actual 1920x1080 supplied Figma bitmap.
        self.ui.btnGetStarted.setGeometry(176, 815, 394, 90)
        self.ui.btnLearnMore.setGeometry(612, 815, 394, 90)
        self.ui.btnLogin.setGeometry(1660, 28, 190, 64)
        self.ui.btnLogin.setText('Log in')
        self.ui.btnLogin.setStyleSheet('QPushButton { color: #704833; background: #fff9e9; border: 1px solid #a39b68; border-radius: 20px; font-size: 22px; font-weight: 600; } QPushButton:hover { background: #fff0b8; }')
        self.ui.btnLearnMore.clicked.connect(self.show_about)
        self._fitted_form = FittedForm(self)

    def show_about(self):
        import os
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, 'About SenyaSabi',
            'Learn Filipino Sign Language through lessons, quizzes, and three spelling games. '
            'Camera recognition runs only when you choose a camera-based activity. '
            'You can explore the other activities without a camera.')
        if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            from screens.dialogs import ComingSoonDialog
            dialog = ComingSoonDialog(self)
            dialog.exec()
