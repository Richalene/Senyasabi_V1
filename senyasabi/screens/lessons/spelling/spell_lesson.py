"""
Spell Lesson — fingerspell a word letter by letter using the alphabet model.

Spaces in the word are skipped automatically.
Layout mirrors alphabet_lesson.py: reference image left, camera right.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QFrame

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from screens.camera_access import LessonCameraMixin, alphabet_engine
from screens.camera_preview import RoundedCameraPreview
from screens.navigation import BackButton, install_page_menu
from backend.session_state import CameraPracticeSession, Event, SessionState

_UI_FILE  = _ROOT / "ui" / "designer" / "spell_lesson.ui"
_VRM_DIR  = _ROOT / "resources" / "VRM_SIGNS"

_CLR_CORRECT = ("color:#0f1117; background-color:#5ecf8a;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_WRONG   = ("color:#ffffff; background-color:#e05252;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HOLDING = ("color:#0f1117; background-color:#a87eed;"
                "border-radius:10px; padding:8px 20px; font-size:18px; font-weight:700;")
_CLR_HIDDEN  = "color:transparent; background-color:transparent;"

# Tile colours
_TILE_DONE    = "#5ecf8a"
_TILE_CURRENT = "#a87eed"
_TILE_PENDING = "#1a1f2e"
_TILE_SPACE   = "#0f1117"   # invisible for spaces


class SpellLessonWidget(LessonCameraMixin, QWidget):
    """
    Fingerspell a word using the alphabet model.

    Parameters
    ----------
    word : str
        The word to spell (e.g. "GOOD MORNING"). Spaces are skipped.
    category : str
        Category label shown in the title bar.

    Signals
    -------
    lesson_finished — emitted when done or back pressed
    """
    lesson_finished = Signal()

    def __init__(self, word: str, category: str = "",
                 parent: QWidget | None = None):
        super().__init__(parent)

        self._word     = word
        self._category = category
        # letters only — skip spaces
        self._letters: List[str] = [c for c in word.upper() if "A" <= c <= "Z"]

        # ── load UI ──────────────────────────────────────────────────────
        loader = QUiLoader()
        self._ui = loader.load(str(_UI_FILE), self)
        if self._ui is None:
            raise RuntimeError(f"Failed to load {_UI_FILE}")
        self._ui.setStyleSheet(self._ui.styleSheet() + (_ROOT / "resources/styles/lessons.qss").read_text())
        self.resize(self._ui.width(), self._ui.height())
        self._ui.resize(self.size())
        self.setWindowTitle(f"SenyaSabi — Spell: {word}")

        # ── widget refs ──────────────────────────────────────────────────
        self._title_lbl    : QLabel  = self._ui.findChild(QLabel,  "lessonTitle")
        self._progress_lbl : QLabel  = self._ui.findChild(QLabel,  "progressLabel")
        self._score_lbl    : QLabel  = self._ui.findChild(QLabel,  "scoreLabel")
        self._letter_lbl   : QLabel  = self._ui.findChild(QLabel,  "currentLetterLabel")
        self._letter_sub   : QLabel  = self._ui.findChild(QLabel,  "letterSubtitle")
        self._ref_img_lbl  : QLabel  = self._ui.findChild(QLabel,  "refImageLabel")
        self._camera_lbl = RoundedCameraPreview.replace(
            self._ui.findChild(QLabel, "cameraLabel")
        )
        self._cam_dot      : QLabel  = self._ui.findChild(QLabel,  "camStatusDot")
        self._feedback_lbl : QLabel  = self._ui.findChild(QLabel,  "feedbackLabel")
        self._pred_lbl     : QLabel  = self._ui.findChild(QLabel,  "predictionLabel")
        self._hold_bg      : QLabel  = self._ui.findChild(QLabel,  "holdBarBg")
        self._hold_fill    : QLabel  = self._ui.findChild(QLabel,  "holdBarFill")
        self._tiles_area   : QLabel  = self._ui.findChild(QLabel,  "tilesArea")
        self._skip_btn     : QPushButton = self._ui.findChild(QPushButton, "skipBtn")
        self._back_btn = BackButton.replace(self._ui.findChild(QPushButton, "backBtn"))
        self._back_btn.setGeometry(1138, 24, 52, 52)
        self._score_lbl.setGeometry(950, 24, 166, 28)
        install_page_menu(self, canvas_size=QSize(1306, 753))

        self._skip_btn.clicked.connect(self._on_skip)
        self._back_btn.clicked.connect(self._on_back)

        # ── word tile widgets (created once, colours updated each step) ──
        self._tile_labels: List[QLabel] = []
        self._build_tiles()

        # ── backend ──────────────────────────────────────────────────────
        self._engine = None
        self._set_cam_dot(False)
        self._resources_closed = False

        self._session = CameraPracticeSession(targets=self._letters)

        # ── timers ───────────────────────────────────────────────────────
        self._timer          = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_action = None
        self._feedback_timer.timeout.connect(self._on_feedback_timeout)

        # ── initial render ───────────────────────────────────────────────
        self._refresh_ui()
        self._init_camera(alphabet_engine)


    # ── tile row ─────────────────────────────────────────────────────────

    def _build_tiles(self):
        """Create one small QLabel per character in the word (inc. spaces)."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        for ch in self._word:
            lbl = QLabel(ch if ch != " " else "")
            if ch == " ":
                lbl.setFixedSize(12, 36)
                lbl.setStyleSheet(f"background: {_TILE_SPACE}; border-radius: 4px;")
            else:
                lbl.setFixedSize(36, 36)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet(
                    f"background: {_TILE_PENDING}; color: #ffffff;"
                    "font-size: 14px; font-weight: 700; border-radius: 6px;"
                )
                self._tile_labels.append(lbl)
            layout.addWidget(lbl)

        layout.addStretch()

        # Replace the placeholder QLabel's layout
        container = QFrame(self._tiles_area)
        container.setGeometry(0, 0,
                              self._tiles_area.width(),
                              self._tiles_area.height())
        container.setStyleSheet("background: transparent;")
        container.setLayout(layout)
        container.show()

    def _update_tiles(self, current_idx: int):
        for i, lbl in enumerate(self._tile_labels):
            if i < current_idx:
                lbl.setStyleSheet(
                    f"background: {_TILE_DONE}; color: #0f1117;"
                    "font-size: 14px; font-weight: 700; border-radius: 6px;"
                )
            elif i == current_idx:
                lbl.setStyleSheet(
                    f"background: {_TILE_CURRENT}; color: #ffffff;"
                    "font-size: 14px; font-weight: 700; border-radius: 6px;"
                )
            else:
                lbl.setStyleSheet(
                    f"background: {_TILE_PENDING}; color: #5a6080;"
                    "font-size: 14px; font-weight: 700; border-radius: 6px;"
                )

    # ── UI helpers ────────────────────────────────────────────────────────

    def _set_cam_dot(self, active: bool):
        color = "#5ecf8a" if active else "#e05252"
        self._cam_dot.setStyleSheet(f"background-color:{color}; border-radius:5px;")

    def _load_ref_image(self, letter: str):
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

        letter = session.current_target

        self._title_lbl.setText(
            f"SPELL MODE — {self._word}"
            + (f"  ·  {self._category}" if self._category else "")
        )
        self._letter_lbl.setText(letter)
        self._letter_sub.setText("SIGN THIS LETTER")
        self._load_ref_image(letter)
        self._progress_lbl.setText(f"Letter {idx + 1} of {total}")
        self._score_lbl.setText(f"Score: {session.score} / {total}")
        self._update_tiles(idx)

        is_last = (idx == total - 1)
        self._skip_btn.setText("Finish →" if is_last else "Skip letter →")

        self._clear_feedback()
        self._pred_lbl.setText("Waiting for hand...")

    def _show_completion(self):
        self._cleanup_resources()
        session = self._session
        pct     = session.score_percent()

        self._letter_lbl.setText("✓")
        self._letter_sub.setText("WORD COMPLETE")
        self._ref_img_lbl.clear()
        self._ref_img_lbl.setText(
            f"<span style='color:#e8f4f8; font-size:22px; font-weight:700;'>"
            f"{self._word}<br>Score: {session.score} / {session.total} ({pct}%)</span>"
        )
        self._ref_img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ref_img_lbl.setTextFormat(Qt.TextFormat.RichText)

        self._update_tiles(session.total)   # all green
        self._camera_lbl.setText("")
        self._clear_feedback()
        self._pred_lbl.setText("")
        self._set_hold_bar(0.0)
        self._progress_lbl.setText(f"All {session.total} letters done!")
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
            logging.getLogger(__name__).exception("Spelling recognition failed")
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

        self._camera_misses = 0
        self._camera_lbl.set_bgr_frame(result.annotated_bgr)
        self._set_cam_dot(True)

        if self._session.state != SessionState.WAITING:
            return

        if not result.hand_detected or result.prediction is None:
            self._session._hold = 0
            self._pred_lbl.setText("No hand detected")
            self._set_hold_bar(0.0)
            return

        pred = result.prediction
        self._pred_lbl.setText(f"Seeing: {pred.label}   ({pred.confidence:.0%})")

        event = self._session.process_prediction(pred.label, pred.confidence)

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
        self._session.skip()
        self._refresh_ui()

    def _on_back(self):
        self.close()

    # ── Qt lifecycle ──────────────────────────────────────────────────────

    def _cleanup_resources(self):
        if self._resources_closed:
            return
        self._resources_closed = True
        self._cancel_camera_setup()
        self.loading.cancel()
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
        super().resizeEvent(event)
        if hasattr(self, "_ui") and self._ui:
            self._ui.resize(self.size())
