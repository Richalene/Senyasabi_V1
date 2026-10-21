"""
FSL Word Lesson widget redesigned with the modern layout matching Figma.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from screens.camera_access import LessonCameraMixin
from screens.media_player import SignVideoPlayer
from screens.startup import FittedForm
from screens.lessons.lesson_ui_components import ModernLessonLayout
from backend.session_state import CameraPracticeSession, Event, SessionState
from backend.content_service import get_signs_for_module
from backend.model_service import CategoryRecognitionEngine, _registry

_VRM_DIR = _ROOT / "resources" / "VRM_SIGNS"


class WordLessonWidget(LessonCameraMixin, QWidget):
    lesson_finished = Signal()

    def __init__(
        self,
        module_code: str | list = "greeting",
        parent_or_code: QWidget | str | None = None,
        parent: QWidget | None = None,
    ):
        # Handle backwards-compatible calls:
        # 1) WordLessonWidget("greeting")
        # 2) WordLessonWidget(words_list, "greeting")
        actual_parent = parent
        if isinstance(parent_or_code, str):
            actual_module = parent_or_code
        elif isinstance(module_code, str):
            actual_module = module_code
            if isinstance(parent_or_code, QWidget):
                actual_parent = parent_or_code
        else:
            actual_module = "greeting"

        super().__init__(actual_parent)
        self.resize(1920, 1080)
        self.module_code = actual_module.casefold()
        self.setWindowTitle(f"SenyaSabi — {self.module_code.title()} Words")

        self.signs = get_signs_for_module(self.module_code)
        self._targets = [s.sign_code.upper() for s in self.signs]

        self.layout_comp = ModernLessonLayout(self)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.layout_comp)

        # Wire UI
        self.layout_comp.next_clicked.connect(self._on_skip)
        self.layout_comp.play_pause_clicked.connect(self._toggle_pause)
        self.layout_comp.replay_clicked.connect(self._replay)
        self.layout_comp.cam_toggle_clicked.connect(self._toggle_camera)
        self.layout_comp.back_requested.connect(self._on_back)
        self.layout_comp.close_requested.connect(self._on_back)

        self._camera_lbl = self.layout_comp.camera
        self._is_paused = False

        # Embedded SignVideoPlayer on avatar card
        self.video = SignVideoPlayer(self.layout_comp.avatar_card)
        v_layout = QVBoxLayout(self.layout_comp.avatar_card)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.addWidget(self.video)
        self.video.hide()

        # Engine & Session
        self._engine = None
        self._resources_closed = False
        self._session = CameraPracticeSession(targets=self._targets)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_action = None
        self._feedback_timer.timeout.connect(self._on_feedback_timeout)

        self._init_camera(lambda: CategoryRecognitionEngine(self.module_code),
                           lambda: _registry.status(self.module_code))
        self._refresh_ui()

        self._fitted_form = FittedForm(self)

    def _camera_ready(self, engine):
        super()._camera_ready(engine)
        if not self._is_paused and not self._session.is_done():
            self._load_ref_media(self._session.current_target)

    def _toggle_pause(self):
        if self._session.is_done():
            return
        self._is_paused = not self._is_paused
        self.layout_comp.avatar_card.set_paused(self._is_paused)
        if self._is_paused:
            self._timer.stop()
            self.layout_comp.btn_pause.set_kind("play")
            self.video.pause()
        else:
            self._timer.start()
            self.layout_comp.btn_pause.set_kind("pause")
            self.video.play()

    def _replay(self):
        if self._session.is_done() or self._is_paused:
            return
        if self.video.isVisible():
            self.video.play()
        else:
            sign_code = self._session.current_target
            self._load_ref_media(sign_code)

    def _toggle_camera(self):
        if self._engine is None:
            self.start_camera(force=True)
            self.layout_comp.set_camera_active(True)
        else:
            self._cleanup_resources()
            self.layout_comp.set_camera_active(False)
            self._camera_lbl.clear()
            self._camera_lbl.setText("Camera is off. Click to turn on.")

    def _load_ref_media(self, sign_code: str):
        self.video.set_sign(self.module_code, sign_code.lower())
        if self._engine is None or self.loading.busy:
            # Keep video invisible until camera / recognition finishes loading
            self.video.hide()
            return
        self.video.setVisible(self.video.media.available)
        if self.video.media.available:
            self.layout_comp.avatar_card.set_sign_pixmap(QPixmap())
            self.video.play()
            return
        img_path = _VRM_DIR / f"{sign_code.upper()}.png"
        if img_path.exists():
            self.layout_comp.avatar_card.set_sign_pixmap(QPixmap(str(img_path)))

    def _refresh_ui(self):
        session = self._session
        total = session.total
        idx = session.index

        if session.is_done():
            self._show_completion()
            return

        sign_code = session.current_target
        self._load_ref_media(sign_code)

        self.layout_comp.feedback_overlay.hide()
        self.layout_comp.btn_next.set_green(False)
        self.layout_comp.avatar_card.set_paused(False)
        self.layout_comp.btn_pause.set_kind("pause")
        self._is_paused = False

    def _show_completion(self):
        self._cleanup_resources()
        pct = self._session.score_percent()
        self.video.hide()
        self.layout_comp.feedback_overlay.show_success(
            accuracy_pct=pct,
            message="Module Complete! You are a Natural!"
        )
        self.layout_comp.btn_next.set_green(True)

        try:
            from backend import auth_service, sync_service, content_service
            user = auth_service.get_current_user()
            if user:
                content_service.update_lesson_progress(
                    user["user_id"],
                    "word",
                    self.module_code,
                    completed=True,
                    score=pct,
                )
        except Exception:
            pass

    def _on_tick(self):
        if self._engine is None or self._is_paused:
            return
        try:
            result = self._engine.read_frame()
        except Exception as error:
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
        self._camera_lbl.set_bgr_frame(result.annotated_bgr if result.annotated_bgr is not None else result.frame_bgr)

        if self._feedback_action is not None:
            return

        label = result.prediction.label if result.prediction else None
        confidence = result.prediction.confidence if result.prediction else 0.0

        event = self._session.process_prediction(label, confidence)

        if event == Event.CORRECT:
            pct = int(confidence * 100) if confidence > 0 else 98
            self.layout_comp.feedback_overlay.show_success(
                accuracy_pct=pct,
                message="You are a Natural!"
            )
            self.layout_comp.btn_next.set_green(True)
            self._feedback_action = "advance"
            self._feedback_timer.start(1400)

        elif event == Event.WRONG:
            pct = int(confidence * 100) if confidence > 0 else 28
            self.layout_comp.feedback_overlay.show_retry(
                accuracy_pct=pct,
                message="Let's Try Again"
            )
            self._feedback_action = "reset"
            self._feedback_timer.start(1200)

    def _on_feedback_timeout(self):
        if self._resources_closed:
            return
        action = self._feedback_action
        self._feedback_action = None
        if action == "advance":
            self._advance()
        elif action == "reset":
            self._session.reset_waiting()
            self.layout_comp.feedback_overlay.hide()

    def _advance(self):
        if self._resources_closed:
            return
        self._session.advance()
        self._refresh_ui()

    def _on_skip(self):
        if self._session.is_done():
            self._on_back()
            return
        self._session.skip()
        self._refresh_ui()

    def _on_back(self):
        from screens.dialogs import WaitConfirmDialog
        dialog = WaitConfirmDialog(mode="lesson", parent=self)
        if dialog.exec() == WaitConfirmDialog.DialogCode.Accepted:
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

    def hideEvent(self, event):
        self._cleanup_resources()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._cleanup_resources()
        self.lesson_finished.emit()
        event.accept()
