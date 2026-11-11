"""Section 15 - Usability / UI UI-001 .. UI-007 (offscreen Qt)."""
import re
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support  # noqa: E402,F401
from support import APP_ROOT, qt_app  # noqa: E402

import numpy as np  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QPushButton  # noqa: E402


def _wait_for_jobs():
    from screens.loading import _JOBS
    app = qt_app()
    deadline = time.monotonic() + 5
    while _JOBS and time.monotonic() < deadline:
        app.processEvents()
        QTest.qWait(10)


def luminance(hex_colour):
    channels = [int(hex_colour.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(fg, bg):
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def setUp(self):
        from backend import auth_service, dashboard_service
        defaults = dashboard_service.DefaultDashboardRepository().get_dashboard_stats(None)
        user = {"user_id": "ui-eval", "display_name": "Tester", "username": "tester"}
        for p in (patch.object(auth_service, "get_current_user", return_value=user),
                  patch.object(dashboard_service, "get_dashboard_stats", return_value=defaults)):
            p.start()
            self.addCleanup(p.stop)
        from screens.app_controller import AppController
        self.c = AppController()
        self.addCleanup(self._teardown)

    def _teardown(self):
        self.c.shutdown()
        _wait_for_jobs()

    def at(self, screen):
        self.app.processEvents()
        self.assertIs(self.c.stack.currentWidget(), screen)

    def test_ui_001_onboarding_navigation_and_back(self):
        c = self.c
        c.show_welcome(); self.at(c.welcome)
        c.welcome.ui.btnContinue.click(); self.at(c.landing)
        c.landing.ui.btnGetStarted.click(); self.at(c.register)
        c.register.sign_in_requested.emit(); self.at(c.login)
        c.login.back_requested.emit(); self.at(c.landing)
        c.landing.ui.btnLogin.click(); self.at(c.login)
        c.login.register_requested.emit(); self.at(c.register)
        c.register.back_requested.emit(); self.at(c.landing)

    def test_ui_001_learning_reachable_in_three_clicks_with_back(self):
        c = self.c
        c.show_main_menu(); self.at(c.main_menu)
        c.main_menu.ui.btnStartLearning.click(); self.at(c.module_map)          # click 1
        c.module_map.buttons[0].click(); self.at(c.module_lessons)              # click 2 (Alphabet)
        shown = [b for b in c.module_lessons.lesson_buttons if not b.isHidden()]
        self.assertEqual(len(shown), 4)                                         # all lessons visible
        c.module_lessons.go_back.emit(); self.at(c.module_map)
        c.module_map.back_button.click(); self.at(c.main_menu)
        c.main_menu.ui.btnMinigames.click(); self.at(c.minigames)
        c.minigames.back_button.click(); self.at(c.main_menu)


class ReadabilityTests(unittest.TestCase):
    def _check(self, fg, bg, minimum):
        ratio = contrast(fg, bg)
        self.assertGreaterEqual(ratio, minimum, f"{fg} on {bg} = {ratio:.2f}:1 (needs {minimum}:1)")

    def test_ui_002_body_text_contrast_cream_card(self):
        self._check("#5C3B28", "#FAFFDC", 4.5)

    def test_ui_002_pill_button_contrast(self):
        self._check("#704833", "#FFFDF0", 4.5)

    def test_ui_002_prediction_pill_contrast(self):
        self._check("#E5E7EB", "#2F4858", 4.5)

    def test_ui_002_next_button_white_on_green(self):         # 22px bold = large text -> 3:1
        self._check("#FFFFFF", "#ACC412", 3.0)

    def test_ui_002_back_to_lessons_white_on_green(self):     # 30px bold = large text -> 3:1
        self._check("#FFFFFF", "#8C9F3E", 3.0)

    def test_ui_002_stylesheet_font_sizes_are_legible(self):
        styles = APP_ROOT / "resources" / "styles"
        if not styles.is_dir():
            self.skipTest("resources/styles not found")
        sizes = [int(n) for f in styles.glob("*.qss") for n in re.findall(r"font-size:\s*(\d+)px", f.read_text())]
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), 11, f"smallest font is {min(sizes)}px")


class ConsistencyAndFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def test_ui_003_clickable_controls_share_pointer_cursor(self):
        from screens.auth.login import LoginScreen
        from screens.auth.register import RegisterScreen
        from screens.navigation import AssetButton, BackButton
        for cls in (LoginScreen, RegisterScreen):
            screen = cls()
            buttons = screen._ui.findChildren(QPushButton)
            self.assertTrue(buttons)
            for b in buttons:
                self.assertEqual(b.cursor().shape(), Qt.CursorShape.PointingHandCursor, b.objectName())
            screen.deleteLater()
        for factory in (AssetButton, BackButton):
            self.assertEqual(factory().cursor().shape(), Qt.CursorShape.PointingHandCursor)

    def test_ui_004_sign_feedback_states_are_visually_distinct(self):
        from screens.lessons.lesson_ui_components import ModernLessonLayout
        layout = ModernLessonLayout()
        styles = {}
        for status in ("waiting", "holding", "correct", "wrong"):
            layout.set_prediction(f"state {status}", status=status)
            styles[status] = layout.lbl_prediction.styleSheet()
        self.assertIn("5ECF8A", styles["correct"])
        self.assertIn("F87171", styles["wrong"])
        self.assertNotEqual(styles["waiting"], styles["correct"])
        self.assertNotEqual(styles["waiting"], styles["wrong"])
        self.assertTrue(layout.feedback_overlay.isHidden())
        layout.feedback_overlay.show_success(accuracy_pct=92, message="You are a Natural!")
        self.assertFalse(layout.feedback_overlay.isHidden())
        self.assertEqual(layout.feedback_overlay.lbl_accuracy.text(), "92% Accuracy")
        layout.feedback_overlay.show_retry(accuracy_pct=30)
        self.assertEqual(layout.feedback_overlay.lbl_accuracy.text(), "30% Accuracy")
        self.assertIn("Try Again", layout.feedback_overlay.lbl_message.text())

    def test_ui_004_results_screen_message_matches_accuracy(self):
        from screens.lessons.lesson_ui_components import LessonResultsWidget
        results = LessonResultsWidget()
        messages = {}
        for pct in (95, 70, 30):
            results.show_results("Lesson", pct, completed_count=1, total_count=2)
            messages[pct] = results.lbl_message.text()
            self.assertEqual(results.badge_acc.text(), f"{pct}% Accuracy")
        self.assertEqual(len(set(messages.values())), 3)

    def test_ui_005_error_messages_are_clear_and_not_technical(self):
        from backend import auth_service
        from backend.camera_service import friendly_camera_error
        from screens.app_controller import AppController
        screen = NS(error_label=Mock())
        AppController._auth_failed(screen, auth_service.AuthError("Username is already registered."), "sign you in")
        screen.error_label.setText.assert_called_with("Username is already registered.")
        screen.error_label.reset_mock()
        AppController._auth_failed(screen, RuntimeError("psycopg stack trace /etc/secret"), "sign you in")
        shown = screen.error_label.setText.call_args.args[0]
        self.assertIn("try again", shown.lower())
        self.assertNotIn("psycopg", shown)
        message = friendly_camera_error(RuntimeError("0x80070005 access violation"))
        self.assertNotIn("0x8007", message)
        self.assertIn("privacy settings", message)


class ResponsivenessTests(unittest.TestCase):
    SIZES = ((800, 600), (1280, 720), (1366, 768), (1920, 1080))

    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def test_ui_006_auth_forms_fit_without_horizontal_scroll(self):
        from screens.auth.login import LoginScreen
        from screens.auth.register import RegisterScreen
        for cls in (LoginScreen, RegisterScreen):
            window = cls()
            for w, h in self.SIZES:
                window.resize(w, h)
                window.show()
                self.app.processEvents()
                scroll = window._auth_form.scroll
                self.assertTrue(window.rect().contains(scroll.geometry()), (cls.__name__, w, h))
                self.assertEqual(scroll.horizontalScrollBar().maximum(), 0, (cls.__name__, w, h))
            window.close()
            window.deleteLater()

    def test_ui_006_minigame_scales_with_window(self):
        from screens.minigames.sign_sprint import SignSprint
        game = SignSprint(module_code="days")
        try:
            for w, h in ((1024, 600),) + self.SIZES[1:]:
                game.resize(w, h)
                game.show()
                self.app.processEvents()
                card = game.game_view.card
                self.assertLessEqual(card.width(), game.width(), (w, h))
                self.assertLessEqual(card.height(), game.height(), (w, h))
        finally:
            game.close()
            game.deleteLater()


class CameraVisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = qt_app()

    def test_ui_007_camera_preview_shows_the_frame(self):
        from screens.camera_preview import RoundedCameraPreview
        preview = RoundedCameraPreview()
        preview.resize(480, 360)
        preview.set_bgr_frame(np.full((360, 480, 3), (31, 11, 241), np.uint8))   # BGR red-ish
        preview.show()
        self.app.processEvents()
        centre = preview.grab().toImage().pixelColor(240, 180)
        self.assertGreater(centre.red(), 200)
        self.assertLess(centre.blue(), 80)
        preview.setText("Camera is off")
        self.assertTrue(preview.pixmap().isNull())                               # off state is explicit
        preview.deleteLater()

    def test_ui_007_hand_tracking_overlay_is_drawn_without_mutating_source(self):
        from backend.word_landmarks import draw_landmarks_on_frame
        frame = np.zeros((480, 640, 3), np.uint8)
        hand = [NS(x=0.4 + i * 0.01, y=0.4 + i * 0.01) for i in range(21)]
        annotated = draw_landmarks_on_frame(frame, hand_landmarks_list=[hand])
        self.assertEqual(annotated.shape, frame.shape)
        self.assertTrue(annotated.any())            # skeleton drawn
        self.assertFalse(frame.any())               # recognition frame untouched


if __name__ == "__main__":
    unittest.main()