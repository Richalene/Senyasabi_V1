"""Shared styling and a centered, scrollable form for the existing auth layouts."""
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QPushButton, QLabel
from screens.loading import LoadingOverlay


class AuthForm:
    def __init__(self, screen):
        self.screen = screen
        root = Path(__file__).resolve().parents[2]
        screen.setStyleSheet((root / 'resources/styles/common.qss').read_text() +
                            (root / 'resources/styles/auth.qss').read_text())
        screen._ui.layout().setContentsMargins(32, 26, 32, 26)
        screen._ui.layout().setSpacing(9)
        for label in screen._ui.findChildren(QLabel):
            label.setWordWrap(True)
        for button in screen._ui.findChildren(QPushButton):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        for name in ('continueButton', 'createAccountButton'):
            button = screen._ui.findChild(QPushButton, name)
            if button:
                button.setProperty('class', 'primaryButton')
        self.scroll = QScrollArea(screen)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setWidget(screen._ui)
        screen._fitted_form = self
        screen.setMinimumSize(320, 320)
        self.fit()
        screen.loading = LoadingOverlay(screen)

    def fit(self):
        width = min(540, max(280, self.screen.width()-32))
        content = self.screen._ui
        content.ensurePolished()
        preferred = max(420, content.layout().minimumSize().height()+12)
        height = min(preferred, max(240, self.screen.height()-40))
        self.scroll.setGeometry((self.screen.width()-width)//2, (self.screen.height()-height)//2, width, height)
