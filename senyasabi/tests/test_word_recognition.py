"""Training parity and live lifecycle checks without fake deployed model artifacts."""
import ast
import hashlib
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

import numpy as np

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import camera_ownership
from backend.content_service import get_signs_for_module
from backend.recognition_labels import normalize_label
from backend.model_service import CategoryRecognitionEngine, ModelState, ModelValidationError, SequenceRecognizer
from backend import word_landmarks as landmarks


def config():
    return dict(num_frames=24, feature_dim=172, num_hands=2,
                pose_indices=list(landmarks.POSE_INDICES), feature_order=landmarks.FEATURE_ORDER,
                normalization=landmarks.NORMALIZATION)


class TrainingParityTests(unittest.TestCase):
    def test_extraction_and_final_normalization_ast_match_supplied_source(self):
        # Digests were obtained from the supplied script's functions without
        # executing any Colab/setup/training code. Ignore only the lazy MP import.
        expected = {
            'xyz': 'c859e762bead6dcb21012a5d56b7fe4d7c27a7f4f2ba962e627da1039b17601c',
            'frame_to_features': '2707150e23a8d0a7ea47802dbd644c8c5da64b67498f097f60ff5063a2a1c101',
            'normalize_label': '2c2b5fc69ae0d4ef2671eef19cb5fac2db39b31de732049f491fd2656f2f5a75',
        }
        for module in ('word_landmarks.py', 'recognition_labels.py'):
            tree = ast.parse((Path(landmarks.__file__).parent / module).read_text(encoding='utf-8'))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in expected:
                    node.body = [item for item in node.body if not isinstance(item, ast.Import)]
                    digest = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
                    self.assertEqual(digest, expected.pop(node.name))
        self.assertFalse(expected)

    def test_recognition_canonicalization_preserves_display_and_sign_code(self):
        self.assertEqual(normalize_label("  don'T   know "), 'DONT KNOW')
        self.assertEqual(normalize_label('don’t  understand'), 'DONT UNDERSTAND')
        sign = next(sign for sign in get_signs_for_module('survival') if 'UNDERSTAND' in sign.label and 'DON' in sign.label)
        self.assertIn('’', sign.label)
        self.assertEqual(sign.recognition_label, 'DONT UNDERSTAND')
        self.assertEqual(sign.sign_code, 'don_t_understand')

    def test_exported_config_validated_without_key_translation(self):
        self.assertEqual(landmarks.validate_landmark_config(config()), config())
        for key, invalid in (('num_frames', 23), ('feature_dim', 171), ('num_hands', 1),
                             ('pose_indices', list(reversed(landmarks.POSE_INDICES))),
                             ('feature_order', 'hand first'), ('normalization', 'wrist')):
            bad = config()
            bad[key] = invalid
            with self.subTest(key=key), self.assertRaises(ValueError):
                landmarks.validate_landmark_config(bad)


