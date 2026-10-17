from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QGridLayout, QScrollArea, QSizePolicy
from backend.minigame_service import letters
from backend.session_state import CameraPracticeSession, Event
from .common import GameWindow, label, style, button
from screens.loading import LoadingOverlay


class FingerSpellQuest(GameWindow):
    # Minigame-only tuning; lesson/session defaults remain unchanged.
    MATCH_FRAMES = 2
    LETTER_COOLDOWN_MS = 250

    def __init__(self, parent=None, engine_factory=None, module_code=None):
        super().__init__("quest", parent, module_code=module_code)
        self.engine_factory = engine_factory
        self.engine = None
        self.practice = None
        self.content.addWidget(label("Fingerspell each highlighted letter. Spaces/apostrophes need no sign.", "instructionCard"))
        self.target = label("", "gameSubtitle")
        self.content.addWidget(self.target)
        self.progress_scroll = QScrollArea()
        self.progress_scroll.setWidgetResizable(True)
        self.progress_scroll.setFixedHeight(130)
        self.content.addWidget(self.progress_scroll)
        self.camera = label("Opening camera...", "cameraFrame")
        self.camera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera.setMinimumSize(320, 180)
        self.camera.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.content.addWidget(self.camera, 1)
        self.retry = button("Retry camera", self.open_camera)
        self.content.addWidget(self.retry)
        self.frame_timer = QTimer(self)
        self.frame_timer.setInterval(33)
        self.frame_timer.timeout.connect(self.read_frame)
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setSingleShot(True)
        self.loading = LoadingOverlay(self)
        self.start()

    def open_camera(self):
        if self.session.resolved or self.session.complete:
            return
        self.stop_activity()
        if self.practice is not None:
            self.practice.reset_waiting()
        self.session.pause()
        self.countdown.stop()
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
                if not engine.open_camera():
                    raise RuntimeError("Camera unavailable. Check permission/device and retry.")
                return engine
            except Exception:
                if engine is not None:
                    engine.close()
                raise

        self.loading.run(prepare, self._camera_ready, self._camera_failed,
                         dispose=lambda engine: engine.close())

    def _camera_ready(self, engine):
        self.engine = engine
        self.retry.setEnabled(True)
        self.camera.setText("Waiting for camera frame...")
        self.session.resume()
        self.frame_timer.start()
        self.countdown.start()

    def _camera_failed(self, error):
        self.retry.setEnabled(True)
        self.camera.setText(f"Unable to start alphabet camera: {error}")

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
                raise RuntimeError("Camera disconnected. Retry camera.")
            frame = result.annotated_bgr
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format.Format_BGR888).copy()
            self.camera.setPixmap(QPixmap.fromImage(image).scaled(self.camera.width()-24,
                self.camera.height()-24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            if result.prediction:
                self.handle_prediction(result.prediction.label, result.prediction.confidence)
            else:
                self.practice.reset_waiting()
        except Exception as error:
            self.stop_activity()
            self.session.pause()
            self.countdown.stop()
            self.camera.clear()
            self.camera.setText(str(error))

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
        if self.engine is not None:
            self.engine.close()
            self.engine = None
