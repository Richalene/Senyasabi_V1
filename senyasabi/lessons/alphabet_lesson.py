"""
FSL Alphabet Lesson widget.

Wires together:
  - alphabet_lesson.ui  (Qt Designer layout)
  - SignRecognitionEngine(mode="alphabet")  (camera + model)
  - CameraPracticeSession  (state machine)

Usage (from main.py or any parent widget):

    from lessons.alphabet_lesson import AlphabetLessonWidget

    LESSON_LETTERS = {
        1: list("ABCDEF"),
        2: list("GHIJKL"),
        3: list("MNOPQR"),
        4: list("STUVWX"),
        5: list("YZ"),
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

import cv2
import numpy as np

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget, QLabel

# ── path gymnastics so imports work whether run directly or as a package ──
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent  # senyasabi/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.recognition_engine import SignRecognitionEngine
from backend.session_state import CameraPracticeSession, Event, SessionState

# ── lesson definitions ────────────────────────────────────────────────────
LESSON_LETTERS: dict[int, List[str]] = {
    1: list("ABCDEF"),
    2: list("GHIJKL"),
    3: list("MNOPQR"),
    4: list("STUVWX"),
    5: list("YZ"),
}

_UI_FILE = _HERE / "alphabet_lesson.ui"
_VRM_DIR = _ROOT / "resources" / "VRM_SIGNS"

# ── colour constants ──────────────────────────────────────────────────────
_CLR_CORRECT  = ("color:#0f1117; background-color:#5ecf8a;"
                 "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_WRONG    = ("color:#ffffff; background-color:#e05252;"
                 "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HOLDING  = ("color:#0f1117; background-color:#f0c040;"
                 "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HIDDEN   = "color:transparent; background-color:transparent;"


def _bgr_to_qpixmap(frame_bgr: np.ndarray, w: int, h: int) -> QPixmap:
    """Convert an OpenCV BGR frame to a scaled QPixmap."""
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0],
                  rgb.strides[0], QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg).scaled(
        w, h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


class AlphabetLessonWidget(QWidget):
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
        self._camera_lbl:     QLabel = self._ui.findChild(QLabel,      "cameraLabel")
        self._cam_dot:        QLabel = self._ui.findChild(QLabel,      "camStatusDot")
        self._feedback_lbl:   QLabel = self._ui.findChild(QLabel,      "feedbackLabel")
        self._pred_lbl:       QLabel = self._ui.findChild(QLabel,      "predictionLabel")
        self._hold_bg:        QLabel = self._ui.findChild(QLabel,      "holdBarBg")
        self._hold_fill:      QLabel = self._ui.findChild(QLabel,      "holdBarFill")

        from PySide6.QtWidgets import QPushButton
        self._next_btn = self._ui.findChild(QPushButton, "nextBtn")
        self._back_btn = self._ui.findChild(QPushButton, "backBtn")

        # ── connect buttons ───────────────────────────────────────────────
        self._next_btn.clicked.connect(self._on_skip)
        self._back_btn.clicked.connect(self._on_back)

        # ── title label ───────────────────────────────────────────────────
        self._title_lbl.setText(f"FSL ALPHABET — LESSON {lesson_number}")

        # ── backend: recognition engine ───────────────────────────────────
        self._engine = SignRecognitionEngine(mode="alphabet")
        cam_ok = self._engine.open_camera()
        self._set_cam_dot(cam_ok)

        # ── backend: session state ────────────────────────────────────────
        self._session = CameraPracticeSession(targets=self._letters)

        # ── camera timer (≈ 30 fps) ───────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

        # ── feedback auto-clear timer ─────────────────────────────────────
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)

        # ── initial render ────────────────────────────────────────────────
        self._refresh_ui()

    # ── UI helpers ────────────────────────────────────────────────────────

    def _set_cam_dot(self, active: bool):
        color = "#5ecf8a" if active else "#e05252"
        self._cam_dot.setStyleSheet(
            f"background-color:{color}; border-radius:5px;"
        )

    def _load_ref_image(self, letter: str):
        """Load VRM reference image for the given letter into refImageLabel."""
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
        self._timer.stop()
        session  = self._session
        pct      = session.score_percent()

        self._letter_lbl.setText("✓")
        self._letter_sub.setText("LESSON COMPLETE")
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

    # ── camera tick ───────────────────────────────────────────────────────

    def _on_tick(self):
        result = self._engine.read_frame()
        if result is None:
            return

        # ── display camera feed ───────────────────────────────────────────
        lbl = self._camera_lbl
        pix = _bgr_to_qpixmap(result.annotated_bgr, lbl.width(), lbl.height())
        lbl.setPixmap(pix)

        # ── update camera status dot ──────────────────────────────────────
        self._set_cam_dot(True)

        # ── only process predictions while in WAITING state ───────────────
        if self._session.state != SessionState.WAITING:
            return

        # ── hand not detected ─────────────────────────────────────────────
        if not result.hand_detected:
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
            # advance after 1.2 s
            self._feedback_timer.singleShot(1200, self._advance)

        elif event == Event.WRONG:
            self._set_hold_bar(0.0)
            self._show_feedback(correct=False)
            # reset waiting after 900 ms
            self._feedback_timer.singleShot(
                900,
                lambda: (self._session.reset_waiting(),
                         self._clear_feedback())
            )

        else:
            # NONE — correct sign not sustained yet, reset bar
            self._set_hold_bar(self._session.hold_progress)

    # ── transitions ───────────────────────────────────────────────────────

    def _advance(self):
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
        self._timer.stop()
        self._engine.close()
        self.lesson_finished.emit()
        self.close()

    # ── Qt lifecycle ──────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._timer.stop()
        self._engine.close()
        self.lesson_finished.emit()
        event.accept()

    def resizeEvent(self, event):
        """Keep the loaded UI widget filling the window."""
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
