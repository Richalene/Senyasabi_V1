"""Shared navigation artwork with real Qt buttons and live streak text."""
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QEvent, QRectF, QSize, Qt
from PySide6.QtGui import QBitmap, QPainter, QPixmap, QRegion
from PySide6.QtWidgets import QLabel, QMenu, QPushButton, QWidget


ASSETS = Path(__file__).resolve().parents[1] / "resources/img/ui"


@lru_cache(maxsize=8)
def _artwork(name, trim=False):
    source = QPixmap(str(ASSETS / name))
    if trim and not source.isNull():
        # Trim transparent export padding in memory; resource files stay untouched.
        bounds = QRegion(QBitmap.fromImage(source.toImage().createAlphaMask())).boundingRect()
        if not bounds.isEmpty():
            source = source.copy(bounds)
    return source


def _fit(source, area):
    if source.isNull() or area.isEmpty():
        return QRectF()
    scale = min(area.width() / source.width(), area.height() / source.height())
    width, height = source.width() * scale, source.height() * scale
    return QRectF(area.center().x() - width / 2, area.center().y() - height / 2, width, height)


class AssetButton(QPushButton):
    """A clickable, keyboard-accessible button painted only with its PNG."""

    def __init__(self, asset="hamburger.png", parent=None, *, accessible_name="Menu"):
        super().__init__(parent)
        self.source = _artwork(asset)
        self.setText("")
        self.setFlat(True)
        self.setAccessibleName(accessible_name)
        self.setToolTip(accessible_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("AssetButton { background: transparent; border: none; padding: 0; min-width: 0; min-height: 0; }")

    def sizeHint(self):
        return QSize(56, 64)

    def minimumSizeHint(self):
        return QSize(32, 32)

    def paintEvent(self, event):
        if self.source.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing |
                               QPainter.RenderHint.SmoothPixmapTransform)
        area = QRectF(self.rect())
        if self.isDown():
            area.adjust(1.5, 1.5, -1.5, -1.5)
        painter.setOpacity(.45 if not self.isEnabled() else .82 if self.isDown()
                           else .90 if self.hasFocus() else .94 if self.underMouse() else 1.0)
        painter.drawPixmap(_fit(self.source, area), self.source, QRectF(self.source.rect()))

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)


class BackButton(AssetButton):
    def __init__(self, parent=None):
        super().__init__("back-button.png", parent, accessible_name="Back")

    def sizeHint(self):
        return QSize(52, 52)

    @classmethod
    def replace(cls, old):
        """Replace a Designer placeholder before connecting its navigation callback."""
        parent = old.parentWidget()
        button = cls(parent)
        button.setObjectName(old.objectName())
        button.setGeometry(old.geometry())
        button.setMinimumSize(old.minimumSize())
        button.setMaximumSize(old.maximumSize())
        button.setSizePolicy(old.sizePolicy())
        button.setEnabled(old.isEnabled())
        if parent is not None:
            if parent.layout() is not None:
                parent.layout().replaceWidget(old, button)
            button.stackUnder(old)
        button.setVisible(not old.isHidden())
        old.hide()
        old.setObjectName("")
        old.setParent(None)
        old.deleteLater()
        return button


