"""Resource boundaries use temporary fixtures and injected loaders, never shipped fake artifacts."""
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.content_service import MODULE_CODES, get_signs_for_module, get_words_for_module
from backend.media_service import MediaRecord, MediaService
from backend.model_service import CategoryModelRegistry, CategoryRecognitionEngine
from backend.minigame_service import GameSession, letters, normalize
from backend.quiz_service import QuizSession, get_quiz
from backend.word_landmarks import POSE_INDICES, FEATURE_ORDER, NORMALIZATION


def training_config():
    # In-memory metadata fixture with the exact schema exported by training.
    return dict(num_frames=24, feature_dim=172, num_hands=2,
                pose_indices=POSE_INDICES, feature_order=FEATURE_ORDER, normalization=NORMALIZATION)


class ContentTests(unittest.TestCase):
    def test_105_signs_and_module_scoped_games_quizzes(self):
        self.assertEqual(sum(len(get_signs_for_module(code)) for code in MODULE_CODES), 105)
        for code in (*MODULE_CODES, "alphabet"):
            allowed = set(get_words_for_module(code))
            self.assertTrue(allowed)
            for kind in ("sprint", "quest", "detective"):
                session = GameSession(kind, module_code=code)
                self.assertTrue(set(session.words) <= allowed)
            quiz = QuizSession(code, count=105)
            self.assertEqual({sign.label for sign in quiz.questions}, allowed)
            self.assertEqual(quiz.definition.module_code, code)
        self.assertEqual(len(get_words_for_module("alphabet")), 26)

    def test_unknown_module_is_not_all_vocabulary(self):
        for operation in (get_words_for_module, get_quiz, QuizSession):
            with self.assertRaises(ValueError):
                operation("typo")

    def test_punctuation_only_skipped_in_physical_sequence(self):
        self.assertEqual(letters("DON’T KNOW"), list("DONTKNOW"))
        self.assertEqual(normalize("don't  know"), normalize("DON’T KNOW"))
        self.assertNotEqual(normalize("dont know"), normalize("DON’T KNOW"))

    def test_quiz_scores_once_and_requires_answer_before_next(self):
        quiz = QuizSession("food", count=2)
        quiz.advance()
        self.assertEqual(quiz.index, 0)
        self.assertTrue(quiz.answer(quiz.current.label))
        self.assertFalse(quiz.answer(quiz.current.label))
        quiz.advance()
        self.assertFalse(quiz.answer("wrong"))
        quiz.advance()
        self.assertTrue(quiz.complete)
        self.assertEqual(quiz.percent, 50)

    def test_timer_pause_expiry_and_single_scoring(self):
        clock = Mock(return_value=100)
        game = GameSession("sprint", rounds=2, module_code="food", clock=clock)
        clock.return_value = 110
        game.pause()
        self.assertEqual(game.remaining, 35)
        clock.return_value = 1000
        self.assertEqual(game.remaining, 35)
        game.resume()
        clock.return_value = 1001
        self.assertEqual(game.remaining, 34)
        game.finish(True)
        game.finish(True)
        self.assertEqual(game.score, 1)
        game.next_round()
        clock.return_value = 2000
        game.finish(True)
        self.assertEqual(game.score, 1)


class MediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.service = MediaService(video_root=self.root)

    def test_missing_keeps_logical_identity(self):
        media = self.service.resolve_sign_video("food", "bread")
        self.assertFalse(media.available)
        self.assertEqual(media.sign_code, "bread")
        self.assertIsNone(media.media_id)

    def test_bundled_and_manifest_paths(self):
        folder = self.root / "word_categories/food"
        folder.mkdir(parents=True)
        path = folder / "bread.mp4"
        path.touch()  # Resolver existence fixture; never used as playable media.
        self.assertEqual(self.service.resolve_sign_video("food", "bread").local_path, path)
        custom = self.root / "real_export.webm"
        custom.touch()
        (self.root / "media_manifest.json").write_text(json.dumps({"food": {"bread": custom.name}}))
        self.assertEqual(self.service.resolve_sign_video("food", "bread").local_path, custom)

    def test_cache_precedence_and_remote_metadata_retained(self):
        cached = self.root / "cached.mp4"
        cached.touch()
        record = MediaRecord("food", "bread", media_id=12, local_cached_path=str(cached), remote_url="https://example.invalid/bread")
        self.service.repository = Mock(get_media_for_sign=Mock(return_value=record))
        media = self.service.resolve_sign_video("food", "bread")
        self.assertEqual(media.status, "cached")
        self.assertEqual(media.media_id, 12)
        cached.unlink()
        media = self.service.resolve_sign_video("food", "bread")
        self.assertFalse(media.available)
        self.assertEqual(media.remote_url, record.remote_url)

    def test_unavailable_repository_and_invalid_manifest(self):
        self.service.repository = Mock(get_media_for_sign=Mock(side_effect=ConnectionError("offline")))
        (self.root / "media_manifest.json").write_text("invalid")
        with self.assertLogs("backend.media_service", level="WARNING"):
            self.assertFalse(self.service.resolve_sign_video("food", "bread").available)

    def test_unknown_sign_is_not_guessed(self):
        with self.assertRaises(ValueError):
            self.service.resolve_sign_video("food", "not_a_food_sign")

    def test_invalid_manifest_value_does_not_crash_or_mask_bundled_video(self):
        folder = self.root / "word_categories/food"
        folder.mkdir(parents=True)
        (folder / "bread.mp4").touch()
        (self.root / "media_manifest.json").write_text(json.dumps({"food": {"bread": {"invalid": "shape"}}}))
        with self.assertLogs("backend.media_service", level="WARNING"):
            self.assertTrue(self.service.resolve_sign_video("food", "bread").available)


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "word_categories/food"
        self.folder.mkdir(parents=True)
        self.loader = Mock(return_value=SimpleNamespace(input_shape=(None, 24, 172), output_shape=(None, 2)))
        self.registry = CategoryModelRegistry(self.root, self.loader)

    def install_metadata_fixture(self):
        # Only injected loader reads this sentinel; no fake Keras/pickle is created.
        (self.folder / "test-artifact.bin").touch()
        (self.folder / "model_manifest.json").write_text(json.dumps({"model_path": "test-artifact.bin"}))
        (self.folder / "class_mapping.json").write_text(json.dumps(["BREAD", "EGG"]))
        (self.folder / "landmark_config.json").write_text(json.dumps(training_config()))

    def test_missing_does_not_load_tensorflow_or_legacy(self):
        self.assertFalse(self.registry.status("food").available)
        with self.assertLogs("backend.model_service", level="WARNING"):
            state = self.registry.get_category_recognizer("food")
        self.assertFalse(state.available)
        self.assertIn("not installed", state.message)
        self.loader.assert_not_called()
        with self.assertRaises(ValueError):
            CategoryRecognitionEngine("food")

    def test_lazy_cache_no_scaler_and_explicit_class_indices(self):
        self.install_metadata_fixture()
        (self.folder / "class_mapping.json").write_text(json.dumps({"1": "EGG", "0": "BREAD"}))
        self.loader.assert_not_called()
        one = self.registry.get_category_recognizer("food")
        self.assertTrue(one.available, one.message)
        two = self.registry.get_category_recognizer("food")
        self.assertIs(one.recognizer, two.recognizer)
        self.loader.assert_called_once()
        self.assertEqual(one.recognizer.labels, ("BREAD", "EGG"))
        self.assertFalse(hasattr(one.recognizer, "scaler"))

    def test_invalid_input_output_dimensions_and_missing_config(self):
        self.install_metadata_fixture()
        for shape, output in (((None, 3, 4), (None, 2)), ((None, 24, 172), (None, 7))):
            self.loader.return_value = SimpleNamespace(input_shape=shape, output_shape=output)
            with self.assertLogs("backend.model_service", level="WARNING"):
                state = self.registry.get_category_recognizer("food")
            self.assertFalse(state.available)
        (self.folder / "landmark_config.json").unlink()
        with self.assertLogs("backend.model_service", level="WARNING"):
            self.assertFalse(self.registry.get_category_recognizer("food").available)

    def test_mapping_is_not_silently_remapped(self):
        self.install_metadata_fixture()
        (self.folder / "class_mapping.json").write_text(json.dumps({"0": "BREAD", "2": "EGG"}))
        with self.assertLogs("backend.model_service", level="WARNING"):
            state = self.registry.get_category_recognizer("food")
        self.assertFalse(state.available)
        self.assertIn("contiguous", state.message)

    def test_best_model_default_custom_filenames_and_disable(self):
        (self.folder / "one.keras").touch()
        (self.folder / "two.keras").touch()
        self.assertIn("best_landmark_model.keras", self.registry.status("food").message)
        self.install_metadata_fixture()
        self.assertTrue(self.registry.status("food").available)
        (self.root / "manifest.json").write_text(json.dumps({"food": {"enabled": False}}))
        self.assertIn("disabled", self.registry.status("food").message)

    def test_category_pipeline_rejects_scaler_configuration(self):
        self.install_metadata_fixture()
        (self.folder / "model_manifest.json").write_text(json.dumps({"model_path": "test-artifact.bin", "scaler_path": "missing.pkl"}))
        self.assertIn("uses no scaler", self.registry.status("food").message)
        self.loader.assert_not_called()

    def test_bad_config_and_escaping_paths(self):
        self.install_metadata_fixture()
        config = training_config()
        config["num_frames"] = 0
        (self.folder / "landmark_config.json").write_text(json.dumps(config))
        with self.assertLogs("backend.model_service", level="WARNING"):
            self.assertFalse(self.registry.get_category_recognizer("food").available)
        self.loader.assert_not_called()
        (self.folder / "model_manifest.json").write_text(json.dumps({"model_path": "../../../outside.keras"}))
        self.assertIn("inside", self.registry.status("food").message)
