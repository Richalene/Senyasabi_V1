"""Reusable child overlay for slow work; image animation stays on the Qt timer."""
from pathlib import Path
import weakref

from PySide6.QtCore import QEvent, QRect, Qt, QThread, QTimer, Slot
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QWidget
from shiboken6 import isValid

_IMAGES = Path(__file__).resolve().parents[1] / "resources/img/ui"
_JOBS = set()  # Retain running threads even if their screen is closed/deleted.


class _LoadingJob(QThread):
    def __init__(self, operation, dispose, overlay):
        super().__init__()
        self.operation, self.dispose = operation, dispose
        self.overlay = weakref.ref(overlay)
        self.result = None
        self.error = None
        self.abandoned = False
        # This QThread object lives on the UI thread; delivery must run there.
        self.finished.connect(self.deliver, Qt.ConnectionType.QueuedConnection)

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
        self.abandoned = True
        self.requestInterruption()
        self.wait()
        self.discard()

    @Slot()
    def deliver(self):
        try:
            overlay = self.overlay()
            if self.abandoned:
                if overlay is not None and isValid(overlay) and overlay._job is self:
                    overlay.cancel()
                self.discard()
            elif overlay is None or not isValid(overlay) or overlay._job is not self:
                self.discard()
            else:
                overlay._complete(self)
        finally:
            _JOBS.discard(self)
            app = QApplication.instance()
            if app is not None:
                app.aboutToQuit.disconnect(self.shutdown)
            self.operation = self.dispose = self.error = None
            self.deleteLater()


class LoadingOverlay(QWidget):
    """run(operation, success, failure, dispose) keeps blocking work off the UI thread.

    Call cancel() when leaving a screen. A cancelled result is disposed, never
    delivered to the screen. Callbacks and all widget changes run on the UI thread.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setProperty("ownsGeometry", True)
        self.setObjectName("loadingOverlay")
        self.setAccessibleName("Loading")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_NoMousePropagation)
        self.setCursor(Qt.CursorShape.BusyCursor)
        self.frames = [QPixmap(str(_IMAGES / name)) for name in
                       ("loading_normal.png", "loading_glowing.png")]
        self.frame = 0
        self._job = None
        self._controls = []
        self._previous_focus = None
        self.animation = QTimer(self)
        self.animation.setInterval(450)
        self.animation.timeout.connect(self._animate)
        self.delay = QTimer(self)
        self.delay.setSingleShot(True)
        self.delay.timeout.connect(self._show)
        self.text = QLabel("Loading…", self)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.setWordWrap(True)
        self.text.setTextFormat(Qt.TextFormat.PlainText)
        self.text.setStyleSheet("background: transparent; color: #704833; font-size: 20px; font-weight: 600;")
        parent.installEventFilter(self)
        self.hide()

    @property
    def busy(self):
        return self._job is not None

    def run(self, operation, success, failure, dispose=None, *, message="Loading…",
            controls=(), show_delay_ms=180):
        """Start once; return False for duplicate submissions already in progress."""
        if self.busy:
            return False
        self.text.setText(message)
        self.setAccessibleDescription(message)
        self._success, self._failure = success, failure
        self._controls = [(control, control.isEnabled()) for control in controls]
        for control, _ in self._controls:
            control.setEnabled(False)
        job = _LoadingJob(operation, dispose, self)
        self._job = job
        _JOBS.add(job)
        app = QApplication.instance()
        app.aboutToQuit.connect(job.shutdown)
        self.delay.start(show_delay_ms)
        job.start()
        return True

    def _complete(self, job):
        success, failure = self._success, self._failure
        self._job = None
        self._success = self._failure = None
        self._hide()
        if job.error is not None:
            failure(job.error)
        else:
            result, job.result = job.result, None
            success(result)

    def cancel(self):
        job, self._job = self._job, None
        if job is not None:
            job.abandoned = True
            job.requestInterruption()
        self._success = self._failure = None
        self._hide()

    def _hide(self):
        self.delay.stop()
        self.animation.stop()
        self.hide()
        for control, enabled in self._controls:
            if isValid(control):
                control.setEnabled(enabled)
        self._controls = []
        focus, self._previous_focus = self._previous_focus, None
        if focus is not None and isValid(focus) and focus.isVisible() and focus.isEnabled():
            focus.setFocus(Qt.FocusReason.OtherFocusReason)

    def _show(self):
        if self.busy and self.parentWidget().isVisible():
            self.frame = 0
            self.setGeometry(self.parentWidget().rect())
            self._previous_focus = self.parentWidget().focusWidget()
            self.show()
            self.raise_()
            self.setFocus(Qt.FocusReason.OtherFocusReason)
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

    def keyPressEvent(self, event):
        event.accept()

    def keyReleaseEvent(self, event):
        event.accept()

    def focusNextPrevChild(self, next):
        return False

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
        self.text.setGeometry(canvas.left()+16, canvas.top()+int(canvas.height()*0.72),
                              max(1, canvas.width()-32), max(60, int(canvas.height()*0.14)))
