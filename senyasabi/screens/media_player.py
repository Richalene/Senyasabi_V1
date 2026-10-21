"""Reusable video surface. Only the service resolves physical media paths."""
import logging
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from backend.audio_service import get_audio_service
from backend.media_service import resolve_sign_video

log = logging.getLogger(__name__)


class SignVideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = None
        self.video = None
        self.audio = None
        self.media = None
        self.body = QVBoxLayout(self)
        self.message = QLabel("Lesson video is not installed yet.")
        self.message.setWordWrap(True)
        self.message.setStyleSheet("color: #704833; background: #fff9e9; border-radius: 12px; padding: 12px; font-size: 16px;")
        self.body.addWidget(self.message)
        self.play_button = QPushButton("Play / Replay video")
        self.play_button.clicked.connect(self.play)
        self.play_button.hide()
        self.body.addWidget(self.play_button)

    def set_sign(self, module_code, sign_code):
        self.stop()
        self.media = resolve_sign_video(module_code, sign_code)
        self.message.setText(self.media.message)
        self.message.show()
        self.play_button.setVisible(self.media.available)
        if self.video:
            self.video.hide()

    def play(self):
        if not self.media or not self.media.available:
            return
        try:
            if self.player is None:
                from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
                from PySide6.QtMultimediaWidgets import QVideoWidget
                self.player = QMediaPlayer(self)
                self.audio = QAudioOutput(self)
                get_audio_service().register_output(self.audio)
                self.video = QVideoWidget(self)
                self.video.setMinimumHeight(120)
                self.body.insertWidget(0, self.video, 1)
                self.player.setAudioOutput(self.audio)
                self.player.setVideoOutput(self.video)
                self.player.errorOccurred.connect(self.failed)
            self.message.hide()
            self.video.show()
            self.player.setSource(QUrl.fromLocalFile(str(self.media.local_path)))
            self.player.play()
        except (ImportError, RuntimeError) as error:
            self.failed(None, str(error))

    def failed(self, error, message):
        log.warning("Lesson video playback unavailable: %s", message)
        self.stop()
        if self.video:
            self.video.hide()
        self.message.setText("This lesson video cannot be played on this device.")
        self.message.show()

    def stop(self):
        if self.player:
            self.player.stop()

    def pause(self):
        if self.player:
            self.player.pause()

    def hideEvent(self, event):
        self.stop()
        super().hideEvent(event)
