"""Reusable video surface. Only the service resolves physical media paths."""
import logging
import os
import sys

# On Windows, use FFmpeg backend so Qt can demux QuickTime (.MOV) and MP4 without third-party splitters.
# On macOS, Qt's default 'darwin' (AVFoundation) backend provides native Apple Silicon acceleration for .MOV and .MP4.
if sys.platform == "win32":
    os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")

from PySide6.QtCore import QUrl, Qt, QRectF
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from backend.audio_service import get_audio_service
from backend.media_service import resolve_sign_video

log = logging.getLogger(__name__)


class _VideoPauseOverlay(QWidget):
    """Semi-transparent overlay with large amber pause bars shown when paused."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 85))

        bar_w = 28
        bar_h = 110
        gap = 24
        cx, cy = self.width() / 2, self.height() / 2
        painter.setBrush(QColor("#FFAE00"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(cx - gap / 2 - bar_w, cy - bar_h / 2, bar_w, bar_h), 10, 10)
        painter.drawRoundedRect(QRectF(cx + gap / 2, cy - bar_h / 2, bar_w, bar_h), 10, 10)


class SignVideoPlayer(QWidget):
    def __init__(self, parent=None, *, show_play_button=False, muted=False):
        super().__init__(parent)
        self.show_play_button = show_play_button
        self.is_muted = muted
        self.player = None
        self.video = None
        self.audio = None
        self.media = None
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.message = QLabel("Lesson video is not installed yet.")
        self.message.setWordWrap(True)
        self.message.setStyleSheet("color: #704833; background: #fff9e9; border-radius: 12px; padding: 12px; font-size: 16px;")
        self.body.addWidget(self.message)
        self.play_button = QPushButton("Play / Replay video")
        self.play_button.clicked.connect(self.play)
        self.play_button.hide()
        self.body.addWidget(self.play_button)
        self.pause_overlay = _VideoPauseOverlay(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "pause_overlay") and self.pause_overlay is not None:
            self.pause_overlay.setGeometry(self.rect())

    def _on_media_status(self, status):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if status == QMediaPlayer.MediaStatus.EndOfMedia and self.player is not None:
                if self.player.loops() != QMediaPlayer.Loops.Infinite:
                    self.player.setPosition(0)
                    self.player.play()
        except Exception:
            pass

    def set_sign(self, module_code, sign_code):
        self.stop()
        self.media = resolve_sign_video(module_code, sign_code)
        is_avail = bool(getattr(self.media, "available", False))
        if is_avail:
            self.message.hide()
            if self.video is not None:
                self.video.show()
        else:
            msg = getattr(self.media, "message", None) or "Lesson video is not installed yet."
            self.message.setText(msg)
            if self.show_play_button:
                self.message.show()
            else:
                self.message.hide()
            if self.video is not None:
                self.video.hide()
        self.play_button.setVisible(is_avail and self.show_play_button)

    def play(self):
        if not self.media or not self.media.available:
            return
        host = self.window()
        if host is not None:
            try:
                from screens.loading import LoadingOverlay
                from PySide6.QtCore import QTimer
                for overlay in host.findChildren(LoadingOverlay):
                    if overlay.busy or overlay.isVisible():
                        QTimer.singleShot(200, self.play)
                        return
            except Exception:
                pass
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if self.player is None:
                from PySide6.QtMultimedia import QAudioOutput
                from PySide6.QtMultimediaWidgets import QVideoWidget
                self.player = QMediaPlayer(self)
                self.audio = QAudioOutput(self)
                if self.is_muted:
                    self.audio.setMuted(True)
                    self.audio.setVolume(0.0)
                else:
                    get_audio_service().register_output(self.audio)
                self.video = QVideoWidget(self)
                self.video.setMinimumHeight(120)
                self.body.insertWidget(0, self.video, 1)
                self.player.setAudioOutput(self.audio)
                self.player.setVideoOutput(self.video)
                self.player.setLoops(QMediaPlayer.Loops.Infinite)
                self.player.mediaStatusChanged.connect(self._on_media_status)
                self.player.errorOccurred.connect(self.failed)
            else:
                if self.is_muted and self.audio is not None:
                    self.audio.setMuted(True)
                    self.audio.setVolume(0.0)

            if hasattr(self, "pause_overlay") and self.pause_overlay is not None:
                self.pause_overlay.hide()

            # If already playing or paused on the same media, handle smoothly
            target_source = QUrl.fromLocalFile(str(self.media.local_path))
            if self.player.source() == target_source:
                if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    return
                if self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
                    self.message.hide()
                    self.video.show()
                    self.player.play()
                    return

            self.message.hide()
            self.video.show()
            if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
                self.player.stop()
            self.player.setSource(target_source)
            self.player.play()
        except Exception as error:
            log.warning("SignVideoPlayer playback error: %s", error)
            self.failed(None, str(error))

    def resume(self):
        from PySide6.QtMultimedia import QMediaPlayer
        if hasattr(self, "pause_overlay") and self.pause_overlay is not None:
            self.pause_overlay.hide()
        if self.player is not None and self.player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()
        else:
            self.play()

    def replay(self):
        if hasattr(self, "pause_overlay") and self.pause_overlay is not None:
            self.pause_overlay.hide()
        if self.player is not None:
            try:
                self.player.setPosition(0)
                self.player.play()
            except Exception:
                self.play()
        else:
            self.play()

    def failed(self, error, message):
        log.warning("Lesson video playback unavailable: %s", message)
        self.stop()
        if self.video is not None:
            try:
                self.video.hide()
            except Exception:
                pass
        self.message.setText("This lesson video cannot be played on this device.")
        self.message.show()

    def stop(self):
        if hasattr(self, "pause_overlay") and self.pause_overlay is not None:
            self.pause_overlay.hide()
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass

    def release(self):
        """Cleanly tear down multimedia pipeline to prevent native backend access violations."""
        if hasattr(self, "pause_overlay") and self.pause_overlay is not None:
            self.pause_overlay.hide()
        if self.player is not None:
            try:
                self.player.stop()
                self.player.setSource(QUrl())
            except Exception:
                pass
            self.player = None
        if self.audio is not None:
            try:
                get_audio_service()._outputs.discard(self.audio)
            except Exception:
                pass
            self.audio = None
        self.video = None

    def pause(self):
        if self.player is not None:
            try:
                self.player.pause()
            except Exception:
                pass
        if hasattr(self, "pause_overlay") and self.pause_overlay is not None:
            self.pause_overlay.setGeometry(self.rect())
            self.pause_overlay.show()
            self.pause_overlay.raise_()

    def hideEvent(self, event):
        self.stop()
        super().hideEvent(event)
