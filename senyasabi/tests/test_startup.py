import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from screens.app_controller import AppController
import main


class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.controller = AppController()
        self.screens = [self.controller.welcome, self.controller.landing,
                        self.controller.login, self.controller.register, self.controller.dashboard,
                        self.controller.main_menu]

    def tearDown(self):
        for screen in self.screens:
            screen.close()
            screen.deleteLater()
        self.app.processEvents()

    def assert_screen(self, screen):
        self.app.processEvents()
        self.assertEqual([widget for widget in self.app.topLevelWidgets() if widget.isVisible()], [screen])

    def test_launch(self):
        with patch.object(main, "QApplication", return_value=self.app), patch.object(main, "AppController", return_value=self.controller), patch.object(QApplication, "exec", return_value=0):
            self.assertEqual(main.main(), 0)
        self.assert_screen(self.controller.welcome)

    def test_repeated_routes_and_existing_back_navigation(self):
        c = self.controller
        original = tuple(self.screens)
        window_count = len(self.app.topLevelWidgets())
        for _ in range(3):
            c.show_welcome()
            self.assert_screen(c.welcome)
            c.welcome.ui.btnContinue.click()
            self.assert_screen(c.landing)
            c.landing.ui.btnLearnMore.click()
            self.assert_screen(c.landing)
            c.landing.ui.btnGetStarted.click()
            self.assert_screen(c.register)
            c.register.sign_in_requested.emit()
            self.assert_screen(c.login)
            c.login.register_requested.emit()
            self.assert_screen(c.register)
            c.show_landing()
            c.landing.ui.btnLogin.click()
            self.assert_screen(c.login)
        self.assertEqual((c.welcome, c.landing, c.login, c.register, c.dashboard, c.main_menu), original)
        self.assertEqual(len(self.app.topLevelWidgets()), window_count)

    def test_project_relative_backgrounds(self):
        root = Path(__file__).resolve().parents[1] / "resources" / "img"
        self.assertEqual(self.controller.welcome.background_path, root / "welcome.png")
        self.assertEqual(self.controller.landing.background_path, root / "landing.png")
        self.assertTrue(self.controller.welcome.ui.imgBackground.text())
