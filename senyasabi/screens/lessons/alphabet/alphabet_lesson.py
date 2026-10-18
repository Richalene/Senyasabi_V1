"""
FSL Alphabet Lesson widget.

Wires together:
  - alphabet_lesson.ui  (Qt Designer layout)
  - SignRecognitionEngine(mode="alphabet")  (camera + model)
  - CameraPracticeSession  (state machine)

Usage (from main.py or any parent widget):

    from screens.lessons.alphabet.alphabet_lesson import AlphabetLessonWidget

    LESSON_LETTERS = {
        1: list("ABCDEF"),
        2: list("GHIJKL"),
        3: list("MNOPQR"),
        4: list("STUVWX"),
        5: list("YZ"), (make it 4)
    }

    def open_alphabet_lesson(self, lesson_number: int = 1):
        letters = LESSON_LETTERS[lesson_number]
        self.alphabet_window = AlphabetLessonWidget(
            letters=letters,
            lesson_number=lesson_number,
        )
        self.alphabet_window.lesson_finished.connect(self.show)   # reshow menu
        self.hide()
        self.alphabet_window.show()
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

# ── path gymnastics so imports work whether run directly or as a package ──
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from screens.camera_access import LessonCameraMixin, alphabet_engine
from screens.camera_preview import RoundedCameraPreview
from screens.media_player import SignVideoPlayer
from screens.navigation import BackButton, install_page_menu
from backend.session_state import CameraPracticeSession, Event, SessionState

# ── lesson definitions ────────────────────────────────────────────────────
LESSON_LETTERS: dict[int, List[str]] = {
    1: list("ABCDEF"),
    2: list("GHIJKL"),
    3: list("MNOPQR"),
    4: list("STUVWX"),
    5: list("YZ"),
}

_UI_FILE = _ROOT / "ui" / "designer" / "alphabet_lesson.ui"
_VRM_DIR = _ROOT / "resources" / "VRM_SIGNS"

# ── colour constants ──────────────────────────────────────────────────────
_CLR_CORRECT  = ("color:#0f1117; background-color:#5ecf8a;"
                 "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_WRONG    = ("color:#ffffff; background-color:#e05252;"
                 "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HOLDING  = ("color:#0f1117; background-color:#f0c040;"
                 "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HIDDEN   = "color:transparent; background-color:transparent;"


class AlphabetLessonWidget(LessonCameraMixin, QWidget):
    """
    Self-contained alphabet lesson window.

    Signals
    -------
    lesson_finished
        Emitted when the user exits (back button) or completes the lesson.
        Connect this to your main window's `.show()` to restore the menu.
    """

    lesson_finished = Signal()

    def __init__(
        self,
        letters: List[str] | None = None,
        lesson_number: int = 1,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        # ── resolve letters ───────────────────────────────────────────────
        if letters is None:
            letters = LESSON_LETTERS.get(lesson_number, list("ABCDEF"))
        self._letters = letters
        self._lesson_number = lesson_number

        # ── load UI ───────────────────────────────────────────────────────
        loader = QUiLoader()
        self._ui = loader.load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load UI file: {_UI_FILE}")
        self._ui.setStyleSheet(self._ui.styleSheet() + (_ROOT / "resources/styles/lessons.qss").read_text())

        # Resize outer widget to match UI
        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle(f"SenyaSabi — Alphabet Lesson {lesson_number}")

        # ── shorthand refs to UI widgets ─────────────────────────────────
        self._title_lbl:      QLabel = self._ui.findChild(QLabel,      "lessonTitle")
        self._progress_lbl:   QLabel = self._ui.findChild(QLabel,      "progressLabel")
        self._score_lbl:      QLabel = self._ui.findChild(QLabel,      "scoreLabel")
        self._letter_lbl:     QLabel = self._ui.findChild(QLabel,      "letterDisplay")
        self._letter_sub:     QLabel = self._ui.findChild(QLabel,      "letterSubtitle")
        self._ref_img_lbl:    QLabel = self._ui.findChild(QLabel,      "refImageLabel")
        self._camera_lbl = RoundedCameraPreview.replace(
            self._ui.findChild(QLabel, "cameraLabel")
        )
        self._cam_dot:        QLabel = self._ui.findChild(QLabel,      "camStatusDot")
        self._feedback_lbl:   QLabel = self._ui.findChild(QLabel,      "feedbackLabel")
        self._pred_lbl:       QLabel = self._ui.findChild(QLabel,      "predictionLabel")
        self._hold_bg:        QLabel = self._ui.findChild(QLabel,      "holdBarBg")
        self._hold_fill:      QLabel = self._ui.findChild(QLabel,      "holdBarFill")

        from PySide6.QtWidgets import QPushButton
        self._next_btn = self._ui.findChild(QPushButton, "nextBtn")
        self._back_btn = BackButton.replace(self._ui.findChild(QPushButton, "backBtn"))
        self._back_btn.setGeometry(1138, 24, 52, 52)
        self._score_lbl.setGeometry(950, 24, 166, 28)
        install_page_menu(self, canvas_size=QSize(1306, 753))

        # ── connect buttons ───────────────────────────────────────────────
        self._next_btn.clicked.connect(self._on_skip)
        self._back_btn.clicked.connect(self._on_back)
        self.video = SignVideoPlayer(self._ref_img_lbl)
        QVBoxLayout(self._ref_img_lbl).addWidget(self.video)
        self.video.hide()

        # ── title label ───────────────────────────────────────────────────
        self._title_lbl.setText(f"FSL ALPHABET — LESSON {lesson_number}")

        # ── backend: recognition engine ───────────────────────────────────
        self._engine = None
        self._set_cam_dot(False)
        self._resources_closed = False

        # ── backend: session state ────────────────────────────────────────
        self._session = CameraPracticeSession(targets=self._letters)

        # ── camera timer (≈ 30 fps) ───────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

        # ── feedback auto-clear timer ─────────────────────────────────────
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_action = None
        self._feedback_timer.timeout.connect(self._on_feedback_timeout)

        # ── initial render ────────────────────────────────────────────────
        self._refresh_ui()
        self._init_camera(alphabet_engine)


    # ── UI helpers ────────────────────────────────────────────────────────

    def _set_cam_dot(self, active: bool):
        color = "#5ecf8a" if active else "#e05252"
        self._cam_dot.setStyleSheet(
            f"background-color:{color}; border-radius:5px;"
        )

    def _load_ref_image(self, letter: str):
        """Load VRM reference image for the given letter into refImageLabel."""
        self.video.set_sign("alphabet", letter.lower())
        self.video.setVisible(self.video.media.available)
        if self.video.media.available:
            self._ref_img_lbl.clear()
            return
        img_path = _VRM_DIR / f"{letter.upper()}.png"
        lbl = self._ref_img_lbl
        if img_path.exists():
            pix = QPixmap(str(img_path)).scaled(
                lbl.width(), lbl.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            lbl.setPixmap(pix)
        else:
            lbl.setText(f"[No image for {letter}]")

    def _refresh_ui(self):
        """Sync all static UI elements to the current session state."""
        session = self._session
        total   = session.total
        idx     = session.index

        if session.is_done():
            self._show_completion()
            return

        letter = session.current_target

        # letter & subtitle
        self._letter_lbl.setText(letter)
        self._letter_sub.setText("SIGN THIS LETTER")

        # reference image
        self._load_ref_image(letter)

        # progress & score
        self._progress_lbl.setText(f"Letter {idx + 1} of {total}")
        self._score_lbl.setText(f"Score: {session.score} / {total}")

        # next/skip button label
        is_last = (idx == total - 1)
        self._next_btn.setText("Finish →" if is_last else "Skip →")

        # clear feedback & hold bar
        self._feedback_lbl.setStyleSheet(_CLR_HIDDEN)
        self._feedback_lbl.setText("")
        self._set_hold_bar(0.0)

        # prediction line
        self._pred_lbl.setText("Waiting for hand...")

    def _set_hold_bar(self, progress: float):
        """progress: 0.0 – 1.0"""
        bar_max_w = self._hold_bg.width()
        fill_w    = int(bar_max_w * max(0.0, min(progress, 1.0)))
        geo       = self._hold_fill.geometry()
        self._hold_fill.setGeometry(geo.x(), geo.y(), fill_w, geo.height())

    def _show_feedback(self, correct: bool):
        if correct:
            self._feedback_lbl.setText("✓  Correct!")
            self._feedback_lbl.setStyleSheet(_CLR_CORRECT)
        else:
            self._feedback_lbl.setText("✗  Try again")
            self._feedback_lbl.setStyleSheet(_CLR_WRONG)

    def _show_completion(self):
        """Replace the lesson view with a simple completion summary."""
        self._cleanup_resources()
        session  = self._session
        pct      = session.score_percent()

        self._letter_lbl.setText("✓")
        self._letter_sub.setText("LESSON COMPLETE")
        self.video.hide()
        self._ref_img_lbl.clear()
        self._ref_img_lbl.setText(
            f"<span style='color:#e8f4f8; font-size:22px; font-weight:700;'>"
            f"Score: {session.score} / {session.total} ({pct}%)</span>"
        )
        self._ref_img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ref_img_lbl.setTextFormat(Qt.TextFormat.RichText)

        self._camera_lbl.setText("")
        self._feedback_lbl.setStyleSheet(_CLR_HIDDEN)
        self._pred_lbl.setText("")
        self._set_hold_bar(0.0)

        self._progress_lbl.setText(f"All {session.total} letters done!")
        self._score_lbl.setText(f"Final score: {pct}%")

        self._next_btn.setText("Back to Menu")
        self._next_btn.clicked.disconnect()
        self._next_btn.clicked.connect(self._on_back)

        try:
            from backend import auth_service, sync_service, content_service
            user = auth_service.get_current_user()
            if user and user.get("user_id"):
                import uuid
                uid = uuid.UUID(str(user["user_id"]))
                lesson_id = content_service.get_lesson_id("alphabet", self._lesson_number)
                if lesson_id:
                    sync_service.queue_lesson_progress(
                        user_id=uid,
                        lesson_id=lesson_id,
                        completion_percentage=float(pct),
                        status="Completed",
                        time_spent_seconds=60,
                    )
                    sync_service.process_pending_syncs(uid)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to record alphabet lesson progress: %s", exc)


    # ── camera tick ───────────────────────────────────────────────────────

    def _on_tick(self):
        if self._engine is None:
            return
        try:
            result = self._engine.read_frame()
        except Exception as error:
            import logging
            logging.getLogger(__name__).exception("Alphabet recognition failed")
            self._cleanup_resources()
            self._camera_failed(error)
            return
        if result is None:
            self._camera_misses += 1
            if self._camera_misses < 3:
                return
            self._cleanup_resources()
            self._camera_failed("Camera disconnected. Reopen the lesson to retry.")
            return

        # ── display camera feed ───────────────────────────────────────────
        self._camera_misses = 0
        self._camera_lbl.set_bgr_frame(result.annotated_bgr)

        # ── update camera status dot ──────────────────────────────────────
        self._set_cam_dot(True)

        # ── only process predictions while in WAITING state ───────────────
        if self._session.state != SessionState.WAITING:
            return

        # ── hand not detected ─────────────────────────────────────────────
        if not result.hand_detected or result.prediction is None:
            self._session._hold = 0
            self._pred_lbl.setText("No hand detected")
            self._set_hold_bar(0.0)
            return

        pred = result.prediction
        self._pred_lbl.setText(
            f"Seeing: {pred.label}   ({pred.confidence:.0%})"
        )

        # ── feed into session state machine ───────────────────────────────
        event = self._session.process_prediction(pred.label, pred.confidence)

        if event == Event.HOLDING:
            # update hold progress bar
            self._set_hold_bar(self._session.hold_progress)
            self._feedback_lbl.setText("Hold it…")
            self._feedback_lbl.setStyleSheet(_CLR_HOLDING)

        elif event == Event.CORRECT:
            self._set_hold_bar(1.0)
            self._show_feedback(correct=True)
            self._feedback_action = "advance"
            self._feedback_timer.start(1200)

        elif event == Event.WRONG:
            self._set_hold_bar(0.0)
            self._show_feedback(correct=False)
            self._feedback_action = "reset"
            self._feedback_timer.start(900)

        else:
            # NONE — correct sign not sustained yet, reset bar
            self._set_hold_bar(self._session.hold_progress)

    # ── transitions ───────────────────────────────────────────────────────

    def _on_feedback_timeout(self):
        if self._resources_closed:
            return
        action = self._feedback_action
        self._feedback_action = None
        if action == "advance":
            self._advance()
        elif action == "reset":
            self._session.reset_waiting()
            self._clear_feedback()

    def _advance(self):
        if self._resources_closed:
            return
        self._session.advance()
        self._refresh_ui()

    def _clear_feedback(self):
        self._feedback_lbl.setStyleSheet(_CLR_HIDDEN)
        self._feedback_lbl.setText("")
        self._set_hold_bar(0.0)

    def _on_skip(self):
        """Skip/next button — skip the current letter."""
        if self._session.is_done():
            return
        self._session.skip()
        self._refresh_ui()

    def _on_back(self):
        """Return to the main menu."""
        self.close()

    # ── Qt lifecycle ──────────────────────────────────────────────────────

    def _cleanup_resources(self):
        if self._resources_closed:
            return
        self._resources_closed = True
        self._cancel_camera_setup()
        self.loading.cancel()
        self.video.stop()
        self._timer.stop()
        self._feedback_timer.stop()
        self._feedback_action = None
        if self._engine is not None:
            self._engine.close()
            self._engine = None
        self._set_cam_dot(False)

    def hideEvent(self, event):
        self._cleanup_resources()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._cleanup_resources()
        self.lesson_finished.emit()
        event.accept()

    def resizeEvent(self, event):
        """Keep the loaded UI widget filling the window."""
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
        if hasattr(self, "_session") and not self._session.is_done():
            QTimer.singleShot(0, self._resize_reference)

    def _resize_reference(self):
        if not self._resources_closed and not self._session.is_done():
            self._load_ref_image(self._session.current_target)
