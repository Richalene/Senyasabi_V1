"""FingerSpell Quest screen redesigned to match the Figma mockup."""
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QGuiApplication, QPixmap
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
    close_clicked = Signal()
    game_finished = Signal(int, int)

    MATCH_FRAMES = 2
    LETTER_COOLDOWN_MS = 250

    # Design size all absolute coordinates below are based on
    BASE_W, BASE_H = 1920, 1080

    def __init__(self, session, engine_factory=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.engine_factory = engine_factory
        self.engine = None
        self._camera_dialog = None
        self.practice = None
        self._ready = False
        self._last_scale = None
        self.setMinimumSize(0, 0)

        # Background foliage
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1920, 1080)
        self.bg_label.setStyleSheet("background-color: #C2D076;")

        # Header
        self.header = MinigameHeader(self)
        self.header.setGeometry(0, 0, 1920, 90)
        self.header.close_requested.connect(self.close_clicked.emit)
        self.header.raise_()

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
        # Spans the left half of the card (0-1000) and is vertically centered on the camera (y center = 460)
        self.tiles_container.setGeometry(0, 310, 1000, 300)
        self.tiles_container.setStyleSheet("background: transparent;")
        self.tiles_layout = QVBoxLayout(self.tiles_container)
        self.tiles_layout.setContentsMargins(0, 0, 0, 0)
        self.tiles_layout.setSpacing(20)
        self.tiles_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.cam_layout = QVBoxLayout(self.camera_container)
        self.cam_layout.setContentsMargins(15, 15, 15, 15)

        # Real Camera Feed with Fallback placeholder (fill_crop=True fills the container without letterbox bars)
        self.camera = RoundedCameraPreview("Opening camera...", self.camera_container, radius=35, fill_crop=True)
        self.camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam_layout.addWidget(self.camera)

        # Retry button if camera is off
        self.btn_retry_cam = QPushButton("Camera Options", self.card)
        self.btn_retry_cam.setGeometry(1020, 835, 200, 45)
        self.btn_retry_cam.setStyleSheet(
            "QPushButton { background: #526536; color: white; border-radius: 999px; font-weight: bold; } "
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

        self._ready = True

    # ------------------------------------------------------------------
    # Responsive scaling
    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_layout()

    def _scale_layout(self):
        if not self._ready or self.width() < 2 or self.height() < 2:
            return
        s = max(0.1, min(self.width() / self.BASE_W, self.height() / self.BASE_H))
        ox = (self.width() - self.BASE_W * s) / 2    # letterbox offsets
        oy = (self.height() - self.BASE_H * s) / 2

        def g(x, y, w, h):  # design coords -> scaled coords (relative to parent)
            return int(x * s), int(y * s), max(1, int(w * s)), max(1, int(h * s))

        # Background + header span the full widget
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.header.set_scale(s)
        self.header.setGeometry(0, int(oy), self.width(), max(1, int(90 * s)))

        # Main card (positioned in the centered 16:9 area)
        x, y, w, h = g(50, 95, 1820, 935)
        self.card.setGeometry(int(ox) + x, int(oy) + y, w, h)

        # Everything inside the card
        self.instruction_note.setGeometry(*g(100, 40, 800, 40))
        self.tiles_container.setGeometry(*g(0, 310, 1000, 300))
        self.bottom_controls.setGeometry(*g(100, 680, 500, 90))
        self.camera_container.setGeometry(*g(1020, 100, 720, 720))
        self.btn_retry_cam.setGeometry(*g(1020, 835, 200, 45))

        self.checkmark_lbl.setFixedSize(max(1, int(55 * s)), max(1, int(55 * s)))
        self.lbl_hourglass.setFixedSize(max(1, int(50 * s)), max(1, int(60 * s)))
        self.btn_next.set_scale(s)

        self.bottom_controls.layout().setSpacing(int(25 * s))
        self.tiles_layout.setSpacing(int(20 * s))
        m = int(15 * s)
        self.cam_layout.setContentsMargins(m, m, m, m)

        for row in self.tile_rows:
            row.layout().setSpacing(int(15 * s))
        for tile in self.tiles_list:
            tile.set_scale(s)

        # Stylesheets (font sizes / radius) only when the scale changes
        if self._last_scale != s:
            self._last_scale = s
            self.card.setStyleSheet(
                f"QWidget {{ background-color: #FAFFDC; border-radius: {int(40 * s)}px; }}")
            self.camera_container.setStyleSheet(
                f"QWidget {{ background-color: #79BAE8; border-radius: {int(40 * s)}px; }}")
            self.instruction_note.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI'; font-size: {max(8, int(20 * s))}px; "
                "font-style: italic; color: #8F8C78; background: transparent; }")
            self.lbl_timer.setStyleSheet(
                f"QLabel {{ font-family: 'Segoe UI'; font-size: {max(10, int(38 * s))}px; "
                "font-weight: bold; font-style: italic; color: #704833; background: transparent; }")
            self.btn_retry_cam.setStyleSheet(
                "QPushButton { background: #526536; color: white; border-radius: 999px; "
                f"font-weight: bold; font-size: {max(8, int(12 * s))}px; }} "
                "QPushButton:hover { background: #687D43; }")

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
        if not (self.isVisible() or (self.window() and self.window().isVisible())):
            return
        camera_access.request_camera(
            self,
            self._prepare_camera,
            self._camera_off,
            force=force
        )

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
        self.camera.setText("Unable to start camera. " + friendly_camera_error(error))
        self.session.pause()
        self.countdown_timer.stop()
        self.frame_timer.stop()

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
        max_w_len = max((len(w) for w in words), default=5)
        # Dynamically scale tile size and spacing so longer words (e.g. TOMORROW) fit cleanly without overflow
        if max_w_len <= 5:
            tile_size = 100
            spacing = 15
        elif max_w_len <= 7:
            tile_size = 96
            spacing = 14
        elif max_w_len <= 8:
            tile_size = 88
            spacing = 12
        elif max_w_len <= 10:
            tile_size = 76
            spacing = 10
        else:
            tile_size = 66
            spacing = 8

        for w in words:
            row_widget = QWidget(self.tiles_container)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setSpacing(spacing)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for ch in w:
                tile = LetterTile(ch, tile_size=tile_size, parent=row_widget)
                row_layout.addWidget(tile)
                self.tiles_list.append(tile)
            self.tiles_layout.addWidget(row_widget)
            self.tile_rows.append(row_widget)

        # Scale the freshly built tiles to the current window size
        self._last_scale = None
        self._scale_layout()

        self.practice = CameraPracticeSession(
            targets=letters(self.session.word), confidence_threshold=0.0,
            hold_frames=self.MATCH_FRAMES
        )

        self.update_tile_states()
        self.position_checkmark()
        self.countdown_timer.start()
        if self.engine is not None:
            self.frame_timer.start()

    def position_checkmark(self):
        self.checkmark_lbl.hide()

    def read_frame(self):
        if self.engine is None or self.session.resolved or self.cooldown_timer.isActive():
            return
        frame_res = self.engine.read_frame()
        if frame_res is None:
            return
        # Render the live BGR camera frame into the preview (flipped for selfie view)
        bgr = frame_res.annotated_bgr if frame_res.annotated_bgr is not None else frame_res.frame_bgr
        if bgr is not None:
            import cv2
            bgr = cv2.flip(bgr, 1)
        self.camera.set_bgr_frame(bgr)

        # Process predicted label
        if self.practice is None:
            return
        prediction = frame_res.prediction
        label = prediction.label if prediction else None
        confidence = prediction.confidence if prediction else 0.0
        if prediction:
            self.handle_prediction(label, confidence)
        else:
            self.practice.reset_waiting()

    def handle_prediction(self, predicted, confidence):
        if self.session.resolved or self.session.remaining <= 0:
            return
        if self.cooldown_timer.isActive():
            return
        if self.practice is None:
            return
        event = self.practice.process_prediction(predicted, 0.0)
        if event == Event.CORRECT:
            self.practice.advance()
            self.current_letter_idx += 1
            self.update_tile_states()
            if self.practice.is_done():
                self.resolve_round(True)
            else:
                self.practice.reset_waiting()
                self.position_checkmark()
                self.cooldown_timer.start(self.LETTER_COOLDOWN_MS)
        elif event == Event.WRONG:
            self.practice.reset_waiting()

    def tick(self):
        secs = max(0, int(self.session.remaining))
        self.lbl_timer.setText(f"{secs}s")
        if self.session.remaining <= 0 and not self.session.resolved:
            self.resolve_round(False)

    def update_tile_states(self):
        for i, tile in enumerate(self.tiles_list):
            if i < self.current_letter_idx:
                tile.set_state("correct")
            elif i == self.current_letter_idx and not self.session.resolved:
                tile.set_state("active")
            else:
                tile.set_state("filled")

    def resolve_round(self, correct):
        if not self.session.finish(correct):
            return
        self.countdown_timer.stop()
        self.frame_timer.stop()
        self.checkmark_lbl.hide()
        if correct:
            for tile in self.tiles_list:
                tile.set_state("correct")
            self.btn_next.set_green(True)
            QTimer.singleShot(1200, self.next_round)
        else:
            self.btn_next.set_green(True)
            QTimer.singleShot(2200, self.next_round)

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
    close_clicked = Signal()

    def __init__(self, parent=None, engine_factory=None, module_code=None, *, scope=None):
        super().__init__(parent)
        self.scope = scope
        self.module_code = module_code
        self.session = GameSession("quest", rounds=5, module_code=module_code, scope=scope)
        self._engine_factory = engine_factory

        # Fit to the screen instead of forcing 1920x1080
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = min(1920, int(screen.width() * 0.9))
        h = min(1080, int(screen.height() * 0.9))
        self.resize(w, h)
        self.setMinimumSize(800, 450)

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
        self.game_view = FingerSpellQuestGameView(self.session, engine_factory=self._engine_factory, parent=self)
        self.game_view.close_clicked.connect(self._prompt_exit)
        self.game_view.back_requested.connect(self.back_requested.emit)
        self.game_view.game_finished.connect(self.show_score)
        self.stack.addWidget(self.game_view)

        # 3. Score
        self.score_view = MinigameScoreWidget(self)
        self.score_view.continue_requested.connect(self.back_requested.emit)
        self.score_view.close_requested.connect(self.back_requested.emit)
        self.score_view.replay_requested.connect(self.start_game)
        self.stack.addWidget(self.score_view)

        # Make sure no page can hold the window open at a large size
        self.stack.setMinimumSize(0, 0)
        for page in (self.how_to, self.game_view, self.score_view):
            page.setMinimumSize(0, 0)

        self._fitted_form = FittedForm(self)

    def showEvent(self, event):
        super().showEvent(event)
        if self._engine_factory is not None:
            if self.stack.currentWidget() != self.game_view:
                self.start_game()
            elif self.game_view.engine is None and not self.game_view.loading.busy:
                self.game_view.open_camera()
        elif self.stack.currentWidget() == self.game_view:
            if self.game_view.engine is None and not self.game_view.loading.busy:
                self.game_view.open_camera()

    @property
    def loading(self):
        return self.game_view.loading

    @property
    def frame_timer(self):
        return self.game_view.frame_timer

    @property
    def cooldown_timer(self):
        return self.game_view.cooldown_timer

    @property
    def countdown(self):
        return self.game_view.countdown_timer

    @property
    def practice(self):
        return self.game_view.practice

    @practice.setter
    def practice(self, value):
        self.game_view.practice = value

    @property
    def camera(self):
        return self.game_view.camera

    @property
    def engine(self):
        return self.game_view.engine

    @engine.setter
    def engine(self, value):
        self.game_view.engine = value

    @property
    def engine_factory(self):
        return self._engine_factory

    @engine_factory.setter
    def engine_factory(self, value):
        self._engine_factory = value
        self.game_view.engine_factory = value

    def open_camera(self, *args, **kwargs):
        if self.stack.currentWidget() != self.game_view:
            self.stack.setCurrentWidget(self.game_view)
        return self.game_view.open_camera(*args, **kwargs)

    def handle_prediction(self, sign, confidence):
        return self.game_view.handle_prediction(sign, confidence)

    def go_back(self):
        self.stop()
        self.back_requested.emit()

    def read_frame(self):
        return self.game_view.read_frame()

    @property
    def back_button(self):
        btn = getattr(self.how_to, "btn_back", None) or getattr(self.how_to, "back_button", None)
        if btn is not None and not self.rect().contains(btn.geometry()):
            # How-to page hasn't been laid out at the current size yet
            self.how_to.setGeometry(self.rect())
            self.how_to._scale_layout()
        return btn

    def start_game(self):
        self.session = GameSession("quest", rounds=5, module_code=self.module_code, scope=self.scope)
        self.game_view.session = self.session
        self.stack.setCurrentWidget(self.game_view)
        self.game_view.start_game()

    def show_score(self, score, total):
        self.record_score(score, total)
        self.score_view.set_score(score, total)
        self.stack.setCurrentWidget(self.score_view)

    def record_score(self, score, total):
        """Save locally (offline-safe), then sync in the background."""
        try:
            from backend.score_service import record_minigame_result
            record_minigame_result("quest", score, total, self.session.limit)
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
        import os
        if hasattr(self, "game_view"):
            try:
                self.game_view.stop_activity()
                if hasattr(self.game_view, "countdown_timer"):
                    self.game_view.countdown_timer.stop()
            except Exception:
                pass
        if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            from screens.dialogs import WaitConfirmDialog
            dialog = WaitConfirmDialog(mode="game", parent=self)
            if dialog.exec() != WaitConfirmDialog.DialogCode.Accepted:
                if hasattr(self, "game_view") and hasattr(self.game_view, "countdown_timer"):
                    try:
                        self.game_view.countdown_timer.start()
                    except Exception:
                        pass
                return
        self.stop()
        self.back_requested.emit()