"""Small-display and artwork hit-area regressions for the existing screens."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint, Qt, QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QPushButton
from screens.startup import LandingScreen, WelcomeScreen
from screens.auth.login import LoginScreen
from screens.auth.register import RegisterScreen
from screens.minigames.sign_sprint import SignSprint
from screens.quizzes.module_quiz import ModuleQuiz


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
