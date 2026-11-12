"""
FSL Alphabet Lesson widget redesigned with the modern layout matching Figma:
- Foliage background (#C2D076)
- Top header with SenyaSabi logo, circular back button, and close '✕'
- Rounded cream container card
- Left amber card with avatar sign and pause overlay
- Vertical center controls: Next, Pause/Play, Replay, Camera toggle
- Right rounded camera feed with fill_crop=True and success feedback overlay
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

from screens.camera_access import LessonCameraMixin, alphabet_engine
from screens.media_player import SignVideoPlayer
from screens.startup import FittedForm
from screens.lessons.lesson_ui_components import ModernLessonLayout
from backend.session_state import CameraPracticeSession, Event, SessionState

import logging
import threading
from shiboken6 import isValid
from backend.content_service import get_synced_lessons

LESSON_LETTERS: dict[int, List[str]] = {
    1: list("ABCDEF"),
    2: list("GHIJKL"),
    3: list("MNOPQR"),
    4: list("STUVWXYZ"),
}

_VRM_DIR = _ROOT / "resources" / "VRM_SIGNS"
log = logging.getLogger(__name__)

class AlphabetLessonWidget(LessonCameraMixin, QWidget):
    lesson_finished = Signal()
    _images_ready = Signal(object)

    def __init__(
        self,
        letters: List[str] | None = None,
        lesson_number: int = 1,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.setStyleSheet('background-color: #C2D076;')
        self.setWindowTitle(f"SenyaSabi — Alphabet Lesson {lesson_number}")

        lessons = get_synced_lessons("alphabet")
        entry = next((l for l in lessons if l["number"] == lesson_number), None)
        if letters is None:
            words = entry.get("words") if entry else None
            letters = [w.upper() for w in words] if isinstance(words, (list, tuple)) else list("ABCDEF")
        self._letters = letters
        self._lesson_number = lesson_number
        self._lesson_id = entry["lesson_id"] if entry else None
        self._remote_images = {}

        self.layout_comp = ModernLessonLayout(self)
        self.layout_comp.setGeometry(0, 0, 1920, 1080)

        # Wire UI components
        self.layout_comp.next_clicked.connect(self._on_skip)
        self.layout_comp.play_pause_clicked.connect(self._toggle_pause)
        self.layout_comp.replay_clicked.connect(self._replay)
        self.layout_comp.cam_toggle_clicked.connect(self._toggle_camera)
        self.layout_comp.back_requested.connect(self._on_back)
        self.layout_comp.close_requested.connect(self._on_back)

        self._resources_closed = False
        self._camera_lbl = self.layout_comp.camera
        self._camera_lbl.setObjectName("cameraLabel")
        self._back_btn = self.layout_comp.btn_back
        self._ui = self.layout_comp
        self._is_paused = False

        # Embedded SignVideoPlayer on the avatar card
        self.video = SignVideoPlayer(self.layout_comp.avatar_card)
        v_layout = QVBoxLayout(self.layout_comp.avatar_card)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.addWidget(self.video)
        self.video.hide()

        # Engine & Session
        self._engine = None
        self._camera_misses = 0
        self._resources_closed = False
        self._session = CameraPracticeSession(targets=self._letters, hold_frames=6, grace_frames=6)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._on_tick)

        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_action = None
        self._feedback_timer.timeout.connect(self._on_feedback_timeout)

        self._refresh_ui()
        self._init_camera(alphabet_engine)

        self._images_ready.connect(self._on_images_ready)
        self._prefetch_images()

        self._fitted_form = FittedForm(self)

    def _toggle_pause(self):
        if self._session.is_done():
            return
        self._is_paused = not self._is_paused
        self.layout_comp.avatar_card.set_paused(self._is_paused)
        if self._is_paused:
            self.layout_comp.btn_pause.set_kind("play")
            self.video.pause()
        else:
            self.layout_comp.btn_pause.set_kind("pause")
            self.video.resume()

    def _replay(self):
        if self._session.is_done():
            return
        self.video.replay()
        self._is_paused = False
        self.layout_comp.avatar_card.set_paused(False)
        self.layout_comp.btn_pause.set_kind("pause")

    def _toggle_camera(self):
        if self._engine is None:
            self.start_camera(force=True)
            self.layout_comp.set_camera_active(True)
        else:
            self._cleanup_resources()
            self.layout_comp.set_camera_active(False)
            self._camera_lbl.clear()
            self._camera_lbl.setText("Camera is off. Click to turn on.")

    def _camera_ready(self, engine):
        super()._camera_ready(engine)
        if not self._is_paused and not self._session.is_done():
            target = self._session.current_target
            if target is not None:
                self._load_ref_image(target)

    def _load_ref_image(self, letter: str):
        self.video.set_sign("alphabet", letter.lower())
        media = self.video.media
        media_available = media is not None and media.available
        self.video.setVisible(media_available)
        if media_available:
            self.layout_comp.avatar_card.set_sign_pixmap(QPixmap())
            if not self._is_paused:
                self.video.play()
            return
        self._show_still(letter)

    def _show_still(self, letter: str):
        """Supabase lesson_media image first, bundled VRM png as the offline fallback."""
        path = self._remote_images.get(letter.upper())
        if path is None or not path.is_file():
            path = _VRM_DIR / f"{letter.upper()}.png"
        self.layout_comp.avatar_card.set_sign_pixmap(
            QPixmap(str(path)) if path.is_file() else QPixmap())

    def _prefetch_images(self):
        lesson_id = self._lesson_id
        if lesson_id is None:
            return

        def work():
            try:
                from backend.media_service import fetch_lesson_images
                paths = fetch_lesson_images(lesson_id)
                print(paths)
            except Exception as error:
                log.warning("Lesson images unavailable: %s", error)
                return
            if paths and isValid(self):
                try:
                    self._images_ready.emit(paths)   # queued to the UI thread
                except RuntimeError:
                    pass

        threading.Thread(target=work, name="alphabet-images", daemon=True).start()

    def _on_images_ready(self, paths):
        self._remote_images = {k.upper(): Path(v) for k, v in paths.items()}
        if self._resources_closed or self._session.is_done():
            return
        if not (self.video.media and self.video.media.available):
            letter = self._session.current_target
            if letter is not None:
                self._show_still(letter)

    def _refresh_ui(self):
        session = self._session
        total = session.total
        idx = session.index

        if session.is_done():
            self._show_completion()
            return

        letter = session.current_target or ""
        
        self.layout_comp.set_target(
            f"Letter {letter.upper() if letter else '?'}",
            category=f"ALPHABET LESSON {self._lesson_number} • SIGN THIS LETTER",
            progress=f"Letter {idx + 1} of {total}"
        )
        self.layout_comp.set_prediction("Waiting for hand...", status="waiting")
        
        if letter:
            self._load_ref_image(letter)

        self.layout_comp.feedback_overlay.hide()
        if hasattr(self.layout_comp, "results_widget") and self.layout_comp.results_widget is not None:
            self.layout_comp.results_widget.hide()
            self.layout_comp.card.show()
        self.layout_comp.btn_next.set_green(False)
        self.layout_comp.avatar_card.set_paused(False)
        self.layout_comp.btn_pause.set_kind("pause")
        self._is_paused = False

    def _show_completion(self):
        self._timer.stop()
        self._feedback_timer.stop()
        self._feedback_action = None
        if hasattr(self, "video") and self.video is not None:
            try:
                self.video.hide()
            except Exception:
                pass
        pct = self._session.accuracy_percent() if hasattr(self._session, "accuracy_percent") else self._session.score_percent()
        self.layout_comp.feedback_overlay.show_success(
            accuracy_pct=pct,
            message="Lesson Complete! You are a Natural!"
        )
        self.layout_comp.btn_next.set_green(True)
        if hasattr(self.layout_comp, "results_widget") and self.layout_comp.results_widget is not None:
            self.layout_comp.card.hide()
            self.layout_comp.results_widget.show_results(
                lesson_name=f"FSL Alphabet — Lesson {self._lesson_number}",
                accuracy_pct=pct,
                completed_count=self._session.score,
                total_count=self._session.total,
                has_next_lesson=self._lesson_number < max(LESSON_LETTERS),
            )

        try:
            from backend import auth_service, sync_service, content_service
            user = auth_service.get_current_user()
            if user:
                lesson_id = content_service.get_lesson_id("alphabet", self._lesson_number)
                if lesson_id is not None:
                    sync_service.queue_lesson_progress(
                        user_id=user["user_id"],
                        lesson_id=lesson_id,
                        completion_percentage=float(pct),
                        status="Completed",
                        time_spent_seconds=0,
                    )
        except Exception:
            pass

    def _on_tick(self):
        if self._engine is None or self._resources_closed:
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
        display_bgr = result.annotated_bgr if result.annotated_bgr is not None else result.frame_bgr
        self._camera_lbl.set_bgr_frame(display_bgr)

        # Recognition evaluation
        if self._feedback_action is not None:
            return

        if not result.hand_detected:
            self.layout_comp.set_prediction("Waiting for hand...", status="waiting")
            return

        target = self._session.current_target
        if not target:
            return

        import re
        def _clean(s):
            return re.sub(r"[^A-Z0-9]", "", str(s).upper())

        target_clean = _clean(target)
        probs = getattr(result.prediction, "probabilities", None) or {}
        argmax_label = result.prediction.label if result.prediction else None
        argmax_conf = result.prediction.confidence if result.prediction else 0.0

        target_prob = 0.0
        other_max_prob = 0.0
        for p_lbl, p_val in probs.items():
            if _clean(p_lbl) == target_clean:
                target_prob = max(target_prob, float(p_val))
            else:
                other_max_prob = max(other_max_prob, float(p_val))

        if not probs and argmax_label:
            if _clean(argmax_label) == target_clean:
                target_prob = argmax_conf
            else:
                other_max_prob = argmax_conf

        target_upper = target.upper()

        if target_upper in ("Z", "J"):
            if target_prob >= other_max_prob and target_prob >= 0.40:
                accuracy_pct = min(100, int(75 + min(target_prob, 0.90) * 25))
                is_match = True
            elif other_max_prob > 0 and (target_prob / other_max_prob) >= 0.70 and target_prob >= 0.35:
                ratio = target_prob / other_max_prob
                accuracy_pct = min(100, int(70 + (ratio - 0.70) / 0.30 * 30))
                is_match = True
            else:
                accuracy_pct = 25
                is_match = False
        elif target_prob >= other_max_prob and target_prob > 0.03:
            accuracy_pct = min(100, 85 + int(min(target_prob, 0.70) / 0.70 * 15))
            is_match = True
        elif other_max_prob > 0 and (target_prob / other_max_prob) >= 0.35 and target_prob >= 0.08:
            ratio = target_prob / other_max_prob
            accuracy_pct = min(100, int(70 + (ratio - 0.35) / 0.65 * 30))
            is_match = True
        else:
            ratio = (target_prob / other_max_prob) if other_max_prob > 0 else 0.0
            accuracy_pct = max(15, min(55, int(ratio * 55)))
            is_match = False

        eval_label = target if is_match else "__NO_MATCH__"
        eval_conf = accuracy_pct / 100.0
        event = self._session.process_prediction(eval_label, eval_conf)

        if event == Event.HOLDING:
            pct_progress = int(self._session.hold_progress * 100)
            if target_upper in ("Z", "J"):
                status_text = f"Trace the '{target_upper}' in the air! ({accuracy_pct}%)"
            else:
                status_text = f"Hold it! {pct_progress}% ({accuracy_pct}%)"
            self.layout_comp.set_prediction(
                status_text,
                status="holding"
            )
        elif event == Event.CORRECT:
            self.layout_comp.set_prediction(
                f"Correct! Letter {target_upper} ({accuracy_pct}%)",
                status="correct"
            )
            self.layout_comp.feedback_overlay.show_success(
                accuracy_pct=accuracy_pct,
                message="You are a Natural!"
            )
            self.layout_comp.btn_next.set_green(True)
            self._feedback_action = "advance"
            feedback_delay = 2200 if target_upper in ("Z", "J") else 1400
            self._feedback_timer.start(feedback_delay)
        else:
            if is_match:
                self.layout_comp.set_prediction(
                    f"Signing: Letter {target_upper} ({accuracy_pct}%)",
                    status="holding"
                )
            else:
                self.layout_comp.set_prediction(
                    f"Sign: Letter {target_upper} ({accuracy_pct}%)",
                    status="waiting"
                )

    def _on_feedback_timeout(self):
        try:
            if self._resources_closed:
                return
            action = self._feedback_action
            self._feedback_action = None
            if action == "advance":
                self._advance()
            elif action == "reset":
                self._session.reset_waiting()
                self.layout_comp.feedback_overlay.hide()
        except Exception:
            pass

    def _advance(self):
        try:
            if self._resources_closed:
                return
            self._session.advance()
            self._refresh_ui()
        except Exception:
            pass

    def _on_skip(self):
        if self._session.is_done():
            self._on_back()
            return
        self._session.skip()
        self._refresh_ui()

    def _on_back(self):
        if self._engine is not None and not self._session.is_done():
            was_paused = self._is_paused
            self._timer.stop()
            if hasattr(self, "video") and self.video is not None:
                try:
                    self.video.pause()
                except Exception:
                    pass
            import os
            if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                from screens.dialogs import WaitConfirmDialog
                dialog = WaitConfirmDialog(mode="lesson", parent=self)
                res = dialog.exec()
                try:
                    dialog.deleteLater()
                except Exception:
                    pass
                if res != WaitConfirmDialog.DialogCode.Accepted:
                    if self._engine is not None and not self._resources_closed:
                        self._timer.start()
                        if not was_paused and hasattr(self, "video") and self.video is not None and getattr(self.video, "media", None) and self.video.media.available:
                            try:
                                self.video.play()
                            except Exception:
                                pass
                    return
        self._cleanup_resources()
        self._emit_finished()
        self.close()

    def _emit_finished(self):
        if not getattr(self, "_finished_emitted", False):
            self._finished_emitted = True
            self.lesson_finished.emit()

    def _cleanup_resources(self):
        if self._resources_closed:
            return
        self._resources_closed = True
        self._timer.stop()
        self._feedback_timer.stop()
        self._feedback_action = None
        self._cancel_camera_setup()
        self.loading.cancel()
        if hasattr(self, "video") and self.video is not None:
            try:
                if hasattr(self.video, "release"):
                    self.video.release()
                else:
                    self.video.stop()
            except Exception:
                pass
        if self._engine is not None:
            try:
                self._engine.close()
            except Exception:
                pass
            self._engine = None

    def hideEvent(self, event):
        self._cleanup_resources()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._cleanup_resources()
        self._emit_finished()
        event.accept()
