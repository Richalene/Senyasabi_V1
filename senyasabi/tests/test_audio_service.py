"""Audio preferences use temporary settings and outputs without audio hardware."""
import gc
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import weakref

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QObject, QSettings
from PySide6.QtWidgets import QApplication, QWidget
import shiboken6

from backend.audio_service import AudioService
from screens.media_player import SignVideoPlayer


class FakeAudioOutput(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.volume = None
        self.muted = None

    def setVolume(self, value):
        if not shiboken6.isValid(self):
            raise RuntimeError('Output has been deleted')
        self.volume = value

    def setMuted(self, value):
        if not shiboken6.isValid(self):
            raise RuntimeError('Output has been deleted')
        self.muted = value


class AudioServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'audio.ini')
        self.settings = QSettings(self.path, QSettings.Format.IniFormat)
        self.service = AudioService(self.settings)

    def tearDown(self):
        self.service = None
        self.settings = None
        self.temp.cleanup()

    def test_safe_defaults_apply_to_new_output_without_opening_hardware(self):
        output = FakeAudioOutput()
        self.service.register_output(output)
        self.assertEqual(self.service.volume, 100)
        self.assertFalse(self.service.muted)
        self.assertEqual(output.volume, 1.0)
        self.assertFalse(output.muted)

    def test_clamped_volume_and_mute_update_all_current_and_later_outputs(self):
        first, second = FakeAudioOutput(), FakeAudioOutput()
        self.service.register_output(first)
        self.service.register_output(second)
        self.service.set_volume(35)
        self.service.set_muted(True)
        for output in (first, second):
            self.assertEqual(output.volume, .35)
            self.assertTrue(output.muted)
        later = FakeAudioOutput()
        self.service.register_output(later)
        self.assertEqual(later.volume, .35)
        self.assertTrue(later.muted)
        self.service.set_volume(500)
        self.assertEqual(self.service.volume, 100)
        self.assertFalse(self.service.muted)
        for output in (first, second, later):
            self.assertEqual(output.volume, 1.0)
            self.assertFalse(output.muted)
        self.service.set_volume(-10)
        self.assertEqual(self.service.volume, 0)
        self.assertEqual(first.volume, 0)

    def test_positive_bar_selection_unmutes_even_at_unchanged_volume(self):
        self.service.set_volume(60)
        self.service.toggle_mute()
        self.assertTrue(self.service.muted)
        self.service.set_volume(60)
        self.assertEqual(self.service.volume, 60)
        self.assertFalse(self.service.muted)

    def test_changes_notify_once_and_persist_between_service_instances(self):
        changed = Mock()
        self.service.changed.connect(changed)
        self.service.set_volume(45)
        self.service.set_muted(True)
        self.service.set_muted(True)
        self.assertEqual(changed.call_count, 2)
        self.settings.sync()
        other_settings = QSettings(self.path, QSettings.Format.IniFormat)
        other = AudioService(other_settings)
        self.assertEqual(other.volume, 45)
        self.assertTrue(other.muted)
        self.assertEqual(other_settings.value('audio/volume', type=int), 45)
        self.assertTrue(other_settings.value('audio/muted', type=bool))

    def test_malformed_saved_volume_uses_safe_default(self):
        self.settings.setValue('audio/volume', 'invalid')
        self.assertEqual(AudioService(self.settings).volume, 100)
        self.settings.setValue('audio/volume', -30)
        self.assertEqual(AudioService(self.settings).volume, 0)
        self.settings.setValue('audio/volume', 250)
        self.assertEqual(AudioService(self.settings).volume, 100)

    def test_closed_outputs_are_not_retained_or_updated_after_qt_deletion(self):
        output = FakeAudioOutput()
        self.service.register_output(output)
        reference = weakref.ref(output)
        del output
        gc.collect()
        self.assertIsNone(reference())
        deleted = FakeAudioOutput()
        self.service.register_output(deleted)
        shiboken6.delete(deleted)
        self.service.toggle_mute()
        self.assertNotIn(deleted, self.service._outputs)

    def test_lesson_player_registers_lazy_output_and_reuses_it(self):
        from PySide6 import QtMultimedia, QtMultimediaWidgets
        fake_player = Mock()
        outputs = []

        def make_output(parent):
            output = FakeAudioOutput(parent)
            outputs.append(output)
            return output

        self.service.set_volume(25)
        self.service.set_muted(True)
        with patch.object(QtMultimedia, 'QMediaPlayer', return_value=fake_player), \
                patch.object(QtMultimedia, 'QAudioOutput', side_effect=make_output), \
                patch.object(QtMultimediaWidgets, 'QVideoWidget', QWidget), \
                patch('screens.media_player.get_audio_service', return_value=self.service):
            player = SignVideoPlayer()
            player.media = SimpleNamespace(available=True, local_path=Path('lesson.mp4'))
            self.assertIsNone(player.audio)
            player.play()
            self.assertEqual(len(outputs), 1)
            self.assertEqual(outputs[0].volume, .25)
            self.assertTrue(outputs[0].muted)
            self.service.set_volume(75)
            self.assertEqual(outputs[0].volume, .75)
            self.assertFalse(outputs[0].muted)
            player.play()
            self.assertEqual(len(outputs), 1)
            self.assertEqual(fake_player.play.call_count, 2)
            player.close()
            player.deleteLater()


if __name__ == '__main__':
    unittest.main()
