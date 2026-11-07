import os
import sys
import traceback
import threading
import time
import logging
from pathlib import Path

_last_qt_tick = time.time()

import cv2
import faulthandler

# In PyInstaller windowed/GUI mode (--windowed/console=False), sys.stdout and sys.stderr are None.
# Redirect them to null or a log file so libraries and handlers don't crash.
if sys.stderr is None:
    try:
        log_dir = Path.home() / ".senyasabi" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        sys.stderr = open(log_dir / "crash_native.log", "a", encoding="utf-8")
    except Exception:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")

# Enable faulthandler to catch low-level C/C++ segmentation faults (e.g., in OpenCV or MediaPipe)
try:
    if sys.stderr is not None:
        faulthandler.enable(file=sys.stderr)
    else:
        faulthandler.enable()
except Exception:
    pass

# def run_camera_loop(device_index=0):
#     print("1. Starting camera", flush=True)
    
#     # Use CAP_AVFOUNDATION since you are on macOS
#     cap = cv2.VideoCapture(device_index, cv2.CAP_AVFOUNDATION)
#     print("2. Camera started:", cap.isOpened(), flush=True)

#     if not cap.isOpened():
#         print("Error: Could not open camera.", flush=True)
#         return

#     try:
#         while cap.isOpened():
#             print("3. Reading frame", flush=True)
#             ok, frame = cap.read()

#             if not ok:
#                 print("Frame read failed", flush=True)
#                 break

#             print("4. Frame received", flush=True)

#             # --- UNCOMMENT & WRAP YOUR MODEL INFERENCE HERE ---
#             # print("5. Starting model inference", flush=True)
#             # result = self.model.process(frame)  # Replace with your actual model call
#             # print("6. Inference completed", flush=True)

#             # Optional: break early during testing if you just want to check if it crashes on startup
#             # break

    # except Exception as e:
    #     print(f"Exception caught in loop: {e}", flush=True)
    # finally:
    #     cap.release()
    #     print("Camera released.", flush=True)

def _watchdog_loop():
    global _last_qt_tick
    while True:
        time.sleep(1.0)
        elapsed = time.time() - _last_qt_tick
        if elapsed > 4.0:
            msg = f"\n[{time.strftime('%H:%M:%S')}] *** UI THREAD HUNG FOR {elapsed:.1f}s ***\n"
            sys.stderr.write(msg)
            try:
                with open("lifecycle.log", "a", encoding="utf-8") as lf:
                    lf.write(msg)
                    for thread_id, frame in sys._current_frames().items():
                        lf.write(f"\n--- Thread {thread_id} ---\n")
                        traceback.print_stack(frame, file=lf)
            except Exception:
                pass
            time.sleep(4.0)


_native_log = None  # module-level so the handle lives for the whole process (faulthandler needs it open)


def _diag(message):
    """Timestamped marker in crash_native.log (diagnostic only; never raises)."""
    try:
        if _native_log is not None:
            _native_log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] pid={os.getpid()} {message}\n")
            _native_log.flush()
    except Exception:
        pass


try:
    import atexit
    import faulthandler
    # Append mode, relative to the launch directory (same place as lifecycle.log / crash.log).
    _native_log = open("crash_native.log", "a", encoding="utf-8")
    faulthandler.enable(file=_native_log, all_threads=True)
    _diag("startup")
    atexit.register(_diag, "atexit")
except Exception:
    try:
        faulthandler.enable()
    except Exception:
        pass


def setup_logging():
    """Configure application logging for distributed builds."""
    log_dir = Path.home() / ".senyasabi" / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to current directory if home directory is not accessible
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "senyasabi.log"),
            logging.StreamHandler()
        ]
    )

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
from PySide6.QtWidgets import QApplication, QPushButton, QWidget, QMessageBox

from screens.startup import FittedForm

from screens.app_controller import AppController
from backend import initialize_database
from backend.config import validate_production_config
from backend.api_client import start_connection_monitoring, add_connection_status_listener
from backend.score_service import flush_pending_async


class SenyaSabiApplication(QApplication):
    """Apply presentation to every application screen, including lazy windows."""

    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)
        self.fullscreen = True
        self._wd_timer = QTimer(self)
        def _ping():
            global _last_qt_tick
            _last_qt_tick = time.time()
        self._wd_timer.timeout.connect(_ping)
        self._wd_timer.start(250)
        self._wd_thread = threading.Thread(target=_watchdog_loop, daemon=True)
        self._wd_thread.start()

    def notify(self, receiver, event):
        if event.type() == QEvent.Type.Show and isinstance(receiver, QPushButton):
            from screens.hover_bounce import install_hover_bounce
            install_hover_bounce(receiver)
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
                palette = receiver.palette()
                palette.setColor(QPalette.ColorRole.Window, QColor("#c5d27b"))
                receiver.setPalette(palette)
                receiver.setAutoFillBackground(True)
                if receiver.isFullScreen() != self.fullscreen:
                    QTimer.singleShot(0, lambda window=receiver: self._present(window)
                                      if window.isVisible() else None)
        return result

    def _present(self, window):
        if self.fullscreen:
            window.showFullScreen()
        else:
            window.showMaximized()


def main() -> int:
    # Setup logging first
    setup_logging()
    
    # Validate configuration for distributed builds
    try:
        validate_production_config()
    except RuntimeError as e:
        # If Qt is not initialized yet, show a simple console error
        if QApplication.instance() is None:
            print(f"Configuration Error: {e}", file=sys.stderr)
            return 1
        # Qt is available, show dialog
        QMessageBox.critical(
            None,
            "Configuration Error",
            f"SenyaSabi is not properly configured.\n\n{str(e)}",
            QMessageBox.StandardButton.Ok
        )
        return 1
    
    # Initialize SQLite database on startup
    initialize_database()
    
    # Sync content from server on startup (best effort)
    try:
        from backend.progress_sync import sync_content_if_due
        sync_content_if_due(force=True)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Content sync on startup failed: %s", e)

    app = QApplication.instance() or SenyaSabiApplication(sys.argv)
    controller = AppController()
    app.aboutToQuit.connect(controller.shutdown)
    app.aboutToQuit.connect(lambda: _diag("aboutToQuit"))
    controller.show_startup_splash()
    return app.exec()      


if __name__ == "__main__":
    sys.exit(main())
