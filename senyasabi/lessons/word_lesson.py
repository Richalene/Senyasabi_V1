"""
Word Lesson — practice signing 105 words using the words model.
Same camera/session flow as alphabet_lesson.py but mode="words".
Reference image panel shows a placeholder until videos are added.
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
from PySide6.QtWidgets import QWidget, QLabel, QPushButton

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.recognition_engine import SignRecognitionEngine
from backend.session_state import CameraPracticeSession, Event, SessionState

_UI_FILE = _HERE / "word_lesson.ui"

_CLR_CORRECT = ("color:#0f1117; background-color:#5ecf8a;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_WRONG   = ("color:#ffffff; background-color:#e05252;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HOLDING = ("color:#0f1117; background-color:#f0c040;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HIDDEN  = "color:transparent; background-color:transparent;"


def _bgr_to_qpixmap(frame_bgr: np.ndarray, w: int, h: int) -> QPixmap:
    rgb  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    qimg = QImage(rgb.data, rgb.shape[1], rgb.shape[0],
                  rgb.strides[0], QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg).scaled(
        w, h,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


class WordLessonWidget(QWidget):
    """
    Practice signing a list of words with the words model.

    Parameters
    ----------
    words    : list of word strings (labels exactly as in 105labels.json)
    category : displayed in the title bar

    Signals
    -------
    lesson_finished
    """
    lesson_finished = Signal()

    def __init__(self, words: List[str], category: str = "",
                 parent: QWidget | None = None):
        super().__init__(parent)

        self._words    = words
        self._category = category

        # ── load UI ──────────────────────────────────────────────────────
        loader   = QUiLoader()
        self._ui = loader.load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")
        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle(f"SenyaSabi — {category}")

        # ── widget refs ──────────────────────────────────────────────────
        self._title_lbl    : QLabel      = self._ui.findChild(QLabel,      "lessonTitle")
        self._progress_lbl : QLabel      = self._ui.findChild(QLabel,      "progressLabel")
        self._score_lbl    : QLabel      = self._ui.findChild(QLabel,      "scoreLabel")
        self._word_lbl     : QLabel      = self._ui.findChild(QLabel,      "wordDisplay")
        self._word_sub     : QLabel      = self._ui.findChild(QLabel,      "wordSubtitle")
        self._ref_lbl      : QLabel      = self._ui.findChild(QLabel,      "refImageLabel")
        self._camera_lbl   : QLabel      = self._ui.findChild(QLabel,      "cameraLabel")
        self._cam_dot      : QLabel      = self._ui.findChild(QLabel,      "camStatusDot")
        self._feedback_lbl : QLabel      = self._ui.findChild(QLabel,      "feedbackLabel")
        self._pred_lbl     : QLabel      = self._ui.findChild(QLabel,      "predictionLabel")
        self._hold_bg      : QLabel      = self._ui.findChild(QLabel,      "holdBarBg")
        self._hold_fill    : QLabel      = self._ui.findChild(QLabel,      "holdBarFill")
        self._skip_btn     : QPushButton = self._ui.findChild(QPushButton,  "skipBtn")
        self._back_btn     : QPushButton = self._ui.findChild(QPushButton,  "backBtn")

        self._skip_btn.clicked.connect(self._on_skip)
        self._back_btn.clicked.connect(self._on_back)

        # ── backend ──────────────────────────────────────────────────────
        self._engine  = SignRecognitionEngine(mode="words")
        cam_ok        = self._engine.open_camera()
        self._set_cam_dot(cam_ok)

        self._session = CameraPracticeSession(targets=self._words)

        # ── timers ───────────────────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)

        # ── initial render ───────────────────────────────────────────────
        self._refresh_ui()

    # ── UI helpers ────────────────────────────────────────────────────────

    def _set_cam_dot(self, active: bool):
        color = "#5ecf8a" if active else "#e05252"
        self._cam_dot.setStyleSheet(
            f"background-color:{color}; border-radius:5px;"
        )

    def _set_hold_bar(self, progress: float):
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

    def _clear_feedback(self):
        self._feedback_lbl.setStyleSheet(_CLR_HIDDEN)
        self._feedback_lbl.setText("")
        self._set_hold_bar(0.0)

    def _refresh_ui(self):
        session = self._session
        total   = session.total
        idx     = session.index

        if session.is_done():
            self._show_completion()
            return

        word = session.current_target

        self._title_lbl.setText(
            f"WORD LESSON — {self._category.upper()}"
        )
        self._word_lbl.setText(word)
        self._word_sub.setText("SIGN THIS WORD")
        self._ref_lbl.setText("📹  Video coming soon")

        self._progress_lbl.setText(f"Word {idx + 1} of {total}")
        self._score_lbl.setText(f"Score: {session.score} / {total}")

        is_last = (idx == total - 1)
        self._skip_btn.setText("Finish →" if is_last else "Skip →")

        self._clear_feedback()
        self._pred_lbl.setText("Waiting for hand...")

    def _show_completion(self):
        self._timer.stop()
        session = self._session
        pct     = session.score_percent()

        self._word_lbl.setText("✓  Done!")
        self._word_sub.setText("LESSON COMPLETE")
        self._ref_lbl.setText(
            f"<span style='color:#e8f4f8; font-size:20px; font-weight:700;'>"
            f"{self._category}<br>"
            f"Score: {session.score} / {session.total} ({pct}%)</span>"
        )
        self._ref_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ref_lbl.setTextFormat(Qt.TextFormat.RichText)

        self._camera_lbl.setText("")
        self._clear_feedback()
        self._pred_lbl.setText("")
        self._progress_lbl.setText(f"All {session.total} words done!")
        self._score_lbl.setText(f"Final: {pct}%")

        self._skip_btn.setText("Back")
        self._skip_btn.clicked.disconnect()
        self._skip_btn.clicked.connect(self._on_back)

    # ── camera tick ───────────────────────────────────────────────────────

    def _on_tick(self):
        result = self._engine.read_frame()
        if result is None:
            return

        lbl = self._camera_lbl
        pix = _bgr_to_qpixmap(result.annotated_bgr, lbl.width(), lbl.height())
        lbl.setPixmap(pix)
        self._set_cam_dot(True)

        if self._session.state != SessionState.WAITING:
            return

        if not result.hand_detected:
            self._pred_lbl.setText("No hand detected")
            self._set_hold_bar(0.0)
            return

        pred  = result.prediction
        self._pred_lbl.setText(
            f"Seeing: {pred.label}   ({pred.confidence:.0%})"
        )

        event = self._session.process_prediction(pred.label, pred.confidence)

        if event == Event.HOLDING:
            self._set_hold_bar(self._session.hold_progress)
            self._feedback_lbl.setText("Hold it…")
            self._feedback_lbl.setStyleSheet(_CLR_HOLDING)

        elif event == Event.CORRECT:
            self._set_hold_bar(1.0)
            self._show_feedback(correct=True)
            self._feedback_timer.singleShot(1200, self._advance)

        elif event == Event.WRONG:
            self._set_hold_bar(0.0)
            self._show_feedback(correct=False)
            self._feedback_timer.singleShot(
                900,
                lambda: (self._session.reset_waiting(), self._clear_feedback())
            )
        else:
            self._set_hold_bar(self._session.hold_progress)

    # ── transitions ───────────────────────────────────────────────────────

    def _advance(self):
        self._session.advance()
        self._refresh_ui()

    def _on_skip(self):
        if self._session.is_done():
            return
        self._session.skip()
        self._refresh_ui()

    def _on_back(self):
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
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
