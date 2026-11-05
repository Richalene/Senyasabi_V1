"""Tests for media resolution and player signal lifecycle fixes."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Setup path so 'backend' and 'screens' can be imported
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PySide6.QtWidgets import QApplication

# Ensure QApplication exists for Qt widgets
app = QApplication.instance() or QApplication([])

from backend.content_service import ROOT
from backend.media_service import resolve_sign_video, alphabet_still
from screens.media_player import SignVideoPlayer


class TestMediaResolution(unittest.TestCase):
    """Test media resolution across all modules and aliases."""

    def test_greeting_manifest_resolution(self):
        """Greeting must resolve using the greeting manifest section."""
        rec = resolve_sign_video("greeting", "good_morning")
        self.assertTrue(rec.available, "greeting/good_morning should be available")
        self.assertEqual(rec.status, "bundled")
        self.assertIsNotNone(rec.local_path)
        self.assertTrue(rec.local_path.is_file())
        self.assertIn("0_GOOD_MORNING", str(rec.local_path))

        rec_fine = resolve_sign_video("greeting", "im_fine")
        self.assertTrue(rec_fine.available, "greeting/im_fine should be available")
        self.assertTrue(rec_fine.local_path.is_file())

        rec_welcome = resolve_sign_video("greeting", "you_re_welcome")
        self.assertTrue(rec_welcome.available, "greeting/you_re_welcome should be available")
        self.assertTrue(rec_welcome.local_path.is_file())

    def test_survival_manifest_resolution(self):
        """Survival must resolve using the survival manifest section."""
        rec = resolve_sign_video("survival", "understand")
        self.assertTrue(rec.available, "survival/understand should be available")
        self.assertEqual(rec.status, "bundled")
        self.assertIsNotNone(rec.local_path)
        self.assertTrue(rec.local_path.is_file())
        self.assertIn("10_UNDERSTAND", str(rec.local_path))

        rec_dont = resolve_sign_video("survival", "dont_understand")
        self.assertTrue(rec_dont.available, "survival/dont_understand should be available")
        self.assertTrue(rec_dont.local_path.is_file())

    def test_communication_shared_module_resolution(self):
        """Shared communication module must correctly resolve greeting and survival signs."""
        rec_greet = resolve_sign_video("communication", "good_morning")
        self.assertTrue(rec_greet.available, "communication/good_morning should resolve")
        self.assertTrue(rec_greet.local_path.is_file())

        rec_surv = resolve_sign_video("communication", "understand")
        self.assertTrue(rec_surv.available, "communication/understand should resolve")
        self.assertTrue(rec_surv.local_path.is_file())

    def test_all_ten_number_mappings(self):
        """Number codes must support both numeric identifiers ('1'-'10') and word keys ('one'-'ten')."""
        num_word_pairs = [
            ("1", "one"),
            ("2", "two"),
            ("3", "three"),
            ("4", "four"),
            ("5", "five"),
            ("6", "six"),
            ("7", "seven"),
            ("8", "eight"),
            ("9", "nine"),
            ("10", "ten"),
        ]
        for digit, word in num_word_pairs:
            rec_digit = resolve_sign_video("number", digit)
            self.assertTrue(rec_digit.available, f"number/{digit} must be available")
            self.assertTrue(rec_digit.local_path.is_file(), f"number/{digit} file must exist")

            rec_word = resolve_sign_video("number", word)
            self.assertTrue(rec_word.available, f"number/{word} must be available")
            self.assertTrue(rec_word.local_path.is_file(), f"number/{word} file must exist")
            self.assertEqual(rec_digit.local_path, rec_word.local_path, f"Paths for {digit} and {word} must match")

    def test_existing_calendar_days_family_resolution(self):
        """Preserve existing calendar, days, and family resolution."""
        rec_cal = resolve_sign_video("calendar", "january")
        self.assertTrue(rec_cal.available)
        self.assertTrue(rec_cal.local_path.is_file())
        self.assertIn("30_JANUARY", str(rec_cal.local_path))

        rec_day = resolve_sign_video("days", "monday")
        self.assertTrue(rec_day.available)
        self.assertTrue(rec_day.local_path.is_file())
        self.assertIn("42_MONDAY", str(rec_day.local_path))

        rec_fam = resolve_sign_video("family", "father")
        self.assertTrue(rec_fam.available)
        self.assertTrue(rec_fam.local_path.is_file())
        self.assertIn("52_FATHER", str(rec_fam.local_path))

    def test_alphabet_no_fake_video_and_png_fallback(self):
        """Alphabet should report unavailable video and resolve to bundled VRM PNG still."""
        rec_alpha = resolve_sign_video("alphabet", "a")
        self.assertFalse(rec_alpha.available, "Alphabet must not invent fake video clips")
        self.assertIsNone(rec_alpha.local_path)

        still = alphabet_still("A")
        self.assertIsNotNone(still, "alphabet_still must find A.png")
        self.assertTrue(Path(still).is_file())
        self.assertTrue(str(still).endswith("A.png"))


class TestPlayerSignalLifecycle(unittest.TestCase):
    """Test SignVideoPlayer signal connection, release, and reuse."""

    def test_signal_reconnection_after_release_and_reuse(self):
        """Ensure mediaStatusChanged and errorOccurred signals reconnect after release."""
        player = SignVideoPlayer(muted=True)
        player.set_sign("calendar", "january")
        self.assertTrue(player.media.available)

        # Initial play: connects signals
        player.play()
        self.assertIsNotNone(player.player)
        self.assertTrue(getattr(player, "_signals_connected", False))

        # Release: disconnects signals and pauses
        player.release()
        self.assertFalse(getattr(player, "_signals_connected", True))

        # Re-use play: reconnects signals exactly once
        player.play()
        self.assertTrue(getattr(player, "_signals_connected", False))

        # Cleanup
        player.release()


def _fake_init_cam(self, factory=None, *args, **kwargs):
    from screens.loading import LoadingOverlay
    self._engine_factory = factory
    self._availability = None
    self._camera_dialog = None
    self._camera_misses = 0
    self._resources_closed = False
    self._engine = None
    self.loading = LoadingOverlay(self)

class TestLessonAndQuizMediaDisplay(unittest.TestCase):
    """Test lesson and quiz media handling with mocks to avoid hardware dependency."""

    @patch("screens.camera_access.LessonCameraMixin._init_camera", _fake_init_cam)
    def test_word_lesson_greeting_media_display(self):
        """Word lesson for greeting should resolve available video."""
        from screens.lessons.words.word_lesson import WordLessonWidget
        widget = WordLessonWidget(words=["Good morning"], category="greeting")
        self.assertTrue(widget.video.media.available, "Greeting word video must be available")
        self.assertFalse(widget.video.isHidden(), "Video widget should not be hidden when media is available")
        widget.close()

    @patch("screens.camera_access.LessonCameraMixin._init_camera", _fake_init_cam)
    def test_alphabet_lesson_still_fallback(self):
        """Alphabet lesson should fall back to VRM PNG still on avatar_card."""
        from screens.lessons.alphabet.alphabet_lesson import AlphabetLessonWidget
        widget = AlphabetLessonWidget(lesson_number=1)
        self.assertFalse(widget.video.media.available, "Alphabet has no video")
        self.assertTrue(widget.video.isHidden(), "Video should be hidden for alphabet")
        pixmap = widget.layout_comp.avatar_card.pixmap_sign
        self.assertFalse(pixmap.isNull(), "AvatarCard should have loaded the letter PNG still")
        widget.close()

    def test_quiz_greeting_and_alphabet_display(self):
        """Quiz should show video for greeting and sign image for alphabet."""
        from screens.quizzes.module_quiz import ModuleQuiz

        # Word Quiz (greeting)
        quiz_greet = ModuleQuiz("greeting")
        current_sign = quiz_greet.session.current
        self.assertIsNotNone(current_sign)
        self.assertTrue(quiz_greet.video.media.available, "Greeting quiz video must be available")
        self.assertFalse(quiz_greet.video.isHidden(), "Video widget should be visible")
        self.assertTrue(quiz_greet.sign_image.isHidden(), "Static sign image should be hidden when video available")
        quiz_greet.close()

        # Alphabet Quiz
        quiz_alpha = ModuleQuiz("alphabet")
        current_alpha = quiz_alpha.session.current
        self.assertIsNotNone(current_alpha)
        self.assertFalse(quiz_alpha.video.media.available, "Alphabet quiz has no video")
        self.assertTrue(quiz_alpha.video.isHidden(), "Video widget should be hidden")
        self.assertFalse(quiz_alpha.sign_image.isHidden(), "Static sign image should be visible")
        self.assertFalse(quiz_alpha._current_sign_pixmap.isNull(), "Static sign image pixmap should be loaded")
        quiz_alpha.close()


if __name__ == "__main__":
    unittest.main()
