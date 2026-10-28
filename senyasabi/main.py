import os
import sys
import traceback

try:
    import faulthandler
    faulthandler.enable()
except Exception:
    pass

def _excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    sys.stderr.write(f"\n================ CRITICAL CRASH ================\n{tb}\n================================================\n")
    sys.stderr.flush()
    try:
        with open("crash.log", "a", encoding="utf-8") as f:
            f.write(f"\n================ CRITICAL CRASH ================\n{tb}\n================================================\n")
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _excepthook

if hasattr(sys, "unraisablehook"):
    def _unraisablehook(unraisable):
        msg = f"\n[UNRAISABLE] {unraisable.err_msg}: {unraisable.object}\n"
        if unraisable.exc_traceback:
            msg += "".join(traceback.format_tb(unraisable.exc_traceback))
        msg += f"{unraisable.exc_type.__name__}: {unraisable.exc_value}\n"
        sys.stderr.write(msg)
        sys.stderr.flush()
        try:
            with open("crash.log", "a", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
    sys.unraisablehook = _unraisablehook

# On Windows, use FFmpeg backend so Qt can demux QuickTime (.MOV) and MP4 without third-party splitters.
# On macOS, Qt's default 'darwin' (AVFoundation) backend provides native Apple Silicon acceleration for .MOV and .MP4.
if sys.platform == "win32":
    os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from screens.startup import FittedForm

from screens.app_controller import AppController
from backend import initialize_database


class SenyaSabiApplication(QApplication):
    """Apply presentation to every application screen, including lazy windows."""

    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        self.fullscreen = True

    def notify(self, receiver, event):
        screen = (isinstance(receiver, QWidget) and receiver.isWindow()
                  and receiver.windowType() == Qt.WindowType.Window)
        if event.type() == QEvent.Type.KeyPress and isinstance(receiver, QWidget):
            window = receiver.window()
            if window.windowType() == Qt.WindowType.Window:
                if event.key() == Qt.Key.Key_F11:
                    self.fullscreen = not window.isFullScreen()
                    self._present(window)
                    event.accept()
                    return True
                if event.key() == Qt.Key.Key_Escape and window.isFullScreen():
                    self.fullscreen = False
                    window.showMaximized()
                    event.accept()
                    return True
        result = super().notify(receiver, event)
        if screen and event.type() == QEvent.Type.Show:
            if not getattr(receiver, "_presentation_ready", False):
                receiver._presentation_ready = True
                if not hasattr(receiver, "_fitted_form"):
                    receiver._fitted_form = FittedForm(receiver)
                palette = receiver.palette()
                palette.setColor(QPalette.ColorRole.Window, QColor("#c5d27b"))
                receiver.setPalette(palette)
                receiver.setAutoFillBackground(True)
            if receiver.isFullScreen() != self.fullscreen:
                QTimer.singleShot(0, lambda window=receiver: self._present(window)
                                  if window.isVisible() else None)
        if screen and event.type() == QEvent.Type.Resize:
            fitted = getattr(receiver, "_fitted_form", None)
            if fitted is not None:
                fitted.fit()
        return result

    def _present(self, window):
        if self.fullscreen:
            window.showFullScreen()
        else:
            window.showMaximized()


def main() -> int:
    # Initialize SQLite database on startup
    initialize_database()

    app = QApplication.instance() or SenyaSabiApplication(sys.argv)
    controller = AppController()
    app.aboutToQuit.connect(controller.shutdown)
    controller.show_welcome()
    return app.exec()      


if __name__ == "__main__":
    sys.exit(main())
