from PySide6.QtCore import Qt, QTimer, QThread
from PySide6.QtWidgets import QWidget, QGridLayout, QScrollArea, QSizePolicy, QHBoxLayout
from backend.minigame_service import letters
from backend.session_state import CameraPracticeSession, Event
from .common import GameWindow, label, style, button
from screens.loading import LoadingOverlay
from screens import camera_access
from screens.camera_preview import RoundedCameraPreview
from backend.camera_service import friendly_camera_error


class FingerSpellQuest(GameWindow):
    # Minigame-only tuning; lesson/session defaults remain unchanged.
    MATCH_FRAMES = 2
    LETTER_COOLDOWN_MS = 250

    def __init__(self, parent=None, engine_factory=None, module_code=None, *, scope=None):
        super().__init__("quest", parent, module_code=module_code, scope=scope)
        self.engine_factory = engine_factory
        self.engine = None
        self._camera_dialog = None
        self._camera_misses = 0
        self.practice = None
        self.content.addWidget(label("Fingerspell each highlighted letter. Spaces/apostrophes need no sign.", "instructionCard"))
        self.target = label("", "gameSubtitle")
        self.content.addWidget(self.target)
        self.progress_scroll = QScrollArea()
        self.progress_scroll.setWidgetResizable(True)
        self.progress_scroll.setFixedHeight(90)
        self.content.addWidget(self.progress_scroll)
        self.camera = RoundedCameraPreview("Opening camera...")
        self.camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera.setMinimumSize(280, 120)
        self.camera.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.content.addWidget(self.camera, 1)
        self.retry = button("Retry camera", self.open_camera)
        self.choose = button('Choose Camera', lambda: self.open_camera(force=True), 'secondaryButton')
        controls = QHBoxLayout()
        controls.addWidget(self.retry)
        controls.addWidget(self.choose)
        self.body.insertLayout(self.body.count()-1, controls)
        self.frame_timer = QTimer(self)
        self.frame_timer.setInterval(33)
        self.frame_timer.timeout.connect(self.read_frame)
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setSingleShot(True)
        self.loading = LoadingOverlay(self)
        self.start()

    def showEvent(self, event):
        super().showEvent(event)
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
        self.countdown.stop()
        if not self.isVisible():
            return
        self._camera_dialog = camera_access.request_camera(self, self._prepare_camera, self._camera_off, force=force)

    def _camera_off(self):
        self._camera_dialog = None
        self.camera.clear()
        self.camera.setText('Camera is off. Choose Camera to set it up, or use Back to keep exploring.')
        self.retry.setEnabled(True)

    def _prepare_camera(self):
        self._camera_dialog = None
        self.retry.setEnabled(False)
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
                    raise RuntimeError('Camera initialization cancelled')
                if not engine.open_camera():
                    raise RuntimeError("Camera unavailable. Check permission/device and retry.")
                return engine
            except Exception:
                if engine is not None:
                    engine.close()
                raise

        self.loading.run(prepare, self._camera_ready, self._camera_failed,
                         dispose=lambda engine: engine.close(), message='Preparing fingerspelling recognition…')

    def _camera_ready(self, engine):
        self.engine = engine
        self._camera_misses = 0
        self.retry.setEnabled(True)
        self.camera.setText("Waiting for camera frame...")
        self.session.resume()
        self.frame_timer.start()
        self.countdown.start()

    def _camera_failed(self, error):
        import logging
        logging.getLogger(__name__).warning("FingerSpell Quest camera unavailable: %s", error)
        self.retry.setEnabled(True)
        self.camera.clear()
        self.camera.setText('Unable to start the camera. ' + friendly_camera_error(error))

    def render_round(self):
        self.round_header()
        self.target.setText(self.session.word)
        self.practice = CameraPracticeSession(
            targets=letters(self.session.word), confidence_threshold=0.0,
            hold_frames=self.MATCH_FRAMES)
        old = self.progress_scroll.takeWidget()
        if old:
            old.deleteLater()
        canvas = QWidget()
        grid = QGridLayout(canvas)
        self.tiles = []
        col = 0
        row = 0
        for char in self.session.word:
            if char == " ":
                col += 1
            elif "A" <= char <= "Z":
                tile = label(char, "progressLetter")
                tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
                grid.addWidget(tile, row, col)
                self.tiles.append(tile)
                col += 1
            if col >= 12:
                row, col = row + 1, 0
        self.progress_scroll.setWidget(canvas)
        canvas.ensurePolished()
        grid.activate()
        self.progress_scroll.setFixedHeight(min(150, max(74, grid.minimumSize().height()+8)))
        self.update_progress()
        self.open_camera()

    def update_progress(self):
        for index, tile in enumerate(self.tiles):
            style(tile, "progressLetterCorrect" if index < self.practice.index else
                  "progressLetterCurrent" if index == self.practice.index else "progressLetter")

    def read_frame(self):
        if self.session.resolved or self.session.remaining <= 0:
            self.tick()
            return
        try:
            result = self.engine.read_frame()
            if result is None:
                self._camera_misses += 1
                if self._camera_misses < 3:
                    return
                raise RuntimeError("Camera disconnected. Retry camera.")
            self._camera_misses = 0
            frame = result.annotated_bgr
            self.camera.set_bgr_frame(frame)
            if result.prediction:
                self.handle_prediction(result.prediction.label, result.prediction.confidence)
            else:
                self.practice.reset_waiting()
        except Exception as error:
            import logging
            logging.getLogger(__name__).exception("FingerSpell Quest camera failed")
            self.stop_activity()
            self.session.pause()
            self.countdown.stop()
            self.camera.clear()
            self._camera_failed(error)

    def handle_prediction(self, predicted, confidence):
        if self.session.resolved or self.session.remaining <= 0:
            return
        if self.cooldown_timer.isActive():
            return
        # The engine already returns the top-probability label. Only its identity
        # matters here; lower-ranked expected letters must never be accepted.
        event = self.practice.process_prediction(predicted, 0.0)
        if event == Event.CORRECT:
            self.practice.advance()
            self.update_progress()
            if self.practice.is_done():
                self.resolve(True)
            else:
                self.cooldown_timer.start(self.LETTER_COOLDOWN_MS)
        elif event == Event.WRONG:
            # A mismatch breaks consecutive matches without a lesson-style delay.
            self.practice.reset_waiting()

    def stop_activity(self):
        self.loading.cancel()
        self.retry.setEnabled(True)
        self.frame_timer.stop()
        self.cooldown_timer.stop()
        dialog, self._camera_dialog = self._camera_dialog, None
        if dialog is not None:
            dialog.reject()
        if self.engine is not None:
            self.engine.close()
            self.engine = None
