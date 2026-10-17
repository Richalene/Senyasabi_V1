"""Camera consent/selection tests use local test settings and injected devices only."""
import os
from pathlib import Path
from queue import Queue
import sys
import tempfile
from threading import Event
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

import numpy as np

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QSettings, QCoreApplication, QEvent
from PySide6.QtGui import QImage, QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QDialog
from backend import camera_service, camera_ownership
from backend.camera_service import CameraDevice, CameraService, CameraError
from screens.camera_setup import CameraSetupDialog
from screens import camera_access


def wait_for(predicate):
    for _ in range(300):
        QApplication.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    raise AssertionError('Timed out waiting for camera UI')


class CameraSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = QSettings(str(Path(self.temp.name)/'camera.ini'), QSettings.Format.IniFormat)
        self.devices = [CameraDevice('stable-usb', 'USB Webcam'), CameraDevice('stable-built-in', 'Integrated Camera')]
        self.capture = Mock(isOpened=Mock(return_value=True), read=Mock(return_value=(True, np.zeros((8, 12, 3), np.uint8))))
        self.factory = Mock(return_value=self.capture)
        self.provider = Mock(return_value=self.devices)
        self.service = CameraService(self.settings, self.provider, self.factory)
        self.single = patch.object(camera_service, '_service', self.service)
        self.single.start()

    def tearDown(self):
        for widget in self.app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        from screens.loading import _JOBS
        wait_for(lambda: not _JOBS)
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.single.stop()
        self.settings = None
        self.temp.cleanup()

    def test_preference_uses_stable_id_across_enumeration_order_and_instances(self):
        self.assertFalse(self.service.configured)
        self.assertIsNone(self.service.selected_device())
        self.service.save_selection(self.devices[0])
        self.provider.return_value = list(reversed(self.devices))
        other = CameraService(self.settings, self.provider, self.factory)
        self.assertEqual(other.selected_device().device_id, 'stable-usb')
        self.assertEqual(other.selected_device().name, 'USB Webcam')
        self.factory.assert_not_called()

    def test_nothing_opens_until_explicit_setup_and_test(self):
        parent = QWidget()
        parent.show()
        ready, cancelled = Mock(), Mock()
        dialog = camera_access.request_camera(parent, ready, cancelled)
        self.assertEqual(dialog.pages.currentIndex(), 0)
        self.factory.assert_not_called()
        next(button for button in dialog.findChildren(QPushButton) if button.text() == 'Not Now').click()
        cancelled.assert_called_once()
        ready.assert_not_called()
        self.assertFalse(self.service.configured)
        self.assertTrue(parent.isVisible())

    def test_no_camera_does_not_prevent_cancellation_or_retry(self):
        self.provider.return_value = []
        dialog = CameraSetupDialog(service=self.service)
        dialog.show()
        self.assertIn('No camera was found', dialog.status.text())
        self.assertFalse(dialog.test_button.isEnabled())
        self.assertFalse(dialog.save_button.isEnabled())
        self.factory.assert_not_called()
        self.provider.return_value = self.devices
        dialog.retry_button.click()
        self.assertTrue(dialog.test_button.isEnabled())
        dialog.without_button.click()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        self.assertFalse(self.service.configured)

    def test_preview_save_release_then_activity_uses_same_device(self):
        dialog = CameraSetupDialog(service=self.service)
        dialog.show()
        dialog.combo.setCurrentIndex(1)
        dialog.test_button.click()
        wait_for(lambda: dialog.save_button.isEnabled())
        self.assertEqual(self.factory.call_args.args[0], self.devices[1])
        self.assertIsNotNone(dialog.preview.pixmap())
        dialog.save_button.click()
        self.capture.release.assert_called_once()
        self.assertFalse(dialog.timer.isActive())
        self.assertEqual(self.service.selected_device().device_id, 'stable-built-in')
        self.assertIsNone(camera_ownership._owner)
        second = Mock(isOpened=Mock(return_value=True))
        self.factory.return_value = second
        owner = object()
        capture = self.service.open_capture(owner=owner)
        self.assertEqual(self.factory.call_args.args[0], self.devices[1])
        capture.release()
        second.release.assert_called_once()

    def test_close_during_preview_releases_and_does_not_save(self):
        dialog = CameraSetupDialog(service=self.service)
        dialog.show()
        dialog.test_camera()
        wait_for(lambda: dialog.save_button.isEnabled())
        dialog.close()
        self.capture.release.assert_called_once()
        self.assertFalse(dialog.timer.isActive())
        self.assertFalse(self.service.configured)
        self.assertIsNone(camera_ownership._owner)

    def test_failure_is_friendly_and_can_choose_retry_or_continue(self):
        self.factory.side_effect = RuntimeError('SECRET_TECHNICAL_TRACEBACK')
        dialog = CameraSetupDialog(service=self.service)
        dialog.show()
        dialog.test_camera()
        wait_for(lambda: not dialog.loading.busy)
        self.assertIn('privacy settings', dialog.status.text())
        self.assertNotIn('SECRET_TECHNICAL_TRACEBACK', dialog.status.text())
        self.assertTrue(dialog.test_button.isEnabled())
        self.assertTrue(dialog.combo.isEnabled())
        self.assertFalse(dialog.save_button.isEnabled())
        self.assertIsNone(camera_ownership._owner)

    def test_device_disconnection_never_silently_picks_another_camera(self):
        self.service.save_selection(self.devices[0])
        self.provider.return_value = [self.devices[1]]
        self.assertIsNone(self.service.selected_device())
        with self.assertRaises(CameraError):
            self.service.open_capture(owner=self)
        self.factory.assert_not_called()

    def test_repeated_failed_reads_release_capture_once(self):
        self.service.save_selection(self.devices[0])
        self.capture.read.return_value = False, None
        capture = self.service.open_capture(owner=self)
        for _ in range(3):
            self.assertFalse(capture.read()[0])
        capture.release()
        self.capture.release.assert_called_once()
        self.assertIsNone(camera_ownership._owner)

    def test_numeric_fallback_is_explicit_and_centralized(self):
        device = CameraDevice('opencv:3', 'Camera device 3', 'opencv', 3)
        self.service.save_selection(device)
        self.service.capture_factory = None
        with patch('cv2.VideoCapture', return_value=self.capture) as video:
            capture = self.service.open_capture(owner=self)
            video.assert_called_once_with(3)
            capture.release()

    def test_both_recognition_engines_reopen_the_shared_selected_camera(self):
        from backend.recognition_engine import SignRecognitionEngine
        from backend.model_service import CategoryRecognitionEngine, SequenceRecognizer, ModelState
        from backend.word_landmarks import POSE_INDICES, FEATURE_ORDER, NORMALIZATION
        self.service.save_selection(self.devices[1])
        config = dict(num_frames=24, feature_dim=172, num_hands=2, pose_indices=POSE_INDICES,
                      feature_order=FEATURE_ORDER, normalization=NORMALIZATION)
        recognizer = SequenceRecognizer(Mock(), ('HELLO',), config)
        registry = Mock(get_category_recognizer=Mock(return_value=ModelState('greeting', True, '', recognizer)))
        with patch.object(SignRecognitionEngine, '_build_predictor', return_value=Mock()), patch('backend.recognition_engine.HandLandmarkExtractor', return_value=Mock()):
            for _ in range(3):
                engines = [SignRecognitionEngine(mode='alphabet'), CategoryRecognitionEngine(
                    'greeting', registry=registry, preprocessor_factory=lambda _: Mock())]
                for engine in engines:
                    self.capture = Mock(isOpened=Mock(return_value=True))
                    self.factory.return_value = self.capture
                    self.assertTrue(engine.open_camera())
                    self.assertEqual(self.factory.call_args.args[0], self.devices[1])
                    engine.close()
                    engine.close()
                    self.capture.release.assert_called_once()
                    self.assertIsNone(camera_ownership._owner)

    def test_configured_gate_is_automatic_and_settings_are_reachable(self):
        self.service.save_selection(self.devices[0])
        ready = Mock()
        self.assertIsNone(camera_access.request_camera(None, ready, Mock()))
        ready.assert_called_once()
        self.factory.assert_not_called()
        from screens.app_controller import AppController
        c = AppController()
        c.dev_login()
        c.main_menu.camera_action.trigger()
        dialog = c.camera_settings
        self.assertIsInstance(dialog, CameraSetupDialog)
        c.main_menu.camera_action.trigger()
        self.assertIs(c.camera_settings, dialog)
        dialog.reject()
        self.assertIsNone(c.camera_settings)
        c.shutdown()

    def test_cancel_onboarding_then_back_keeps_session_and_module(self):
        from screens.app_controller import AppController
        c = AppController()
        c.dev_login()
        c.open_module('alphabet')
        c.open_module_lesson(1)
        lesson = c.active_lesson
        wait_for(lambda: lesson._camera_dialog is not None)
        lesson._camera_dialog.reject()
        self.assertIsNone(lesson._engine)
        self.factory.assert_not_called()
        self.assertIn('Camera is off', lesson._camera_lbl.text())
        lesson._back_btn.click()
        self.assertTrue(c.module_lessons.isVisible())
        self.assertEqual(c.selected_module, 'alphabet')
        c.shutdown()

    def test_qt_video_frame_conversion_preserves_orientation_and_bgr(self):
        from PySide6.QtMultimedia import QVideoFrame
        capture = NS(closed=False, frames=Queue(maxsize=2), ready=Event(), error=None)
        worker = camera_service._CameraWorker(capture, None)
        image = QImage(2, 1, QImage.Format.Format_RGB888)
        image.setPixelColor(0, 0, QColor(10, 20, 30))
        image.setPixelColor(1, 0, QColor(40, 50, 60))
        worker.frame(QVideoFrame(image))
        self.assertTrue(capture.ready.is_set())
        np.testing.assert_array_equal(capture.frames.get_nowait(), [[[30, 20, 10], [60, 50, 40]]])
        worker.deleteLater()

    def test_qt_capture_worker_thread_stops_without_gui_blocked_callbacks(self):
        from PySide6.QtMultimedia import QVideoFrame
        def start(worker):
            image = QImage(2, 2, QImage.Format.Format_RGB888)
            image.fill(QColor(10, 20, 30))
            worker.frame(QVideoFrame(image))
        # No QCamera is created: this exercises the real thread/frame transport.
        with patch.object(camera_service._CameraWorker, 'start', start):
            capture = camera_service._QtCapture(self.devices[0])
            self.assertTrue(capture.isOpened())
            self.assertTrue(capture.read()[0])
            capture.release()
            self.assertFalse(capture.thread.isRunning())
            capture.release()

    def test_qt_camera_start_failure_releases_lease(self):
        def fail(worker):
            worker.capture.error = 'Device busy'
            worker.capture.ready.set()
            worker.stop()
        self.service.capture_factory = None
        with patch.object(camera_service._CameraWorker, 'start', fail):
            with self.assertRaisesRegex(CameraError, 'Device busy'):
                self.service.open_capture(owner=self, device=self.devices[0])
        self.assertIsNone(camera_ownership._owner)

    def test_close_while_preview_initializes_disposes_late_capture(self):
        release = Event()
        def delayed(device):
            release.wait(2)
            return self.capture
        self.factory.side_effect = delayed
        dialog = CameraSetupDialog(service=self.service)
        dialog.show()
        dialog.test_camera()
        wait_for(lambda: self.factory.called)
        dialog.close()
        release.set()
        wait_for(lambda: self.capture.release.called)
        self.capture.release.assert_called_once()
        self.assertFalse(self.service.configured)
        self.assertIsNone(camera_ownership._owner)

    def test_repeated_game_and_quiz_routes_do_not_reset_active_windows(self):
        from screens.app_controller import AppController
        c = AppController()
        c.dev_login()
        c.open_module('food')
        c.open_module_quiz()
        quiz = c.quiz
        c.open_module_quiz()
        self.assertIs(c.quiz, quiz)
        c.show_module_choices()
        c.open_module_game('sprint')
        game = c.minigames.game
        c.open_module_game('sprint')
        self.assertIs(c.minigames.game, game)
        c.shutdown()
