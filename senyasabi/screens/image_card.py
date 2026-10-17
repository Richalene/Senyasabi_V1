"""Centered, smoothly scaled character artwork with real rounded clipping."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QWidget


class CharacterImageCard(QWidget):
    def __init__(self, image=None, parent=None, radius=28):
        super().__init__(parent)
        self.radius = radius
        self.source = QPixmap(str(image)) if image else QPixmap()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_image(self, image):
        self.source = QPixmap(str(image))
        self.update()

    def paintEvent(self, event):
        if self.source.isNull() or not self.width() or not self.height():
            return
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        target = QRectF(self.rect())
        clip = QPainterPath()
        clip.addRoundedRect(target, self.radius, self.radius)
        painter.setClipPath(clip)
        scale = max(self.width()/self.source.width(), self.height()/self.source.height())
        width, height = self.width()/scale, self.height()/scale
        crop = QRectF((self.source.width()-width)/2, (self.source.height()-height)/2, width, height)
        painter.drawPixmap(target, self.source, crop)
