"""Offscreen navigation, resource states, cancellation and camera lifecycle tests."""
import os
from pathlib import Path
import subprocess
import sys
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget, QPushButton
from backend import auth_service, camera_ownership, dashboard_service, leaderboard_service
from backend.session_state import CameraPracticeSession
from screens.app_controller import AppController
from screens.image_card import CharacterImageCard
from screens.loading import LoadingOverlay
from screens.minigames.fingerspell_quest import FingerSpellQuest


def wait_until(predicate, timeout=3000):
    for _ in range(timeout // 10):
        QApplication.processEvents()
        if predicate():
            return
        QTest.qWait(10)
    raise AssertionError("Timed out waiting for asynchronous UI operation")


class UatFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setQuitOnLastWindowClosed(False)

    def setUp(self):
        gate = patch('screens.camera_access.request_camera', side_effect=lambda parent, ready, cancelled, **kwargs: ready())
        gate.start()
        self.addCleanup(gate.stop)
        auth_service.logout_user()
        self.controller = AppController()

    def tearDown(self):
        self.controller.shutdown()
        for widget in self.app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        auth_service.logout_user()

    def only(self, screen):
        self.app.processEvents()
        self.assertEqual([window for window in self.app.topLevelWidgets() if window.isVisible()], [screen])

    def login(self):
        self.controller.show_login()
        self.controller.login.dev_button.click()
        self.only(self.controller.main_menu)

    def test_dev_guard_and_session_not_persisted(self):
        from screens.auth import login
        c = self.controller
        with patch.object(login, "DEV_MODE", False):
            c.dev_login()
            self.assertIsNone(auth_service.get_current_user())
            window = login.LoginScreen()
            self.assertFalse(hasattr(window, "dev_button"))
            window.deleteLater()
        self.login()
        user = auth_service.get_current_user()
        self.assertEqual(user["username"], "dev")
        self.assertEqual(user["display_name"], "Dev User")
        self.assertNotIn("password", user)
        self.assertIsNone(auth_service._repository.find_by_identifier("dev@example.invalid"))

    def test_missing_word_resources_quiz_and_all_back_routes(self):
        c = self.controller
        self.login()
        c.main_menu.ui.btnStartLearning.click()
        self.only(c.module_map)
        food = next(button for button in c.module_map.buttons if button.property("module_code").casefold() == "basic_communication")
        c.module_map.hover_node(food, True)
        self.assertTrue(c.module_map.popup.isVisible())
        self.assertTrue(food.graphicsEffect().isEnabled())
        food.click()
        self.only(c.module_lessons)
        self.assertEqual(c.selected_module, "basic_communication")
        self.assertFalse(c.module_map.popup.isVisible())
        from backend.model_service import ModelState
        with patch("screens.lessons.words.word_lesson._registry.status", return_value=ModelState("survival", False, "Recognition model not installed")),              patch("screens.media_player.resolve_sign_video", return_value=SimpleNamespace(available=False, local_cached_path=None, video_path=None, local_path=None)):
            c.module_lessons.lesson_buttons[0].click()
            lesson = c.active_lesson
            self.only(lesson)
            wait_until(lambda: not lesson.loading.busy)
            self.assertIn("not installed", lesson._camera_lbl.text())
            self.assertFalse(lesson.video.media.available)
            self.assertIsNone(lesson._engine)
            lesson._back_btn.click()
        self.only(c.module_lessons)
        c.module_lessons.quiz_button.click()
        self.only(c.quiz)
        self.assertEqual(c.quiz.module_code, "basic_communication")
        while not c.quiz.session.complete:
            c.quiz.answer.setText(c.quiz.session.current.label)
            c.quiz.check_button.click()
            c.quiz.next_button.click()
        self.assertEqual(c.quiz.session.percent, 100)
        c.quiz.back_requested.emit()
        self.only(c.module_lessons)
        c.module_lessons.go_back.emit()
        self.only(c.module_map)
        c.module_map.back_button.click()
        self.only(c.main_menu)
        c.main_menu.ui.btnLessonsCompleted.click()
        self.only(c.dashboard)
        c.dashboard.ui.btnLeaderboard.click()
        self.only(c.dashboard._leaderboard)
        c.dashboard._leaderboard.ui.btnBack.click()
        self.only(c.dashboard)
        c.dashboard.ui.btnBack.click()
        self.only(c.main_menu)
        c.logout()
        self.only(c.login)
        self.assertIsNone(auth_service.get_current_user())
        self.assertIsNone(c.selected_module)

    def test_repeated_word_lessons_do_not_leave_hidden_windows(self):
        c = self.controller
        self.login()
        c.open_module("food")
        for _ in range(3):
            c.open_module_lesson(1)
            lesson = c.active_lesson
            wait_until(lambda: not lesson.loading.busy)
            lesson._on_back()
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        from screens.lessons.words.word_lesson import WordLessonWidget
        self.assertEqual(sum(isinstance(window, WordLessonWidget) for window in self.app.topLevelWidgets()), 1)
        self.only(c.module_lessons)

    def test_word_recognition_uses_canonical_label_but_keeps_display_text(self):
        import numpy as np
        from backend import config
        from backend.content_service import get_signs_for_module
        from backend.recognition_engine import FrameResult, PredictionResult
        from screens.lessons.words import word_lesson
        c = self.controller
        self.login()
        c.open_module('survival')
        sign = next(sign for sign in get_signs_for_module('survival')
                    if sign.recognition_label == 'DONT UNDERSTAND')
        frame = np.zeros((2, 2, 3), np.uint8)
        engine = Mock(open_camera=Mock(return_value=True), read_frame=Mock(
            return_value=FrameResult(frame, frame, True, PredictionResult('DONT UNDERSTAND', .95))))
        with patch.object(word_lesson, 'CategoryRecognitionEngine', return_value=engine), patch.object(word_lesson._registry, 'status', return_value=SimpleNamespace(available=True)):
            c.open_module_lesson(1)
            lesson = c.active_lesson
            wait_until(lambda: not lesson.loading.busy)
            lesson._timer.stop()
            lesson._session.targets = [sign.label]
            lesson._session.restart()
            lesson._refresh_ui()
            # Inference runs in a worker thread; tick consumes its latest prediction.
            wait_until(lambda: lesson._on_tick() or lesson._session.score == 1)
            wait_until(lambda: engine.reset_sequence.called)
            self.assertEqual(lesson._session.score, 1)
            self.assertEqual(lesson._word_lbl.text(), sign.label)
            self.assertIn('’', lesson._word_lbl.text())
            engine.reset_sequence.assert_called_once()
            lesson._back_btn.click()
            self.assertFalse(lesson._timer.isActive())
            engine.close.assert_called_once()
            self.only(c.module_lessons)

    def test_sprint_and_detective_module_scoping_and_lifecycle(self):
        c = self.controller
        self.login()
        c.open_module("color")
        for kind in ("sprint", "detective"):
            c.module_lessons.game_buttons[kind].click()
            self.only(c.minigames)
            game = c.minigames.game
            self.assertEqual(game.module_code, "color")
            self.assertTrue(game.countdown.isActive())
            if kind == "sprint":
                game.pause()
                self.assertFalse(game.sequence.isActive())
                self.assertIsNotNone(game.session.saved_time)
                game.replay()
                self.assertTrue(game.sequence.isActive())
            while not game.session.complete:
                game.answer.setText(game.session.word)
                game.check_answer()
                game.next_round()
            self.assertEqual(game.session.score, game.session.total)
            self.assertFalse(game.countdown.isActive())
            game.go_back()
            self.only(c.module_lessons)
            self.assertIsNone(c.minigames.game)

    def test_alphabet_unavailable_camera_and_hide_cleanup(self):
        c = self.controller
        self.login()
        c.open_module("alphabet")
        from backend import recognition_engine
        engine = Mock(open_camera=Mock(return_value=False))
        with patch.object(recognition_engine, "SignRecognitionEngine", return_value=engine):
            c.open_module_lesson(1)
            lesson = c.active_lesson
            wait_until(lambda: not lesson.loading.busy)
            self.assertIn("could not be started", lesson._camera_lbl.text())
            engine.close.assert_called_once()
            self.assertFalse(lesson._timer.isActive())
            lesson._back_btn.click()
            self.only(c.module_lessons)

    def test_alphabet_camera_close_on_navigation_and_reopen(self):
        c = self.controller
        self.login()
        c.open_module("alphabet")
        from backend import recognition_engine
        engines = [Mock(open_camera=Mock(return_value=True)) for _ in range(2)]
        with patch.object(recognition_engine, "SignRecognitionEngine", side_effect=engines):
            for engine in engines:
                c.open_module_lesson(1)
                lesson = c.active_lesson
                wait_until(lambda: not lesson.loading.busy)
                self.assertIs(lesson._engine, engine)
                c.show_module_map()  # Hiding, not just pressing Back, releases it.
                self.assertFalse(lesson._timer.isActive())
                engine.close.assert_called_once()


class CameraAndLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        gate = patch('screens.camera_access.request_camera', side_effect=lambda parent, ready, cancelled, **kwargs: ready())
        gate.start()
        self.addCleanup(gate.stop)

    def tearDown(self):
        for widget in self.app.topLevelWidgets():
            widget.close()
            widget.deleteLater()
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_quest_tuning_top_prediction_cooldown_and_cleanup(self):
        engine = Mock(open_camera=Mock(return_value=True))
        game = FingerSpellQuest(engine_factory=lambda **kwargs: engine, module_code="food")
        game.show()
        wait_until(lambda: not game.loading.busy)
        game.frame_timer.stop()
        game.practice = CameraPracticeSession(list("CC"), confidence_threshold=0.0, hold_frames=2)
        game.handle_prediction("G", .43)
        self.assertEqual(game.practice.index, 0)
        game.handle_prediction("C", .10)
        game.handle_prediction("C", .10)
        self.assertEqual(game.practice.index, 1)
        game.handle_prediction("C", .90)
        game.handle_prediction("C", .90)
        self.assertEqual(game.practice.index, 1)
        game.cooldown_timer.stop()
        game.handle_prediction("C", .10)
        game.handle_prediction("C", .10)
        self.assertTrue(game.practice.is_done())
        self.assertEqual(game.session.score, 1)
        engine.close.assert_called_once()
        game.go_back()
        self.assertFalse(game.frame_timer.isActive())
        self.assertFalse(game.countdown.isActive())

    def test_quest_unavailable_camera_and_retry(self):
        engine = Mock(open_camera=Mock(return_value=False))
        game = FingerSpellQuest(engine_factory=lambda **kwargs: engine, module_code="food")
        game.show()
        wait_until(lambda: not game.loading.busy)
        self.assertIn("Unable to start", game.camera.text())
        self.assertIsNotNone(game.session.saved_time)
        self.assertFalse(game.frame_timer.isActive())
        engine.close.assert_called_once()
        replacement = Mock(open_camera=Mock(return_value=True))
        game.engine_factory = lambda **kwargs: replacement
        game.open_camera()
        wait_until(lambda: not game.loading.busy)
        self.assertIs(game.engine, replacement)
        game.hide()
        replacement.close.assert_called_once()

    def test_cancelled_loading_disposes_result_without_callback(self):
        host = QWidget()
        host.show()
        overlay = LoadingOverlay(host)
        released = Event()
        success = Mock()
        failure = Mock()
        disposed = Mock()
        def operation():
            released.wait(2)
            return object()
        overlay.run(operation, success, failure, dispose=disposed)
        overlay.cancel()
        released.set()
        wait_until(lambda: disposed.called)
        wait_until(lambda: not __import__("screens.loading", fromlist=["_JOBS"])._JOBS)
        success.assert_not_called()
        failure.assert_not_called()
        disposed.assert_called_once()
        self.assertFalse(overlay.animation.isActive())

    def test_camera_lease_is_exclusive_and_reusable(self):
        one, two = object(), object()
        self.assertTrue(camera_ownership.claim(one))
        self.assertFalse(camera_ownership.claim(two))
        camera_ownership.release(two)
        self.assertFalse(camera_ownership.claim(two))
        camera_ownership.release(one)
        self.assertTrue(camera_ownership.claim(two))
        camera_ownership.release(two)

    def test_statistics_and_leaderboard_offline_defaults(self):
        with patch.object(dashboard_service._repository, "get_dashboard_stats", side_effect=ConnectionError("offline")):
            with self.assertLogs("backend.dashboard_service", level="WARNING"):
                self.assertEqual(dashboard_service.get_dashboard_stats("dev")["user_statistics"]["lessons_completed"], 0)
        with patch.object(leaderboard_service._repository, "get_leaderboard", side_effect=ConnectionError("offline")):
            with self.assertLogs("backend.leaderboard_service", level="WARNING"):
                self.assertEqual(leaderboard_service.get_leaderboard(), [])

    def test_current_top_three_keep_actual_rank_styling(self):
        from screens.dashboard.leaderboard import LeaderboardWindow
        with patch.object(auth_service, "get_current_user", return_value={"user_id": "mock-2"}):
            window = LeaderboardWindow()
            window.refresh()
            wait_until(lambda: not window.loading.busy)
            row = window.ui.leaderboardLayout.itemAt(1).widget()
            self.assertTrue(row.property("currentUser"))
            self.assertEqual(row.property("rank_position"), 2)
            self.assertEqual(row.property("class"), "leaderboardRank2")

    def test_image_card_rounding_and_center_crop(self):
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        source = QPixmap(200, 100)
        source.fill(QColor("red"))
        card = CharacterImageCard()
        card.source = source
        card.resize(100, 100)
        target = QPixmap(card.size())
        target.fill(Qt.GlobalColor.transparent)
        card.render(target)
        pixels = target.toImage()
        self.assertEqual(pixels.pixelColor(50, 50).name(), "#ff0000")
        self.assertEqual(pixels.pixelColor(0, 0).alpha(), 0)


class PresentationTests(unittest.TestCase):
    def test_real_application_fullscreen_keys_and_aspect_ratio(self):
        script = '''
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from main import SenyaSabiApplication
from screens.app_controller import AppController
app = SenyaSabiApplication([])
app.setQuitOnLastWindowClosed(False)
c = AppController()
c.show_welcome()
app.processEvents()
assert c.welcome.isFullScreen()
QTest.keyClick(c.welcome.ui.btnContinue, Qt.Key.Key_Escape)
app.processEvents()
assert not c.welcome.isFullScreen()
QTest.keyClick(c.welcome, Qt.Key.Key_F11)
app.processEvents()
assert c.welcome.isFullScreen()
c.dev_login()
c.show_module_map()
app.processEvents()
assert c.module_map.isFullScreen()
import sys
assert 'tensorflow' not in sys.modules
assert 'mediapipe' not in sys.modules
c.module_map.resize(1200, 900)
c.module_map.fit()
canvas = c.module_map._ui
assert abs(canvas.width()/canvas.height() - 1920/1080) < .01
assert c.module_map.rect().contains(canvas.geometry())
c.shutdown()
app.processEvents()
import os
os._exit(0)
'''
        env = dict(os.environ)
        result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1],
                                env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
