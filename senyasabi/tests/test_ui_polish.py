"""Small-display and artwork hit-area regressions for the existing screens."""
import os
from pathlib import Path
import subprocess
import sys
from threading import Event
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, Qt, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from PySide6.QtTest import QTest
from screens.startup import LandingScreen, WelcomeScreen
from screens.auth.login import LoginScreen
from screens.auth.register import RegisterScreen
from screens.minigames.sign_sprint import SignSprint
from screens.minigames.minigame_ui_components import PillBadge
from screens.quizzes.module_quiz import ModuleQuiz
from screens.dashboard.dashboard import DashboardWindow
from screens.dialogs import ComingSoonDialog
from screens.lessons.lesson_ui_components import LessonResultsWidget, ModernLessonLayout
from screens.main_menu.lesson_select import LessonSelectWidget
from screens.main_menu.module_select import (
    FIREFLY_ROTATION_RANGE, FIREFLY_SIZE_RANGE, MODULE_NODES, ModuleSelectWidget,
)
from screens.hover_bounce import install_hover_bounce
from screens.app_controller import AppController
from screens.hover_bounce import HoverScaleEffect


class UiPolishTests(unittest.TestCase):
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

    def test_artwork_native_aspect_and_landing_hit_regions(self):
        landing = LandingScreen()
        welcome = WelcomeScreen()
        self.assertEqual(landing._fitted_form.canvas.width(), 1920)
        self.assertEqual(landing._fitted_form.canvas.height(), 1080)
        self.assertEqual(welcome._fitted_form.canvas, welcome.ui.imgBackground.pixmap().size())
        for width, height in ((800, 600), (1024, 600), (1366, 768)):
            landing.resize(width, height)
            landing._fitted_form.fit()
            scale = min(width/1920, height/1080)
            left, top = (width-1920*scale)/2, (height-1080*scale)/2
            for button, x, y in ((landing.ui.btnGetStarted, 373, 860), (landing.ui.btnLearnMore, 809, 860)):
                point = QPoint(round(left+x*scale), round(top+y*scale))
                self.assertTrue(button.geometry().contains(point))
            self.assertAlmostEqual(landing.ui.imgBackground.width()/landing.ui.imgBackground.height(), 16/9, places=2)
        self.assertEqual(landing.ui.btnLogin.text(), 'Log in')

    def test_fitted_form_clamps_to_new_screen_bounds(self):
        from PySide6.QtCore import QRect

        class Screen:
            def availableGeometry(self):
                return QRect(100, 50, 1280, 720)

        window = WelcomeScreen()
        window.resize(1600, 900)
        window.move(-200, -100)
        window._fitted_form._screen_changed(Screen())
        geometry = window.geometry()
        self.assertLessEqual(geometry.width(), 1280)
        self.assertLessEqual(geometry.height(), 720)
        self.assertGreaterEqual(geometry.left(), 100)
        self.assertGreaterEqual(geometry.top(), 50)
        self.assertLessEqual(geometry.right(), 1379)
        self.assertLessEqual(geometry.bottom(), 769)

    def test_dashboard_primary_actions_are_tight_and_nonoverlapping(self):
        dashboard = DashboardWindow()
        start = dashboard.ui.btnStartLearning.geometry()
        games = dashboard.ui.btnMinigames.geometry()
        self.assertEqual(games.x() - start.x() - start.width(), 0)
        self.assertEqual(start.y() + start.height(), games.y() + games.height())
        self.assertAlmostEqual(start.width() / start.height(), 555 / 275, places=2)
        self.assertAlmostEqual(games.width() / games.height(), 446 / 203, places=2)

    def test_dashboard_buttons_bounce_on_hover_and_restore_geometry(self):
        dashboard = DashboardWindow()
        dashboard.resize(1920, 1080)
        dashboard.show()
        self.app.processEvents()
        button = dashboard.ui.btnStartLearning
        label = dashboard.ui.lblStartLearningText
        button_geometry = button.geometry()
        label_geometry = label.geometry()
        label_screen_position = label.mapTo(dashboard, QPoint(0, 0))
        label_style = label.styleSheet()

        QTest.mouseMove(button, button.rect().center())
        QTest.qWait(180)
        self.app.processEvents()
        self.assertGreater(button.width(), button_geometry.width())
        self.assertEqual(label.width(), label_geometry.width())
        self.assertEqual(label.mapTo(dashboard, QPoint(0, 0)), label_screen_position)
        self.assertNotEqual(label.styleSheet(), label_style)

        QTest.mouseMove(dashboard, QPoint(20, 20))
        QTest.qWait(400)
        self.app.processEvents()
        self.assertEqual(button.geometry(), button_geometry)
        self.assertEqual(label.geometry(), label_geometry)
        self.assertEqual(label.styleSheet(), label_style)

    def test_shared_button_bounce_scales_visual_without_moving_hitbox(self):
        button = QPushButton("Next")
        button.setGeometry(20, 30, 180, 56)
        effect = install_hover_bounce(button)
        original_geometry = button.geometry()
        effect.set_hovered(True)
        QTest.qWait(170)
        self.app.processEvents()
        self.assertEqual(button.geometry(), original_geometry)
        self.assertGreater(effect.scale, 1.0)
        button.click()
        effect.set_hovered(False)
        QTest.qWait(220)
        self.app.processEvents()
        self.assertAlmostEqual(effect.scale, 1.0, places=2)
        self.assertEqual(button.geometry(), original_geometry)

    def test_home_stats_do_not_reload_on_same_user_screen_revisits(self):
        from backend import auth_service

        dashboard = DashboardWindow()
        dashboard._displayed_user_id = "same-user"
        with patch.object(auth_service, "get_current_user",
                          return_value={"user_id": "same-user", "display_name": "Learner"}), \
                patch.object(dashboard, "refresh_home_stats") as refresh:
            dashboard.show()
            self.app.processEvents()
            dashboard.hide()
            dashboard.show()
            self.app.processEvents()
            refresh.assert_not_called()

            dashboard._displayed_user_id = "previous-user"
            dashboard.hide()
            dashboard.show()
            self.app.processEvents()
            refresh.assert_called_once()

    def test_dashboard_stats_load_survives_screen_hide(self):
        dashboard = DashboardWindow()
        release = Event()
        completed = []
        self.assertTrue(dashboard.loading.run(
            lambda: (release.wait(2), "loaded")[1],
            completed.append,
            self.fail,
            show_delay_ms=0,
        ))
        dashboard.show()
        dashboard.hide()
        self.app.processEvents()
        busy_after_hide = dashboard.loading.busy
        release.set()
        for _ in range(100):
            self.app.processEvents()
            if completed:
                break
            QTest.qWait(5)
        self.assertTrue(busy_after_hide)
        self.assertEqual(completed, ["loaded"])

    def test_fireflies_are_larger_and_expression_is_hidden_for_alphabet(self):
        module_map = ModuleSelectWidget()
        module_map.resize(1920, 1080)
        module_map.fit()
        module_map.show()
        self.app.processEvents()
        sizes = [size for _, _, size in module_map.node_layout]
        self.assertTrue(all(FIREFLY_SIZE_RANGE[0] <= size <= FIREFLY_SIZE_RANGE[1]
                    for size in sizes))
        self.assertGreater(len(set(sizes)), 1)
        self.assertTrue(any(
            abs(x - node["x"]) > 0.001 or abs(y - node["y"]) > 0.001
            for (x, y, _), node in zip(module_map.node_layout, MODULE_NODES)
        ))
        self.assertTrue(any(abs(angle) >= FIREFLY_ROTATION_RANGE[0]
                            for angle in module_map.firefly_angles))
        self.assertTrue(any(angle == 0 for angle in module_map.firefly_angles))
        stable_layout = list(module_map.node_layout)
        module_map.play_intro("forward")
        self.assertIsNotNone(module_map._intro_animation)
        module_map.stop_intro()
        module_map.play_intro("backward")
        self.assertIsNotNone(module_map._intro_animation)
        module_map.stop_intro()
        module_map.resize(1200, 900)
        module_map.fit()
        self.assertEqual(module_map.node_layout, stable_layout)
        firefly = module_map.buttons[0]
        self.assertFalse(firefly.toolTip())
        module_map.hover_node(firefly, True)
        self.assertTrue(module_map.popup.isVisible())
        self.assertEqual(module_map.popup_title.text(), "Module 1: FSL Alphabet")
        self.assertIn("Learn the FSL alphabet", module_map.popup_detail.text())
        self.assertTrue(module_map.firefly_visuals[0].graphicsEffect().isEnabled())
        module_map.hover_node(firefly, False)
        self.assertFalse(module_map.popup.isVisible())
        self.assertFalse(module_map.firefly_visuals[0].graphicsEffect().isEnabled())

        lessons = LessonSelectWidget(module_code="alphabet")
        self.assertTrue(lessons.btn_expression.isHidden())
        lessons.set_module("number")
        self.assertFalse(lessons.btn_expression.isHidden())

    def test_fullscreen_persists_across_reused_screen_switches(self):
        script = """
from main import SenyaSabiApplication
from screens.app_controller import AppController
from screens.hover_bounce import HoverScaleEffect
from screens.minigames.minigame_select import MinigameSelect
app = SenyaSabiApplication([])
app.setQuitOnLastWindowClosed(False)
presented = []
original_present = app._present
def count_present(window):
    presented.append(window)
    original_present(window)
app._present = count_present
controller = AppController()
controller.show_welcome()
app.processEvents()
assert controller.welcome.isFullScreen()
assert presented == [controller.welcome]
assert isinstance(controller.welcome.ui.btnContinue.graphicsEffect(), HoverScaleEffect)
controller.show_landing()
app.processEvents()
assert controller.landing.isFullScreen()
assert presented == [controller.welcome, controller.landing]
assert isinstance(controller.landing.ui.btnGetStarted.graphicsEffect(), HoverScaleEffect)
controller.show_welcome()
app.processEvents()
assert controller.welcome.isFullScreen()
assert presented == [controller.welcome, controller.landing]
minigames = MinigameSelect()
minigames.show()
app.processEvents()
assert isinstance(minigames.menu.ui.btnSprint.graphicsEffect(), HoverScaleEffect)
assert isinstance(minigames.menu.ui.btnQuest.graphicsEffect(), HoverScaleEffect)
assert isinstance(minigames.menu.ui.btnDetective.graphicsEffect(), HoverScaleEffect)
controller.shutdown()
minigames.close()
app.processEvents()
"""
        env = dict(os.environ)
        env["QT_QPA_PLATFORM"] = "offscreen"
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_module_transition_uses_fireflies_without_a_full_window_overlay(self):
        controller = AppController()
        try:
            controller._show_screen(controller.welcome)
            self.app.processEvents()
            with patch("screens.app_controller.auth_service.get_current_user",
                       return_value={"user_id": "transition-test"}):
                controller.show_module_map()
                self.app.processEvents()

            self.assertFalse(controller.welcome.isVisible())
            self.assertTrue(controller.module_map.isVisible())
            self.app.processEvents()
            self.assertIsNotNone(controller.module_map._intro_animation)
        finally:
            controller.shutdown()

    def test_lesson_target_label_is_large_and_centered(self):
        lesson = ModernLessonLayout()
        lesson.set_target("A", category="ALPHABET LESSON 1")
        self.assertEqual(lesson.lbl_target_word.text(), "A")
        self.assertTrue(lesson.lbl_target_word.alignment() & Qt.AlignmentFlag.AlignHCenter)
        self.assertIn("52px", lesson.lbl_target_word.styleSheet())

    def test_coming_soon_copy_wraps_and_next_lesson_is_optional(self):
        dialog = ComingSoonDialog()
        labels = dialog.findChildren(QLabel)
        title = next(label for label in labels if label.text().startswith("Building"))
        description = next(label for label in labels if label.text().startswith("We appreciate"))
        self.assertTrue(title.wordWrap())
        self.assertNotIn("\n", title.text())
        self.assertTrue(description.wordWrap())

        results = LessonResultsWidget()
        self.assertIsInstance(results.badge_acc, PillBadge)
        results.show_results("FSL Alphabet - Lesson 1", 90, has_next_lesson=True)
        badge_image = results.badge_acc.grab().toImage()
        self.assertNotEqual(
            badge_image.pixelColor(0, 0),
            badge_image.pixelColor(badge_image.width() // 2, badge_image.height() // 2),
        )
        calls = []
        results.next_lesson_requested.connect(lambda: calls.append(True))
        results.show_results("FSL Alphabet - Lesson 1", 90, has_next_lesson=True)
        self.assertTrue(results.btn_next_lesson.isVisible())
        results.btn_next_lesson.click()
        self.assertEqual(calls, [True])
        results.show_results("FSL Alphabet - Lesson 4", 90, has_next_lesson=False)
        self.assertFalse(results.btn_next_lesson.isVisible())

    def test_auth_forms_scroll_instead_of_clipping_small_displays(self):
        for cls in (LoginScreen, RegisterScreen):
            window = cls()
            window.resize(800, 600)
            window.show()
            self.app.processEvents()
            form = window._auth_form
            self.assertTrue(window.rect().contains(form.scroll.geometry()))
            self.assertEqual(form.scroll.horizontalScrollBar().maximum(), 0)
            if cls is RegisterScreen:
                form.scroll.verticalScrollBar().setValue(form.scroll.verticalScrollBar().maximum())
                last = window._ui.findChild(QPushButton, 'signInButton')
                self.assertTrue(form.scroll.viewport().rect().contains(last.mapTo(form.scroll.viewport(), last.rect().center())))
            window.close()

    def test_sprint_playback_and_back_controls_remain_reachable_at_600_height(self):
        game = SignSprint(module_code='greeting')
        game.resize(800, 600)
        game.show()
        self.app.processEvents()
        game.fit_sequence()
        self.app.processEvents()
        viewport = game.content_scroll.viewport()
        self.assertTrue(game.rect().contains(game.next_button.geometry()))
        self.assertTrue(game.rect().contains(game.back_button.geometry()))
        for button in (game.play_button, game.pause_button, game.replay_button):
            center = button.mapTo(viewport, button.rect().center())
            self.assertTrue(viewport.rect().contains(center))
        self.assertLessEqual(game.image.width(), 250)

    def test_sprint_game_scales_with_window_size(self):
        game = SignSprint(module_code='greeting')
        game.resize(1200, 800)
        game.show()
        self.app.processEvents()
        self.assertLessEqual(game.game_view.card.width(), game.width())
        self.assertLessEqual(game.game_view.card.height(), game.height())
        game.showFullScreen()
        self.app.processEvents()
        self.assertLessEqual(game.game_view.card.width(), game.width())
        self.assertLessEqual(game.game_view.card.height(), game.height())

    def test_quiz_long_sequences_reflow_without_losing_answer(self):
        quiz = ModuleQuiz('relationships')
        quiz.resize(800, 600)
        quiz.show()
        self.app.processEvents()
        quiz.answer.setText('HARD OF HEARING')
        quiz.resize(640, 600)
        self.app.processEvents()
        quiz.reflow_sequence()
        self.app.processEvents()
        self.assertEqual(quiz.answer.text(), 'HARD OF HEARING')
        self.assertLessEqual(quiz._sequence_columns, 5)
        self.assertEqual(quiz.scroll.horizontalScrollBar().maximum(), 0)