class FeaturesTests(unittest.TestCase):
    def setUp(self):
        self.mp = NS(Image=Mock(side_effect=lambda **kwargs: NS(**kwargs)), ImageFormat=NS(SRGB='rgb'))
        self.modules = patch.dict(sys.modules, {'mediapipe': self.mp})
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def extract(self, pose=(), hands=(), names=()):
        self.pose = Mock(detect=Mock(return_value=NS(pose_landmarks=[pose] if pose else [])))
        self.hand = Mock(detect=Mock(return_value=NS(hand_landmarks=hands, handedness=[
            [NS(category_name=name)] if name else [] for name in names])))
        return landmarks.frame_to_features(np.zeros((2, 2, 3), np.uint8), self.hand, self.pose)

    @staticmethod
    def hand_at(x, y, z):
        return [NS(x=x, y=y, z=z) for _ in range(21)]

    def test_exact_order_origin_scale_visibility_and_handedness(self):
        pose = [NS(x=.5, y=.5, z=0, visibility=1) for _ in range(33)]
        pose[0] = NS(x=.5, y=.6, z=.1, visibility=.9)
        pose[11].x, pose[12].x = .4, .6
        left, right = self.hand_at(.4, .6, .2), self.hand_at(.8, .4, -.1)
        vector, pose_found, hand_count = self.extract(pose, [right, left], ['Right', 'Left'])
        self.assertEqual(vector.shape, (172,))
        self.assertEqual(vector.dtype, np.float32)
        np.testing.assert_allclose(vector[:4], [0, .5, .5, .9], atol=1e-6)
        np.testing.assert_allclose(vector[20:28], [-.5, 0, 0, 1, .5, 0, 0, 1], atol=1e-6)
        np.testing.assert_allclose(vector[44:107], np.tile([-.5, .5, 1], 21), atol=1e-6)
        np.testing.assert_allclose(vector[107:170], np.tile([1.5, -.5, -.5], 21), atol=1e-6)
        np.testing.assert_array_equal(vector[170:], [1, 1])
        self.assertTrue(pose_found)
        self.assertEqual(hand_count, 2)

    def test_no_pose_no_hands_are_exact_zero_frames(self):
        vector, found, count = self.extract()
        np.testing.assert_array_equal(vector, np.zeros(172, np.float32))
        self.assertFalse(found)
        self.assertEqual(count, 0)

    def test_missing_pose_fallback_and_missing_hand_slots(self):
        vector, found, count = self.extract(hands=[self.hand_at(.75, .25, .5)], names=['Right'])
        np.testing.assert_array_equal(vector[:107], np.zeros(107))
        np.testing.assert_array_equal(vector[107:170], np.tile([1, -1, 2], 21))
        np.testing.assert_array_equal(vector[170:], [0, 1])
        self.assertFalse(found)
        self.assertEqual(count, 1)

    def test_duplicate_and_unlabeled_hands_use_training_leftovers_order(self):
        one, two = self.hand_at(.75, .5, 0), self.hand_at(.25, .5, 0)
        for names in (['Left', 'Left'], ['', ''], []):
            vector, _, count = self.extract(hands=[one, two], names=names)
            np.testing.assert_array_equal(vector[44:47], [1, 0, 0])
            np.testing.assert_array_equal(vector[107:110], [-1, 0, 0])
            self.assertEqual(count, 2)

    def test_shoulder_scale_floor_visibility_and_nan_behavior(self):
        pose = [NS(x=.5, y=.5, z=0, visibility=None) for _ in range(33)]
        pose[0] = NS(x=.58, y=.5, z=.08, visibility=0)
        pose[7].x = float('nan')
        vector, _, _ = self.extract(pose)
        np.testing.assert_allclose(vector[:4], [1, 0, 1, 0], atol=1e-6)
        self.assertEqual(vector[4], 0)
        self.assertTrue(np.isfinite(vector).all())

    def test_partial_hand_is_not_silently_padded_differently_from_training(self):
        with self.assertRaisesRegex(RuntimeError, 'Feature shape'):
            self.extract(hands=[self.hand_at(.5, .5, 0)[:20]], names=['Left'])

    def test_runtime_converts_bgr_to_rgb_without_mirroring(self):
        preprocessor = landmarks.WordLandmarkPreprocessor.__new__(landmarks.WordLandmarkPreprocessor)
        preprocessor.hand_detector, preprocessor.pose_detector = object(), object()
        frame = np.array([[[10, 20, 30], [40, 50, 60]]], np.uint8)
        with patch.object(landmarks, 'frame_to_features', return_value=(np.zeros(172, np.float32), False, 0)) as extract:
            preprocessor.process(frame)
        np.testing.assert_array_equal(extract.call_args.args[0], [[[30, 20, 10], [60, 50, 40]]])


class SequenceTests(unittest.TestCase):
    def recognizer(self):
        model = Mock(predict=Mock(return_value=np.array([[.1, .9]], np.float32)))
        return SequenceRecognizer(model, ('BREAD', 'EGG'), config())

    def test_24_frames_required_float32_order_and_sliding_window(self):
        recognizer = self.recognizer()
        for index in range(23):
            self.assertIsNone(recognizer.predict_frame(np.full(172, index, np.float32)))
        recognizer.model.predict.assert_not_called()
        prediction = recognizer.predict_frame(np.full(172, 23, np.float32))
        self.assertEqual(prediction.label, 'EGG')
        batch = recognizer.model.predict.call_args.args[0]
        self.assertEqual(batch.shape, (1, 24, 172))
        self.assertEqual(batch.dtype, np.float32)
        np.testing.assert_array_equal(batch[0, :, 0], np.arange(24))
        recognizer.predict_frame(np.full(172, 24, np.float32))
        np.testing.assert_array_equal(recognizer.model.predict.call_args.args[0][0, :, 0], np.arange(1, 25))
        self.assertAlmostEqual(prediction.confidence, .9, places=6)  # No double softmax.

    def test_zero_frames_retained_and_buffers_are_per_session(self):
        recognizer = self.recognizer()
        other = recognizer.fork()
        for _ in range(24):
            recognizer.predict_frame(np.zeros(172, np.float32))
        self.assertEqual(len(recognizer.frames), 24)
        self.assertEqual(len(other.frames), 0)
        self.assertIs(recognizer.model, other.model)
        recognizer.reset()
        self.assertIsNone(recognizer.predict_frame(np.zeros(172, np.float32)))

    def test_frame_copied_and_invalid_input_or_output_rejected(self):
        recognizer = self.recognizer()
        frame = np.zeros(172, np.float32)
        recognizer.predict_frame(frame)
        frame[:] = 1
        np.testing.assert_array_equal(recognizer.frames[0], np.zeros(172))
        with self.assertRaises(ModelValidationError):
            recognizer.predict_frame(np.zeros(171))
        recognizer.model.predict.return_value = [[3, 2]]
        with self.assertRaisesRegex(ModelValidationError, 'softmax'):
            for _ in range(24):
                recognizer.predict_frame(np.zeros(172))


