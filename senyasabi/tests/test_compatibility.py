"""Section 14 - Compatibility: OS/runtime, webcams (built-in vs USB), resolutions, packaging."""
import importlib
import platform
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import APP_ROOT, qt_app  # noqa: E402

import numpy as np  # noqa: E402
from PySide6.QtCore import QSettings, QSize  # noqa: E402

from backend import camera_ownership  # noqa: E402
from backend.camera_service import CameraDevice, CameraService  # noqa: E402

RESOLUTIONS = [(320, 240), (640, 480), (1280, 720), (1920, 1080), (480, 640)]


class RuntimeCompatibilityTests(unittest.TestCase):
    def test_compat_python_and_os_supported(self):
        self.assertGreaterEqual(sys.version_info[:2], (3, 10), "code uses PEP 604 'X | None' at runtime")
        self.assertIn(platform.system(), ("Windows", "Darwin", "Linux"))

    def test_compat_core_dependencies_import(self):
        missing = []
        for name in ("PySide6", "cv2", "numpy", "sqlalchemy", "argon2", "requests"):
            try:
                importlib.import_module(name)
            except ImportError:
                missing.append(name)
        self.assertEqual(missing, [])

    def test_compat_ml_dependencies_import(self):
        missing = []
        for name in ("mediapipe", "tensorflow"):
            try:
                importlib.import_module(name)
            except Exception:
                missing.append(name)
        self.assertEqual(missing, [])

    def test_compat_frozen_build_resolves_resources(self):
        from backend import paths
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            (Path(tmp) / "resources").mkdir()
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "_MEIPASS", tmp, create=True):
                self.assertEqual(paths.get_base_dir(), Path(tmp))
        self.assertTrue((paths.get_base_dir() / "resources").is_dir())


class WebcamCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.settings = QSettings(str(Path(self.tmp.name, "c.ini")), QSettings.Format.IniFormat)
        self.owner = object()
        self.addCleanup(camera_ownership.release, self.owner)

    def test_compat_real_device_enumeration_never_crashes(self):
        devices = CameraService(self.settings).discover()          # may legitimately be empty (CI)
        self.assertIsInstance(devices, list)
        for d in devices:
            self.assertTrue(d.device_id and d.name)

    def test_compat_builtin_and_usb_cameras_selected_by_stable_id(self):
        devices = [CameraDevice("built-in", "Integrated Camera"), CameraDevice("usb", "USB Webcam")]
        factory = Mock(return_value=Mock(isOpened=Mock(return_value=True), error=None))
        for order in (devices, list(reversed(devices))):           # enumeration order differs per machine
            service = CameraService(self.settings, Mock(return_value=order), factory)
            for chosen in devices:
                service.save_selection(chosen)
                cap = service.open_capture(owner=self.owner)
                self.assertEqual(factory.call_args.args[0].device_id, chosen.device_id)
                cap.release()

    def test_compat_landmark_features_are_resolution_independent(self):
        from backend.recognition_engine import HandLandmarkExtractor
        lm = [NS(x=0.4 + i * 0.01, y=0.5 + i * 0.008, z=0.0) for i in range(21)]
        results = []
        for w, h in RESOLUTIONS:
            ex = HandLandmarkExtractor.__new__(HandLandmarkExtractor)
            ex._hands = Mock(process=Mock(return_value=NS(multi_hand_landmarks=[NS(landmark=lm)])))
            features, _ = ex.process(np.zeros((h, w, 3), np.uint8))
            self.assertEqual(features.shape, (63,), (w, h))
            results.append(features)
        for other in results[1:]:
            np.testing.assert_allclose(results[0], other)

    def test_compat_preview_handles_every_webcam_resolution(self):
        from screens.camera_preview import RoundedCameraPreview
        for w, h in RESOLUTIONS:
            preview = RoundedCameraPreview()
            preview.resize(640, 480)
            preview.set_bgr_frame(np.full((h, w, 3), 90, np.uint8))
            self.assertEqual(preview.pixmap().size(), QSize(w, h))
            self.assertFalse(preview.grab().isNull())
            preview.deleteLater()

    def test_compat_landing_screen_fits_common_laptop_displays(self):
        from screens.startup import LandingScreen
        landing = LandingScreen()
        try:
            for w, h in ((1280, 720), (1366, 768), (1536, 864), (1920, 1080), (1024, 600)):
                landing.resize(w, h)
                landing._fitted_form.fit()
                for button in (landing.ui.btnGetStarted, landing.ui.btnLearnMore, landing.ui.btnLogin):
                    self.assertTrue(landing.rect().contains(button.geometry()), (w, h, button.objectName()))
        finally:
            landing.close()
            landing.deleteLater()


if __name__ == "__main__":
    unittest.main()