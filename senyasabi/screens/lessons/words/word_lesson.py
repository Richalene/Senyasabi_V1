"""
Module word lesson with lazy category recognition and service-resolved video.
Missing trained artifacts leave browsing and navigation available.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.model_service import CategoryRecognitionEngine, _registry
from backend.content_service import get_signs_for_module
from backend.recognition_labels import normalize_label
from backend.session_state import CameraPracticeSession, Event, SessionState
from screens.camera_access import LessonCameraMixin, alphabet_engine
from screens.camera_preview import RoundedCameraPreview
from screens.media_player import SignVideoPlayer
from screens.navigation import BackButton, install_page_menu

_UI_FILE = _ROOT / "ui" / "designer" / "word_lesson.ui"

_CLR_CORRECT = ("color:#0f1117; background-color:#5ecf8a;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_WRONG   = ("color:#ffffff; background-color:#e05252;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HOLDING = ("color:#0f1117; background-color:#f0c040;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HIDDEN  = "color:transparent; background-color:transparent;"


class WordLessonWidget(LessonCameraMixin, QWidget):
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
        self.module_code = category.casefold()
        self._signs = {sign.label: sign for sign in get_signs_for_module(self.module_code)}

        # ── load UI ──────────────────────────────────────────────────────
        loader   = QUiLoader()
        self._ui = loader.load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")
        self._ui.setStyleSheet(self._ui.styleSheet() + (_ROOT / "resources/styles/lessons.qss").read_text())
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
        self._camera_lbl = RoundedCameraPreview.replace(
            self._ui.findChild(QLabel, "cameraLabel")
        )
        self._cam_dot      : QLabel      = self._ui.findChild(QLabel,      "camStatusDot")
        self._feedback_lbl : QLabel      = self._ui.findChild(QLabel,      "feedbackLabel")
        self._pred_lbl     : QLabel      = self._ui.findChild(QLabel,      "predictionLabel")
        self._hold_bg      : QLabel      = self._ui.findChild(QLabel,      "holdBarBg")
        self._hold_fill    : QLabel      = self._ui.findChild(QLabel,      "holdBarFill")
        self._skip_btn     : QPushButton = self._ui.findChild(QPushButton,  "skipBtn")
        self._back_btn = BackButton.replace(self._ui.findChild(QPushButton, "backBtn"))
        self._back_btn.setGeometry(1138, 24, 52, 52)
        self._score_lbl.setGeometry(950, 24, 166, 28)
        install_page_menu(self, canvas_size=QSize(1306, 753))

        self._skip_btn.clicked.connect(self._on_skip)
        self._back_btn.clicked.connect(self._on_back)
        self._ref_lbl.clear()
        self.video = SignVideoPlayer(self._ref_lbl)
        QVBoxLayout(self._ref_lbl).addWidget(self.video)

        # ── backend ──────────────────────────────────────────────────────
        self._engine = None
        self._set_cam_dot(False)
        self._resources_closed = False

        self._session = CameraPracticeSession(targets=self._words)

        # ── timers ───────────────────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_action = None
        self._feedback_timer.timeout.connect(self._on_feedback_timeout)

        # ── initial render ───────────────────────────────────────────────
        self._refresh_ui()
        self._init_camera(lambda: CategoryRecognitionEngine(self.module_code), lambda: _registry.status(self.module_code))


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
        if self._engine is not None:
            self._engine.reset_sequence()

        self._title_lbl.setText(
            f"WORD LESSON — {self._category.upper()}"
        )
        self._word_lbl.setWordWrap(True)
        self._word_lbl.setText(word)
        self._word_sub.setText("SIGN THIS WORD")
        sign = self._signs[word]
        self.video.set_sign(self.module_code, sign.sign_code)

        self._progress_lbl.setText(f"Word {idx + 1} of {total}")
        self._score_lbl.setText(f"Score: {session.score} / {total}")

        is_last = (idx == total - 1)
        self._skip_btn.setText("Finish →" if is_last else "Skip →")

        self._clear_feedback()
        self._pred_lbl.setText("Waiting for hand...")

    def _show_completion(self):
        self._cleanup_resources()
        session = self._session
        pct     = session.score_percent()

        self._word_lbl.setText("✓  Done!")
        self._word_sub.setText("LESSON COMPLETE")
        self.video.hide()
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
        if self._engine is None:
            return
        try:
            result = self._engine.read_frame()
        except Exception as error:
            import logging
            logging.getLogger(__name__).exception("Category recognition failed")
            self._cleanup_resources()
            self._camera_failed(error)
            return
        if result is None:
            self._camera_misses += 1
            if self._camera_misses < 3:
                return
            self._cleanup_resources()
            self._camera_failed(RuntimeError("Camera disconnected. Reopen the lesson to retry."))
            return

        self._camera_misses = 0
        self._camera_lbl.set_bgr_frame(result.annotated_bgr)
        self._set_cam_dot(True)

        if self._session.state != SessionState.WAITING:
            return

        if result.prediction is None:
            self._pred_lbl.setText(f"Collecting gesture: {self._engine.buffered_frames}/24 frames")
            self._session._hold = 0
            self._set_hold_bar(0.0)
            return
        if not result.hand_detected:
            self._pred_lbl.setText("No hand detected")
            self._session._hold = 0
            self._set_hold_bar(0.0)
            return

        pred  = result.prediction
        self._pred_lbl.setText(
            f"Seeing: {pred.label}   ({pred.confidence:.0%})"
        )

        target = self._signs[self._session.current_target]
        label = target.label if normalize_label(pred.label) == normalize_label(target.recognition_label) else ""
        event = self._session.process_prediction(label, pred.confidence)

        if event == Event.HOLDING:
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

    def _on_skip(self):
        if self._session.is_done():
            return
        self._feedback_timer.stop()
        self._feedback_action = None
        self._session.skip()
        self._refresh_ui()

    def _on_back(self):
        self.close()

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

    # ── Qt lifecycle ──────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._cleanup_resources()
        self.lesson_finished.emit()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
