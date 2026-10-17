"""Reusable child overlay for slow work; image animation stays on the Qt timer."""
from pathlib import Path

from PySide6.QtCore import QEvent, QRect, Qt, QThread, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget
from shiboken6 import isValid

_IMAGES = Path(__file__).resolve().parents[1] / "resources/img/ui"
_JOBS = set()  # Retain running threads even if their screen is closed/deleted.


class _LoadingJob(QThread):
    def __init__(self, operation, dispose):
        super().__init__()
        self.operation, self.dispose = operation, dispose
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.operation()
        except Exception as error:
            self.error = error
        if self.isInterruptionRequested():
            self.discard()

    def discard(self):
        result, self.result = self.result, None
        if result is not None and self.dispose:
            self.dispose(result)

    def shutdown(self):
        self.requestInterruption()
        self.wait()
        self.discard()


class LoadingOverlay(QWidget):
    """run(operation, success, failure, dispose) keeps blocking work off the UI thread.

    Call cancel() when leaving a screen. A cancelled result is disposed, never
    delivered to the screen. Callbacks and all widget changes run on the UI thread.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.frames = [QPixmap(str(_IMAGES / name)) for name in
                       ("loading_normal.png", "loading_glowing.png")]
        self.frame = 0
        self._job = None
        self.animation = QTimer(self)
        self.animation.setInterval(450)
        self.animation.timeout.connect(self._animate)
        self.delay = QTimer(self)
        self.delay.setSingleShot(True)
        self.delay.timeout.connect(self._show)
        self.text = QLabel("Loading...", self)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.setStyleSheet("background: transparent; color: #704833; font-size: 20px; font-weight: 600;")
        parent.installEventFilter(self)
        self.hide()

    @property
    def busy(self):
        return self._job is not None

    def run(self, operation, success, failure, dispose=None):
        self.cancel()
        job = _LoadingJob(operation, dispose)
        self._job = job
        _JOBS.add(job)
        app = QApplication.instance()
        app.aboutToQuit.connect(job.shutdown)

        def finished():
            try:
                if not isValid(self) or self._job is not job:
                    job.discard()
                    return
                self._job = None
                self._hide()
                if job.error is not None:
                    failure(job.error)
                else:
                    result, job.result = job.result, None
                    success(result)
            finally:
                _JOBS.discard(job)
                app.aboutToQuit.disconnect(job.shutdown)
                job.deleteLater()

        job.finished.connect(finished)
        self.delay.start(180)
        job.start()

    def cancel(self):
        job, self._job = self._job, None
        if job is not None:
            job.requestInterruption()
        self._hide()

    def _hide(self):
        self.delay.stop()
        self.animation.stop()
        self.hide()

    def _show(self):
        if self.busy and self.parentWidget().isVisible():
            self.frame = 0
            self.setGeometry(self.parentWidget().rect())
            self.show()
            self.raise_()
            self.animation.start()

    def _animate(self):
        self.frame = 1 - self.frame
        self.update()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize:
            self.setGeometry(watched.rect())
        elif event.type() == QEvent.Type.Hide:
            self.cancel()
        return super().eventFilter(watched, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#C2D076"))
        image = self.frames[self.frame]
        canvas = self.rect()
        if not image.isNull():
            size = image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            canvas = QRect((self.width()-size.width())//2, (self.height()-size.height())//2,
                           size.width(), size.height())
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawPixmap(canvas, image)
        self.text.setGeometry(canvas.left(), canvas.top()+int(canvas.height()*0.83), canvas.width(), 40)