class StreakDisplay(QWidget):
    """The supplied streak container, its supplied flame, and dynamic Qt text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source = _artwork("streak-bg.png")
        # This export has an empty medallion; its flame is a separate supplied PNG.
        self.flame = _artwork("streak.png", trim=True)
        self.value_label = QLabel("0 Days", self)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setTextFormat(Qt.TextFormat.PlainText)
        self.value_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("StreakDisplay { background: transparent; border: none; }")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        area = _fit(self.source, QRectF(self.rect()))
        scale = area.width() / 406
        self.value_label.setGeometry(round(area.x() + 48 * scale), round(area.y() + 22 * scale),
                                     round(230 * scale), round(74 * scale))
        self.value_label.setStyleSheet(
            "QLabel { background: transparent; border: none; padding: 0; color: #704833; "
            "font-family: 'Segoe UI'; font-style: italic; font-weight: 500; "
            f"font-size: {max(1, 40 * scale):.2f}px; }}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing |
                               QPainter.RenderHint.SmoothPixmapTransform)
        area = _fit(self.source, QRectF(self.rect()))
        if area.isEmpty():
            return
        painter.drawPixmap(area, self.source, QRectF(self.source.rect()))
        scale = area.width() / 406
        flame_area = QRectF(area.x() + 314 * scale, area.y() + 33 * scale, 42 * scale, 50 * scale)
        painter.drawPixmap(_fit(self.flame, flame_area), self.flame, QRectF(self.flame.rect()))


class SenyaSabiHeader(QWidget):
    """Optional shared controls anchored to the fitted Figma canvas, never the desktop."""

    def __init__(self, parent=None, *, show_back=False, show_streak=True, show_menu=True):
        super().__init__(parent)
        self.setProperty("ownsGeometry", True)
        self.setObjectName("senyasabiHeader")
        self.setStyleSheet("SenyaSabiHeader { background: transparent; border: none; }")
        self.back_button = BackButton(self) if show_back else None
        self.streak = StreakDisplay(self) if show_streak else None
        self.streak_label = self.streak.value_label if self.streak is not None else None
        self.menu_button = AssetButton(parent=self) if show_menu else None
        self._positions = []
        cursor = 0
        if self.back_button is not None:
            self._positions.append((self.back_button, QRectF(cursor, 28, 74, 74)))
            cursor += 98
        if self.streak is not None:
            self._positions.append((self.streak, QRectF(cursor, 8, 406, 122)))
            cursor += 406
        if self.menu_button is not None:
            # Account for the PNGs' transparent export margins when spacing their art.
            cursor -= 6 if self.streak is not None else 0
            self._positions.append((self.menu_button, QRectF(cursor, 0, 111, 130)))
            cursor += 111
        self._native_size = QSize(max(1, cursor), 130)
        self._canvas = None
        self.resize(self._native_size)

    def sizeHint(self):
        return self._native_size

    def set_streak_text(self, text):
        if self.streak_label is not None:
            self.streak_label.setText(str(text))

    def anchor_to_canvas(self, canvas_size):
        self._canvas = QSize(canvas_size)
        self.parentWidget().installEventFilter(self)
        self.fit()

    def fit(self):
        parent = self.parentWidget()
        if parent is None or self._canvas is None or self._canvas.isEmpty():
            return
        scale = min(parent.width() / self._canvas.width(), parent.height() / self._canvas.height())
        unit = self._canvas.width() / 1920
        width, height = self._native_size.width() * unit * scale, 130 * unit * scale
        left = (parent.width() - self._canvas.width() * scale) / 2
        top = (parent.height() - self._canvas.height() * scale) / 2
        self.setGeometry(round(left + self._canvas.width() * scale - 32 * unit * scale - width),
                         round(top + 16 * unit * scale), round(width), round(height))
        self.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "_positions"):
            return
        scale = min(self.width() / self._native_size.width(), self.height() / 130)
        for widget, rect in self._positions:
            widget.setGeometry(round(rect.x() * scale), round(rect.y() * scale),
                               round(rect.width() * scale), round(rect.height() * scale))

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            self.fit()
        return super().eventFilter(watched, event)


def install_page_menu(widget, *, header=None, canvas_size=None):
    """Attach the shared header/menu with Camera Settings and Sign Out actions."""
    if header is None:
        return None
    if header.menu_button is not None:
        if header.menu_button.objectName() == "menuBtn" and hasattr(widget, "menu_requested"):
            header.menu_button.clicked.connect(widget.menu_requested.emit)
        else:
            from screens.dialogs import MenuCalloutPopup
            popup = MenuCalloutPopup(header.menu_button)
            header.menu_button.clicked.connect(popup.toggle_popup)
            # Retain backwards-compatible mock actions for screens listening to camera / logout
            class _MockAction:
                def __init__(self, name):
                    self.name = name
                    self._callbacks = []
                def connect(self, cb):
                    self._callbacks.append(cb)
                def emit(self):
                    for cb in self._callbacks: cb()
                @property
                def triggered(self):
                    return self
            class _MockMenu:
                def __init__(self):
                    self.camera_action = _MockAction("camera")
                    self.sign_out_action = _MockAction("sign_out")
            header.menu_button._menu_compat = _MockMenu()
            header.menu_button.menu = lambda: header.menu_button._menu_compat
            popup.sign_out_requested.connect(header.menu_button._menu_compat.sign_out_action.emit)
    return header


