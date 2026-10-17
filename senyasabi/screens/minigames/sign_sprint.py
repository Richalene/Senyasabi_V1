from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout
from backend.minigame_service import letters
from .common import AnswerGame, SignImage, button, label


class SignSprint(AnswerGame):
    def __init__(self, parent=None, module_code=None, *, scope=None):
        super().__init__("sprint", parent, module_code=module_code, scope=scope)
        self.content.addWidget(label("Watch Senyas fingerspell, then type the answer.", "instructionCard"))
        self.image = SignImage("A", 250)
        self.content.addWidget(self.image, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        controls = QHBoxLayout()
        self.play_button = button("Play", self.play)
        self.pause_button = button("Pause", self.pause)
        self.replay_button = button("Replay", self.replay)
        for control in (self.play_button, self.pause_button, self.replay_button):
            controls.addWidget(control)
        self.content.addLayout(controls)
        self.sequence = QTimer(self)
        self.sequence.timeout.connect(self.advance_image)
        self.position = 0
        self.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'image'):
            QTimer.singleShot(0, self.fit_sequence)

    def fit_sequence(self):
        # Reserve room for instructions and all playback controls on short displays.
        size = max(100, min(250, self.content_scroll.viewport().height()-150))
        self.image.setFixedSize(size, size)

    def render_round(self):
        self.round_header()
        self.position = 0
        self.sequence.setInterval(self.session.sequence_interval)
        self.advance_image()
        self.sequence.start()

    def advance_image(self):
        from PySide6.QtGui import QPixmap
        from backend.minigame_service import ROOT
        sequence = [char for char in self.session.word.upper() if char == " " or "A" <= char <= "Z"]
        if self.position >= len(sequence):
            self.sequence.stop()
            self.image.clear()
            self.image.setText("Sequence finished. Type your answer or Replay.")
            return
        char = sequence[self.position]
        if char == " ":
            self.image.source = QPixmap()
            self.image.clear()
            self.image.setText("Word gap")
        else:
            self.image.source = QPixmap(str(ROOT / "resources/VRM_SIGNS" / f"{char}.png"))
            self.image.refresh()
        self.position += 1

    def play(self):
        if self.session.resolved:
            return
        self.session.resume()
        self.answer.setEnabled(True)
        self.countdown.start()
        if self.position >= len([char for char in self.session.word.upper() if char == " " or "A" <= char <= "Z"]):
            self.position = 0
        self.sequence.start()

    def pause(self):
        if self.session.resolved:
            return
        self.session.pause()
        self.sequence.stop()
        self.countdown.stop()
        self.answer.setEnabled(False)

    def replay(self):
        if self.session.resolved:
            return
        self.position = 0
        self.play()
        self.advance_image()

    def stop_activity(self):
        self.sequence.stop()