class EngineLifecycleTests(unittest.TestCase):
    def engine(self):
        model = Mock(predict=Mock(return_value=np.array([[.2, .8]], np.float32)))
        recognizer = SequenceRecognizer(model, ('BREAD', 'EGG'), config())
        registry = Mock(get_category_recognizer=Mock(return_value=ModelState('food', True, '', recognizer)))
        self.preprocessor = Mock(process=Mock(return_value=(np.zeros(172, np.float32), False, 0)))
        engine = CategoryRecognitionEngine('food', registry=registry, preprocessor_factory=lambda _: self.preprocessor)
        self.addCleanup(engine.close)
        return engine

    def test_no_hand_frames_still_fill_buffer_and_disconnect_cleans_up(self):
        engine = self.engine()
        capture = Mock(isOpened=Mock(return_value=True), read=Mock(return_value=(True, np.zeros((2, 2, 3), np.uint8))))
        with patch('backend.model_service.open_selected_capture', return_value=capture):
            self.assertTrue(engine.open_camera())
            for _ in range(23):
                self.assertIsNone(engine.read_frame().prediction)
            self.assertIsNotNone(engine.read_frame().prediction)
        capture.read.return_value = False, None
        for _ in range(3):
            self.assertIsNone(engine.read_frame())
        self.assertEqual(engine.buffered_frames, 0)
        capture.release.assert_called_once()
        self.preprocessor.close.assert_called_once()
        self.assertIsNone(camera_ownership._owner)

    def test_preprocessor_error_releases_capture_and_clears_sequence(self):
        engine = self.engine()
        capture = Mock(isOpened=Mock(return_value=True), read=Mock(return_value=(True, np.zeros((2, 2, 3), np.uint8))))
        self.preprocessor.process.side_effect = RuntimeError('detector failed')
        with patch('backend.model_service.open_selected_capture', return_value=capture):
            engine.open_camera()
            with self.assertRaisesRegex(RuntimeError, 'detector failed'):
                engine.read_frame()
        capture.release.assert_called_once()
        self.preprocessor.close.assert_called_once()
        self.assertEqual(engine.buffered_frames, 0)

    def test_detector_cleanup_includes_pose_even_when_hand_close_fails(self):
        preprocessor = landmarks.WordLandmarkPreprocessor.__new__(landmarks.WordLandmarkPreprocessor)
        hand, pose = Mock(), Mock()
        preprocessor.hand_detector, preprocessor.pose_detector = hand, pose
        hand.close.side_effect = RuntimeError('close failed')
        with self.assertRaises(RuntimeError):
            preprocessor.close()
        pose.close.assert_called_once()
        preprocessor.close()  # Idempotent after partial teardown.

    def test_missing_task_assets_fail_before_importing_mediapipe(self):
        with self.assertRaisesRegex(FileNotFoundError, 'not installed'):
            landmarks.make_landmarkers(Path(__file__).parent / 'absent-hand.task', Path(__file__).parent / 'absent-pose.task')

    def test_training_detector_options_and_partial_creation_cleanup(self):
        hand = Mock()
        vision = NS(RunningMode=NS(IMAGE='image'),
                    HandLandmarkerOptions=Mock(side_effect=lambda **kwargs: NS(**kwargs)),
                    PoseLandmarkerOptions=Mock(side_effect=lambda **kwargs: NS(**kwargs)),
                    HandLandmarker=NS(create_from_options=Mock(return_value=hand)),
                    PoseLandmarker=NS(create_from_options=Mock(side_effect=RuntimeError('pose unavailable'))))
        mp = NS(tasks=NS(BaseOptions=lambda **kwargs: NS(**kwargs), vision=vision))
        with patch.dict(sys.modules, {'mediapipe': mp}), patch('pathlib.Path.is_file', return_value=True):
            with self.assertRaisesRegex(RuntimeError, 'pose unavailable'):
                landmarks.make_landmarkers()
        hand.close.assert_called_once()
        hand_options = vision.HandLandmarkerOptions.call_args.kwargs
        pose_options = vision.PoseLandmarkerOptions.call_args.kwargs
        self.assertEqual(hand_options['running_mode'], 'image')
        self.assertEqual(pose_options['running_mode'], 'image')
        self.assertEqual(hand_options['num_hands'], 2)
        self.assertEqual(pose_options['num_poses'], 1)
        self.assertEqual(hand_options['min_hand_detection_confidence'], .35)
        self.assertEqual(hand_options['min_hand_presence_confidence'], .35)
        self.assertEqual(pose_options['min_pose_detection_confidence'], .35)
        self.assertEqual(pose_options['min_pose_presence_confidence'], .35)
