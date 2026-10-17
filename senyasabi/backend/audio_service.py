"""Local lesson audio preferences shared by every menu and media player."""
from weakref import WeakSet

from PySide6.QtCore import QObject, QSettings, Signal


class AudioService(QObject):
    changed = Signal()

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings('SenyaSabi', 'SenyaSabi')
        try:
            self._volume = max(0, min(100, int(self.settings.value('audio/volume', 100))))
        except (TypeError, ValueError, OverflowError):
            self._volume = 100
        self._muted = self.settings.value('audio/muted', False, type=bool)
        self._outputs = WeakSet()

    @property
    def volume(self):
        return self._volume

    @property
    def muted(self):
        return self._muted

    def set_volume(self, volume):
        volume = max(0, min(100, int(volume)))
        muted = False if volume > 0 else self._muted
        self._set_state(volume, muted)

    def set_muted(self, muted):
        self._set_state(self._volume, bool(muted))

    def toggle_mute(self):
        self.set_muted(not self._muted)

    def register_output(self, output):
        """Apply saved preferences, including to outputs created after a menu change."""
        self._outputs.add(output)
        self._apply(output)

    def _set_state(self, volume, muted):
        if (volume, muted) == (self._volume, self._muted):
            return
        self._volume, self._muted = volume, muted
        self.settings.setValue('audio/volume', volume)
        self.settings.setValue('audio/muted', muted)
        for output in list(self._outputs):
            self._apply(output)
        self.changed.emit()

    def _apply(self, output):
        try:
            output.setVolume(self._volume / 100.0)
            output.setMuted(self._muted)
        except RuntimeError:
            # Qt may have deleted a screen-owned output before its Python wrapper.
            self._outputs.discard(output)


_service = None


def get_audio_service():
    global _service
    if _service is None:
        _service = AudioService()
    return _service
