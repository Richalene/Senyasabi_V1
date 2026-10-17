"""Render real Qt camera surfaces with synthetic frames; never open a camera."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication, QEvent, QSize
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget
from screens.camera_preview import RoundedCameraPreview


class CameraPreviewTests(unittest.TestCase):
    COLOR = QColor(241, 11, 31)

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def tearDown(self):
        for window in self.app.topLevelWidgets():
            window.close()
            window.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def frame(self, width=640, height=360):
        frame = np.empty((height, width, 3), dtype=np.uint8)
        frame[:] = self.COLOR.blue(), self.COLOR.green(), self.COLOR.red()
        return frame

    def render(self, preview):
        self.app.processEvents()
        image = preview.grab().toImage()
        # Assertions use logical widget pixels, including on a high-DPI desktop.
        if image.size() != preview.size():
            image = image.scaled(preview.size())
        return image

    def is_source(self, image, x, y):
        color = image.pixelColor(x, y)
        return all(abs(a - b) <= 2 for a, b in zip(
            (color.red(), color.green(), color.blue()),
            (self.COLOR.red(), self.COLOR.green(), self.COLOR.blue())))

    def assert_fitted_and_rounded(self, preview, aspect):
        image = self.render(preview)
        width, height = image.width(), image.height()
        xs = [x for x in range(width) if self.is_source(image, x, height // 2)]
        ys = [y for y in range(height) if self.is_source(image, width // 2, y)]
        self.assertTrue(xs, 'Camera image is missing from the rendered surface')
        self.assertTrue(ys)
        left, right, top, bottom = xs[0], xs[-1], ys[0], ys[-1]
        self.assertAlmostEqual((right - left + 1) / (bottom - top + 1), aspect, delta=.025)
        self.assertAlmostEqual((left + right) / 2, (width - 1) / 2, delta=1)
        self.assertAlmostEqual((top + bottom) / 2, (height - 1) / 2, delta=1)
        self.assertTrue(self.is_source(image, width // 2, height // 2))
        # Sample the actual image corners, which can lie inside letterbox bars.
        for x in (left + 4, right - 4):
            for y in (top + 4, bottom - 4):
                self.assertFalse(self.is_source(image, x, y),
                                 f'Square camera corner is visible at {(x, y)}')
        return image

    def test_actual_image_is_clipped_when_source_matches_widget_aspect(self):
        preview = RoundedCameraPreview()
        preview.resize(400, 300)
        preview.set_bgr_frame(self.frame(640, 480))
        preview.show()
        self.assert_fitted_and_rounded(preview, 4 / 3)

    def test_letterboxed_image_keeps_rounded_corners_and_is_centered(self):
        preview = RoundedCameraPreview()
        preview.resize(480, 420)
        preview.set_bgr_frame(self.frame())
        preview.show()
        image = self.assert_fitted_and_rounded(preview, 16 / 9)
        self.assertFalse(self.is_source(image, image.width() // 2, 30))
        self.assertFalse(self.is_source(image, image.width() // 2, image.height() - 31))

    def test_resize_and_fullscreen_keep_original_aspect_and_source_resolution(self):
        preview = RoundedCameraPreview()
        source = QPixmap(640, 360)
        source.fill(self.COLOR)
        preview.setPixmap(source)
        preview.show()
        for size in ((760, 300), (300, 620), (540, 405)):
            with self.subTest(size=size):
                preview.resize(*size)
                self.assert_fitted_and_rounded(preview, 16 / 9)
                self.assertEqual(preview.pixmap().size(), source.size())
        preview.showFullScreen()
        self.app.processEvents()
        self.assertTrue(preview.isFullScreen())
        self.assert_fitted_and_rounded(preview, 16 / 9)
        self.assertEqual(preview.pixmap().size(), source.size())

    def test_bgr_display_conversion_copies_without_mutating_recognition_frame(self):
        preview = RoundedCameraPreview()
        frame = self.frame(320, 240)
        original = frame.copy()
        frame.setflags(write=False)
        preview.set_bgr_frame(frame)
        np.testing.assert_array_equal(frame, original)
        self.assertEqual(preview.pixmap().size(), QSize(320, 240))
        self.assertEqual(preview.pixmap().toImage().pixelColor(160, 120), self.COLOR)
        # A capture may reuse its numpy storage on the following frame.
        frame.setflags(write=True)
        frame[:] = 0
        self.assertEqual(preview.pixmap().toImage().pixelColor(160, 120), self.COLOR)

    def test_status_text_and_clear_remove_previous_live_image(self):
        preview = RoundedCameraPreview()
        preview.resize(400, 300)
        preview.set_bgr_frame(self.frame())
        preview.setText('Camera is off')
        preview.show()
        self.assertTrue(preview.pixmap().isNull())
        self.assertEqual(preview.text(), 'Camera is off')
        image = self.render(preview)
        self.assertFalse(self.is_source(image, 200, 150))
        preview.set_bgr_frame(self.frame())
        preview.clear()
        self.assertTrue(preview.pixmap().isNull())
        self.assertEqual(preview.text(), '')

    def test_camera_action_button_keeps_ancestor_theme_over_the_live_image(self):
        parent = QWidget()
        parent.resize(520, 390)
        parent.setStyleSheet('QPushButton { background: #fff9e9; border: 1px solid #a39b68; }')
        preview = RoundedCameraPreview(parent=parent)
        preview.setGeometry(20, 20, 480, 350)
        preview.set_bgr_frame(self.frame())
        actions = QWidget(preview)
        actions.setGeometry(120, 230, 240, 70)
        # An empty caption leaves the center pixel available for a fill check.
        retry = QPushButton('', actions)
        retry.setGeometry(20, 10, 200, 45)
        parent.show()
        image = self.render(preview)
        center = retry.mapTo(preview, retry.rect().center())
        self.assertEqual(image.pixelColor(center), QColor('#fff9e9'))

    def test_ancestor_label_styles_cannot_restore_square_preview_background(self):
        parent = QWidget()
        parent.setObjectName('previewHost')
        parent.resize(460, 360)
        parent.setStyleSheet('QWidget#previewHost { background: #335577; } '
                            'QLabel#cameraPreview { background: #00ff00; '
                            'border: 9px solid #00ff00; border-radius: 0; padding: 12px; }')
        preview = RoundedCameraPreview(parent=parent)
        preview.setObjectName('cameraPreview')
        preview.setGeometry(30, 30, 400, 300)
        preview.set_bgr_frame(self.frame(640, 480))
        parent.show()
        image = self.assert_fitted_and_rounded(preview, 4 / 3)
        host_image = self.render(parent)
        for x in (2, image.width() - 3):
            for y in (2, image.height() - 3):
                self.assertEqual(host_image.pixelColor(preview.x() + x, preview.y() + y),
                                 QColor('#335577'))

    def test_designer_replacement_preserves_geometry_layout_and_identity(self):
        for in_layout in (False, True):
            with self.subTest(in_layout=in_layout):
                parent = QWidget()
                old = QLabel('Set up your camera', parent)
                old.setObjectName('cameraLabel')
                old.setGeometry(30, 40, 420, 300)
                old.setMinimumSize(110, 80)
                old.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
                if in_layout:
                    QVBoxLayout(parent).addWidget(old)
                geometry, policy = old.geometry(), old.sizePolicy()
                preview = RoundedCameraPreview.replace(old)
                self.assertIs(parent.findChild(QLabel, 'cameraLabel'), preview)
                self.assertEqual(preview.geometry(), geometry)
                self.assertEqual(preview.minimumSize(), QSize(110, 80))
                self.assertEqual(preview.sizePolicy(), policy)
                self.assertEqual(preview.text(), 'Set up your camera')
                if in_layout:
                    self.assertIs(parent.layout().itemAt(0).widget(), preview)

    def test_all_five_camera_screens_present_frames_through_shared_component(self):
        from screens.camera_setup import CameraSetupDialog
        from screens.lessons.alphabet.alphabet_lesson import AlphabetLessonWidget
        from screens.lessons.spelling.spell_lesson import SpellLessonWidget
        from screens.lessons.words.word_lesson import WordLessonWidget
        from screens.minigames.fingerspell_quest import FingerSpellQuest

        frame = self.frame(320, 240)
        original = frame.copy()
        result = SimpleNamespace(annotated_bgr=frame, hand_detected=False, prediction=None)
        setup = CameraSetupDialog(service=Mock(), onboarding=True)
        setup.capture = Mock(read=Mock(return_value=(True, frame)))
        setup._testing_device = SimpleNamespace(device_id='synthetic-camera')
        setup.read_frame()
        previews = [setup.preview]
        for screen in (AlphabetLessonWidget(letters=['A']),
                       SpellLessonWidget('HELLO', category='greeting'),
                       WordLessonWidget(['HELLO'], category='greeting')):
            screen._engine = Mock(read_frame=Mock(return_value=result))
            screen._on_tick()
            previews.append(screen._camera_lbl)
            self.assertIs(screen._ui.findChild(QLabel, 'cameraLabel'), screen._camera_lbl)
        quest = FingerSpellQuest(module_code='greeting')
        quest.engine = Mock(read_frame=Mock(return_value=result))
        quest.read_frame()
        previews.append(quest.camera)
        self.assertEqual(len(previews), 5)
        for preview in previews:
            self.assertIsInstance(preview, RoundedCameraPreview)
            self.assertEqual(preview.pixmap().size(), QSize(320, 240))
            self.assertEqual(preview.pixmap().toImage().pixelColor(160, 120), self.COLOR)
        np.testing.assert_array_equal(frame, original)


if __name__ == '__main__':
    unittest.main()
