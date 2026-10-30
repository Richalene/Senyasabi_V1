"""
FSL Word Lesson widget redesigned with the modern layout matching Figma.
"""
from __future__ import annotations

import logging
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
from backend.inference_worker import InferenceWorker

log = logging.getLogger(__name__)

_VRM_DIR = _ROOT / "resources" / "VRM_SIGNS"



class WordLessonWidget(LessonCameraMixin, QWidget):
    lesson_finished = Signal()

    def __init__(
        self,
        module_code: str | list = "greeting",
        parent_or_code: QWidget | str | None = None,
        parent: QWidget | None = None,
        *,
        words: list | None = None,
        category: str | None = None,
        **kwargs,
    ):
        actual_parent = parent
        actual_words = words
        if isinstance(module_code, list):
            actual_words = module_code if actual_words is None else actual_words
            actual_module = parent_or_code if isinstance(parent_or_code, str) else (category or "greeting")
            if isinstance(parent_or_code, QWidget):
                actual_parent = parent_or_code
        elif isinstance(parent_or_code, str):
            actual_module = parent_or_code
        elif isinstance(module_code, str):
            actual_module = module_code
            if isinstance(parent_or_code, QWidget):
                actual_parent = parent_or_code
        elif category is not None:
            actual_module = category
        else:
            actual_module = "greeting"

        super().__init__(actual_parent)
        self.resize(1920, 1080)
        self.setStyleSheet('background-color: #C2D076;')
        self.module_code = actual_module.casefold()
        self._category = actual_module.title()
        self.setWindowTitle(f"SenyaSabi - {self.module_code.title()} Words")

        if actual_words is not None:
            self.signs = get_signs_for_module(self.module_code)
            self._targets = [str(w).upper() for w in actual_words]
        else:
            self.signs = get_signs_for_module(self.module_code)
            self._targets = [s.sign_code.upper() for s in self.signs]
        self.layout_comp = ModernLessonLayout(self)
        self.layout_comp.setGeometry(0, 0, 1920, 1080)

        # Wire UI
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
        self._word_lbl = self.layout_comp.lbl_target_word
        self._ui = self.layout_comp
        self._is_paused = False

        # Embedded SignVideoPlayer on avatar card
        self.video = SignVideoPlayer(self.layout_comp.avatar_card, muted=True)
        v_layout = QVBoxLayout(self.layout_comp.avatar_card)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.addWidget(self.video)
        self.video.hide()

        # Engine & Session
        self._engine = None
        self._worker = None
        self._camera_misses = 0
        self._resources_closed = False
        self._session = CameraPracticeSession(targets=self._targets, confidence_threshold=0.20, hold_frames=5, grace_frames=5)

        self._is_ticking = False
        self._tick_counter = 0

        self._timer = QTimer(self)
        self._timer.setInterval(41)
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

    def _load_ref_media(self, sign_code: str):
        try:
            self.video.set_sign(self.module_code, sign_code.lower())
            is_avail = bool(getattr(self.video.media, "available", False))
            self.video.setVisible(is_avail)
            if is_avail:
                self.layout_comp.avatar_card.set_sign_pixmap(QPixmap())
                if not self._is_paused:
                    self.video.play()
                return
        except Exception as e:
            pass
        try:
            img_path = _VRM_DIR / f"{sign_code.upper()}.png"
            if img_path.exists():
                self.layout_comp.avatar_card.set_sign_pixmap(QPixmap(str(img_path)))
            else:
                self.layout_comp.avatar_card.set_sign_pixmap(QPixmap())
        except Exception:
            self.layout_comp.avatar_card.set_sign_pixmap(QPixmap())

    def _refresh_ui(self):
        session = self._session
        total = session.total
        idx = session.index

        if session.is_done():
            self._show_completion()
            return

        sign_code = session.current_target
        clean_word = sign_code.replace("_", " ").title()
        self.layout_comp.set_target(
            clean_word,
            category=f"{self._category.upper()} - SIGN THIS WORD",
            progress=f"Word {idx + 1} of {total}"
        )
        self.layout_comp.set_prediction("Waiting for hand...", status="waiting")
        self._load_ref_media(sign_code)

        self.layout_comp.feedback_overlay.hide()
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
                # hide() pauses via SignVideoPlayer.hideEvent; release() does the final teardown.
                self.video.hide()
            except Exception:
                pass
        pct = self._session.score_percent()
        self.layout_comp.feedback_overlay.show_success(
            accuracy_pct=pct,
            message="Module Complete! You are a Natural!"
        )
        self.layout_comp.btn_next.set_green(True)

        try:
            from backend import auth_service, sync_service, content_service
            user = auth_service.get_current_user()
            if user:
                lesson_id = content_service.get_lesson_id(self.module_code)
                if lesson_id is not None:
                    sync_service.get_sync_service().queue_lesson_progress(
                        user_id=user["user_id"],
                        lesson_id=lesson_id,
                        completion_percentage=float(pct),
                        status="Completed",
                        time_spent_seconds=0,
                    )
        except Exception:
            pass

    def _on_tick(self):
        if getattr(self, "_is_ticking", False) or self._engine is None or self._resources_closed:
            return
        self._is_ticking = True
        try:
            # Camera reads + MediaPipe/Keras inference run in InferenceWorker; the UI thread only
            # consumes the latest frame / latest prediction (older ones are dropped).
            worker = self._worker
            if worker is not None and worker.engine is not self._engine:
                self._stop_inference()
                worker = None
            if worker is None:
                worker = self._worker = InferenceWorker(self._engine)
            worker.predict_enabled = self._feedback_action is None
            latest, pred, error = worker.take()
            if error is not None:
                self._cleanup_resources("inference worker error: %s" % (error,))
                self._camera_failed(error)
                return
            if latest is None:
                return

            display_frame = latest.annotated_bgr if latest.annotated_bgr is not None else latest.frame_bgr
            if display_frame is not None:
                import cv2
                display_frame = cv2.flip(display_frame, 1)
            self._camera_lbl.set_bgr_frame(display_frame)

            if pred is None or self._feedback_action is not None:
                return
            result = pred

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

            # Extract probability specifically for the TARGET sign
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

            clean_target_display = str(target).replace("_", " ").title()

            # Grade the user's accuracy on the TARGET sign
            if target_prob >= other_max_prob and target_prob > 0.05:
                # Target is the #1 recognized sign (85% - 98%)
                accuracy_pct = min(98, 85 + int(min(target_prob, 0.70) / 0.70 * 13))
                is_match = True
            elif other_max_prob > 0 and (target_prob / other_max_prob) >= 0.40 and target_prob >= 0.12:
                # Target is a strong contender (65% - 84%)
                ratio = target_prob / other_max_prob
                accuracy_pct = int(65 + (ratio - 0.40) / 0.60 * 19)
                is_match = True
            else:
                ratio = (target_prob / other_max_prob) if other_max_prob > 0 else 0.0
                accuracy_pct = max(15, min(55, int(ratio * 55)))
                is_match = False

            # Only pass the target into session evaluation
            eval_label = target if is_match else "__NO_MATCH__"
            eval_conf = accuracy_pct / 100.0

            event = self._session.process_prediction(eval_label, eval_conf)

            if event == Event.HOLDING:
                pct_progress = int(self._session.hold_progress * 100)
                self.layout_comp.set_prediction(
                    f"Hold it! {pct_progress}% ({accuracy_pct}%)",
                    status="holding"
                )
            elif event == Event.CORRECT:
                self._reset_sequence()
                self.layout_comp.set_prediction(
                    f"Correct! {clean_target_display} ({accuracy_pct}%)",
                    status="correct"
                )
                self.layout_comp.feedback_overlay.show_success(
                    accuracy_pct=accuracy_pct,
                    message="You are a Natural!"
                )
                self.layout_comp.btn_next.set_green(True)
                self._feedback_action = "advance"
                self._feedback_timer.start(1400)
            else:
                # We ONLY check and display for the target sign - never other signs!
                if is_match:
                    self.layout_comp.set_prediction(
                        f"Signing: {clean_target_display} ({accuracy_pct}%)",
                        status="holding"
                    )
                else:
                    self.layout_comp.set_prediction(
                        f"Sign: {clean_target_display} ({accuracy_pct}%)",
                        status="waiting"
                    )
        except Exception as e:
            pass
        finally:
            self._is_ticking = False

    def _reset_sequence(self):
        """Ask the worker (sole user of the recognizer buffer) to reset; direct call if no worker."""
        try:
            if self._worker is not None:
                self._worker.request_reset()
            elif self._engine is not None and hasattr(self._engine, "reset_sequence"):
                self._engine.reset_sequence()
        except Exception:
            pass

    def _stop_inference(self):
        """Stop the worker. True when it is gone (engine safe to close); False when it will
        close the engine itself after leaving a stuck native call."""
        worker, self._worker = self._worker, None
        return True if worker is None else worker.shutdown()

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
        except Exception as e:
            pass

    def _advance(self):
        try:
            self._timer.stop()
            self._feedback_timer.stop()
            self._feedback_action = None
            if self._resources_closed:
                return
            self._reset_sequence()
            self._session.advance()
            self._refresh_ui()
        except Exception as e:
            pass
        finally:
            if self._engine is not None and not self._resources_closed and not self._session.is_done():
                self._camera_misses = 0
                if hasattr(self._engine, "_missed_reads"):
                    self._engine._missed_reads = 0
                cap = getattr(self._engine, "_cap", None)
                if cap is not None:
                    if hasattr(cap, "last_frame"):
                        from time import monotonic
                        cap.last_frame = monotonic()
                    if hasattr(cap, "failed_reads"):
                        cap.failed_reads = 0
                self._timer.start()

    def _on_skip(self):
        try:
            self._timer.stop()
            self._feedback_timer.stop()
            self._feedback_action = None
            if self._session.is_done():
                self._on_back()
                return
            self._session.skip()
            self._refresh_ui()
        except Exception:
            pass
        finally:
            if self._engine is not None and not self._resources_closed and not self._session.is_done():
                self._camera_misses = 0
                if hasattr(self._engine, "_missed_reads"):
                    self._engine._missed_reads = 0
                cap = getattr(self._engine, "_cap", None)
                if cap is not None:
                    if hasattr(cap, "last_frame"):
                        from time import monotonic
                        cap.last_frame = monotonic()
                    if hasattr(cap, "failed_reads"):
                        cap.failed_reads = 0
                self._timer.start()

    def _on_back(self):
        self._feedback_timer.stop()
        self._feedback_action = None
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

    def _cleanup_resources(self, reason="unspecified"):
        if self._resources_closed:
            return
        import sys
        caller = sys._getframe(1)
        log.warning("Word lesson cleanup: reason=%s caller=%s:%s", reason,
                    caller.f_code.co_name, caller.f_lineno)
        self._resources_closed = True
        self._timer.stop()
        self._feedback_timer.stop()
        self._feedback_action = None
        self._cancel_camera_setup()
        self.loading.cancel()
        # DIAGNOSTIC (temporary): SENYASABI_DIAG_VIDEO_LAST=1 releases the video after the camera,
        # worker and engine are shut down, to test whether stopping the player with the camera active hangs.
        import os
        video_last = os.environ.get("SENYASABI_DIAG_VIDEO_LAST") == "1"

        def release_video():
            if hasattr(self, "video") and self.video is not None:
                try:
                    if hasattr(self.video, "release"):
                        self.video.release()
                    else:
                        self.video.stop()
                except Exception:
                    pass

        if not video_last:
            release_video()
        worker_gone = self._stop_inference()
        if self._engine is not None:
            if worker_gone:  # else the worker closes it when it exits
                try:
                    self._engine.close()
                except Exception:
                    pass
            self._engine = None
        if video_last:
            release_video()

    def hideEvent(self, event):
        self._timer.stop()
        if self._worker is not None:
            self._worker.set_active(False)
        if hasattr(self, "video") and self.video is not None:
            try:
                self.video.pause()
            except Exception:
                pass
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._resources_closed and self._engine is not None and not self.loading.busy and not self._session.is_done():
            if not self._is_paused:
                self._camera_misses = 0
                cap = getattr(self._engine, "_cap", None)
                if cap is not None and hasattr(cap, "last_frame"):
                    from time import monotonic
                    cap.last_frame = monotonic()
                    cap.failed_reads = 0
                if self._worker is not None:
                    self._worker.set_active(True)
                self._timer.start()
                if hasattr(self, "video") and self.video is not None and getattr(self.video, "media", None) and self.video.media.available:
                    try:
                        self.video.resume()
                    except Exception:
                        pass

    def closeEvent(self, event):
        self._cleanup_resources()
        self._emit_finished()
        event.accept()
