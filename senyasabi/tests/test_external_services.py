"""Section 11 - API / external services API-001 .. API-008 (OpenCV, MediaPipe, TensorFlow, DB)."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import qt_app  # noqa: E402

import numpy as np  # noqa: E402
from PySide6.QtCore import QSettings, Qt  # noqa: E402

from backend import camera_ownership  # noqa: E402
from backend.camera_service import CameraDevice, CameraError, CameraService, friendly_camera_error  # noqa: E402


def hand(n=21, x=0.5, y=0.5):
    return [NS(x=x + i * 0.01, y=y + i * 0.01, z=0.0) for i in range(n)]


class CameraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.settings = QSettings(str(Path(self.tmp.name, "cam.ini")), QSettings.Format.IniFormat)
        self.devices = [CameraDevice("usb", "USB Webcam"), CameraDevice("built-in", "Integrated Camera")]
        self.capture = Mock(isOpened=Mock(return_value=True), error=None,
                            read=Mock(return_value=(True, np.zeros((480, 640, 3), np.uint8))))
        self.factory = Mock(return_value=self.capture)
        self.service = CameraService(self.settings, Mock(return_value=self.devices), self.factory)
        self.service.save_selection(self.devices[0])
        self.owner = object()
        self.addCleanup(camera_ownership.release, self.owner)
        self.addCleanup(self.tmp.cleanup)

    def test_api_001_webcam_access_and_video_feed(self):
        cap = self.service.open_capture(owner=self.owner)
        self.assertTrue(cap.isOpened())
        ok, frame = cap.read()
        self.assertTrue(ok)
        self.assertEqual(frame.shape, (480, 640, 3))
        cap.release()
        self.capture.release.assert_called_once()
        self.assertIsNone(camera_ownership._owner)

    def test_api_002_camera_unavailable_or_disconnected(self):
        gone = CameraService(self.settings, Mock(return_value=[]), self.factory)
        self.assertEqual(gone.discover(), [])
        self.assertIsNone(gone.selected_device())               # never silently picks another
        with self.assertRaises(CameraError):
            gone.open_capture(owner=self.owner)
        self.factory.assert_not_called()
        broken = CameraService(self.settings, Mock(side_effect=RuntimeError("driver")), self.factory)
        self.assertEqual(broken.discover(), [])
        self.assertIn("driver", broken.discovery_error)

    def test_api_006_camera_permission_denied_or_in_use(self):
        self.factory.side_effect = RuntimeError("Device busy")
        with self.assertRaises(RuntimeError):
            self.service.open_capture(owner=self.owner)
        self.assertIsNone(camera_ownership._owner)             # lease not leaked
        self.factory.side_effect = None
        other = object()
        self.assertTrue(camera_ownership.claim(other))
        try:
            with self.assertRaises(CameraError):               # another activity holds the camera
                self.service.open_capture(owner=self.owner)
        finally:
            camera_ownership.release(other)
        self.assertIn("privacy settings", friendly_camera_error(RuntimeError("x")))

    def test_api_006_os_permission_prompt_paths(self):
        from screens import camera_permission as cp
        for status, expected in ((Qt.PermissionStatus.Denied, False), (Qt.PermissionStatus.Granted, True)):
            app = Mock()
            app.checkPermission.return_value = status
            got = []
            with patch.object(cp.sys, "platform", "darwin"), patch.object(cp, "QCoreApplication") as qca:
                qca.instance.return_value = app
                cp.ensure_camera_permission(got.append)
            self.assertEqual(got, [expected])
        app = Mock()
        app.checkPermission.return_value = Qt.PermissionStatus.Undetermined
        got = []
        with patch.object(cp.sys, "platform", "darwin"), patch.object(cp, "QCoreApplication") as qca:
            qca.instance.return_value = app
            cp.ensure_camera_permission(got.append)
            handler = app.requestPermission.call_args.args[2]
            handler(Mock(status=lambda: Qt.PermissionStatus.Granted))
        self.assertEqual(got, [True])


class LandmarkTests(unittest.TestCase):
    def setUp(self):
        self.mp = NS(Image=Mock(side_effect=lambda **kw: NS(**kw)), ImageFormat=NS(SRGB="rgb"))
        p = patch.dict(sys.modules, {"mediapipe": self.mp})
        p.start()
        self.addCleanup(p.stop)

    def _features(self, pose=(), hands=(), names=()):
        from backend import word_landmarks as wl
        pose_det = Mock(detect=Mock(return_value=NS(pose_landmarks=[pose] if pose else [])))
        hand_det = Mock(detect=Mock(return_value=NS(
            hand_landmarks=list(hands), handedness=[[NS(category_name=n)] if n else [] for n in names])))
        return wl.frame_to_features(np.zeros((4, 4, 3), np.uint8), hand_det, pose_det)

    def test_api_003_21_hand_landmarks_extracted(self):
        from backend.recognition_engine import HandLandmarkExtractor
        extractor = HandLandmarkExtractor.__new__(HandLandmarkExtractor)
        result = NS(multi_hand_landmarks=[NS(landmark=hand())])
        extractor._hands = Mock(process=Mock(return_value=result))
        features, _ = extractor.process(np.zeros((480, 640, 3), np.uint8))
        self.assertEqual(features.shape, (63,))                          # 21 x (x, y, z)
        np.testing.assert_allclose(features[:3], 0)                      # wrist-centred
        self.assertAlmostEqual(float(np.linalg.norm(features[27:30])), 1.0, places=5)  # palm-scaled
        vec, _, hands_found = self._features(hands=[hand()], names=["Right"])
        self.assertEqual(vec.shape, (172,))
        self.assertEqual(hands_found, 1)
        np.testing.assert_array_equal(vec[170:], [0, 1])
        self.assertTrue(np.any(vec[107:170]))

    def test_api_004_model_returns_sign_and_confidence(self):
        from backend.recognition_engine import SignPredictor
        predictor = SignPredictor.__new__(SignPredictor)
        predictor.class_names, predictor.scaler = ["A", "B", "C"], None
        predictor._infer = lambda x: np.array([[0.1, 0.7, 0.2]], np.float32)
        result = predictor.predict(np.zeros(63))
        self.assertEqual(result.label, "B")
        self.assertAlmostEqual(result.confidence, 0.7, places=5)
        self.assertAlmostEqual(sum(result.probabilities.values()), 1.0, places=5)

    def test_api_004_word_model_needs_24_frames_then_predicts(self):
        from backend import word_landmarks as wl
        from backend.model_service import SequenceRecognizer
        cfg = dict(num_frames=24, feature_dim=172, num_hands=2, pose_indices=list(wl.POSE_INDICES),
                   feature_order=wl.FEATURE_ORDER, normalization=wl.NORMALIZATION)
        model = Mock(predict=Mock(return_value=np.array([[0.2, 0.8]], np.float32)))
        rec = SequenceRecognizer(model, ("HELLO", "THANK YOU"), cfg)
        outputs = [rec.predict_frame(np.zeros(172, np.float32)) for _ in range(24)]
        self.assertTrue(all(o is None for o in outputs[:23]))
        self.assertEqual(outputs[23].label, "THANK YOU")
        self.assertTrue(0.0 <= outputs[23].confidence <= 1.0)

    def test_api_007_partial_visibility_and_poor_lighting(self):
        vec, pose_found, hands = self._features(hands=[hand()], names=["Left"])   # no pose
        self.assertEqual(vec.shape, (172,))
        self.assertFalse(pose_found)
        self.assertEqual(hands, 1)
        vec, pose_found, hands = self._features()                                  # nothing detected
        np.testing.assert_array_equal(vec, np.zeros(172, np.float32))
        self.assertEqual(hands, 0)
        pose = [NS(x=0.5, y=0.5, z=0.0, visibility=None) for _ in range(33)]
        pose[7].x = float("nan")                                                   # corrupt landmark
        vec, _, _ = self._features(pose=pose)
        self.assertTrue(np.isfinite(vec).all())


class ServiceFailureTests(unittest.TestCase):
    def test_api_005_database_connection_failure_is_handled(self):
        from backend.database import postgre_session
        with patch.object(postgre_session, "PostgreSQLSessionLocal", None):
            with self.assertRaises(RuntimeError):
                postgre_session.get_postgres_session()
            try:
                from fastapi import HTTPException
                from backend.api import media
            except ImportError:
                return
            with self.assertRaises(HTTPException) as ctx:
                media._media_row(1)
            self.assertEqual(ctx.exception.status_code, 503)

    def test_api_005_dashboard_falls_back_when_backend_down(self):
        from backend import dashboard_service
        client = Mock(get_dashboard=Mock(side_effect=ConnectionError("down")))
        with patch("backend.api_client.get_api_client", return_value=client):
            data = dashboard_service.get_dashboard_stats("some-user")
        self.assertEqual(data, dashboard_service.DefaultDashboardRepository().get_dashboard_stats("some-user"))

    def _registry(self):
        from backend.model_service import CategoryModelRegistry
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        folder = root / "word_categories" / "days"
        folder.mkdir(parents=True)
        loader = Mock()
        return CategoryModelRegistry(root, loader), folder, loader

    def _install(self, folder):
        from backend import word_landmarks as wl
        (folder / "best_landmark_model.keras").touch()
        (folder / "class_mapping.json").write_text(json.dumps(["MONDAY", "TUESDAY"]))
        (folder / "landmark_config.json").write_text(json.dumps(dict(
            num_frames=24, feature_dim=172, num_hands=2, pose_indices=list(wl.POSE_INDICES),
            feature_order=wl.FEATURE_ORDER, normalization=wl.NORMALIZATION)))

    def test_api_008_missing_or_unreadable_model(self):
        from backend.model_service import CategoryRecognitionEngine, ModelValidationError
        registry, folder, loader = self._registry()
        state = registry.get_category_recognizer("days")                 # nothing installed
        self.assertFalse(state.available)
        self.assertIn("not installed", state.message)
        with self.assertRaises(ModelValidationError):
            CategoryRecognitionEngine("days", registry=registry)
        self._install(folder)
        loader.side_effect = OSError("file is corrupt")                  # unreadable model
        state = registry.get_category_recognizer("days")
        self.assertFalse(state.available)
        self.assertIn("corrupt", state.message)
        (folder / "class_mapping.json").write_text("{not json")          # unreadable mapping
        self.assertFalse(registry.get_category_recognizer("days").available)

    @unittest.skipUnless(importlib.util.find_spec("tensorflow"), "tensorflow not installed")
    def test_api_008_alphabet_model_missing_file(self):
        from backend.recognition_engine import SignPredictor
        with self.assertRaises(Exception):
            SignPredictor(Path(tempfile.gettempdir()) / "does_not_exist.keras", labels_fallback=list("AB"))


if __name__ == "__main__":
    unittest.main()