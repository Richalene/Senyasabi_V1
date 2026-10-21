"""FingerSpell Quest screen redesigned to match the Figma mockup."""
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                              QVBoxLayout, QStackedWidget)
from backend.minigame_service import ROOT, GameSession, letters
from backend.session_state import CameraPracticeSession, Event
from screens.loading import LoadingOverlay
from screens import camera_access
from screens.camera_preview import RoundedCameraPreview
from backend.camera_service import friendly_camera_error
from screens.startup import FittedForm
from .minigame_ui_components import (HowToPlayWidget, MinigameScoreWidget,
                                     MinigameHeader, LetterTile, CircularActionButton)


class FingerSpellQuestGameView(QWidget):
    """
    Main active gameplay screen for FingerSpell Quest:
    - Target word letter tiles on the left
    - Green checkmark indicator on current letter matched
    - Rounded camera preview / user avatar placeholder on the right
    - Controls: Next button, Countdown timer
    """
    back_requested = Signal()
    game_finished = Signal(int, int)

    MATCH_FRAMES = 2
    LETTER_COOLDOWN_MS = 250

    def __init__(self, session, engine_factory=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.engine_factory = engine_factory
        self.engine = None
        self._camera_dialog = None
        self.practice = None
        self.resize(1920, 1080)

        # Background foliage
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setStyleSheet("background-color: #C2D076;")

        # Header
        self.header = MinigameHeader(self)
        self.header.setGeometry(0, 0, 1920, 90)
        self.header.close_requested.connect(self._prompt_exit)

        # Main Cream Card Container
        self.card = QWidget(self)
        self.card.setGeometry(50, 95, 1820, 935)
        self.card.setStyleSheet("QWidget { background-color: #FAFFDC; border-radius: 40px; }")

        # Instruction note top-left
        self.instruction_note = QLabel("Fingerspell each letter of the word(s) before time runs out.", self.card)
        self.instruction_note.setGeometry(100, 40, 800, 40)
        self.instruction_note.setStyleSheet(
            "QLabel { font-family: 'Segoe UI'; font-size: 20px; font-style: italic; color: #8F8C78; background: transparent; }"
        )

        # Left: Target Letter Tiles Container
        self.tiles_container = QWidget(self.card)
        self.tiles_container.setGeometry(100, 260, 850, 300)
        self.tiles_container.setStyleSheet("background: transparent;")
        self.tiles_layout = QVBoxLayout(self.tiles_container)
        self.tiles_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Checkmark icon indicator
        self.checkmark_lbl = QLabel(self.card)
        self.checkmark_lbl.setFixedSize(55, 55)
        self.checkmark_lbl.setPixmap(QPixmap(str(ROOT / "resources/img/ui/green_check.png")))
        self.checkmark_lbl.setScaledContents(True)
        self.checkmark_lbl.hide()

        # Bottom Left Controls: Next button + timer
        self.bottom_controls = QWidget(self.card)
        self.bottom_controls.setGeometry(100, 680, 500, 90)
        self.bottom_controls.setStyleSheet("background: transparent;")
        b_layout = QHBoxLayout(self.bottom_controls)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(25)

        self.btn_next = CircularActionButton("next", self.bottom_controls)
        self.btn_next.clicked.connect(self.next_round)
        b_layout.addWidget(self.btn_next)

        self.lbl_timer = QLabel("10s", self.bottom_controls)
        self.lbl_timer.setStyleSheet(
            "QLabel { font-family: 'Segoe UI'; font-size: 38px; font-weight: bold; font-style: italic; color: #704833; background: transparent; }"
        )
        b_layout.addWidget(self.lbl_timer)

        self.lbl_hourglass = QLabel(self.bottom_controls)
        self.lbl_hourglass.setFixedSize(50, 60)
        self.lbl_hourglass.setPixmap(QPixmap(str(ROOT / "resources/img/ui/hourglass.png")))
        self.lbl_hourglass.setScaledContents(True)
        b_layout.addWidget(self.lbl_hourglass)
        b_layout.addStretch()

        # Right: Camera Container Card
        self.camera_container = QWidget(self.card)
        self.camera_container.setGeometry(1020, 100, 720, 720)
        self.camera_container.setStyleSheet(
            "QWidget { background-color: #79BAE8; border-radius: 40px; }"
        )
        cam_layout = QVBoxLayout(self.camera_container)
        cam_layout.setContentsMargins(15, 15, 15, 15)

        # Real Camera Feed with Fallback placeholder (fill_crop=True fills the container without letterbox bars)
        self.camera = RoundedCameraPreview("Opening camera...", self.camera_container, radius=35, fill_crop=True)
        self.camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cam_layout.addWidget(self.camera)

        # Retry button if camera is off
        self.btn_retry_cam = QPushButton("Camera Options", self.card)
        self.btn_retry_cam.setGeometry(1020, 835, 200, 45)
        self.btn_retry_cam.setStyleSheet(
            "QPushButton { background: #526536; color: white; border-radius: 15px; font-weight: bold; } "
            "QPushButton:hover { background: #687D43; }"
        )
        self.btn_retry_cam.clicked.connect(lambda: self.open_camera(force=True))

        # Frame and cooldown timers
        self.frame_timer = QTimer(self)
        self.frame_timer.setInterval(33)
        self.frame_timer.timeout.connect(self.read_frame)

        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setSingleShot(True)

        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(100)
        self.countdown_timer.timeout.connect(self.tick)

        self.loading = LoadingOverlay(self)

        self.tile_rows = []
        self.tiles_list = []
        self.current_letter_idx = 0

    def start_game(self):
        self.load_round()
        if self.engine is None and not self.loading.busy:
            self.open_camera()

    def open_camera(self, checked=False, *, force=False):
        if self.session.resolved or self.session.complete:
            return
        if self.loading.busy or (self._camera_dialog is not None and self._camera_dialog.isVisible()):
            return
        self.stop_activity()
        if self.practice is not None:
            self.practice.reset_waiting()
        self.session.pause()
        self.countdown_timer.stop()
        if not self.isVisible():
            return
        self._camera_dialog = camera_access.request_camera(self, self._prepare_camera, self._camera_off, force=force)

    def _camera_off(self):
        self._camera_dialog = None
        self.camera.clear()
        # Fallback yellow silhouette
        placeholder_path = ROOT / "resources/img/ui/quest_user_placeholder.png"
        if placeholder_path.exists():
            self.camera.setPixmap(QPixmap(str(placeholder_path)))
            self.camera.setScaledContents(True)
        else:
            self.camera.setText("Camera is off.")

    def _prepare_camera(self):
        self._camera_dialog = None
        factory = self.engine_factory

        def prepare():
            engine = None
            try:
                engine_type = factory
                if engine_type is None:
                    from backend.recognition_engine import SignRecognitionEngine
                    engine_type = SignRecognitionEngine
                engine = engine_type(mode="alphabet")
                if QThread.currentThread().isInterruptionRequested():
                    raise RuntimeError("Camera initialization cancelled")
                if not engine.open_camera():
                    raise RuntimeError("Camera unavailable. Check permission/device and retry.")
                return engine
            except Exception:
                if engine is not None:
                    engine.close()
                raise

        self.loading.run(prepare, self._camera_ready, self._camera_failed,
                         dispose=lambda eng: eng.close(), message="Preparing fingerspelling recognition…")

    def _camera_ready(self, engine):
        self.engine = engine
        self.camera.setText("Waiting for camera frame...")
        self.session.resume()
        self.frame_timer.start()
        self.countdown_timer.start()

    def _camera_failed(self, error):
        import logging
        logging.getLogger(__name__).warning("FingerSpell Quest camera unavailable: %s", error)
        self.camera.clear()
        placeholder_path = ROOT / "resources/img/ui/quest_user_placeholder.png"
        if placeholder_path.exists():
            self.camera.setPixmap(QPixmap(str(placeholder_path)))
            self.camera.setScaledContents(True)
        else:
            self.camera.setText("Unable to start camera. " + friendly_camera_error(error))

    def load_round(self):
        self.checkmark_lbl.hide()
        self.btn_next.set_green(False)
        self.current_letter_idx = 0

        # Build tiles
        for r in self.tile_rows:
            r.deleteLater()
        self.tile_rows.clear()
        self.tiles_list.clear()

        words = self.session.word.split()
        for w in words:
            row_widget = QWidget(self.tiles_container)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(15)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for ch in w:
                tile = LetterTile(ch, row_widget)
                row_layout.addWidget(tile)
                self.tiles_list.append(tile)
            self.tiles_layout.addWidget(row_widget)
            self.tile_rows.append(row_widget)

        self.practice = CameraPracticeSession(
            targets=letters(self.session.word), confidence_threshold=0.0,
            hold_frames=self.MATCH_FRAMES
        )

        self.position_checkmark()
        self.countdown_timer.start()
        if self.engine is not None:
            self.frame_timer.start()

    def position_checkmark(self):
        if self.current_letter_idx < len(self.tiles_list):
            tile = self.tiles_list[self.current_letter_idx]
            tile_pos = tile.mapTo(self.card, tile.rect().topLeft())
            self.checkmark_lbl.move(tile_pos.x() + (tile.width() - self.checkmark_lbl.width()) // 2,
                                   tile_pos.y() - 65)
            self.checkmark_lbl.show()
        else:
            self.checkmark_lbl.hide()

    def read_frame(self):
        if self.engine is None or self.session.resolved or self.cooldown_timer.isActive():
            return
        frame_res = self.engine.read_frame()
        if frame_res is None:
            return
        # Render the live BGR camera frame into the preview
        self.camera.set_bgr_frame(frame_res.annotated_bgr if frame_res.annotated_bgr is not None else frame_res.frame_bgr)

        # Process predicted label
        prediction = frame_res.prediction
        label = prediction.label if prediction else None
        confidence = prediction.confidence if prediction else 0.0

        event = self.practice.process_prediction(label, confidence)
        if event == Event.CORRECT:
            self.current_letter_idx += 1
            if self.practice.advance():
                self.resolve_round(True)
            else:
                self.practice.reset_waiting()
                self.position_checkmark()
                self.cooldown_timer.start(self.LETTER_COOLDOWN_MS)

    def tick(self):
        secs = max(0, int(self.session.remaining))
        self.lbl_timer.setText(f"{secs}s")
        if self.session.remaining <= 0 and not self.session.resolved:
            self.resolve_round(False)

    def resolve_round(self, correct):
        if not self.session.finish(correct):
            return
        self.countdown_timer.stop()
        self.frame_timer.stop()
        self.checkmark_lbl.hide()
        self.btn_next.set_green(True)

    def next_round(self):
        if not self.session.resolved:
            return
        if self.session.next_round():
            self.load_round()
        else:
            self.stop_activity()
            self.game_finished.emit(self.session.score, self.session.total)

    def stop_activity(self):
        self.countdown_timer.stop()
        self.frame_timer.stop()
        if self.engine is not None:
            self.engine.close()
            self.engine = None


class FingerSpellQuest(QWidget):
    """
    Complete FingerSpell Quest experience:
    - How-To Screen (FINGERSPELLQUESTHOW.png)
    - Gameplay Screen
    - Score Screen (scores_bg.png)
    """
    back_requested = Signal()

    def __init__(self, parent=None, engine_factory=None, module_code=None, *, scope=None):
        super().__init__(parent)
        self.resize(1920, 1080)
        self.session = GameSession("quest", rounds=5, module_code=module_code, scope=scope)
        self.engine_factory = engine_factory

        self.stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # 1. How to play
        self.how_to = HowToPlayWidget("FINGERSPELLQUESTHOW.png", self)
        self.how_to.start_requested.connect(self.start_game)
        self.how_to.back_requested.connect(self.back_requested.emit)
        self.stack.addWidget(self.how_to)

        # 2. Gameplay
        self.game_view = FingerSpellQuestGameView(self.session, engine_factory=self.engine_factory, parent=self)
        self.game_view.back_requested.connect(self.back_requested.emit)
        self.game_view.game_finished.connect(self.show_score)
        self.stack.addWidget(self.game_view)

        # 3. Score
        self.score_view = MinigameScoreWidget(self)
        self.score_view.continue_requested.connect(self.back_requested.emit)
        self.score_view.close_requested.connect(self.back_requested.emit)
        self.stack.addWidget(self.score_view)

        self._fitted_form = FittedForm(self)

    def start_game(self):
        self.stack.setCurrentWidget(self.game_view)
        self.game_view.start_game()

    def show_score(self, score, total):
        self.record_score(score, total)
        self.score_view.set_score(score, total)
        self.stack.setCurrentWidget(self.score_view)

    def record_score(self, score, total):
        try:
            import uuid
            from datetime import datetime, timezone
            from backend import auth_service
            from backend.database.session import session_scope
            from backend.database.repository import upsert_minigame_attempt, rebuild_user_statistics
            from backend.leaderboard_service import notify_scores_changed

            user = auth_service.get_current_user()
            if not user:
                return
            uid = uuid.UUID(user["user_id"]) if isinstance(user["user_id"], str) else user["user_id"]

            with session_scope() as db:
                # minigame_id 5 is FingerSpell Quest
                upsert_minigame_attempt(
                    db,
                    user_id=uid,
                    game_attempt_id=uuid.uuid4(),
                    minigame_id=5,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    score=score,
                    duration_seconds=75,
                    accuracy=score / max(1, total)
                )
                rebuild_user_statistics(db, uid)
            notify_scores_changed()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to record minigame score: %s", e)

    def stop(self):
        self.game_view.stop_activity()

    def hideEvent(self, event):
        self.stop()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)

    def _prompt_exit(self):
        from screens.dialogs import WaitConfirmDialog
        dialog = WaitConfirmDialog(mode="game", parent=self)
        if dialog.exec() == WaitConfirmDialog.DialogCode.Accepted:
            self.back_requested.emit()
