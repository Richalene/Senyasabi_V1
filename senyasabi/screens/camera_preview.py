"""Rounded, aspect-preserving camera presentation; never changes capture frames."""
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QLabel


class RoundedCameraPreview(QLabel):
    """Keep the full source image and fit/clip it again on every paint/resize."""

    def __init__(self, text="", parent=None, *, radius=28, fill_crop=False):
        super().__init__(text, parent)
        self.radius = radius
        self.fill_crop = fill_crop
        self._source = QPixmap()
        self.setObjectName("roundedCameraPreview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.PlainText)
        # The painter owns the surface, including its transparent outer corners.
        # Suppress inherited QLabel backgrounds/borders, which can be square.
        self.setStyleSheet("RoundedCameraPreview { background: transparent; border: none; padding: 0; }")
        self.setAutoFillBackground(False)

    @classmethod
    def replace(cls, label):
        """Promote a Designer placeholder without changing its layout or geometry."""
        parent = label.parentWidget()
        preview = cls(label.text(), parent)
        preview.setObjectName(label.objectName())
        preview.setGeometry(label.geometry())
        preview.setMinimumSize(label.minimumSize())
        preview.setMaximumSize(label.maximumSize())
        preview.setSizePolicy(label.sizePolicy())
        preview.setFont(label.font())
        preview.setToolTip(label.toolTip())
        preview.setAccessibleName(label.accessibleName())
        preview.setAccessibleDescription(label.accessibleDescription())
        preview.setEnabled(label.isEnabled())
        if parent is not None and parent.layout() is not None:
            parent.layout().replaceWidget(label, preview)
        if parent is not None:
            preview.stackUnder(label)
        preview.setVisible(not label.isHidden())
        label.hide()
        label.setObjectName("")
        label.setParent(None)
        label.deleteLater()
        return preview

    def sizeHint(self):
        # A high-resolution source must not force the surrounding layout to grow.
        return QSize(320, 240)

    def minimumSizeHint(self):
        return QSize(80, 60)

    def set_bgr_frame(self, frame):
        """Copy a BGR display frame, leaving recognition's pixels and shape intact."""
        image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0],
                       QImage.Format.Format_BGR888).copy()
        self.setPixmap(QPixmap.fromImage(image))

    def setPixmap(self, pixmap):
        super().clear()
        self._source = QPixmap(pixmap)
        self.update()

    def pixmap(self):
        return QPixmap(self._source)

    def clear(self):
        self._source = QPixmap()
        super().clear()
        self.update()

    def setText(self, text):
        self._source = QPixmap()
        super().setText(text)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing |
                               QPainter.RenderHint.SmoothPixmapTransform)
        frame_rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if frame_rect.isEmpty():
            return
        frame_path = QPainterPath()
        frame_path.addRoundedRect(frame_rect, self.radius, self.radius)
        painter.fillPath(frame_path, QColor("#EEEAD5"))
        if not self._source.isNull():
            available = frame_rect.adjusted(2, 2, -2, -2)
            if not available.isEmpty():
                if self.fill_crop:
                    scale = max(available.width() / self._source.width(),
                                available.height() / self._source.height())
                else:
                    scale = min(available.width() / self._source.width(),
                                available.height() / self._source.height())
                width, height = self._source.width() * scale, self._source.height() * scale
                image_rect = QRectF(available.center().x() - width / 2,
                                    available.center().y() - height / 2, width, height)
                image_path = QPainterPath()
                image_path.addRoundedRect(image_rect, self.radius, self.radius)
                painter.save()
                painter.setClipPath(frame_path)
                # Round the image too: letterboxing must not expose square video corners.
                painter.setClipPath(image_path, Qt.ClipOperation.IntersectClip)
                # Selfie-style mirror applies to display only; frames stay unflipped.
                cx = image_rect.center().x()
                painter.translate(cx, 0)
                painter.scale(-1, 1)
                painter.translate(-cx, 0)
                painter.drawPixmap(image_rect, self._source, QRectF(self._source.rect()))
                painter.restore()
        else:
            painter.setPen(QColor("#704833"))
            painter.setFont(self.font())
            painter.drawText(frame_rect.adjusted(14, 14, -14, -14),
                             Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                             self.text())
        painter.setPen(QPen(QColor("#A39B68"), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(frame_path)
