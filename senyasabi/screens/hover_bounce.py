from PIL.ImageChops import offset
from PySide6.QtCore import QEasingCurve, QEvent, QObject, QPoint, QVariantAnimation, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsEffect, QPushButton


class HoverScaleEffect(QGraphicsEffect):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 1.0
        self.max_scale = 1.2
        self.animation = QVariantAnimation(self)
        self.animation.valueChanged.connect(self._set_scale)

    def _set_scale(self, value):
        self.scale = float(value)
        self.update()

    def set_hovered(self, hovered):
        self.animation.stop()
        self.animation.setDuration(330 if hovered else 185)
        self.animation.setStartValue(self.scale)
        if hovered:
            self.animation.setKeyValueAt(0.42, 1.2)
            self.animation.setEndValue(1.065)
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        else:
            self.animation.setEndValue(1.0)
            self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.animation.start()

    def boundingRectFor(self, source_rect):
        pad_x = source_rect.width() * (self.max_scale - 1) / 2
        pad_y = source_rect.height() * (self.max_scale - 1) / 2
        return source_rect.adjusted(-pad_x, -pad_y, pad_x, pad_y)

    def draw(self, painter):
        offset = QPoint()
        pixmap = self.sourcePixmap(Qt.CoordinateSystem.LogicalCoordinates, offset)
        if pixmap.isNull():
            self.drawSource(painter)
            return
        center_x = offset.x() + pixmap.width() / 2
        center_y = offset.y() + pixmap.height() / 2
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(center_x, center_y)
        painter.scale(self.scale, self.scale)
        painter.translate(-center_x, -center_y)
        painter.drawPixmap(offset, pixmap)
        painter.restore()


class _HoverScaleFilter(QObject):
    def __init__(self, button: QPushButton, effect: HoverScaleEffect):
        super().__init__(button)
        self.button = button
        self.effect = effect

    def eventFilter(self, watched, event):
        if watched is self.button:
            if event.type() == QEvent.Type.Enter:
                self.effect.set_hovered(True)
            elif event.type() == QEvent.Type.Leave:
                self.effect.set_hovered(False)
        return False


def install_hover_bounce(button: QPushButton):
    if button.property("noHoverBounce") or button.property("hoverBounceHandled"):
        return None
    if button.graphicsEffect() is not None:
        return None
    effect = HoverScaleEffect(button)
    button.setGraphicsEffect(effect)
    event_filter = _HoverScaleFilter(button, effect)
    button.installEventFilter(event_filter)
    button._hover_scale_filter = event_filter
    return effect